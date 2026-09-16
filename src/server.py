"""
Built-in HTTP server for browsing, streaming, and downloading generated videos.

Start with:
    python main.py --serve-only            # browse existing output/
    python main.py --idea "…" --serve      # generate then serve

Or directly:
    python -m src.server                   # default port 8080
    python -m src.server --port 9000
"""
from __future__ import annotations

import html
import http.server
import io
import mimetypes
import os
import socketserver
import threading
import urllib.parse
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# HTML templates
# ---------------------------------------------------------------------------

_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🎬 Animated Cinematic Video Generator</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0d0d1a;
      color: #e8e8f0;
      min-height: 100vh;
      padding: 2rem 1rem;
    }}
    header {{
      text-align: center;
      margin-bottom: 2.5rem;
    }}
    header h1 {{
      font-size: 2rem;
      background: linear-gradient(135deg, #f9c946 0%, #ff6b6b 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    header p {{
      color: #888;
      margin-top: 0.4rem;
      font-size: 0.95rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
      gap: 2rem;
      max-width: 1400px;
      margin: 0 auto;
    }}
    .card {{
      background: #161628;
      border: 1px solid #2a2a4a;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 16px 48px rgba(0,0,0,0.6);
    }}
    .card video {{
      width: 100%;
      display: block;
      background: #000;
      max-height: 360px;
    }}
    .card-body {{
      padding: 1.2rem 1.4rem;
    }}
    .card-title {{
      font-size: 1.05rem;
      font-weight: 600;
      color: #f0f0ff;
      word-break: break-all;
      margin-bottom: 0.5rem;
    }}
    .card-meta {{
      font-size: 0.82rem;
      color: #666;
      margin-bottom: 1rem;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.55rem 1.2rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      border: none;
      transition: opacity 0.15s;
    }}
    .btn:hover {{ opacity: 0.85; }}
    .btn-download {{
      background: linear-gradient(135deg, #f9c946 0%, #ff9a44 100%);
      color: #1a1a1a;
    }}
    .empty {{
      text-align: center;
      padding: 4rem 2rem;
      color: #555;
    }}
    .empty h2 {{ font-size: 1.4rem; margin-bottom: 0.8rem; color: #888; }}
    .empty code {{
      background: #1e1e38;
      color: #f9c946;
      padding: 0.2em 0.5em;
      border-radius: 4px;
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <header>
    <h1>🎬 Animated Cinematic Video Generator</h1>
    <p>Your generated films – stream or download below</p>
  </header>
  {body}
</body>
</html>
"""

_VIDEO_CARD = """\
<div class="card">
  <video controls preload="metadata" src="{url}"></video>
  <div class="card-body">
    <div class="card-title">{name}</div>
    <div class="card-meta">{size_mb:.1f} MB &nbsp;·&nbsp; {mtime}</div>
    <a class="btn btn-download" href="{url}" download="{name}">
      ⬇ Download
    </a>
  </div>
</div>
"""

_EMPTY_BODY = """\
<div class="empty">
  <h2>No videos found yet</h2>
  <p>Run the generator first:</p>
  <br>
  <code>python main.py --idea "Your story idea here"</code>
</div>
"""


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class _VideoHandler(http.server.BaseHTTPRequestHandler):
    """Serves the output directory with a styled HTML index and raw file download."""

    output_dir: Path  # set by factory

    # ------------------------------------------------------------------
    def log_message(self, fmt: str, *args) -> None:  # type: ignore[override]
        # Route to Python logger instead of stderr
        import logging
        logging.getLogger(__name__).info(fmt, *args)

    # ------------------------------------------------------------------
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path).lstrip("/")

        if path == "" or path == "index.html":
            self._serve_index()
        else:
            self._serve_file(path)

    # ------------------------------------------------------------------
    def _serve_index(self) -> None:
        mp4_files = sorted(
            self.output_dir.glob("*.mp4"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if mp4_files:
            cards = []
            for f in mp4_files:
                stat = f.stat()
                size_mb = stat.st_size / (1024 * 1024)
                import datetime
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                )
                cards.append(
                    _VIDEO_CARD.format(
                        url=f"/{urllib.parse.quote(f.name)}",
                        name=html.escape(f.name),
                        size_mb=size_mb,
                        mtime=mtime,
                    )
                )
            body = f'<div class="grid">{"".join(cards)}</div>'
        else:
            body = _EMPTY_BODY

        page = _PAGE_TEMPLATE.format(body=body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    # ------------------------------------------------------------------
    def _serve_file(self, relative_path: str) -> None:
        # Only serve files directly inside output_dir (no path traversal)
        target = (self.output_dir / relative_path).resolve()
        if not str(target).startswith(str(self.output_dir.resolve())):
            self._send_error(403, "Forbidden")
            return

        if not target.exists() or not target.is_file():
            self._send_error(404, "Not found")
            return

        mime, _ = mimetypes.guess_type(str(target))
        mime = mime or "application/octet-stream"
        file_size = target.stat().st_size

        # Support HTTP Range requests so browsers can seek within videos
        range_header = self.headers.get("Range")
        if range_header and mime.startswith("video/"):
            self._serve_range(target, file_size, mime, range_header)
        else:
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(file_size))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{urllib.parse.quote(target.name)}"',
            )
            self.end_headers()
            with open(target, "rb") as fh:
                self._copy(fh, self.wfile)

    # ------------------------------------------------------------------
    def _serve_range(
        self, target: Path, file_size: int, mime: str, range_header: str
    ) -> None:
        """Handle HTTP 206 partial content for video seeking."""
        try:
            unit, ranges = range_header.strip().split("=")
            start_str, end_str = ranges.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
        except (ValueError, AttributeError):
            self._send_error(416, "Invalid Range")
            return

        length = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(length))
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(target, "rb") as fh:
            fh.seek(start)
            remaining = length
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    # ------------------------------------------------------------------
    def _send_error(self, code: int, message: str) -> None:
        body = message.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ------------------------------------------------------------------
    @staticmethod
    def _copy(src: io.IOBase, dst) -> None:
        while True:
            buf = src.read(65536)
            if not buf:
                break
            dst.write(buf)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_handler(output_dir: Path):
    """Return a handler class bound to *output_dir*."""
    class BoundHandler(_VideoHandler):
        pass
    BoundHandler.output_dir = output_dir
    return BoundHandler


def start_server(
    output_dir: Path,
    port: int = 8080,
    open_browser: bool = True,
    block: bool = True,
) -> Optional[socketserver.TCPServer]:
    """
    Start the video download/preview server.

    Args:
        output_dir:    Directory containing the generated MP4 files.
        port:          TCP port to listen on (default 8080).
        open_browser:  Automatically open the browser after starting.
        block:         If True, block until KeyboardInterrupt. If False,
                       start in a background daemon thread and return the
                       server object.
    """
    import logging
    logger = logging.getLogger("video_project.server")

    handler = make_handler(output_dir.resolve())
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", port), handler)

    url = f"http://localhost:{port}"
    print(f"\n🌐  Video server running at:  {url}")
    print("    Press Ctrl+C to stop.\n")
    logger.info("Serving '%s' on port %d", output_dir, port)

    if open_browser:
        import webbrowser
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    if block:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n⏹  Server stopped.")
            server.server_close()
        return None
    else:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server


# ---------------------------------------------------------------------------
# Allow running as `python -m src.server`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from src.config import get_config

    p = argparse.ArgumentParser(description="Video preview & download server")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--no-browser", action="store_true")
    a = p.parse_args()

    cfg = get_config()
    start_server(cfg.output_dir, port=a.port, open_browser=not a.no_browser)
