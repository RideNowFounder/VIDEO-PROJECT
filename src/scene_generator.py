"""
Scene / Image Generator – produces one image per Shot using DALL-E 3.

When no OpenAI key is present, it writes solid-colour placeholder PNG images
so the rest of the pipeline can be exercised without API credentials.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from src.config import Config, get_config
from src.models import Screenplay, Shot

logger = logging.getLogger(__name__)

# Colour palette for placeholder images (one per scene, cycling)
_PLACEHOLDER_COLOURS = [
    (30, 30, 80),    # deep navy
    (20, 60, 20),    # dark forest green
    (80, 20, 20),    # dark crimson
    (60, 40, 0),     # dark amber
    (10, 50, 70),    # deep teal
    (50, 0, 80),     # deep purple
]


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
            return self._placeholder_generate(shot, scene_number, out_path)

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
    def _placeholder_generate(
        self, shot: Shot, scene_number: int, out_path: Path
    ) -> Path:
        """
        Write a solid-colour PNG with shot info as a placeholder when no
        OpenAI key is available. Requires Pillow.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
        except ImportError:
            # Ultimate fallback: write a 1×1 white PNG header manually
            out_path.write_bytes(_minimal_png())
            logger.warning("Pillow not installed – wrote minimal placeholder PNG.")
            return out_path

        colour = _PLACEHOLDER_COLOURS[(scene_number - 1) % len(_PLACEHOLDER_COLOURS)]
        img = Image.new(
            "RGB",
            (self.cfg.video_width, self.cfg.video_height),
            colour,
        )
        draw = ImageDraw.Draw(img)

        # Try to use a basic font; fall back to default if unavailable
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            small_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28
            )
        except OSError:
            font = ImageFont.load_default()
            small_font = font

        label = f"Shot {shot.shot_number}  [{shot.shot_type.value.upper()}]"
        desc_lines = _wrap_text(shot.description, 80)

        # Draw a semi-transparent overlay bar
        overlay_y = self.cfg.video_height - 200
        draw.rectangle(
            [(0, overlay_y), (self.cfg.video_width, self.cfg.video_height)],
            fill=(0, 0, 0),
        )
        draw.text((50, overlay_y + 10), label, fill=(255, 220, 50), font=font)
        y = overlay_y + 65
        for line in desc_lines[:3]:
            draw.text((50, y), line, fill=(200, 200, 200), font=small_font)
            y += 36

        img.save(str(out_path), "PNG")
        logger.info("Placeholder image saved: %s", out_path)
        return out_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wrap_text(text: str, width: int) -> list[str]:
    import textwrap
    return textwrap.wrap(text, width)


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
