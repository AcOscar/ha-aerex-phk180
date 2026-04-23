"""Binary Sensor Plattform für Aerex PHK180."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerexCoordinator
from .aerex_client import AerexData
from .const import DOMAIN, MANUFACTURER, MODEL


@dataclass(frozen=True, kw_only=True)
class AerexBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[AerexData], bool | None] = lambda d: None


BINARY_SENSORS: tuple[AerexBinarySensorDescription, ...] = (
    AerexBinarySensorDescription(
        key="heat_pump",
        name="Wärmepumpe",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.heat_pump_aktiv,
    ),
    AerexBinarySensorDescription(
        key="ehz",
        name="Elektroheizstab",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.ehz_aktiv,
    ),
    AerexBinarySensorDescription(
        key="stosslüftung",
        name="Stoßlüftung aktiv",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.stosslüftung_aktiv,
    ),
    AerexBinarySensorDescription(
        key="filter_geraet",
        name="Filterwechsel Gerät",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.filter_meldung_geraet,
    ),
    AerexBinarySensorDescription(
        key="filter_aussen",
        name="Filterwechsel Außen",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.filter_meldung_aussen,
    ),
    AerexBinarySensorDescription(
        key="fehler",
        name="Störung",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.error_id != 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AerexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(AerexBinarySensor(coordinator, desc, entry) for desc in BINARY_SENSORS)


class AerexBinarySensor(CoordinatorEntity[AerexCoordinator], BinarySensorEntity):
    entity_description: AerexBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, entry):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Aerex {MODEL}",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)
