# 🎬 VIDEO-PROJECT – Animated Cinematic Video Generator

Generate a **full animated short film** from a single story idea – complete with
screenplay, cinematic shots, AI-generated visuals, voice-over narration, and a
final rendered MP4 – all in one command.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📖 **Screenplay generation** | GPT-4o writes a full multi-scene screenplay with shot-by-shot breakdowns |
| 🎨 **AI visuals** | DALL-E 3 renders each shot as a high-quality 1920 × 1080 image |
| 🎙 **Voice-over narration** | ElevenLabs → gTTS → pyttsx3 (falls back gracefully) |
| 🎬 **Ken Burns effect** | Smooth zoom/pan on each shot for a cinematic feel |
| 🔀 **Crossfade transitions** | Smooth dissolve between every shot |
| 🎵 **Music prompts** | Per-shot background-music description (ready for Suno / Udio) |
| 🌐 **Built-in web player** | One command spins up a local server – stream or download your film in any browser |
| 📦 **Offline demo mode** | Works without any API keys – placeholder images + silent audio |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (and optionally ELEVENLABS_API_KEY)
```

### 3. Run

```bash
# Full pipeline: screenplay → images → audio → video
python main.py --idea "A young astronaut discovers a living planet full of music"

# Generate AND open browser player/downloader when done
python main.py --idea "A young astronaut discovers a living planet full of music" --serve

# Serve already-generated videos for download/playback (no re-generation)
python main.py --serve-only

# Custom port
python main.py --serve-only --port 9000

# Custom style
python main.py --idea "A samurai ghost searches for redemption" --style "anime ink-wash"

# Screenplay only (no image/audio/video generation)
python main.py --idea "Two robots fall in love" --screenplay-only

# Control length
python main.py --idea "..." --scenes 4 --shots 3 --duration 120
```

The final MP4 is saved to `output/<title>.mp4`.

### 🌐 Download & Play Your Video

After generating, point your browser at `http://localhost:8080` to see a gallery
of all your films with an HTML5 in-browser player and a **⬇ Download** button.

```bash
python main.py --serve-only        # browse http://localhost:8080
```

---

## 🗂 Project Structure

```
VIDEO-PROJECT/
├── main.py                  # CLI entry point
├── requirements.txt
├── .env.example             # Copy to .env and fill in keys
├── src/
│   ├── config.py            # Config via env vars
│   ├── models.py            # Pydantic data models
│   ├── story_generator.py   # LLM screenplay writer
│   ├── scene_generator.py   # AI image generator (DALL-E 3)
│   ├── audio_generator.py   # TTS narration generator
│   ├── video_assembler.py   # MoviePy video renderer
│   └── server.py            # Built-in HTTP server (stream + download)
└── tests/
    └── test_pipeline.py     # Offline unit + integration tests
```

---

## 🔧 Configuration

All settings can be overridden via environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required for AI features)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | LLM for screenplay |
| `IMAGE_MODEL` | `dall-e-3` | Image model |
| `IMAGE_SIZE` | `1792x1024` | DALL-E image size |
| `IMAGE_QUALITY` | `hd` | DALL-E quality |
| `ELEVENLABS_API_KEY` | *(optional)* | ElevenLabs TTS key |
| `OUTPUT_DIR` | `output` | Where files are saved |
| `VIDEO_FPS` | `24` | Output video FPS |
| `VIDEO_WIDTH` | `1920` | Output width |
| `VIDEO_HEIGHT` | `1080` | Output height |
| `ZOOM_FACTOR` | `1.08` | Ken Burns zoom (1.0 = none) |
| `CROSSFADE_DURATION` | `0.5` | Transition length (s) |
| `TARGET_DURATION_SECONDS` | `180` | Target film length |
| `MAX_SCENES` | `6` | Number of scenes |
| `SHOTS_PER_SCENE` | `4` | Shots per scene |

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 📋 Pipeline Overview

```
Story Idea
    │
    ▼
StoryGenerator      ← GPT-4o writes full screenplay (scenes + shots + audio cues)
    │
    ▼
SceneGenerator      ← DALL-E 3 renders each shot as an HD image
    │
    ▼
AudioGenerator      ← ElevenLabs / gTTS generates narration per shot
    │
    ▼
VideoAssembler      ← MoviePy assembles images + audio → final MP4
    │
    ▼
  🎬 output/<title>.mp4
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.

## 📄 License

MIT