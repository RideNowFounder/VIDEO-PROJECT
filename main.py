"""
Main entry-point for the Animated Cinematic Video Generator.

Usage:
    python main.py --idea "A young astronaut discovers a living planet"
    python main.py --idea "..." --style "anime" --output my_film.mp4
    python main.py --idea "..." --screenplay-only   # skip image/audio/video
    python main.py --idea "..." --serve             # generate then open browser player
    python main.py --serve-only                     # serve already-generated videos
    python main.py --serve-only --port 9000         # custom port
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("video_project")


def _load_dotenv() -> None:
    """Load .env file if python-dotenv is installed."""
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except ImportError:
        pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="video-project",
        description="Generate a full animated cinematic short film from a story idea.",
    )
    parser.add_argument(
        "--idea",
        default="",
        help="Your story idea (any length, any language). Required unless --serve-only is set.",
    )
    parser.add_argument(
        "--style",
        default="cinematic animated 3D Pixar-style",
        help="Animation / visual style (default: 'cinematic animated 3D Pixar-style').",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output MP4 filename (default: auto-generated from title).",
    )
    parser.add_argument(
        "--screenplay-only",
        action="store_true",
        help="Only generate the screenplay JSON, skip image/audio/video steps.",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Skip audio generation step.",
    )
    parser.add_argument(
        "--screenplay-file",
        default="",
        help="Path to an existing screenplay JSON to skip story generation.",
    )
    parser.add_argument(
        "--scenes",
        type=int,
        default=None,
        help="Override number of scenes (default: from config / 6).",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=None,
        help="Override shots per scene (default: from config / 4).",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Target video duration in seconds (default: 180).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="After generation, start a local web server to stream / download the video.",
    )
    parser.add_argument(
        "--serve-only",
        action="store_true",
        help="Skip generation and just start the web server for already-generated videos.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the built-in web server (default: 8080).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically when starting the server.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def _print_banner() -> None:
    banner = r"""
  ╔══════════════════════════════════════════════════════════╗
  ║         🎬  ANIMATED CINEMATIC VIDEO GENERATOR  🎬       ║
  ╚══════════════════════════════════════════════════════════╝
"""
    print(banner)


def _print_screenplay_summary(sp) -> None:
    print("\n" + "=" * 60)
    print(f"  📖  {sp.title}")
    print(f"  🎭  Genre: {sp.genre}")
    print(f"  ✏️   {sp.logline}")
    print(f"  🎬  {len(sp.scenes)} scenes  |  {sp.total_shots} shots  |  ~{sp.total_duration:.0f}s")
    print(f"  🎨  Style: {sp.style}")
    print("=" * 60)
    for scene in sp.scenes:
        print(f"\n  Scene {scene.scene_number}: {scene.title}  [{scene.location}]")
        for shot in scene.shots:
            print(
                f"    Shot {shot.shot_number:3d} [{shot.shot_type.value:20s}] "
                f"{shot.duration_seconds:.1f}s – {shot.description[:60]}"
            )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    _load_dotenv()
    args = _parse_args()
    _print_banner()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    from src.config import get_config
    cfg = get_config()

    # ------------------------------------------------------------------
    # Serve-only: just start the web server, no generation
    # ------------------------------------------------------------------
    if args.serve_only:
        from src.server import start_server
        start_server(cfg.output_dir, port=args.port, open_browser=not args.no_browser)
        return 0

    # ------------------------------------------------------------------
    # Validate --idea is present for generation paths
    # ------------------------------------------------------------------
    if not args.idea:
        print("error: --idea is required unless --serve-only is set.", file=sys.stderr)
        return 1

    if args.scenes:
        cfg.max_scenes = args.scenes
    if args.shots:
        cfg.shots_per_scene = args.shots
    if args.duration:
        cfg.target_duration_seconds = args.duration

    # ------------------------------------------------------------------
    # Step 1 – Screenplay
    # ------------------------------------------------------------------
    from src.models import Screenplay

    if args.screenplay_file:
        logger.info("Loading screenplay from %s", args.screenplay_file)
        sp_data = json.loads(Path(args.screenplay_file).read_text())
        from src.story_generator import StoryGenerator
        sp = StoryGenerator._parse_screenplay(sp_data, args.idea)
    else:
        logger.info("🖊  Generating screenplay…")
        from src.story_generator import StoryGenerator
        sg = StoryGenerator(cfg)
        sp = sg.generate(args.idea, style=args.style)

    _print_screenplay_summary(sp)

    # Save screenplay JSON
    sp_path = cfg.output_dir / "screenplay.json"
    sp_path.write_text(sp.model_dump_json(indent=2))
    logger.info("Screenplay saved → %s", sp_path)

    if args.screenplay_only:
        print(f"\n✅ Screenplay saved to: {sp_path}")
        return 0

    # ------------------------------------------------------------------
    # Step 2 – Generate Images
    # ------------------------------------------------------------------
    logger.info("🎨  Generating scene images…")
    from src.scene_generator import SceneGenerator
    sg2 = SceneGenerator(cfg)
    sp = sg2.generate_all(sp)
    logger.info("Images generated: %d", sp.total_shots)

    # ------------------------------------------------------------------
    # Step 3 – Generate Audio
    # ------------------------------------------------------------------
    if not args.no_audio:
        logger.info("🎙  Generating audio narration…")
        from src.audio_generator import AudioGenerator
        ag = AudioGenerator(cfg)
        sp = ag.generate_all(sp)
        logger.info("Audio generation complete.")

    # ------------------------------------------------------------------
    # Step 4 – Assemble Video
    # ------------------------------------------------------------------
    logger.info("🎬  Assembling final video…")
    from src.video_assembler import VideoAssembler
    va = VideoAssembler(cfg)
    video_path = va.assemble(sp, output_filename=args.output)

    print(f"\n🎉  Your animated cinematic film is ready:\n    {video_path}\n")

    # ------------------------------------------------------------------
    # Step 5 (optional) – Serve for download / playback
    # ------------------------------------------------------------------
    if args.serve:
        from src.server import start_server
        start_server(cfg.output_dir, port=args.port, open_browser=not args.no_browser)

    return 0


if __name__ == "__main__":
    sys.exit(main())
