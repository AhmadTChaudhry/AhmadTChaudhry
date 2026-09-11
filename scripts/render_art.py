"""Redraws the three animated panels on the profile. Run: python scripts/render_art.py"""
import math, os, random
import numpy as np
from PIL import Image
from pixel import (C, upscale, draw_text, text_width, SCALE,
                   VOID, NIGHT, NIGHT2, PANEL, LINE, PCB_DK, PCB, TRACE,
                   GOLD, GOLD_D, CREAM, DIM, RED, SKIN, CYAN, WIN)

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUT, exist_ok=True)

HERO = [
    "....KKKK....",
    "...KKKKKKK..",
    "..KKSSSSSKK.",
    "..KSSSSSSSK.",
    "...SESSSES..",
    "...SSSSSSS..",
    "....SSSSS...",
    "....TTTTT...",
    "...TTTTTTT..",
    "..STTTTTTTS.",
    "..STTTTTTTS.",
    "...TTTTTTT..",
    "....PPPPP...",
    "....PP.PP...",
    "....PP.PP...",
    "...BBB.BBB..",
]
HERO_MAP = {"K": (42, 36, 56), "S": SKIN, "E": VOID, "T": RED, "P": PANEL, "B": VOID}

random.seed(7)
STARS = [(random.randrange(4, 316), random.randrange(4, 60)) for _ in range(38)]
TWINKLE = set(random.sample(range(38), 12))


