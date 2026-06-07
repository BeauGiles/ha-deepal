from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTemperature, UnitOfPressure
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)
DOMAIN = "deepal"


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

    sensors = [
        # --- Vehicle Status ---
        DeepalSensor(coordinator, entry, vehicle_info, "State of Charge", "soc", PERCENTAGE,
                     SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT,
                     ["vehicleStatus", "soc"]),
        DeepalSensor(coordinator, entry, vehicle_info, "Estimated Range", "range", UnitOfLength.KILOMETERS,
                     SensorDeviceClass.DISTANCE, SensorStateClass.MEASUREMENT,
                     ["vehicleStatus", "drvMileage"]),
        DeepalSensor(coordinator, entry, vehicle_info, "Odometer", "odometer", UnitOfLength.KILOMETERS,
                     SensorDeviceClass.DISTANCE, SensorStateClass.TOTAL_INCREASING,
                     ["vehicleStatus", "totalMileage"]),
        DeepalSensor(coordinator, entry, vehicle_info, "Power Status", "power_status", None, None, None,
                     ["vehicleStatus", "powerStatus"],
                     lambda x: {0: "Idle", 2: "Drive"}.get(x, f"Unknown ({x})")),

        # --- Charge ---
        DeepalSensor(coordinator, entry, vehicle_info, "Charge Status", "charge_status", None, None, None,
                     ["charge", "chargeStatus"],
                     lambda x: {0: "Charge Complete", 1: "Not Charging", 6: "Charging"}.get(x, f"Unknown ({x})")),
        DeepalSensor(coordinator, entry, vehicle_info, "DC Charge Gun", "dc_charge_gun", None, None, None,
                     ["charge", "dcChargeGunConnectStatus"],
                     lambda x: "Connected" if x == 3 else f"Unknown ({x})"),
        DeepalSensor(coordinator, entry, vehicle_info, "Max Charge Limit", "charge_limit", PERCENTAGE, None,
                     SensorStateClass.MEASUREMENT,
                     ["charge", "maxSocPercent"]),
        DeepalSensor(coordinator, entry, vehicle_info, "DC Charge Current", "dc_charge_current", "A",
                     SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT,
                     ["charge", "dcChargeCurrent"]),
        DeepalSensor(coordinator, entry, vehicle_info, "AC Charge Current", "ac_charge_current", "A",
                     SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT,
                     ["charge", "acChargeCurrent"]),
        DeepalSensor(coordinator, entry, vehicle_info, "Remaining Charge Time", "remain_charge_time", "min",
                     SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT,
                     ["charge", "remainChargeTime"],
                     lambda x: None if x >= 8191 else int(x)),

        # --- Climate ---
        DeepalSensor(coordinator, entry, vehicle_info, "Cabin Temperature", "cabin_temp", UnitOfTemperature.CELSIUS,
                     SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
                     ["hvac", "insideTemp"],
                     lambda x: round(x / 10, 1)),
        DeepalSensor(coordinator, entry, vehicle_info, "Cabin Humidity", "cabin_humidity", PERCENTAGE,
                     SensorDeviceClass.HUMIDITY, SensorStateClass.MEASUREMENT,
                     ["hvac", "insideHumidity"]),
        DeepalSensor(coordinator, entry, vehicle_info, "Remote Temp Setting", "remote_temp", UnitOfTemperature.CELSIUS,
                     SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,
                     ["hvac", "remoteTemp"],
                     lambda x: round(x / 10, 1)),
        DeepalSensor(coordinator, entry, vehicle_info, "HVAC A/C Status", "ac_status", None, None, None,
                     ["hvac", "acStatus"],
                     lambda x: f"{'On' if x == 1 else 'Off'} ({x})"),
        DeepalSensor(coordinator, entry, vehicle_info, "HVAC Defrost Status", "defrost_status", None, None, None,
                     ["hvac", "defrostStatus"],
                     lambda x: f"{'On' if x == 1 else 'Off'} ({x})"),

        # --- OTA ---
        DeepalOTASensor(coordinator, entry, vehicle_info),

        # --- Tyres ---
        DeepalTyreSensor(coordinator, entry, vehicle_info, "Tyre Pressure Front Left", "tyre_fl", ["tire", "leftFront"]),
        DeepalTyreSensor(coordinator, entry, vehicle_info, "Tyre Pressure Front Right", "tyre_fr", ["tire", "rightFront"]),
        DeepalTyreSensor(coordinator, entry, vehicle_info, "Tyre Pressure Rear Left", "tyre_rl", ["tire", "leftBack"]),
        DeepalTyreSensor(coordinator, entry, vehicle_info, "Tyre Pressure Rear Right", "tyre_rr", ["tire", "rightBack"]),
    ]
    async_add_entities(sensors)


