#!/usr/bin/env python3
"""Build the reel's audio: the music edit, foley for visible actions, and the final mixes.

Music: "Product Launch Advertising Commercial Music" by lNPLUSMUSIC (Pixabay Content License), played at its own
tempo (129.98 BPM; the reel runs at 130). The edit maps reel beats to song beats (see MUSIC below): the reel opens
on the last beat of the build, the second drop lands on "Draw", one 2-bar edit hides under the zoom-through, and
the song's final hit lands on the end card and rings out.

Foley: only the sounds of actions you can see, mixed quietly under the music.

- A close-miked mouse click for each visible click in the takes (tool presses, colour, arrow points, library
  tiles, the pictures clicked under the Spotlight, Effects).
- One real laptop keystroke for each character of the typed label, at the moment it appears.
- A soft pen-on-paper stroke under the three hand-drawn strokes (ellipse, rough box and arrow, highlighter).
No sound for titles, camera moves or transitions. Every time comes from the same beat plan as the picture
(tools/shots.py, src/scene-shots.js); typed characters go through the take's retime.
Writes assets/audio/music-bed.wav and foley-bed.wav, then assets/audio/mix.wav (music + foley under a limiter,
used by index.html and phone.html).
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import find_peaks

sys.path.insert(0, str(Path(__file__).resolve().parent))
import camera  # noqa: E402
import shots  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FOLEY = ROOT / "assets/audio/foley"
SR = 48000
B = shots.B
TOTAL = shots.TOTAL  # index.html data-duration (64 beats)


def bt(n: float) -> float:
    return (n - 1) * B


def D(k: float) -> float:
    return bt(shots.BEATS["dashboard"][0]) + k * B


def S(k: float) -> float:
    return bt(shots.BEATS["smart"][0]) + k * B


def F(k: float) -> float:
    return bt(shots.BEATS["focus"][0]) + k * B


def load(name: str) -> np.ndarray:
    y, _ = librosa.load(FOLEY / name, sr=SR, mono=True)
    return y / (np.max(np.abs(y)) or 1.0)


def keystrokes() -> list[np.ndarray]:
    """Individual keys cut from the typing recording: 10 ms before each transient, 110 ms after, faded out."""
    y = load("mixkit-2537-laptop-keyboard-typing-sequence.wav")
    env = np.sqrt(np.convolve(y**2, np.ones(240) / 240, mode="same"))
    peaks, _ = find_peaks(env, height=env.max() * 0.2, distance=int(0.06 * SR))
    keys = []
    for p in peaks[:10]:
        a, b = max(0, p - int(0.01 * SR)), min(len(y), p + int(0.11 * SR))
        key = y[a:b].copy()
        key *= np.linspace(1, 0, len(key)) ** 1.5
        keys.append(key / (np.max(np.abs(key)) or 1.0))
    return keys


def typed_times() -> list[float]:
    """Reel time of each typed character: source times from the take, through the smart shot's retime."""
    meta = json.loads((REPO / "build/reel-takes/latest-smart.json").read_text())
    tmap = camera.TimeMap(shots.build("smart", "16x9")["retime"])
    lo, hi = tmap.o[0], tmap.o[-1]

    def clip_time(src: float) -> float:
        a, b = lo, hi
        for _ in range(50):
            mid = (a + b) / 2
            a, b = (mid, b) if tmap.src(mid) < src else (a, mid)
        return (a + b) / 2

    return [S(0) + clip_time(a["time"]) for a in meta["actions"] if a.get("gesture") == "type-character"]


def cues() -> list[tuple[float, str, float]]:
    """(time of the transient, sound, gain dB)."""
    click = "click"
    c = [(D(k), click, -15) for k in (8, 11.5, 12.5, 14.5, 21.25)]           # Ellipse, Arrow, Stroke color, Blue, Highlighter
    c += [(D(k), click, -18) for k in (15.25, 16, 16.75)]                     # the three arrow points
    c += [(S(7.5), click, -16)]                                               # click to place the label
    c += [(F(k), click, -15) for k in (0.5, 1.75, 2.75, 3.5, 8.5, 9.5)]       # library, halo, Spotlight, close, stop, Effects
    c += [(F(k), click, -14) for k in (4.5, 6.0, 7.5)]                        # the pictures clicked under the Spotlight
    c += [(t, "key", -20) for t in typed_times()]
    c += [(D(9.02), "pen", -20), (D(22.28), "pen", -21)]                      # ellipse, highlighter
    c += [(S(1.3), "scribble", -19), (S(2.55), "scribble", -21), (S(4.8), "marker", -21)]
    return c


