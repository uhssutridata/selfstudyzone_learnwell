(() => {
  document.querySelectorAll('[data-performance-carousel]').forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll('[data-performance-slide]'));
    const status = carousel.querySelector('[data-performance-status]');
    if (slides.length < 2) return;

    let activeIndex = 0;
    let timer = null;
    let isHovered = false;
    let isFocused = false;
    const prefersLessMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const show = (nextIndex) => {
      activeIndex = (nextIndex + slides.length) % slides.length;
      slides.forEach((slide, index) => {
        const isActive = index === activeIndex;
        slide.hidden = !isActive;
        slide.classList.toggle('is-active', isActive);
      });
      if (status) status.textContent = `${activeIndex + 1} / ${slides.length}`;
    };

    const stop = () => {
      if (timer) window.clearInterval(timer);
      timer = null;
    };
    const start = () => {
      stop();
      if (!prefersLessMotion && !document.hidden && !isHovered && !isFocused) timer = window.setInterval(() => show(activeIndex + 1), 6000);
    };

    const previous = carousel.querySelector('[data-performance-previous]');
    const next = carousel.querySelector('[data-performance-next]');
    if (previous) previous.addEventListener('click', () => { show(activeIndex - 1); start(); });
    if (next) next.addEventListener('click', () => { show(activeIndex + 1); start(); });
    carousel.addEventListener('mouseenter', () => { isHovered = true; stop(); });
    carousel.addEventListener('mouseleave', () => { isHovered = false; start(); });
    carousel.addEventListener('focusin', () => { isFocused = true; stop(); });
    carousel.addEventListener('focusout', (event) => {
      if (!carousel.contains(event.relatedTarget)) { isFocused = false; start(); }
    });
    document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());
    start();
  });
})();
