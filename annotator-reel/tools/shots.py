"""Shot list for the Annotator reel: retime anchors and camera keys per take and aspect.

Everything is timed in beats of the music bed (130 BPM). Clip time 0 is the moment the shot starts in the
reel; `k` is the beat offset inside the clip (clip seconds = k * B). Source times come from the recorded
press/release samples in build/reel-takes/latest-<take>.json. Rectangles are source pixels of the 3840x2160
capture (sample window 340..3500 x 48..1428, toolbar underneath).
"""
from __future__ import annotations

BPM = 130.0  # "Product Launch Advertising Commercial Music" by lNPLUSMUSIC (Pixabay), 129.98 BPM
B = 60.0 / BPM
FPS = 60
FRAMES = 1772  # 64 beats at 130 BPM, rounded down to whole frames (index.html data-duration)
TOTAL = FRAMES / FPS
ASPECT_SIZE = {"16x9": (1920, 1080), "4x5": (1080, 1350)}
ZMIN = {"16x9": 0.5, "4x5": 0.42}
ZMAX = 1.15
WIN = (340, 48, 3500, 1428)       # x0, y0, x1, y1: views that must stay inside the sample app
ALL = (340, 48, 3500, 1840)       # views that also show the toolbar under the app
WINDOW = (340, 48, 3160, 1380)
TOOLBAR = (988, 1456, 1864, 360)

# Reel placement as 1-based beat numbers [start, end): beat n starts at (n - 1) * B. 64 beats = 16 bars.
# Bars start on beats 2, 6, 10, ...: the music's downbeats fall on "Draw", the cuts (30, 42) and the end card (58).
BEATS = {"dashboard": (4, 30), "smart": (30, 42), "focus": (42, 58)}
REEL = {name: ((a - 1) * B, (b - 1) * B) for name, (a, b) in BEATS.items()}
WHIP_PX = 1300  # output px travelled by the whip either side of the cut

# Toolbar button centres (source px), measured from the idle toolbar in the dashboard take.
BUTTONS = {
    "select": 1055, "rectangle": 1166, "diamond": 1258, "ellipse": 1350, "arrow": 1442, "line": 1534,
    "pen": 1643, "text": 1735, "highlighter": 1828, "eraser": 1938, "effects": 2048, "library": 2148,
    "desk": 2262, "draw": 2378,
}
BUTTON_ROW_Y = 1516  # icon row centre; shortcut numbers sit at ~1553


def union(*rects):
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)


def clamp(aspect, pose, region):
    width, height = ASPECT_SIZE[aspect]
    vw, vh = width / pose["z"], height / pose["z"]
    x0, y0, x1, y1 = region
    out = dict(pose)
    if vw <= x1 - x0:
        out["cx"] = min(max(out["cx"], x0 + vw / 2), x1 - vw / 2)
    if vh <= y1 - y0:
        out["cy"] = min(max(out["cy"], y0 + vh / 2), y1 - vh / 2)
    return out


def view(aspect, rect, pad=0, region=None, zmax=ZMAX, bias=(0.0, 0.0)):
    x, y, w, h = rect
    px, py = pad if isinstance(pad, tuple) else (pad, pad)
    width, height = ASPECT_SIZE[aspect]
    z = min(width / (w + 2 * px), height / (h + 2 * py))
    pose = {"cx": x + w / 2 + bias[0], "cy": y + h / 2 + bias[1], "z": max(ZMIN[aspect], min(zmax, z))}
    return clamp(aspect, pose, region) if region else pose


def key(k, pose, ease="inOutCubic", **extra):
    """Camera key at beat offset k inside the clip."""
    out = {"t": round(k * B, 4), "ease": ease, "rx": 0.0, "ry": 0.0}
    out.update({name: pose[name] for name in ("cx", "cy", "z")})
    out.update(extra)
    return out


def push(aspect, pose, factor, region=None, dx=0.0, dy=0.0):
    out = dict(pose, z=pose["z"] * factor, cx=pose["cx"] + dx, cy=pose["cy"] + dy)
    return clamp(aspect, out, region) if region else out


def whip(pose, direction):
    """Pose offset along x by the whip distance (direction -1 = camera travelling left)."""
    return dict(pose, cx=pose["cx"] + direction * WHIP_PX / pose["z"])


