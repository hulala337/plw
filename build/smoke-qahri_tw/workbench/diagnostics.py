"""Bounded local diagnostic logs; never log input content or API payloads."""

import logging
from logging.handlers import RotatingFileHandler


def configure_logging(data_dir):
    logger = logging.getLogger("pelican")
    if not logger.handlers:
        handler = RotatingFileHandler(
            data_dir / "pelican.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def configure_console():
    import sys

    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def install_exception_hooks(logger):
    import sys
    import threading

    def main_hook(kind, value, traceback):
        logger.critical(
            "Unhandled application exception", exc_info=(kind, value, traceback)
        )
        sys.__excepthook__(kind, value, traceback)

    def thread_hook(args):
        logger.error(
            "Background thread failed: %s",
            args.thread.name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = main_hook
    threading.excepthook = thread_hook
