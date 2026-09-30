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
  }

  // expose for programmatic use (e.g. a future "reset to default" button)
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
