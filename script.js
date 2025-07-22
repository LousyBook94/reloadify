// Welcome message with style
console.log("%cReloadify is working! ✨", "font-size: 18px; color: #4361ee; font-weight: bold;");
console.log("%cChanges will be reflected instantly when you save your files.", "color: #4895ef;");

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add scroll reveal animations
    const revealElements = document.querySelectorAll('.feature-card, .hero-content, .hero-image');
    
    const revealOnScroll = () => {
        const windowHeight = window.innerHeight;
        const revealPoint = 150;
        
        revealElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            if (elementTop < windowHeight - revealPoint) {
                element.classList.add('reveal');
            }
        });
    };
    
    // Initial check
    revealOnScroll();
    
    // Check on scroll
    window.addEventListener('scroll', revealOnScroll);
    
    // Enhanced feature card animations with better performance
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-15px) scale(1.02)';
            card.style.boxShadow = '0 20px 40px rgba(0,0,0,0.5)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '0 10px 20px rgba(0,0,0,0.3)';
        });
    });
    
    // Improved CTA Button with better feedback
    const ctaBtn = document.getElementById('cta-btn');
    if (ctaBtn) {
        ctaBtn.addEventListener('click', function() {
            // Add loading state
            this.disabled = true;
            this.style.opacity = '0.8';
            this.innerHTML = 'Redirecting... <i class="fas fa-spinner fa-spin"></i>';
            
            setTimeout(() => {
                window.location.href = 'https://github.com/LousyBook94/reloadify';
            }, 1000);
        });
    }
    
    // Enhanced live reload demo with better animation
    let reloadCount = 0;
    const reloadDemo = document.getElementById('reload-demo');
    
    if (reloadDemo) {
        const updateReloadCount = () => {
            reloadCount++;
            reloadDemo.textContent = `Live reloaded ${reloadCount} times`;
            reloadDemo.style.transform = 'scale(1.05)';
            
            setTimeout(() => {
                reloadDemo.style.transform = 'scale(1)';
            }, 300);
        };
        
        // Initial update
        updateReloadCount();
        
        // Update every 5 seconds
        setInterval(updateReloadCount, 5000);
    }
    
    // Smooth scrolling with better control
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL without page reload
                history.pushState(null, null, this.getAttribute('href'));
            }
        });
    });
    
    // Add keyboard navigation
    document.addEventListener('keydown', (e) => {
        // Space or Enter key for CTA button
        if ((e.code === 'Space' || e.code === 'Enter') && document.activeElement === ctaBtn) {
            e.preventDefault();
            ctaBtn.click();
        }
    });
});

// Enhanced animation helper with better performance
function animateValue(element, start, end, duration) {
    if (!element) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            // Ensure final value is set
            element.textContent = end;
        }
    };
    window.requestAnimationFrame(step);
}