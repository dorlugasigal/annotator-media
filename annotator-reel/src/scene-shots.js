/* Real product shots: beat-synced captions whose marks act out the words, and the three cuts.
   Every caption lines up with the native action in the take underneath it (tools/shots.py). */
(function () {
  const R = window.R;

  R.sceneShots = function (tl) {
    const $ = R.$, C = R.C, L = R.L, W = R.W, H = R.H, f = R.f, bt = R.bt, B = R.BEAT;
    // Beat offsets inside each shot (tools/shots.py BEATS): dashboard from beat 4, smart 30, focus 42.
    const D = (k) => bt(4) + k * B, S = (k) => bt(30) + k * B, F = (k) => bt(42) + k * B;
    /** Virtual-camera pose of a shot at reel time t (tools/camera.py writes one per frame). */
    const poseAt = (shot, t) => {
      const P = R.POSES[shot], n = Math.round((t - P.start) * P.fps);
      const q = P.frames[Math.max(0, Math.min(P.frames.length - 1, n))];
      return { cx: q[0], cy: q[1], z: q[2] };
    };
    const WEIGHT = 720, LS = -0.04, GAP = 0.09, PADX = 0.36, TOP = 0.9, BOTTOM = 0.34, RAD = 0.24, RISE = 1.0;
    const MARGIN = L.cap.slots.bl.x;
    const CYAN = "#14ccd6"; // the take's cursor halo colour
    const THEME = {
      night: { slab: C.night, text: C.ink, mark: C.apricot, edge: "rgba(171, 199, 255, 0.24)" },
      apricot: { slab: C.apricot, text: C.night, mark: C.night, edge: "rgba(255, 255, 255, 0.4)" },
      peri: { slab: C.peri, text: C.night, mark: C.night, edge: "rgba(255, 255, 255, 0.45)" },
    };
    const hidden = (...els) => els.forEach((el) => (el.style.opacity = "0"));

    /* ---------- caption primitives ---------- */
    function slabProxy(id, T, rect) {
      const el = $(`${id}-slab`), box = $(`${id}-box`);
      el.style.background = T.slab;
      el.style.boxShadow = `inset 0 0 0 2px ${T.edge}, 0 26px 60px -26px rgba(3, 5, 12, 0.7)`;
      const g = { x: rect.x, y: rect.y, w: 0, h: rect.h, r: rect.r };
      const write = () => {
        const w = Math.max(0, g.w), r = Math.min(g.r, w / 2, g.h / 2), s = el.style;
        s.left = `${f(g.x)}px`; s.top = `${f(g.y)}px`; s.width = `${f(w)}px`; s.height = `${f(g.h)}px`;
        s.borderRadius = `${f(r)}px`;
        box.style.clipPath = `inset(${f(g.y)}px ${f(W - g.x - w)}px ${f(H - g.y - g.h)}px ${f(g.x)}px round ${f(r)}px)`;
      };
      write();
      R.writers.push(write);
      return { g, write };
    }

    function caption(id, words, slotName, themeName) {
      const slot = L.cap.slots[slotName], T = THEME[themeName], full = words.join(" ");
      // Display tracking is tight, so words get extra air (GAP em) on top of the space.
      const slabW = (size) => R.measure(full, size, WEIGHT, LS).w + (words.length - 1) * GAP * size + 2 * PADX * size;
      let fs = L.cap.fs;
      if (slabW(fs) > W - 2 * MARGIN) fs = Math.floor((fs * (W - 2 * MARGIN)) / slabW(fs));
      const w = slabW(fs), x = slot.align === "right" ? slot.x - w : slot.x, x0 = x + PADX * fs;
      const placed = words.map((word, i) => {
        const wx = i === 0 ? x0 : x0 + R.measure(`${words.slice(0, i).join(" ")} `, fs, WEIGHT, LS).w + i * GAP * fs;
        return R.placeWord($(`${id}-w${i}`), { text: word, x: wx, y: slot.base, fs, weight: WEIGHT, ls: LS, color: T.text });
      });
      const rect = { x, y: slot.base - TOP * fs, w, h: (TOP + BOTTOM) * fs, r: RAD * fs };
      const c = {
        id, fs, T, rect, x0, base: slot.base, words: placed, right: slot.align === "right", el: $(id),
        // Marks go towards the frame centre: above bottom slots, below top slots.
        d: slot.base > H / 2 ? -1 : 1,
        groups: words.map((_, i) => [$(`${id}-w${i}`)]),
      };
      c.slab = slabProxy(id, T, rect);
      c.edge = c.d < 0 ? rect.y : rect.y + rect.h; // slab edge that faces the frame centre
      return c;
    }
    const copyWord = (c, i, id, color) =>
      R.placeWord($(id), { text: $(id).textContent, x: c.words[i].x, y: c.base, fs: c.fs, weight: WEIGHT, ls: LS, color });

    function wordsIn(c, t, o = {}) {
      const dur = o.dur ?? 0.34, stagger = o.stagger ?? 0.045;
      c.groups.forEach((g, i) => tl.fromTo(g, { y: RISE * c.fs }, { y: 0, duration: dur, ease: "power4.out", immediateRender: false }, t + i * stagger));
    }
    function wordsOut(c, t) {
      c.groups.forEach((g, i) => tl.fromTo(g, { y: 0 }, { y: -RISE * c.fs, duration: 0.12, ease: "power3.in", immediateRender: false }, t + i * 0.02));
    }
    function capIn(c, t) {
      const r = c.rect;
      tl.fromTo(c.slab.g, { x: c.right ? r.x + r.w : r.x, w: 0 }, { x: r.x, w: r.w, duration: 0.28, ease: "power4.out", onUpdate: c.slab.write, immediateRender: false }, t);
      wordsIn(c, t + 0.04);
    }
    function capOut(c, t) {
      const r = c.rect;
      wordsOut(c, t);
      tl.fromTo(c.slab.g, { x: r.x, w: r.w }, { x: c.right ? r.x : r.x + r.w, w: 0, duration: 0.2, ease: "power3.in", onUpdate: c.slab.write, immediateRender: false }, t + 0.05);
    }
    /** `a` hands its slot to `b` at t: a's words leave upward, b's slab reshapes from a's, b's words rise. */
    function swap(a, b, t, o = {}) {
      wordsOut(a, t - 0.16);
      const ra = a.rect, rb = b.rect;
      tl.fromTo(b.slab.g, { x: ra.x, y: ra.y, w: ra.w, h: ra.h }, { x: rb.x, y: rb.y, w: rb.w, h: rb.h, duration: o.slab ?? 0.26, ease: "power3.inOut", onUpdate: b.slab.write, immediateRender: false }, t);
      wordsIn(b, t + 0.02, o);
    }
    const fadeOut = (els, t, dur = 0.12) => tl.fromTo(els, { opacity: 1 }, { opacity: 0, duration: dur, ease: "none", immediateRender: false }, t);

    /* ================= Dashboard (beats 4-29): toolbar tour, then the marks ================= */

    /* Toolbar tour (beats 5-11): the camera glides along the real toolbar; labels are pinned to the footage
       on a layer that follows the virtual camera frame by frame. */
    {
      const world = $("tour-world"), fsSrc = L.tour.fs, stroke = L.tour.stroke;
      const writeWorld = () => {
        const p = poseAt("dashboard", tl.time());
        world.style.transform = `translate(${f(W / 2 - p.cx * p.z)}px, ${f(H / 2 - p.cy * p.z)}px) scale(${p.z.toFixed(5)})`;
      };
      writeWorld();
      R.writers.push(writeWorld);
      const groups = [
        { text: "Tool library", x0: 2148, x1: 2148, row: 0 },
        { text: "Effects", x0: 2048, x1: 2048, row: 1 },
        { text: "Pen, text and highlighter", x0: 1643, x1: 1828, row: 0 },
        { text: "Arrows and lines", x0: 1442, x1: 1534, row: 1 },
        { text: "Shapes", x0: 1166, x1: 1350, row: 0 },
      ];
      const Y0 = 1688, BASE = [1748, 1812], half = 38, fade = D(7.72);
      let last = D(2.0);
      groups.forEach((g, i) => {
        // Show each group once the glide brings it into the middle of the frame, on a half beat.
        let t = D(2.05);
        for (let k = 2.05; k < 7.3; k += 0.02) {
          const p = poseAt("dashboard", D(k));
          if (Math.abs((g.x0 + g.x1) / 2 - p.cx) * p.z < 0.36 * W) { t = D(k); break; }
        }
        t = Math.max(last + B / 2, bt(1) + Math.ceil((t - bt(1)) / (B / 2)) * (B / 2));
        last = t;
        const cx = (g.x0 + g.x1) / 2, base = BASE[g.row];
        const d = `M${g.x0 - half} ${Y0 - 14} V${Y0} H${g.x1 + half} V${Y0 - 14} M${cx} ${Y0} V${base - fsSrc * 0.95}`;
        const path = R.stroke(R.setD($(`tb${i}`), d), C.apricot, stroke);
        path.setAttribute("vector-effect", "non-scaling-stroke");
        R.drawOn(tl, path, t, 0.24);
        const el = $(`tl${i}`);
        R.placeWord(el, { text: g.text, x: cx, y: base, fs: fsSrc, weight: 640, ls: -0.01, align: "center", color: C.ink });
        tl.fromTo(el, { y: 0.6 * fsSrc, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: "power3.out", immediateRender: false }, t + 0.06);
        hidden(el);
        fadeOut([path, el], fade, 0.2);
      });
    }

    /* Circle it. — an apricot ellipse circles the word while the real teal one circles the KPI. */
    const c1 = caption("c1", ["Circle", "it."], "bl", "night");
    capIn(c1, D(8.85));
    {
      const w = c1.words[0], fs = c1.fs;
      const cx = (w.left + w.right) / 2, cy = (w.top + w.bottom) / 2 + 0.02 * fs;
      const el = R.setD($("c1-m0"), R.roughEllipse(cx, cy, (w.right - w.left) / 2 + 0.2 * fs, (w.bottom - w.top) / 2 + 0.22 * fs, -3, 31));
      R.stroke(el, c1.T.mark, 0.065 * fs);
      R.drawOn(tl, el, D(9.05), 1.65 * B); // with the real ellipse drag
      fadeOut(el, D(10.9));
    }
    capOut(c1, D(10.9)); // clear the frame before the camera pulls back to the toolbar

    /* Point at it. — an arrow lands on "it." as the real arrow points are placed. */
    const c2 = caption("c2", ["Point", "at", "it."], "br", "night");
    capIn(c2, D(15.1));
    {
      const w = c2.words[2], fs = c2.fs, d = c2.d;
      const end = [(w.left + w.right) / 2 + 0.02 * fs, d < 0 ? w.top - 0.14 * fs : w.bottom + 0.18 * fs];
      const start = [w.left - 1.35 * fs, c2.edge + d * 0.9 * fs];
      const k1 = [start[0] + 0.62 * fs, start[1] + d * 0.3 * fs], k2 = [end[0], end[1] + d * 0.62 * fs];
      const shaftD = R.cubic(start, k1, k2, end), headD = R.arrowHead(end, R.cubicPt(start, k1, k2, end, 0.88), 0.24 * fs, 32);
      // Navy under-strokes keep apricot ink readable over the light sample app.
      for (const [id, dd, color, width] of [["c2-u0", shaftD, C.night, 0.15 * fs], ["c2-u1", headD, C.night, 0.15 * fs], ["c2-m0", shaftD, c2.T.mark, 0.075 * fs], ["c2-m1", headD, c2.T.mark, 0.075 * fs]]) {
        R.stroke(R.setD($(id), dd), color, width);
      }
      for (const id of ["c2-u0", "c2-m0"]) R.drawOn(tl, $(id), D(15.95), 0.3);
      for (const id of ["c2-u1", "c2-m1"]) R.drawOn(tl, $(id), D(15.95) + 0.28, 0.08, "power1.out");
    }

    /* Bend it. — the arrow above the words bends with the real edit drag. */
    const c3 = caption("c3", ["Bend", "it."], "br", "night");
    swap(c2, c3, D(17.8));
    {
      const fs = c3.fs, d = c3.d, y = c3.edge + d * 0.36 * fs;
      const a = [c3.words[0].left + 0.02 * fs, y], b = [c3.words[1].right, y];
      const shafts = [R.stroke($("c3-u0"), C.night, 0.15 * fs), R.stroke($("c3-m0"), c3.T.mark, 0.075 * fs)];
      const heads = [R.stroke($("c3-u1"), C.night, 0.15 * fs), R.stroke($("c3-m1"), c3.T.mark, 0.075 * fs)];
      const bend = { p: 0 };
      const writeBend = () => {
        const k = d * 0.8 * fs * bend.p, len = b[0] - a[0];
        const k1 = [a[0] + len * 0.28, a[1] + k], k2 = [a[0] + len * 0.72, b[1] + k];
        const sd = R.cubic(a, k1, k2, b), hd = R.arrowHead(b, R.cubicPt(a, k1, k2, b, 0.88), 0.24 * fs, 32);
        for (const el of shafts) el.setAttribute("d", sd);
        for (const el of heads) el.setAttribute("d", hd);
      };
      writeBend();
      R.writers.push(writeBend);
      for (const el of shafts) R.drawOn(tl, el, D(17.85), 0.16);
      hidden(...heads);
      tl.fromTo(heads, { opacity: 0 }, { opacity: 1, duration: 0.05, ease: "none", immediateRender: false }, D(17.85) + 0.13);
      tl.fromTo(bend, { p: 0 }, { p: 1, duration: D(19.5) - D(18.0), ease: "power1.inOut", onUpdate: writeBend, immediateRender: false }, D(18.0)); // with the real drag
      fadeOut([...shafts, ...heads], D(19.8));
    }
    capOut(c3, D(19.8));

    /* Highlight it. — a highlighter pass reveals the word in night ink, in step with the real drag. */
    const c4 = caption("c4", ["Highlight", "it."], "bl", "night");
    {
      const w = c4.words[0], fs = c4.fs;
      copyWord(c4, 0, "c4-w0h", C.night);
      c4.groups[0].push($("c4-w0h"));
      const hl = $("c4-hl"), hx = w.left - 0.07 * fs, hw = w.right - w.left + 0.14 * fs;
      Object.assign(hl.style, { left: `${f(hx)}px`, top: `${f(c4.base - 0.66 * fs)}px`, width: `${f(hw)}px`, height: `${f(0.76 * fs)}px`, borderRadius: `${f(0.08 * fs)}px` });
      const pass = { p: 0 };
      const dark = $("c4-w0h");
      const writePass = () => {
        hl.style.transform = `scaleX(${pass.p.toFixed(4)})`;
        dark.style.clipPath = `inset(-50% ${f(Math.max(0, w.w - (hx + hw * pass.p - w.x)))}px -50% -10%)`;
      };
      writePass();
      R.writers.push(writePass);
      tl.fromTo(pass, { p: 0 }, { p: 1, duration: D(24) - D(22.25), ease: "power1.inOut", onUpdate: writePass, immediateRender: false }, D(22.25)); // with the real drag
    }
    capIn(c4, D(21.6));

    /* ---- Cut 1 (beat 30): whip. The camera streaks left, so type and ink streak right. ---- */
    const wa = R.blurProxy("wblur-a-n"), wb = R.blurProxy("wblur-b-n");
    R.writers.push(wa.write, wb.write);
    tl.set(c4.el, { filter: "url(#wblur-a)" }, bt(30) - 0.2);
    tl.fromTo(c4.el, { x: 0 }, { x: 0.9 * W, duration: 0.2, ease: "power3.in", immediateRender: false }, bt(30) - 0.2);
    tl.fromTo(wa.p, { v: 0 }, { v: 44, duration: 0.2, ease: "power3.in", onUpdate: wa.write, immediateRender: false }, bt(30) - 0.2);
    {
      const sw = $("swoosh-p");
      R.setD(sw, R.wavy(-260, W + 260, L.swoosh.y, L.swoosh.amp, 1.1, 9, -60));
      R.stroke(sw, C.apricot, 0.16 * L.cap.fs);
      const len = sw.getTotalLength(), seg = 0.36 * len;
      sw.style.strokeDasharray = `${f(seg)} ${f(len + seg)}`;
      sw.style.strokeDashoffset = `${f(seg)}`;
      tl.fromTo(sw, { strokeDashoffset: seg }, { strokeDashoffset: -len, duration: 0.4, ease: "power2.inOut", immediateRender: false }, bt(30) - 0.185);
    }

    /* ================= Smart Draw (beats 30-41) ================= */

    /* Draw it rough. — flies in with the whip; a scribble draws with the real pen stroke. */
    const c5 = caption("c5", ["Draw", "it", "rough."], "br", "apricot");
    tl.set(c5.slab.g, { x: c5.rect.x, w: c5.rect.w }, S(0.35));
    tl.set(c5.el, { filter: "url(#wblur-b)" }, S(0.35));
    tl.fromTo(c5.el, { x: -0.7 * W }, { x: 0, duration: 0.36, ease: "expo.out", immediateRender: false }, S(0.35));
    tl.fromTo(wb.p, { v: 44 }, { v: 0, duration: 0.36, ease: "expo.out", onUpdate: wb.write, immediateRender: false }, S(0.35));
    tl.set(c5.el, { filter: "none" }, S(0.35) + 0.38);
    const rw = c5.words[2], fs5 = c5.fs;
    const roughD = R.roughBox(rw.left - 0.14 * fs5, rw.top - 0.2 * fs5, rw.right - rw.left + 0.28 * fs5, rw.bottom - rw.top + 0.4 * fs5, 17);
    {
      const el = R.stroke(R.setD($("c5-m0"), roughD), c5.T.mark, 0.05 * fs5);
      R.drawOn(tl, el, S(1.25), S(3.95) - S(1.25), "power1.inOut"); // with the real pen stroke
    }

    /* It snaps clean. — on the real snap the scribble morphs into a clean box around "clean." */
    const c6 = caption("c6", ["It", "snaps", "clean."], "br", "apricot");
    swap(c5, c6, S(3.8), { dur: 0.2, stagger: 0.02, slab: 0.18 });
    const m6 = R.stroke(R.setD($("c6-m0"), roughD), c6.T.mark, 0.05 * c6.fs);
    {
      const w = c6.words[2], fs = c6.fs;
      const cleanD = R.roundRect(w.left - 0.16 * fs, w.top - 0.18 * fs, w.right - w.left + 0.32 * fs, w.bottom - w.top + 0.36 * fs, 0.12 * fs);
      tl.to(m6, { morphSVG: cleanD, duration: 0.2, ease: "expo.out" }, S(3.97)); // the real snap lands on S(4.0)
      const cx = c6.rect.x + c6.rect.w / 2, cy = c6.rect.y + c6.rect.h / 2;
      c6.el.style.transformOrigin = `${f(cx)}px ${f(cy)}px`;
      tl.fromTo(c6.el, { scale: 1.05 }, { scale: 1, duration: 0.26, ease: "power3.out", immediateRender: false }, S(4.0));
    }

    /* Add a note. — the slab becomes an empty text box and grows as the real label is typed. */
    const c7 = caption("c7", ["Add a note."], "br", "apricot");
    {
      const r7 = c7.rect, fs = c7.fs, text = "Add a note.", caret = $("c7-caret");
      const boxW = (n) => 2 * PADX * fs + (n ? R.measure(text.slice(0, n), fs, WEIGHT, LS).w : 0) + 0.1 * fs;
      wordsOut(c6, S(6.9) - 0.16);
      fadeOut(m6, S(6.9) - 0.14, 0.1);
      tl.fromTo(c7.slab.g, { x: c6.rect.x, y: c6.rect.y, w: c6.rect.w, h: c6.rect.h }, { x: r7.x, y: r7.y, w: boxW(0), h: r7.h, duration: 0.2, ease: "power3.inOut", onUpdate: c7.slab.write, immediateRender: false }, S(6.9));
      Object.assign(caret.style, { width: `${f(0.075 * fs)}px`, height: `${f(0.9 * fs)}px`, top: `${f(c7.base - 0.74 * fs)}px`, background: C.night });
      const caretX = (n) => c7.x0 + (n ? R.measure(text.slice(0, n), fs, WEIGHT, LS).w : 0) + 0.04 * fs;
      caret.style.left = `${f(caretX(0))}px`;
      hidden(caret);
      tl.set(caret, { opacity: 1 }, S(6.9) + 0.12);
      tl.set(caret, { opacity: 0 }, S(6.9) + 0.38);
      tl.set(caret, { opacity: 1 }, S(6.9) + 0.52);
      const word = $("c7-w0"), fullW = R.measure(text, fs, WEIGHT, LS).w;
      const reveal = (n) => `inset(-50% ${f(n >= text.length ? -0.2 * fs : fullW - R.measure(text.slice(0, n), fs, WEIGHT, LS).w)}px -50% -10%)`;
      word.style.clipPath = reveal(0);
      const t0 = S(7.88), dt = (S(8.98) - t0) / text.length; // with the real typing
      for (let i = 1; i <= text.length; i++) {
        tl.set(c7.slab.g, { w: boxW(i) }, t0 + (i - 1) * dt);
        tl.set(caret, { left: caretX(i) }, t0 + (i - 1) * dt);
        tl.set(word, { clipPath: reveal(i) }, t0 + (i - 1) * dt);
      }
      for (let i = 0; i < 4; i++) tl.set(caret, { opacity: i % 2 ? 1 : 0 }, S(9.1) + i * 0.26);
      /* Cut 2 (beat 42): zoom-through. The caption rides the camera's push into the label. */
      c7.el.style.transformOrigin = `${W / 2}px ${H / 2}px`;
      tl.fromTo(c7.el, { scale: 1, opacity: 1, filter: "blur(0px)" }, { scale: 2.7, opacity: 0, filter: "blur(12px)", duration: 0.22, ease: "expo.in", immediateRender: false }, bt(42) - 0.22);
    }
    {
      const ring = $("ring-c"), diag = Math.hypot(W, H);
      ring.setAttribute("cx", f(W / 2));
      ring.setAttribute("cy", f(H / 2));
      tl.fromTo(ring, { attr: { r: 0.03 * diag, "stroke-width": 0.14 * L.cap.fs } }, { attr: { r: 0.66 * diag, "stroke-width": 3 }, duration: 0.32, ease: "expo.out", immediateRender: false }, bt(42) - 0.04);
      tl.fromTo(ring, { opacity: 1 }, { opacity: 0, duration: 0.32, ease: "power2.in", immediateRender: false }, bt(42) - 0.04);
      const flash = $("flash-f");
      tl.fromTo(flash, { opacity: 0 }, { opacity: 0.32, duration: 0.035, ease: "none", immediateRender: false }, bt(42) - 0.035);
      tl.fromTo(flash, { opacity: 0.32 }, { opacity: 0, duration: 0.17, ease: "power2.out", immediateRender: false }, bt(42));
    }

    /* ================= Focus tools (beats 42-57) ================= */

    /* Show your pointer. — a cyan halo pops round "pointer." on the real halo click; ripples echo each click. */
    const c8 = caption("c8", ["Show", "your", "pointer."], "br", "peri");
    capIn(c8, F(0.8));
    {
      const w = c8.words[2], fs = c8.fs;
      const hx = w.left - 0.16 * fs, hy = w.top - 0.2 * fs, hw = w.right - w.left + 0.32 * fs, hh = w.bottom - w.top + 0.4 * fs;
      const haloD = R.roundRect(hx, hy, hw, hh, 0.32 * hh), origin = `${f(hx + hw / 2)} ${f(hy + hh / 2)}`;
      for (const [id, color, width] of [["c8-m3", C.night, 0.12 * fs], ["c8-m0", CYAN, 0.065 * fs], ["c8-m1", CYAN, 0.045 * fs], ["c8-m2", CYAN, 0.045 * fs]]) {
        R.stroke(R.setD($(id), haloD), color, width);
        hidden($(id));
      }
      tl.fromTo([$("c8-m3"), $("c8-m0")], { scale: 0.72, opacity: 0, svgOrigin: origin }, { scale: 1, opacity: 1, svgOrigin: origin, duration: 0.3, ease: "expo.out", immediateRender: false }, F(1.75)); // the real halo click
      for (const [id, t] of [["c8-m1", F(1.75) + 0.01], ["c8-m2", F(2.75)]]) {
        tl.fromTo($(id), { scale: 1, opacity: 0.95, svgOrigin: origin }, { scale: 1.55, opacity: 0, svgOrigin: origin, duration: 0.42, ease: "power2.out", immediateRender: false }, t);
      }
    }

    /* Spotlight it. — dim words; a spotlight walks across them with the real one, then lights them all. */
    const c9 = caption("c9", ["Spotlight", "it."], "br", "peri");
    {
      const fs = c9.fs;
      copyWord(c9, 0, "c9-w0l", C.night);
      copyWord(c9, 1, "c9-w1l", C.night);
      c9.groups[0].push($("c9-w0l"));
      c9.groups[1].push($("c9-w1l"));
      $("c9-w0").style.opacity = "0.3";
      $("c9-w1").style.opacity = "0.3";
      const lit = $("c9-lit"), glow = $("c9-glow");
      const cy = c9.base - 0.34 * fs, spot = { x: c9.words[0].left - 0.3 * fs, r: 0.64 * fs };
      glow.style.background = "radial-gradient(closest-side, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0))";
      const writeSpot = () => {
        lit.style.clipPath = `circle(${f(spot.r)}px at ${f(spot.x)}px ${f(cy)}px)`;
        const gr = spot.r * 1.5;
        Object.assign(glow.style, { left: `${f(spot.x - gr)}px`, top: `${f(cy - gr)}px`, width: `${f(2 * gr)}px`, height: `${f(2 * gr)}px` });
      };
      writeSpot();
      R.writers.push(writeSpot);
      swap(c8, c9, F(3.6));
      tl.fromTo(spot, { x: c9.words[0].left - 0.3 * fs }, { x: c9.words[1].right + 0.1 * fs, duration: F(7.4) - F(4.0), ease: "power1.inOut", onUpdate: writeSpot, immediateRender: false }, F(4.0)); // with the real walk
      tl.fromTo(spot, { r: 0.64 * fs }, { r: 1.2 * c9.rect.w, duration: 0.26, ease: "expo.out", onUpdate: writeSpot, immediateRender: false }, F(7.6));
      // Each real click on a picture sends a cyan ripple out of the caption's spotlight.
      const x0 = c9.words[0].left - 0.3 * fs, x1 = c9.words[1].right + 0.1 * fs, walk = gsap.parseEase("power1.inOut");
      [F(4.5), F(6.0), F(7.5)].forEach((t, i) => {
        const u = Math.min(1, Math.max(0, (t - F(4.0)) / (F(7.4) - F(4.0))));
        const ring = $(`c9-r${i}`);
        ring.setAttribute("cx", f(x0 + (x1 - x0) * walk(u)));
        ring.setAttribute("cy", f(cy));
        ring.setAttribute("stroke", CYAN);
        hidden(ring);
        tl.fromTo(ring, { attr: { r: 0.6 * fs, "stroke-width": 0.07 * fs }, opacity: 0.95 },
          { attr: { r: 1.5 * fs, "stroke-width": 0.012 * fs }, opacity: 0, duration: 0.5, ease: "power2.out", immediateRender: false }, t);
      });
    }
    capOut(c9, F(8.4));

    /* Effects: a hand-drawn ring circles the real button as the pointer chooses it, so the blur's tool is seen. */
    {
      const world = $("fx-world");
      const writeFx = () => {
        const p = poseAt("focus", tl.time());
        world.style.transform = `translate(${f(W / 2 - p.cx * p.z)}px, ${f(H / 2 - p.cy * p.z)}px) scale(${p.z.toFixed(5)})`;
      };
      writeFx();
      R.writers.push(writeFx);
      const d = R.roughEllipse(2048, 1532, 74, 62, -6, 41);
      const under = R.stroke(R.setD($("fx-u"), d), C.night, 13), ink = R.stroke(R.setD($("fx-m"), d), C.apricot, 6.5);
      for (const el of [under, ink]) {
        el.setAttribute("vector-effect", "non-scaling-stroke");
        R.drawOn(tl, el, F(9.3), 0.34);
      }
      fadeOut([under, ink], F(10.15), 0.2);
    }

    /* Blur it. — a dashed selection drags open round "Blur" with the real drag; the word blurs when the effect lands. */
    const c10 = caption("c10", ["Blur", "it."], "br", "peri");
    capIn(c10, F(9.8));
    {
      const w = c10.words[0], fs = c10.fs, m = R.stroke($("c10-m0"), C.night, 0.034 * fs);
      const sel = { x: w.left - 0.13 * fs, y: w.top - 0.15 * fs, w: 0, h: 0 };
      const selW = w.right - w.left + 0.26 * fs, selH = w.bottom - w.top + 0.3 * fs;
      m.style.strokeDasharray = `${f(0.1 * fs)} ${f(0.07 * fs)}`;
      m.style.strokeLinecap = "butt";
      const writeSel = () => m.setAttribute("d", `M${f(sel.x)} ${f(sel.y)} h${f(sel.w)} v${f(sel.h)} h${f(-sel.w)} Z`);
      writeSel();
      R.writers.push(writeSel);
      tl.fromTo(sel, { w: 0, h: 0 }, { w: selW, h: selH, duration: F(12.5) - F(10.55), ease: "power1.inOut", onUpdate: writeSel, immediateRender: false }, F(10.55)); // with the real drag
      tl.fromTo(m, { strokeDashoffset: 0 }, { strokeDashoffset: -0.85 * fs, duration: F(15) - F(12.5), ease: "none", immediateRender: false }, F(12.5));
      tl.fromTo($("c10-w0"), { filter: "blur(0px)" }, { filter: `blur(${f(0.075 * fs)}px)`, duration: 0.24, ease: "power2.out", immediateRender: false }, F(13.25)); // the real blur lands
    }

    /* ---- Cut 3 (beat 57): the blur region grows until the whole frame is night. ---- */
    {
      const sw = $("sw-focus"), el = $("blur-rect"), fs = L.cap.fs;
      // Start from the busy tile's on-screen rectangle at that moment (the take's blur region).
      const pz = poseAt("focus", bt(57));
      const t0 = { x: W / 2 + (396 - pz.cx) * pz.z, y: H / 2 + (838 - pz.cy) * pz.z, w: 735 * pz.z, h: 538 * pz.z, r: 0.03 * 735 * pz.z };
      tl.fromTo(sw, { filter: "blur(0px)" }, { filter: "blur(26px)", duration: 0.42, ease: "power2.in", immediateRender: false }, bt(57));
      tl.set(sw, { filter: "none" }, bt(58) + 0.05);
      const g = { x: t0.x, y: t0.y, w: t0.w, h: t0.h, r: t0.r, a: 0.3, e: 1 };
      const write = () => {
        Object.assign(el.style, {
          left: `${f(g.x)}px`, top: `${f(g.y)}px`, width: `${f(g.w)}px`, height: `${f(g.h)}px`, borderRadius: `${f(g.r)}px`,
          background: `rgba(11, 16, 26, ${g.a.toFixed(3)})`, borderWidth: `${f(0.035 * fs)}px`, borderColor: `rgba(255, 181, 140, ${g.e.toFixed(3)})`,
        });
      };
      write();
      R.writers.push(write);
      tl.fromTo(g, { x: t0.x, y: t0.y, w: t0.w, h: t0.h, r: t0.r }, { x: -60, y: -60, w: W + 120, h: H + 120, r: 0, duration: 0.42, ease: "expo.inOut", onUpdate: write, immediateRender: false }, bt(57));
      tl.fromTo(g, { a: 0.3 }, { a: 1, duration: 0.42, ease: "power2.in", onUpdate: write, immediateRender: false }, bt(57));
      tl.fromTo(g, { e: 1 }, { e: 0, duration: 0.2, ease: "power1.in", onUpdate: write, immediateRender: false }, bt(57) + 0.22);
      tl.fromTo(c10.el, { filter: "blur(0px)", opacity: 1 }, { filter: "blur(18px)", opacity: 0, duration: 0.26, ease: "power2.in", immediateRender: false }, bt(57));
    }
  };
})();
