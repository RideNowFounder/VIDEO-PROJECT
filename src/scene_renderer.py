"""
Scene renderers — one function per scene.

Each renderer takes (t, fonts) and returns a 1280×720 PIL Image.
The letterbox bars and subtitle are baked in here.
"""

import math
from typing import Dict, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from src.config import (
    VIDEO_WIDTH as W,
    VIDEO_HEIGHT as H,
    LETTERBOX_BAR, FRAME_Y0, FRAME_Y1, C,
    FONT_TITLE_SIZE, FONT_SUBTITLE_SIZE,
)
from src.draw_utils import (
    draw_sky, draw_stars, draw_sun, draw_moon,
    draw_cloud, draw_mountains, draw_hills,
    draw_ground_strip, draw_crop_rows, draw_cracked_earth,
    draw_tree, draw_palm_tree, draw_hut,
    draw_letterbox, draw_vignette,
    draw_subtitle_bar, fade_alpha,
    draw_dust_particles, draw_golden_particles,
    gradient_v, fill_gradient_rect,
)
from src.characters import (
    draw_ramlal_standing, draw_ramlal_working,
    draw_ramlal_digging, draw_ramlal_teaching,
    draw_villager, draw_villager_worried,
    draw_walking_figure,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _base() -> Image.Image:
    return Image.new("RGB", (W, H), (0, 0, 0))


def _lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def _ease(t):
    """Smooth-step easing."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _fade_in(img, t, duration=1.0):
    return fade_alpha(img, _ease(t / duration))


def _fade_out(img, t, total, duration=1.0):
    elapsed_from_end = total - t
    return fade_alpha(img, _ease(elapsed_from_end / duration))


def _apply_fades(img, t, total, fade_dur=0.8):
    img = _fade_in(img, t, fade_dur)
    img = _fade_out(img, t, total, fade_dur)
    return img


def _subtitle(img, scene, fonts):
    """Draw Hindi subtitle at the bottom of the active frame area."""
    text = scene.get("subtitle_hindi", "")
    if not text:
        return
    font = fonts["bold"]["caption"]
    draw_subtitle_bar(
        img, text, font,
        bar_bottom_y=H - LETTERBOX_BAR - 8,
        text_color=(255, 235, 180),
    )


def _draw_shared_village_bg(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    sky_top, sky_bottom, sky_mid=None, mid_pos=0.5,
    t=0.0,
    sun_x_ratio=0.72, sun_y_ratio=0.28, sun_radius=38, has_sun=True,
    has_moon=False,
    cloud_alpha=1.0,
):
    """Shared village background: sky, sun/moon, mountains, hills, village."""
    draw_sky(img, sky_top, sky_bottom, sky_mid, mid_pos)

    if has_moon:
        draw_moon(img, int(W * 0.75), int(H * 0.22), 28)

    if has_sun:
        sun_x = int(W * sun_x_ratio)
        sun_y = int(H * sun_y_ratio)
        draw_sun(img, sun_x, sun_y, sun_radius, C["sun_core"], C["sun_glow"])

    # Clouds (moving)
    if cloud_alpha > 0:
        cloud_configs = [
            (0.15, 0.012, 0.31, int(H * 0.15), 130, 42),
            (0.55, 0.008, 0.31, int(H * 0.09), 100, 32),
            (0.80, 0.006, 0.00, int(H * 0.18),  80, 26),
        ]
        ci = int(cloud_alpha * 210)
        for idx, (base_x, speed, offset, cloud_y, cw, ch) in enumerate(cloud_configs):
            cx = int((base_x + speed * t + idx * offset) % 1.0 * W)
            draw_cloud(draw, cx, cloud_y, cw, ch, (ci, ci, ci + 10))

    # Far mountains
    draw_mountains(draw, W, H,
        [(0.05, 0.42), (0.18, 0.33), (0.33, 0.41), (0.48, 0.30),
         (0.62, 0.38), (0.78, 0.27), (0.90, 0.35), (1.00, 0.43)],
        horizon_y=H * 0.52, color=C["mountain_far"])

    # Mid mountains
    draw_mountains(draw, W, H,
        [(0.0, 0.50), (0.12, 0.44), (0.28, 0.52), (0.45, 0.40),
         (0.60, 0.50), (0.75, 0.43), (0.88, 0.51), (1.0, 0.49)],
        horizon_y=H * 0.56, color=C["mountain_mid"])

    # Green hills
    ground_y = int(H * 0.60)
    draw_hills(draw, W, H,
        [(0.15, 0.57, 0.20), (0.45, 0.54, 0.18), (0.75, 0.58, 0.22)],
        ground_y=ground_y, color=C["hill_dark"])

    # Ground
    draw_ground_strip(img, ground_y, H, C["ground_green"], C["ground_lush"])


# ── Scene 1 — Title Card ──────────────────────────────────────────────────────

def scene_title(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    # Night sky → fade to deep blue
    frac = min(t / total, 1.0)
    sky_top    = tuple(int(_lerp(C["night_top"][i],    C["dawn_top"][i],    frac)) for i in range(3))
    sky_bottom = tuple(int(_lerp(C["night_bottom"][i], C["dawn_bottom"][i], frac)) for i in range(3))
    draw_sky(img, sky_top, sky_bottom)
    draw_stars(img, count=160, brightness=1.0 - frac * 0.7, y_limit=0.6)

    # Moon fading out
    moon_alpha = max(0, 1.0 - frac * 2.0)
    if moon_alpha > 0:
        moon_arr = np.array(img)
        moon_img = img.copy()
        draw_moon(moon_img, int(W * 0.82), int(H * 0.22), 28)
        moon_arr2 = np.array(moon_img).astype(np.float32)
        blended = moon_arr.astype(float) * (1 - moon_alpha) + moon_arr2 * moon_alpha
        img.paste(Image.fromarray(blended.astype(np.uint8), "RGB"), (0, 0))
        draw = ImageDraw.Draw(img)

    # Title text
    title_font = fonts["bold"]["title"]
    subtitle_font = fonts["regular"]["caption"]
    tagline_font = fonts["regular"]["small"]

    title_text  = "रामलाल की कहानी"
    sub_text    = "The Story of Ramlal"
    tagline     = "मेहनत · ईमानदारी · हिम्मत"

    draw_dummy = ImageDraw.Draw(img)
    def text_w(txt, fnt):
        try:
            bb = draw_dummy.textbbox((0, 0), txt, font=fnt)
            return bb[2] - bb[0]
        except Exception:
            return len(txt) * 14

    cy = int(H * 0.38)

    # Glow behind title
    glow_w = text_w(title_text, title_font) + 60
    glow_h = FONT_TITLE_SIZE + 30
    for radius in (30, 20, 10):
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        alpha = max(0, int(60 * (1 - radius / 30.0)))
        gd.rectangle(
            [W // 2 - glow_w // 2 - radius, cy - glow_h // 2 - radius,
             W // 2 + glow_w // 2 + radius, cy + glow_h // 2 + radius],
            fill=(200, 150, 30, alpha),
        )
        img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(img)

    # Title
    tx = (W - text_w(title_text, title_font)) // 2
    draw.text((tx + 3, cy - FONT_TITLE_SIZE // 2 + 3), title_text, font=title_font, fill=(80, 50, 10))
    draw.text((tx, cy - FONT_TITLE_SIZE // 2), title_text, font=title_font, fill=C["gold_light"])

    # Decorative line
    line_y = cy + FONT_TITLE_SIZE // 2 + 10
    lw = text_w(title_text, title_font) // 2 + 20
    draw.line([(W // 2 - lw, line_y), (W // 2 + lw, line_y)], fill=C["gold"], width=2)

    # Subtitle English
    sub_y = line_y + 18
    stx = (W - text_w(sub_text, subtitle_font)) // 2
    draw.text((stx, sub_y), sub_text, font=subtitle_font, fill=(200, 190, 160))

    # Tagline
    tag_y = sub_y + FONT_SUBTITLE_SIZE + 10
    ttx = (W - text_w(tagline, tagline_font)) // 2
    draw.text((ttx, tag_y), tagline, font=tagline_font, fill=C["gold"])

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.6)
    img = _apply_fades(img, t, total, fade_dur=1.0)
    return img


# ── Scene 2 — Village Introduction ───────────────────────────────────────────

def scene_village_intro(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    sun_rise = min(t / (total * 0.6), 1.0)
    sun_y_r = _lerp(0.72, 0.28, _ease(sun_rise))

    _draw_shared_village_bg(
        img, draw,
        sky_top=C["dawn_top"], sky_bottom=C["dawn_bottom"], sky_mid=C["dawn_mid"],
        mid_pos=0.45, t=t,
        sun_x_ratio=0.72, sun_y_ratio=sun_y_r,
        sun_radius=38,
    )

    # Village huts
    hut_y = int(H * 0.72)
    for hx, hw, wc, rc, smoke in [
        (int(W * 0.08), 70, C["hut_wall"],  C["hut_roof"],  True),
        (int(W * 0.22), 85, C["hut_wall2"], C["hut_roof"],  False),
        (int(W * 0.38), 60, C["hut_wall"],  C["hut_shadow"], True),
        (int(W * 0.68), 80, C["hut_wall2"], C["hut_roof"],  False),
        (int(W * 0.83), 65, C["hut_wall"],  C["hut_roof"],  True),
    ]:
        draw_hut(draw, hx, hut_y, hw, wc, rc, smoke)

    # Trees
    for tx_, ty_, th_, tc_ in [
        (int(W * 0.54), int(H * 0.68), 55, C["tree_dark"]),
        (int(W * 0.58), int(H * 0.70), 45, C["tree_mid"]),
        (int(W * 0.94), int(H * 0.69), 60, C["tree_dark"]),
        (int(W * 0.03), int(H * 0.68), 50, C["tree_mid"]),
    ]:
        draw_tree(draw, tx_, ty_, th_, tc_, C["tree_trunk"])

    # Path
    path_pts = [
        (int(W * 0.42), H), (int(W * 0.58), H),
        (int(W * 0.55), int(H * 0.72)), (int(W * 0.45), int(H * 0.72)),
    ]
    draw.polygon(path_pts, fill=C["path"])

    # Ramlal walking toward fields (near centre, small scale — distant)
    ramlal_x = int(W * 0.50 - t * 8)
    draw_walking_figure(draw, ramlal_x, int(H * 0.72), scale=0.7, t=t, direction=1)

    # A few birds (v-shapes)
    for i, (bx_r, by_r) in enumerate([(0.30, 0.22), (0.35, 0.19), (0.26, 0.24)]):
        bx = int((bx_r + t * 0.012 * (i + 1)) % 1.0 * W)
        by = int(by_r * H)
        span = 10
        draw.arc([bx - span, by - 4, bx, by + 4], 200, 340, fill=(40, 35, 30), width=1)
        draw.arc([bx, by - 4, bx + span, by + 4], 200, 340, fill=(40, 35, 30), width=1)

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.5)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 3 — Ramlal Working ──────────────────────────────────────────────────

def scene_ramlal_working(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    draw_sky(img, C["morning_top"], C["morning_bottom"])
    draw_sun(img, int(W * 0.80), int(H * 0.20), 36, C["sun_core"], C["sun_glow"])

    # Clouds
    for cx_r, cy_r, cw, ch in [(0.10, 0.12, 110, 36), (0.55, 0.08, 90, 28), (0.80, 0.16, 75, 24)]:
        cx_ = int((cx_r + 0.009 * t) % 1.0 * W)
        draw_cloud(draw, cx_, int(cy_r * H), cw, ch, (240, 240, 248))

    # Mountains
    draw_mountains(draw, W, H,
        [(0.05, 0.40), (0.20, 0.31), (0.40, 0.38), (0.60, 0.28),
         (0.80, 0.36), (1.0, 0.42)],
        horizon_y=H * 0.50, color=C["mountain_far"])

    # Ground / field
    ground_y = int(H * 0.58)
    draw_ground_strip(img, ground_y, H, C["ground_green"], C["ground_lush"])

    # Crop rows (full green field — healthy)
    sway = math.sin(t * 1.2) * 3.5
    draw_crop_rows(draw, 30, W - 30, int(H * 0.62), 24, 4,
                   C["crop_green"], (50, 130, 30), plant_h=22, sway=sway)

    # Border trees
    for tx_, ty_, th_ in [(45, int(H * 0.68), 65), (W - 45, int(H * 0.68), 55)]:
        draw_tree(draw, tx_, ty_, th_, C["tree_dark"], C["tree_trunk"])

    # Ramlal working (large, centre)
    draw_ramlal_working(draw, int(W * 0.50), int(H * 0.74), scale=1.3, t=t)

    # Small well in background
    well_x = int(W * 0.78)
    well_y = int(H * 0.65)
    draw.rectangle([well_x - 14, well_y - 8, well_x + 14, well_y], fill=(120, 90, 50))
    draw.arc([well_x - 14, well_y - 16, well_x + 14, well_y - 2],
             0, 180, fill=(100, 75, 40), width=4)

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.45)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 4 — The Drought ─────────────────────────────────────────────────────

def scene_drought(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    draw_sky(img, C["harsh_top"], C["harsh_bottom"])

    # Harsh bleached sun (hot)
    draw_sun(img, int(W * 0.65), int(H * 0.18), 44, (255, 252, 220), (255, 235, 130))

    # Dry mountains
    draw_mountains(draw, W, H,
        [(0.0, 0.48), (0.22, 0.38), (0.45, 0.45), (0.68, 0.36), (0.90, 0.44), (1.0, 0.50)],
        horizon_y=H * 0.54, color=(130, 115, 85))

    # Dry ground
    ground_y = int(H * 0.56)
    draw_ground_strip(img, ground_y, H, C["ground_dry"], C["ground_cracked"])
    draw_cracked_earth(draw, 0, ground_y, W, H, seed=12)

    # Dead / withered crops
    draw_crop_rows(draw, 30, W - 30, int(H * 0.60), 24, 4,
                   C["crop_dead"], (110, 85, 40), plant_h=14, sway=0.0)

    # Dust particles
    draw_dust_particles(draw, W, H, t, seed=3, count=50)

    # Worried farmers
    for i, (fx, fs, tc_) in enumerate([
        (int(W * 0.20), 0.9, (180, 140, 60)),
        (int(W * 0.38), 0.85, (160, 110, 45)),
        (int(W * 0.70), 0.88, (130, 90, 35)),
    ]):
        draw_villager_worried(draw, fx, int(H * 0.74), scale=fs, t=t + i)

    # One farmer walking away (giving up)
    leave_x = int(W * 0.88 + t * 12)
    if leave_x < W + 30:
        draw_walking_figure(draw, leave_x, int(H * 0.73), scale=0.65, t=t, direction=1)

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.55)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 5 — Ramlal Determined ───────────────────────────────────────────────

def scene_ramlal_determined(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    # Slightly warmer tones — resolve / turning point
    draw_sky(img, (90, 105, 155), (230, 190, 110))
    draw_sun(img, int(W * 0.60), int(H * 0.25), 32, C["sun_core"], C["sun_glow"])

    draw_mountains(draw, W, H,
        [(0.0, 0.46), (0.25, 0.36), (0.55, 0.43), (0.80, 0.34), (1.0, 0.48)],
        horizon_y=H * 0.52, color=C["mountain_far"])

    ground_y = int(H * 0.56)
    draw_ground_strip(img, ground_y, H, C["ground_dry"], C["ground_cracked"])
    draw_cracked_earth(draw, 0, ground_y, W, H, seed=7)

    # Ramlal standing tall — close-up (larger scale)
    draw_ramlal_standing(draw, int(W * 0.50), int(H * 0.80), scale=1.6, t=t)

    # Subtle determined text overlay
    dtext = "हार नहीं!"
    dfont = fonts["bold"]["subtitle"]
    try:
        bb = ImageDraw.Draw(img).textbbox((0, 0), dtext, font=dfont)
        dtw = bb[2] - bb[0]
    except Exception:
        dtw = len(dtext) * 20
    dtx = (W - dtw) // 2
    dty = int(H * 0.30)
    # Glow
    ImageDraw.Draw(img).text((dtx + 2, dty + 2), dtext, font=dfont, fill=(40, 20, 0))
    ImageDraw.Draw(img).text((dtx, dty), dtext, font=dfont, fill=C["gold_light"])

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.5)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 6 — New Techniques ──────────────────────────────────────────────────

def scene_new_techniques(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    draw_sky(img, (75, 125, 200), (230, 210, 140))
    draw_sun(img, int(W * 0.78), int(H * 0.22), 34, C["sun_core"], C["sun_glow"])

    draw_mountains(draw, W, H,
        [(0.0, 0.48), (0.20, 0.38), (0.48, 0.46), (0.72, 0.36), (1.0, 0.50)],
        horizon_y=H * 0.52, color=C["mountain_far"])

    ground_y = int(H * 0.58)
    draw_ground_strip(img, ground_y, H, C["ground_dry"], C["ground_cracked"])

    # Small ponds being dug (progress over time)
    pond_progress = min(t / (total * 0.7), 1.0)
    pond_w = int(80 * pond_progress)
    pond_h = int(30 * pond_progress)
    for i, (px_r, py_r) in enumerate([(0.32, 0.68), (0.55, 0.72), (0.68, 0.66)]):
        px = int(px_r * W) - pond_w // 2
        py = int(py_r * H) - pond_h // 2
        if pond_w > 4:
            draw.ellipse([px, py, px + pond_w, py + pond_h], fill=C["water"])
            # Water shimmer (only draw if the arc bounding box has positive height)
            shimmer_x = px + int(pond_w * 0.3)
            shimmer_x2 = shimmer_x + int(pond_w * 0.3)
            if shimmer_x2 > shimmer_x + 2 and (py + pond_h - 4) > (py + 4):
                draw.arc([shimmer_x, py + 4, shimmer_x2, py + pond_h - 4],
                         190, 350, fill=C["water_shimmer"], width=2)

    # Some drought-resistant crops (shorter, sturdier)
    if pond_progress > 0.3:
        prog2 = (pond_progress - 0.3) / 0.7
        sway = math.sin(t * 1.3) * 2
        draw_crop_rows(draw, int(W * 0.65), W - 30, int(H * 0.62), 22, 3,
                       C["crop_green"], (55, 125, 28), plant_h=int(16 * prog2 + 4), sway=sway)

    # Ramlal digging
    draw_ramlal_digging(draw, int(W * 0.40), int(H * 0.76), scale=1.2, t=t)

    # Two observers watching from side
    draw_villager(draw, int(W * 0.75), int(H * 0.74), scale=0.82, t=t,
                  shirt_color=(200, 195, 175), turban_color=(100, 70, 30))
    draw_villager(draw, int(W * 0.82), int(H * 0.74), scale=0.78, t=t + 1,
                  shirt_color=(180, 165, 140), has_turban=False)

    # Progress label
    if pond_progress > 0.5:
        plabel = "छोटे-छोटे गड्ढे"
        pf = fonts["regular"]["small"]
        try:
            bb = ImageDraw.Draw(img).textbbox((0, 0), plabel, font=pf)
            pw = bb[2] - bb[0]
        except Exception:
            pw = len(plabel) * 10
        ImageDraw.Draw(img).text(
            (int(W * 0.36) - pw // 2, int(H * 0.78)),
            plabel, font=pf, fill=(255, 235, 160),
        )

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.45)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 7 — Green Contrast ──────────────────────────────────────────────────

def scene_green_contrast(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    # Sky: left harsh (drought side), right morning (Ramlal side)
    # Blend via a split sky
    draw_sky(img, C["morning_top"], C["morning_bottom"])

    # Divide line
    split_x = int(W * 0.50)

    # --- Left (dry side) ---
    dry_img = _base()
    dry_draw = ImageDraw.Draw(dry_img)
    draw_sky(dry_img, C["harsh_top"], C["harsh_bottom"])
    draw_ground_strip(dry_img, int(H * 0.58), H, C["ground_dry"], C["ground_cracked"])
    draw_cracked_earth(dry_draw, 0, int(H * 0.58), split_x, H, seed=9)
    draw_crop_rows(dry_draw, 30, split_x - 20, int(H * 0.62), 24, 3,
                   C["crop_dead"], (110, 85, 35), plant_h=10, sway=0.0)
    # Worried farmer left side
    draw_villager_worried(dry_draw, int(W * 0.25), int(H * 0.74), scale=0.9, t=t)

    # --- Right (Ramlal's side) ---
    green_img = _base()
    green_draw = ImageDraw.Draw(green_img)
    draw_sky(green_img, C["morning_top"], C["morning_bottom"])
    draw_ground_strip(green_img, int(H * 0.58), H, C["ground_green"], C["ground_lush"])
    sway = math.sin(t * 1.2) * 3.5
    draw_crop_rows(green_draw, split_x + 20, W - 30, int(H * 0.60), 22, 4,
                   C["crop_green"], (50, 130, 30), plant_h=22, sway=sway)
    for tx_, ty_, th_ in [(int(W * 0.60), int(H * 0.68), 55),
                          (int(W * 0.90), int(H * 0.67), 50)]:
        draw_tree(green_draw, tx_, ty_, th_, C["tree_dark"], C["tree_trunk"])
    draw_ramlal_standing(green_draw, int(W * 0.74), int(H * 0.74), scale=1.0, t=t)
    # Small ponds glinting
    for px, py in [(int(W * 0.65), int(H * 0.70)), (int(W * 0.80), int(H * 0.68))]:
        green_draw.ellipse([px - 20, py - 8, px + 20, py + 8], fill=C["water"])

    # Composite: left dry, right green
    img.paste(dry_img.crop((0, 0, split_x, H)), (0, 0))
    img.paste(green_img.crop((split_x, 0, W, H)), (split_x, 0))
    draw = ImageDraw.Draw(img)

    # Dividing line
    draw.line([(split_x, LETTERBOX_BAR), (split_x, H - LETTERBOX_BAR)],
              fill=(40, 30, 10), width=3)

    # Labels
    lf = fonts["regular"]["small"]
    draw.text((int(W * 0.12), int(H * 0.32)), "दूसरों के खेत", font=lf, fill=(200, 185, 140))
    draw.text((int(W * 0.62), int(H * 0.32)), "रामलाल के खेत", font=lf, fill=(180, 255, 160))

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.45)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 8 — Harvest ────────────────────────────────────────────────────────

def scene_harvest(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    draw_sky(img, C["golden_top"], C["golden_bottom"], C["golden_mid"], 0.4)
    draw_sun(img, int(W * 0.75), int(H * 0.28), 42, C["sun_core"], (255, 215, 90))

    draw_mountains(draw, W, H,
        [(0.0, 0.46), (0.18, 0.36), (0.42, 0.44), (0.65, 0.33), (0.88, 0.43), (1.0, 0.48)],
        horizon_y=H * 0.52, color=(90, 70, 45))

    ground_y = int(H * 0.58)
    draw_ground_strip(img, ground_y, H, C["ground_golden"], (140, 115, 45))

    # Golden crops
    sway = math.sin(t * 0.9) * 4
    draw_crop_rows(draw, 30, W - 30, int(H * 0.60), 22, 5,
                   C["crop_golden"], (160, 135, 40), plant_h=24, sway=sway)

    # Golden particles floating
    draw_golden_particles(draw, W, H, t, seed=8, count=65)

    # Ramlal harvesting
    draw_ramlal_working(draw, int(W * 0.45), int(H * 0.76), scale=1.25, t=t)

    # Cart
    cart_x = int(W * 0.68)
    cart_y = int(H * 0.73)
    # Wheels
    for wx in [cart_x - 20, cart_x + 20]:
        draw.ellipse([wx - 12, cart_y - 12, wx + 12, cart_y + 12],
                     outline=(80, 55, 25), width=3, fill=(110, 80, 35))
    # Cart body
    draw.rectangle([cart_x - 36, cart_y - 28, cart_x + 36, cart_y - 2],
                   fill=(130, 95, 40))
    # Load (golden bundle)
    draw.ellipse([cart_x - 28, cart_y - 44, cart_x + 28, cart_y - 20],
                 fill=C["crop_golden"])

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.4)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 9 — Villagers Learning ─────────────────────────────────────────────

def scene_villagers_learning(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    draw_sky(img, C["morning_top"], C["morning_bottom"])
    draw_sun(img, int(W * 0.82), int(H * 0.22), 34, C["sun_core"], C["sun_glow"])

    draw_mountains(draw, W, H,
        [(0.0, 0.46), (0.22, 0.36), (0.50, 0.44), (0.75, 0.34), (1.0, 0.48)],
        horizon_y=H * 0.52, color=C["mountain_far"])

    ground_y = int(H * 0.58)
    draw_ground_strip(img, ground_y, H, C["ground_green"], C["ground_lush"])

    # Green field in background
    sway = math.sin(t * 1.1) * 3
    draw_crop_rows(draw, W // 2, W - 20, int(H * 0.60), 24, 3,
                   C["crop_green"], (55, 130, 30), plant_h=18, sway=sway)

    # Trees framing
    draw_tree(draw, int(W * 0.06), int(H * 0.68), 65, C["tree_dark"], C["tree_trunk"])
    draw_tree(draw, int(W * 0.94), int(H * 0.68), 55, C["tree_mid"], C["tree_trunk"])

    # Ramlal teaching (centre)
    draw_ramlal_teaching(draw, int(W * 0.50), int(H * 0.75), scale=1.2, t=t)

    # Ring of villagers around Ramlal
    villager_configs = [
        (int(W * 0.28), int(H * 0.75), 0.85, (200, 185, 155), True,  (130, 90, 30)),
        (int(W * 0.36), int(H * 0.76), 0.82, (170, 155, 125), False, (100, 70, 25)),
        (int(W * 0.64), int(H * 0.76), 0.85, (195, 180, 150), True,  (110, 75, 28)),
        (int(W * 0.72), int(H * 0.75), 0.80, (175, 165, 135), False, (90,  60, 22)),
        (int(W * 0.20), int(H * 0.76), 0.75, (160, 150, 120), True,  (140, 95, 35)),
        (int(W * 0.80), int(H * 0.75), 0.78, (185, 170, 145), True,  (120, 80, 28)),
    ]
    for vx, vy, vs, sc, ht, tc in villager_configs:
        draw_villager(draw, vx, vy, scale=vs, t=t + vx * 0.002,
                      shirt_color=sc, has_turban=ht, turban_color=tc)

    # Small huts in background
    for hx_, hw_, wc_, rc_ in [
        (int(W * 0.10), 55, C["hut_wall2"], C["hut_roof"]),
        (int(W * 0.85), 60, C["hut_wall"],  C["hut_roof"]),
    ]:
        draw_hut(draw, hx_, int(H * 0.68), hw_, wc_, rc_)

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.45)
    _subtitle(img, scene, fonts)
    img = _apply_fades(img, t, total)
    return img


# ── Scene 10 — Moral ──────────────────────────────────────────────────────────

def scene_moral(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    # Warm sunset
    draw_sky(img, C["golden_top"], C["golden_bottom"], C["golden_mid"], 0.5)
    draw_sun(img, int(W * 0.50), int(H * 0.58), 50, (255, 210, 100), (255, 155, 40))

    draw_mountains(draw, W, H,
        [(0.0, 0.46), (0.15, 0.36), (0.40, 0.44), (0.62, 0.32), (0.85, 0.42), (1.0, 0.48)],
        horizon_y=H * 0.54, color=(75, 55, 35))

    ground_y = int(H * 0.58)
    draw_ground_strip(img, ground_y, H, (90, 60, 30), (60, 40, 20))

    # Silhouettes of village and farmers in sunset
    sil_y = int(H * 0.72)

    # Huts silhouette
    for hx_, hw_ in [(int(W * 0.06), 60), (int(W * 0.18), 75), (int(W * 0.76), 65), (int(W * 0.88), 55)]:
        draw_hut(draw, hx_, sil_y, hw_, (35, 25, 15), (25, 18, 10))

    # Farmers silhouette (community)
    for i, fx in enumerate([int(W * 0.38), int(W * 0.46), int(W * 0.54), int(W * 0.62)]):
        sway = math.sin(t * 1.2 + i * 0.8) * 2
        draw_villager(draw, fx, sil_y, scale=0.85 + i * 0.02, t=t + i,
                      shirt_color=(35, 25, 15), dhoti_color=(45, 35, 20),
                      has_turban=True, turban_color=(30, 20, 10))

    # Trees
    for tx_, ty_, th_ in [(int(W * 0.25), int(H * 0.66), 65), (int(W * 0.75), int(H * 0.66), 60)]:
        draw_tree(draw, tx_, ty_, th_, (25, 18, 10), (20, 14, 8))

    # Moral text (appears in two-part stagger)
    moral1 = "मुश्किल में हार नहीं माननी चाहिए"
    moral2 = "समझदारी और मेहनत से काम लो"

    mf = fonts["bold"]["caption"]
    for line_idx, (line, line_t_start) in enumerate([(moral1, 0.6), (moral2, 2.5)]):
        line_alpha = _ease(min(1.0, (t - line_t_start) / 1.2))
        if line_alpha <= 0:
            continue
        try:
            bb = ImageDraw.Draw(img).textbbox((0, 0), line, font=mf)
            lw = bb[2] - bb[0]
        except Exception:
            lw = len(line) * 18
        lx = (W - lw) // 2
        ly = int(H * 0.35) + line_idx * (FONT_SUBTITLE_SIZE + 10)
        # Shadow
        ImageDraw.Draw(img).text((lx + 2, ly + 2), line, font=mf,
                                  fill=(0, 0, 0))
        # Text
        col = tuple(int(c * line_alpha) for c in C["gold_light"])
        ImageDraw.Draw(img).text((lx, ly), line, font=mf, fill=col)

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.5)
    img = _apply_fades(img, t, total, fade_dur=1.0)
    return img


# ── Scene 11 — End Card ───────────────────────────────────────────────────────

def scene_end_card(t: float, total: float, scene: dict, fonts: dict) -> Image.Image:
    img = _base()
    draw = ImageDraw.Draw(img)

    draw_sky(img, C["night2_top"], C["night2_bottom"])
    draw_stars(img, count=140, brightness=min(t * 0.8, 0.9), y_limit=0.7)

    # "समाप्त" — The End
    end_font = fonts["bold"]["title"]
    end_text = "समाप्त"
    sub_text = "— The End —"

    try:
        bb = ImageDraw.Draw(img).textbbox((0, 0), end_text, font=end_font)
        etw = bb[2] - bb[0]
        bb2 = ImageDraw.Draw(img).textbbox((0, 0), sub_text, font=fonts["regular"]["caption"])
        stw = bb2[2] - bb2[0]
    except Exception:
        etw = len(end_text) * 30
        stw = len(sub_text) * 14

    cy = int(H * 0.42)
    alpha = _ease(min(t / 1.5, 1.0))
    col_main = tuple(int(c * alpha) for c in C["gold_light"])
    col_sub  = tuple(int(c * alpha) for c in (190, 180, 155))

    etx = (W - etw) // 2
    draw.text((etx + 2, cy - FONT_TITLE_SIZE // 2 + 2), end_text,
              font=end_font, fill=(0, 0, 0))
    draw.text((etx, cy - FONT_TITLE_SIZE // 2), end_text,
              font=end_font, fill=col_main)

    stx = (W - stw) // 2
    sty = cy + FONT_TITLE_SIZE // 2 + 12
    draw.text((stx, sty), sub_text,
              font=fonts["regular"]["caption"], fill=col_sub)

    # Decorative line
    line_y = cy + FONT_TITLE_SIZE // 2 + 8
    lw = etw // 2 + 30
    draw.line([(W // 2 - lw, line_y), (W // 2 + lw, line_y)], fill=C["gold"], width=2)

    draw_letterbox(img, LETTERBOX_BAR)
    draw_vignette(img, 0.65)
    img = _apply_fades(img, t, total, fade_dur=1.2)
    return img


# ── Scene dispatcher ──────────────────────────────────────────────────────────

_RENDERERS = {
    "title":              scene_title,
    "village_intro":      scene_village_intro,
    "ramlal_working":     scene_ramlal_working,
    "drought":            scene_drought,
    "ramlal_determined":  scene_ramlal_determined,
    "new_techniques":     scene_new_techniques,
    "green_contrast":     scene_green_contrast,
    "harvest":            scene_harvest,
    "villagers_learning": scene_villagers_learning,
    "moral":              scene_moral,
    "end_card":           scene_end_card,
}


def render_scene(
    scene_id: str,
    t: float,
    total: float,
    scene_data: dict,
    fonts: dict,
) -> np.ndarray:
    """
    Render one frame for *scene_id* at time *t* (0 … total).
    Returns a (H, W, 3) uint8 numpy array for MoviePy.
    """
    renderer = _RENDERERS.get(scene_id)
    if renderer is None:
        img = _base()
    else:
        img = renderer(t, total, scene_data, fonts)
    return np.array(img)
