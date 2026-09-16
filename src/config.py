"""
Configuration management – reads settings from environment variables.

Copy `.env.example` to `.env` and fill in your API keys before running.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # ------------------------------------------------------------------ #
    # OpenAI
    # ------------------------------------------------------------------ #
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    image_model: str = field(
        default_factory=lambda: os.getenv("IMAGE_MODEL", "dall-e-3")
    )
    image_size: str = field(
        default_factory=lambda: os.getenv("IMAGE_SIZE", "1792x1024")
    )
    image_quality: str = field(
        default_factory=lambda: os.getenv("IMAGE_QUALITY", "hd")
    )

    # ------------------------------------------------------------------ #
    # ElevenLabs (text-to-speech)
    # ------------------------------------------------------------------ #
    elevenlabs_api_key: str = field(
        default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", "")
    )
    elevenlabs_voice_id: str = field(
        default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    )

    # ------------------------------------------------------------------ #
    # Output paths
    # ------------------------------------------------------------------ #
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "output"))
    )

    # ------------------------------------------------------------------ #
    # Video settings
    # ------------------------------------------------------------------ #
    video_fps: int = field(default_factory=lambda: int(os.getenv("VIDEO_FPS", "24")))
    video_width: int = field(default_factory=lambda: int(os.getenv("VIDEO_WIDTH", "1920")))
    video_height: int = field(default_factory=lambda: int(os.getenv("VIDEO_HEIGHT", "1080")))
    # Ken Burns zoom range (1.0 = no zoom, 1.1 = 10 % zoom)
    zoom_factor: float = field(
        default_factory=lambda: float(os.getenv("ZOOM_FACTOR", "1.08"))
    )
    crossfade_duration: float = field(
        default_factory=lambda: float(os.getenv("CROSSFADE_DURATION", "0.5"))
    )

    # ------------------------------------------------------------------ #
    # Story generation
    # ------------------------------------------------------------------ #
    target_duration_seconds: int = field(
        default_factory=lambda: int(os.getenv("TARGET_DURATION_SECONDS", "180"))
    )
    shots_per_scene: int = field(
        default_factory=lambda: int(os.getenv("SHOTS_PER_SCENE", "4"))
    )
    max_scenes: int = field(
        default_factory=lambda: int(os.getenv("MAX_SCENES", "6"))
    )

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "audio").mkdir(parents=True, exist_ok=True)

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_elevenlabs(self) -> bool:
        return bool(self.elevenlabs_api_key)


# Module-level singleton
_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
