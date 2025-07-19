"""Central logging setup so every module logs consistently to console + file."""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(log_file: str = "reserver.log", level: int = logging.INFO) -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = logging.FileHandler(Path(log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
