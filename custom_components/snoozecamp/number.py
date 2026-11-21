"""The climate setpoint, stored on the relay and then sent to the worker."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError

from .entity import SnoozeEntity, listen_vehicles


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["snoozecamp"][entry.entry_id]

    def build(vehicle_id, _vehicle):
        return [ClimateTarget(coordinator, vehicle_id)]

    listen_vehicles(coordinator, async_add_entities, build)


class ClimateTarget(SnoozeEntity, NumberEntity):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "target")
        self._attr_translation_key = "target"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_native_min_value = 16
        self._attr_native_max_value = 30
        self._attr_native_step = 0.5

    @property
    def native_value(self):
        vehicle = self.vehicle or {}
        return vehicle.get("climateTargetCelsius")

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.client.climate_target(self._vehicle_id, value)
            await self.coordinator.client.command(self._vehicle_id, "SET_CLIMATE_TARGET")
        except Exception as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()
