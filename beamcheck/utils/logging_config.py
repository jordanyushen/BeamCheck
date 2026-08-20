"""Local rotating application log configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(base_directory: str | Path | None = None) -> Path:
    base = Path(base_directory) if base_directory else Path.cwd()
    log_directory = base / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "beamcheck.log"
    root = logging.getLogger("beamcheck")
    root.setLevel(logging.INFO)
    if not root.handlers:
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)
    return log_path
