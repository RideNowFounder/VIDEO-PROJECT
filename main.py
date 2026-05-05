"""
Ramlal Ki Kahani — Cinematic Animated Film
==========================================
A story about perseverance, hard work, and wisdom set in rural India.

Story source: Hindi folktale about farmer Ramlal who overcomes a drought
              through innovation and determination.

Usage:
    pip install -r requirements.txt
    python main.py

Output:
    output/ramlal_ki_kahani.mp4
"""

import os
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=" * 60)
    logger.info("  रामलाल की कहानी  —  Animated Cinematic Film")
    logger.info("=" * 60)

    # Create output & asset directories
    for d in ("output", "assets/fonts", "assets/audio"):
        os.makedirs(d, exist_ok=True)

    # Step 1 — Fonts
    logger.info("[1/4] Loading Devanagari fonts …")
    from src.font_loader import load_fonts
    fonts = load_fonts()
    logger.info("      Fonts ready.")

    # Step 2 — Audio narration
    logger.info("[2/4] Generating Hindi narration audio …")
    from src.audio_generator import generate_all_audio
    audio_map = generate_all_audio()
    logger.info("      Audio segments ready.")

    # Step 3 — Compose & export film
    logger.info("[3/4] Rendering and compositing film …")
    from src.video_composer import compose_film
    out_path = compose_film(fonts, audio_map)

    logger.info("[4/4] Done!")
    logger.info("=" * 60)
    logger.info("  Output → %s", out_path)
    logger.info("=" * 60)


if __name__ == "__main__":
    t0 = time.time()
    main()
    logger.info("Total render time: %.1f s", time.time() - t0)
