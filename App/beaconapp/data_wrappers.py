from dataclasses import dataclass, asdict
from enum import Enum


class TransmissionMode(Enum):
    WSPR = 1


@dataclass
class ActiveTXMode:
    transmission_mode: TransmissionMode = None
    tx_call: str = None
    qth_locator: str = None
    output_power: int = None
    transmit_every: str = None
    active_band: str = None

    def clear(self):
        self.__init__()

    def to_json(self):
        data = asdict(self)

        if self.transmission_mode is not None:
            data["transmission_mode"] = self.transmission_mode.name

        return data

    @classmethod
    def from_json(cls, json_data):
        if not json_data:
            return cls()

        mode = json_data.get("transmission_mode")
        if mode:
            json_data["transmission_mode"] = TransmissionMode[mode]

        return cls(**json_data)


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
