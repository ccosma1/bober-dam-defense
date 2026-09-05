#!/usr/bin/env python3
"""Paint the Bober Dam Defense mark with PIL primitives.

Composition (top to bottom): crescent moon, wide beaver mound peeking,
giant cream teeth hanging on timber, four staggered capsule logs.
The 32px read is horizontal bars + two cream teeth — not a face, not a V.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

NIGHT = (58, 42, 106)
FUR = (139, 90, 43)
CREAM = (244, 230, 195)
WOOD = (92, 58, 26)
MOON = (245, 196, 0)

WOOD_SHADOW = (62, 36, 14)
WOOD_LIT = (122, 82, 42)
FUR_SHADOW = (96, 58, 26)
INK = (32, 22, 18)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "icons"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def _px(size: int, n: float) -> float:
    return n * size


def _ellipse(draw: ImageDraw.ImageDraw, cx, cy, rx, ry, fill, outline=None, width: int = 1) -> None:
    box = [cx - rx, cy - ry, cx + rx, cy + ry]
    if outline is None:
        draw.ellipse(box, fill=fill)
    else:
        draw.ellipse(box, fill=fill, outline=outline, width=width)


def _capsule(draw: ImageDraw.ImageDraw, x0, y0, x1, y1, fill) -> None:
    rad = max(1, int((y1 - y0) / 2))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=fill)


def _draw_moon(draw: ImageDraw.ImageDraw, size: int) -> None:
    cx, cy = _px(size, 0.15), _px(size, 0.13)
    r = max(3.0, _px(size, 0.085))
    _ellipse(draw, cx, cy, r, r, MOON)
    _ellipse(draw, cx + r * 0.40, cy - r * 0.10, r * 0.84, r * 0.84, NIGHT)


def _draw_log(draw: ImageDraw.ImageDraw, size: int, x0, y0, x1, y1) -> None:
    h = y1 - y0
    _capsule(draw, x0, y0, x1, y1, WOOD)
    hi = max(1.0, h * 0.26)
    _capsule(draw, x0 + h * 0.55, y0, x1 - h * 0.55, y0 + hi, WOOD_LIT)
    if size < 48:
        return
    # Saw-cut discs on both ends — this is timber, not a chocolate bar.
    erx, ery = h * 0.40, h * 0.40
    _ellipse(draw, x0 + h * 0.50, y0 + h * 0.50, erx, ery, WOOD_SHADOW)
    _ellipse(draw, x1 - h * 0.50, y0 + h * 0.50, erx, ery, WOOD_SHADOW)
    if h >= 12:
        ring_w = max(1, int(_px(size, 0.007)))
        _ellipse(draw, x0 + h * 0.50, y0 + h * 0.50, erx * 0.48, ery * 0.48, None, outline=WOOD_LIT, width=ring_w)
        _ellipse(draw, x1 - h * 0.50, y0 + h * 0.50, erx * 0.48, ery * 0.48, None, outline=WOOD_LIT, width=ring_w)
    if h >= 18:
        tick = max(1, int(_px(size, 0.007)))
        for t in (0.32, 0.50, 0.68):
            x = x0 + (x1 - x0) * t
            draw.line([(x, y0 + h * 0.40), (x + h * 0.16, y0 + h * 0.82)], fill=WOOD_SHADOW, width=tick)


def _draw_dam(draw: ImageDraw.ImageDraw, size: int) -> None:
    # Staggered capsules with a pixel-floor gutter so 32px still reads as bars.
    n = 3 if size < 48 else 4
    gutters = (
        (0.06, 0.96),
        (0.00, 0.88),
        (0.10, 1.00),
        (0.02, 0.94),
    )[:n]
    top = _px(size, 0.395)
    bot = _px(size, 1.025)
    gap = max(2.0 if size >= 24 else 1.0, _px(size, 0.018))
    log_h = (bot - top - gap * (n - 1)) / n
    y = top
    for i, (x0n, x1n) in enumerate(gutters):
        _draw_log(draw, size, _px(size, x0n), y, _px(size, x1n), y + log_h)
        y += log_h + gap


def _draw_head(draw: ImageDraw.ImageDraw, size: int) -> None:
    """Wide mound sitting on the dam — not a circle badge, not a rounded square."""
    s = float(size)
    cx = s * 0.54
    base_y = s * 0.42
    rim = max(1, int(s * 0.012))

    # Ear nubs on the crown (short ovals, not side-discs).
    ear_rx, ear_ry = s * 0.055, s * 0.078
    ear_y = s * 0.175
    for side in (-1.0, 1.0):
        ex = cx + side * s * 0.145
        _ellipse(draw, ex, ear_y, ear_rx + rim, ear_ry + rim, WOOD_SHADOW)
        _ellipse(draw, ex, ear_y, ear_rx, ear_ry, FUR)

    # Head = wide dome (ellipse 2:1) + a flat slab down to the log.
    rx, ry = s * 0.23, s * 0.125
    cy = s * 0.275
    _ellipse(draw, cx, cy, rx + rim, ry + rim, WOOD_SHADOW)
    draw.rectangle([cx - rx - rim, cy, cx + rx + rim, base_y + rim], fill=WOOD_SHADOW)
    _ellipse(draw, cx, cy, rx, ry, FUR)
    draw.rectangle([cx - rx, cy, cx + rx, base_y], fill=FUR)

    # Two ink dots parked on the dam line. No sclera, no cartoon glint.
    if size >= 24:
        eye_y = s * 0.30
        er = max(1.4, s * 0.022)
        for side in (-1.0, 1.0):
            _ellipse(draw, cx + side * s * 0.07, eye_y, er, er * 1.15, INK)

    if size >= 48:
        _ellipse(draw, cx, s * 0.355, s * 0.024, s * 0.014, INK)


def _draw_teeth_and_paws(draw: ImageDraw.ImageDraw, size: int) -> None:
    s = float(size)
    cx = s * 0.54

    if size >= 64:
        paw_y = s * 0.425
        paw_rx, paw_ry = s * 0.058, s * 0.030
        for side in (-1.0, 1.0):
            px = cx + side * s * 0.205
            _ellipse(draw, px, paw_y, paw_rx, paw_ry, FUR_SHADOW)
            _ellipse(draw, px, paw_y - s * 0.006, paw_rx * 0.78, paw_ry * 0.60, FUR)

    # Two fat cream posts hanging over the top log. This is the small-size punch.
    tooth_w = max(4.0, s * 0.080)
    tooth_h = max(7.0 if size >= 32 else 5.0, s * 0.175)
    top = s * 0.355
    gap = max(1.0, s * 0.012)
    rad = max(1, int(max(1.0, s * 0.028)))
    for side in (-1.0, 1.0):
        tx = cx + side * (tooth_w * 0.52 + gap)
        x0, y0 = tx - tooth_w / 2, top
        x1, y1 = tx + tooth_w / 2, top + tooth_h
        draw.rounded_rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], radius=rad + 1, fill=WOOD_SHADOW)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=CREAM)


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (*NIGHT, 255))
    draw = ImageDraw.Draw(img)
    _draw_moon(draw, size)
    _draw_head(draw, size)
    _draw_dam(draw, size)
    _draw_teeth_and_paws(draw, size)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    render(512).save(OUT / "icon-512.png")
    render(192).save(OUT / "icon-192.png")
    frames = [render(s) for s in ICO_SIZES]
    frames[0].save(
        OUT / "bober-dam.ico",
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=frames[1:],
    )
    print(f"wrote {OUT / 'icon-512.png'}")
    print(f"wrote {OUT / 'icon-192.png'}")
    print(f"wrote {OUT / 'bober-dam.ico'}")


if __name__ == "__main__":
    main()
