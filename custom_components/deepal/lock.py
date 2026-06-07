from __future__ import annotations
import logging
from homeassistant.components.lock import LockEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)
DOMAIN = "deepal"

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    vehicle_info = data.get("vehicle_info", {})
    async_add_entities([DeepalLock(coordinator, entry, vehicle_info)])


class DeepalLock(CoordinatorEntity, LockEntity):
    def __init__(self, coordinator, entry, vehicle_info):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info

    @property
    def unique_id(self):
        return f"deepal_{self._entry.data['vehicle_id']}_lock"

    @property
    def name(self):
        return "Lock"

    @property
    def is_locked(self):
        try:
            status = self.coordinator.data.get("data", {}).get("door", {}).get("driverLock")
            return status == 0
        except (KeyError, TypeError):
            return None

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data["vehicle_id"])},
            name=f"Deepal {self._vehicle_info.get('modelName') or 'S07'}",
            manufacturer="Deepal",
            model=self._vehicle_info.get("modelName") or "S07",
            serial_number=self._vehicle_info.get("vin"),
        )
