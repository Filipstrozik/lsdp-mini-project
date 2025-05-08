import logging
import sys
from inference_service.config.config import ModelConfig


def setup_logging():
    """Set up logging configuration"""
    config = ModelConfig()

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(config.LOG_LEVEL)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(config.LOG_LEVEL)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger
