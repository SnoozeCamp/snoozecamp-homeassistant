"""Sensors for the stored vehicle stand."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTemperature, UnitOfTime

from .entity import SnoozeEntity, listen_vehicles


SENSORS = (
    ("range", "range", SensorDeviceClass.DISTANCE, UnitOfLength.KILOMETERS, "range_km", SensorStateClass.MEASUREMENT),
    ("battery", "battery", SensorDeviceClass.BATTERY, PERCENTAGE, "battery_percent", SensorStateClass.MEASUREMENT),
    ("charge_target", "charge_target", SensorDeviceClass.BATTERY, PERCENTAGE, "charge_target_percent", SensorStateClass.MEASUREMENT),
    ("climate_target", "climate_target", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, "climate_target_celsius", SensorStateClass.MEASUREMENT),
    ("climate_remaining", "climate_remaining", SensorDeviceClass.DURATION, UnitOfTime.MINUTES, "climate_remaining_minutes", SensorStateClass.MEASUREMENT),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["snoozecamp"][entry.entry_id]

    def build(vehicle_id, _vehicle):
        entities = [SnoozeSensor(coordinator, vehicle_id, *spec) for spec in SENSORS]
        entities.append(SnoozeTimeSensor(coordinator, vehicle_id, "camp_until", "camp_until", "until"))
        entities.append(SnoozeTimeSensor(coordinator, vehicle_id, "read_at", "read_at", "readAt"))
        return entities

    listen_vehicles(coordinator, async_add_entities, build)


class SnoozeSensor(SnoozeEntity, SensorEntity):
    """One number from the last reading."""

    def __init__(self, coordinator, vehicle_id, key, name_key, device_class, unit, field, state_class):
        super().__init__(coordinator, vehicle_id, key)
        self._field = field
        self._attr_translation_key = name_key
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class

    @property
    def native_value(self):
        if self._field == "climate_target_celsius":
            vehicle = self.vehicle or {}
            reported = self.status().get("climate_target_celsius")
            return vehicle.get("climateTargetCelsius") if vehicle.get("climateTargetCelsius") is not None else reported
        return self.status().get(self._field)


class SnoozeTimeSensor(SnoozeEntity, SensorEntity):
    """A timestamp from the camper plan or the last reading."""

    def __init__(self, coordinator, vehicle_id, key, name_key, field):
        super().__init__(coordinator, vehicle_id, key)
        self._field = field
        self._attr_translation_key = name_key
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        from homeassistant.util import dt as dt_util

        if self._field == "readAt":
            raw = (self.vehicle or {}).get("readAt")
        else:
            camper = (self.vehicle or {}).get("camper") or {}
            raw = camper.get(self._field)
        return dt_util.parse_datetime(raw) if raw else None
