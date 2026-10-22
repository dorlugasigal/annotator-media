#!/usr/bin/env python3
"""Rewrite the clip windows in index.html from beat positions, using BPM and FRAMES from tools/shots.py.

Every timed element in the composition is listed here in beats, so a tempo change is one edit in shots.py
followed by this script. Beat n starts at (n - 1) * B; D(k), S(k) and F(k) are beat offsets inside the
dashboard, Smart Draw and focus shots (the same helpers as src/scene-shots.js).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shots  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
B = shots.B
bt = lambda n: (n - 1) * B  # noqa: E731
D = lambda k: bt(shots.BEATS["dashboard"][0]) + k * B  # noqa: E731
S = lambda k: bt(shots.BEATS["smart"][0]) + k * B  # noqa: E731
F = lambda k: bt(shots.BEATS["focus"][0]) + k * B  # noqa: E731
TOTAL = shots.TOTAL

CLIPS = {
    "hkDraw": (0.1, bt(3)), "hkOver": (bt(3), bt(4)), "hkAny": (bt(4), bt(5) + 0.05),
    "v-dash": (bt(4), bt(30)), "v-smart": (bt(30), bt(42)), "v-focus": (bt(42), bt(58)),
    "tour": (D(2.0), D(7.8)),
    "c1": (D(8.85), D(10.9) + 0.25), "c2": (D(15.1), D(17.8)), "c3": (D(17.8), D(19.8) + 0.25), "c4": (D(21.6), bt(30)),
    "swoosh": (bt(30) - 0.2, bt(30) + 0.22),
    "c5": (S(0.35), S(3.8)), "c6": (S(3.8), S(6.9)), "c7": (S(6.9), bt(42)),
    "flash": (bt(42) - 0.04, bt(42) + 0.18), "ring": (bt(42) - 0.05, bt(42) + 0.31),
    "c8": (F(0.8), F(3.6)), "c9": (F(3.6), F(8.4) + 0.25), "fxmark": (F(9.15), F(9.15) + 1.2), "c10": (F(9.8), F(15) + 0.3),
    "blurT": (bt(57) - 0.01, bt(57) + 0.54), "ecB": (bt(58) - 0.06, TOTAL), "music": (0, TOTAL),
}


def main() -> None:
    path = ROOT / "index.html"
    html = path.read_text()
    for cid, (a, b) in CLIPS.items():
        pattern = re.compile(r'(id="%s"[^>]*?)data-start="[^"]*" data-duration="[^"]*"' % re.escape(cid))
        html, n = pattern.subn(lambda m: f'{m.group(1)}data-start="{a:.4f}" data-duration="{b - a:.4f}"', html)
        if n != 1:
            raise SystemExit(f"index.html: clip {cid} matched {n} times")
    html, n = re.subn(r'(data-composition-id="main"[^>]*?)data-duration="[0-9.]+"', lambda m: f'{m.group(1)}data-duration="{TOTAL:.4f}"', html)
    if n != 1:
        raise SystemExit("index.html: root duration not found")
    path.write_text(html)
    print(f"index.html: {len(CLIPS)} clips at {shots.BPM:g} BPM, {TOTAL:.4f} s")


if __name__ == "__main__":
    main()
