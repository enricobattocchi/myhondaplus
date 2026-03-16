"""Sensor platform for My Honda+."""

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VIN, DOMAIN
from .coordinator import HondaDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HondaSensorDescription(SensorEntityDescription):
    pass


SENSOR_DESCRIPTIONS: list[HondaSensorDescription] = [
    HondaSensorDescription(
        key="battery_level",
        translation_key="battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HondaSensorDescription(
        key="range_km",
        translation_key="range",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
    ),
    HondaSensorDescription(
        key="charge_status",
        translation_key="charge_status",
        icon="mdi:ev-station",
    ),
    HondaSensorDescription(
        key="plug_status",
        translation_key="plug_status",
        icon="mdi:power-plug",
    ),
    HondaSensorDescription(
        key="climate_active",
        translation_key="climate_active",
        icon="mdi:air-conditioner",
    ),
    HondaSensorDescription(
        key="cabin_temp_c",
        translation_key="cabin_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HondaSensorDescription(
        key="odometer_km",
        translation_key="odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    HondaSensorDescription(
        key="doors_locked",
        translation_key="doors_locked",
        icon="mdi:car-door-lock",
    ),
    HondaSensorDescription(
        key="all_windows_closed",
        translation_key="windows_closed",
        icon="mdi:car-door",
    ),
    HondaSensorDescription(
        key="timestamp",
        translation_key="last_updated",
        icon="mdi:clock-outline",
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
        HondaSensor(coordinator, description, vin)
        for description in SENSOR_DESCRIPTIONS
    )


class HondaSensor(CoordinatorEntity[HondaDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HondaDataUpdateCoordinator,
        description: HondaSensorDescription,
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
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)
