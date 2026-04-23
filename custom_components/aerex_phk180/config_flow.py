"""Config Flow für Aerex PHK180."""
from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .aerex_client import AerexPHK180Client
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN, MODEL


class AerexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Führt den Benutzer durch die Einrichtung."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host     = user_input[CONF_HOST].strip()
            username = user_input.get(CONF_USERNAME, "").strip()
            password = user_input.get(CONF_PASSWORD, "")
            session  = async_get_clientsession(self.hass)
            client   = AerexPHK180Client(host, session, username, password)

            try:
                ok = await client.async_test_connection()
                if ok:
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Aerex {MODEL} ({host})",
                        data={
                            CONF_HOST:     host,
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                        },
                    )
                else:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, description={"suggested_value": "192.168.1.x"}): str,
                vol.Optional(CONF_USERNAME, default=""): str,
                vol.Optional(CONF_PASSWORD, default=""): str,
            }),
            errors=errors,
        )
