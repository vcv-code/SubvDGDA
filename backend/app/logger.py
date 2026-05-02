import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging() -> logging.Logger:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("bdns")
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers si se llama más de una vez (recarga en dev)
    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Ficheros de log solo si LOG_DIR está configurado (entorno Docker)
    log_dir_env = os.getenv("LOG_DIR")
    if log_dir_env:
        log_dir = Path(log_dir_env)
        log_dir.mkdir(parents=True, exist_ok=True)

        access_handler = logging.handlers.RotatingFileHandler(
            log_dir / "access.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        access_handler.setFormatter(formatter)
        logger.addHandler(access_handler)

        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    return logger
