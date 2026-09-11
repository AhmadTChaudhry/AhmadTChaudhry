"""Pixel-art toolkit: a hand-authored 5x7 bitmap font and a tiny pixel canvas.

Everything on this profile is drawn one pixel at a time and upscaled with
nearest-neighbour sampling, then given CRT scanlines. No external fonts,
no image assets, no third-party services.
"""
import math
import numpy as np
from PIL import Image

ptGLYPHS = {}

_RAW = r"""
A
.###.
#...#
#...#
#####
#...#
#...#
#...#
B
####.
#...#
#...#
####.
#...#
#...#
####.
C
.###.
#...#
#....
#....
#....
#...#
.###.
D
####.
#...#
#...#
#...#
#...#
#...#
####.
E
#####
#....
#....
####.
#....
#....
#####
F
#####
#....
#....
####.
#....
#....
#....
G
.###.
#...#
#....
#.###
#...#
#...#
.###.
H
#...#
#...#
#...#
#####
#...#
#...#
#...#
I
#####
..#..
..#..
..#..
..#..
..#..
#####
J
..###
...#.
...#.
...#.
...#.
#..#.
.##..
K
#...#
#..#.
#.#..
##...
#.#..
#..#.
#...#
L
#....
#....
#....
#....
#....
#....
#####
M
#...#
##.##
#.#.#
#.#.#
#...#
#...#
#...#
N
#...#
##..#
#.#.#
#..##
#...#
#...#
#...#
O
.###.
#...#
#...#
#...#
#...#
#...#
.###.
P
####.
#...#
#...#
####.
#....
#....
#....
Q
.###.
#...#
#...#
#...#
#.#.#
#..#.
.##.#
R
####.
#...#
#...#
####.
#.#..
#..#.
#...#
S
.####
#....
#....
.###.
....#
....#
####.
T
#####
..#..
..#..
..#..
..#..
..#..
..#..
U
#...#
#...#
#...#
#...#
#...#
#...#
.###.
V
#...#
#...#
#...#
#...#
#...#
.#.#.
..#..
W
#...#
#...#
#...#
#.#.#
#.#.#
##.##
#...#
X
#...#
#...#
.#.#.
..#..
.#.#.
#...#
#...#
Y
#...#
#...#
.#.#.
..#..
..#..
..#..
..#..
Z
#####
....#
...#.
..#..
.#...
#....
#####
0
.###.
#...#
#..##
#.#.#
##..#
#...#
.###.
1
..#..
.##..
..#..
..#..
..#..
..#..
.###.
2
.###.
#...#
....#
...#.
..#..
.#...
#####
3
#####
...#.
..#..
...#.
....#
#...#
.###.
4
...#.
..##.
.#.#.
#..#.
#####
...#.
...#.
5
#####
#....
####.
....#
....#
#...#
.###.
6
..##.
.#...
#....
####.
#...#
#...#
.###.
7
#####
....#
...#.
..#..
.#...
.#...
.#...
8
.###.
#...#
#...#
.###.
#...#
#...#
.###.
9
.###.
#...#
#...#
.####
....#
...#.
.##..
.
.....
.....
.....
.....
.....
.##..
.##..
,
.....
.....
.....
.....
.##..
.##..
.#...
'
..#..
..#..
.....
.....
.....
.....
.....
!
..#..
..#..
..#..
..#..
..#..
.....
..#..
?
.###.
#...#
....#
...#.
..#..
.....
..#..
-
.....
.....
.....
#####
.....
.....
.....
:
.....
.##..
.##..
.....
.##..
.##..
.....
/
....#
...#.
...#.
..#..
.#...
.#...
#....
&
.##..
#..#.
#.#..
.#...
#.#.#
#..#.
.##.#
+
.....
..#..
..#..
#####
..#..
..#..
.....
(
..#..
.#...
#....
#....
#....
.#...
..#..
)
..#..
...#.
....#
....#
....#
...#.
..#..
>
#....
.#...
..#..
...#.
..#..
.#...
#....
*
.....
..#..
#.#.#
.###.
#.#.#
..#..
.....
=
.....
.....
#####
.....
#####
.....
.....
_
.....
.....
.....
.....
.....
.....
#####
@
.###.
#...#
#.##.
#.#.#
#.###
#....
.###.
"""

