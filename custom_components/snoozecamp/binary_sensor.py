"""On/off facts from the stored stand."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity import SnoozeEntity, listen_vehicles


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["snoozecamp"][entry.entry_id]

    def build(vehicle_id, _vehicle):
        return [
            SnoozeBinary(coordinator, vehicle_id, "charging", "charging", BinarySensorDeviceClass.BATTERY_CHARGING, "charging"),
            SnoozeBinary(coordinator, vehicle_id, "climate", "climate", BinarySensorDeviceClass.RUNNING, "climate_active"),
            SnoozeWorker(coordinator, vehicle_id),
        ]

    def build_lock(_vehicle_id, vehicle):
        # Older models show no lock state in the maker's app. The sensor appears with the first
        # reading that has one; until then the builder is asked again on every update.
        status = vehicle.get("status") or {}
        if status.get("locked") is None:
            return []
        return [SnoozeLockState(coordinator, _vehicle_id)]

    def build_phone(vehicle_id, vehicle):
        if (vehicle.get("worker") or {}).get("batteryPercent") is None:
            return []
        return [SnoozePhonePlugged(coordinator, vehicle_id)]

    listen_vehicles(coordinator, async_add_entities, build)
    listen_vehicles(coordinator, async_add_entities, build_lock)
    listen_vehicles(coordinator, async_add_entities, build_phone)


class SnoozeBinary(SnoozeEntity, BinarySensorEntity):
    def __init__(self, coordinator, vehicle_id, key, name_key, device_class, field):
        super().__init__(coordinator, vehicle_id, key)
        self._field = field
        self._attr_translation_key = name_key
        self._attr_device_class = device_class

    @property
    def is_on(self):
        value = self.status().get(self._field)
        return None if value is None else bool(value)


class SnoozeLockState(SnoozeEntity, BinarySensorEntity):
    """Whether the car is locked, as the maker's app last showed it. Read only.

    Home Assistant's lock class reads "on" as unlocked.
    """

    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "locked")
        self._attr_translation_key = "locked"
        self._attr_device_class = BinarySensorDeviceClass.LOCK

    @property
    def is_on(self):
        locked = self.status().get("locked")
        return None if locked is None else not bool(locked)

    @property
    def extra_state_attributes(self):
        text = self.status().get("lock_state")
        return {"lock_state": text} if text else None


class SnoozeWorker(SnoozeEntity, BinarySensorEntity):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "worker")
        self._attr_translation_key = "worker"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self):
        worker = (self.vehicle or {}).get("worker")
        if not worker:
            return None
        return bool(worker.get("online"))


class SnoozePhonePlugged(SnoozeEntity, BinarySensorEntity):
    """Whether the worker phone has power, even while it holds the charge at a limit."""

    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "phone_plugged")
        self._attr_translation_key = "phone_plugged"
        self._attr_device_class = BinarySensorDeviceClass.PLUG

    @property
    def is_on(self):
        value = ((self.vehicle or {}).get("worker") or {}).get("pluggedIn")
        return None if value is None else bool(value)
