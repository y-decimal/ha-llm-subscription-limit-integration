"""LLM subscription limits integration."""

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DATA_COORDINATORS, DATA_SETTINGS, DOMAIN
from .coordinator import GoCoordinator
from .providers.opencode_go import OpenCodeGoClient
from .settings import Settings

PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.BUTTON]


async def async_setup_entry(hass, entry):
    """Set up one independent provider entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    settings = domain_data.get(DATA_SETTINGS)
    if settings is None:
        settings = Settings(hass)
        await settings.async_load()
        domain_data[DATA_SETTINGS] = settings
        domain_data[DATA_COORDINATORS] = set()

    client = OpenCodeGoClient(async_get_clientsession(hass), entry.data[CONF_API_KEY])
    coordinator = GoCoordinator(hass, entry, client, settings.interval)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    domain_data[DATA_COORDINATORS].add(coordinator)

    def _interval_changed() -> None:
        # Assigning update_interval reschedules the next refresh.
        coordinator.update_interval = settings.interval

    entry.async_on_unload(settings.async_add_listener(_interval_changed))
    entry.async_on_unload(lambda: domain_data[DATA_COORDINATORS].discard(coordinator))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload the provider."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
