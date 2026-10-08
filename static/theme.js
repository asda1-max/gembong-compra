/* Gembong IT — theme switcher.
   The admin sets the public default (injected as data-theme on <html> by an
   inline script in each template). Public theme switching is currently hidden. */
(function () {
  var root = document.documentElement;
  var VALID = ['retro', 'modern', 'professional'];

  function current() {
    var t = root.getAttribute('data-theme');
    return VALID.indexOf(t) !== -1 ? t : 'retro';
  }

  function apply(theme) {
    if (VALID.indexOf(theme) === -1) theme = 'retro';
    root.setAttribute('data-theme', theme);
    sync(theme);
  }

  function sync(theme) {
    var selects = document.querySelectorAll('select[data-theme-select]');
    for (var i = 0; i < selects.length; i++) selects[i].value = theme;
  }

  function wire() {
    var selects = document.querySelectorAll('select[data-theme-select]');
    sync(current());
    for (var i = 0; i < selects.length; i++) {
      selects[i].addEventListener('change', function () {
        var theme = this.value;
        apply(theme);
        window.dispatchEvent(new CustomEvent('gembong:theme', { detail: theme }));
      });
    }
    wirePageTransitions();
  }

  function wirePageTransitions() {
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function clearPageStrip() {
      document.documentElement.classList.remove('page-strip-pending');
      var strips = document.querySelectorAll('.page-strip');
      for (var i = 0; i < strips.length; i++) strips[i].remove();
    }

    var busy = false;

    // A page restored from the back/forward cache keeps its DOM and animation
    // state. Always remove any transition overlay when it becomes active again.
    window.addEventListener('pageshow', function (event) {
      busy = false;
      if (event.persisted) clearPageStrip();
    });
    if (reducedMotion) return;

    if (document.documentElement.classList.contains('page-strip-pending')) {
      window.setTimeout(clearPageStrip, 550);
    }

    document.addEventListener('click', function (event) {
      var link = event.target.closest('a[href]');
      if (!link || busy || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if ((link.target && link.target !== '_self') || link.hasAttribute('download')) return;

      var destination;
      try { destination = new URL(link.href, window.location.href); } catch (e) { return; }
      if (destination.origin !== window.location.origin || destination.pathname === window.location.pathname) return;
      if (destination.protocol !== 'http:' && destination.protocol !== 'https:') return;

      busy = true;
      event.preventDefault();
      var outgoing = document.createElement('div');
      outgoing.className = 'page-strip page-strip-out';
      outgoing.setAttribute('aria-hidden', 'true');
      document.body.appendChild(outgoing);

      window.setTimeout(function () {
        try { sessionStorage.setItem('gembong_page_strip_in', '1'); } catch (e) {}
        window.location.assign(destination.href);
      }, 520);
    });
  }

  window.GembongTheme = {
    get: current,
    set: function (theme, persist) {
      apply(theme);
    },
    reset: function () {
      apply(window.__GEMBONG_DEFAULT_THEME || 'retro');
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
