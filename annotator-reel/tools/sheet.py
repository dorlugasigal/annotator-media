#!/usr/bin/env python3
"""Tile PNG stills into one labelled review sheet: sheet.py OUT.jpg COLS FILE..."""
import sys
from pathlib import Path

import cv2
import numpy as np

out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tiles = []
for f in files:
    img = cv2.imread(f)
    h, w = img.shape[:2]
    scale = 640 / w
    img = cv2.resize(img, (640, int(h * scale)), interpolation=cv2.INTER_AREA)
    label = Path(f).stem
    cv2.rectangle(img, (0, 0), (len(label) * 11 + 12, 26), (0, 0, 0), -1)
    cv2.putText(img, label, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    tiles.append(img)
th = max(t.shape[0] for t in tiles)
tiles = [cv2.copyMakeBorder(t, 0, th - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(60, 60, 60)) for t in tiles]
while len(tiles) % cols:
    tiles.append(np.full_like(tiles[0], 60))
rows = [cv2.hconcat(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, cv2.vconcat(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
print(out)
