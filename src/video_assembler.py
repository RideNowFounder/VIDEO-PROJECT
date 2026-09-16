"""
Video Assembler – combines generated images and audio into a final MP4 video.

For each shot it:
  - Loads the image
  - Applies a Ken Burns zoom/pan effect to simulate camera movement
  - Adds cross-fade transitions between shots
  - Layers per-shot narration audio
  - Renders to a final HD MP4

Requires: moviepy, Pillow, numpy
"""
from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Optional

import numpy as np

from src.config import Config, get_config
from src.models import Screenplay

logger = logging.getLogger(__name__)


class VideoAssembler:
    """Assembles images + audio into a finished MP4."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.cfg = config or get_config()

    # ------------------------------------------------------------------
    def assemble(self, screenplay: Screenplay, output_filename: str = "") -> Path:
        """
        Build the final video from *screenplay* and return the output path.
        """
        try:
            try:
                from moviepy.editor import (  # type: ignore
                    AudioFileClip,
                    CompositeVideoClip,
                    ImageClip,
                    concatenate_videoclips,
                )
            except ImportError:
                from moviepy import (  # type: ignore
                    AudioFileClip,
                    CompositeVideoClip,
                    ImageClip,
                    concatenate_videoclips,
                )
            from PIL import Image  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "moviepy and Pillow are required. "
                "Run: pip install moviepy Pillow"
            ) from exc

        if not output_filename:
            safe_title = screenplay.title.replace(" ", "_").replace("/", "-")[:40]
            output_filename = f"{safe_title}.mp4"

        output_path = self.cfg.output_dir / output_filename
        w, h = self.cfg.video_width, self.cfg.video_height
        fps = self.cfg.video_fps

        clips = []
        for scene in screenplay.scenes:
            for shot in scene.shots:
                img_path = shot.image_path
                if not img_path or not Path(img_path).exists():
                    logger.warning(
                        "Missing image for scene %d shot %d – using black frame.",
                        scene.scene_number,
                        shot.shot_number,
                    )
                    frame = np.zeros((h, w, 3), dtype=np.uint8)
                    img_path = str(
                        self.cfg.output_dir
                        / "images"
                        / f"black_{shot.shot_number:03d}.png"
                    )
                    Image.fromarray(frame).save(img_path)

                duration = shot.duration_seconds
                clip = self._make_ken_burns_clip(
                    img_path, duration, w, h, fps
                )
                subtitle_text = self._subtitle_for_shot(shot)
                clip = self._add_subtitle_overlay(clip, subtitle_text, w, h)

                # Attach per-shot audio if present
                audio_path = shot.audio_path
                if audio_path and Path(audio_path).exists():
                    try:
                        audio_clip = AudioFileClip(audio_path).subclip(0, duration)
                        clip = _with_audio(clip, audio_clip)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Could not attach audio for shot %d: %s", shot.shot_number, exc)

                clips.append(clip)

        if not clips:
            raise ValueError("No clips to assemble – check that images were generated.")

        logger.info("Concatenating %d clips with crossfade…", len(clips))
        final = concatenate_videoclips(clips, method="compose", padding=-self.cfg.crossfade_duration)
        if hasattr(final, "fadein") and hasattr(final, "fadeout"):
            final = final.fadein(0.5).fadeout(0.5)

        logger.info("Writing final video → %s", output_path)
        final.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            preset="medium",
            threads=os.cpu_count() or 4,
            logger=None,  # suppress moviepy's own progress bar in favour of ours
        )

        for clip in clips:
            clip.close()
        final.close()

        logger.info("✅ Video ready: %s", output_path)
        return output_path

    def _subtitle_for_shot(self, shot) -> str:
        text = shot.audio.dialogue or shot.audio.narration or ""
        if not text:
            return ""
        return text.strip()

    def _add_subtitle_overlay(self, base_clip, subtitle: str, w: int, h: int):
        if not subtitle:
            return base_clip
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
        except ImportError:
            return base_clip
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip  # type: ignore
        except ImportError:
            from moviepy import ImageClip, CompositeVideoClip  # type: ignore

        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = _load_subtitle_font(48)
        wrapped = _wrap_text(subtitle, 34)
        box_h = 110 + (max(1, len(wrapped)) * 56)
        y0 = h - box_h - 90
        draw.rounded_rectangle([(50, y0), (w - 50, h - 40)], radius=32, fill=(0, 0, 0, 165))
        y = y0 + 28
        for line in wrapped:
            draw.text((90, y), line, fill=(255, 255, 255, 255), font=font)
            y += 54
        subtitle_clip = ImageClip(np.array(overlay))
        subtitle_clip = _with_duration(subtitle_clip, base_clip.duration)
        subtitle_clip = _with_position(subtitle_clip, ("center", "center"))
        return CompositeVideoClip([base_clip, subtitle_clip], size=(w, h))

    # ------------------------------------------------------------------
    def _make_ken_burns_clip(
        self, image_path: str, duration: float, w: int, h: int, fps: int
    ):
        """
        Load image, resize/crop to target resolution, apply Ken Burns effect
        (gradual zoom), and return an ImageClip with the effect baked in as a
        VideoClip using make_frame.
        """
        try:
            from moviepy.editor import VideoClip  # type: ignore
        except ImportError:
            from moviepy import VideoClip  # type: ignore
        from PIL import Image  # type: ignore

        # ---- load & fit image ----
        img = Image.open(image_path).convert("RGB")
        img = _resize_cover(img, w, h)
        arr = np.array(img, dtype=np.uint8)

        zoom = self.cfg.zoom_factor  # e.g. 1.08

        def make_frame(t: float) -> np.ndarray:
            progress = t / duration  # 0→1
            # Zoom from 1.0 → zoom over the clip
            scale = 1.0 + (zoom - 1.0) * progress
            new_w = int(w * scale)
            new_h = int(h * scale)

            # Crop centre
            x_off = (new_w - w) // 2
            y_off = (new_h - h) // 2

            frame_img = Image.fromarray(arr)
            frame_img = frame_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            frame_arr = np.array(frame_img)
            return frame_arr[y_off : y_off + h, x_off : x_off + w]

        try:
            return VideoClip(make_frame, duration=duration)
        except TypeError:
            return VideoClip(frame_function=make_frame, duration=duration)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resize_cover(img, target_w: int, target_h: int):
    """Resize *img* so it fills (target_w × target_h), then centre-crop."""
    from PIL import Image  # type: ignore

    orig_w, orig_h = img.size
    scale = max(target_w / orig_w, target_h / orig_h)
    new_w = math.ceil(orig_w * scale)
    new_h = math.ceil(orig_h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    x = (new_w - target_w) // 2
    y = (new_h - target_h) // 2
    return img.crop((x, y, x + target_w, y + target_h))


def _with_duration(clip, duration: float):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _with_position(clip, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_position(position)


def _with_audio(clip, audio_clip):
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio_clip)
    return clip.set_audio(audio_clip)


def _load_subtitle_font(size: int):
    from PIL import ImageFont  # type: ignore

    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for fp in font_candidates:
        try:
            return ImageFont.truetype(fp, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, width: int) -> list[str]:
    import textwrap

    return textwrap.wrap(text, width)
