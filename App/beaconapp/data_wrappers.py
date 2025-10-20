from dataclasses import dataclass, asdict
from enum import Enum


class Band(Enum):
    BAND_2200M = 2200
    BAND_600M = 600
    BAND_160M = 160
    BAND_80M = 80
    BAND_60M = 60
    BAND_40M = 40
    BAND_30M = 30
    BAND_20M = 20
    BAND_17M = 17
    BAND_15M = 15
    BAND_12M = 12
    BAND_10M = 10
    BAND_6M = 6
    BAND_4M = 4
    BAND_2M = 2


class CalibrationType(Enum):
    AUTO = "auto"
    MANUAL = "manual"


class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAIL = "fail"


class TransmitEvery(Enum):
    MINUTES_60 = 60
    MINUTES_30 = 30
    MINUTES_10 = 10
    MINUTES_2 = 2


class TXMode(Enum):
    WSPR = 1


@dataclass
class ActiveTXMode:
    tx_mode: TXMode = None
    tx_call: str = None
    qth_locator: str = None
    output_power: int = None
    transmit_every: TransmitEvery = None
    active_band: Band = None

    def clear(self):
        self.__init__()

    def to_json(self):
        data = asdict(self)

        data["tx_mode"] = getattr(self.tx_mode, "value", None)
        data["transmit_every"] = getattr(self.transmit_every, "value", None)
        data["active_band"] = getattr(self.active_band, "value", None)

        return data

    @classmethod
    def from_json(cls, json_data):
        if not json_data:
            return cls()

        json_data["tx_mode"] = TXMode(json_data["tx_mode"]) if (
            json_data.get("tx_mode") is not None) else None
        json_data["transmit_every"] = TransmitEvery(json_data.get("transmit_every")) if (
            json_data.get("transmit_every") is not None) else None
        json_data["active_band"] = Band(json_data.get("active_band")) if (
            json_data.get("active_band") is not None) else None

        return cls(**json_data)


@dataclass
class WiFiCredentials:
    ssid: str = None
    password: str = None

    def to_json(self) -> dict:
        return asdict(self)


@dataclass
class WiFiData:
    ssid: str = None
    password: str = None
    connect_at_startup: bool = False

    @classmethod
    def from_json(cls, json_data):
        return cls(**json_data)
