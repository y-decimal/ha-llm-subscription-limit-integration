"""Integration-wide controls, attached to the service device."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import callback

from .const import (
    DATA_HUB_ENTITIES,
    DATA_SETTINGS,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .device import hub_device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Add the poll interval once, not once per provider entry."""
    domain_data = hass.data[DOMAIN]
    created = domain_data.setdefault(DATA_HUB_ENTITIES, set())
    if "number" in created:
        return
    created.add("number")
    async_add_entities([PollIntervalNumber(domain_data[DATA_SETTINGS])])


class PollIntervalNumber(NumberEntity):
    """How often every provider is polled, in minutes."""

    _attr_has_entity_name = True
    _attr_name = "Poll interval"
    _attr_icon = "mdi:timer-sync-outline"
    _attr_native_min_value = MIN_SCAN_INTERVAL
    _attr_native_max_value = MAX_SCAN_INTERVAL
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_info = hub_device_info()

    def __init__(self, settings) -> None:
        self._settings = settings
        self._attr_unique_id = f"{DOMAIN}_poll_interval"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._settings.async_add_listener(self._handle_change))

    @callback
    def _handle_change(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        return self._settings.interval_minutes

    async def async_set_native_value(self, value: float) -> None:
        await self._settings.async_set_interval(value)
        self.async_write_ha_state()
