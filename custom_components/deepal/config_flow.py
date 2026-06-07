import voluptuous as vol
import uuid
import logging
from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_TOKEN, CONF_REFRESH_TOKEN, CONF_DEVICE_ID, CONF_VEHICLE_ID,
    CONF_EMAIL, CONF_PASSWORD, CONF_AUTH_MODE, CONF_COUNTRY,
    AUTH_MODE_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class DeepalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._token = None
        self._refresh_token = None
        self._device_id = None
        self._country = None
        self._vehicles = []

    async def async_step_user(self, user_input=None):
        """First step — fetch and select country."""
        errors = {}
        countries = {}
        try:
            from .api import fetch_countries
            result = await self.hass.async_add_executor_job(fetch_countries)
            if result and result.get("success"):
                for c in result.get("data", []):
                    countries[c["countryCode"]] = c["englishName"]
        except Exception as e:
            _LOGGER.error("Deepal: could not fetch countries: %s", e)
            errors["base"] = "cannot_connect"

        if not countries:
            countries = {
                "AU": "Australia", "NZ": "New Zealand", "SG": "Singapore",
                "MY": "Malaysia", "TH": "Thailand", "VN": "Viet Nam",
                "HK": "Hong Kong", "MO": "Macau", "ID": "Indonesia",
                "PH": "Philippines", "MN": "Mongolia",
            }

        if user_input is not None and not errors:
            self._country = user_input[CONF_COUNTRY]
            return await self.async_step_token()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_COUNTRY, default="AU"): vol.In(countries),
            }),
            errors=errors,
        )

    async def async_step_token(self, user_input=None):
        """Enter tokens and optional device ID."""
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            refresh_token = user_input[CONF_REFRESH_TOKEN].strip()
            self._token = token if token.startswith("Bearer ") else f"Bearer {token}"
            self._refresh_token = refresh_token if refresh_token.startswith("Bearer ") else f"Bearer {refresh_token}"
            self._device_id = user_input.get(CONF_DEVICE_ID, "").strip() or str(uuid.uuid4()).upper()
            return await self._async_discover_vehicle(errors)

        return self.async_show_form(
            step_id="token",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_DEVICE_ID, description={"suggested_value": ""}): str,
            }),
            errors=errors,
        )

    async def _async_discover_vehicle(self, errors: dict):
        """Fetch vehicle list and create entry."""
        from .api import DeepalAPI
        api = DeepalAPI(
            device_id=self._device_id,
            vehicle_id="",
            country=self._country,
            token=self._token,
            refresh_token=self._refresh_token,
        )
        try:
            result = await self.hass.async_add_executor_job(api.get_vehicles)
            vehicles = result.get("data", []) if result and result.get("success") else []
        except Exception:
            vehicles = []

        if not vehicles:
            errors["base"] = "cannot_connect"
            return await self.async_step_token()

        if len(vehicles) == 1:
            return self._create_entry(vehicles[0])

        self._vehicles = vehicles
        return await self.async_step_pick_vehicle()

    async def async_step_pick_vehicle(self, user_input=None):
        """Let user pick a vehicle if multiple are found."""
        if user_input is not None:
            vehicle = next(v for v in self._vehicles if v["carId"] == user_input["vehicle"])
            return self._create_entry(vehicle)

        options = {v["carId"]: f"{v['modelName']} ({v['vin']})" for v in self._vehicles}
        return self.async_show_form(
            step_id="pick_vehicle",
            data_schema=vol.Schema({
                vol.Required("vehicle"): vol.In(options),
            }),
        )

    def _create_entry(self, vehicle: dict):
        return self.async_create_entry(
            title=f"Deepal {vehicle['modelName']}",
            data={
                CONF_AUTH_MODE: AUTH_MODE_TOKEN,
                CONF_TOKEN: self._token,
                CONF_REFRESH_TOKEN: self._refresh_token,
                CONF_DEVICE_ID: self._device_id,
                CONF_VEHICLE_ID: vehicle["carId"],
                CONF_COUNTRY: self._country,
                CONF_EMAIL: "",
                CONF_PASSWORD: "",
            },
        )

    async def async_step_reconfigure(self, user_input=None):
        """Allow reconfiguring tokens."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            refresh_token = user_input[CONF_REFRESH_TOKEN].strip()
            return self.async_update_reload_and_abort(
                entry,
                data={
                    **entry.data,
                    CONF_TOKEN: token if token.startswith("Bearer ") else f"Bearer {token}",
                    CONF_REFRESH_TOKEN: refresh_token if refresh_token.startswith("Bearer ") else f"Bearer {refresh_token}",
                    CONF_DEVICE_ID: user_input.get(CONF_DEVICE_ID, "").strip() or entry.data.get(CONF_DEVICE_ID),
                },
                reason="reconfigure_successful",
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN, default=entry.data.get(CONF_TOKEN, "")): str,
                vol.Required(CONF_REFRESH_TOKEN, default=entry.data.get(CONF_REFRESH_TOKEN, "")): str,
                vol.Optional(CONF_DEVICE_ID, default=entry.data.get(CONF_DEVICE_ID, "")): str,
            }),
        )
