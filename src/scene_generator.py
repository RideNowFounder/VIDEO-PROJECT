"""
Scene / Image Generator – produces one image per Shot using DALL-E 3.

When no OpenAI key is present, it renders original cartoon illustrations with
Pillow so offline output remains usable and non-placeholder.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from src.config import Config, get_config
from src.models import Screenplay, Shot

logger = logging.getLogger(__name__)

class SceneGenerator:
    """Generates one image per shot and saves it to disk."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.cfg = config or get_config()
        self._images_dir = self.cfg.output_dir / "images"

    # ------------------------------------------------------------------
    def generate_all(self, screenplay: Screenplay) -> Screenplay:
        """
        Iterate over every Shot in *screenplay*, generate its image, and set
        ``shot.image_path``.  Returns the updated screenplay.
        """
        total = screenplay.total_shots
        generated = 0
        for scene in screenplay.scenes:
            for shot in scene.shots:
                path = self._generate_shot_image(shot, scene.scene_number)
                shot.image_path = str(path)
                generated += 1
                logger.info(
                    "[%d/%d] Scene %d, Shot %d → %s",
                    generated,
                    total,
                    scene.scene_number,
                    shot.shot_number,
                    path.name,
                )
        return screenplay

    # ------------------------------------------------------------------
    def _generate_shot_image(self, shot: Shot, scene_number: int) -> Path:
        filename = f"scene{scene_number:02d}_shot{shot.shot_number:03d}.png"
        out_path = self._images_dir / filename

        if out_path.exists():
            logger.debug("Image already exists, skipping: %s", out_path)
            return out_path

        if self.cfg.has_openai:
            return self._dalle_generate(shot, out_path)
        else:
            return self._illustrated_generate(shot, scene_number, out_path)

    # ------------------------------------------------------------------
    def _dalle_generate(self, shot: Shot, out_path: Path) -> Path:
        try:
            import openai  # type: ignore
            import requests  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "openai and requests packages are required for image generation."
            ) from exc

        client = openai.OpenAI(api_key=self.cfg.openai_api_key)

        # DALL-E 3 prompt – keep under 4000 chars
        prompt = shot.visual_prompt[:3900]

        logger.debug("DALL-E 3 generating: %s…", prompt[:80])
        response = client.images.generate(
            model=self.cfg.image_model,
            prompt=prompt,
            size=self.cfg.image_size,
            quality=self.cfg.image_quality,
            n=1,
        )

        image_url = response.data[0].url
        img_data = requests.get(image_url, timeout=60).content
        out_path.write_bytes(img_data)
        logger.info("DALL-E image saved: %s", out_path)
        return out_path

    # ------------------------------------------------------------------
    def _illustrated_generate(
        self, shot: Shot, scene_number: int, out_path: Path
    ) -> Path:
        """Render original offline cartoon illustration with simple character art."""
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
        except ImportError:
            out_path.write_bytes(_minimal_png())
            logger.warning("Pillow not installed – wrote minimal fallback PNG.")
            return out_path

        w, h = self.cfg.video_width, self.cfg.video_height
        img = Image.new("RGB", (w, h), (238, 231, 214))
        draw = ImageDraw.Draw(img)

        title_font, caption_font = _load_fonts(52, 38)
        self._draw_scene_background(draw, scene_number, w, h)
        self._draw_scene_action(draw, scene_number, w, h)
        self._draw_caption(draw, shot, scene_number, w, h, title_font, caption_font)

        img.save(str(out_path), "PNG")
        logger.info("Programmatic illustrated image saved: %s", out_path)
        return out_path

    def _draw_scene_background(self, draw, scene_number: int, w: int, h: int) -> None:
        palettes = {
            1: ((235, 232, 250), (208, 225, 255)),
            2: ((245, 240, 219), (255, 232, 199)),
            3: ((221, 238, 232), (245, 214, 230)),
            4: ((211, 228, 255), (196, 208, 245)),
            5: ((246, 231, 213), (252, 211, 174)),
            6: ((220, 248, 244), (180, 229, 255)),
        }
        top, bottom = palettes.get(scene_number, ((235, 235, 235), (210, 210, 210)))
        for y in range(h):
            t = y / max(1, h - 1)
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            draw.line([(0, y), (w, y)], fill=color)
        draw.rectangle([(0, int(h * 0.75)), (w, h)], fill=(194, 157, 118))

    def _draw_scene_action(self, draw, scene_number: int, w: int, h: int) -> None:
        self._draw_table(draw, int(w * 0.12), int(h * 0.58), int(w * 0.86), int(h * 0.74))
        if scene_number == 1:
            self._draw_books(draw, w, h, messy=True)
            self._draw_aman(draw, int(w * 0.52), int(h * 0.65), phone=False)
        elif scene_number == 2:
            self._draw_books(draw, w, h, messy=False)
            self._draw_aman(draw, int(w * 0.52), int(h * 0.65), phone=False, smile=True)
            draw.rectangle([(int(w * 0.36), int(h * 0.45)), (int(w * 0.39), int(h * 0.67))], fill=(140, 110, 90))
        elif scene_number == 3:
            draw.rectangle([(int(w * 0.68), int(h * 0.25)), (int(w * 0.92), int(h * 0.76))], fill=(122, 89, 60))
            draw.rectangle([(int(w * 0.71), int(h * 0.30)), (int(w * 0.89), int(h * 0.73))], fill=(170, 130, 95))
            self._draw_mummy(draw, int(w * 0.45), int(h * 0.69))
        elif scene_number == 4:
            self._draw_books(draw, w, h, messy=False)
            self._draw_aman(draw, int(w * 0.50), int(h * 0.67), phone=True)
            draw.rounded_rectangle([(int(w * 0.64), int(h * 0.53)), (int(w * 0.87), int(h * 0.70))], radius=20, fill=(35, 35, 45))
            draw.text((int(w * 0.67), int(h * 0.58)), "REELS", fill=(255, 255, 255))
        elif scene_number == 5:
            self._draw_aman(draw, int(w * 0.42), int(h * 0.70), phone=True)
            self._draw_clock(draw, int(w * 0.78), int(h * 0.36), int(w * 0.16), "10")
            self._draw_clock(draw, int(w * 0.78), int(h * 0.36), int(w * 0.11), "3")
            draw.text((int(w * 0.66), int(h * 0.55)), "10 AM -> 3 PM", fill=(40, 40, 50))
        else:
            self._draw_aman(draw, int(w * 0.40), int(h * 0.68), phone=False, smile=True)
            self._draw_ravi(draw, int(w * 0.62), int(h * 0.68))
            draw.text((int(w * 0.30), int(h * 0.50)), "Kal Se Pakka!", fill=(35, 60, 90))

    def _draw_caption(self, draw, shot: Shot, scene_number: int, w: int, h: int, title_font, caption_font) -> None:
        overlays = {
            1: "Scene 1: Aman vs Messy Table",
            3: "Mummy Radar Activated",
            5: "Time Skip Combo!",
            6: "Best Friend Roast Finale",
        }
        caption = overlays.get(scene_number, "")
        if caption:
            draw.rounded_rectangle([(int(w * 0.06), int(h * 0.05)), (int(w * 0.94), int(h * 0.12))], radius=22, fill=(0, 0, 0))
            draw.text((int(w * 0.09), int(h * 0.067)), caption, fill=(255, 238, 120), font=caption_font)
        draw.rounded_rectangle([(int(w * 0.05), int(h * 0.84)), (int(w * 0.95), int(h * 0.98))], radius=25, fill=(0, 0, 0))
        draw.text((int(w * 0.08), int(h * 0.865)), "Original programmatic cartoon art", fill=(255, 255, 255), font=caption_font)
        desc = _wrap_text(shot.description, 52)
        y = int(h * 0.90)
        for line in desc[:2]:
            draw.text((int(w * 0.08), y), line, fill=(208, 225, 255), font=title_font)
            y += 42

    def _draw_table(self, draw, x0: int, y0: int, x1: int, y1: int) -> None:
        draw.rectangle([(x0, y0), (x1, y1)], fill=(160, 115, 80))
        draw.rectangle([(x0, y1), (x1, y1 + 25)], fill=(115, 79, 52))

    def _draw_books(self, draw, w: int, h: int, messy: bool) -> None:
        books = [
            (int(w * 0.18), int(h * 0.60), (220, 80, 90)),
            (int(w * 0.29), int(h * 0.62), (85, 140, 220)),
            (int(w * 0.72), int(h * 0.60), (100, 200, 150)),
            (int(w * 0.58), int(h * 0.63), (245, 210, 90)),
        ]
        for idx, (x, y, color) in enumerate(books):
            tilt = 30 if messy and idx % 2 == 0 else 0
            draw.rounded_rectangle([(x, y - 20), (x + 130, y + 15)], radius=6, fill=color)
            if tilt:
                draw.line([(x + 15, y - 18), (x + 120, y + 12)], fill=(50, 50, 50), width=4)

    def _draw_aman(self, draw, cx: int, cy: int, phone: bool, smile: bool = False) -> None:
        self._draw_person_base(draw, cx, cy, shirt=(73, 133, 222), hair_curly=False, smile=smile)
        draw.ellipse([(cx - 32, cy - 102), (cx + 2, cy - 74)], outline=(20, 20, 20), width=3)
        draw.ellipse([(cx + 2, cy - 102), (cx + 36, cy - 74)], outline=(20, 20, 20), width=3)
        draw.line([(cx - 1, cy - 88), (cx + 4, cy - 88)], fill=(20, 20, 20), width=2)
        if phone:
            draw.rounded_rectangle([(cx + 50, cy - 35), (cx + 90, cy + 30)], radius=8, fill=(30, 30, 45))

    def _draw_ravi(self, draw, cx: int, cy: int) -> None:
        self._draw_person_base(draw, cx, cy, shirt=(247, 208, 69), hair_curly=True, smile=True)
        draw.arc([(cx - 45, cy - 130), (cx + 45, cy - 60)], start=160, end=380, fill=(15, 15, 15), width=8)

    def _draw_mummy(self, draw, cx: int, cy: int) -> None:
        self._draw_person_base(draw, cx, cy, shirt=(202, 85, 160), hair_curly=False, smile=True)
        draw.polygon([(cx - 75, cy + 40), (cx + 75, cy + 40), (cx, cy - 40)], fill=(250, 165, 75))
        draw.rounded_rectangle([(cx + 66, cy - 40), (cx + 115, cy - 8)], radius=10, fill=(205, 205, 205))

    def _draw_person_base(self, draw, cx: int, cy: int, shirt: tuple[int, int, int], hair_curly: bool, smile: bool) -> None:
        draw.ellipse([(cx - 34, cy - 128), (cx + 34, cy - 58)], fill=(245, 200, 160), outline=(60, 40, 20))
        hair_color = (30, 30, 30)
        if hair_curly:
            for xo in (-24, -10, 4, 18):
                draw.ellipse([(cx + xo - 14, cy - 138), (cx + xo + 10, cy - 114)], fill=hair_color)
        else:
            draw.pieslice([(cx - 40, cy - 140), (cx + 40, cy - 66)], start=180, end=360, fill=hair_color)
        draw.rounded_rectangle([(cx - 56, cy - 55), (cx + 56, cy + 42)], radius=25, fill=shirt)
        mouth = [(cx - 11, cy - 74), (cx + 11, cy - 74)] if not smile else [(cx - 12, cy - 82), (cx + 12, cy - 74)]
        draw.line(mouth, fill=(40, 20, 20), width=3)

    def _draw_clock(self, draw, cx: int, cy: int, radius: int, hour: str) -> None:
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], fill=(252, 252, 252), outline=(40, 40, 50), width=6)
        draw.text((cx - int(radius * 0.6), cy + int(radius * 1.2)), f"{hour} o'clock", fill=(30, 30, 30))
        draw.line([(cx, cy), (cx, cy - int(radius * 0.55))], fill=(10, 10, 10), width=4)
        draw.line([(cx, cy), (cx + int(radius * 0.45), cy)], fill=(10, 10, 10), width=4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wrap_text(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width)


def _load_fonts(title_size: int, caption_size: int):
    from PIL import ImageFont  # type: ignore

    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    title_font = ImageFont.load_default()
    caption_font = title_font
    for fp in font_candidates:
        try:
            title_font = ImageFont.truetype(fp, title_size)
            caption_font = ImageFont.truetype(fp, caption_size)
            break
        except OSError:
            continue
    return title_font, caption_font


def _minimal_png() -> bytes:
    """Return bytes of a minimal 1×1 white PNG."""
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\xff\xff"
    idat = _chunk(b"IDAT", zlib.compress(raw))
    iend = _chunk(b"IEND", b"")
    return signature + ihdr + idat + iend
