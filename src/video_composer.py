"""
Video composer — stitches all scenes into a single cinematic MP4.

Pipeline
--------
1. For each scene, create a MoviePy VideoClip whose make_frame calls the
   corresponding scene renderer.
2. Optionally attach per-scene narration audio (or silence).
3. Concatenate all clips and write the final file.
"""

import os
import logging
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)

_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
_OUT_FILE   = os.path.join(_OUTPUT_DIR, "ramlal_ki_kahani.mp4")


def compose_film(fonts: dict, audio_map: Dict[str, Optional[str]]) -> str:
    """
    Build and export the film.  Returns the output file path.
    """
    from moviepy.editor import VideoClip, AudioFileClip, concatenate_videoclips  # type: ignore

    from src.config import FPS, SCENE_DURATIONS
    from src.story import SCENES
    from src.scene_renderer import render_scene

    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    clips = []

    for scene in SCENES:
        sid      = scene["id"]
        duration = SCENE_DURATIONS.get(sid, 8.0)

        logger.info("  Rendering scene %-22s (%.1f s)", sid, duration)

        # Closure captures current values
        def make_frame(t, _sid=sid, _dur=duration, _scene=scene, _fonts=fonts):
            return render_scene(_sid, t, _dur, _scene, _fonts)

        clip = VideoClip(make_frame, duration=duration).set_fps(FPS)

        # Attach narration audio
        audio_path = audio_map.get(sid)
        if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 500:
            try:
                audio = AudioFileClip(audio_path)
                # Trim or pad to fit scene duration
                if audio.duration > duration:
                    audio = audio.subclip(0, duration)
                clip = clip.set_audio(audio)
            except Exception as exc:
                logger.warning("    Could not attach audio for %s: %s", sid, exc)

        clips.append(clip)

    logger.info("  Concatenating %d scenes …", len(clips))
    final = concatenate_videoclips(clips, method="compose")

    logger.info("  Writing → %s", _OUT_FILE)
    final.write_videofile(
        _OUT_FILE,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="faster",
        ffmpeg_params=["-crf", "20"],
        verbose=False,
        logger=None,
    )

    # Clean up
    for clip in clips:
        try:
            clip.close()
        except Exception:
            pass
    try:
        final.close()
    except Exception:
        pass

    size_mb = os.path.getsize(_OUT_FILE) / 1_048_576 if os.path.exists(_OUT_FILE) else 0
    logger.info("  Done! File size: %.1f MB", size_mb)
    return _OUT_FILE
