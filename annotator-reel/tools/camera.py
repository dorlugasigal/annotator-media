#!/usr/bin/env python3
"""Virtual camera for the Annotator reel.

Renders one native take (3840x2160 ScreenCaptureKit capture of the live overlay) through an authored
camera: monotone speed ramps, keyframed zoom/pan/3D tilt and true sub-frame motion blur. Every sample is
warped into a 2x supersampled canvas and area-downsampled, so Retina UI text stays crisp and camera
moves never alias. Nothing is drawn on top of the footage here; type and marks live in HyperFrames.

Usage (inside videos/annotator-reel):
  .venv/bin/python tools/camera.py dashboard --aspect 16x9            # full render
  .venv/bin/python tools/camera.py dashboard --aspect 16x9 --stills 0.5,1.2
Other shot lists (for example website demo clips) use the same takes and renderer:
  .venv/bin/python tools/camera.py <shot> --spec path/to/spec.py --aspect <name> --out <dir>
A spec module defines build(shot, aspect) -> {take, retime, camera, shutter} (see tools/shots.py) and may
define ASPECT_SIZE = {name: (width, height)} for its own output sizes.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shots  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FPS = 60
NAVY = (26, 16, 11)  # BGR of #0b101a
ASPECTS = {"16x9": (1920, 1080), "4x5": (1080, 1350)}


class TimeMap:
    """Monotone cubic (Fritsch-Carlson) map from clip time to source time."""

    def __init__(self, pairs):
        self.o = np.array([p[1] for p in pairs], float)
        self.s = np.array([p[0] for p in pairs], float)
        if np.any(np.diff(self.o) <= 0) or np.any(np.diff(self.s) <= 0):
            raise ValueError("retime anchors must increase in both source and clip time")
        self.h = np.diff(self.o)
        d = np.diff(self.s) / self.h
        m = np.empty(len(self.o))
        m[0], m[-1] = d[0], d[-1]
        for k in range(1, len(m) - 1):
            if d[k - 1] * d[k] <= 0:
                m[k] = 0.0
            else:
                w1, w2 = 2 * self.h[k] + self.h[k - 1], self.h[k] + 2 * self.h[k - 1]
                m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])
        self.m = m

    @property
    def duration(self) -> float:
        return float(self.o[-1] - self.o[0])

    def src(self, t: float) -> float:
        t = min(max(t, self.o[0]), self.o[-1])
        k = min(int(np.searchsorted(self.o, t, "right")) - 1, len(self.h) - 1)
        h = self.h[k]
        u = (t - self.o[k]) / h
        h00, h10 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u
        h01, h11 = -2 * u**3 + 3 * u**2, u**3 - u**2
        return float(h00 * self.s[k] + h10 * h * self.m[k] + h01 * self.s[k + 1] + h11 * h * self.m[k + 1])


EASES = {
    "linear": lambda u: u,
    "inOut": lambda u: u * u * (3 - 2 * u),
    "inOutCubic": lambda u: 4 * u**3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    "out": lambda u: 1 - (1 - u) ** 3,
    "outQuart": lambda u: 1 - (1 - u) ** 4,
    "outExpo": lambda u: 1.0 if u >= 1 else 1 - 2 ** (-10 * u),
    "in": lambda u: u**3,
    "inExpo": lambda u: 0.0 if u <= 0 else 2 ** (10 * u - 10),
}


class Camera:
    """Keyframed pose: centre (source px), zoom (output px per source px), tilt (degrees)."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k["t"])

    def pose(self, t: float) -> dict:
        ks = self.keys
        if t <= ks[0]["t"]:
            return dict(ks[0])
        if t >= ks[-1]["t"]:
            return dict(ks[-1])
        for a, b in zip(ks, ks[1:]):
            if a["t"] <= t <= b["t"]:
                u = EASES[b.get("ease", "inOutCubic")]((t - a["t"]) / (b["t"] - a["t"]))
                out = {"t": t}
                for key in ("cx", "cy", "rx", "ry"):
                    out[key] = a.get(key, 0.0) + (b.get(key, 0.0) - a.get(key, 0.0)) * u
                out["z"] = math.exp(math.log(a["z"]) + (math.log(b["z"]) - math.log(a["z"])) * u)
                return out
        return dict(ks[-1])


def homography(pose: dict, width: int, height: int, level: float) -> np.ndarray:
    """Source (at pyramid scale `level`) to supersampled canvas (2x output) homography."""
    zoom = 2 * pose["z"] / level
    cx, cy = pose["cx"] * level, pose["cy"] * level
    cw, ch = 2 * width, 2 * height
    rx, ry = math.radians(pose.get("rx", 0.0)), math.radians(pose.get("ry", 0.0))
    if abs(rx) < 1e-6 and abs(ry) < 1e-6:
        return np.array([[zoom, 0, cw / 2 - cx * zoom], [0, zoom, ch / 2 - cy * zoom], [0, 0, 1]], float)
    focal = 2.2 * cw
    rot_x = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    rot_y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    rot = rot_y @ rot_x
    src_pts, dst_pts = [], []
    for sx, sy in ((cx - 900, cy - 600), (cx + 900, cy - 600), (cx + 900, cy + 600), (cx - 900, cy + 600)):
        vec = rot @ np.array([(sx - cx) * zoom, (sy - cy) * zoom, 0.0])
        depth = focal + vec[2]
        src_pts.append((sx, sy))
        dst_pts.append((cw / 2 + focal * vec[0] / depth, ch / 2 + focal * vec[1] / depth))
    return cv2.getPerspectiveTransform(np.float32(src_pts), np.float32(dst_pts))


