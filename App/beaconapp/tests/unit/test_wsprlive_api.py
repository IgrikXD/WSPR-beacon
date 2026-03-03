import json
import os
import urllib.parse
import urllib.request

import pytest

from beaconapp.wsprlive_api import WsprLiveApi


# DummyResponse simulates a response object returned by urllib.request.urlopen
class DummyResponse:
    def __init__(self, content):
        self.content = content.encode("utf-8")

    def read(self):
        return self.content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def urlopen_success_mock(url):
    """
    Dummy urlopen function that returns a dummy JSON response loaded from file.
    """
    dummy_response = os.path.join(os.path.dirname(__file__), 'wsprlive_dummy_response.json')
    with open(dummy_response, 'r', encoding='utf-8') as file:
        return DummyResponse(file.read())


def urlopen_no_data_mock(url):
    """
    Dummy urlopen function that returns empty JSON response.
    """
    return DummyResponse(json.dumps({}))


def urlopen_no_connection_mock(url):
    """
    Dummy urlopen function that simulates no internet connection by raising URLError.
    """
    raise urllib.error.URLError("No internet connection")


@pytest.mark.unit
@pytest.mark.parametrize("band, tx_call, order_by, order_direction, records_amount, expected_error", [
    ("1m", "XX0YYY", "time", "DESC", 10, "Invalid band"),
    (2, "XX0YYY", "DROP TABLE rx;--", "DESC", 10, "Invalid order_by"),
    (2, "XX0YYY", "time", "DROP", 10, "Invalid order_direction"),
    (2, "XX0YYY", "time", "DESC", "abc", "Invalid records_amount"),
])
def test_invalid_query_parameters_raise_error(band, tx_call, order_by, order_direction, records_amount, expected_error):
    """
    Test that get_wspr_spots_data raises ValueError when invalid query parameters are provided.
    """
    with pytest.raises(ValueError, match=expected_error):
        WsprLiveApi.get_wspr_spots_data(band, tx_call, order_by, order_direction, records_amount)


@pytest.mark.unit
def test_get_wspr_spots_data_no_internet(monkeypatch):
    """
    Test that get_wspr_spots_data raises URLError when there is no internet connection.
    """
    # Mock urllib.request.urlopen with our urlopen_no_connection_mock function
    monkeypatch.setattr(urllib.request, "urlopen", urlopen_no_connection_mock)
    with pytest.raises(urllib.error.URLError):
        WsprLiveApi.get_wspr_spots_data(2, "XX0YYY", "time", "DESC", 10)


@pytest.mark.unit
def test_get_wspr_spots_data_returns_empty_list_when_no_data(monkeypatch):
    """
    Test that get_wspr_spots_data returns an empty list when the JSON response is empty.
    """
    # Mock urllib.request.urlopen with urlopen_no_data_mock function
    monkeypatch.setattr(urllib.request, "urlopen", urlopen_no_data_mock)
    assert WsprLiveApi.get_wspr_spots_data(2, "XX0YYY", "time", "DESC", 10) == []


@pytest.mark.unit
def test_get_wspr_spots_data_constructs_correct_query(monkeypatch):
    """
    Test that get_wspr_spots_data constructs the correct SQL query and returns expected data.
    """
    # Mock urllib.request.urlopen with urlopen_success_mock function
    monkeypatch.setattr(urllib.request, "urlopen", urlopen_success_mock)
    data = WsprLiveApi.get_wspr_spots_data(2, "XX0YYY", "time", "DESC", 10)

    assert len(data) == 10
    for item in data:
        assert item.get("time") in ["2024-07-14 20:00:00", "2024-07-14 20:10:00", "2024-07-14 20:20:00"]
        assert item.get("tx_sign") == "XX0YYY"
        assert item.get("tx_loc") == "XX00"
        assert item.get("tx_lat") == 55.479
        assert item.get("tx_lon") == 22.958
        assert str(item.get("frequency")).startswith("144")
        assert item.get("power") == 23
        assert item.get("snr") <= -13
        assert item.get("drift") == 0
        assert item.get("distance") >= 1706
