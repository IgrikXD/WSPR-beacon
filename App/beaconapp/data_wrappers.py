from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


@dataclass
class WiFiCredentials:
    ssid: str = None
    password: str = None

    def to_json(self) -> dict:
        return asdict(self)


class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAIL = "fail"


@dataclass
class WiFiData:
    ssid: str = None
    password: str = None
    status: ConnectionStatus = None
    connect_at_startup: bool = False

    @classmethod
    def from_json(cls, json_data):
        json_data = json_data.copy()
        json_data["status"] = ConnectionStatus(json_data["status"].lower())
        return cls(**json_data)
