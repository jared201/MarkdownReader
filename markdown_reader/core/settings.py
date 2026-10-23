"""Thin wrapper around QSettings for recent files, theme, and geometry."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QByteArray, QSettings

_MAX_RECENT = 10


class SettingsStore:
    """Persist app preferences via QSettings."""

    def __init__(self) -> None:
        self._settings = QSettings("MarkdownReader", "MarkdownReader")

    # -- Recent files -------------------------------------------------
    def recent_files(self) -> List[Path]:
        raw = self._settings.value("recent/files", [], type=list) or []
        result: List[Path] = []
        for item in raw:
            try:
                p = Path(str(item))
            except (TypeError, ValueError):
                continue
            if p.exists():
                result.append(p)
        return result

    def add_recent_file(self, path: Path) -> None:
        path_str = str(path.resolve())
        existing = [str(p) for p in self.recent_files() if str(p.resolve()) != path_str]
        existing.insert(0, path_str)
        self._settings.setValue("recent/files", existing[:_MAX_RECENT])

    # -- Theme --------------------------------------------------------
    def theme(self) -> str:
        return str(self._settings.value("view/theme", "light"))

    def set_theme(self, theme: str) -> None:
        self._settings.setValue("view/theme", theme)

    # -- Geometry -----------------------------------------------------
    def geometry(self) -> Optional[QByteArray]:
        value = self._settings.value("window/geometry")
        if isinstance(value, QByteArray) and not value.isEmpty():
            return value
        return None

    def set_geometry(self, data: QByteArray) -> None:
        self._settings.setValue("window/geometry", data)
