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
    """Return the offline 60s Hinglish screenplay used when no API key is present."""
    characters = [
        Character(
            name="Aman",
            description=(
                "20-year-old Indian competitive-exam student, round glasses, messy "
                "black hair, blue T-shirt, procrastinates but means well"
            ),
            role="protagonist",
        ),
        Character(
            name="Ravi",
            description="Aman's funny friend, curly black hair, yellow hoodie, always joking",
            role="supporting",
        ),
        Character(
            name="Mummy",
            description=(
                "Middle-aged Indian mother in colorful salwar suit, sarcastic but loving, "
                "keeps Aman grounded"
            ),
            role="supporting",
        ),
    ]
    scene_data = [
        {
            "title": "Messy Morning Promise",
            "location": "Aman's messy study room",
            "mood": MoodType.COMEDIC,
            "shot_type": ShotType.WIDE,
            "description": "Messy study table, books everywhere, Aman staring at syllabus in panic.",
            "dialogue": "Aman: Aaj full focus. Kal se pakka wali aadat khatam.",
        },
        {
            "title": "Mission Clean Desk",
            "location": "Same room, table cleaning montage",
            "mood": MoodType.COMEDIC,
            "shot_type": ShotType.TRACKING,
            "description": "Aman aggressively cleans table, arranges books, sprays confidence.",
            "dialogue": "Narrator: Padhai se pehle safai. Classic topper illusion mode on.",
        },
        {
            "title": "Mummy at the Door",
            "location": "Outside Aman's room",
            "mood": MoodType.COMEDIC,
            "shot_type": ShotType.OVER_THE_SHOULDER,
            "description": "Mummy stands outside door with raised eyebrow and steel-glass of chai.",
            "dialogue": "Mummy: Beta padhai shuru hui ya timetable ka bhi trailer chal raha hai?",
        },
        {
            "title": "Phone Trap",
            "location": "Study table close-up",
            "mood": MoodType.TENSE,
            "shot_type": ShotType.CLOSE_UP,
            "description": "Aman opens phone for one doubt video, then reels flood screen.",
            "dialogue": "Aman: Bas 2 minute ke liye phone. Ravi meme bhej de toh ignore kaise karu?",
        },
        {
            "title": "Clock Sprint",
            "location": "Wall clock and study desk",
            "mood": MoodType.COMEDIC,
            "shot_type": ShotType.EXTREME_CLOSE_UP,
            "description": "Clock hand jumps from 10 AM to 3 PM while Aman keeps scrolling.",
            "dialogue": "Narrator: 10 baje start plan tha. 3 baje tak sirf motivation videos complete.",
        },
        {
            "title": "Ravi Roast Finale",
            "location": "Balcony corner study area",
            "mood": MoodType.COMEDIC,
            "shot_type": ShotType.MEDIUM,
            "description": "Aman and Ravi laugh together as notebook reads 'Kal Se Pakka'.",
            "dialogue": "Ravi: Bhai tera syllabus nahi, tera kal hi sabse consistent hai!",
        },
    ]
    scenes = []
    for idx, entry in enumerate(scene_data, start=1):
        shot = Shot(
            shot_number=idx,
            shot_type=entry["shot_type"],
            duration_seconds=10.0,
            visual_prompt=(
                "Original stylized 2D cartoon illustration, Indian student comedy, "
                f"scene {idx}: {entry['description']}"
            ),
            description=entry["description"],
            camera_movement="gentle push-in",
            lighting="bright natural indoor daylight",
            color_palette="warm Indian home tones with playful colors",
            audio=AudioTrack(
                narration=entry["dialogue"] if idx in (2, 5) else "",
                dialogue=entry["dialogue"] if idx not in (2, 5) else "",
                music_prompt="light comedic beat with playful percussion",
                sound_effects=["clock tick", "page flip", "mobile ping"],
            ),
        )
        scenes.append(
            Scene(
                scene_number=idx,
                title=entry["title"],
                location=entry["location"],
                time_of_day="day",
                mood=entry["mood"],
                scene_summary=entry["description"],
                shots=[shot],
            )
        )

    return Screenplay(
        title="Kal Se Pakka",
        genre="Hinglish Cartoon Comedy",
        logline=(
            "Aman plans a serious study day, but procrastination, Mummy's sarcasm, "
            "and Ravi's jokes turn it into a 60-second comedy spiral."
        ),
        original_idea=idea,
        characters=characters,
        scenes=scenes,
        style="Original programmatic cartoon illustration",
        total_duration_target=60.0,
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
