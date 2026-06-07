from __future__ import annotations
import logging
from homeassistant.components.image import ImageEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant
from datetime import datetime, timezone
import urllib.request

_LOGGER = logging.getLogger(__name__)
DOMAIN = "deepal"

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    vehicle_info = data.get("vehicle_info", {})
    async_add_entities([DeepalVehicleImage(hass, entry, vehicle_info)])


class DeepalVehicleImage(ImageEntity):
    def __init__(self, hass, entry, vehicle_info):
        super().__init__(hass)
        self._entry = entry
        self._vehicle_info = vehicle_info
        self._image_url = vehicle_info.get("imgUrl")
        self._cached_image = None
        self._attr_image_last_updated = datetime.now(timezone.utc)

    @property
    def unique_id(self):
        return f"deepal_{self._entry.data['vehicle_id']}_image"

    @property
    def name(self):
        return "Vehicle Image"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["vehicle_id"])},
            name=f"Deepal {self._vehicle_info.get('modelName') or 'S07'}",
            manufacturer="Deepal",
            model=self._vehicle_info.get("modelName") or "S07",
            serial_number=self._vehicle_info.get("vin"),
        )

    async def async_image(self) -> bytes | None:
        if self._cached_image:
            return self._cached_image
        if not self._image_url:
            return None
        try:
            def fetch():
                req = urllib.request.Request(
                    self._image_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.read()
            self._cached_image = await self.hass.async_add_executor_job(fetch)
            return self._cached_image
        except Exception as e:
            _LOGGER.error("Deepal: failed to fetch vehicle image: %s", e)
            return None
