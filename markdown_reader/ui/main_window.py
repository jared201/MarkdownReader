"""Main application window."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from markdown_reader.core.file_watcher import DebouncedFileWatcher
from markdown_reader.core.pdf_exporter import PdfExporter
from markdown_reader.core.renderer import MarkdownRenderer, Theme
from markdown_reader.core.settings import SettingsStore


class MainWindow(QMainWindow):
    """Main window hosting the Markdown preview."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Markdown Reader")
        self.resize(1000, 720)
        self.setAcceptDrops(True)

        self._settings = SettingsStore()
        self._current_file: Optional[Path] = None
        initial_theme: Theme = "dark" if self._settings.theme() == "dark" else "light"
        self._renderer = MarkdownRenderer(theme=initial_theme)
        self._pdf_exporter = PdfExporter(self)

        self._watcher = DebouncedFileWatcher(parent=self)
        self._watcher.fileChanged.connect(self._on_file_changed)

        self._web_view = QWebEngineView(self)
        self.setCentralWidget(self._web_view)

        self._export_pdf_action: Optional[QAction] = None
        self._print_action: Optional[QAction] = None
        self._recent_menu = None  # populated in _build_menu

        self._build_menu()
        self._update_document_actions()
        self._refresh_recent_menu()

        geom = self._settings.geometry()
        if geom is not None:
            self.restoreGeometry(geom)

        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    # Menu construction
    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        self._export_pdf_action = QAction("Export as &PDF...", self)
        self._export_pdf_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        self._export_pdf_action.triggered.connect(self._on_export_pdf)
        file_menu.addAction(self._export_pdf_action)

        self._print_action = QAction("&Print...", self)
        self._print_action.setShortcut(QKeySequence.StandardKey.Print)
        self._print_action.triggered.connect(self._on_print)
        file_menu.addAction(self._print_action)

        file_menu.addSeparator()

        self._recent_menu = file_menu.addMenu("&Recent")

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("&View")
        light_action = QAction("Theme: &Light", self)
        light_action.triggered.connect(lambda: self.set_theme("light"))
        view_menu.addAction(light_action)
        dark_action = QAction("Theme: &Dark", self)
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        view_menu.addAction(dark_action)

        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def open_file(self, path: Path) -> None:
        """Load, render, and display a Markdown file."""
        try:
            md_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Open failed", f"Could not read file:\n{exc}")
            return

        self._current_file = path
        html = self._renderer.render(md_text, base_dir=path.parent)
        base_url = QUrl.fromLocalFile(str(path.parent) + "/")
        self._web_view.setHtml(html, base_url)

        self._watcher.watch(path)
        self._settings.add_recent_file(path)
        self._refresh_recent_menu()

        self.setWindowTitle(f"{path.name} - Markdown Reader")
        self.statusBar().showMessage(f"Opened {path}")
        self._update_document_actions()

    def set_theme(self, theme: Theme) -> None:
        self._renderer.set_theme(theme)
        self._settings.set_theme(theme)
        if self._current_file is not None:
            self.open_file(self._current_file)

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802
        self._settings.set_geometry(self.saveGeometry())
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # File watcher
    # ------------------------------------------------------------------
    def _on_file_changed(self, path_str: str) -> None:
        path = Path(path_str)
        if path.exists() and self._current_file is not None:
            self.open_file(path)

    # ------------------------------------------------------------------
    # Recent files menu
    # ------------------------------------------------------------------
    def _refresh_recent_menu(self) -> None:
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        recents = self._settings.recent_files()
        if not recents:
            empty = QAction("(empty)", self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
            return
        for path in recents:
            action = QAction(str(path), self)
            action.triggered.connect(lambda _checked=False, p=path: self.open_file(p))
            self._recent_menu.addAction(action)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in {".md", ".markdown", ".txt"}:
                    self.open_file(path)
                    break

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    def _on_open(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)",
        )
        if path_str:
            self.open_file(Path(path_str))

    def _on_export_pdf(self) -> None:
        if self._current_file is None:
            return
        default_name = self._current_file.with_suffix(".pdf").name
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export as PDF",
            default_name,
            "PDF Files (*.pdf)",
        )
        if not path_str:
            return
        out_path = Path(path_str)
        self.statusBar().showMessage(f"Exporting PDF to {out_path}...")

        def _done(success: bool, message: str) -> None:
            self.statusBar().showMessage(message, 5000)
            if not success:
                QMessageBox.warning(self, "Export PDF", message)

        self._pdf_exporter.export(self._web_view.page(), out_path, on_finished=_done)

    def _on_print(self) -> None:
        if self._current_file is None:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        def _print_done(success: bool) -> None:
            if success:
                self.statusBar().showMessage("Print job sent", 5000)
            else:
                QMessageBox.warning(self, "Print", "Printing failed.")

        self._web_view.page().print(printer, _print_done)

    def _update_document_actions(self) -> None:
        has_doc = self._current_file is not None
        if self._export_pdf_action is not None:
            self._export_pdf_action.setEnabled(has_doc)
        if self._print_action is not None:
            self._print_action.setEnabled(has_doc)

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "About Markdown Reader",
            "Markdown Reader\nA lightweight PyQt6 Markdown viewer with PDF export.",
        )
