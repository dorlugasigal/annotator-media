/* Layout for desktop (1920x1080) and phone (1080x1350). */
(function () {
  const R = window.R;
  // Called from build(): the compiler may hoist scripts above the composition markup.
  R.initLayout = function () {
    const root = document.querySelector('[data-composition-id="main"]');
    const W = Number(root.dataset.width), H = Number(root.dataset.height);
    const PH = root.dataset.layout === "phone";
    R.W = W; R.H = H; R.PH = PH;

    const desktop = {
      ec: { maxFs: 250, maxW: 1480, x: 140, b1: 482, b2: 716, wmFs: 64, wmRight: 1780, wmBase: 968, tagFs: 26, tagX: 146, tagBase: 968,
            glowA: { x: 980, y: -380, w: 1500, h: 1100 }, glowB: { x: -380, y: 620, w: 1200, h: 820 } },
      hook: { draw: { max: 560, maxW: 1500, y: 770 }, over: { max: 560, maxW: 1500, y: 700 }, any: { max: 440, maxW: 1700, y: 690 } },
      // Caption slots: baseline y; left slots grow right from x, right slots grow left from x.
      cap: { fs: 104, slots: { bl: { x: 96, base: 968, align: "left" }, br: { x: 1824, base: 968, align: "right" } } },
      swoosh: { y: 560, amp: 60 },
      tour: { fs: 26, stroke: 2.8 }, // label size in source px (the tour runs at 1.35x)
    };

    const phone = {
      ec: { maxFs: 212, maxW: 920, x: 80, b1: 560, b2: 770, wmFs: 58, wmRight: 1000, wmBase: 1250, tagFs: 26, tagX: 84, tagBase: 1250,
            glowA: { x: 300, y: -360, w: 1200, h: 1000 }, glowB: { x: -420, y: 880, w: 1100, h: 800 } },
      hook: { draw: { max: 430, maxW: 940, y: 820 }, over: { max: 430, maxW: 940, y: 770 }, any: { max: 300, maxW: 980, y: 770 } },
      // The toolbar lives at the bottom of the portrait shots, so captions sit at the top.
      cap: { fs: 96, slots: { bl: { x: 64, base: 188, align: "left" }, br: { x: 1016, base: 188, align: "right" } } },
      swoosh: { y: 700, amp: 70 },
      tour: { fs: 26, stroke: 2.8 }, // the portrait tour runs at 1.4x
    };

    R.L = PH ? phone : desktop;
  };
})();
