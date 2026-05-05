"""
Data models for the animated cinematic video pipeline.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ShotType(str, Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close-up"
    EXTREME_CLOSE_UP = "extreme close-up"
    OVER_THE_SHOULDER = "over-the-shoulder"
    AERIAL = "aerial"
    LOW_ANGLE = "low-angle"
    HIGH_ANGLE = "high-angle"
    TRACKING = "tracking"
    PAN = "pan"


class MoodType(str, Enum):
    DRAMATIC = "dramatic"
    ROMANTIC = "romantic"
    MYSTERIOUS = "mysterious"
    ADVENTUROUS = "adventurous"
    COMEDIC = "comedic"
    SUSPENSEFUL = "suspenseful"
    MELANCHOLIC = "melancholic"
    TRIUMPHANT = "triumphant"
    SERENE = "serene"
    TENSE = "tense"


class AudioTrack(BaseModel):
    """Represents the audio elements for a shot."""

    narration: str = Field(default="", description="Voice-over narration text")
    dialogue: str = Field(default="", description="Character dialogue")
    music_prompt: str = Field(default="", description="Description of background music style")
    sound_effects: List[str] = Field(default_factory=list, description="List of sound effects")


class Shot(BaseModel):
    """A single cinematic shot within a scene."""

    shot_number: int = Field(description="Sequential shot number")
    shot_type: ShotType = Field(description="Type of camera shot")
    duration_seconds: float = Field(ge=1.0, le=30.0, description="Duration of this shot in seconds")
    visual_prompt: str = Field(description="Detailed AI image generation prompt for this shot")
    description: str = Field(description="Human-readable description of what happens")
    audio: AudioTrack = Field(default_factory=AudioTrack)
    camera_movement: str = Field(default="static", description="Camera movement instruction")
    lighting: str = Field(default="natural", description="Lighting style for this shot")
    color_palette: str = Field(default="", description="Color palette description")
    image_path: Optional[str] = Field(default=None, description="Path to the generated image file")
    audio_path: Optional[str] = Field(default=None, description="Path to the generated audio file")


class Scene(BaseModel):
    """A complete scene made up of multiple shots."""

    scene_number: int = Field(description="Sequential scene number")
    title: str = Field(description="Short scene title")
    location: str = Field(description="Where the scene takes place")
    time_of_day: str = Field(default="day", description="Time of day (dawn/day/dusk/night)")
    mood: MoodType = Field(description="Emotional tone of the scene")
    shots: List[Shot] = Field(default_factory=list)
    scene_summary: str = Field(description="Brief summary of what happens in this scene")

    @property
    def total_duration(self) -> float:
        return sum(s.duration_seconds for s in self.shots)


class Character(BaseModel):
    """A character in the story."""

    name: str
    description: str = Field(description="Physical and personality description")
    role: str = Field(description="Role in the story (protagonist/antagonist/supporting)")


class Screenplay(BaseModel):
    """The full generated screenplay / storyboard."""

    title: str
    genre: str
    logline: str = Field(description="One-sentence story summary")
    original_idea: str = Field(description="The raw story idea provided by the user")
    characters: List[Character] = Field(default_factory=list)
    scenes: List[Scene] = Field(default_factory=list)
    style: str = Field(
        default="cinematic animated 3D",
        description="Visual style of the animation",
    )
    total_duration_target: float = Field(
        default=180.0, description="Target total duration in seconds"
    )

    @property
    def total_duration(self) -> float:
        return sum(scene.total_duration for scene in self.scenes)

    @property
    def total_shots(self) -> int:
        return sum(len(scene.shots) for scene in self.scenes)


class GenerationStatus(BaseModel):
    """Tracks the progress of the video generation pipeline."""

    screenplay_generated: bool = False
    images_generated: int = 0
    total_images: int = 0
    audio_generated: bool = False
    video_assembled: bool = False
    output_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
