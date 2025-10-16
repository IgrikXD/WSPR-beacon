import urllib.request
import urllib.parse
import json


class WsprLiveApi:
    WSPRLIVE_API_ENDPOINT = "https://db1.wspr.live/"

    FREQUENCY_MAPPING = {
        2200: "-1",
        600: "0",
        160: "1",
        80: "3",
        60: "5",
        40: "7",
        30: "10",
        20: "14",
        17: "18",
        5: "21",
        12: "24",
        10: "28",
        6: "50",
        4: "70",
        2: "144"
    }

    @classmethod
    def _fetch_data(cls, query):
        """
        Fetches data from the WSPR.live API for a given SQL query.
        """
        request_url = f"{cls.WSPRLIVE_API_ENDPOINT}?query={urllib.parse.quote_plus(query)}"

        with urllib.request.urlopen(request_url) as response:
            return json.loads(response.read().decode("UTF-8")).get("data", [])

    @classmethod
    def get_wspr_spots_data(cls, band, tx_call, order_by, order_direction, records_amount):
        """
        Fetches WSPR spots data for a specific band, transmitter call sign, and query parameters.
        """
        if band not in cls.FREQUENCY_MAPPING:
            raise ValueError

        return cls._fetch_data(
            f"SELECT * FROM rx "
            f"WHERE band = {cls.FREQUENCY_MAPPING[band]} "
            f"AND tx_sign = '{tx_call}' "
            f"ORDER BY {order_by} {order_direction} "
            f"LIMIT {records_amount} FORMAT JSON"
        )
