// Welcome message with style
console.log("%cReloadify is working! ✨", "font-size: 18px; color: #4361ee; font-weight: bold;");
console.log("%cChanges will be reflected instantly when you save your files.", "color: #4895ef;");

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Animated counters for stats
    const counters = [
        { element: document.getElementById('reloads-counter'), target: 1000, duration: 2000 },
        { element: document.getElementById('users-counter'), target: 500, duration: 2500 },
        { element: document.getElementById('speed-counter'), target: 99, duration: 1500, suffix: '%' }
    ];
    
    // Initialize counters
    counters.forEach(counter => {
        if (counter.element) {
            let current = 0;
            const increment = counter.target / (counter.duration / 16);
            
            const updateCounter = () => {
                current += increment;
                if (current < counter.target) {
                    counter.element.textContent = Math.floor(current) + (counter.suffix || '');
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.element.textContent = counter.target + (counter.suffix || '');
                }
            };
            
            updateCounter();
        }
    });
    
    // CTA Button - Go to GitHub repo
    const ctaBtn = document.getElementById('cta-btn');
    if (ctaBtn) {
        ctaBtn.addEventListener('click', function() {
            this.innerHTML = 'Redirecting... <i class="fas fa-spinner fa-spin"></i>';
            setTimeout(() => {
                window.location.href = 'https://github.com/LousyBook94/reloadify';
            }, 1000);
        });
    }
    
    // Feature card animations
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px) scale(1.03)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Live reload demo
    let reloadCount = 0;
    const reloadDemo = document.getElementById('reload-demo');
    
    if (reloadDemo) {
        setInterval(() => {
            reloadCount++;
            reloadDemo.textContent = `Live reloaded ${reloadCount} times`;
        }, 5000);
    }
    
    // Smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});

// Animation helper
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}