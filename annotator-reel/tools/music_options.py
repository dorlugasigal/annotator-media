#!/usr/bin/env python3
"""Cut candidate music beds for the reel so each one sits on the reel's phrasing, then build review cuts.

The reel is 64 beats (tempo and length in tools/shots.py). Its big moments fall on beat 2 of a bar: the "Draw" slam (beat 2), the whip
(beat 30), the zoom-through (beat 42) and the end card (beat 58). So each bed starts one beat before a bar
downbeat: the last beat of the build plays under the opening dive, and the downbeat lands on "Draw".

For each option in build/music-options/options.json (id, slug, source_bpm, start_s = the chosen section):
1. Beats and bar downbeats come from beat_this (tools/beat_track.py writes build/music-options/beat_this.json).
   The bed starts at the strongest bar-line entrance near start_s (a bar much louder in the low band than the
   bar before it); for a steady groove, at the bar line nearest start_s.
2. The source is tempo-matched to the reel's BPM with Rubber Band R3 (pylibrb; pitch and transients kept) and trimmed
   so the kick attacks of the tracked beats land
   on the reel's beat grid (percussive onsets folded over one beat, searched only near the tracked beat, so a
   strong offbeat hi-hat or bass is never mistaken for the beat).
3. Checks: attack phase, energy per bar (no breakdown inside the reel), loudness; then a mix with the foley
   bed and a review MP4 with the desktop master.

Usage (inside videos/annotator-reel): .venv/bin/python tools/music_options.py [slug ...]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shots  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OPT = ROOT / "build/music-options"
BPM, SR = shots.BPM, 48000
B = shots.B
TOTAL = shots.TOTAL
TARGET_PHASE = 0.0  # kick attacks on the beat


def fold_phase(y: np.ndarray, sr: int, grid0: float, period: float, seconds: float = 28.0, window: float | None = None) -> float:
    """Phase (s) of the dominant on-beat percussive onset family relative to a grid starting at grid0."""
    y = y[: int((grid0 + seconds) * sr)]
    yp = librosa.effects.percussive(y, margin=2.0)
    hop = 64
    nb = 96
    kern = np.array([0.25, 0.5, 1.0, 0.5, 0.25]) / 2.5

    def profile(signal):
        env = librosa.onset.onset_strength(y=signal, sr=sr, hop_length=hop)
        t = librosa.frames_to_time(np.arange(len(env)), sr=sr, hop_length=hop)
        keep = t >= grid0
        ph = ((t[keep] - grid0) % period) / period
        prof = np.zeros(nb)
        np.add.at(prof, (ph * nb).astype(int) % nb, env[keep])
        prof = np.convolve(np.concatenate([prof[-2:], prof, prof[:2]]), kern, mode="same")[2:-2]
        return prof / (prof.max() + 1e-9)

    low = sosfiltfilt(butter(4, 120, btype="low", fs=sr, output="sos"), yp)
    score = profile(yp) + 0.6 * profile(low)
    phases = (np.arange(nb) + 0.5) / nb * period
    phases = np.where(phases > period / 2, phases - period, phases)
    if window is not None:
        score = np.where(np.abs(phases) <= window, score, -np.inf)
    return float(phases[int(np.argmax(score))])


def stretch(stereo: np.ndarray, factor: float) -> np.ndarray:
    """Tempo change by factor (>1 = faster), pitch kept, with Rubber Band's R3 engine (offline, no latency)."""
    if abs(factor - 1) < 1e-6:
        return stereo
    import pylibrb

    options = pylibrb.Option.PROCESS_OFFLINE | pylibrb.Option.ENGINE_FINER | pylibrb.Option.CHANNELS_TOGETHER
    rb = pylibrb.RubberBandStretcher(sample_rate=SR, channels=2, options=options, initial_time_ratio=1 / factor)
    audio = np.ascontiguousarray(stereo.T, dtype=np.float32)  # (channels, samples)
    rb.set_max_process_size(audio.shape[1])
    rb.study(audio, final=True)
    rb.process(audio, final=True)
    return np.ascontiguousarray(rb.retrieve_available().T)


def choose_downbeat(o: dict, downs: np.ndarray, low: np.ndarray, sr: int) -> tuple[float, str, float]:
    """The bar-line entrance near the chosen section, or the bar line nearest it for a steady groove."""
    b = 60 / float(o["source_bpm"])
    cands = [float(d) for d in downs if o["start_s"] - 6.5 * b < d < o["start_s"] + 6.5 * b]
    if not cands:
        raise SystemExit(f"{o['slug']}: no tracked downbeat near {o['start_s']} s")

    def bar(t: float) -> float:
        return float(np.sqrt(np.mean(low[int(max(0.0, t) * sr):int((t + 4 * b) * sr)] ** 2)))

    peak = max(bar(d) for d in cands)
    ratio, best = max((bar(d) / (bar(d - 4 * b) + 1e-9), d) for d in cands if bar(d) >= 0.75 * peak)
    if ratio < 1.25:
        nearest = min(cands, key=lambda d: abs(d - o["start_s"]))
        return nearest, "bar line nearest the section start", ratio
    return best, f"bar-line entrance, low band x{ratio:.1f}", ratio


