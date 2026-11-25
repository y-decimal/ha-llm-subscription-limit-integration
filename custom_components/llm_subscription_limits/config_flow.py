"""Setup and reauthentication for subscription providers."""

import probatio
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .const import CONF_PROVIDER, DOMAIN, PROVIDER_GO
from .providers.opencode_go import AuthenticationError, EntitlementError, OpenCodeGoClient, ProviderError


class SubscriptionFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one OpenCode Go account; reserve separate entries for providers."""

    VERSION = 1

    async def _validate(self, user_input):
        try:
            await OpenCodeGoClient(async_get_clientsession(self.hass), user_input[CONF_API_KEY]).fetch()
        except AuthenticationError:
            return "invalid_auth"
        except EntitlementError:
            return "no_subscription"
        except ProviderError:
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input=None):
        """Set up the Go provider."""
        await self.async_set_unique_id(PROVIDER_GO)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            error = await self._validate(user_input)
            if not error:
                return self.async_create_entry(
                    title="OpenCode Go",
                    data={CONF_PROVIDER: PROVIDER_GO, CONF_API_KEY: user_input[CONF_API_KEY]},
                )
        else:
            error = None
        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema({
                probatio.Required(CONF_API_KEY): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
            }),
            errors={"base": error} if error else {},
        )

    async def async_step_reauth(self, entry_data):
        """Ask for a replacement key."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Validate and replace the credential without changing entity identity."""
        error = None
        if user_input is not None:
            error = await self._validate(user_input)
            if not error:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates={CONF_API_KEY: user_input[CONF_API_KEY]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=probatio.Schema({
                probatio.Required(CONF_API_KEY): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
            }),
            errors={"base": error} if error else {},
        )
