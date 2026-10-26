(function () {
  function boot() {
    const btn = document.getElementById('pad-more');
    if (!btn) return;
    const sync = () => {
      const vpad = document.querySelector('.vpad');
      const menu = document.querySelector('.title-card, .diablo-select, .over-card, .char-select');
      const playing = !!vpad && !menu;
      btn.hidden = !playing;
      btn.classList.toggle('touch-on', playing);
      if (!playing) {
        if (vpad) vpad.classList.remove('pad-expanded');
        btn.classList.remove('on');
        btn.textContent = 'More';
      }
    };
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const vpad = document.querySelector('.vpad');
      if (!vpad) return;
      const on = vpad.classList.toggle('pad-expanded');
      btn.classList.toggle('on', on);
      btn.textContent = on ? 'Less' : 'More';
    });
    setInterval(sync, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
