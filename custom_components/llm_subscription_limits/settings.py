"""Integration-wide settings that outlive any single provider entry."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DEFAULT_SCAN_INTERVAL, MAX_SCAN_INTERVAL, MIN_SCAN_INTERVAL, STORAGE_VERSION

STORAGE_KEY = "llm_subscription_limits.settings"


class Settings:
    """Poll interval shared by every provider coordinator.

    A config entry belongs to one provider, so a global value cannot live in
    entry options. Per-provider overrides can be layered on top later without
    moving this value.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._interval = DEFAULT_SCAN_INTERVAL
        self._listeners: list[Callable[[], None]] = []

    async def async_load(self) -> None:
        """Read the stored interval, tolerating a missing or corrupt file."""
        try:
            data = await self._store.async_load() or {}
            self._interval = self._clamp(data.get("scan_interval", DEFAULT_SCAN_INTERVAL))
        except (TypeError, ValueError):
            self._interval = DEFAULT_SCAN_INTERVAL

    @staticmethod
    def _clamp(value) -> int:
        try:
            minutes = int(value)
        except (TypeError, ValueError):
            return DEFAULT_SCAN_INTERVAL
        return max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, minutes))

    @property
    def interval_minutes(self) -> int:
        return self._interval

    @property
    def interval(self) -> timedelta:
        return timedelta(minutes=self._interval)

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for interval changes; returns the remover."""
        self._listeners.append(listener)

        def _remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _remove

    async def async_set_interval(self, minutes) -> None:
        """Store a new interval and notify the coordinators."""
        value = self._clamp(minutes)
        if value == self._interval:
            return
        self._interval = value
        await self._store.async_save({"scan_interval": value})
        for listener in list(self._listeners):
            listener()
