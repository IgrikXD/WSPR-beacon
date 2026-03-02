from beaconapp.data_wrappers import Transport
from colorama import Fore, Style

import logging
import sys

# Module-level logger
logger = logging.getLogger('beaconapp')

# Add handler only if not already present (prevents duplicate handlers on re-import)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG if ('--debug' in sys.argv) else logging.CRITICAL)


def is_debug_mode() -> bool:
    """
    Returns True if the application was started with --debug flag.
    """
    return '--debug' in sys.argv


def log_error(message: str) -> None:
    """
    Logs an error message in red color.
    Args:
        message (str): The error message to log.
    """
    logger.error(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")


def log_ok(message: str) -> None:
    """
    Logs an info message in green color.
    Args:
        message (str): The info message to log.
    """
    logger.info(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")


def log_rx_message(message: str, transport: Transport) -> None:
    """
    Logs an incoming message in magenta color.
    Args:
        message (str): The incoming message to log.
        transport (Transport): The transport method used.
    """
    logger.info(f"{Fore.MAGENTA}[RX, ({transport.value})]: {message}{Style.RESET_ALL}")


def log_tx_message(message: str, transport: Transport) -> None:
    """
    Logs an outgoing message in green color.
    Args:
        message (str): The outgoing message to log.
        transport (Transport): The transport method used.
    """
    logger.info(f"{Fore.GREEN}[TX, ({transport.value})]: {message}{Style.RESET_ALL}")


def log_warning(message: str) -> None:
    """
    Logs an warning message in yellow color.
    Args:
        message (str): The warning message to log.
    """
    logger.warning(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")
