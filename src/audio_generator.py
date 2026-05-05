"""
Audio Generator – creates voice-over narration audio files per shot and
optionally assembles a background music track.

Backends (in priority order):
  1. ElevenLabs  – high-quality TTS (requires ELEVENLABS_API_KEY)
  2. gTTS        – free Google TTS (requires internet)
  3. pyttsx3     – offline TTS
  4. Silent WAV  – plain fallback (no voice, generates silence)
"""
from __future__ import annotations

import logging
import os
import wave
import struct
from pathlib import Path
from typing import Optional

from src.config import Config, get_config
from src.models import Screenplay, Shot

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Generates per-shot narration audio files."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.cfg = config or get_config()
        self._audio_dir = self.cfg.output_dir / "audio"

    # ------------------------------------------------------------------
    def generate_all(self, screenplay: Screenplay) -> Screenplay:
        """
        Generates an audio file for every Shot that has narration or dialogue,
        saves it to ``output/audio/``, and sets ``shot.audio`` metadata.
        Returns the updated screenplay.
        """
        total = screenplay.total_shots
        done = 0
        for scene in screenplay.scenes:
            for shot in scene.shots:
                text = self._get_speech_text(shot)
                if text:
                    audio_path = self._generate_audio(shot, scene.scene_number, text)
                    shot.audio_path = str(audio_path)
                done += 1
                logger.info(
                    "[%d/%d] Audio for Scene %d, Shot %d",
                    done,
                    total,
                    scene.scene_number,
                    shot.shot_number,
                )
        return screenplay

    # ------------------------------------------------------------------
    @staticmethod
    def _get_speech_text(shot: Shot) -> str:
        parts = []
        if shot.audio.narration:
            parts.append(shot.audio.narration)
        if shot.audio.dialogue:
            parts.append(shot.audio.dialogue)
        return " ".join(parts).strip()

    # ------------------------------------------------------------------
    def _generate_audio(self, shot: Shot, scene_number: int, text: str) -> Path:
        filename = f"scene{scene_number:02d}_shot{shot.shot_number:03d}.mp3"
        out_path = self._audio_dir / filename

        if out_path.exists():
            return out_path

        # Try backends in order
        if self.cfg.has_elevenlabs:
            if self._try_elevenlabs(text, out_path):
                return out_path

        if self._try_gtts(text, out_path):
            return out_path

        if self._try_pyttsx3(text, out_path):
            return out_path

        # Ultimate fallback: generate a silent WAV (renamed to .mp3 – most
        # players / moviepy accept it even with the wrong extension)
        wav_path = out_path.with_suffix(".wav")
        _write_silent_wav(wav_path, duration_seconds=shot.duration_seconds)
        wav_path.rename(out_path)
        logger.warning(
            "No TTS backend available – wrote silent audio for shot %d.",
            shot.shot_number,
        )
        return out_path

    # ------------------------------------------------------------------
    def _try_elevenlabs(self, text: str, out_path: Path) -> bool:
        try:
            import requests  # type: ignore

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.cfg.elevenlabs_voice_id}"
            headers = {
                "xi-api-key": self.cfg.elevenlabs_api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
            logger.info("ElevenLabs audio saved: %s", out_path)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("ElevenLabs TTS failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    @staticmethod
    def _try_gtts(text: str, out_path: Path) -> bool:
        try:
            from gtts import gTTS  # type: ignore

            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(str(out_path))
            logger.info("gTTS audio saved: %s", out_path)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("gTTS failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    @staticmethod
    def _try_pyttsx3(text: str, out_path: Path) -> bool:
        try:
            import pyttsx3  # type: ignore

            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.setProperty("volume", 0.9)
            wav_path = out_path.with_suffix(".wav")
            engine.save_to_file(text, str(wav_path))
            engine.runAndWait()
            wav_path.rename(out_path)
            logger.info("pyttsx3 audio saved: %s", out_path)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("pyttsx3 failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_silent_wav(path: Path, duration_seconds: float, sample_rate: int = 44100) -> None:
    """Write a PCM WAV file containing pure silence."""
    num_samples = int(sample_rate * duration_seconds)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * num_samples, *([0] * num_samples)))
