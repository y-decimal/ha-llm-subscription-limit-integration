"""Polling coordinator for the OpenCode Go provider."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .providers.opencode_go import AuthenticationError, EntitlementError, OpenCodeGoClient, ProviderError


class GoCoordinator(DataUpdateCoordinator):
    """Maintain one provider's independent data and errors."""

    def __init__(self, hass, entry: ConfigEntry, client: OpenCodeGoClient) -> None:
        super().__init__(hass, logger=logging.getLogger(__name__),
                         name=f"{DOMAIN}_opencode_go", config_entry=entry,
                         update_interval=timedelta(minutes=5))
        self.client = client

    async def _async_update_data(self):
        try:
            return await self.client.fetch()
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("OpenCode Go API key rejected") from err
        except EntitlementError as err:
            raise UpdateFailed("OpenCode Go subscription is not available for this key") from err
        except ProviderError as err:
            raise UpdateFailed("OpenCode Go usage request failed") from err
