#!/usr/bin/env python3
"""
XHS Carousel Renderer — self-contained script.

Renders a Markdown file with YAML front matter into XHS-format
carousel PNGs using Playwright Chromium screenshots.

Architecture adapted from Auto-Redbook-Skills, with:
- Local themes/ directory (not /tmp/)
- Pygments syntax highlighting via codehilite
- 3:5 aspect ratio (1440x2400) for XHS carousel

Usage:
    uv run --python 3.12 --with markdown --with pyyaml \
        --with playwright --with pygments \
        python render_xhs.py <markdown_file> [options]

Options:
    -t, --theme     Theme name (looks for themes/<name>.css)
    -o, --output-dir  Output directory for PNGs
    -w, --width     Card width in px (default 1440)
    --height        Card height in px (default 2400)
    --dpr           Device pixel ratio (default 2)
"""

import argparse
import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import List

try:
    import markdown
    import yaml
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"Missing dependency: {e}")
    print(
        "Install: uv run --python 3.12 --with markdown --with pyyaml "
        "--with playwright --with pygments python -m playwright install chromium"
    )
    sys.exit(1)


# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
THEMES_DIR = SCRIPT_DIR / "themes"

# ── Defaults (3:5 ratio for XHS) ──────────────────────────────────
DEFAULT_WIDTH = 1440
DEFAULT_HEIGHT = 2400
DEFAULT_DPR = 2


# ── Markdown parsing ──────────────────────────────────────────────

