"""
Global configuration — video dimensions, colour palette, scene timings.
"""

# ── Video ─────────────────────────────────────────────────────────────────────
VIDEO_WIDTH: int = 1280
VIDEO_HEIGHT: int = 720
FPS: int = 24

# Cinematic 2.35 : 1 letterbox
_CINEMA_H: int = int(VIDEO_WIDTH / 2.35)           # ≈ 544 px
LETTERBOX_BAR: int = (VIDEO_HEIGHT - _CINEMA_H) // 2  # ≈ 88 px

# Active picture area (y range inside letterbox)
FRAME_Y0: int = LETTERBOX_BAR
FRAME_Y1: int = VIDEO_HEIGHT - LETTERBOX_BAR

# ── Typography ────────────────────────────────────────────────────────────────
FONT_TITLE_SIZE: int = 72
FONT_SUBTITLE_SIZE: int = 36
FONT_CAPTION_SIZE: int = 28
FONT_SMALL_SIZE: int = 22

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    # Sky gradients
    "night_top":        (5,   5,  25),
    "night_bottom":     (20,  20,  60),
    "dawn_top":         (18,  10,  55),
    "dawn_mid":         (175,  55,  20),
    "dawn_bottom":      (255, 135,  45),
    "morning_top":      (55, 120, 210),
    "morning_bottom":   (255, 215, 140),
    "harsh_top":        (205, 185, 120),
    "harsh_bottom":     (255, 245, 195),
    "golden_top":       (215,  75,  15),
    "golden_mid":       (255, 140,  40),
    "golden_bottom":    (255, 200,  95),
    "night2_top":       (8,   8,  30),
    "night2_bottom":    (30,  30,  80),

    # Landscape
    "mountain_far":     (35,  50,  75),
    "mountain_mid":     (50,  70,  95),
    "hill_dark":        (25,  70,  20),
    "hill_light":       (45, 100,  30),
    "ground_green":     (40, 110,  25),
    "ground_lush":      (55, 140,  30),
    "ground_dry":       (155, 115,  50),
    "ground_cracked":   (140, 100,  55),
    "ground_golden":    (180, 145,  50),

    # Crops
    "crop_green":       (75, 155,  35),
    "crop_yellow":      (195, 165,  45),
    "crop_brown":       (135, 105,  35),
    "crop_golden":      (215, 175,  45),
    "crop_dead":        (145, 115,  50),

    # Water
    "water":            (35,  95, 175),
    "water_light":      (75, 145, 215),
    "water_shimmer":    (120, 190, 240),

    # Village
    "hut_wall":         (175, 138,  85),
    "hut_wall2":        (155, 120,  70),
    "hut_roof":         (135,  95,  45),
    "hut_shadow":       ( 95,  65,  25),
    "path":             (190, 160, 105),
    "door":             ( 80,  50,  20),

    # Characters
    "skin":             ( 95,  58,  25),
    "skin_hi":          (140,  90,  45),
    "dhoti_white":      (235, 228, 210),
    "dhoti_off":        (215, 195, 155),
    "turban_red":       (195,  60,  25),
    "turban_orange":    (210,  95,  20),
    "shirt_tan":        (130,  95,  50),

    # Trees
    "tree_trunk":       ( 90,  58,  25),
    "tree_dark":        ( 20,  65,  15),
    "tree_mid":         ( 40,  95,  25),
    "tree_light":       ( 65, 120,  35),

    # UI / overlay
    "black":            (  0,   0,   0),
    "white":            (255, 255, 255),
    "gold":             (220, 168,  55),
    "gold_light":       (255, 218,  95),
    "subtitle_bar":     (  0,   0,   0),   # alpha handled separately
    "stars":            (230, 230, 250),
    "sun_core":         (255, 245, 180),
    "sun_glow":         (255, 200,  80),
    "smoke":            (200, 185, 165),
}

# ── Scene timing (seconds) ────────────────────────────────────────────────────
SCENE_DURATIONS: dict = {
    "title":              6.0,
    "village_intro":     11.0,
    "ramlal_working":     9.0,
    "drought":           11.0,
    "ramlal_determined":  7.0,
    "new_techniques":    11.0,
    "green_contrast":     9.0,
    "harvest":            9.0,
    "villagers_learning": 9.0,
    "moral":             10.0,
    "end_card":           6.0,
}