def beats(pairs):
    """(source seconds, beat offset) anchors -> (source seconds, clip seconds)."""
    return [(src, round(k * B, 5)) for src, k in pairs]


def tour(a):
    """Toolbar close-up: the idle toolbar fills the upper half, tool labels live on the desktop below."""
    if a == "4x5":  # portrait: tighter, with the chart's dip above the toolbar for context
        z = 1.4
        return {"cx": 2440, "cy": 1500, "z": z}, {"cx": 1400, "cy": 1500, "z": z}
    z = 1.35
    return {"cx": 2240, "cy": 1600, "z": z}, {"cx": 1640, "cy": 1600, "z": z}


def dashboard(a):
    wide = view(a, union(WINDOW, TOOLBAR), 60)
    tour_a, tour_b = tour(a)
    kpi = view(a, (1486, 324, 630, 192), (250, 190), WIN)
    picks = view(a, (820, 600, 1700, 1200), 20, ALL)
    # The Stroke color popover spans (766, 456)-(1330, 1406); it sits near the window's left edge.
    picker = {"cx": 1110, "cy": 925, "z": 1.04} if a == "16x9" else {"cx": 1048, "cy": 925, "z": 1.18}
    arrow = view(a, (1440, 440, 330, 760), (480, 120), WIN)
    note_wide = view(a, (1700, 600, 1600, 1000), 20, ALL)
    note = view(a, (2560, 620, 690, 90), (380, 280), WIN)
    retime = beats([
        (0.00, 0), (0.05, 1), (1.10, 7),                  # idle toolbar for the tour; the pointer rests off-frame
        (1.645, 8),                                       # the pointer arrives and chooses Ellipse on beat 12
        (2.28, 9), (3.34, 10.75),                         # rough teal ellipse round the KPI
        (3.81, 11.5), (4.55, 12.5),                       # Arrow, then Stroke color
        (5.94, 14.5),                                     # hover on Blue, then choose it
        (6.54, 15.25), (7.03, 16), (7.61, 16.75), (7.90, 17.25),  # three arrow points, Return
        (8.57, 18), (9.34, 19.5),                         # drag the middle point: the arrow bends
        (10.40, 21.25),                                   # pause, hover, choose Highlighter
        (11.08, 22.25), (12.04, 24),                      # highlight the note
        (12.64, 26),
    ])
    end = push(a, note, 1.06, WIN)
    camera = [
        key(0, push(a, wide, 0.96), rx=5.0, ry=-7.0),
        key(0.9, wide, "out"),
        key(2.0, tour_a, "inOutCubic"),                   # dive onto the toolbar
        key(7.4, tour_b, "inOut"),                        # a slow glide across the tools
        key(8.1, push(a, tour_b, 1.02), "inOut"),
        key(9.0, kpi, "inOutCubic"),                      # crane up to the KPI as the drag starts
        key(10.75, push(a, kpi, 1.04, WIN), "inOut"),
        key(11.45, picks, "inOutCubic"),                  # the toolbar: Arrow, Stroke color
        key(12.55, push(a, picks, 1.02, ALL, dx=-20), "inOut"),
        key(13.15, picker, "inOutCubic"),                 # centre on the colour picker
        key(14.6, push(a, picker, 1.03), "inOut"),
        key(15.2, arrow, "inOutCubic"),
        key(18.0, push(a, arrow, 1.03, WIN), "inOut"),
        key(19.5, push(a, arrow, 1.06, WIN), "inOut"),
        key(20.2, note_wide, "inOutCubic"),               # toolbar Highlighter and the note together
        key(21.4, push(a, note_wide, 1.02, ALL), "inOut"),
        key(23.0, note, "inOutCubic"),                    # push in while the note is highlighted
        key(25.8, end, "inOut"),
        key(26, whip(end, -1), "in"),
    ]
    return {"take": "dashboard", "retime": retime, "camera": camera, "shutter": 0.5}


