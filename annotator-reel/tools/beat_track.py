#!/usr/bin/env python3
"""Beat and downbeat tracking for the music options with beat_this (CPJKU), a neural beat tracker.

Needs its own environment with PyTorch (build/ is ignored by git):
  python3 -m venv --system-site-packages build/.venv-beat
  build/.venv-beat/bin/pip install "beat_this @ https://github.com/CPJKU/beat_this/archive/main.zip"
Usage (inside videos/annotator-reel): build/.venv-beat/bin/python tools/beat_track.py [slug ...]
Reads build/music-options/options.json and source/<id>.mp3; writes (merges into) build/music-options/beat_this.json.
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from beat_this.inference import Audio2Beats

ROOT = Path(__file__).resolve().parents[1]
OPT = ROOT / "build/music-options"


def main() -> None:
    options = json.loads((OPT / "options.json").read_text())
    (OPT / "wav").mkdir(exist_ok=True)
    tracker = Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)
    out = OPT / "beat_this.json"
    result = json.loads(out.read_text()) if out.exists() else {}
    only = set(sys.argv[1:])
    for o in options:
        if only and o["slug"] not in only:
            continue
        wav = OPT / "wav" / f"{o['id']}.wav"
        if not wav.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OPT / "source" / f"{o['id']}.mp3"), "-ac", "1", "-ar", "22050",
                            str(wav)], check=True)
        with wave.open(str(wav)) as w:
            rate = w.getframerate()
            signal = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
        beats, downbeats = tracker(signal, rate)
        result[o["id"]] = {"beats": np.asarray(beats).tolist(), "downbeats": np.asarray(downbeats).tolist()}
        print(o["slug"], len(beats), "beats", len(downbeats), "downbeats")
    out.write_text(json.dumps(result))


if __name__ == "__main__":
    main()
