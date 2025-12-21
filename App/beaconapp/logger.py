from colorama import Fore, Style

import logging
import sys

# Module-level logger
logger = logging.getLogger('beaconapp')

# Add handler only if not already present (prevents duplicate handlers on re-import)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG if ('--debug' in sys.argv) else logging.CRITICAL)


def log_error(message: str) -> None:
    """
    Logs an error message in red color.
    """
    logger.error(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")


def log_ok(message: str) -> None:
    """
    Logs a info message in green color.
    """
    logger.info(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")


def log_rx_message(message: str) -> None:
    """
    Logs an incoming message in magenta color.
    """
    logger.info(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")


def log_tx_message(message: str) -> None:
    """
    Logs a outgoing message in green color.
    """
    logger.info(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def log_warning(message: str) -> None:
    """
    Logs a warning message in yellow color.
    """
    logger.warning(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")
