/* End card (beats 58-64): the lockup draws itself and settles on the exact frame the reel opens with. */
(function () {
  const R = window.R;

  R.sceneEnd = function (tl) {
    const $ = R.$, W = R.W;
    R.buildEndCard("ecB");
    const t0 = R.bt(58);
    const l1 = $("ecB-l1"), l2 = $("ecB-l2"), wm = $("ecB-wm"), tag = $("ecB-tag");
    const glows = [$("ecB-ga"), $("ecB-gb")];
    for (const el of [l1, l2, wm, ...glows]) el.style.opacity = "0";

    tl.fromTo(glows, { opacity: 0 }, { opacity: 1, duration: 0.75, ease: "power1.inOut", immediateRender: false }, t0 - 0.03);

    l1.style.transformOrigin = "0% 70%";
    tl.fromTo(l1, { scale: 1.28, filter: "blur(16px)", opacity: 0 }, { scale: 1, filter: "blur(0px)", opacity: 1, duration: 0.42, ease: "power4.out", immediateRender: false }, t0 + 0.02);
    tl.set(l1, { filter: "none" }, t0 + 0.45);

    tl.fromTo(l2, { x: 0.32 * W, opacity: 0 }, { x: 0, opacity: 1, duration: 0.42, ease: "expo.out", immediateRender: false }, t0 + R.BEAT / 2);

    R.drawOn(tl, $("ecB-ell"), R.bt(59), 0.42);
    R.drawOn(tl, $("ecB-arrow"), R.bt(60), 0.26);
    R.drawOn(tl, $("ecB-head"), R.bt(60) + 0.24, 0.09, "power1.out");

    tl.fromTo(wm, { y: 36, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: "power3.out", immediateRender: false }, R.bt(60));
    tag.style.clipPath = "inset(0 100% 0 0)";
    tl.fromTo(tag, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.3, ease: "power2.out", immediateRender: false }, R.bt(60) + 0.12);
    tl.set(tag, { clipPath: "none" }, R.bt(60) + 0.43);
  };
})();
