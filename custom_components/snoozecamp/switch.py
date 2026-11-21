"""Climate and camping. Both become commands on the relay."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_CAMP_HOURS
from .entity import SnoozeEntity, listen_vehicles

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["snoozecamp"][entry.entry_id]

    def build(vehicle_id, _vehicle):
        return [
            ClimateSwitch(coordinator, vehicle_id),
            CampSwitch(coordinator, vehicle_id),
        ]

    listen_vehicles(coordinator, async_add_entities, build)


class CommandSwitch(SnoozeEntity, SwitchEntity):
    """Shows the requested state until the worker answers."""

    def __init__(self, coordinator, vehicle_id, key):
        super().__init__(coordinator, vehicle_id, key)
        self._optimistic = None
        self._pending = None

    def _handle_coordinator_update(self) -> None:
        event = self.coordinator.last_event or {}
        if event.get("commandId") == self._pending:
            self._pending = None
            if not event.get("success"):
                self._optimistic = None
                _LOGGER.error("SnoozeCamp: %s", event.get("error"))
            elif self._matches_server():
                self._optimistic = None
        elif self._optimistic is not None and self._matches_server():
            self._optimistic = None
        super()._handle_coordinator_update()

    def _matches_server(self) -> bool:
        return False

    async def _send(self, action: str, wanted: bool, params: dict | None = None) -> None:
        self._optimistic = wanted
        self.async_write_ha_state()
        try:
            result = await self.coordinator.client.command(self._vehicle_id, action, params)
        except Exception as err:
            self._optimistic = None
            self._pending = None
            self.async_write_ha_state()
            raise HomeAssistantError(str(err)) from err
        self._pending = result.get("commandId")


class ClimateSwitch(CommandSwitch):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "climate_switch")
        self._attr_translation_key = "climate_switch"

    @property
    def is_on(self):
        if self._optimistic is not None:
            return self._optimistic
        return bool(self.status().get("climate_active"))

    def _matches_server(self) -> bool:
        return bool(self.status().get("climate_active")) == self._optimistic

    async def async_turn_on(self, **kwargs):
        await self._send("TRIGGER_ONCE", True)

    async def async_turn_off(self, **kwargs):
        await self._send("STOP_CLIMATE", False)


class CampSwitch(CommandSwitch):
    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator, vehicle_id, "camp")
        self._attr_translation_key = "camp"

    @property
    def is_on(self):
        if self._optimistic is not None:
            return self._optimistic
        camper = (self.vehicle or {}).get("camper") or {}
        return bool(camper.get("active"))

    def _matches_server(self) -> bool:
        camper = (self.vehicle or {}).get("camper") or {}
        return bool(camper.get("active")) == self._optimistic

    async def async_turn_on(self, **kwargs):
        hours = self.coordinator.entry.options.get("camp_hours", DEFAULT_CAMP_HOURS)
        until = (datetime.now(timezone.utc) + timedelta(hours=int(hours))).isoformat().replace("+00:00", "Z")
        await self._send("START_CAMPER_MODE", True, {"until": until})

    async def async_turn_off(self, **kwargs):
        await self._send("STOP_CAMPER_MODE", False)
