"""Polling plus a server-sent stream, from the relay or from the worker's local server."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SnoozeClient, SnoozeError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
POLL = 60


class SnoozeCoordinator(DataUpdateCoordinator):
    """Keeps the last stand the relay stored."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=POLL))
        self.entry = entry
        self.client = SnoozeClient(async_get_clientsession(hass), entry.data["url"], entry.data["token"])
        self.last_event: dict | None = None
        self._stream: asyncio.Task | None = None

    async def _async_update_data(self) -> dict:
        try:
            payload = await self.client.vehicles()
        except SnoozeError as err:
            if err.status == 401:
                self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(str(err)) from err
        return {
            "scopes": payload.get("scopes") or [],
            "vehicles": {item["id"]: item for item in payload.get("vehicles") or []},
        }

    def start_events(self):
        """Opens the stream and refreshes whenever the relay publishes."""
        self._stream = self.hass.async_create_background_task(self._listen(), "snoozecamp-events")

        def _stop() -> None:
            if self._stream:
                self._stream.cancel()

        return _stop

    async def _listen(self) -> None:
        backoff = 1
        while True:
            try:
                async for event, payload in self.client.events():
                    backoff = 1
                    self.last_event = {"type": event, **payload}
                    await self.async_request_refresh()
            except asyncio.CancelledError:
                raise
            except SnoozeError as err:
                if err.status == 401:
                    self.entry.async_start_reauth(self.hass)
                    return
                _LOGGER.debug("SnoozeCamp stream: %s", err)
            except Exception as err:
                _LOGGER.debug("SnoozeCamp stream dropped: %s", err)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
