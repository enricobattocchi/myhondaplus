"""My Honda+ integration for Home Assistant."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import HondaDataUpdateCoordinator
from .data import MyHondaPlusConfigEntry, MyHondaPlusData

PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: MyHondaPlusConfigEntry) -> bool:
    """Set up My Honda+ from a config entry."""
    coordinator = HondaDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MyHondaPlusData(coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MyHondaPlusConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: MyHondaPlusConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
