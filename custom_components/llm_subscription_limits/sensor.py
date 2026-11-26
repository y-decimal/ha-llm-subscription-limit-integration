"""Usage sensors for OpenCode Go."""

import calendar
from datetime import timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATORS, DATA_HUB_ENTITIES, DOMAIN
from .device import hub_device_info

WINDOWS = (("rolling", "Five-hour usage"), ("weekly", "Weekly usage"), ("monthly", "Monthly usage"))


async def async_setup_entry(hass, entry, async_add_entities):
    """Add the current provider's sensors, plus the shared refresh timer once."""
    async_add_entities(GoUsageSensor(entry.runtime_data, key, name) for key, name in WINDOWS)

    domain_data = hass.data[DOMAIN]
    created = domain_data.setdefault(DATA_HUB_ENTITIES, set())
    if "next_refresh" not in created:
        created.add("next_refresh")
        async_add_entities([NextRefreshSensor(hass)])


class GoUsageSensor(CoordinatorEntity, SensorEntity):
    """One Go usage percentage and reset."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-donut"
    _attr_device_info = {"identifiers": {(DOMAIN, "opencode_go")}, "name": "OpenCode Go",
                         "manufacturer": "OpenCode"}

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"opencode_go_{key}_usage"

    @property
    def native_value(self):
        return self.coordinator.data[self._key].percent

    @property
    def extra_state_attributes(self):
        window = self.coordinator.data[self._key]
        reset = window.resets_at
        if self._key == "monthly":
            year, month = (reset.year, reset.month - 1) if reset.month > 1 else (reset.year - 1, 12)
            start = reset.replace(year=year, month=month, day=min(reset.day, calendar.monthrange(year, month)[1]))
        else:
            start = reset - timedelta(hours=5) if self._key == "rolling" else reset - timedelta(days=7)
        return {"status": window.status, "resets_at": reset.isoformat(),
                "window_started_at": start.isoformat()}


class NextRefreshSensor(SensorEntity):
    """When the next poll is due, across every provider.

    This is the single source of truth for the UI: the badge counts down from
    this timestamp instead of inferring a cadence from the usage sensors.
    """

    _attr_has_entity_name = True
    _attr_name = "Next refresh"
    _attr_icon = "mdi:timer-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_info = hub_device_info()
    _attr_unique_id = f"{DOMAIN}_next_refresh"

    def __init__(self, hass) -> None:
        self.hass = hass

    async def async_added_to_hass(self) -> None:
        for coordinator in list(self.hass.data[DOMAIN][DATA_COORDINATORS]):
            self.async_on_remove(coordinator.async_add_listener(self._handle_change))
        self.async_on_remove(
            self.hass.data[DOMAIN]["settings"].async_add_listener(self._handle_change)
        )

    def _handle_change(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Earliest next refresh among providers; None until one has polled."""
        due = []
        for coordinator in self.hass.data[DOMAIN][DATA_COORDINATORS]:
            if coordinator.last_refresh_at and coordinator.update_interval:
                due.append(coordinator.last_refresh_at + coordinator.update_interval)
        if not due:
            return None
        return min(due)
