"""Markdown to HTML rendering pipeline."""
from __future__ import annotations

import html
import zlib
from pathlib import Path
from typing import Literal

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

Theme = Literal["light", "dark"]

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _plantuml_encode(plantuml_text: str) -> str:
    """Encode PlantUML source to the format used by the PlantUML server."""
    compressed = zlib.compress(plantuml_text.encode("utf-8"))[2:-4]
    return _plantuml_encode_compressed(compressed)


def _plantuml_encode_compressed(compressed: bytes) -> str:
    """Base64-like encoding using PlantUML's 6-bit alphabet."""
    alphabet = (
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    )
    res = []
    for i in range(0, len(compressed), 3):
        if i + 2 == len(compressed):
            b1, b2 = compressed[i], compressed[i + 1]
            b3 = 0
            res.append(_encode6bit((b1 >> 2) & 0x3F))
            res.append(_encode6bit(((b1 & 0x3) << 4) | (b2 >> 4)))
            res.append(_encode6bit(((b2 & 0xF) << 2) | (b3 >> 6)))
            res.append(_encode6bit(b3 & 0x3F))
        elif i + 1 == len(compressed):
            b1 = compressed[i]
            b2 = b3 = 0
            res.append(_encode6bit((b1 >> 2) & 0x3F))
            res.append(_encode6bit(((b1 & 0x3) << 4) | (b2 >> 4)))
            res.append(_encode6bit(((b2 & 0xF) << 2) | (b3 >> 6)))
            res.append(_encode6bit(b3 & 0x3F))
        else:
            b1, b2, b3 = compressed[i], compressed[i + 1], compressed[i + 2]
            res.append(_encode6bit((b1 >> 2) & 0x3F))
            res.append(_encode6bit(((b1 & 0x3) << 4) | (b2 >> 4)))
            res.append(_encode6bit(((b2 & 0xF) << 2) | (b3 >> 6)))
            res.append(_encode6bit(b3 & 0x3F))
    return "".join(res)


def _encode6bit(b: int) -> str:
    if b < 10:
        return chr(48 + b)
    b -= 10
    if b < 26:
        return chr(65 + b)
    b -= 26
    if b < 26:
        return chr(97 + b)
    b -= 26
    if b == 0:
        return "-"
    if b == 1:
        return "_"
    return "?"


def _highlight(code: str, lang: str, _attrs: str) -> str:
    """Highlight a fenced code block using Pygments; returns HTML.
    Special-cases mermaid and plantuml for diagram rendering.
    """

    lang = (lang or "").lower()
    if lang == "mermaid":
        # Mermaid will be rendered client-side via JS
        # Escape HTML special chars so < > & etc. in diagram source don't break the outer HTML
        escaped = html.escape(code)
        return f'<div class="mermaid">{escaped}</div>'
    if lang == "plantuml":
        # Render via PlantUML server as SVG image (requires internet)
        try:
            # Auto-wrap with @startuml/@enduml if missing for reliable rendering
            src = code.strip()
            if not src.lower().startswith("@startuml"):
                src = "@startuml\n" + src + "\n@enduml"
            encoded = _plantuml_encode(src)
            url = f"https://www.plantuml.com/plantuml/svg/{encoded}"
            return f'<img src="{url}" class="plantuml" alt="PlantUML diagram" />'
        except Exception:  # noqa: BLE001
            escaped = html.escape(code)
            return f'<pre class="plantuml">{escaped}</pre>'
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except (ClassNotFound, Exception):  # noqa: BLE001
        # Fallback to plain preformatted block.
        return ""
    formatter = HtmlFormatter(nowrap=False, cssclass="highlight")
    return highlight(code, lexer, formatter)


class MarkdownRenderer:
    """Converts Markdown text to a full styled HTML document."""

    def __init__(self, theme: Theme = "light") -> None:
        self.theme: Theme = theme
        self._md = (
            MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True})
            .enable(["table", "strikethrough"])
            .use(anchors_plugin, permalink=False)
            .use(footnote_plugin)
            .use(tasklists_plugin, enabled=True)
        )
        self._md.options["highlight"] = _highlight

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme

    def render(self, md_text: str, base_dir: Path) -> str:
        """Return a full HTML document with theme CSS inlined."""
        body_html = self._md.render(md_text)
        screen_css = self._read_asset(f"screen-{self.theme}.css")
        pygments_style = "default" if self.theme == "light" else "monokai"
        pygments_css = HtmlFormatter(style=pygments_style).get_style_defs(".highlight")
        print_css = self._read_asset("print.css")

        base_uri = base_dir.resolve().as_uri() + "/"
        # Mermaid initialization script (local file + auto-render)
        # Use current theme for mermaid; run immediately (elements already parsed)
        m_theme = 'dark' if self.theme == 'dark' else 'default'
        mermaid_js = _SCRIPTS_DIR / "mermaid.min.js"
        mermaid_src = mermaid_js.as_uri() if mermaid_js.exists() else "https://cdn.jsdelivr.net/npm/mermaid@latest/dist/mermaid.min.js"
        mermaid_script = f"""
<script src="{mermaid_src}"></script>
<script>
  if (window.mermaid) {{
    mermaid.initialize({{ startOnLoad: true, theme: '{m_theme}', securityLevel: 'loose' }});
    mermaid.run();
  }}
</script>
"""
        # Add minimal diagram CSS
        diagram_css = """
<style>
  div.mermaid, pre.mermaid, .plantuml { background: #fff; padding: 1em; border-radius: 6px; }
  .plantuml { max-width: 100%; height: auto; }
  @media (prefers-color-scheme: dark) {
    div.mermaid, pre.mermaid, .plantuml { background: #2d2d2d; }
  }
</style>
"""
        return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <base href=\"{base_uri}\">
  <title>Markdown Preview</title>
  <style>{screen_css}</style>
  <style>{pygments_css}</style>
  <style media=\"print\">{print_css}</style>
  {diagram_css}
</head>
<body class=\"markdown-body theme-{self.theme}\">
{body_html}
{mermaid_script}
</body>
</html>
"""

    @staticmethod
    def _read_asset(name: str) -> str:
        path = _ASSETS_DIR / name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