def make_bed(o: dict, bed_path: Path, source: Path | None = None, downbeat: float | None = None) -> dict:
    """Write a 64-beat bed: one pickup beat, then the chosen bar downbeat on reel beat 2, kicks on the grid."""
    src = source or OPT / "source" / f"{o['id']}.mp3"
    bpm = float(o["source_bpm"])
    b_src = 60 / bpm
    how, entrance = "fixed downbeat", None
    if downbeat is None:
        tracked = OPT / "beat_this.json"
        if not tracked.exists():
            raise SystemExit("Run tools/beat_track.py first (see its docstring).")
        downs = np.asarray(json.loads(tracked.read_text())[o["id"]]["downbeats"])
        y_src, sr_src = librosa.load(src, sr=22050, mono=True)
        low = sosfiltfilt(butter(4, 100, btype="low", fs=sr_src, output="sos"), y_src)
        downbeat, how, entrance = choose_downbeat(o, downs, low, sr_src)
    factor = BPM / bpm
    pad = 1.0
    seg_start = downbeat - b_src - pad  # one beat of pickup before the downbeat, plus padding
    need = (64 * B + 2.0) * factor + pad
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, seg_start):.4f}", "-t", f"{need:.4f}", "-i", str(src),
                          "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    ys = stretch(np.frombuffer(raw, np.float32).reshape(-1, 2), factor)
    lead = (downbeat - b_src - max(0.0, seg_start)) / factor  # stretched time of the pickup beat
    mono = librosa.resample(ys.mean(axis=1), orig_sr=SR, target_sr=22050)
    p = fold_phase(mono, 22050, grid0=lead + B, period=B, window=0.04)  # grid anchored on the tracked downbeat
    t0 = lead + (p - TARGET_PHASE)
    a = int(round(t0 * SR))
    n = int(round(TOTAL * SR))
    bed = ys[a:a + n]
    if len(bed) < n:
        bed = np.pad(bed, ((0, n - len(bed)), (0, 0)))
    tmp = bed_path.with_name(f"_{bed_path.stem}.wav")
    sf.write(tmp, bed, SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af",
                    f"afade=t=in:st=0:d=0.004,afade=t=out:st={60 * B:.4f}:d={TOTAL - 60 * B:.4f}:curve=qsin,"
                    "loudnorm=I=-14:TP=-1.2:LRA=11,aresample=48000", "-ac", "2", "-c:a", "pcm_s16le", str(bed_path)], check=True)
    tmp.unlink()
    return {"downbeat_s": round(downbeat, 3), "downbeat_how": how, "entrance_ratio": None if entrance is None else round(entrance, 2),
            "bed_source_start_s": round(max(0.0, seg_start) + t0 * factor, 3), "tempo_factor": round(factor, 6)}


def build(o: dict, foley: Path, master: Path, out_dir: Path, number: int) -> dict:
    bed_path = out_dir / f"bed-{o['slug']}.wav"
    o.update(make_bed(o, bed_path, downbeat=o.get("downbeat_fixed")))
    # Checks on the finished bed.
    yb, _ = librosa.load(bed_path, sr=22050, mono=True)
    check_phase = fold_phase(yb, 22050, grid0=B, period=B, window=0.06)  # the kicks, not a louder offbeat hi-hat
    rms = librosa.feature.rms(y=yb, frame_length=2048, hop_length=512)[0]
    t = librosa.frames_to_time(np.arange(len(rms)), sr=22050, hop_length=512)
    bars = []
    for k in range(15):  # bars start on reel beats 2, 6, 10, ... (bar k spans beats 2+4k .. 5+4k)
        s, e = (1 + 4 * k) * B, (5 + 4 * k) * B
        bars.append(float(rms[(t >= s) & (t < e)].mean()))
    bars = np.array(bars)
    weakest = int(np.argmin(bars[:14]))
    mix_path = out_dir / f"mix-{o['slug']}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bed_path), "-i", str(foley), "-filter_complex",
                    "[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.84:attack=2:release=60:level=disabled,aresample=48000",
                    "-c:a", "pcm_s16le", str(mix_path)], check=True)
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mix_path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    video = ROOT / "renders/music-options" / f"{number:02d}-{o['label'].replace(' ', '-')}-{o['slug']}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-i", str(mix_path), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(video)], check=True)
    o.update({
        "attack_phase_ms": round(check_phase * 1000, 1),
        "bar_energy": [round(v / bars.max(), 2) for v in bars], "weakest_bar": weakest + 1,
        "weakest_ratio": round(float(bars[weakest] / np.median(bars)), 2),
        "lufs": float(re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)[-1]), "peak_dbfs": float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)[-1]),
        "review": str(video.relative_to(ROOT)),
    })
    return o


def main() -> None:
    options = json.loads((OPT / "options.json").read_text())
    only = set(sys.argv[1:])
    (ROOT / "renders/music-options").mkdir(parents=True, exist_ok=True)
    foley, master = ROOT / "assets/audio/foley-bed.wav", ROOT / "renders/reel-desktop-master.mp4"
    for number, o in enumerate(options, 1):
        if only and o["slug"] not in only:
            continue
        o = build(o, foley, master, OPT, number)
        print(f"{o['slug']:22} downbeat {o['downbeat_s']:7.3f}s ({o['downbeat_how']}) x{o['tempo_factor']:.3f} attack {o['attack_phase_ms']:+6.1f} ms  "
              f"weakest bar {o['weakest_bar']:>2} x{o['weakest_ratio']:.2f}  {o['lufs']} LUFS  bars {o['bar_energy']}", flush=True)
    (OPT / "options.json").write_text(json.dumps(options, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
