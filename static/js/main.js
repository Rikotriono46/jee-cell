document.addEventListener('DOMContentLoaded', function () {

  // ===== NAVBAR SCROLL EFFECT =====
  const navbar = document.querySelector('.navbar');
  function handleNavScroll() {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }
  window.addEventListener('scroll', handleNavScroll);
  handleNavScroll();

  // ===== MOBILE HAMBURGER TOGGLE =====
  const hamburger = document.querySelector('.hamburger');
  const navMenu = document.querySelector('.navbar-menu');
  if (hamburger && navMenu) {
    hamburger.addEventListener('click', function () {
      hamburger.classList.toggle('active');
      navMenu.classList.toggle('active');
    });
  }

  // ===== CLOSE MENU ON LINK CLICK =====
  document.querySelectorAll('.navbar-menu a').forEach(function (link) {
    link.addEventListener('click', function () {
      if (hamburger) hamburger.classList.remove('active');
      if (navMenu) navMenu.classList.remove('active');
    });
  });

  // ===== INTERSECTION OBSERVER FOR FADE-UP =====
  var fadeEls = document.querySelectorAll('.fade-up');
  if (fadeEls.length > 0 && 'IntersectionObserver' in window) {
    var fadeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          fadeObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    fadeEls.forEach(function (el) {
      fadeObserver.observe(el);
    });
  }

  // ===== OPERATING HOURS STATUS =====
  function updateOpenStatus() {
    var statusEl = document.getElementById('open-status');
    if (!statusEl) return;

    var now = new Date();
    var utc = now.getTime() + now.getTimezoneOffset() * 60000;
    var wib = new Date(utc + 7 * 3600000);
    var hour = wib.getHours();
    var day = wib.getDay();

    var openHour = parseInt(statusEl.getAttribute('data-open') || '8', 10);
    var closeHour = parseInt(statusEl.getAttribute('data-close') || '17', 10);
    var weekendClose = parseInt(statusEl.getAttribute('data-weekend-close') || closeHour, 10);
    var isOpen = false;

    if (day === 0) {
      isOpen = false;
    } else if (day === 6) {
      isOpen = hour >= openHour && hour < weekendClose;
    } else {
      isOpen = hour >= openHour && hour < closeHour;
    }

    if (isOpen) {
      statusEl.className = 'hero-badge hero-badge-status open';
      statusEl.innerHTML = '<span class="status-dot-hero"></span> Sedang Buka';
    } else {
      statusEl.className = 'hero-badge hero-badge-status closed';
      statusEl.innerHTML = '<span class="status-dot-hero"></span> Sedang Tutup';
    }
  }
  updateOpenStatus();
  setInterval(updateOpenStatus, 60000);

  // ===== SMOOTH SCROLL FOR ANCHOR LINKS =====
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var targetId = this.getAttribute('href');
      if (targetId === '#') return;
      var target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        var offset = 70;
        var top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
    });
  });

  // ===== ACTIVE NAV LINK HIGHLIGHT =====
  var sections = document.querySelectorAll('section[id]');
  var navLinks = document.querySelectorAll('.navbar-menu a[href^="#"]');

  function highlightNavLink() {
    var scrollPos = window.scrollY + 100;
    sections.forEach(function (section) {
      var top = section.offsetTop - 100;
      var bottom = top + section.offsetHeight;
      var id = section.getAttribute('id');
      if (scrollPos >= top && scrollPos < bottom) {
        navLinks.forEach(function (link) {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + id) {
            link.classList.add('active');
          }
        });
      }
    });
  }
  window.addEventListener('scroll', highlightNavLink);
  highlightNavLink();

  // ===== BACK TO TOP BUTTON =====
  var backToTop = document.querySelector('.back-to-top');
  if (backToTop) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 400) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
    });

    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ===== ANNOUNCEMENT MARQUEE DUPLICATION =====
  var marqueeInner = document.querySelector('.announcements-inner');
  if (marqueeInner) {
    var clone = marqueeInner.innerHTML;
    marqueeInner.innerHTML = clone + clone;
  }

});