def pcb_ground(c, y0):
    """Circuit-board terrain filling from y0 to the bottom."""
    c.rect(0, y0, c.w, c.h - y0, PCB_DK)
    c.rect(0, y0, c.w, 1, TRACE)
    # horizontal traces
    for i, yy in enumerate((y0 + 7, y0 + 15, y0 + 24, y0 + 33)):
        c.rect(6 + i * 5, yy, c.w - 20 - i * 6, 1, PCB)
    # vias / pads
    for i in range(0, c.w, 17):
        yy = y0 + 7 + (i // 17 % 4) * 8
        c.rect(i + 5, yy - 1, 3, 3, PCB)
        c.put(i + 6, yy, PCB_DK)
    # diagonal trace flourishes
    for k in range(6):
        x = 22 + k * 48
        for d in range(7):
            c.put(x + d, y0 + 5 + d, PCB)


def dip_chip(c, x, ybase, w, h, lit, label=None):
    top = ybase - h
    c.rect(x, top, w, h, VOID)
    c.frame(x, top, w, h, LINE)
    # pins
    for i in range(2, w - 2, 3):
        c.rect(x + i, ybase, 2, 2, GOLD_D)
    # notch
    c.rect(x + w // 2 - 1, top + 1, 2, 1, LINE)
    if label:
        c.text(x + (w - text_width(label, 1)) // 2, top + (h - 7) // 2, label, GOLD, 1)
        return
    # lit windows
    for row in range(2):
        for col in range((w - 6) // 4):
            on = ((col + row * 3 + lit) % 4) != 0
            c.rect(x + 3 + col * 4, top + 4 + row * 5, 2, 3,
                   GOLD if on else (30, 28, 48))


def capacitor(c, x, ybase, h, col=CYAN):
    c.rect(x, ybase - h, 5, h, PANEL)
    c.frame(x, ybase - h, 5, h, LINE)
    c.rect(x + 1, ybase - h + 2, 3, 2, col)
    c.rect(x + 1, ybase - h - 1, 3, 1, LINE)


def resistor(c, x, y, bands=(GOLD, RED, CYAN)):
    c.rect(x, y, 16, 5, (96, 84, 64))
    c.rect(x - 3, y + 2, 3, 1, DIM)
    c.rect(x + 16, y + 2, 3, 1, DIM)
    for i, b in enumerate(bands):
        c.rect(x + 3 + i * 4, y, 2, 5, b)


def tower(c, x, ybase, top, blink):
    """Lattice antenna mast. Returns the tip coordinate."""
    half_b, half_t = 11, 3
    n = ybase - top
    for i in range(n + 1):
        t = i / n
        hw = half_b + (half_t - half_b) * t
        y = ybase - i
        c.put(round(x - hw), y, LINE)
        c.put(round(x + hw), y, LINE)
    # cross bracing
    for i in range(0, n - 3, 7):
        t0, t1 = i / n, min(1.0, (i + 7) / n)
        hw0 = half_b + (half_t - half_b) * t0
        hw1 = half_b + (half_t - half_b) * t1
        y0, y1 = ybase - i, ybase - min(n, i + 7)
        c.line(x - hw0, y0, x + hw1, y1, PANEL)
        c.line(x + hw0, y0, x - hw1, y1, PANEL)
        c.rect(round(x - hw1), y1, round(2 * hw1) + 1, 1, LINE)
    # mast
    c.rect(x, top - 6, 1, 6, LINE)
    tip = (x, top - 6)
    c.rect(x - 1, top - 8, 3, 2, RED if blink else (70, 34, 32))
    return tip


# ==========================================================================
# HEADER
# ==========================================================================
def header_frame(f, nframes):
    W, H = 320, 126
    c = C(W, H, NIGHT)
    c.rect(0, 70, W, 20, NIGHT2)

    for i, (sx, sy) in enumerate(STARS):
        if i in TWINKLE and ((f // 5) + i) % 3 == 0:
            continue
        c.put(sx, sy, CREAM if i % 4 else DIM)

    # moon, top right
    c.disc(298, 15, 7, CREAM)
    c.disc(294, 12, 6, NIGHT)
    c.put(301, 18, (214, 206, 188)); c.put(300, 11, (214, 206, 188))

    GROUND = 96
    pcb_ground(c, GROUND)

    blink = (f % 24) < 4 or 12 <= (f % 24) < 16
    tip = tower(c, 28, GROUND, 60, blink)

    # radio arcs from the mast tip
    for k in range(3):
        phase = ((f + k * 8) % 24) / 24.0
        r = 8 + phase * 26
        col = GOLD if phase < 0.45 else GOLD_D
        if phase < 0.9:
            c.arc(tip[0], tip[1], r, -62, 62, col)

    dip_chip(c, 116, GROUND, 36, 22, f // 6, "ESP32")
    dip_chip(c, 232, GROUND, 26, 16, f // 6 + 2)
    capacitor(c, 160, GROUND, 15, CYAN)
    capacitor(c, 168, GROUND, 11, RED)
    capacitor(c, 268, GROUND, 13, GOLD)
    resistor(c, 186, GROUND - 7)
    c.rect(210, GROUND - 9, 12, 9, PANEL); c.frame(210, GROUND - 9, 12, 9, LINE)
    c.rect(212, GROUND - 7, 8, 3, DIM)
    led_on = (f // 4) % 2 == 0
    c.rect(292, GROUND - 5, 3, 5, GOLD if led_on else GOLD_D)
    c.rect(291, GROUND - 6, 5, 1, LINE)

    bob = 1 if (f % 24) >= 12 else 0
    c.sprite(74, GROUND - 16 + bob, HERO, HERO_MAP)

    # ---- title
    c.ctext(160, 9, "AHMAD TAHIR CHAUDHRY", GOLD_D, 2)      # drop shadow
    c.ctext(159, 8, "AHMAD TAHIR CHAUDHRY", CREAM, 2)
    c.ctext(160, 29, "AI PRODUCT ENGINEER", GOLD, 1, 1)
    c.ctext(160, 41, "MELBOURNE, AUSTRALIA", DIM, 1)

    if (f % 24) < 17:
        c.ctext(163, 58, "PRESS START", CREAM, 1, 1)
        c.rect(163 - text_width("PRESS START", 1, 1) // 2 - 8, 58, 1, 7, GOLD)
        c.rect(163 - text_width("PRESS START", 1, 1) // 2 - 7, 59, 1, 5, GOLD)
        c.rect(163 - text_width("PRESS START", 1, 1) // 2 - 6, 60, 1, 3, GOLD)
        c.rect(163 - text_width("PRESS START", 1, 1) // 2 - 5, 61, 1, 1, GOLD)

    c.frame(0, 0, W, H, LINE)
    c.frame(1, 1, W - 2, H - 2, VOID)
    return c


# ==========================================================================
# EQUIPMENT PANEL
# ==========================================================================
ROWS = [
    ("LANGUAGES",  "TYPESCRIPT  JAVASCRIPT  PYTHON  C++  SQL"),
    ("FRONTEND",   "REACT  NEXT.JS  VITE  TAILWIND  SHADCN/UI"),
    ("BACKEND",    "NODE  EXPRESS  POSTGRES  DRIZZLE  DOCKER"),
    ("AI/AGENTS",  "OPENAI  GEMINI  N8N  AGENT WORKFLOWS"),
    ("EMBEDDED",   "ESP32  LORA  PLATFORMIO  WLED  NODE-RED"),
]


def panel_frame(f):
    W, H = 320, 137
    c = C(W, H, VOID)
    c.frame(2, 2, W - 4, H - 4, LINE)
    c.frame(4, 4, W - 8, H - 8, CREAM)
    c.rect(6, 6, W - 12, H - 12, PANEL)

    c.rect(6, 6, W - 12, 12, LINE)
    c.text(12, 8, "EQUIPMENT", GOLD, 1, 1)
    c.text(W - 12 - text_width("LV.99", 1, 1), 8, "LV.99", CREAM, 1, 1)

    y = 26
    for i, (label, items) in enumerate(ROWS):
        sel = (f // 8) % 5 == i
        if sel:
            c.rect(10, y - 2, W - 20, 20, LINE)
            c.rect(14, y + 1, 1, 5, GOLD)
            c.rect(15, y + 2, 1, 3, GOLD)
            c.rect(16, y + 3, 1, 1, GOLD)
        c.text(22, y, label, GOLD if sel else GOLD_D, 1, 1)
        c.text(22, y + 9, items, CREAM if sel else DIM, 1)
        y += 21
    return c


# ==========================================================================
# FOOTER
# ==========================================================================
def tram(c, x, y):
    """Melbourne tram, 46x20, drawn from its top-left corner."""
    W = 46
    c.rect(x + 2, y + 3, W - 4, 15, PCB)
    c.frame(x + 2, y + 3, W - 4, 15, VOID)
    c.rect(x + 3, y + 2, W - 6, 1, VOID)
    # windows
    for i in range(5):
        c.rect(x + 5 + i * 8, y + 5, 6, 5, WIN)
        c.frame(x + 5 + i * 8, y + 5, 6, 5, VOID)
    # gold livery stripe
    c.rect(x + 3, y + 11, W - 6, 2, GOLD)
    c.rect(x + 3, y + 15, W - 6, 2, PCB_DK)
    # headlight
    c.rect(x + W - 4, y + 13, 2, 2, CREAM)
    # skirt + wheels
    c.rect(x + 4, y + 18, W - 8, 1, VOID)
    for wx in (x + 9, x + W - 14):
        c.rect(wx, y + 18, 5, 3, VOID)
        c.rect(wx + 1, y + 19, 3, 1, (70, 66, 92))
    # pantograph
    for d in range(5):
        c.put(x + 18 + d, y + 2 - d, DIM)
        c.put(x + 28 - d, y + 2 - d, DIM)
    c.rect(x + 16, y - 3, 14, 1, DIM)


def footer_frame(f, nframes):
    W, H = 320, 80
    c = C(W, H, NIGHT)
    for i, (sx, sy) in enumerate(STARS[:16]):
        c.put(sx, sy % 11 + 2, CREAM if i % 3 else DIM)

    c.ctext(160, 18, "THANKS FOR PLAYING", CREAM, 1, 1)
    if (f % 24) < 17:
        c.ctext(160, 30, "CONTINUE AT AHMADTC.COM", GOLD, 1)

    # overhead wire with hangers
    c.rect(0, 42, W, 1, LINE)
    for px in range(10, W, 70):
        c.rect(px, 37, 1, 5, LINE)
        c.rect(px - 2, 37, 5, 1, LINE)

    GROUND = 64
    c.rect(0, GROUND, W, H - GROUND, PCB_DK)
    c.rect(0, GROUND, W, 1, TRACE)
    c.rect(0, 66, W, 1, DIM)
    for px in range(-((f * 2) % 12), W, 12):
        c.rect(px, 69, 6, 1, PCB)
    c.rect(8, 73, W - 30, 1, PCB)
    for px in range(14, W, 19):
        c.rect(px, 75, 3, 3, PCB)
        c.put(px + 1, 76, PCB_DK)

    x = -72 + int((f / nframes) * (W + 78))
    tram(c, x, 45)

    c.frame(0, 0, W, H, LINE)
    return c


# ==========================================================================
def save_gif(path, frames, duration):
    imgs = [upscale(f) for f in frames]
    pal = imgs[0].convert("P", palette=Image.ADAPTIVE, colors=64)
    conv = [im.convert("RGB").quantize(palette=pal, dither=Image.NONE) for im in imgs]
    conv[0].save(path, save_all=True, append_images=conv[1:], duration=duration,
                 loop=0, optimize=True, disposal=2)


NF = 24
save_gif(f"{OUT}/header.gif", [header_frame(i, NF) for i in range(NF)], 90)
save_gif(f"{OUT}/equipment.gif", [panel_frame(i) for i in range(40)], 130)
NF2 = 48
save_gif(f"{OUT}/footer.gif", [footer_frame(i, NF2) for i in range(NF2)], 90)


for n in ("header.gif", "equipment.gif", "footer.gif"):
    print(n, os.path.getsize(f"{OUT}/{n}") // 1024, "KB")
