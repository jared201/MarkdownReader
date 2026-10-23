"""PDF export using QWebEnginePage.printToPdf."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import QMarginsF, QObject, pyqtSignal
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtWebEngineCore import QWebEnginePage


def default_page_layout() -> QPageLayout:
    """A4 with ~15 mm margins."""
    return QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(15, 15, 15, 15),
        QPageLayout.Unit.Millimeter,
    )


class PdfExporter(QObject):
    """Wraps `QWebEnginePage.printToPdf` and reports completion via signals."""

    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._page: Optional[QWebEnginePage] = None
        self._output_path: Optional[Path] = None

    def export(
        self,
        page: QWebEnginePage,
        output_path: Path,
        page_layout: Optional[QPageLayout] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """Kick off the async PDF export."""
        self._page = page
        self._output_path = output_path
        layout = page_layout or default_page_layout()

        if on_finished is not None:
            # Use a one-shot connection for the caller.
            def _relay(success: bool, message: str) -> None:
                try:
                    on_finished(success, message)
                finally:
                    try:
                        self.finished.disconnect(_relay)
                    except TypeError:
                        pass

            self.finished.connect(_relay)

        # printToPdf(filePath, layout) is fire-and-forget; result is signalled
        # via QWebEnginePage.pdfPrintingFinished(filePath, success).
        try:
            page.pdfPrintingFinished.disconnect(self._on_pdf_finished)
        except TypeError:
            pass
        page.pdfPrintingFinished.connect(self._on_pdf_finished)
        page.printToPdf(str(output_path), layout)

    def _on_pdf_finished(self, file_path: str, success: bool) -> None:
        if success:
            self.finished.emit(True, f"PDF saved to {file_path}")
        else:
            self.finished.emit(False, f"Failed to write PDF: {file_path}")
