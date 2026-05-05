"""
Character drawing — Ramlal and supporting villagers.

All functions draw onto a PIL ImageDraw and accept a pixel (x, base_y)
anchor plus a *scale* factor (1.0 ≈ 80 px tall).
"""

import math
from typing import Tuple

from PIL import ImageDraw

Color = Tuple[int, ...]

# ── Palette ───────────────────────────────────────────────────────────────────
SKIN        = ( 95,  58,  25)
SKIN_HI     = (140,  90,  45)
TURBAN      = (195,  60,  22)
DHOTI_W     = (235, 228, 210)
DHOTI_OFF   = (215, 195, 155)
SHIRT_TAN   = (125,  90,  45)
KURTA_WHITE = (230, 222, 205)
SAREE_RED   = (185,  40,  30)
SAREE_GOLD  = (200, 160,  40)
HOE_BROWN   = (100,  65,  25)
HOE_GREY    = (130, 125, 120)
BASKET_CLR  = (160, 120,  55)


def _circle(draw, cx, cy, r, fill):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def _line(draw, p1, p2, fill, width=3):
    draw.line([p1, p2], fill=fill, width=width)


# ── Ramlal ────────────────────────────────────────────────────────────────────

def draw_ramlal_standing(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 1.0,
    t: float = 0.0,
) -> None:
    """Ramlal standing upright — used in village / learning scenes."""
    s = scale
    h = int(80 * s)

    # Head
    hr = int(11 * s)
    head_cx = x
    head_cy = base_y - h + hr
    _circle(draw, head_cx, head_cy, hr, SKIN)

    # Turban (arc / D-shape on top)
    tr = int(13 * s)
    draw.arc(
        [head_cx - tr, head_cy - tr, head_cx + tr, head_cy + tr],
        200, 340, fill=TURBAN, width=int(7 * s),
    )
    # Turban knot
    _circle(draw, head_cx + int(tr * 0.7), head_cy - int(tr * 0.3), int(3 * s), TURBAN)

    # Neck
    nw = int(5 * s)
    draw.rectangle(
        [head_cx - nw, head_cy + hr - 2, head_cx + nw, head_cy + hr + int(6 * s)],
        fill=SKIN,
    )

    # Body (kurta)
    body_top = head_cy + hr + int(5 * s)
    body_bot = base_y - int(22 * s)
    bw = int(12 * s)
    draw.rectangle([x - bw, body_top, x + bw, body_bot], fill=SHIRT_TAN)

    # Arms — slight breathing sway
    sway = math.sin(t * 1.8) * int(3 * s)
    arm_top_y = body_top + int(8 * s)
    # Left arm
    _line(
        draw,
        (x - bw, arm_top_y),
        (x - int(22 * s) + int(sway), arm_top_y + int(26 * s)),
        SKIN, max(2, int(5 * s)),
    )
    # Right arm
    _line(
        draw,
        (x + bw, arm_top_y),
        (x + int(22 * s) - int(sway), arm_top_y + int(26 * s)),
        SKIN, max(2, int(5 * s)),
    )

    # Dhoti (lower body flared)
    dhoti_pts = [
        (x - bw,            body_bot),
        (x + bw,            body_bot),
        (x + int(16 * s),   base_y),
        (x - int(16 * s),   base_y),
    ]
    draw.polygon(dhoti_pts, fill=DHOTI_W)

    # Feet
    fw = int(5 * s)
    draw.ellipse([x - int(15 * s) - fw, base_y - fw // 2, x - int(15 * s) + fw, base_y + fw // 2], fill=SKIN)
    draw.ellipse([x + int(15 * s) - fw, base_y - fw // 2, x + int(15 * s) + fw, base_y + fw // 2], fill=SKIN)


def draw_ramlal_working(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 1.0,
    t: float = 0.0,
) -> None:
    """Ramlal bent over, hoeing the field — animated stroke."""
    s = scale
    h = int(80 * s)
    # Stroke phase: 0 = raised, 1 = down
    stroke = (math.sin(t * 2.5) + 1) / 2  # 0..1

    # Torso — leaning forward
    torso_angle = math.radians(50 + stroke * 15)
    torso_len = int(30 * s)
    torso_bot_x = x + int(math.cos(torso_angle) * torso_len)
    torso_bot_y = base_y - int(h * 0.45) + int(math.sin(torso_angle) * torso_len)

    head_cx = x - int(10 * s)
    head_cy = base_y - int(h * 0.78)
    hr = int(10 * s)
    _circle(draw, head_cx, head_cy, hr, SKIN)

    # Turban
    draw.arc(
        [head_cx - int(12 * s), head_cy - int(12 * s),
         head_cx + int(12 * s), head_cy + int(12 * s)],
        190, 360, fill=TURBAN, width=int(6 * s),
    )

    # Torso
    _line(draw, (head_cx, head_cy + hr), (torso_bot_x, torso_bot_y), SHIRT_TAN, max(2, int(10 * s)))

    # Legs
    leg_spread = int(8 * s)
    _line(draw, (torso_bot_x, torso_bot_y),
          (torso_bot_x - leg_spread, base_y), DHOTI_W, max(2, int(8 * s)))
    _line(draw, (torso_bot_x, torso_bot_y),
          (torso_bot_x + leg_spread, base_y), DHOTI_W, max(2, int(8 * s)))

    # Hoe arm position
    hoe_raise = int(40 * s * (1 - stroke * 0.6))
    arm_end_x = head_cx + int(25 * s)
    arm_end_y = head_cy + hr + hoe_raise
    # Arms
    _line(draw, (head_cx, head_cy + hr + int(6 * s)),
          (arm_end_x, arm_end_y), SKIN, max(2, int(5 * s)))
    # Hoe handle
    _line(draw, (arm_end_x, arm_end_y),
          (arm_end_x + int(30 * s), arm_end_y + int(30 * s)),
          HOE_BROWN, max(2, int(4 * s)))
    # Hoe blade
    blade_x = arm_end_x + int(30 * s)
    blade_y = arm_end_y + int(30 * s)
    draw.rectangle(
        [blade_x - int(5 * s), blade_y,
         blade_x + int(12 * s), blade_y + int(6 * s)],
        fill=HOE_GREY,
    )


def draw_ramlal_digging(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 1.0,
    t: float = 0.0,
) -> None:
    """Ramlal kneeling/bent, digging a pond — animated."""
    s = scale
    h = int(80 * s)
    stroke = (math.sin(t * 2.0) + 1) / 2

    head_cx = x - int(8 * s)
    head_cy = base_y - int(h * 0.72)
    hr = int(10 * s)
    _circle(draw, head_cx, head_cy, hr, SKIN)
    draw.arc(
        [head_cx - int(12 * s), head_cy - int(12 * s),
         head_cx + int(12 * s), head_cy + int(12 * s)],
        190, 360, fill=TURBAN, width=int(6 * s),
    )

    torso_top = head_cy + hr
    torso_bot_x = x + int(5 * s)
    torso_bot_y = base_y - int(20 * s)
    _line(draw, (head_cx, torso_top), (torso_bot_x, torso_bot_y), SHIRT_TAN, int(10 * s))

    # Kneeling legs
    _line(draw, (torso_bot_x, torso_bot_y),
          (x - int(10 * s), base_y), DHOTI_W, int(8 * s))
    _line(draw, (torso_bot_x, torso_bot_y),
          (x + int(12 * s), base_y - int(5 * s)), DHOTI_W, int(8 * s))

    # Shovel arm
    dig_depth = int(25 * s * stroke)
    arm_x = head_cx + int(18 * s)
    arm_y = torso_bot_y - int(5 * s)
    _line(draw, (head_cx, torso_top + int(8 * s)),
          (arm_x, arm_y), SKIN, int(5 * s))
    # Shovel
    _line(draw, (arm_x, arm_y),
          (arm_x + int(5 * s), arm_y + int(30 * s) + dig_depth),
          HOE_BROWN, int(4 * s))
    blade_x = arm_x + int(5 * s)
    blade_y = arm_y + int(30 * s) + dig_depth
    draw.ellipse(
        [blade_x - int(6 * s), blade_y, blade_x + int(6 * s), blade_y + int(9 * s)],
        fill=HOE_GREY,
    )


def draw_ramlal_teaching(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 1.0,
    t: float = 0.0,
) -> None:
    """Ramlal gesturing / explaining to villagers."""
    s = scale
    h = int(80 * s)
    gesture = math.sin(t * 1.5) * int(8 * s)

    hr = int(11 * s)
    head_cx = x
    head_cy = base_y - h + hr
    _circle(draw, head_cx, head_cy, hr, SKIN)
    draw.arc(
        [head_cx - int(13 * s), head_cy - int(13 * s),
         head_cx + int(13 * s), head_cy + int(13 * s)],
        200, 340, fill=TURBAN, width=int(7 * s),
    )

    body_top = head_cy + hr + int(5 * s)
    body_bot = base_y - int(22 * s)
    bw = int(12 * s)
    draw.rectangle([x - bw, body_top, x + bw, body_bot], fill=SHIRT_TAN)

    arm_top_y = body_top + int(8 * s)
    # Right arm raised (gesturing)
    _line(draw, (x + bw, arm_top_y),
          (x + int(28 * s), arm_top_y - int(15 * s) + int(gesture)),
          SKIN, max(2, int(5 * s)))
    # Left arm relaxed
    _line(draw, (x - bw, arm_top_y),
          (x - int(22 * s), arm_top_y + int(22 * s)),
          SKIN, max(2, int(5 * s)))

    dhoti_pts = [
        (x - bw, body_bot), (x + bw, body_bot),
        (x + int(16 * s), base_y), (x - int(16 * s), base_y),
    ]
    draw.polygon(dhoti_pts, fill=DHOTI_W)


# ── Generic villager ──────────────────────────────────────────────────────────

def draw_villager(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 0.8,
    t: float = 0.0,
    shirt_color: Color = KURTA_WHITE,
    dhoti_color: Color = DHOTI_OFF,
    has_turban: bool = True,
    turban_color: Color = (120, 80, 30),
) -> None:
    """Generic villager / bystander."""
    s = scale
    h = int(70 * s)

    hr = int(9 * s)
    head_cx = x
    head_cy = base_y - h + hr
    _circle(draw, head_cx, head_cy, hr, SKIN)

    if has_turban:
        tr = int(11 * s)
        draw.arc(
            [head_cx - tr, head_cy - tr, head_cx + tr, head_cy + tr],
            200, 340, fill=turban_color, width=int(6 * s),
        )

    body_top = head_cy + hr + int(4 * s)
    body_bot = base_y - int(18 * s)
    bw = int(10 * s)
    draw.rectangle([x - bw, body_top, x + bw, body_bot], fill=shirt_color)

    sway = math.sin(t * 1.4 + x * 0.05) * int(2 * s)
    arm_y = body_top + int(7 * s)
    _line(draw, (x - bw, arm_y),
          (x - int(18 * s), arm_y + int(22 * s) + int(sway)),
          SKIN, max(2, int(4 * s)))
    _line(draw, (x + bw, arm_y),
          (x + int(18 * s), arm_y + int(22 * s) - int(sway)),
          SKIN, max(2, int(4 * s)))

    dhoti_pts = [
        (x - bw, body_bot), (x + bw, body_bot),
        (x + int(14 * s), base_y), (x - int(14 * s), base_y),
    ]
    draw.polygon(dhoti_pts, fill=dhoti_color)


def draw_villager_worried(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 0.75,
    t: float = 0.0,
) -> None:
    """Villager with both hands on head (worried pose)."""
    s = scale
    h = int(70 * s)

    hr = int(9 * s)
    head_cx = x
    head_cy = base_y - h + hr
    _circle(draw, head_cx, head_cy, hr, SKIN)

    body_top = head_cy + hr + int(4 * s)
    body_bot = base_y - int(18 * s)
    bw = int(10 * s)
    draw.rectangle([x - bw, body_top, x + bw, body_bot], fill=SHIRT_TAN)

    # Both arms raised to head
    _line(draw, (x - bw, body_top + int(6 * s)),
          (head_cx - int(8 * s), head_cy + int(2 * s)),
          SKIN, max(2, int(4 * s)))
    _line(draw, (x + bw, body_top + int(6 * s)),
          (head_cx + int(8 * s), head_cy + int(2 * s)),
          SKIN, max(2, int(4 * s)))

    dhoti_pts = [
        (x - bw, body_bot), (x + bw, body_bot),
        (x + int(14 * s), base_y), (x - int(14 * s), base_y),
    ]
    draw.polygon(dhoti_pts, fill=DHOTI_OFF)


def draw_walking_figure(
    draw: ImageDraw.ImageDraw,
    x: int,
    base_y: int,
    scale: float = 0.6,
    t: float = 0.0,
    direction: int = 1,
) -> None:
    """Small walking silhouette (leaving the village)."""
    s = scale
    h = int(65 * s)
    step = math.sin(t * 4.0) * int(12 * s)

    hr = int(8 * s)
    head_cx = x
    head_cy = base_y - h + hr
    _circle(draw, head_cx, head_cy, hr, (70, 45, 20))

    body_top = head_cy + hr
    body_bot = base_y - int(18 * s)
    _line(draw, (head_cx, body_top), (head_cx, body_bot), (80, 55, 25), int(8 * s))

    # Swinging legs
    _line(draw, (head_cx, body_bot),
          (head_cx + int(step * 0.5), base_y), (80, 55, 25), int(6 * s))
    _line(draw, (head_cx, body_bot),
          (head_cx - int(step * 0.5), base_y), (80, 55, 25), int(6 * s))
    # Arms swing
    _line(draw, (head_cx, body_top + int(6 * s)),
          (head_cx - direction * int(step * 0.4), body_top + int(22 * s)),
          (80, 55, 25), int(4 * s))
    _line(draw, (head_cx, body_top + int(6 * s)),
          (head_cx + direction * int(step * 0.4), body_top + int(22 * s)),
          (80, 55, 25), int(4 * s))
