"""Asks the relay to read the vehicle once."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .entity import SnoozeEntity, listen_vehicles


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["snoozecamp"][entry.entry_id]

    def build(vehicle_id, _vehicle):
        return [ReadButton(coordinator, vehicle_id)]

    listen_vehicles(coordinator, async_add_entities, build)


class ReadButton(SnoozeEntity, ButtonEntity):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "read")
        self._attr_translation_key = "read"

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.command(self._vehicle_id, "READ_STATUS")
        except Exception as err:
            raise HomeAssistantError(str(err)) from err
