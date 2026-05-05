# रामलाल की कहानी — Ramlal's Story
### A Cinematic Animated Film

> *"मुश्किल समय में हार नहीं माननी चाहिए, बल्कि समझदारी और मेहनत से काम लेना चाहिए।"*
> *"In difficult times, one should not give up — use wisdom and hard work instead."*

---

## Story

In a small village lived a hardworking farmer named **Ramlal**.  
One year, a severe drought struck. Other farmers gave up — but Ramlal refused to surrender.  
He dug small water-conservation ponds, planted drought-resistant crops, and kept working.  
While every other field dried up, **Ramlal's fields stayed green**.  
His harvest was abundant, and the whole village learned from his example.

---

## Project Structure

```
VIDEO-PROJECT/
├── main.py                  # Entry point — run this to generate the film
├── requirements.txt         # Python dependencies
├── src/
│   ├── config.py            # Video dimensions, colour palette, scene timings
│   ├── story.py             # Hindi narrations, subtitles, scene metadata
│   ├── font_loader.py       # Downloads Noto Sans Devanagari font
│   ├── draw_utils.py        # Drawing primitives (sky, terrain, crops, clouds …)
│   ├── characters.py        # Ramlal & villager character renderers
│   ├── scene_renderer.py    # All 11 animated scene renderers
│   ├── audio_generator.py   # Hindi TTS via gTTS (with silence fallback)
│   └── video_composer.py    # MoviePy composition & MP4 export
├── assets/
│   ├── fonts/               # Auto-downloaded Devanagari fonts
│   └── audio/               # Auto-generated narration mp3s
└── output/
    └── ramlal_ki_kahani.mp4 # ← Final film (generated)
```

---

## Scenes

| # | Scene ID             | Duration | Description                                |
|---|----------------------|----------|--------------------------------------------|
| 1 | `title`              | 6 s      | Title card — night sky fading to dawn      |
| 2 | `village_intro`      | 11 s     | Dawn village — Ramlal walks to his field   |
| 3 | `ramlal_working`     | 9 s      | Morning field — Ramlal hoeing his crops    |
| 4 | `drought`            | 11 s     | Harsh drought sky — cracked earth          |
| 5 | `ramlal_determined`  | 7 s      | Close-up: Ramlal stands firm — "हार नहीं!" |
| 6 | `new_techniques`     | 11 s     | Ramlal digs water ponds, plants new crops  |
| 7 | `green_contrast`     | 9 s      | Split: Ramlal's green field vs dry fields  |
| 8 | `harvest`            | 9 s      | Golden harvest — cart full of produce      |
| 9 | `villagers_learning` | 9 s      | Villagers gather to learn from Ramlal      |
|10 | `moral`              | 10 s     | Sunset — moral of the story                |
|11 | `end_card`           | 6 s      | Star-lit night — "समाप्त / The End"         |

**Total runtime ≈ 98 seconds**

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the film generator
python main.py
```

The script will:
1. Download **Noto Sans Devanagari** fonts automatically
2. Generate **Hindi narration audio** via Google TTS (requires internet; silently falls back to no audio if unavailable)
3. Render all **11 animated scenes** frame-by-frame
4. Export **`output/ramlal_ki_kahani.mp4`**

---

## Technical Details

| Property      | Value                   |
|---------------|-------------------------|
| Resolution    | 1280 × 720 (720p HD)    |
| Aspect ratio  | 2.35 : 1 (letterboxed)  |
| Frame rate    | 24 fps                  |
| Codec         | H.264 / AAC             |
| Language      | Hindi (हिन्दी)           |
| Visual style  | Layered silhouette art  |
| Animation     | Parametric (PIL + NumPy)|

---

## Dependencies

| Package    | Purpose                        |
|------------|--------------------------------|
| `moviepy`  | Video composition & MP4 export |
| `Pillow`   | Frame-by-frame scene drawing   |
| `numpy`    | Fast pixel / gradient maths    |
| `gTTS`     | Hindi text-to-speech           |
| `requests` | Font auto-download             |