def parse_markdown_file(file_path: str) -> dict:
    """Parse a Markdown file, extracting YAML front matter and body."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    yaml_match = re.match(yaml_pattern, content, re.DOTALL)

    metadata = {}
    body = content

    if yaml_match:
        try:
            metadata = yaml.safe_load(yaml_match.group(1)) or {}
        except yaml.YAMLError:
            metadata = {}
        body = content[yaml_match.end():]

    return {"metadata": metadata, "body": body.strip()}


def split_pages(body: str) -> List[str]:
    """Split body on --- separators into page contents."""
    parts = re.split(r"\n---+\n", body)
    return [p.strip() for p in parts if p.strip()]


def md_to_html(md_content: str) -> str:
    """Convert Markdown to HTML with tag extraction and syntax highlighting."""
    # Extract trailing #tags (XHS-style hashtags)
    tags_pattern = r"((?:#[\w\u4e00-\u9fa5]+\s*)+)$"
    tags_match = re.search(tags_pattern, md_content, re.MULTILINE)
    tags_html = ""

    if tags_match:
        tags_str = tags_match.group(1)
        md_content = md_content[: tags_match.start()].strip()
        tags = re.findall(r"#([\w\u4e00-\u9fa5]+)", tags_str)
        if tags:
            tags_html = '<div class="tags-container">'
            for tag in tags:
                tags_html += f'<span class="tag">#{tag}</span>'
            tags_html += "</div>"

    html = markdown.markdown(
        md_content,
        extensions=["extra", "codehilite", "tables", "nl2br"],
        extension_configs={
            "codehilite": {
                "guess_lang": True,
                "css_class": "codehilite",
                "noclasses": False,
            }
        },
    )

    return html + tags_html


# ── Theme loading ─────────────────────────────────────────────────

def load_theme_css(theme: str) -> str:
    """Load CSS from themes/<theme>.css, falling back to default.css."""
    theme_file = THEMES_DIR / f"{theme}.css"
    if theme_file.exists():
        with open(theme_file, "r", encoding="utf-8") as f:
            return f.read()

    default_file = THEMES_DIR / "default.css"
    if default_file.exists():
        with open(default_file, "r", encoding="utf-8") as f:
            return f.read()

    print(f"  Warning: no theme file found for '{theme}', using empty CSS")
    return ""


# ── Cover card backgrounds per theme ─────────────────────────────

COVER_BACKGROUNDS = {
    "notion-tech": "linear-gradient(160deg, #EEF2FF 0%, #DBEAFE 40%, #E0E7FF 100%)",
    "professional": "linear-gradient(180deg, #2563EB 0%, #3B82F6 100%)",
    "default": "linear-gradient(180deg, #f3f3f3 0%, #f9f9f9 100%)",
}

COVER_TITLE_GRADIENTS = {
    "notion-tech": "linear-gradient(180deg, #111827 0%, #1E40AF 100%)",
    "professional": "linear-gradient(180deg, #1E3A8A 0%, #2563EB 100%)",
    "default": "linear-gradient(180deg, #111827 0%, #4B5563 100%)",
}

CARD_OUTER_BACKGROUNDS = {
    "notion-tech": "#F0F2F5",
    "professional": "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)",
    "default": "linear-gradient(180deg, #f3f3f3 0%, #f9f9f9 100%)",
}


# ── HTML generators ───────────────────────────────────────────────

def generate_cover_html(metadata: dict, theme: str,
                        width: int, height: int) -> str:
    """Generate the cover (page 1) HTML."""
    emoji = metadata.get("emoji", "📝")
    title = metadata.get("title", "标题")
    subtitle = metadata.get("subtitle", "")

    # Dynamic title sizing
    title_len = len(title)
    if title_len <= 6:
        title_size = int(width * 0.14)
    elif title_len <= 10:
        title_size = int(width * 0.12)
    elif title_len <= 18:
        title_size = int(width * 0.09)
    elif title_len <= 30:
        title_size = int(width * 0.07)
    else:
        title_size = int(width * 0.055)

    bg = COVER_BACKGROUNDS.get(theme, COVER_BACKGROUNDS["default"])
    title_bg = COVER_TITLE_GRADIENTS.get(theme, COVER_TITLE_GRADIENTS["default"])

    # Accent stripe color
    accent_stripe = "#4F46E5" if theme == "notion-tech" else "#2563EB"

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width={width}, height={height}">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Noto Sans SC', 'PingFang SC', 'SF Pro Display', -apple-system, sans-serif;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
}}
.cover-container {{
    width: {width}px;
    height: {height}px;
    background: {bg};
    position: relative;
    overflow: hidden;
}}
/* Subtle accent stripe at top */
.cover-container::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 8px;
    background: {accent_stripe};
}}
.cover-inner {{
    position: absolute;
    width: {int(width * 0.88)}px;
    height: {int(height * 0.91)}px;
    left: {int(width * 0.06)}px;
    top: {int(height * 0.045)}px;
    background: #FFFFFF;
    border-radius: 28px;
    display: flex;
    flex-direction: column;
    padding: {int(width * 0.074)}px {int(width * 0.079)}px;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
}}
.cover-emoji {{
    font-size: {int(width * 0.089)}px;
    line-height: 1.2;
    margin-bottom: {int(height * 0.035)}px;
}}
.cover-title {{
    font-weight: 900;
    font-size: {title_size}px;
    line-height: 1.35;
    background: {title_bg};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    flex: 1;
    display: flex;
    align-items: flex-start;
    word-break: break-word;
    letter-spacing: -0.02em;
}}
.cover-subtitle {{
    font-weight: 400;
    font-size: {int(width * 0.05)}px;
    line-height: 1.5;
    color: #6B7280;
    margin-top: auto;
    padding-top: 24px;
    border-top: 2px solid #E5E7EB;
}}
</style>
</head>
<body>
<div class="cover-container">
    <div class="cover-inner">
        <div class="cover-emoji">{emoji}</div>
        <div class="cover-title">{title}</div>
        <div class="cover-subtitle">{subtitle}</div>
    </div>
</div>
</body>
</html>'''


def generate_card_html(content: str, theme: str,
                       page_num: int, total_pages: int,
                       width: int, height: int) -> str:
    """Generate an inner content card HTML page."""
    html_content = md_to_html(content)
    theme_css = load_theme_css(theme)

    page_text = f"{page_num}/{total_pages}" if total_pages > 1 else ""
    outer_bg = CARD_OUTER_BACKGROUNDS.get(theme, CARD_OUTER_BACKGROUNDS["default"])

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width={width}">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Noto Sans SC', 'PingFang SC', 'SF Pro Display', -apple-system, sans-serif;
    width: {width}px;
    overflow: hidden;
    background: transparent;
}}
.card-container {{
    width: {width}px;
    min-height: {height}px;
    background: {outer_bg};
    position: relative;
    padding: 50px;
    overflow: hidden;
}}
.card-inner {{
    background: rgba(255, 255, 255, 0.97);
    border-radius: 24px;
    padding: 72px;
    min-height: calc({height}px - 100px);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}}
.card-content {{
    line-height: 1.8;
}}
.card-content :not(pre) > code {{
    overflow-wrap: anywhere;
    word-break: break-word;
}}

/* ── Theme CSS injected below ── */
{theme_css}

/* ── Page number ── */
.page-number {{
    position: absolute;
    bottom: 72px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 32px;
    color: #9CA3AF;
    font-weight: 500;
    letter-spacing: 2px;
}}
</style>
</head>
<body>
<div class="card-container">
    <div class="card-inner">
        <div class="card-content">{html_content}</div>
    </div>
    <div class="page-number">{page_text}</div>
</div>
</body>
</html>'''


# ── Rendering engine ──────────────────────────────────────────────

async def render_html_to_png(html: str, output_path: str,
                             width: int, height: int, dpr: int) -> int:
    """Render HTML string to a PNG file via Playwright. Returns actual height."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=dpr,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html)
            temp_path = f.name

        try:
            await page.goto(f"file://{temp_path}")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(500)  # font loading

            # Measure actual content height
            actual_height = await page.evaluate("""() => {
                const c = document.querySelector('.card-container')
                    || document.querySelector('.cover-container');
                return c ? c.scrollHeight : document.body.scrollHeight;
            }""")
            # Fit to content: use actual height, not fixed canvas
            # XHS allows variable height images in carousels
            actual_height = max(actual_height, width)  # min 1:1 ratio

            await page.screenshot(
                path=output_path,
                clip={"x": 0, "y": 0, "width": width, "height": actual_height},
                type="png",
            )

            print(f"  -> {Path(output_path).name}  ({width}x{actual_height})")
            return actual_height

        finally:
            os.unlink(temp_path)
            await browser.close()


