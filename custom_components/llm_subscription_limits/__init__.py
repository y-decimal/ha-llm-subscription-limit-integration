"""LLM subscription limits integration."""

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import GoCoordinator
from .providers.opencode_go import OpenCodeGoClient

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass, entry):
    """Set up one independent provider entry."""
    client = OpenCodeGoClient(async_get_clientsession(hass), entry.data[CONF_API_KEY])
    coordinator = GoCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload the provider."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
