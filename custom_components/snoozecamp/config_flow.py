"""Config flow for SnoozeCamp."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SnoozeClient, SnoozeError
from .const import DEFAULT_CAMP_HOURS, DEFAULT_URL, DOMAIN, LOCAL_URL_EXAMPLE


class SnoozeOptionsFlow(OptionsFlow):
    """How long a camping start should run."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        hours = self.config_entry.options.get("camp_hours", DEFAULT_CAMP_HOURS)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("camp_hours", default=hours): vol.All(vol.Coerce(int), vol.Range(min=1, max=48)),
            }),
        )


class SnoozeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the relay URL or the worker address, and a token."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return SnoozeOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            url = user_input["url"].rstrip("/")
            token = user_input["token"].strip()
            try:
                await self._check(url, token)
            except SnoozeError as err:
                errors["base"] = "invalid_auth" if err.status == 401 else "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(token[:12])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="SnoozeCamp", data={"url": url, "token": token})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("url", default=DEFAULT_URL): str,
                vol.Required("token"): str,
            }),
            errors=errors,
            description_placeholders={"online_url": DEFAULT_URL, "local_url": LOCAL_URL_EXAMPLE},
        )

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            token = user_input["token"].strip()
            try:
                await self._check(entry.data["url"], token)
            except SnoozeError as err:
                errors["base"] = "invalid_auth" if err.status == 401 else "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(entry, data={**entry.data, "token": token})
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required("token"): str}),
            errors=errors,
        )

    async def _check(self, url: str, token: str) -> None:
        client = SnoozeClient(async_get_clientsession(self.hass), url, token)
        await client.vehicles()
