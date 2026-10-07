(function () {
  'use strict';

  // ---- Force hero video autoplay (some mobile browsers show a play
  // button and wait instead of honoring the autoplay attribute) ----
  var heroVideo = document.querySelector('.hero-video');
  if (heroVideo) {
    var tryPlay = function () {
      var p = heroVideo.play();
      if (p && p.catch) p.catch(function () {});
    };
    tryPlay();
    heroVideo.addEventListener('loadedmetadata', tryPlay);
    heroVideo.addEventListener('canplay', tryPlay);
    ['touchstart', 'click'].forEach(function (evt) {
      document.addEventListener(evt, tryPlay, { once: true, passive: true });
    });
  }

  // ---- Hero logo-overlay test: ?heromark=off shows the hero without it ----
  if (/[?&]heromark=off\b/.test(window.location.search)) {
    document.documentElement.classList.add('heromark-off');
  }

  // ---- Scrolled header state (transparent-over-hero -> solid fill) ----
  var updateScrolled = function () {
    document.body.classList.toggle('scrolled', window.scrollY > 8);
  };
  window.addEventListener('scroll', updateScrolled, { passive: true });
  updateScrolled();

  // ---- Scroll progress bar ----
  var progressBar = document.getElementById('scroll-progress');
  if (progressBar) {
    var updateProgress = function () {
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var pct = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
      progressBar.style.width = pct + '%';
    };
    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', updateProgress);
    updateProgress();
  }

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
      valEl.textContent = Math.round(eased * target).toLocaleString('en-US');
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        valEl.textContent = target.toLocaleString('en-US');
      }
    }
    window.requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window && counters.length) {
    // The real value is in the HTML (for crawlers / no-JS); zero it just before animating.
    counters.forEach(function (el) { var v = el.querySelector('.val'); if (v) v.textContent = '0'; });
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

  // ---- Lead forms -> GoHighLevel inbound webhook ----
  // Every [data-quote-form] posts straight from the browser to GHL (no server
  // hop). Forms are told apart by their hidden "source" input (form_source).
  var GHL_WEBHOOK_URL = 'https://services.leadconnectorhq.com/hooks/6I0LjKqhOUErlUG5Lyzi/webhook-trigger/5f0f8268-04f9-468f-9721-af32861149a6';
  var ATTR_KEY = 'sca_attr';
  var UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'fbclid'];

  // First-touch attribution: captured on whatever page the visitor lands on, never overwritten.
  var attribution = (function () {
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(ATTR_KEY) || '{}'); } catch (e) {}
    if (saved._captured) return saved;
    var q = new URLSearchParams(location.search);
    var a = { _captured: new Date().toISOString(), landing_page: location.pathname + location.search, referrer: document.referrer || '' };
    UTM_KEYS.forEach(function (k) { a[k] = q.get(k) || ''; });
    try { localStorage.setItem(ATTR_KEY, JSON.stringify(a)); } catch (e) {}
    return a;
  })();

  function toE164(raw) {
    var d = String(raw || '').replace(/\D/g, '');
    if (d.length === 10) return '+1' + d;
    if (d.length === 11 && d[0] === '1') return '+' + d;
    return String(raw || '').trim();
  }

  function newEventId() {
    return (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
  }

  function buildLeadPayload(form, eventId) {
    var data = {};
    new FormData(form).forEach(function (v, k) {
      if (k === 'website') return; // honeypot
      data[k === 'source' ? 'form_source' : k] = typeof v === 'string' ? v.trim() : v;
    });
    var parts = (data.name || '').split(/\s+/).filter(Boolean);
    data.full_name = data.name || '';
    data.first_name = parts.shift() || '';
    data.last_name = parts.join(' ');
    delete data.name;
    data.phone = toE164(data.phone);
    if (data.service) data.service_needed = data.service;
    data.source = 'Website';
    data.form_name = location.pathname.replace(/^\/+|\/+$/g, '') || 'home';
    data.page_url = location.href.split('#')[0];
    data.submitted_at = new Date().toISOString();
    data.event_id = eventId;
    UTM_KEYS.concat(['referrer', 'landing_page']).forEach(function (k) {
      if (!data[k]) data[k] = attribution[k] || '';
    });
    return data;
  }

  var telLink = document.querySelector('a[href^="tel:"]');
  var phoneText = telLink ? telLink.textContent.replace(/\s+/g, ' ').trim() : '';
  var callUs = phoneText ? ' Please call us at ' + phoneText + '.' : ' Please give us a call.';

  document.querySelectorAll('[data-quote-form]').forEach(function (form) {
    var status = form.querySelector('.form-success');
    var okText = status ? status.textContent : '';
    var btn = form.querySelector('[type="submit"]');
    var busy = false;

    function show(text, isError) {
      if (!status) return;
      status.textContent = text;
      status.classList.toggle('is-error', !!isError);
      status.classList.add('show');
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (busy) return;
      var hp = form.querySelector('input[name="website"]');
      if (hp && hp.value.trim()) { show(okText); form.reset(); return; } // bot: fake success, send nothing
      busy = true;
      if (btn) btn.disabled = true;
      if (status) status.classList.remove('show');
      var eventId = newEventId();
      var payload = buildLeadPayload(form, eventId);
      fetch(GHL_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          show(okText);
          form.reset();
          (window.dataLayer = window.dataLayer || []).push({ event: 'generate_lead', form_source: payload.form_source || '', event_id: eventId });
          if (window.gtag) window.gtag('event', 'generate_lead', { event_id: eventId, form_source: payload.form_source || '' });
        })
        .catch(function () { show("Sorry, we couldn't send your request." + callUs, true); })
        .then(function () { busy = false; if (btn) btn.disabled = false; });
    });
  });
})();
