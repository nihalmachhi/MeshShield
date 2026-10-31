"""Capture dashboard screenshots and demo frames for the README.

The script is optional and never fabricates an image. If Playwright is not
installed it prints the exact commands needed and exits successfully, so CI and
contributors without a browser are unaffected.

Usage:
    python scripts/capture_screenshots.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS = PROJECT_ROOT / "docs" / "assets"
FRAMES = ASSETS / "frames"


def playwright_available() -> bool:
    """Return True when the optional browser automation dependency is importable."""
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return shutil.which("npx") is not None or shutil.which("playwright") is not None


def capture(base_url: str, widths: tuple[int, ...], frame_count: int = 12) -> list[Path]:
    """Take a full-page screenshot and a scroll sequence, returning written paths."""
    from playwright.sync_api import sync_playwright

    ASSETS.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page(viewport={"width": max(widths), "height": 960})
        page.goto(base_url, wait_until="networkidle")

        dashboard = ASSETS / "dashboard.png"
        page.screenshot(path=str(dashboard), full_page=True)
        written.append(dashboard)

        page.set_viewport_size({"width": 1440, "height": 900})
        for step in range(frame_count):
            page.mouse.wheel(0, 180)
            frame = FRAMES / f"frame-{step:02d}.png"
            page.screenshot(path=str(frame))
            written.append(frame)

        # A narrow viewport guards against layout regressions at the low end.
        page.set_viewport_size({"width": min(widths), "height": 900})
        page.goto(base_url, wait_until="networkidle")
        narrow = ASSETS / "dashboard-320.png"
        page.screenshot(path=str(narrow), full_page=True)
        written.append(narrow)
        browser.close()
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--widths", type=int, nargs="+", default=(320, 1440))
    parser.add_argument("--frames", type=int, default=12)
    args = parser.parse_args()

    if not playwright_available():
        print("Playwright is not installed, so no screenshots were captured.")
        print("Install it with:")
        print("  python -m pip install playwright")
        print("  python -m playwright install chromium")
        print("Then start the app (`meshshield serve`) and re-run this script.")
        print("The README keeps a clearly marked TODO until a real image exists.")
        return 0

    if not (PROJECT_ROOT / "site" / "dist" / "index.html").exists():
        print("site/dist is missing. Build the site first:")
        print("  npm --prefix site ci && npm --prefix site run build")
        return 1

    written = capture(args.base_url, tuple(args.widths), args.frames)
    print(f"Wrote {len(written)} files under {ASSETS}.")
    print("Assemble the GIF with:")
    print(
        "  ffmpeg -framerate 4 -i docs/assets/frames/frame-%02d.png "
        "-vf scale=720:-1 docs/assets/demo.gif"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
