"""
Low-level drawing utilities.

All coordinate helpers work in a W×H = 1280×720 space and accept
proportional (0..1) coordinates where convenient.
"""

import math
from typing import Tuple, List, Optional, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

Color = Tuple[int, ...]   # RGB or RGBA


# ── Gradient helpers ──────────────────────────────────────────────────────────

def gradient_v(
    width: int,
    height: int,
    top: Color,
    bottom: Color,
    mid: Optional[Color] = None,
    mid_pos: float = 0.5,
) -> Image.Image:
    """Vertical gradient (top → bottom), optional mid-stop."""
    t = np.linspace(0.0, 1.0, height)
    top_a = np.array(top[:3], dtype=float)
    bot_a = np.array(bottom[:3], dtype=float)

    if mid is not None:
        mid_a = np.array(mid[:3], dtype=float)
        s = np.where(
            t <= mid_pos,
            t / max(mid_pos, 1e-6),
            (t - mid_pos) / max(1.0 - mid_pos, 1e-6),
        )
        s = np.clip(s, 0.0, 1.0)
        cols = np.where(
            t[:, None] <= mid_pos,
            top_a * (1 - s[:, None]) + mid_a * s[:, None],
            mid_a * (1 - s[:, None]) + bot_a * s[:, None],
        )
    else:
        cols = top_a * (1 - t[:, None]) + bot_a * t[:, None]

    cols = np.clip(cols, 0, 255).astype(np.uint8)
    arr = np.broadcast_to(cols[:, np.newaxis, :], (height, width, 3)).copy()
    return Image.fromarray(arr, "RGB")


def fill_gradient_rect(
    img: Image.Image,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    top: Color,
    bottom: Color,
) -> None:
    """Fill a rectangle in *img* with a vertical gradient (in-place)."""
    h = y1 - y0
    w = x1 - x0
    grad = gradient_v(w, h, top, bottom)
    img.paste(grad, (x0, y0))


# ── Sky / atmosphere ──────────────────────────────────────────────────────────

def draw_sky(
    img: Image.Image,
    top: Color,
    bottom: Color,
    mid: Optional[Color] = None,
    mid_pos: float = 0.5,
) -> None:
    """Paint the full image as a sky gradient (in-place)."""
    W, H = img.size
    sky = gradient_v(W, H, top, bottom, mid, mid_pos)
    img.paste(sky, (0, 0))


def draw_stars(
    img: Image.Image,
    count: int = 120,
    seed: int = 42,
    brightness: float = 1.0,
    y_limit: float = 0.55,
) -> None:
    """Scatter tiny stars in the upper portion of *img*."""
    rng = np.random.default_rng(seed)
    W, H = img.size
    draw = ImageDraw.Draw(img)
    limit_y = int(H * y_limit)
    xs = rng.integers(0, W, size=count)
    ys = rng.integers(0, limit_y, size=count)
    alphas = rng.uniform(0.4, 1.0, size=count)
    for x, y, a in zip(xs, ys, alphas):
        v = int(min(255, 230 * brightness * a))
        r = 1 if a > 0.7 else 0
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, v + 20))


def draw_sun(
    img: Image.Image,
    cx: int,
    cy: int,
    radius: int,
    core_color: Color = (255, 245, 180),
    glow_color: Color = (255, 200, 80),
) -> None:
    """Draw a glowing sun disk."""
    arr = np.array(img).astype(np.float32)
    H, W, _ = arr.shape
    ys, xs = np.ogrid[:H, :W]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).astype(np.float32)

    # Soft outer glow
    glow_r = radius * 3.5
    glow_mask = np.clip(1.0 - dist / glow_r, 0.0, 1.0) ** 2
    gc = np.array(glow_color, dtype=float)
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + glow_mask * gc[c] * 0.6, 0, 255)

    # Core disk
    core_mask = (dist <= radius).astype(np.float32)
    cc = np.array(core_color, dtype=float)
    for c in range(3):
        arr[:, :, c] = np.where(core_mask > 0, cc[c], arr[:, :, c])

    img.paste(Image.fromarray(arr.astype(np.uint8), "RGB"), (0, 0))


