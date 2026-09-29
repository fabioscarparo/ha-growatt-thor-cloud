"""Config flow for the Growatt THOR integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrowattThorApi, GrowattThorApiError, GrowattThorAuthError, hash_password
from .const import CONF_PASSWORD_HASH, DOMAIN

USER_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})


class GrowattThorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the ShinePhone account; only the Growatt password hash is stored."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Initial setup: one config entry per ShinePhone account."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            # Lower-cased so "User" and "user" cannot become two entries.
            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()
            password_hash = hash_password(user_input[CONF_PASSWORD])
            errors = await self._async_validate(username, password_hash)
            if not errors:
                return self.async_create_entry(
                    title=username,
                    data={CONF_USERNAME: username, CONF_PASSWORD_HASH: password_hash},
                )
        return self.async_show_form(
            step_id="user",
            # Keep the username on error, never echo the password back.
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA, {CONF_USERNAME: (user_input or {}).get(CONF_USERNAME)}
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Triggered by ConfigEntryAuthFailed, e.g. after a password change."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new password and reload the entry with it."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            password_hash = hash_password(user_input[CONF_PASSWORD])
            errors = await self._async_validate(entry.data[CONF_USERNAME], password_hash)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD_HASH: password_hash}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
        )

    async def _async_validate(self, username: str, password_hash: str) -> dict[str, str]:
        """Log in and list chargers; returns form errors, empty if all is fine."""
        api = GrowattThorApi(async_get_clientsession(self.hass), username, password_hash)
        try:
            await api.login()
            chargers = await api.async_get_chargers()
        except GrowattThorAuthError:
            return {"base": "invalid_auth"}
        except GrowattThorApiError:
            return {"base": "cannot_connect"}
        if not chargers:
            # Valid account without a charger: nothing to create entities for.
            return {"base": "no_chargers"}
        return {}
