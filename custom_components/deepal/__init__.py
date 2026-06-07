from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.issue_registry import async_create_issue, IssueSeverity
from datetime import timedelta
import logging

from .api import DeepalAPI, TokenInvalidError
from .const import (
    DOMAIN, PLATFORMS,
    CONF_TOKEN, CONF_REFRESH_TOKEN, CONF_DEVICE_ID, CONF_VEHICLE_ID,
    CONF_EMAIL, CONF_PASSWORD, CONF_AUTH_MODE, CONF_COUNTRY, AUTH_MODE_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


async def _async_create_repair(hass):
    async_create_issue(
        hass,
        DOMAIN,
        "token_invalid",
        is_fixable=True,
        severity=IssueSeverity.ERROR,
        translation_key="token_invalid",
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    scan_interval = entry.data.get("scan_interval", 60)

    def on_tokens_updated(token: str, refresh_token: str):
        """Persist new tokens to config entry after refresh."""
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_TOKEN: token, CONF_REFRESH_TOKEN: refresh_token},
        )
        _LOGGER.debug("Deepal: tokens persisted to config entry")

    def on_token_invalid():
        """Create a repair issue when tokens are dead — must be scheduled on event loop."""
        hass.loop.call_soon_threadsafe(
            lambda: hass.async_create_task(
                _async_create_repair(hass)
            )
        )
        _LOGGER.error("Deepal: tokens invalid — repair notification created")

    api = DeepalAPI(
        device_id=entry.data[CONF_DEVICE_ID],
        vehicle_id=entry.data[CONF_VEHICLE_ID],
        country=entry.data.get(CONF_COUNTRY, "AU"),
        token=entry.data.get(CONF_TOKEN, ""),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN, ""),
        on_tokens_updated=on_tokens_updated,
        on_token_invalid=on_token_invalid,
    )

    # Fetch vehicle info
    try:
        vehicle_info_response = await hass.async_add_executor_job(api.get_vehicle_info)
    except TokenInvalidError:
        _LOGGER.error("Deepal: tokens invalid on startup, repair required")
        await _async_create_repair(hass)
        return False
    if vehicle_info_response and vehicle_info_response.get("success"):
        vehicles = vehicle_info_response.get("data", [])
        matched = next(
            (v for v in vehicles if v["carId"] == entry.data[CONF_VEHICLE_ID]),
            None,
        )
    else:
        matched = None
        code = vehicle_info_response.get("code", "") if vehicle_info_response else ""
        msg = vehicle_info_response.get("msg", "Unknown error") if vehicle_info_response else "No response"
        # Clean up non-breaking spaces from API messages
        msg = msg.replace(" ", " ") if msg else msg
        if code in ("APP_1_1_02_005", "401", "40001", "COMMON_1_1_01_001"):
            _LOGGER.error("Deepal: auth error loading vehicle info (%s): %s", code, msg)
            on_token_invalid()
        else:
            _LOGGER.warning("Deepal: could not load vehicle info (%s): %s", code, msg)

    if matched:
        _LOGGER.info("Deepal: loaded vehicle info for %s (%s)", matched.get("modelName"), matched.get("vin"))

    async def _async_update_data():
        try:
            condition = await hass.async_add_executor_job(api.get_vehicle_condition)
            if condition is None:
                raise UpdateFailed("No data returned from API")
            if not condition.get("success"):
                raise UpdateFailed(f"API returned error: {condition.get('code')}")

            # Fetch OTA status — failure here is non-fatal
            try:
                ota_response = await hass.async_add_executor_job(api.get_ota_status)
                ota_data = ota_response.get("data") if ota_response and ota_response.get("success") else None
            except Exception:
                ota_data = None

            # Merge OTA into condition data
            condition["ota"] = ota_data
            return condition
        except TokenInvalidError as e:
            raise ConfigEntryAuthFailed(f"Token invalid: {e}") from e

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="deepal",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "vehicle_info": matched or {},
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
