# infrastructure/logging/__init__.py
from .logging.logger import get_logger, setup_logging

__all__ = ['setup_logging', 'get_logger']