class DeepalSensor(CoordinatorEntity, SensorEntity):
    ICONS = {
        "dc_charge_gun": "mdi:ev-plug-ccs2",
    }

    def __init__(self, coordinator, entry, vehicle_info, name, key, unit, device_class, state_class, path, transform=None):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info
        self._name = name
        self._key = key
        self._unit = unit
        self._device_class = device_class
        self._state_class = state_class
        self._path = path
        self._transform = transform

    @property
    def icon(self):
        return self.ICONS.get(self._key)

    @property
    def unique_id(self):
        return f"deepal_{self._entry.data['vehicle_id']}_{self._key}"

    @property
    def name(self):
        return self._name

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def native_value(self):
        try:
            if self.coordinator.data is None:
                return None
            data = self.coordinator.data.get("data", {})
            value = data
            for key in self._path:
                value = value[key]
            if self._transform:
                return self._transform(value)
            return value
        except (KeyError, TypeError):
            return None

    @property
    def device_info(self):
        return _device_info(self._entry, self._vehicle_info)


class DeepalTyreSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, vehicle_info, name, key, path):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info
        self._name = name
        self._key = key
        self._path = path
        self._last_value = None

    @property
    def unique_id(self):
        return f"deepal_{self._entry.data['vehicle_id']}_{self._key}"

    @property
    def name(self):
        return self._name

    @property
    def native_unit_of_measurement(self):
        return UnitOfPressure.KPA

    @property
    def device_class(self):
        return SensorDeviceClass.PRESSURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        try:
            if self.coordinator.data is None:
                return self._last_value
            data = self.coordinator.data.get("data", {})
            tyre = data
            for key in self._path:
                tyre = tyre[key]
            pressure = tyre.get("pressure")
            if pressure and pressure > 0:
                self._last_value = pressure
            return self._last_value
        except (KeyError, TypeError):
            return self._last_value

    @property
    def extra_state_attributes(self):
        try:
            if self.coordinator.data is None:
                return {}
            data = self.coordinator.data.get("data", {})
            tyre = data
            for key in self._path:
                tyre = tyre[key]
            return {"status": "OK" if tyre.get("status") == 0 else "Warning"}
        except (KeyError, TypeError):
            return {}

    @property
    def device_info(self):
        return _device_info(self._entry, self._vehicle_info)


class DeepalOTASensor(CoordinatorEntity, SensorEntity):
    """Sensor for OTA firmware update status."""

    def __init__(self, coordinator, entry, vehicle_info):
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_info = vehicle_info

    @property
    def unique_id(self):
        return f"deepal_{self._entry.data['vehicle_id']}_ota_status"

    @property
    def name(self):
        return "OTA Status"

    @property
    def icon(self):
        return "mdi:update"

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        ota = self.coordinator.data.get("ota")
        if not ota:
            return None
        state = ota.get("state", "Unknown")
        process = ota.get("process", 0)
        if state == "INSTALLED":
            return "Up to date"
        if state == "DOWNLOADING":
            return f"Downloading {process}%"
        if state == "INSTALLING":
            return f"Installing {process}%"
        return state

    @property
    def extra_state_attributes(self):
        if self.coordinator.data is None:
            return {}
        ota = self.coordinator.data.get("ota")
        if not ota:
            return {}
        return {
            "stage": ota.get("stage"),
            "process": ota.get("process"),
            "state": ota.get("state"),
            "task_id": ota.get("taskBase", {}).get("taskId"),
        }

    @property
    def device_info(self):
        return _device_info(self._entry, self._vehicle_info)
