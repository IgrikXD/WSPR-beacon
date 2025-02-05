from dataclasses import dataclass
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