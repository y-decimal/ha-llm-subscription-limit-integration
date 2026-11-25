"""Usage sensors for OpenCode Go."""

import calendar
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

WINDOWS = (("rolling", "Five-hour usage"), ("weekly", "Weekly usage"), ("monthly", "Monthly usage"))


async def async_setup_entry(hass, entry, async_add_entities):
    """Add the current provider's sensors."""
    async_add_entities(GoUsageSensor(entry.runtime_data, key, name) for key, name in WINDOWS)


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
