#!/usr/bin/env python3
"""clipsheet.py CLIP.mp4 OUT.jpg STEP [COLS] [START] [END]: labelled frames every STEP seconds."""
import subprocess
import sys
import tempfile
from pathlib import Path

clip, out, step = sys.argv[1], sys.argv[2], float(sys.argv[3])
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                           capture_output=True, text=True).stdout)
start = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
end = min(float(sys.argv[6]) if len(sys.argv) > 6 else dur, dur - 0.02)
with tempfile.TemporaryDirectory() as tmp:
    files, t = [], start
    while t <= end + 1e-6:
        name = Path(tmp) / f"t{t:06.3f}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.4f}", "-i", clip, "-frames:v", "1", str(name)], check=True)
        files.append(str(name))
        t += step
    subprocess.run([sys.executable, str(Path(__file__).with_name("sheet.py")), out, str(cols), *files], check=True)
