import json
import urllib.request
import urllib.parse
import pytest
import os
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


def test_invalid_band_raises_error():
    """
    Test that get_wspr_spots_data raises ValueError when an invalid band is provided.
    """
    with pytest.raises(ValueError):
        WsprLiveApi.get_wspr_spots_data("1m", "N0CALL", "time", "DESC", 10)


def test_get_wspr_spots_data_no_internet(monkeypatch):
    """
    Test that get_wspr_spots_data raises URLError when there is no internet connection.
    """
    # Mock urllib.request.urlopen with our urlopen_no_connection_mock function
    monkeypatch.setattr(urllib.request, "urlopen", urlopen_no_connection_mock)
    with pytest.raises(urllib.error.URLError):
        WsprLiveApi.get_wspr_spots_data("2m", "N0CALL", "time", "DESC", 10)


def test_get_wspr_spots_data_returns_empty_list_when_no_data(monkeypatch):
    """
    Test that get_wspr_spots_data returns an empty list when the JSON response is empty.
    """
    # Mock urllib.request.urlopen with urlopen_no_data_mock function
    monkeypatch.setattr(urllib.request, "urlopen", urlopen_no_data_mock)
    assert WsprLiveApi.get_wspr_spots_data("2m", "N0CALL", "time", "DESC", 10) == []


def test_get_wspr_spots_data_constructs_correct_query(monkeypatch):
    """
    Test that get_wspr_spots_data constructs the correct SQL query and returns expected data.
    """
    # Mock urllib.request.urlopen with urlopen_success_mock function
    monkeypatch.setattr(urllib.request, "urlopen", urlopen_success_mock)
    data = WsprLiveApi.get_wspr_spots_data("2m", "N0CALL", "time", "DESC", 10)

    assert len(data) == 10
    for item in data:
        assert item.get("time") in ["2024-07-14 20:00:00", "2024-07-14 20:10:00", "2024-07-14 20:20:00"]
        assert item.get("tx_sign") == "N0CALL"
        assert item.get("tx_loc") == "XX00"
        assert item.get("tx_lat") == 55.479
        assert item.get("tx_lon") == 22.958
        assert str(item.get("frequency")).startswith("144")
        assert item.get("power") == 23
        assert item.get("snr") <= -13
        assert item.get("drift") == 0
        assert item.get("distance") >= 1706
