(function () {
  var STORAGE_KEY = "coe-hpc-theme";
  var LIGHT = "corporate";
  var DARK = "business";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  function currentTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  var preferred =
    currentTheme() ||
    (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? DARK
      : LIGHT);
  applyTheme(preferred);

  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === DARK ? LIGHT : DARK;
      applyTheme(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        /* private browsing / storage disabled: theme just won't persist */
      }
    });
  });
})();
