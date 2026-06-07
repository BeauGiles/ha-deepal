import requests
import logging
import time
import json
import base64
import threading
from typing import Callable, Optional

_LOGGER = logging.getLogger(__name__)

from .const import BASE_URL, USER_AGENT, RSA_PUBLIC_KEY

BASE_HEADERS = {
    "appId": "ca",
    "appType": "IOS",
    "deviceType": "iPhone",
    "appVersion": "V1.11.0",
    "language": "en_US",
    "Accept-Language": "en_US",
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT,
    "X-OS-Version": "26.5",
}


class TokenInvalidError(Exception):
    """Raised when tokens are invalid and cannot be refreshed."""
    pass


def _decode_token_expiry(token: str) -> int:
    try:
        jwt = token.replace("Bearer ", "").split("|")[0]
        payload = jwt.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        return decoded.get("exp", 0)
    except Exception as e:
        _LOGGER.error("Error decoding token: %s", e)
        return 0




def fetch_countries() -> dict:
    """Fetch supported countries — no auth required."""
    import urllib.request
    req = urllib.request.Request(
        f"{BASE_URL}/intl-app-auth/api/country/register-list/v2",
        method="POST",
        headers={**BASE_HEADERS, "Content-Type": "application/json"},
        data=b"{}",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


class DeepalAPI:
    def __init__(
        self,
        device_id: str,
        vehicle_id: str,
        country: str = "AU",
        token: str = "",
        refresh_token: str = "",
        on_tokens_updated: Optional[Callable[[str, str], None]] = None,
        on_token_invalid: Optional[Callable[[], None]] = None,
    ):
        self.device_id = device_id
        self.vehicle_id = vehicle_id
        self.country = country
        self.token = token
        self.refresh_token = refresh_token
        self._token_expiry = _decode_token_expiry(token) if token else 0
        self._refresh_lock = threading.Lock()
        self._on_tokens_updated = on_tokens_updated
        self._on_token_invalid = on_token_invalid

        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self.session.headers.update({
            "deviceId": device_id,
            "selectCountry": country,
        })
        if token:
            self._set_auth_headers()

    def _set_auth_headers(self):
        parts = self.token.split("|")
        user_token = parts[1] if len(parts) > 1 else ""
        self.session.headers.update({
            "Authorization": self.token,
            "X-Tsp-User-Token": user_token,
            "X-VCS-User-Token": user_token,
        })

    def _token_needs_refresh(self) -> bool:
        return time.time() > (self._token_expiry - 600)

    def update_tokens(self, token: str, refresh_token: str):
        self.token = token
        self.refresh_token = refresh_token
        self._token_expiry = _decode_token_expiry(token)
        self._set_auth_headers()
        if self._on_tokens_updated:
            self._on_tokens_updated(token, refresh_token)

    def refresh(self) -> bool:
        """Refresh the access token using the refresh token."""
        with self._refresh_lock:
            if not self._token_needs_refresh():
                return True
            url = f"{BASE_URL}/intl-app-auth/api/auth/refresh-token"
            try:
                r = self.session.post(url, json={"refreshToken": self.refresh_token})
                data = r.json()
                if data.get("success"):
                    self.update_tokens(
                        data["data"]["token"],
                        data["data"]["refreshToken"],
                    )
                    _LOGGER.info("Deepal: token refreshed, expires at %s", self._token_expiry)
                    return True
                _LOGGER.error("Deepal: token refresh failed: %s", data)
                return False
            except Exception as e:
                _LOGGER.error("Deepal: token refresh exception: %s", e)
                return False

    def _is_auth_error(self, data: dict) -> bool:
        if not data:
            return False
        code = str(data.get("code", ""))
        return not data.get("success") and code in (
            "401", "40001", "token expired",
            "COMMON_1_1_01_001",
            "APP_1_1_02_005",  # Logged in on another device
        )

    def _request(self, method: str, url: str, **kwargs):
        try:
            if self._token_needs_refresh():
                if not self.refresh():
                    raise TokenInvalidError("Token refresh failed")

            r = self.session.request(method, url, **kwargs)
            data = r.json()

            if self._is_auth_error(data):
                _LOGGER.info("Deepal: token rejected, attempting refresh...")
                if self.refresh():
                    r = self.session.request(method, url, **kwargs)
                    data = r.json()

                if self._is_auth_error(data):
                    _LOGGER.error("Deepal: token invalid after refresh, repair required")
                    if self._on_token_invalid:
                        self._on_token_invalid()
                    raise TokenInvalidError("Token invalid after refresh")

            return data
        except TokenInvalidError:
            raise
        except Exception as e:
            _LOGGER.error("Deepal: API request exception: %s", e)
            return None

    def get_vehicle_condition(self):
        url = f"{BASE_URL}/intl-app-car-condition/api/vehicle/condition"
        body = {
            "vehicleId": int(self.vehicle_id),
            "vechileCriteria": {
                "lamp": "1",
                "airConditionPlan": "0",
                "hvac": "1",
                "charge": "1",
                "door": "1",
                "departurePlan": "0",
                "seat": "1",
                "warmCoolingBox": "0",
                "window": "1",
                "fuel": "0",
                "welcome": "0",
                "location": "0",
                "vehicleStatus": "1",
                "tire": "1",
            },
        }
        return self._request("POST", url, json=body)

    def get_ota_status(self):
        url = f"{BASE_URL}/intl-app-user/api/ota/get-upgrade-status"
        return self._request("POST", url, json={"vehicleId": int(self.vehicle_id)})

    def get_vehicle_info(self):
        url = f"{BASE_URL}/intl-app-user/api/car/vehicles"
        return self._request("POST", url, json={})

    def get_vehicles(self):
        """Fetch vehicle list — used during config flow before full API init."""
        url = f"{BASE_URL}/intl-app-user/api/car/vehicles"
        return self.session.post(url, json={}).json()
