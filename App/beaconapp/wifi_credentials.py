from dataclasses import dataclass, asdict


@dataclass
class WiFiCredentials:
    wifi_access_point_name: str = None
    wifi_access_point_password: str = None

    def to_json(self) -> dict:
        return asdict(self)
