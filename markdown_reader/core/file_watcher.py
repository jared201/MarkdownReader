"""File watcher with debounce on top of QFileSystemWatcher."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QFileSystemWatcher, QObject, QTimer, pyqtSignal


class DebouncedFileWatcher(QObject):
    """Watch a single file and emit `fileChanged` after debounce_ms of quiet."""

    fileChanged = pyqtSignal(str)

    def __init__(self, debounce_ms: int = 200, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_raw_change)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._emit)

        self._current: Optional[str] = None

    def watch(self, path: Path) -> None:
        """Start watching a single file, replacing any previous target."""
        if self._current is not None:
            self._watcher.removePath(self._current)
        self._current = str(path)
        self._watcher.addPath(self._current)

    def stop(self) -> None:
        if self._current is not None:
            self._watcher.removePath(self._current)
            self._current = None

    def _on_raw_change(self, path: str) -> None:
        # Some editors replace the file, which drops the watch; re-add.
        if path not in self._watcher.files() and Path(path).exists():
            self._watcher.addPath(path)
        self._timer.start()

    def _emit(self) -> None:
        if self._current is not None:
            self.fileChanged.emit(self._current)
