"""BeamCheck desktop application entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from beamcheck.gui.main_window import MainWindow
from beamcheck.utils.logging_config import configure_logging
from beamcheck.utils.i18n import LANGUAGES, translate


def main() -> int:
    log_path = configure_logging()
    logger = logging.getLogger("beamcheck")
    logger.info("BeamCheck starting; log=%s", log_path)
    app = QApplication(sys.argv)
    app.setApplicationName("BeamCheck")
    app.setOrganizationName("BeamCheck")
    language = str(QSettings("BeamCheck", "BeamCheck").value("language", "en"))
    if language not in LANGUAGES:
        language = "en"

    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, translate(language, "calculation_failed"), translate(language, "unexpected_error", error="logs/beamcheck.log"))

    sys.excepthook = handle_exception
    window = MainWindow()
    if "--smoke-test" in sys.argv:
        window.calculate()
        return 0 if window.current_result is not None else 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
