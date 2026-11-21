"""Shared device for one vehicle."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SnoozeCoordinator


class SnoozeEntity(CoordinatorEntity[SnoozeCoordinator]):
    """One vehicle, as the relay last reported it."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SnoozeCoordinator, vehicle_id: str, key: str) -> None:
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._key = key
        self._attr_unique_id = f"{vehicle_id}_{key}"

    @property
    def vehicle(self) -> dict | None:
        data = self.coordinator.data or {}
        return data.get("vehicles", {}).get(self._vehicle_id)

    @property
    def available(self) -> bool:
        return super().available and self.vehicle is not None

    @property
    def device_info(self) -> DeviceInfo:
        name = (self.vehicle or {}).get("name") or "SnoozeCamp"
        return DeviceInfo(
            identifiers={(DOMAIN, self._vehicle_id)},
            name=name,
            manufacturer="SnoozeCamp",
        )

    def status(self) -> dict:
        vehicle = self.vehicle or {}
        status = vehicle.get("status")
        return status if isinstance(status, dict) else {}

    def scopes(self) -> list:
        return (self.coordinator.data or {}).get("scopes") or []


def listen_vehicles(coordinator: SnoozeCoordinator, async_add_entities, build) -> None:
    """Creates entities for vehicles already known and for ones that appear later."""
    known: set[str] = set()

    def _sync() -> None:
        fresh = []
        for vehicle_id, vehicle in (coordinator.data or {}).get("vehicles", {}).items():
            if vehicle_id in known:
                continue
            made = build(vehicle_id, vehicle)
            if not made:
                continue
            known.add(vehicle_id)
            fresh.extend(made)
        if fresh:
            async_add_entities(fresh)

    coordinator.async_add_listener(_sync)
    _sync()