def _build():
    lines = [l for l in _RAW.split("\n")]
    i = 0
    while i < len(lines):
        if lines[i] == "":
            i += 1
            continue
        ch = lines[i]
        rows = lines[i+1:i+8]
        ptGLYPHS[ch] = rows
        i += 8
    ptGLYPHS[" "] = ["....."] * 7
    # middot rendered as a narrow dot
    ptGLYPHS["·"] = ["....."] * 3 + ["..#.."] + ["....."] * 3

_build()

CHAR_W, CHAR_H, ADVANCE = 5, 7, 6


def text_width(s, scale=1, tracking=0):
    return (len(s) * (ADVANCE + tracking) - (1 + tracking)) * scale


def draw_text(put, x, y, s, color, scale=1, tracking=0):
    """put(px, py, color) draws one native pixel."""
    cx = x
    for ch in s.upper():
        g = ptGLYPHS.get(ch)
        if g is None:
            g = ptGLYPHS["?"]
        for ry in range(CHAR_H):
            row = g[ry]
            for rx in range(CHAR_W):
                if row[rx] == "#":
                    for sy in range(scale):
                        for sx in range(scale):
                            put(cx + rx*scale + sx, y + ry*scale + sy, color)
        cx += (ADVANCE + tracking) * scale
    return cx


# ---- palette -------------------------------------------------------------
VOID    = (11, 10, 20)
NIGHT   = (22, 20, 42)
NIGHT2  = (30, 27, 56)
PANEL   = (34, 31, 58)
LINE    = (59, 53, 96)
PCB_DK  = (18, 58, 46)
PCB     = (27, 94, 74)
TRACE   = (47, 163, 123)
GOLD    = (232, 184, 75)
GOLD_D  = (168, 122, 34)
CREAM   = (244, 236, 216)
DIM     = (138, 132, 166)
RED     = (217, 79, 69)
SKIN    = (224, 160, 112)
CYAN    = (91, 209, 215)
WIN     = (159, 216, 232)

SCALE = 3


class C:
    def __init__(self, w, h, bg=VOID):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 3), np.uint8)
        self.a[:, :] = bg

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[int(y), int(x)] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = c

    def frame(self, x, y, w, h, c):
        self.rect(x, y, w, 1, c); self.rect(x, y + h - 1, w, 1, c)
        self.rect(x, y, 1, h, c); self.rect(x + w - 1, y, 1, h, c)

    def text(self, x, y, s, c, scale=1, tracking=0):
        return draw_text(self.put, x, y, s, c, scale, tracking)

    def ctext(self, cx, y, s, c, scale=1, tracking=0):
        w = text_width(s, scale, tracking)
        return self.text(cx - w // 2, y, s, c, scale, tracking)

    def sprite(self, x, y, rows, cmap):
        for ry, row in enumerate(rows):
            for rx, ch in enumerate(row):
                if ch in cmap:
                    self.put(x + rx, y + ry, cmap[ch])

    def arc(self, cx, cy, r, a0, a1, c, thin=True):
        steps = max(8, int(r * 3))
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            self.put(round(cx + r * math.cos(a)), round(cy + r * math.sin(a)), c)

    def line(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(int(n) + 1):
            t = i / max(n, 1)
            self.put(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.put(x, y, c)

    def img(self):
        return Image.fromarray(self.a, "RGB")


def upscale(c, scanlines=True, bezel=True):
    im = c.img().resize((c.w * SCALE, c.h * SCALE), Image.NEAREST)
    a = np.asarray(im).astype(np.int16)
    if scanlines:
        a[2::SCALE] = (a[2::SCALE] * 0.82).astype(np.int16)
    a = np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGB")
    return im


