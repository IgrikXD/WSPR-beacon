import pytest
from beaconapp.data_validation import DataValidation


# Test suite for validate_tx_call_input function
@pytest.mark.parametrize("input_value, expected_value", [
    ("", True),
    ("CALL1", True),
    ("ABCDEF", True),
    ("123456", True),
    ("ABCDE1", True),
    ("abcdef", False),    # Lowercase letters are not allowed
    ("ABCDEF1", False),   # 7 characters long - too long
    ("AB@12", False),     # Invalid character '@'
])
def test_validate_tx_call_input(input_value, expected_value):
    assert DataValidation.validate_tx_call_input(input_value) == expected_value


# Test suite for validate_qth_locator_input function
@pytest.mark.parametrize("input_value, expected_value", [
    ("", True),
    ("A", True),
    ("AB", True),
    ("A1", True),
    ("AB12", True),
    ("12", True),
    ("a1", False),    # Letters must be uppercase
    ("ABC", False),   # More than 2 letters
    ("A123", False),  # More than 2 digits after letters
    ("AB123", False),  # Too long and more than 2 digits
    ("A12B", False),  # Letter after digits is not allowed
    ("1234", False),  # More than 2 digits when no letters are present
])
def test_validate_qth_locator_input(input_value, expected_value):
    assert DataValidation.validate_qth_locator_input(input_value) == expected_value


# Test suite for validate_output_power_input function
@pytest.mark.parametrize("input_value, expected_value", [
    ("", True),   # Empty string is allowed
    ("0", True),
    ("1", True),
    ("12", True),
    ("99", True),
    ("123", False),  # More than 2 digits
    ("a", False),   # Not a digit
    ("1a", False),  # Mixed characters are not allowed
])
def test_validate_output_power_input(input_value, expected_value):
    assert DataValidation.validate_output_power_input(input_value) == expected_value


# Test suite for validate_cal_value_input function
@pytest.mark.parametrize("input_value, expected_value", [
    ("", True),       # Empty string is allowed
    ("-", True),      # Only a minus sign is allowed
    ("123", True),
    ("-123", True),
    ("9999", True),
    ("-9999", True),
    ("0", True),
    ("0001", True),
    ("-12345", False),  # More than 4 digits after the minus sign
    ("a", False),       # Invalid character
    ("+123", False),    # Only minus sign is allowed, plus is not permitted
    ("12-3", False),    # The sign must be at the beginning
])
def test_validate_cal_value_input(input_value, expected_value):
    assert DataValidation.validate_cal_value_input(input_value) == expected_value


# Test suite for validate_cal_frequency_input function
@pytest.mark.parametrize("input_value, expected_value", [
    ("", True),       # Empty string is allowed
    ("1", True),
    ("1.0", True),
    ("1.000", True),
    ("1.", True),     # Allowed: fractional part is missing
    ("50", True),
    ("50.123", True),
    ("99.999", True),
    ("99", True),
    ("10.5", True),
    ("10.500", True),
    ("1.0000", False),  # More than 3 decimal places
    ("0.999", False),   # Value less than 1.000
    ("100", False),     # Value greater than 99.999
    ("abc", False),     # Not a number
    ("1.1234", False),  # More than 3 decimal places
])
def test_validate_cal_frequency_input(input_value, expected_value):
    assert DataValidation.validate_cal_frequency_input(
        input_value) == expected_value
