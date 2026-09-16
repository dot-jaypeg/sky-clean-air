(function () {
  'use strict';

  // ---- Mobile nav drawer ----
  var navToggle = document.querySelector('.nav-toggle');
  var mobileNav = document.querySelector('.mobile-nav');
  var mobileNavClose = document.querySelector('.mobile-nav-close');

  function openNav() {
    mobileNav.classList.add('open');
    mobileNav.setAttribute('aria-hidden', 'false');
    document.body.classList.add('nav-open');
  }
  function closeNav() {
    mobileNav.classList.remove('open');
    mobileNav.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('nav-open');
  }
  if (navToggle) navToggle.addEventListener('click', openNav);
  if (mobileNavClose) mobileNavClose.addEventListener('click', closeNav);
  document.querySelectorAll('.mobile-nav-links a, .mobile-nav-cta a').forEach(function (link) {
    link.addEventListener('click', closeNav);
  });

  // ---- Reveal on scroll ----
  var revealEls = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && revealEls.length) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach(function (el) { revealObserver.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // ---- Counter animation ----
  var counters = document.querySelectorAll('.num[data-count]');
  function animateCounter(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var valEl = el.querySelector('.val');
    if (!valEl) return;
    var duration = 1400;
    var start = null;

    function step(timestamp) {
      if (!start) start = timestamp;
      var progress = Math.min((timestamp - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      valEl.textContent = Math.round(eased * target);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        valEl.textContent = target;
      }
    }
    window.requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window && counters.length) {
    var counterObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { counterObserver.observe(el); });
  }

  // ---- Contact form prototype (no backend yet) ----
  var quoteForm = document.getElementById('quote-form');
  var formSuccess = document.getElementById('form-success');
  if (quoteForm) {
    quoteForm.addEventListener('submit', function (e) {
      e.preventDefault();
      if (formSuccess) formSuccess.classList.add('show');
      quoteForm.reset();
    });
  }
})();
