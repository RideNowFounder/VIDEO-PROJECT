"""
Story Generator – converts a raw story idea into a full structured screenplay
using an LLM (OpenAI GPT-4o by default).

When no OpenAI key is present, a deterministic demo screenplay is returned so
the rest of the pipeline can be tested without API credentials.
"""
from __future__ import annotations

import json
import logging
import textwrap
from typing import Optional

from src.config import Config, get_config
from src.models import (
    AudioTrack,
    Character,
    MoodType,
    Scene,
    Screenplay,
    Shot,
    ShotType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a professional cinematic animated short-film director and screenwriter.
    Given a story idea, you produce a full, detailed animated screenplay in JSON.

    Rules:
    - Create {max_scenes} scenes.
    - Each scene has exactly {shots_per_scene} shots.
    - Total runtime must be approximately {target_duration}s.
    - Every shot must include a vivid, detailed AI image-generation prompt
      (visual_prompt) that describes the exact frame in rich visual language,
      specifying animation style, lighting, colors, camera angle, and emotion.
    - Include narration, dialogue, music description, and sound effects per shot.
    - Shots must feel like a real animated feature film (Pixar / DreamWorks quality).
    - Return ONLY valid JSON matching the schema exactly.
    """
)

_USER_PROMPT = textwrap.dedent(
    """
    Story idea: {idea}

    Animation style: {style}

    Return a JSON object with this exact structure:
    {{
      "title": "string",
      "genre": "string",
      "logline": "string",
      "style": "string",
      "characters": [
        {{"name": "string", "description": "string", "role": "string"}}
      ],
      "scenes": [
        {{
          "scene_number": 1,
          "title": "string",
          "location": "string",
          "time_of_day": "day|dawn|dusk|night",
          "mood": "dramatic|romantic|mysterious|adventurous|comedic|suspenseful|melancholic|triumphant|serene|tense",
          "scene_summary": "string",
          "shots": [
            {{
              "shot_number": 1,
              "shot_type": "wide|medium|close-up|extreme close-up|over-the-shoulder|aerial|low-angle|high-angle|tracking|pan",
              "duration_seconds": 5.0,
              "visual_prompt": "string",
              "description": "string",
              "camera_movement": "string",
              "lighting": "string",
              "color_palette": "string",
              "audio": {{
                "narration": "string",
                "dialogue": "string",
                "music_prompt": "string",
                "sound_effects": ["string"]
              }}
            }}
          ]
        }}
      ]
    }}
    """
)


# ---------------------------------------------------------------------------
# Demo fallback screenplay (used when no API key is available)
# ---------------------------------------------------------------------------

def _make_demo_screenplay(idea: str, cfg: Config) -> Screenplay:
    """Return a hardcoded demo screenplay so offline tests pass."""
    characters = [
        Character(name="Aria", description="A brave young explorer with golden hair", role="protagonist"),
        Character(name="Shadow", description="A mysterious ancient spirit", role="antagonist"),
    ]
    scenes = []
    moods = [MoodType.ADVENTUROUS, MoodType.MYSTERIOUS, MoodType.DRAMATIC,
             MoodType.TENSE, MoodType.TRIUMPHANT, MoodType.SERENE]
    shot_types = [ShotType.WIDE, ShotType.MEDIUM, ShotType.CLOSE_UP, ShotType.AERIAL]
    locations = [
        "Ancient forest at dawn", "Mystical cave interior", "Mountain peak",
        "Hidden temple ruins", "Glowing crystal valley", "Sky above the clouds",
    ]

    for i in range(min(cfg.max_scenes, 6)):
        shots = []
        for j in range(cfg.shots_per_scene):
            shot_num = i * cfg.shots_per_scene + j + 1
            shots.append(
                Shot(
                    shot_number=shot_num,
                    shot_type=shot_types[j % len(shot_types)],
                    duration_seconds=5.0,
                    visual_prompt=(
                        f"Cinematic animated scene, {locations[i]}, "
                        f"shot {j+1}, high quality 3D animation, dramatic lighting, "
                        f"vibrant colors, Pixar style"
                    ),
                    description=f"Scene {i+1}, shot {j+1} from the story: {idea[:60]}",
                    camera_movement="slow push-in",
                    lighting="cinematic",
                    color_palette="warm golden tones with deep shadows",
                    audio=AudioTrack(
                        narration=f"And so the journey continues in {locations[i]}…",
                        dialogue="",
                        music_prompt="epic orchestral score, strings and horns",
                        sound_effects=["wind", "footsteps"],
                    ),
                )
            )
        scenes.append(
            Scene(
                scene_number=i + 1,
                title=f"Chapter {i+1}: {locations[i]}",
                location=locations[i],
                time_of_day="dawn" if i == 0 else "day",
                mood=moods[i % len(moods)],
                scene_summary=f"Scene {i+1} of the story unfolds at {locations[i]}.",
                shots=shots,
            )
        )

    return Screenplay(
        title="The Animated Adventure",
        genre="Adventure / Fantasy",
        logline=f"A brave hero embarks on an epic quest inspired by: {idea[:80]}",
        original_idea=idea,
        characters=characters,
        scenes=scenes,
        style=cfg.openai_model,
        total_duration_target=float(cfg.target_duration_seconds),
    )


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

class StoryGenerator:
    """Generates a Screenplay from a plain-text story idea."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.cfg = config or get_config()

    # ------------------------------------------------------------------
    def generate(self, idea: str, style: str = "cinematic animated 3D Pixar-style") -> Screenplay:
        """
        Convert *idea* into a full Screenplay.
        Falls back to a demo screenplay when no OpenAI key is configured.
        """
        if not self.cfg.has_openai:
            logger.warning(
                "OPENAI_API_KEY not set – returning demo screenplay. "
                "Set the key to generate a real story."
            )
            sp = _make_demo_screenplay(idea, self.cfg)
            sp.original_idea = idea
            return sp

        return self._call_openai(idea, style)

    # ------------------------------------------------------------------
    def _call_openai(self, idea: str, style: str) -> Screenplay:
        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "openai package is required. Run: pip install openai"
            ) from exc

        client = openai.OpenAI(api_key=self.cfg.openai_api_key)

        system = _SYSTEM_PROMPT.format(
            max_scenes=self.cfg.max_scenes,
            shots_per_scene=self.cfg.shots_per_scene,
            target_duration=self.cfg.target_duration_seconds,
        )
        user = _USER_PROMPT.format(idea=idea, style=style)

        logger.info("Calling %s to generate screenplay…", self.cfg.openai_model)
        response = client.chat.completions.create(
            model=self.cfg.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.85,
        )

        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)

        sp = self._parse_screenplay(data, idea)
        logger.info(
            "Screenplay '%s' generated: %d scenes, %d shots, ~%.0fs",
            sp.title,
            len(sp.scenes),
            sp.total_shots,
            sp.total_duration,
        )
        return sp

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_screenplay(data: dict, original_idea: str) -> Screenplay:
        characters = [Character(**c) for c in data.get("characters", [])]
        scenes = []
        for s in data.get("scenes", []):
            shots = []
            for sh in s.get("shots", []):
                audio_data = sh.pop("audio", {})
                audio = AudioTrack(**audio_data)
                shots.append(Shot(**sh, audio=audio))
            s_copy = {k: v for k, v in s.items() if k != "shots"}
            scenes.append(Scene(**s_copy, shots=shots))

        return Screenplay(
            title=data.get("title", "Untitled"),
            genre=data.get("genre", "Adventure"),
            logline=data.get("logline", ""),
            original_idea=original_idea,
            characters=characters,
            scenes=scenes,
            style=data.get("style", "cinematic animated 3D"),
            total_duration_target=float(data.get("total_duration_target", 180)),
        )
