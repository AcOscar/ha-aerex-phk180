"""Sensor-Plattform für Aerex PHK180."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfTime,
    REVOLUTIONS_PER_MINUTE,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerexCoordinator
from .aerex_client import AerexData
from .const import DOMAIN, MANUFACTURER, MODEL


@dataclass(frozen=True, kw_only=True)
class AerexSensorDescription(SensorEntityDescription):
    value_fn: Callable[[AerexData], float | int | str | None] = lambda d: None


SENSORS: tuple[AerexSensorDescription, ...] = (
    # Temperaturen
    AerexSensorDescription(
        key="temp_raum",
        name="Raumtemperatur",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.temp_raum,
    ),
    AerexSensorDescription(
        key="soll_temp_raum",
        name="Raumsolltemperatur",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.soll_temp_raum,
    ),
    AerexSensorDescription(
        key="absenktemperatur",
        name="Absenktemperatur",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.absenktemperatur,
    ),
    AerexSensorDescription(
        key="t_lufteintritt",
        name="T-Lufteintritt Gerät",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.t_lufteintritt,
    ),
    AerexSensorDescription(
        key="temp_zuluft",
        name="T-Zuluft",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.temp_zuluft,
    ),
    AerexSensorDescription(
        key="t_abluft",
        name="T-Abluft",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.t_abluft,
    ),
    AerexSensorDescription(
        key="he_wws_te",
        name="Warmwasserspeicher oben",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.he_wws_te,
    ),
    AerexSensorDescription(
        key="he_wws_tw",
        name="Warmwasserspeicher unten",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.he_wws_tw,
    ),
    AerexSensorDescription(
        key="t_verdampfer",
        name="T-Verdampfer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.t_verdampfer,
    ),
    AerexSensorDescription(
        key="wws_t_soll",
        name="Warmwassersolltemperatur",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.wws_t_soll,
    ),
    # Lüftung
    AerexSensorDescription(
        key="drehzahl_zu",
        name="Drehzahl Zuluft",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        value_fn=lambda d: d.drehzahl_zu,
    ),
    AerexSensorDescription(
        key="drehzahl_ab",
        name="Drehzahl Abluft",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        value_fn=lambda d: d.drehzahl_ab,
    ),
    AerexSensorDescription(
        key="volumenstrom",
        name="Volumenstrom",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="m³/h",
        value_fn=lambda d: d.volumenstrom,
    ),
    AerexSensorDescription(
        key="betriebsart",
        name="Betriebsart",
        value_fn=lambda d: d.betriebsartstring,
    ),
    AerexSensorDescription(
        key="fan_mode",
        name="Lüftungsstufe",
        value_fn=lambda d: d.fan_mode,
    ),
    AerexSensorDescription(
        key="bypass",
        name="Bypass",
        value_fn=lambda d: d.bypass_zustand,
    ),
    # CO2
    AerexSensorDescription(
        key="co2_sensor1",
        name="CO₂ Sensor 1",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda d: d.co2_sensor1,
    ),
    AerexSensorDescription(
        key="co2_sensor2",
        name="CO₂ Sensor 2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda d: d.co2_sensor2,
    ),
    AerexSensorDescription(
        key="co2_sensor3",
        name="CO₂ Sensor 3",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda d: d.co2_sensor3,
    ),
    AerexSensorDescription(
        key="rh_aktuell",
        name="Relative Feuchte",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.rh_aktuell,
    ),
    # Filter
    AerexSensorDescription(
        key="filter_restlaufzeit_geraet",
        name="Filter Geräte Restlaufzeit",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="d",
        value_fn=lambda d: d.filter_restlaufzeit_geraet,
    ),
    AerexSensorDescription(
        key="filter_restlaufzeit_aussen",
        name="Filter Außen Restlaufzeit",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="d",
        value_fn=lambda d: d.filter_restlaufzeit_aussen,
    ),
    # Betriebsstunden
    AerexSensorDescription(
        key="betriebsstunden_wp",
        name="Betriebsstunden Wärmepumpe",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda d: d.betriebsstunden_wp,
    ),
    AerexSensorDescription(
        key="betriebsstunden_luft",
        name="Betriebsstunden Lüftung gesamt",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda d: d.betriebsstunden_luft,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AerexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(AerexSensor(coordinator, desc, entry) for desc in SENSORS)


class AerexSensor(CoordinatorEntity[AerexCoordinator], SensorEntity):
    entity_description: AerexSensorDescription
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
            "sw_version": coordinator.data.sw_version_lt if coordinator.data else None,
        }

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)
