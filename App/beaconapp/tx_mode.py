from dataclasses import asdict, dataclass
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