def draw_moon(img: Image.Image, cx: int, cy: int, radius: int) -> None:
    draw = ImageDraw.Draw(img)
    r = radius
    # Full circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(240, 235, 210))
    # Crescent mask (offset smaller circle)
    offset = int(r * 0.45)
    draw.ellipse(
        [cx - r + offset, cy - r - offset // 2,
         cx + r + offset, cy + r - offset // 2],
        fill=(20, 20, 55),
    )


# ── Clouds ────────────────────────────────────────────────────────────────────

def draw_cloud(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    w: int,
    h: int,
    color: Color,
) -> None:
    """Puffy cloud from overlapping ellipses."""
    r = h // 2
    # Main body
    draw.ellipse([cx - w // 2, cy - r, cx + w // 2, cy + r], fill=color)
    # Puffs
    puffs = [
        (cx - w // 3, cy - int(r * 0.6), int(r * 0.9)),
        (cx + w // 4, cy - int(r * 0.7), int(r * 0.85)),
        (cx - w // 6, cy - int(r * 1.0), int(r * 0.75)),
        (cx + w // 8, cy - int(r * 0.9), int(r * 0.7)),
    ]
    for px, py, pr in puffs:
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=color)


# ── Terrain ───────────────────────────────────────────────────────────────────

def draw_mountains(
    draw: ImageDraw.ImageDraw,
    W: int,
    H: int,
    peaks: List[Tuple[float, float]],
    horizon_y: float,
    color: Color,
) -> None:
    """
    Draw a mountain range silhouette.
    *peaks* is a list of (x_ratio, y_ratio) for each peak apex.
    *horizon_y* is the y pixel at the base of the mountains.
    """
    pts = [(0, int(horizon_y))]
    for xr, yr in peaks:
        pts.append((int(xr * W), int(yr * H)))
    pts.append((W, int(horizon_y)))
    draw.polygon(pts, fill=color)


def draw_hills(
    draw: ImageDraw.ImageDraw,
    W: int,
    H: int,
    bumps: List[Tuple[float, float, float]],
    ground_y: int,
    color: Color,
) -> None:
    """
    Rounded hills using Bezier-approximated circles.
    *bumps*: list of (cx_ratio, peak_y_ratio, radius_ratio).
    """
    pts: List[Tuple[int, int]] = [(0, ground_y), (W, ground_y)]
    for cx_r, cy_r, rad_r in sorted(bumps, key=lambda b: b[0]):
        cx = int(cx_r * W)
        cy = int(cy_r * H)
        rad = int(rad_r * W)
        # Sample arc from 180° to 0° (top of circle)
        for angle_deg in range(180, -1, -5):
            a = math.radians(angle_deg)
            pts.append((cx + int(rad * math.cos(a)), cy - int(rad * math.sin(a))))
    # Re-sort by x for correct polygon winding
    interior = sorted(pts[2:], key=lambda p: p[0])
    final = [(0, ground_y)] + interior + [(W, ground_y), (W, H), (0, H)]
    draw.polygon(final, fill=color)


def draw_ground_strip(
    img: Image.Image,
    y_top: int,
    y_bot: int,
    top_color: Color,
    bot_color: Color,
) -> None:
    """Gradient ground strip."""
    fill_gradient_rect(img, 0, y_top, img.width, y_bot, top_color, bot_color)


# ── Crop rows ─────────────────────────────────────────────────────────────────

def draw_crop_rows(
    draw: ImageDraw.ImageDraw,
    x0: int,
    x1: int,
    row_y: int,
    row_spacing: int,
    row_count: int,
    plant_color: Color,
    stem_color: Color,
    plant_h: int = 18,
    sway: float = 0.0,
) -> None:
    """
    Draw rows of crop plants with optional sway animation.
    *sway*: float offset in x pixels for top of plant (wind animation).
    """
    col_spacing = 22
    for row in range(row_count):
        y_base = row_y + row * row_spacing
        y_top = y_base - plant_h
        for x in range(x0, x1, col_spacing):
            # Per-plant phase offset so they don't all move together
            phase_x = math.sin(x * 0.07) * sway
            # Stem
            draw.line(
                [(x, y_base), (x + int(phase_x), y_top)],
                fill=stem_color,
                width=2,
            )
            # Plant head (small ellipse)
            r = 5
            hx = x + int(phase_x)
            draw.ellipse([hx - r, y_top - r, hx + r, y_top + r], fill=plant_color)


def draw_cracked_earth(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    seed: int = 7,
) -> None:
    """Draw random cracks on the ground (drought effect)."""
    rng = np.random.default_rng(seed)
    W = x1 - x0
    H = y1 - y0
    num_cracks = 30
    crack_color = (100, 72, 40)
    for _ in range(num_cracks):
        sx = x0 + int(rng.uniform(0.05, 0.95) * W)
        sy = y0 + int(rng.uniform(0.1, 0.9) * H)
        length = int(rng.uniform(20, 70))
        angle = rng.uniform(0, math.pi * 2)
        ex = sx + int(math.cos(angle) * length)
        ey = sy + int(math.sin(angle) * length * 0.4)
        draw.line([(sx, sy), (ex, ey)], fill=crack_color, width=1)
        # Branch
        branch_angle = angle + rng.uniform(0.3, 1.0) * (1 if rng.random() > 0.5 else -1)
        bl = int(length * rng.uniform(0.3, 0.6))
        bx = (sx + ex) // 2 + int(math.cos(branch_angle) * bl)
        by = (sy + ey) // 2 + int(math.sin(branch_angle) * bl * 0.4)
        draw.line(
            [((sx + ex) // 2, (sy + ey) // 2), (bx, by)],
            fill=crack_color,
            width=1,
        )


# ── Trees ─────────────────────────────────────────────────────────────────────

def draw_tree(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    h: int,
    foliage_color: Color,
    trunk_color: Color,
) -> None:
    tw = max(4, h // 9)
    th = h // 3
    # Trunk
    draw.rectangle([x - tw, base_y - th, x + tw, base_y], fill=trunk_color)
    # Foliage: stacked triangles
    fw = h // 2
    tiers = [
        (base_y - th,          fw,      int(h * 0.55)),
        (base_y - int(th * 1.6), int(fw * 0.8), int(h * 0.72)),
        (base_y - int(th * 2.1), int(fw * 0.55), int(h * 0.92)),
    ]
    for by_, fw_, ty_ in tiers:
        pts = [(x, ty_), (x - fw_, by_), (x + fw_, by_)]
        draw.polygon(pts, fill=foliage_color)


def draw_palm_tree(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    h: int,
    color: Color,
) -> None:
    """Simple stylised palm tree."""
    tw = max(3, h // 12)
    # Trunk (slight curve to the right)
    pts = [
        (x - tw, base_y),
        (x + tw, base_y),
        (x + tw * 2, base_y - h),
        (x,          base_y - h),
    ]
    draw.polygon(pts, fill=(110, 75, 35))
    top_x = x + tw
    top_y = base_y - h
    # Fronds
    fronds = [
        (-60,  -20, 50),
        (-40,  -35, 45),
        (0,   -45, 40),
        (40,  -35, 45),
        (60,  -20, 50),
    ]
    for dx, dy, length in fronds:
        ex = top_x + dx
        ey = top_y + dy
        # Draw frond as thick line + ellipse
        draw.line([(top_x, top_y), (ex, ey)], fill=color, width=3)
        draw.ellipse([ex - 5, ey - 3, ex + 5, ey + 3], fill=color)


# ── Village structures ────────────────────────────────────────────────────────

def draw_hut(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    width: int,
    wall_color: Color,
    roof_color: Color,
    has_smoke: bool = False,
) -> None:
    """Village hut with thatched roof."""
    w = width
    h_wall = int(w * 0.75)
    # Wall
    draw.rectangle([x, base_y - h_wall, x + w, base_y], fill=wall_color)
    # Roof (triangle)
    overhang = w // 6
    roof_pts = [
        (x - overhang,     base_y - h_wall),
        (x + w + overhang, base_y - h_wall),
        (x + w // 2,       base_y - h_wall - int(w * 0.55)),
    ]
    draw.polygon(roof_pts, fill=roof_color)
    # Door
    dw = w // 5
    dh = int(h_wall * 0.55)
    dx = x + (w - dw) // 2
    draw.rectangle([dx, base_y - dh, dx + dw, base_y], fill=(70, 45, 18))
    # Window
    ww = dw
    draw.rectangle(
        [x + w // 5, base_y - h_wall + 8, x + w // 5 + ww, base_y - h_wall + 8 + ww],
        fill=(120, 160, 200),
        outline=(90, 60, 20),
    )
    # Smoke wisps
    if has_smoke:
        sx = x + w // 2
        sy = base_y - h_wall - int(w * 0.55)
        for i in range(3):
            draw.arc(
                [sx + i * 3 - 6, sy - 20 - i * 12, sx + i * 3 + 6, sy - i * 12],
                0, 180,
                fill=(190, 180, 165),
                width=1,
            )


# ── Overlay / letterbox ───────────────────────────────────────────────────────

def draw_letterbox(img: Image.Image, bar_h: int, color: Color = (0, 0, 0)) -> None:
    """Paint top and bottom letterbox bars."""
    draw = ImageDraw.Draw(img)
    W, H = img.size
    draw.rectangle([0, 0, W, bar_h], fill=color)
    draw.rectangle([0, H - bar_h, W, H], fill=color)


def draw_vignette(img: Image.Image, strength: float = 0.55) -> None:
    """Darken edges (in-place)."""
    W, H = img.size
    ys, xs = np.ogrid[:H, :W]
    cx, cy = W / 2.0, H / 2.0
    # Elliptical distance normalised to 1
    d = np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2)
    mask = np.clip(d - 0.4, 0.0, 1.0) / 0.6 * strength
    arr = np.array(img).astype(np.float32)
    arr *= (1.0 - mask[:, :, np.newaxis])
    img.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB"), (0, 0))


def draw_subtitle_bar(
    img: Image.Image,
    text: str,
    font,
    bar_bottom_y: int,
    bar_alpha: int = 180,
    text_color: Color = (255, 255, 255),
    padding: int = 14,
) -> None:
    """Draw a semi-transparent subtitle bar with text."""
    if not text:
        return
    W = img.width

    # Measure text bounds
    dummy = ImageDraw.Draw(img)
    try:
        bb = dummy.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
    except AttributeError:
        tw, th = len(text) * 14, 30

    bar_h = th + padding * 2
    bar_y0 = bar_bottom_y - bar_h

    # Semi-transparent overlay
    overlay = Image.new("RGBA", (W, bar_h), (0, 0, 0, bar_alpha))
    base = img.convert("RGBA")
    base.paste(overlay, (0, bar_y0), overlay)
    img.paste(base.convert("RGB"), (0, 0))

    # Centred text
    tx = (W - tw) // 2
    ty = bar_y0 + padding
    draw = ImageDraw.Draw(img)
    # Drop shadow
    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0))
    draw.text((tx, ty), text, font=font, fill=text_color)


def fade_alpha(img: Image.Image, alpha: float) -> Image.Image:
    """Blend *img* toward black by *alpha* (0=black, 1=original)."""
    if alpha >= 1.0:
        return img
    arr = (np.array(img).astype(np.float32) * max(0.0, alpha)).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


# ── Particles ─────────────────────────────────────────────────────────────────

def draw_dust_particles(
    draw: ImageDraw.ImageDraw,
    W: int,
    H: int,
    t: float,
    seed: int = 0,
    count: int = 40,
    color: Color = (200, 175, 130),
) -> None:
    """Animated floating dust motes (drought scene)."""
    rng = np.random.default_rng(seed)
    xs0 = rng.uniform(0, W, size=count)
    ys0 = rng.uniform(H * 0.4, H * 0.9, size=count)
    speeds = rng.uniform(10, 40, size=count)
    phases = rng.uniform(0, math.pi * 2, size=count)
    for i in range(count):
        x = (xs0[i] + speeds[i] * t) % W
        y = ys0[i] + math.sin(phases[i] + t * 1.2) * 6
        r = int(rng.uniform(1, 3))
        a = int(rng.uniform(80, 160))
        c = tuple(max(0, min(255, v - 30 + rng.integers(-10, 10))) for v in color[:3])
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)


def draw_golden_particles(
    draw: ImageDraw.ImageDraw,
    W: int,
    H: int,
    t: float,
    seed: int = 5,
    count: int = 55,
) -> None:
    """Floating golden motes for harvest scene."""
    rng = np.random.default_rng(seed)
    xs0 = rng.uniform(0, W, size=count)
    ys0 = rng.uniform(H * 0.2, H * 0.85, size=count)
    speeds_x = rng.uniform(-15, 15, size=count)
    speeds_y = rng.uniform(-25, -10, size=count)
    phases = rng.uniform(0, math.pi * 2, size=count)
    for i in range(count):
        x = (xs0[i] + speeds_x[i] * t) % W
        y = ys0[i] + speeds_y[i] * t + math.sin(phases[i] + t) * 4
        y = y % H
        r = int(rng.uniform(1, 4))
        v = int(rng.uniform(180, 255))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(v, int(v * 0.85), 30))