def smart(a):
    phone = view(a, (1400, 200, 1200, 1000), 0, WIN, bias=(200, 0))
    pay = view(a, (1638, 948, 172, 52), (340, 260), WIN)
    arrow = view(a, (1540, 880, 1050, 200), (170, 230), WIN)
    label = view(a, (1850, 900, 800, 150), (160, 230), WIN)
    retime = beats([
        (0.40, 0), (0.653, 0.5), (1.24, 1.25),            # Pen, then the rough stroke
        (3.05, 4),                                        # release: Smart Draw snaps the box on beat 34
        (3.59, 4.75), (4.39, 6),                          # a rough arrow snaps clean
        (5.03, 6.75), (5.64, 7.5), (6.50, 9),             # Text, click, type the label
        (7.36, 12),
    ])
    zoom_in = dict(label, z=label["z"] * 3.0, cx=2370, cy=972)
    camera = [
        key(0, whip(push(a, phone, 1.02), 1), "linear"),
        key(0.45, phone, "outQuart"),
        key(1.2, push(a, phone, 1.01), "inOut"),
        key(2.1, pay, "inOutCubic"),
        key(3.95, push(a, pay, 1.03, WIN), "inOut"),
        key(4.08, push(a, pay, 1.08), "out"),             # a small punch on the snap
        key(4.4, push(a, pay, 1.02, WIN), "inOut"),
        key(5.0, arrow, "inOutCubic"),
        key(6.2, push(a, arrow, 1.03), "inOut"),
        key(7.0, label, "inOutCubic"),
        key(11.55, push(a, label, 1.06, WIN), "inOut"),
        key(12, zoom_in, "inExpo"),                       # zoom through the label into the next shot
    ]
    return {"take": "smart", "retime": retime, "camera": camera, "shutter": 0.5}


def focus(a):
    button = {"cx": BUTTONS["library"], "cy": 1532, "z": 3.0}
    lib = view(a, (900, 350, 1400, 1250), 20, ALL)
    tiles = view(a, (988, 372, 880, 460), (300, 240), WIN)
    board = view(a, WINDOW, 40)
    if a == "4x5":  # portrait cannot hold the whole board: track the spotlight from picture to picture
        board_a = view(a, (340, 48, 1700, 1380), 0, WIN)
        board_b = view(a, (1500, 48, 1700, 1380), 0, WIN)
    else:
        board_a, board_b = board, push(a, board, 1.05, dx=160, dy=-20)
    hero = view(a, (1938, 264, 735, 538), (230, 170), WIN)
    # Toolbar close-up for Stop spotlight (1142, 1636) and Effects (2048, 1528): the blur tool must be seen.
    fx = {"cx": 1600, "cy": 1560, "z": 1.35} if a == "16x9" else {"cx": 1595, "cy": 1470, "z": 0.98}
    busy = view(a, (396, 838, 735, 538), (230, 170), WIN)
    retime = beats([
        (0.40, 0), (0.70, 0.5),                           # Tool library
        (1.43, 1.75), (2.04, 2.75), (2.62, 3.5),          # Cursor halo, Spotlight, close the library
        (3.37, 4.5), (4.61, 6), (5.73, 7.5), (6.25, 8),   # the spotlight walks and clicks each picture
        (6.66, 8.5), (7.32, 9.5),                         # stop the spotlight, choose Effects
        (8.02, 10.5), (9.64, 12.5),                       # drag the blur region over the busy tile
        (9.95, 13.25), (10.21, 16),                       # the blur lands; hold under the end card
    ])
    camera = [
        key(0, button, "linear"),
        key(0.45, lib, "outQuart"),
        key(1.0, push(a, lib, 1.02), "inOut"),
        key(1.5, tiles, "inOutCubic"),
        key(3.4, push(a, tiles, 1.02, WIN), "inOut"),
        key(4.2, board_a, "inOutCubic"),
        key(7.0, board_b, "inOut"),
        key(7.6, hero, "inOutCubic"),
        key(7.95, push(a, hero, 1.02, WIN), "inOut"),
        key(8.45, fx, "inOutCubic"),                      # follow the pointer down to the toolbar
        key(9.8, push(a, fx, 1.02), "inOut"),             # hold: Stop spotlight, then Effects
        key(10.5, busy, "inOutCubic"),                    # follow it back up as the blur drag starts
        key(12.6, push(a, busy, 1.03, WIN), "inOut"),
        key(16, push(a, busy, 1.12, WIN), "inOut"),
    ]
    return {"take": "focus", "retime": retime, "camera": camera, "shutter": 0.5}


SHOTS = {"dashboard": dashboard, "smart": smart, "focus": focus}


def build(name: str, aspect: str) -> dict:
    spec = SHOTS[name](aspect)
    spec["reel"] = REEL[name]
    return spec
