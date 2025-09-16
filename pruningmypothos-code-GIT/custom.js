document.addEventListener('DOMContentLoaded', () => {

  /************************************************************
   * TYPEWRITER EFFECT (LOOP)
   ************************************************************/
  const typewriterEl = document.getElementById('typewriter');
  if (typewriterEl) {
    const phrases = ['Pruning My Pot', 'Pruning My Pothos'];
    let phraseIndex = 0;
    let charIndex = 0;
    let deleting = false;
    const commonPrefixLength = 11;

    const typingSpeed = 150;
    const deletingSpeed = 100;
    const pauseAfterPot = 1000;
    const pauseBeforePothos = 500;
    const pauseBeforeRestart = 1000;

    const typeEffect = function () {
      const currentPhrase = phrases[phraseIndex];
      const displayText = currentPhrase.substring(0, charIndex);

      typewriterEl.innerHTML = displayText + '<span class="cursor"></span>';

      if (!deleting) {
        if (charIndex < currentPhrase.length) {
          charIndex++;
          setTimeout(typeEffect, typingSpeed);
        } else {
          if (phraseIndex === 0) {
            setTimeout(() => {
              deleting = true;
              setTimeout(typeEffect, deletingSpeed);
            }, pauseAfterPot);
          } else {
            setTimeout(() => {
              phraseIndex = 0;
              charIndex = 0;
              deleting = false;
              typewriterEl.innerHTML = '';
              typeEffect();
            }, pauseBeforeRestart);
          }
        }
      } else {
        if (charIndex > commonPrefixLength) {
          charIndex--;
          setTimeout(typeEffect, deletingSpeed);
        } else {
          deleting = false;
          phraseIndex = 1;
          setTimeout(typeEffect, pauseBeforePothos);
        }
      }
    };

    typeEffect();
  }

  /************************************************************
   * MOBILE MENU TOGGLE
   ************************************************************/
  const menuToggle = document.querySelector('.menu-toggle');
  const headerNav = document.querySelector('.header-nav');
  const navLinks = document.querySelectorAll('.header-nav a');

  if (menuToggle && headerNav) {
    menuToggle.addEventListener('click', () => {
      headerNav.classList.toggle('show');
      const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
      menuToggle.setAttribute('aria-expanded', !expanded);
    });

    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        headerNav.classList.remove('show');
        menuToggle.setAttribute('aria-expanded', false);
      });
    });
  }

  /************************************************************
   * DARK MODE TOGGLE
   ************************************************************/
  const darkModeToggle = document.getElementById('darkModeToggle');

  const enableDarkMode = function () {
    document.body.classList.add('dark-mode');
    localStorage.setItem('darkMode', 'enabled');
  };

  const disableDarkMode = function () {
    document.body.classList.remove('dark-mode');
    localStorage.setItem('darkMode', 'disabled');
  };

  if (localStorage.getItem('darkMode') === 'enabled') {
    enableDarkMode();
  }

  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
      if (document.body.classList.contains('dark-mode')) {
        disableDarkMode();
      } else {
        enableDarkMode();
      }
    });
  }

  /************************************************************
   * SCROLL TO TOP BUTTON
   ************************************************************/
  const scrollToTopBtn = document.getElementById('scrollToTopBtn');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
      scrollToTopBtn.style.display = 'block';
    } else {
      scrollToTopBtn.style.display = 'none';
    }
  });

  if (scrollToTopBtn) {
    scrollToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /************************************************************
   * LAZY LOAD IMAGES
   ************************************************************/
  const images = document.querySelectorAll('img[loading="lazy"]');
  if ('loading' in HTMLImageElement.prototype) {
    images.forEach(img => {
      img.loading = 'lazy';
    });
  } else {
    console.log('Lazy loading not supported natively. Consider a polyfill.');
  }

  /************************************************************
   * GALLERY MODAL + RANKING
   ************************************************************/
  const galleryCards = document.querySelectorAll('.gallery-card');
  const modal = document.getElementById('modal');
  const modalImg = document.getElementById('modal-img');
  const modalCaption = document.getElementById('modal-caption');
  const modalClose = document.querySelector('.gallery-modal-close'); // ✅ FIXED SELECTOR

  galleryCards.forEach(card => {
    const img = card.querySelector('img');
    const caption = card.querySelector('.gallery-caption');

    img.addEventListener('click', () => {
      modal.style.display = 'flex'; // ✅ ensure it's flex not block
      modalImg.src = img.src;
      modalImg.alt = img.alt;
      modalCaption.textContent = caption ? caption.textContent : '';
    });

    const rankBtns = card.querySelectorAll('.rank-btn');
    rankBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        btn.classList.toggle('active');
      });
    });
  });

  if (modalClose) {
    modalClose.addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }

  window.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });
});

/************************************************************
 * FADE-IN ON SCROLL
 ************************************************************/
const fadeInElements = document.querySelectorAll('.fade-in');

const observerOptions = {
  root: null,
  threshold: 0.1,
};

const revealOnScroll = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

fadeInElements.forEach(el => {
  revealOnScroll.observe(el);
});



