import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_sample_data(filename: str) -> Dict[str, Any]:
    """
    Load sample data from a JSON file.

    Args:
        filename: The name of the file to load

    Returns:
        The loaded data
    """
    try:
        file_path = Path(__file__).parent.parent.parent.parent / filename
        if not file_path.exists():
            # Try to find it in the current directory
            file_path = Path(os.getcwd()) / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Could not find sample data file: {filename}")

        with open(file_path, "r") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error loading sample data from {filename}: {e!s}")
        raise


def set_log_level(log_level: str = "info") -> None:
    """
    Set the log level for the application.

    Args:
        log_level: The log level to use (debug, info, warning, error, critical)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Set the level for application loggers
    logging.getLogger("eyos").setLevel(numeric_level)

    # Set the level for web framework loggers
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("fastapi").setLevel(numeric_level)

    # Set a higher level for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_level: The log level to use
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set the level for specific loggers
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("fastapi").setLevel(numeric_level)

    # Set a higher level for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)


def format_currency(amount: float, currency: str = "GBP") -> str:
    """
    Format a currency amount.

    Args:
        amount: The amount to format
        currency: The currency code

    Returns:
        The formatted amount
    """
    currency_symbols = {
        "GBP": "£",
        "USD": "$",
        "EUR": "€",
    }

    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"
