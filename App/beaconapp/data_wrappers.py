from dataclasses import dataclass, asdict
from enum import Enum


# General device status enums
class Status(Enum):
    CALIBRATED = "calibrated"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    INITIATED = "initiated"
    FAILED = "failed"


# ActiveTXMode related enums
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
        return {
            "tx_mode": self.tx_mode.value if self.tx_mode else None,
            "tx_call": self.tx_call,
            "qth_locator": self.qth_locator,
            "output_power": self.output_power,
            "transmit_every": self.transmit_every.value if self.transmit_every else None,
            "active_band": self.active_band.value if self.active_band else None,
        }

    @classmethod
    def from_json(cls, json_data):
        if not json_data:
            return cls()

        return cls(
            tx_mode=TXMode(json_data["tx_mode"]) if json_data.get(
                "tx_mode") is not None else None,
            tx_call=json_data.get("tx_call"),
            qth_locator=json_data.get("qth_locator"),
            output_power=json_data.get("output_power"),
            transmit_every=TransmitEvery(json_data["transmit_every"]) if json_data.get(
                "transmit_every") is not None else None,
            active_band=Band(json_data["active_band"]) if json_data.get(
                "active_band") is not None else None,
        )


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
