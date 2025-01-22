import urllib.request
import urllib.parse
import json

class WsprLiveApi:
    WSPRLIVE_API_ENDPOINT = "https://db1.wspr.live/"

    FREQUENCY_MAPPING = {
        "2200m": "-1",
        "600m": "0",
        "160m": "1",
        "80m": "3",
        "60m": "5",
        "40m": "7",
        "30m": "10",
        "20m": "14",
        "17m": "18",
        "15m": "21",
        "12m": "24",
        "10m": "28",
        "6m": "50",
        "4m": "70",
        "2m": "144"
    }

    @staticmethod
    def fetch_data(query):
        """Fetches data from the WSPR.live API for a given SQL query."""
        request_url = f"{WsprLiveApi.WSPRLIVE_API_ENDPOINT}?query={urllib.parse.quote_plus(query)}"
        try:
            with urllib.request.urlopen(request_url) as response:
                return json.loads(response.read().decode("UTF-8")).get("data", [])
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from WSPR.live: {e}")

    @staticmethod
    def get_wspr_spots_data(band, tx_call, order_by, order_direction, records_amount):
        """Fetches WSPR spots data for a specific band, transmitter call sign, and query parameters."""
        if band not in WsprLiveApi.FREQUENCY_MAPPING:
            raise ValueError(f"Invalid band: {band}. "
                             f"Must be one of: {', '.join(WsprLiveApi.FREQUENCY_MAPPING.keys())}"
            )

        return WsprLiveApi.fetch_data(
            f"SELECT * FROM rx "
            f"WHERE band = {WsprLiveApi.FREQUENCY_MAPPING[band]} "
            f"AND tx_sign = '{tx_call}' "
            f"ORDER BY {order_by} {order_direction} "
            f"LIMIT {records_amount} FORMAT JSON"
        )