# ── Main pipeline ─────────────────────────────────────────────────

async def render_carousel(md_file: str, output_dir: str,
                          theme: str, width: int, height: int,
                          dpr: int):
    """Full pipeline: parse markdown -> generate HTML -> screenshot PNGs."""
    print(f"\nRendering: {md_file}")
    print(f"  Theme: {theme}  |  Size: {width}x{height}  |  DPR: {dpr}")

    os.makedirs(output_dir, exist_ok=True)

    data = parse_markdown_file(md_file)
    metadata = data["metadata"]
    body = data["body"]

    pages = split_pages(body)
    total_pages = len(pages) + (1 if metadata.get("title") else 0)

    print(f"  Pages: {total_pages} ({1 if metadata.get('title') else 0} cover + {len(pages)} content)")

    idx = 1

    # Cover
    if metadata.get("title") or metadata.get("emoji"):
        print(f"  Rendering cover...")
        cover_html = generate_cover_html(metadata, theme, width, height)
        cover_path = os.path.join(output_dir, f"{idx:02d}-cover.png")
        await render_html_to_png(cover_html, cover_path, width, height, dpr)
        idx += 1

    # Content cards
    for i, page_content in enumerate(pages, 1):
        page_num_display = i + (1 if metadata.get("title") else 0)
        print(f"  Rendering card {i}/{len(pages)}...")
        card_html = generate_card_html(
            page_content, theme,
            page_num_display, total_pages,
            width, height,
        )
        card_path = os.path.join(output_dir, f"{idx:02d}-card.png")
        await render_html_to_png(card_html, card_path, width, height, dpr)
        idx += 1

    print(f"\nDone. {idx - 1} images in {output_dir}")


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Render Markdown to XHS carousel PNGs",
    )
    parser.add_argument("markdown_file", help="Path to .md file")
    parser.add_argument(
        "-o", "--output-dir", default=os.getcwd(),
        help="Output directory (default: cwd)",
    )
    parser.add_argument(
        "-t", "--theme", default="notion-tech",
        help="Theme name (default: notion-tech)",
    )
    parser.add_argument(
        "-w", "--width", type=int, default=DEFAULT_WIDTH,
        help=f"Card width in px (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT,
        help=f"Card height in px (default: {DEFAULT_HEIGHT})",
    )
    parser.add_argument(
        "--dpr", type=int, default=DEFAULT_DPR,
        help=f"Device pixel ratio (default: {DEFAULT_DPR})",
    )

    args = parser.parse_args()

    if not os.path.exists(args.markdown_file):
        print(f"Error: file not found - {args.markdown_file}")
        sys.exit(1)

    asyncio.run(
        render_carousel(
            args.markdown_file,
            args.output_dir,
            theme=args.theme,
            width=args.width,
            height=args.height,
            dpr=args.dpr,
        )
    )


if __name__ == "__main__":
    main()
