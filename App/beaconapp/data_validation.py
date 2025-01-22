import re

class DataValidation:
    @staticmethod
    def validate_tx_call_input(value):
        """
        Validate a transmission call input field.
        """
        return (len(value) <= 6) and (re.fullmatch(r"[A-Z0-9]*", value) is not None)

    @staticmethod
    def validate_qth_locator_input(value):
        """
        Validate a QTH locator input field.
        """
        return (len(value) <= 4) and (re.fullmatch(r"[A-Z]{0,2}\d{0,2}", value) is not None)

    @staticmethod
    def validate_output_power_input(value):
        """
        Validate an output power input field. Allows empty or digit values up to 2 characters.
        """
        return (not value) or (len(value) <= 2 and value.isdigit())

    @staticmethod
    def validate_cal_value_input(value):
        """
        Validate a calibration value input field. Allows optional sign and up to 4 digits.
        """
        return bool(re.fullmatch(r"-?\d{0,4}", value))

    @staticmethod
    def validate_cal_frequency_input(value):
        """
        Validate a calibration frequency input field. Allows floats with up to 3 decimals in the range 1.000 to 99.999.
        """
        return (not value) or (bool(re.fullmatch(r"^(\d+(\.\d{0,3})?)?$", value)) and (1.000 <= float(value) <= 99.999))
