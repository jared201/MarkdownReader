"""Application bootstrap: creates QApplication and MainWindow."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from markdown_reader.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Markdown Reader")
    app.setOrganizationName("MarkdownReader")

    window = MainWindow()
    window.show()

    # Optional CLI argument: path to a .md file
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1])
        if candidate.exists() and candidate.is_file():
            window.open_file(candidate)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
