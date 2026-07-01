from abc import ABC, abstractmethod


class BaseTransport(ABC):
    """
    Abstract base class for different transport implementations (Serial, WebSocket, etc.).
    """
    def __init__(self, device):
        """
        Initializes the transport with a reference to the Device instance.
        """
        self._device = device

    @abstractmethod
    async def connect(self):
        """
        Attempts to establish a connection with the device.
        """
        raise NotImplementedError

    @abstractmethod
    def send(self, message: str):
        """
        Sends a message string via the transport.
        """
        raise NotImplementedError
