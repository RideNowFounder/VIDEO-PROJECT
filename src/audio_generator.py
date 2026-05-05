"""
Hindi narration audio generator — uses gTTS (Google Text-to-Speech).

Falls back to silence clips when the network is unavailable, so the film
still renders without audio rather than crashing.
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "audio")


def _gtts_generate(text: str, dest_path: str) -> bool:
    """Generate Hindi TTS mp3 via gTTS.  Returns True on success."""
    try:
        from gtts import gTTS  # type: ignore
        tts = gTTS(text=text, lang="hi", slow=False)
        tts.save(dest_path)
        logger.info("  Audio: %s", os.path.basename(dest_path))
        return True
    except Exception as exc:
        logger.warning("  gTTS failed for '%s…': %s", text[:40], exc)
        return False


def _silence_mp3(dest_path: str, duration_s: float) -> bool:
    """Write a silent mp3 using moviepy (always available)."""
    try:
        from moviepy.audio.AudioClip import AudioClip  # type: ignore
        import numpy as np

        def make_silent(t):
            return np.zeros((1,)) if np.isscalar(t) else np.zeros((len(t), 1))

        clip = AudioClip(make_silent, duration=max(0.1, duration_s))
        clip.write_audiofile(dest_path, fps=22050, nbytes=2, bitrate="32k",
                             verbose=False, logger=None)
        return True
    except Exception as exc:
        logger.warning("  Silence fallback also failed: %s", exc)
        return False


def generate_all_audio() -> Dict[str, Optional[str]]:
    """
    Generate one mp3 per scene narration.

    Returns a dict mapping scene_id → mp3_path (or None if no narration).
    """
    from src.story import SCENES

    os.makedirs(_AUDIO_DIR, exist_ok=True)
    audio_map: Dict[str, Optional[str]] = {}

    for scene in SCENES:
        sid = scene["id"]
        text = scene.get("narration_hindi", "").strip()

        if not text:
            audio_map[sid] = None
            continue

        dest = os.path.join(_AUDIO_DIR, f"{sid}.mp3")

        # Use cached file if it looks valid
        if os.path.exists(dest) and os.path.getsize(dest) > 500:
            logger.info("  Audio cache hit: %s", sid)
            audio_map[sid] = dest
            continue

        success = _gtts_generate(text, dest)
        if not success:
            # Generate silence so video still plays
            from src.config import SCENE_DURATIONS
            dur = SCENE_DURATIONS.get(sid, 8.0)
            success = _silence_mp3(dest, dur)

        audio_map[sid] = dest if success else None

    return audio_map
