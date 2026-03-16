"""Number platform for My Honda+ (charge limits)."""

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VIN, DOMAIN
from .coordinator import HondaDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HondaNumberDescription(NumberEntityDescription):
    limit_key: str = ""


NUMBER_DESCRIPTIONS: list[HondaNumberDescription] = [
    HondaNumberDescription(
        key="charge_limit_home",
        translation_key="charge_limit_home",
        icon="mdi:battery-charging-80",
        native_min_value=80,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        limit_key="home",
    ),
    HondaNumberDescription(
        key="charge_limit_away",
        translation_key="charge_limit_away",
        icon="mdi:battery-charging-90",
        native_min_value=80,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        limit_key="away",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HondaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    vin = entry.data[CONF_VIN]
    async_add_entities(
        HondaChargeLimitNumber(coordinator, description, vin)
        for description in NUMBER_DESCRIPTIONS
    )


class HondaChargeLimitNumber(
    CoordinatorEntity[HondaDataUpdateCoordinator], NumberEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HondaDataUpdateCoordinator,
        description: HondaNumberDescription,
        vin: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"
        self._vin = vin

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._vin)},
            name=f"Honda {self._vin[-6:]}",
            manufacturer="Honda",
        )

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data.get(self.entity_description.key)
        return float(val) if val is not None else None

    @property
    def assumed_state(self) -> bool:
        return False

    async def async_set_native_value(self, value: float) -> None:
        data = self.coordinator.data or {}
        home = data.get("charge_limit_home", 80)
        away = data.get("charge_limit_away", 90)

        if self.entity_description.limit_key == "home":
            home = int(value)
        else:
            away = int(value)

        await self.coordinator.async_send_command(
            self.coordinator.api.set_charge_limit, self._vin, home, away,
        )

        if self.coordinator.data is not None:
            self.coordinator.data[self.entity_description.key] = int(value)
            self.async_write_ha_state()
