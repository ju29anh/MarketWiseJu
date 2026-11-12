try {
  if (localStorage.getItem('mw_auros_theme') === 'light') document.documentElement.classList.add('light-theme');
} catch { /* The dark default also works when storage is unavailable. */ }
