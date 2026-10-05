/* Gembong IT — theme switcher.
   The admin sets a default (injected as data-theme on <html> by an inline
   script in each template). A visitor can override it here; the choice is
   persisted in localStorage. All selects marked data-theme-select stay in sync. */
(function () {
  var root = document.documentElement;
  var KEY = 'gembong_theme';
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
        try { localStorage.setItem(KEY, theme); } catch (e) {}
        window.dispatchEvent(new CustomEvent('gembong:theme', { detail: theme }));
      });
    }
    wirePageTransitions();
  }

  function wirePageTransitions() {
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) return;

    var busy = false;
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
      if (persist) { try { localStorage.setItem(KEY, theme); } catch (e) {} }
    },
    reset: function () {
      try { localStorage.removeItem(KEY); } catch (e) {}
      apply(window.__GEMBONG_DEFAULT_THEME || 'retro');
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
