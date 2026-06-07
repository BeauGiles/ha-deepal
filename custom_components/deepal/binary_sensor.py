from __future__ import annotations
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)
DOMAIN = "deepal"

ICONS = {
    "driver_door": "mdi:car-door",
    "passenger_door": "mdi:car-door",
    "trunk": "mdi:car-back",
    "charge_gun": "mdi:ev-plug-type2",
}


def _device_info(entry, vehicle_info: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.data["vehicle_id"])},
        name=f"Deepal {vehicle_info.get('modelName') or 'S07'}",
        manufacturer="Deepal",
        model=vehicle_info.get("modelName") or "S07",
        serial_number=vehicle_info.get("vin"),
    )


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    vehicle_info = data.get("vehicle_info", {})

    entities = [
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Driver Door", "driver_door",
                           BinarySensorDeviceClass.DOOR,
                           ["door", "driverLock"],
                           lambda x: x == 1),
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Front Passenger Door", "passenger_door",
                           BinarySensorDeviceClass.DOOR,
                           ["door", "passengerLock"],
                           lambda x: x == 1),
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Boot", "trunk",
                           BinarySensorDeviceClass.DOOR,
                           ["door", "trunk"],
                           lambda x: x == 1),
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Charge Gun", "charge_gun",
                           BinarySensorDeviceClass.PLUG,
                           ["charge", "chargeConStatus"],
                           lambda x: x == 3),
    ]
    async_add_entities(entities)


class DeepalBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, vehicle_info, name, key, device_class, path, is_on_fn):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info
        self._name = name
        self._key = key
        self._attr_device_class = device_class
        self._path = path
        self._is_on_fn = is_on_fn

    @property
    def icon(self):
        return ICONS.get(self._key)

    @property
    def unique_id(self):
        return f"deepal_{self._entry.data['vehicle_id']}_{self._key}"

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        try:
            if self.coordinator.data is None:
                return None
            data = self.coordinator.data.get("data", {})
            value = data
            for key in self._path:
                value = value[key]
            return self._is_on_fn(value)
        except (KeyError, TypeError):
            return None

    @property
    def device_info(self):
        return _device_info(self._entry, self._vehicle_info)