def build_bed() -> Path:
    click = load("mixkit-1113-mouse-click-close.wav")
    sounds = {"click": (click, 0.012), "pen": (load("mixkit-2367-writing-with-a-pen-on-paper.wav"), 0.04),
              "scribble": (load("mixkit-2369-writing-scribble-on-paper.wav"), 0.03),
              "marker": (load("mixkit-2998-pen-marker-line.wav"), 0.01)}
    keys = keystrokes()
    out = np.zeros(int(round(TOTAL * SR)) + SR, np.float32)
    placed, key_index = [], 0
    for t, name, gain in sorted(cues()):
        if name == "key":
            y, hit = keys[key_index % len(keys)], 0.01
            key_index += 1
        else:
            y, hit = sounds[name]
        start = int(round((t - hit) * SR))
        y = y * (10 ** (gain / 20))
        end = min(len(out), start + len(y))
        out[start:end] += y[: end - start]
        placed.append({"time": round(t, 3), "sound": name, "gain_db": gain})
    out = out[: int(round(TOTAL * SR))]
    stereo = np.stack([out, out], axis=1)
    path = ROOT / "assets/audio/foley-bed.wav"
    sf.write(path, stereo, SR, subtype="PCM_16")
    (ROOT / "assets/audio/foley-bed.json").write_text(json.dumps({"cues": placed}, indent=1) + "\n")
    print(path.name, f"{len(placed)} cues, peak {20 * math.log10(float(np.max(np.abs(out))) + 1e-9):.1f} dBFS")
    return path


# Song grid: beat n starts at t0 + (n - 1) * beat (first downbeat, kick attacks on the grid; tools/beat_track.py).
# The song: intro bar, first drop (song beats 5-68), breakdown and build (69-100), second drop (101-164), final
# hit on beat 165 with a 3.7 s tail. Segments play from (reel beat, song beat): the reel opens on the build's last
# beat, so the second drop hits "Draw" (reel beat 2). At the zoom-through (reel beat 42) the edit skips two bars
# (song beats 141-148; the bars either side are the most alike pair in the drop), so the final hit lands on the
# end card (reel beat 58). The Smart Draw snap (reel beat 34) falls on the drop's second phrase.
MUSIC = {
    "source": "pixabay-306038-product-launch.mp3",
    "t0": 0.0388,
    "beat": 0.461595,
    "segments": [(1, 100), (42, 149)],
    "crossfade": 0.012,  # equal-power, ending 3 ms before each edit's downbeat
    "lufs": -14.0,
}


def music_bed() -> Path:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "assets/audio/source" / MUSIC["source"]), "-f", "f32le",
                          "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    src = np.frombuffer(raw, np.float32).reshape(-1, 2)
    n = int(round(TOTAL * SR))
    out = np.zeros((n, 2), np.float32)
    xf, guard = int(MUSIC["crossfade"] * SR), int(0.003 * SR)
    segs = MUSIC["segments"]
    edits = [int(round(bt(reel) * SR)) for reel, _ in segs]  # output sample where each segment's first beat lands
    for i, (_, song_beat) in enumerate(segs):
        q0 = int(round((MUSIC["t0"] + (song_beat - 1) * MUSIC["beat"]) * SR))
        a = 0 if i == 0 else edits[i] - guard - xf  # fade in over [edit - guard - xf, edit - guard)
        b = n if i + 1 == len(segs) else edits[i + 1] - guard  # fade out over the same span before the next edit
        piece = src[q0 + (a - edits[i]):q0 + (b - edits[i])]
        if len(piece) != b - a:
            raise SystemExit(f"segment {i}: the song is too short for this edit")
        gain = np.ones(b - a, np.float32)
        if i > 0:
            gain[:xf] = np.sin(np.linspace(0, np.pi / 2, xf))
        if i + 1 < len(segs):
            gain[-xf:] = np.cos(np.linspace(0, np.pi / 2, xf))
        out[a:b] += piece * gain[:, None]
    fade_in, fade_out = int(0.005 * SR), int(0.4 * SR)
    out[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    out[-fade_out:] *= np.cos(np.linspace(0, np.pi / 2, fade_out))[:, None]
    tmp = ROOT / "assets/audio/_music.wav"
    sf.write(tmp, out, SR, subtype="FLOAT")
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(tmp), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    measured = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)[-1])
    path = ROOT / "assets/audio/music-bed.wav"
    sf.write(path, np.clip(out * 10 ** ((MUSIC["lufs"] - measured) / 20), -1, 1), SR, subtype="PCM_16")
    tmp.unlink()
    print(path.name, f"{measured:.1f} LUFS before gain")
    return path


def final_mix(music: Path, bed: Path, out: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(music), "-i", str(bed), "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.84:attack=2:release=60:level=disabled,"
                    "aresample=48000", "-c:a", "pcm_s16le", str(out)], check=True)
    print(out.name)


if __name__ == "__main__":
    audio = ROOT / "assets/audio"
    music = music_bed()
    foley = build_bed()
    final_mix(music, foley, audio / "mix.wav")  # both renders use the same mix
