"""Shared device information for the integration's own entities."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def hub_device_info() -> DeviceInfo:
    """The service device holding integration-wide settings and controls.

    Provider entries get their own devices; this one carries only knobs that
    apply to every provider, so its name does not mention one of them.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, "hub")},
        name="LLM Subscription Limits",
        manufacturer="y-decimal",
        model="Integration settings",
        entry_type=DeviceEntryType.SERVICE,
    )
