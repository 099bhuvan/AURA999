"""AURA — Pure Python AI Personal Assistant.

Entry point for launching the desktop application.
"""

import sys
import os
from pathlib import Path

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.config import config
from app.ui.main_window import MainWindow


def main():
    # Setup application attributes
    QApplication.setApplicationName("AURA")
    QApplication.setApplicationDisplayName(f"{config.assistant_name} — AI Personal Assistant")
    QApplication.setOrganizationName("AURA-AI")

    app = QApplication(sys.argv)
    
    # Set default modern typography
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Instantiate and show main command center window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
