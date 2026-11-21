"""HTTP client for the SnoozeCamp relay."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import aiohttp

from .const import DEFAULT_URL


class SnoozeError(Exception):
    """The relay refused the call."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class SnoozeClient:
    """Talks to /api/v1, which the relay and the worker's local server both answer."""

    def __init__(self, session: aiohttp.ClientSession, url: str, token: str) -> None:
        self._session = session
        self._url = (url or DEFAULT_URL).rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    async def vehicles(self) -> dict:
        """The stored stand of every vehicle."""
        return await self._request("GET", "/api/v1/vehicles")

    async def command(self, vehicle_id: str, action: str, params: dict | None = None) -> dict:
        """Hands a command to the relay, which forwards it to the worker."""
        return await self._request(
            "POST",
            f"/api/v1/vehicles/{vehicle_id}/commands",
            {"action": action, "params": params or {}},
        )

    async def climate_target(self, vehicle_id: str, celsius: float) -> dict:
        """Stores the setpoint. A following command tells the worker."""
        return await self._request(
            "PUT",
            f"/api/v1/vehicles/{vehicle_id}/climate-target",
            {"celsius": celsius},
        )

    def events(self) -> AsyncIterator[tuple[str, dict]]:
        """Server-sent events. The caller refreshes after each one."""
        return self._events()

    async def _events(self) -> AsyncIterator[tuple[str, dict]]:
        timeout = aiohttp.ClientTimeout(total=None, sock_read=90)
        async with self._session.get(
            f"{self._url}/api/v1/events",
            headers=self._headers,
            timeout=timeout,
        ) as response:
            if response.status >= 400:
                raise SnoozeError(response.reason or "events", response.status)
            event = "message"
            data: list[str] = []
            async for raw in response.content:
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                if line == "":
                    if data:
                        yield event, json.loads("\n".join(data))
                    event = "message"
                    data = []
                elif line.startswith(":"):
                    continue
                elif line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:].strip())

    async def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        async with self._session.request(
            method,
            f"{self._url}{path}",
            headers={**self._headers, "Content-Type": "application/json"},
            json=body,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            payload = await response.json(content_type=None)
            if response.status >= 400:
                message = payload.get("error") if isinstance(payload, dict) else response.reason
                raise SnoozeError(str(message or "request failed"), response.status)
            return payload
