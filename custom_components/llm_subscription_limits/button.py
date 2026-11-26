"""Refresh control, attached to the service device."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .const import DATA_COORDINATORS, DATA_HUB_ENTITIES, DOMAIN
from .device import hub_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Add the refresh button once, not once per provider entry."""
    domain_data = hass.data[DOMAIN]
    created = domain_data.setdefault(DATA_HUB_ENTITIES, set())
    if "button" in created:
        return
    created.add("button")
    async_add_entities([RefreshNowButton(hass)])


class RefreshNowButton(ButtonEntity):
    """Fetch every provider immediately instead of waiting for the interval."""

    _attr_has_entity_name = True
    _attr_name = "Refresh now"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_info = hub_device_info()

    def __init__(self, hass) -> None:
        self.hass = hass
        self._attr_unique_id = f"{DOMAIN}_refresh_now"

    async def async_press(self) -> None:
        # One provider failing must not stop the others from refreshing.
        for coordinator in list(self.hass.data[DOMAIN][DATA_COORDINATORS]):
            try:
                await coordinator.async_refresh()
            except Exception:  # noqa: BLE001 - surfaced by the coordinator itself
                continue
