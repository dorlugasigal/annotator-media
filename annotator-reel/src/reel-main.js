/* Builds the single paused timeline once fonts are ready. */
(function () {
  const R = window.R;

  function build() {
    gsap.registerPlugin(MorphSVGPlugin);
    R.initLayout();
    const tl = gsap.timeline({ paused: true });
    R.writers = [];
    R.sceneHook(tl);
    R.sceneShots(tl);
    R.sceneEnd(tl);
    // Frames are rendered in any order: re-run every proxy writer after each render.
    tl.eventCallback("onUpdate", () => {
      for (const w of R.writers) w();
    });
    for (const w of R.writers) w();
    return tl;
  }

  // index.html registers the timeline inline once this resolves.
  const domReady = new Promise((resolve) => {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", resolve, { once: true });
    else resolve();
  });
  R.ready = domReady.then(() => Promise.all([
    document.fonts.load('800 100px "Bricolage Grotesque"'),
    document.fonts.load('300 100px "Bricolage Grotesque"'),
    document.fonts.load('700 30px "JetBrains Mono"'),
  ]))
    .then(() => document.fonts.ready)
    // GSAP timelines are thenables: resolve with a plain wrapper, or the promise waits for a paused timeline to finish.
    .then(() => ({ tl: build() }));
})();