class Source:
    """Sequential constant-rate (60 fps) frames of a variable-rate capture, with a small cache."""

    def __init__(self, path: Path, width: int, height: int, start: float = 0.0, limit: int | None = None):
        self.w, self.h = width, height
        cmd = ["ffmpeg", "-v", "error", "-hwaccel", "videotoolbox"]
        if start > 0:
            cmd += ["-ss", f"{start:.4f}"]
        cmd += ["-i", str(path), "-vf",
                f"fps={FPS},scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=bgr24"]
        if limit:
            cmd += ["-frames:v", str(limit)]
        cmd += ["-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.first = self.next_index = int(round(start * FPS))
        self.cache: dict[int, np.ndarray] = {}
        self.halves: dict[int, np.ndarray] = {}
        self.last: np.ndarray | None = None

    def frame(self, index: int, half: bool = False) -> np.ndarray:
        index = max(self.first, index)
        while index >= self.next_index:
            raw = self.proc.stdout.read(self.w * self.h * 3)
            if len(raw) < self.w * self.h * 3:
                break  # past the end: hold the last frame
            self.last = np.frombuffer(raw, np.uint8).reshape(self.h, self.w, 3)
            self.cache[self.next_index] = self.last
            self.next_index += 1
            for old in [k for k in self.cache if k < self.next_index - 48]:
                del self.cache[old]
                self.halves.pop(old, None)
        if self.last is None:
            raise RuntimeError("the source produced no frames")
        chosen = min(index, self.next_index - 1)
        img = self.cache.get(chosen, self.last)
        if not half:
            return img
        if chosen not in self.halves:
            self.halves[chosen] = cv2.resize(img, (self.w // 2, self.h // 2), interpolation=cv2.INTER_AREA)
        return self.halves[chosen]

    def close(self):
        self.proc.stdout.close()
        self.proc.kill()
        self.proc.wait()


def line_kernel(dx: float, dy: float) -> np.ndarray | None:
    """Normalised line kernel along (dx, dy) canvas px, used to smooth steps between capped samples."""
    length = math.hypot(dx, dy)
    if length < 2.0:
        return None
    size = int(math.ceil(length)) | 1
    kernel = np.zeros((size, size), np.float32)
    c = size // 2
    ux, uy = dx / length, dy / length
    cv2.line(kernel, (int(round(c - ux * length / 2)), int(round(c - uy * length / 2))),
             (int(round(c + ux * length / 2)), int(round(c + uy * length / 2))), 1.0, 1, cv2.LINE_AA)
    total = kernel.sum()
    return kernel / total if total > 0 else None


def render_frame(src: Source, cam: Camera, tmap: TimeMap, t: float, width: int, height: int,
                 shutter: float, kmax: int) -> np.ndarray:
    half_open = shutter / FPS / 2
    a, b = cam.pose(t - half_open), cam.pose(t + half_open)
    probe = np.float32([[0, 0], [width, 0], [width, height], [0, height], [width / 2, height / 2]]) * 2
    ha, hb = homography(a, width, height, 1.0), homography(b, width, height, 1.0)
    in_source = cv2.perspectiveTransform(probe.reshape(-1, 1, 2), np.linalg.inv(ha))
    travel = cv2.perspectiveTransform(in_source, hb).reshape(-1, 2) - probe  # canvas px during the shutter
    moved = float(np.max(np.linalg.norm(travel, axis=1))) / 2  # output px
    need = max(1, math.ceil(moved / 1.2))
    samples = int(min(kmax, need))
    index = int(round(tmap.src(t) * FPS))  # one source frame: blending sped-up UI frames ghosts popovers
    acc = None
    for i in range(samples):
        ts = t if samples == 1 else t - half_open + (i + 0.5) * (2 * half_open / samples)
        pose = cam.pose(ts)
        half = 2 * pose["z"] < 0.75
        level = 0.5 if half else 1.0
        img = src.frame(index, half=half)
        # Past 1:1 the Retina pixels are enlarged, so resample bicubically to keep UI edges clean.
        interp = cv2.INTER_CUBIC if pose["z"] > 1.02 else cv2.INTER_LINEAR
        warped = cv2.warpPerspective(img, homography(pose, width, height, level), (2 * width, 2 * height),
                                     flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=NAVY)
        if acc is None:
            acc = warped.astype(np.float32)
        else:
            cv2.add(acc, warped.astype(np.float32), acc)
    if samples > 1:
        acc *= 1.0 / samples
    if need > samples:
        # Too fast for the sample budget (whips): smear the gaps along the centre's motion.
        dx, dy = travel[4] / samples
        kernel = line_kernel(float(dx), float(dy))
        if kernel is not None:
            acc = cv2.filter2D(acc, -1, kernel, borderType=cv2.BORDER_REPLICATE)
    frame = np.clip(acc, 0, 255).astype(np.uint8)
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)


def write_poses(path: Path, shot: str, aspect: str, cam: Camera, frames: int, spec: dict) -> None:
    """Per-frame camera poses, so overlays in the composition can stick to points in the footage."""
    poses = []
    for n in range(frames):
        p = cam.pose(n / FPS)
        poses.append([round(p["cx"], 2), round(p["cy"], 2), round(p["z"], 5)])
    body = json.dumps({"fps": FPS, "start": spec.get("reel", [0, 0])[0], "frames": poses}, separators=(",", ":"))
    path.write_text(
        "/* Generated by tools/camera.py: per-frame [cx, cy, z] of the virtual camera (source px). */\n"
        f"(window.R = window.R || {{}}).POSES = Object.assign(window.R.POSES || {{}}, {{{json.dumps(shot)}: {body}}});\n")


def encoder(path: Path, width: int, height: int) -> subprocess.Popen:
    return subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}",
         "-r", str(FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-colorspace", "bt709", "-color_primaries", "bt709",
         "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)


def load_spec(path: str):
    """Import a shot-list module by file path; the default is tools/shots.py (the reel)."""
    if not path:
        return shots
    import importlib.util
    file = Path(path).resolve()
    sys.path.insert(0, str(file.parent))
    module_spec = importlib.util.spec_from_file_location(file.stem.replace("-", "_"), file)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--aspect", default="16x9")
    ap.add_argument("--spec", default="", help="shot-list module path (default: tools/shots.py)")
    ap.add_argument("--out", default="", help="output directory (default: assets/shots)")
    ap.add_argument("--takes", default="", help="folder with latest-<take>.json (default: build/reel-takes)")
    ap.add_argument("--stills", default="", help="comma-separated clip times to render as PNG")
    ap.add_argument("--shutter", type=float, default=None, help="shutter in frames (0.5 = 180 degrees)")
    ap.add_argument("--kmax", type=int, default=32)
    ap.add_argument("--poses-only", action="store_true", help="write the per-frame pose file without rendering")
    args = ap.parse_args()

    module = load_spec(args.spec)
    sizes = {**ASPECTS, **getattr(module, "ASPECT_SIZE", {})}
    if args.aspect not in sizes:
        raise SystemExit(f"Unknown aspect {args.aspect}; known: {', '.join(sorted(sizes))}")
    width, height = sizes[args.aspect]
    spec = module.build(args.shot, args.aspect)
    takes = Path(args.takes) if args.takes else REPO / "build/reel-takes"
    meta = json.loads((takes / f"latest-{spec['take']}.json").read_text())
    tmap, cam = TimeMap(spec["retime"]), Camera(spec["camera"])
    shutter = args.shutter if args.shutter is not None else spec.get("shutter", 0.5)
    out_dir = Path(args.out).resolve() if args.out else ROOT / "assets/shots"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{args.shot}-{args.aspect}"

    if args.stills:
        still_dir = ROOT / "build/stills"
        still_dir.mkdir(parents=True, exist_ok=True)
        for value in args.stills.split(","):
            t = float(value)
            start = max(0.0, tmap.src(max(0.0, t - 0.05)) - 0.25)
            src = Source(Path(meta["path"]), meta["width"], meta["height"], start=start, limit=90)
            frame = render_frame(src, cam, tmap, t, width, height, shutter, args.kmax)
            src.close()
            path = still_dir / f"{name}-{t:.3f}.png"
            cv2.imwrite(str(path), frame)
            print(path)
        return

    frames = int(round(tmap.duration * FPS))
    write_poses(out_dir / f"{name}.poses.js", args.shot, args.aspect, cam, frames, spec)
    if args.poses_only:
        return
    out_path = out_dir / f"{name}.mp4"
    enc = encoder(out_path, width, height)
    src = Source(Path(meta["path"]), meta["width"], meta["height"])
    started = time.time()
    for n in range(frames):
        frame = render_frame(src, cam, tmap, n / FPS, width, height, shutter, args.kmax)
        enc.stdin.write(frame.tobytes())
        if n % 60 == 0:
            print(f"{name}: {n}/{frames} ({time.time() - started:.0f}s)", flush=True)
    src.close()
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("ffmpeg failed to encode the shot")
    info = {"shot": args.shot, "aspect": args.aspect, "take": spec["take"], "source": meta["path"],
            "fps": FPS, "frames": frames, "duration": frames / FPS, "reel": spec.get("reel"),
            "retime": spec["retime"], "camera": spec["camera"], "shutter": shutter}
    (out_dir / f"{name}.json").write_text(json.dumps(info, indent=2) + "\n")
    print(out_path, f"{time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
