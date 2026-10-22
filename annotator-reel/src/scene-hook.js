/* Hook (bar 1) and the shared end-card builder. */
(function () {
  const R = window.R;

  /** Lay out one end-card copy. ecA (frame 0) and ecB (last frame) use this same function. */
  R.buildEndCard = function (p) {
    const L = R.L.ec, C = R.C, $ = R.$;
    const fs = R.fit("Draw over", L.maxFs, L.maxW, 700, -0.05);
    const l1 = R.placeWord($(`${p}-l1`), { x: L.x, y: L.b1, fs, weight: 700, color: C.ink });
    const l2 = R.placeWord($(`${p}-l2`), { x: L.x, y: L.b2, fs, weight: 700, color: C.peri });
    const wm = R.placeWord($(`${p}-wm`), { x: L.wmRight, y: L.wmBase, fs: L.wmFs, weight: 760, align: "right", color: C.ink });
    $(`${p}-wm`).querySelector(".ec-dot").style.color = C.apricot;
    R.placeMono($(`${p}-tag`), { x: L.tagX, y: L.tagBase, fs: L.tagFs, color: C.muted });

    for (const [id, g, rgba] of [[`${p}-ga`, L.glowA, "171,199,255,0.2"], [`${p}-gb`, L.glowB, "255,181,140,0.11"]]) {
      Object.assign($(id).style, {
        left: `${g.x}px`, top: `${g.y}px`, width: `${g.w}px`, height: `${g.h}px`,
        background: `radial-gradient(closest-side, rgba(${rgba}), rgba(${rgba.replace(/[\d.]+$/, "0")}))`,
      });
    }

    const k = fs / 250;
    const cx = (l2.left + l2.right) / 2, cy = (l2.top + l2.bottom) / 2 + 4 * k;
    const rx = (l2.right - l2.left) / 2 + 66 * k, ry = (l2.bottom - l2.top) / 2 + 62 * k;
    const ell = R.setD($(`${p}-ell`), R.roughEllipse(cx, cy, rx, ry, -3, 7));
    R.stroke(ell, C.apricot, Math.max(7, 10.5 * k));

    const start = [wm.left - 34 * (L.wmFs / 64), L.wmBase - 30 * (L.wmFs / 64)];
    const end = [cx + rx * 0.9, cy + ry * 0.62];
    const c1 = [start[0] + 8, start[1] - 150 * k], c2 = [end[0] + 190 * k, end[1] + 8 * k];
    R.stroke(R.setD($(`${p}-arrow`), R.cubic(start, c1, c2, end)), C.apricot, Math.max(6, 8 * k));
    const pre = R.cubicPt(start, c1, c2, end, 0.93);
    R.stroke(R.setD($(`${p}-head`), R.arrowHead(end, pre, 36 * k, 32)), C.apricot, Math.max(6, 8 * k));
    return { fs, l1, l2, wm, cx, cy, rx, ry };
  };

  R.sceneHook = function (tl) {
    const $ = R.$, C = R.C, W = R.W, L = R.L, f = R.f;
    const g = R.buildEndCard("ecA");

    /* Beat 1 — dive through the apricot ellipse; the iris is the ellipse's own interior. */
    const inA = $("ecA-in"), inD = $("hkDraw-in");
    inA.style.transformOrigin = `${f(g.cx)}px ${f(g.cy)}px`;
    const expoIn = gsap.parseEase("expo.in");
    const dive = { p: 0 };
    const writeDive = () => {
      const q = dive.p, sc = 1 + 8 * expoIn(q);
      inA.style.transform = `scale(${sc.toFixed(4)})`;
      inA.style.filter = `blur(${(10 * expoIn(q)).toFixed(2)}px)`;
      const fill = Math.min(1, Math.max(0, (q - 0.18) / 0.4));
      const kk = sc * fill * fill * (1 - 0.06 * (1 - fill));
      inD.style.clipPath = `ellipse(${f(g.rx * kk)}px ${f(g.ry * kk)}px at ${f(g.cx)}px ${f(g.cy)}px)`;
    };
    writeDive();
    R.writers.push(writeDive);
    tl.fromTo(dive, { p: 0 }, { p: 1, duration: R.BEAT - 0.075, ease: "none", onUpdate: writeDive, immediateRender: false }, 0.06);

    /* Beat 2 — "Draw" slams on apricot; navy underline on the offbeat. */
    const hd = L.hook.draw;
    const fsD = R.fit("Draw", hd.max, hd.maxW, 800, -0.055);
    const wD = $("hk-draw-w");
    const d = R.placeWord(wD, { x: W / 2, y: hd.y, fs: fsD, weight: 800, ls: -0.055, align: "center", color: C.night });
    wD.style.transformOrigin = "50% 62%";
    wD.style.opacity = "0";
    tl.fromTo(wD, { scale: 1.5, filter: "blur(18px)", opacity: 0 }, { scale: 1, filter: "blur(0px)", opacity: 1, duration: 0.36, ease: "power4.out", immediateRender: false }, R.bt(2));
    tl.fromTo(wD, { scale: 1 }, { scale: 1.045, duration: 0.11, ease: "none", immediateRender: false }, R.bt(2) + 0.36);
    const ul = R.setD($("hk-draw-ul"), R.wavy(d.left - 0.02 * fsD, d.right + 0.03 * fsD, d.bottom + 0.1 * fsD, 0.018 * fsD, 2.3, 11, -0.02 * fsD));
    R.stroke(ul, C.night, 0.03 * fsD);
    R.drawOn(tl, ul, R.bt(2) + R.BEAT / 2, 0.2);

    /* Beat 3 — "over" snaps in from the right with a directional streak; an arrow arcs over it. */
    const ho = L.hook.over;
    const fsO = R.fit("over", ho.max, ho.maxW, 800, -0.055);
    const wO = $("hk-over-w");
    const o = R.placeWord(wO, { x: W / 2, y: ho.y, fs: fsO, weight: 800, ls: -0.055, align: "center", color: C.night });
    wO.style.filter = "url(#oblur)";
    const ob = R.blurProxy("oblur-n");
    R.writers.push(ob.write);
    tl.fromTo(wO, { x: 0.55 * W }, { x: 0, duration: 0.3, ease: "expo.out", immediateRender: false }, R.bt(3));
    tl.fromTo(ob.p, { v: 40 }, { v: 0, duration: 0.3, ease: "expo.out", onUpdate: ob.write, immediateRender: false }, R.bt(3));
    const ow = o.right - o.left;
    const a0 = [o.left + 0.02 * ow, o.top - 0.05 * fsO], a3 = [o.right - 0.01 * ow, o.top - 0.02 * fsO];
    const ac1 = [o.left + ow * 0.18, o.top - 0.6 * fsO], ac2 = [o.left + ow * 0.86, o.top - 0.62 * fsO];
    R.stroke(R.setD($("hk-over-arc"), R.cubic(a0, ac1, ac2, a3)), C.night, 0.028 * fsO);
    R.stroke(R.setD($("hk-over-head"), R.arrowHead(a3, R.cubicPt(a0, ac1, ac2, a3, 0.9), 0.085 * fsO, 34)), C.night, 0.028 * fsO);
    R.drawOn(tl, $("hk-over-arc"), R.bt(3) + 0.07, 0.24);
    R.drawOn(tl, $("hk-over-head"), R.bt(3) + 0.3, 0.08, "power1.out");

    /* Beat 4 — "any app." is cut out of the night; the real dashboard take shows through. */
    const ha = L.hook.any;
    const fsA = R.fit("any app.", ha.max, ha.maxW, 800, -0.05);
    const mA = R.measure("any app.", fsA, 800, -0.05);
    const x0 = W / 2 - mA.w / 2, y0 = ha.y;
    for (const id of ["hk-any-mtext", "hk-any-otext"]) {
      const t = $(id);
      t.setAttribute("x", f(x0)); t.setAttribute("y", f(y0));
      t.setAttribute("font-size", f(fsA)); t.setAttribute("font-weight", "800");
      t.setAttribute("letter-spacing", f(-0.05 * fsA));
      t.style.fontFamily = "Bricolage Grotesque";
    }
    const px = x0 + R.measure("any a", fsA, 800, -0.05).w + 0.105 * fsA, py = y0 - 0.2 * fsA;
    const gA = $("hk-any-g"), svgA = $("hk-any-svg");
    const origin = `${f(px)} ${f(py)}`;
    tl.fromTo(gA, { scale: 1.08, svgOrigin: origin }, { scale: 1, svgOrigin: origin, duration: 0.22, ease: "power3.out", immediateRender: false }, R.bt(4));
    tl.fromTo(gA, { scale: 1, svgOrigin: origin }, { scale: 64, svgOrigin: origin, duration: R.BEAT / 2, ease: "expo.in", immediateRender: false }, R.bt(4) + R.BEAT / 2);
    tl.fromTo(svgA, { filter: "blur(0px)" }, { filter: "blur(6px)", duration: R.BEAT / 2, ease: "expo.in", immediateRender: false }, R.bt(4) + R.BEAT / 2);

  };
})();
