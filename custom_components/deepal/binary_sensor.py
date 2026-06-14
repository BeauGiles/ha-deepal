from __future__ import annotations
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)
DOMAIN = "deepal"

ICONS = {
    "driver_door": "mdi:car-door-lock",
    "passenger_door": "mdi:car-door-lock",
    "trunk": "mdi:car-back",
    "charge_gun": "mdi:ev-plug-type2",
    "door_front_right": "mdi:car-door",
    "door_front_left": "mdi:car-door",
    "door_rear_left": "mdi:car-door",
    "door_rear_right": "mdi:car-door",
    "window_front_right": "mdi:car-windshield",
    "window_front_left": "mdi:car-windshield",
    "window_rear_left": "mdi:car-windshield",
    "window_rear_right": "mdi:car-windshield",
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
        # --- Lock state (driverLock / passengerLock) ---
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Driver Door Lock", "driver_door",
                           BinarySensorDeviceClass.LOCK,
                           ["door", "driverLock"],
                           lambda x: x == 0),
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Front Passenger Door Lock", "passenger_door",
                           BinarySensorDeviceClass.LOCK,
                           ["door", "passengerLock"],
                           lambda x: x == 0),

        # --- Boot ---
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Boot", "trunk",
                           BinarySensorDeviceClass.DOOR,
                           ["door", "trunk"],
                           lambda x: x == 1),

        # --- Charge gun ---
        DeepalBinarySensor(coordinator, entry, vehicle_info,
                           "Charge Gun", "charge_gun",
                           BinarySensorDeviceClass.PLUG,
                           ["charge", "chargeConStatus"],
                           lambda x: x == 3),

        # --- Door open/closed ---
        DeepalDoorSensor(coordinator, entry, vehicle_info,
                         "Front Right Door", "door_front_right", 0),
        DeepalDoorSensor(coordinator, entry, vehicle_info,
                         "Front Left Door", "door_front_left", 1),
        DeepalDoorSensor(coordinator, entry, vehicle_info,
                         "Rear Left Door", "door_rear_left", 2),
        DeepalDoorSensor(coordinator, entry, vehicle_info,
                         "Rear Right Door", "door_rear_right", 3),

        # --- Window open/closed ---
        DeepalWindowSensor(coordinator, entry, vehicle_info,
                           "Front Right Window", "window_front_right", 0),
        DeepalWindowSensor(coordinator, entry, vehicle_info,
                           "Front Left Window", "window_front_left", 1),
        DeepalWindowSensor(coordinator, entry, vehicle_info,
                           "Rear Left Window", "window_rear_left", 2),
        DeepalWindowSensor(coordinator, entry, vehicle_info,
                           "Rear Right Window", "window_rear_right", 3),
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


class DeepalDoorSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for individual door open/closed state from doors[] array."""

    def __init__(self, coordinator, entry, vehicle_info, name, key, index):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info
        self._name = name
        self._key = key
        self._index = index
        self._attr_device_class = BinarySensorDeviceClass.DOOR

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
            doors = self.coordinator.data.get("data", {}).get("door", {}).get("doors", [])
            return doors[self._index] == 1
        except (IndexError, TypeError):
            return None

    @property
    def device_info(self):
        return _device_info(self._entry, self._vehicle_info)


class DeepalWindowSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for individual window open/closed state with openDegree attribute."""

    def __init__(self, coordinator, entry, vehicle_info, name, key, index):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info
        self._name = name
        self._key = key
        self._index = index
        self._attr_device_class = BinarySensorDeviceClass.WINDOW

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
            windows = self.coordinator.data.get("data", {}).get("window", {}).get("windows", [])
            return windows[self._index] == 1
        except (IndexError, TypeError):
            return None

    @property
    def extra_state_attributes(self):
        try:
            if self.coordinator.data is None:
                return {}
            degrees = self.coordinator.data.get("data", {}).get("window", {}).get("openDegree", [])
            return {"open_degree": degrees[self._index]}
        except (IndexError, TypeError):
            return {}

    @property
    def device_info(self):
        return _device_info(self._entry, self._vehicle_info)
