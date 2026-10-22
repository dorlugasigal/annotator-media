/* Shared helpers for the Annotator reel. Deterministic: no clocks, seeded noise only. */
(function () {
  const R = (window.R = window.R || {});
  R.BPM = 130; // "Product Launch Advertising Commercial Music" by lNPLUSMUSIC (Pixabay); keep in sync with tools/shots.py
  R.BEAT = 60 / R.BPM;
  R.bt = (n) => (n - 1) * R.BEAT; // start of beat n (1-based)
  R.$ = (id) => document.getElementById(id);

  R.C = {
    night: "#0b101a", desk: "#1d202d", ink: "#f1f4fc", muted: "#b8c3d8",
    apricot: "#ffb58c", peri: "#abc7ff", teal: "#61919d", tealLight: "#8fc3cc",
    blue: "#5c71d7", blueLight: "#9aa8f2", lagoon: "#3d4c7f", lagoonTeal: "#80c2ba",
    yellow: "#edfa56", surface: "#151e2d",
  };

  R.mulberry32 = function (seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  const f = (n) => (Math.round(n * 100) / 100).toString();
  R.f = f;

  /** Catmull-Rom spline through points, emitted as cubic Béziers. */
  R.smoothPath = function (pts) {
    let d = `M${f(pts[0][0])} ${f(pts[0][1])}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C${f(c1[0])} ${f(c1[1])} ${f(c2[0])} ${f(c2[1])} ${f(p2[0])} ${f(p2[1])}`;
    }
    return d;
  };

  /** Hand-drawn ellipse: ~1.1 turns with a gentle wobble; the second pass drifts outward. */
  R.roughEllipse = function (cx, cy, rx, ry, rotDeg, seed, o = {}) {
    const rnd = R.mulberry32(seed);
    const turns = o.turns ?? 1.12, start = o.start ?? -2.55, n = o.n ?? 80;
    const ph1 = rnd() * 6.283, ph2 = rnd() * 6.283, wob = o.wobble ?? 0.022, drift = o.drift ?? 0.07;
    const rot = (rotDeg * Math.PI) / 180, cr = Math.cos(rot), sr = Math.sin(rot);
    const pts = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n, a = start + u * turns * Math.PI * 2;
      const k = 1 + wob * Math.sin(2 * a + ph1) + wob * 0.6 * Math.sin(3 * a + ph2) + drift * (u - 0.45);
      const x = rx * k * Math.cos(a), y = ry * k * Math.sin(a);
      pts.push([cx + x * cr - y * sr, cy + x * sr + y * cr]);
    }
    return R.smoothPath(pts);
  };

  R.cubicPt = function (p0, c1, c2, p3, t) {
    const u = 1 - t;
    return [
      u * u * u * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * p3[0],
      u * u * u * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * p3[1],
    ];
  };
  R.cubic = (p0, c1, c2, p3) =>
    `M${f(p0[0])} ${f(p0[1])} C${f(c1[0])} ${f(c1[1])} ${f(c2[0])} ${f(c2[1])} ${f(p3[0])} ${f(p3[1])}`;

  /** Open chevron arrowhead at `tip`, aligned with the direction from `from`. */
  R.arrowHead = function (tip, from, len, spreadDeg = 30) {
    const a = Math.atan2(tip[1] - from[1], tip[0] - from[0]), s = (spreadDeg * Math.PI) / 180;
    const l = [tip[0] - len * Math.cos(a - s), tip[1] - len * Math.sin(a - s)];
    const r = [tip[0] - len * Math.cos(a + s), tip[1] - len * Math.sin(a + s)];
    return `M${f(l[0])} ${f(l[1])} L${f(tip[0])} ${f(tip[1])} L${f(r[0])} ${f(r[1])}`;
  };

  /** A loose hand-drawn line across x0..x1 with a few waves. */
  R.wavy = function (x0, x1, y, amp, waves, seed, tilt = 0) {
    const rnd = R.mulberry32(seed), n = 28, pts = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n;
      const x = x0 + (x1 - x0) * u;
      const yy = y + amp * Math.sin(u * waves * Math.PI * 2 + 0.6) + (rnd() - 0.5) * amp * 0.25 + tilt * (u - 0.5);
      pts.push([x, yy]);
    }
    return R.smoothPath(pts);
  };

  /** Rounded rectangle path (arcs; MorphSVG converts them). */
  R.roundRect = function (x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    return `M${f(x + r)} ${f(y)} H${f(x + w - r)} A${f(r)} ${f(r)} 0 0 1 ${f(x + w)} ${f(y + r)} V${f(y + h - r)} ` +
      `A${f(r)} ${f(r)} 0 0 1 ${f(x + w - r)} ${f(y + h)} H${f(x + r)} A${f(r)} ${f(r)} 0 0 1 ${f(x)} ${f(y + h - r)} ` +
      `V${f(y + r)} A${f(r)} ${f(r)} 0 0 1 ${f(x + r)} ${f(y)} Z`;
  };

  /** Hand-drawn box: ~1.1 laps with bowed edges and a little drift, like a quick pen scribble. */
  R.roughBox = function (x, y, w, h, seed, o = {}) {
    const rnd = R.mulberry32(seed), laps = o.laps ?? 1.12, n = o.n ?? 44, jit = o.jitter ?? 0.035;
    const corners = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
    const normals = [[0, -1], [1, 0], [0, 1], [-1, 0]];
    const size = Math.min(w, h), total = Math.round(n * laps), pts = [];
    for (let i = 0; i <= total; i++) {
      const s = (i / n) * 4 + 0.18, k = Math.floor(s) % 4, u = s - Math.floor(s);
      const a = corners[k], b = corners[(k + 1) % 4], nrm = normals[k];
      const out = Math.sin(u * Math.PI) * size * 0.06 + (i / total) * size * 0.1;
      pts.push([
        a[0] + (b[0] - a[0]) * u + nrm[0] * out + (rnd() - 0.5) * size * jit,
        a[1] + (b[1] - a[1]) * u + nrm[1] * out + (rnd() - 0.5) * size * jit,
      ]);
    }
    return R.smoothPath(pts);
  };

  /* ---------- Type ---------- */
  const ctx = document.createElement("canvas").getContext("2d");
  R.FONT = '"Bricolage Grotesque"';
  R.measure = function (text, px, weight, lsEm = -0.05, family = R.FONT) {
    ctx.font = `${weight} ${px}px ${family}`;
    ctx.letterSpacing = `${lsEm * px}px`;
    const m = ctx.measureText(text);
    return {
      w: m.width, asc: m.actualBoundingBoxAscent, desc: m.actualBoundingBoxDescent,
      l: m.actualBoundingBoxLeft, r: m.actualBoundingBoxRight,
      fa: m.fontBoundingBoxAscent, fd: m.fontBoundingBoxDescent,
    };
  };
  /** Largest size <= max whose advance width fits maxW. */
  R.fit = function (text, max, maxW, weight, lsEm = -0.05) {
    const w100 = R.measure(text, 100, weight, lsEm).w;
    return Math.min(max, Math.floor((maxW / w100) * 100));
  };
  /**
   * Place a .word at left x with its alphabetic baseline at y (line-height 1).
   * Returns ink metrics in frame pixels: left/right/top/bottom and width.
   */
  R.placeWord = function (el, o) {
    const weight = o.weight ?? 760, ls = o.ls ?? -0.05, family = o.family ?? R.FONT;
    const m = R.measure(o.text ?? el.textContent, o.fs, weight, ls, family);
    // With line-height 1 the alphabetic baseline sits at top + (fs + ascent - descent) / 2.
    const x = o.align === "center" ? o.x - m.w / 2 : o.align === "right" ? o.x - m.w : o.x;
    Object.assign(el.style, {
      left: `${x}px`, top: `${o.y - (o.fs + m.fa - m.fd) / 2}px`, fontSize: `${o.fs}px`,
      fontWeight: String(weight), letterSpacing: `${ls}em`, fontFamily: family === R.FONT ? "" : family,
    });
    if (o.color) el.style.color = o.color;
    return { x, y: o.y, w: m.w, left: x - m.l, right: x + m.r, top: o.y - m.asc, bottom: o.y + m.desc, asc: m.asc, desc: m.desc, fs: o.fs };
  };
  R.placeMono = function (el, o) {
    const fam = '"JetBrains Mono"';
    const m = R.measure(el.textContent.toUpperCase(), o.fs, 700, 0.16, fam);
    Object.assign(el.style, { left: `${o.x}px`, top: `${o.y - (o.fs + m.fa - m.fd) / 2}px`, fontSize: `${o.fs}px` });
    if (o.color) el.style.color = o.color;
    return { x: o.x, w: m.w };
  };

  /* ---------- SVG draw-on ---------- */
  R.setD = (el, d) => { el.setAttribute("d", d); return el; };
  R.stroke = (el, color, width) => { el.style.stroke = color; el.style.strokeWidth = String(width); return el; };
  /** Prepare a path for a draw-on; returns its length (padded so the end never clips). */
  R.dash = function (el) {
    const len = Math.ceil(el.getTotalLength() * 1.02) + 2;
    el.style.strokeDasharray = `${len}`;
    el.style.strokeDashoffset = `${len}`;
    return len;
  };
  /** Draw-on tween that ends with the dash removed, so the finished mark is a plain stroke. */
  R.drawOn = function (tl, el, t, dur, ease = "power2.out") {
    const len = R.dash(el);
    tl.fromTo(el, { strokeDashoffset: len, strokeDasharray: `${len}` }, { strokeDashoffset: 0, duration: dur, ease, immediateRender: false }, t);
    tl.set(el, { strokeDasharray: "none" }, t + dur);
    return len;
  };

  /* Directional blur proxies (SVG feGaussianBlur on one axis). */
  R.blurProxy = function (nodeId) {
    const node = R.$(nodeId), p = { v: 0 };
    const write = () => node.setAttribute("stdDeviation", `${p.v.toFixed(2)} 0`);
    write();
    return { p, write };
  };
})();
