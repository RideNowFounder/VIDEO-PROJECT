"""
Tests for the animated cinematic video pipeline.

All tests run fully offline without any API keys – they exercise the demo /
fallback code paths.
"""
from __future__ import annotations

import json
import struct
import wave
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(tmp_path):
    """Return a Config pointing at a temp output dir."""
    from src.config import Config
    return Config(output_dir=tmp_path)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TestModels:
    def test_screenplay_total_duration(self):
        from src.models import AudioTrack, Scene, Screenplay, Shot, ShotType, MoodType

        shot = Shot(
            shot_number=1,
            shot_type=ShotType.WIDE,
            duration_seconds=6.0,
            visual_prompt="test",
            description="test",
        )
        scene = Scene(
            scene_number=1,
            title="T",
            location="L",
            mood=MoodType.DRAMATIC,
            scene_summary="S",
            shots=[shot],
        )
        sp = Screenplay(
            title="X",
            genre="Adventure",
            logline="l",
            original_idea="i",
            scenes=[scene],
        )
        assert sp.total_duration == 6.0
        assert sp.total_shots == 1

    def test_generation_status_defaults(self):
        from src.models import GenerationStatus
        gs = GenerationStatus()
        assert gs.screenplay_generated is False
        assert gs.errors == []


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_defaults(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        assert cfg.video_fps == 24
        assert cfg.video_width == 1920
        assert cfg.video_height == 1080
        assert not cfg.has_openai
        assert not cfg.has_elevenlabs

    def test_output_dirs_created(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        assert (cfg.output_dir / "images").is_dir()
        assert (cfg.output_dir / "audio").is_dir()


# ---------------------------------------------------------------------------
# Story Generator (demo path – no API key)
# ---------------------------------------------------------------------------

class TestStoryGenerator:
    def test_demo_screenplay(self, tmp_path):
        from src.story_generator import StoryGenerator
        cfg = _make_cfg(tmp_path)
        sg = StoryGenerator(cfg)
        sp = sg.generate("A hero saves the world")

        assert sp.title
        assert sp.logline
        assert len(sp.scenes) == cfg.max_scenes
        for scene in sp.scenes:
            assert len(scene.shots) == cfg.shots_per_scene

    def test_original_idea_preserved(self, tmp_path):
        from src.story_generator import StoryGenerator
        idea = "Unique story idea XYZ"
        cfg = _make_cfg(tmp_path)
        sp = StoryGenerator(cfg).generate(idea)
        assert sp.original_idea == idea

    def test_screenplay_serialization(self, tmp_path):
        from src.story_generator import StoryGenerator
        cfg = _make_cfg(tmp_path)
        sp = StoryGenerator(cfg).generate("Robot falls in love with a flower")
        data = json.loads(sp.model_dump_json())
        assert data["title"]
        assert len(data["scenes"]) > 0


# ---------------------------------------------------------------------------
# Scene Generator (placeholder path – no API key)
# ---------------------------------------------------------------------------

class TestSceneGenerator:
    def test_generates_placeholder_images(self, tmp_path):
        pytest.importorskip("PIL", reason="Pillow required for placeholder images")
        from src.story_generator import StoryGenerator
        from src.scene_generator import SceneGenerator

        cfg = _make_cfg(tmp_path)
        sp = StoryGenerator(cfg).generate("A dragon learns to paint")
        SceneGenerator(cfg).generate_all(sp)

        for scene in sp.scenes:
            for shot in scene.shots:
                assert shot.image_path is not None
                assert Path(shot.image_path).exists()
                assert Path(shot.image_path).stat().st_size > 0

    def test_existing_image_not_regenerated(self, tmp_path):
        """If image already exists on disk, SceneGenerator must not overwrite it."""
        pytest.importorskip("PIL")
        from src.story_generator import StoryGenerator
        from src.scene_generator import SceneGenerator

        cfg = _make_cfg(tmp_path)
        sp = StoryGenerator(cfg).generate("A cat explores space")
        SceneGenerator(cfg).generate_all(sp)

        # Record mtimes
        mtimes = {
            shot.image_path: Path(shot.image_path).stat().st_mtime
            for scene in sp.scenes
            for shot in scene.shots
        }

        # Run again – should NOT regenerate
        SceneGenerator(cfg).generate_all(sp)

        for path, mtime in mtimes.items():
            assert Path(path).stat().st_mtime == mtime


# ---------------------------------------------------------------------------
# Audio Generator (silent fallback path – no TTS backend)
# ---------------------------------------------------------------------------

class TestAudioGenerator:
    def test_generates_audio_files(self, tmp_path):
        from src.story_generator import StoryGenerator
        from src.audio_generator import AudioGenerator

        cfg = _make_cfg(tmp_path)
        sp = StoryGenerator(cfg).generate("A mermaid discovers a lost city")

        # Disable all real TTS backends so we always hit the silent WAV fallback
        with (
            patch("src.audio_generator.AudioGenerator._try_elevenlabs", return_value=False),
            patch("src.audio_generator.AudioGenerator._try_gtts", return_value=False),
            patch("src.audio_generator.AudioGenerator._try_pyttsx3", return_value=False),
        ):
            ag = AudioGenerator(cfg)
            ag.generate_all(sp)

        # Every shot with narration should have an audio file
        for scene in sp.scenes:
            for shot in scene.shots:
                if shot.audio.narration or shot.audio.dialogue:
                    audio_path = getattr(shot, "audio_path", None)
                    assert audio_path is not None, f"Shot {shot.shot_number} missing audio_path"
                    assert Path(audio_path).exists(), f"Audio file missing: {audio_path}"

    def test_silent_wav_helper(self, tmp_path):
        from src.audio_generator import _write_silent_wav
        out = tmp_path / "silence.wav"
        _write_silent_wav(out, duration_seconds=2.0)
        assert out.exists()
        with wave.open(str(out)) as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 44100


# ---------------------------------------------------------------------------
# Pipeline integration (dry run – no video rendering)
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    def test_story_to_images_pipeline(self, tmp_path):
        """Screenplay → image generation completes without errors."""
        pytest.importorskip("PIL")
        from src.story_generator import StoryGenerator
        from src.scene_generator import SceneGenerator

        cfg = _make_cfg(tmp_path)
        cfg.max_scenes = 2
        cfg.shots_per_scene = 2

        sp = StoryGenerator(cfg).generate("Two robots become best friends")
        sp = SceneGenerator(cfg).generate_all(sp)

        assert sp.total_shots == 4
        for scene in sp.scenes:
            for shot in scene.shots:
                assert shot.image_path and Path(shot.image_path).exists()


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class TestServer:
    def _get(self, server, path: str):
        """Make a GET request to the running server and return (status, body)."""
        import http.client
        host, port = server.server_address
        conn = http.client.HTTPConnection(f"localhost:{port}", timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, body

    def test_index_empty(self, tmp_path):
        """Index page loads with 200 and shows 'No videos found' when output is empty."""
        from src.server import start_server

        srv = start_server(tmp_path, port=0, open_browser=False, block=False)
        try:
            status, body = self._get(srv, "/")
            assert status == 200
            assert b"No videos found" in body
        finally:
            srv.shutdown()
            srv.server_close()

    def test_index_with_video(self, tmp_path):
        """Index page lists an MP4 file and shows a download button."""
        from src.server import start_server

        # Create a tiny fake MP4
        fake_mp4 = tmp_path / "my_film.mp4"
        fake_mp4.write_bytes(b"\x00" * 1024)

        srv = start_server(tmp_path, port=0, open_browser=False, block=False)
        try:
            status, body = self._get(srv, "/")
            assert status == 200
            assert b"my_film.mp4" in body
            assert b"Download" in body
        finally:
            srv.shutdown()
            srv.server_close()

    def test_file_download(self, tmp_path):
        """Requesting a file directly returns its bytes."""
        from src.server import start_server

        content = b"FAKE_MP4_CONTENT"
        (tmp_path / "film.mp4").write_bytes(content)

        srv = start_server(tmp_path, port=0, open_browser=False, block=False)
        try:
            status, body = self._get(srv, "/film.mp4")
            assert status == 200
            assert body == content
        finally:
            srv.shutdown()
            srv.server_close()

    def test_path_traversal_blocked(self, tmp_path):
        """Requests that try to escape output_dir are rejected with 403 or 404."""
        from src.server import start_server

        srv = start_server(tmp_path, port=0, open_browser=False, block=False)
        try:
            # Use a relative path traversal that doesn't rely on any specific OS file
            status, _ = self._get(srv, "/%2e%2e/outside.txt")
            assert status in (403, 404)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_missing_file_returns_404(self, tmp_path):
        """Requesting a non-existent file returns 404."""
        from src.server import start_server

        srv = start_server(tmp_path, port=0, open_browser=False, block=False)
        try:
            status, _ = self._get(srv, "/nonexistent.mp4")
            assert status == 404
        finally:
            srv.shutdown()
            srv.server_close()
