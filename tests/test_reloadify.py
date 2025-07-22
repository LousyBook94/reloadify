import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reloadify import select_html_file

@pytest.fixture
def create_html_files(tmp_path):
    (tmp_path / "index.html").touch()
    (tmp_path / "page.html").touch()
    (tmp_path / "another.html").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.html").touch()

def test_select_html_file_no_files(tmp_path):
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        assert select_html_file() is None

def test_select_html_file_single_file(tmp_path):
    (tmp_path / "index.html").touch()
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        assert select_html_file() == str((tmp_path / "index.html").resolve())

@patch('reloadify.prompt')
def test_select_html_file_multiple_files(mock_prompt, tmp_path, create_html_files):
    mock_prompt.return_value = "index.html"
    with patch('pathlib.Path.cwd', return_value=tmp_path):
        result = select_html_file()
        assert result == str((tmp_path / "index.html").resolve())
    mock_prompt.assert_called_once()
