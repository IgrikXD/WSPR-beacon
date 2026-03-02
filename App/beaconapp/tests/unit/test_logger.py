import logging
import pytest

from beaconapp.data_wrappers import Transport
from beaconapp.logger import log_error, log_ok, log_rx_message, log_tx_message, log_warning


@pytest.mark.unit
def test_log_error(caplog):

    with caplog.at_level(logging.ERROR, logger="beaconapp"):
        log_error("Test error message")

    assert any("[ERROR] Test error message" in record.message for record in caplog.records)


@pytest.mark.unit
def test_log_ok(caplog):

    with caplog.at_level(logging.INFO, logger="beaconapp"):
        log_ok("Test OK message")

    assert any("[OK] Test OK message" in record.message for record in caplog.records)


@pytest.mark.unit
def test_log_rx_message(caplog):

    with caplog.at_level(logging.INFO, logger="beaconapp"):
        log_rx_message("Test RX message", Transport.USB)

    assert any(f"[RX, ({Transport.USB.value})]: Test RX message" in record.message for record in caplog.records)


@pytest.mark.unit
def test_log_tx_message(caplog):

    with caplog.at_level(logging.INFO, logger="beaconapp"):
        log_tx_message("Test TX message", Transport.WIFI)

    assert any(f"[TX, ({Transport.WIFI.value})]: Test TX message" in record.message for record in caplog.records)


@pytest.mark.unit
def test_log_warning(caplog):

    with caplog.at_level(logging.WARNING, logger="beaconapp"):
        log_warning("Test warning message")

    assert any("[WARNING] Test warning message" in record.message for record in caplog.records)
