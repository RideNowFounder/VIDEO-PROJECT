"""
Font loader — downloads Noto Sans Devanagari (supports Hindi script) and
provides PIL ImageFont objects at several sizes.
"""

import os
import logging
from typing import Dict

from PIL import ImageFont

logger = logging.getLogger(__name__)

# Google Fonts static CDN for Noto Sans Devanagari (Bold & Regular)
_FONT_URLS = {
    "bold": (
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
        "NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
    ),
    "regular": (
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
        "NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"
    ),
}

_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")


def _download(url: str, dest: str) -> bool:
    """Download *url* to *dest*.  Returns True on success."""
    try:
        import requests  # type: ignore

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            fh.write(resp.content)
        return True
    except Exception as exc:
        logger.warning("Font download failed (%s): %s", url, exc)
        return False


def _ensure_font(variant: str) -> str | None:
    """Return local path to font file, downloading it if needed."""
    dest = os.path.join(_FONT_DIR, f"NotoSansDevanagari-{variant.capitalize()}.ttf")
    if os.path.exists(dest) and os.path.getsize(dest) > 10_000:
        return dest
    os.makedirs(_FONT_DIR, exist_ok=True)
    url = _FONT_URLS[variant]
    logger.info("Downloading font: %s", os.path.basename(dest))
    if _download(url, dest):
        return dest
    # Try alternate mirror
    alt = url.replace(
        "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/",
        "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/",
    )
    if _download(alt, dest):
        return dest
    return None


def load_fonts() -> Dict[str, Dict[str, ImageFont.FreeTypeFont]]:
    """
    Return a nested dict:  fonts[variant][size_name] = ImageFont

    Variants: 'bold', 'regular'
    Size names: 'title', 'subtitle', 'caption', 'small'
    """
    from src.config import (
        FONT_TITLE_SIZE,
        FONT_SUBTITLE_SIZE,
        FONT_CAPTION_SIZE,
        FONT_SMALL_SIZE,
    )

    sizes = {
        "title": FONT_TITLE_SIZE,
        "subtitle": FONT_SUBTITLE_SIZE,
        "caption": FONT_CAPTION_SIZE,
        "small": FONT_SMALL_SIZE,
    }

    fonts: Dict[str, Dict[str, ImageFont.FreeTypeFont]] = {}

    for variant in ("bold", "regular"):
        path = _ensure_font(variant)
        variant_fonts: Dict[str, ImageFont.FreeTypeFont] = {}
        for name, px in sizes.items():
            if path:
                try:
                    variant_fonts[name] = ImageFont.truetype(path, px)
                    continue
                except Exception as exc:
                    logger.warning("Could not load font %s @%d: %s", path, px, exc)
            # Fallback to PIL default (no Devanagari, but won't crash)
            variant_fonts[name] = ImageFont.load_default()
        fonts[variant] = variant_fonts

    logger.info("Fonts loaded (bold=%s, regular=%s)",
                "ok" if fonts["bold"]["title"] else "fallback",
                "ok" if fonts["regular"]["title"] else "fallback")
    return fonts
