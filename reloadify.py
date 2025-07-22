import asyncio
import http.server
import socketserver
import webbrowser
import re
import urllib.parse
from pathlib import Path
import click
import rich
from rich.console import Console
from rich.panel import Panel
import watchdog.events
import watchdog.observers
import websockets
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

# --- Configuration ---
DEFAULT_PORT = 4005
MAX_PORTS_TO_TRY = 10
WATCH_GLOBS = ["*.html", "*.css", "*.js"]

# --- State ---
console = Console()
connected_clients = set()

# --- WebSocket Server ---
async def websocket_server(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def notify_clients_of_reload():
    if connected_clients:
        message = "reload"
        await asyncio.gather(*[client.send(message) for client in connected_clients])

# --- File System Watcher ---
class ChangeHandler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self, patterns, loop):
        super().__init__(patterns=patterns)
        self.loop = loop

    def on_any_event(self, event):
        if event.event_type in ["modified", "created", "deleted", "moved"]:
            console.log(f"[yellow]File change detected:[/] {event.src_path}")
            asyncio.run_coroutine_threadsafe(notify_clients_of_reload(), self.loop)

# --- HTTP Server ---
class InjectedScriptHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # In Python 3.9+, directory is a keyword argument
        if 'directory' in kwargs:
            self.directory = kwargs.pop('directory')
        else:
            self.directory = '.'  # Default to current directory
        super().__init__(*args, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def render_and_send_html(self, path):
        # The path from do_GET is URL-encoded, so decode it
        decoded_path = urllib.parse.unquote(path)

        # Normalize and secure the path
        base_dir = Path(self.directory).resolve()
        # The requested path is relative to the base_dir
        requested_path = (base_dir / decoded_path).resolve()

        # Prevent directory traversal attacks
        if not requested_path.is_relative_to(base_dir):
            self.send_error(403, "Forbidden")
            return

        try:
            with open(requested_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Inject the reload script
            reload_script = '''
                <script>
                    (function() {
                        const ws = new WebSocket("ws://localhost:5678");
                        ws.onmessage = function(event) {
                            if (event.data === "reload") {
                                window.location.reload();
                            }
                        };
                    })();
                </script>
            '''
            # Use a case-insensitive regex for the body tag
            body_end_tag = re.search(r'</body\s*>', content, re.IGNORECASE)
            if body_end_tag:
                content = content[:body_end_tag.start()] + reload_script + content[body_end_tag.start():]

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except FileNotFoundError:
            # If the specific file is not found, let the default handler try to serve it
            # (e.g., it might be a directory, and the default handler will look for index.html)
            super().do_GET()
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {e}")

    def do_GET(self):
        # Serve index.html by default
        path = self.path.lstrip('/')
        if path == '' or path.endswith('/'):
            path += 'index.html'

        # If it's an HTML file, inject the script
        if path.endswith(".html"):
            self.render_and_send_html(path)
        else:
            # For other file types (CSS, JS, images), serve them directly
            super().do_GET()

# --- Main Application Logic ---
def find_available_port(start_port, max_ports):
    for port in range(start_port, start_port + max_ports):
        try:
            with socketserver.TCPServer(("localhost", port), None) as s:
                return port
        except OSError:
            continue
    return None

async def main_async(file, watch_dir, custom_port, no_open, timeout):
    # Determine watch directory
    if watch_dir:
        watch_path = Path(watch_dir)
    else:
        watch_path = Path(file).parent

    # Determine port
    if custom_port:
        port = custom_port
        try:
            with socketserver.TCPServer(("localhost", port), None) as s:
                pass
        except OSError:
            console.print(f"[red]Error:[/] Port {port} is already in use.")
            return
    else:
        port = find_available_port(DEFAULT_PORT, MAX_PORTS_TO_TRY)
        if not port:
            console.print(f"[red]Error:[/] Could not find an available port between {DEFAULT_PORT} and {DEFAULT_PORT + MAX_PORTS_TO_TRY - 1}.")
            return

    # --- Start Services ---
    console.print(Panel(
        f"[bold green]reloadify[/] is running!\n\n"
        f"[cyan]Serving on:[/] http://localhost:{port}\n"
        f"[cyan]Watching:[/] {watch_path}",
        expand=False,
        border_style="green"
    ))

    loop = asyncio.get_running_loop()

    # Start file watcher
    event_handler = ChangeHandler(patterns=WATCH_GLOBS, loop=loop)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, str(watch_path), recursive=True)
    observer.start()

    # Configure and start HTTP server
    handler_class = lambda *args, **kwargs: InjectedScriptHttpRequestHandler(*args, directory=str(watch_path), **kwargs)
    httpd = socketserver.TCPServer(("localhost", port), handler_class)
    
    http_server_future = loop.run_in_executor(None, httpd.serve_forever)

    # Start WebSocket server
    async with websockets.serve(websocket_server, "localhost", 5678):
        if not no_open:
            # Make the file path relative to the watch path for the URL
            url_path = Path(file).relative_to(watch_path).as_posix()
            webbrowser.open(f"http://localhost:{port}/{url_path}")

        # Main loop with timeout
        try:
            if timeout:
                await asyncio.wait_for(http_server_future, timeout=timeout)
            else:
                await http_server_future
        except asyncio.TimeoutError:
            console.print(f"\n[bold yellow]Timeout of {timeout} seconds reached. Shutting down.[/]")
        except KeyboardInterrupt:
            pass  # Allow graceful shutdown
        finally:
            observer.stop()
            observer.join()
            httpd.shutdown()
            console.print("\n[bold red]Server stopped.[/]")


def select_html_file():
    """Finds HTML files and prompts the user to select one if multiple are found."""
    html_files = list(Path.cwd().rglob("*.html"))

    if not html_files:
        console.print("[bold red]No HTML files found in the current directory.[/]")
        return None

    if len(html_files) == 1:
        return str(html_files[0].resolve())

    file_paths = sorted([(str(f.relative_to(Path.cwd())), str(f.resolve())) for f in html_files])

    try:
        # Custom style for the dialog - soft, pleasing colors
        dialog_style = Style.from_dict({
            'dialog': 'bg:#2d3748',  # Soft dark blue-gray
            'dialog.body': 'bg:#2d3748 fg:#e2e8f0',  # Light gray text
            'dialog frame.label': 'bg:#4a5568 fg:#f7fafc bold',  # Title styling
            'radio-list': 'bg:#2d3748',
            'radio-checked': 'bg:#48bb78 fg:#1a202c',  # Soft green for selected
            'radio-selected': 'bg:#4a5568 fg:#f7fafc',  # Lighter gray for focused
            'button': 'bg:#4a5568 fg:#f7fafc',
            'button.focused': 'bg:#48bb78 fg:#1a202c',
        })
        
        selected_file = radiolist_dialog(
            title="🎯 Multiple HTML files found",
            text="Use ↑↓ arrows to navigate, SPACE to select, TAB to OK button, ENTER to confirm\n💡 You can also click with your mouse!",
            values=file_paths,
            style=dialog_style
        ).run()
        return selected_file
    except (KeyboardInterrupt, EOFError):
        return None


@click.command()
@click.argument("file", default=None, required=False, type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option("-d", "--directory", "watch_dir", type=click.Path(exists=True, file_okay=False, resolve_path=True), help="Custom directory to watch.")
@click.option("-p", "--port", "custom_port", type=int, help="Custom port to serve on.")
@click.option("--no-open", "no_open", is_flag=True, help="Do not open the browser automatically.")
@click.option("-t", "--timeout", "timeout", type=int, help="Automatically shut down the server after a specified number of seconds.")
def main(file, watch_dir, custom_port, no_open, timeout):
    """A blazing-fast, ultra-lightweight Python CLI tool for live-reloading web content."""
    if file is None:
        file = select_html_file()
        if file is None:
            return

    try:
        asyncio.run(main_async(file, watch_dir, custom_port, no_open, timeout))
    except KeyboardInterrupt:
        console.print("\n[bold red]Server stopped.[/]")

if __name__ == "__main__":
    main()
