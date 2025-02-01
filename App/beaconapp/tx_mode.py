from enum import Enum


class TransmissionMode(Enum):
    WSPR = 1


class ActiveTXMode:
    def __init__(self, transmission_mode=None, tx_call=None, qth_locator=None,
                 output_power=None, transmit_every=None, active_band=None):
        self.set(transmission_mode, tx_call, qth_locator, output_power, transmit_every, active_band)

    def clear(self):
        """Reset all attributes to None."""
        self.set(None, None, None, None, None, None)

    def set(self, transmission_mode=None, tx_call=None, qth_locator=None,
            output_power=None, transmit_every=None, active_band=None):
        """Set all attributes at once."""
        self.transmission_mode = transmission_mode
        self.tx_call = tx_call
        self.qth_locator = qth_locator
        self.output_power = output_power
        self.transmit_every = transmit_every
        self.active_band = active_band
