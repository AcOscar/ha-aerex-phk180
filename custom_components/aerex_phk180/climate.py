"""Climate Plattform für Aerex PHK180 – Raumtemperatur + Betriebsart."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerexCoordinator
from .const import DOMAIN, MANUFACTURER, MODEL

# Betriebsart-Wert (P[522][0]) → HVAC-Mode
# 0=Aus, 1=Warmwasser, 2=Manuell, 3=Auto Zeit, 4=Auto Sensor, 6=Unfall
BETRIEBSART_TO_HVAC = {
    0: HVACMode.OFF,
    1: HVACMode.OFF,      # Nur Warmwasser, keine Raumheizung
    2: HVACMode.HEAT,     # Manuell
    3: HVACMode.AUTO,     # Auto Zeit
    4: HVACMode.AUTO,     # Auto Sensor
    6: HVACMode.HEAT,     # Unfall-/Notbetrieb
}

HVAC_TO_BETRIEBSART = {
    HVACMode.OFF:  0,   # Aus
    HVACMode.HEAT: 2,   # Manuell
    HVACMode.AUTO: 3,   # Auto Zeit (bevorzugt)
}

# Preset-Namen für die 6 echten Betriebsarten
PRESET_AUS          = "Aus"
PRESET_WARMWASSER   = "Warmwasser"
PRESET_MANUELL      = "Manuell"
PRESET_AUTO_ZEIT    = "Auto Zeit"
PRESET_AUTO_SENSOR  = "Auto Sensor"
PRESET_UNFALL       = "Unfall"

BETRIEBSART_TO_PRESET = {
    0: PRESET_AUS,
    1: PRESET_WARMWASSER,
    2: PRESET_MANUELL,
    3: PRESET_AUTO_ZEIT,
    4: PRESET_AUTO_SENSOR,
    6: PRESET_UNFALL,
}

PRESET_TO_BETRIEBSART = {v: k for k, v in BETRIEBSART_TO_PRESET.items()}

ALL_PRESETS = list(BETRIEBSART_TO_PRESET.values())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AerexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AerexClimate(coordinator, entry)])


class AerexClimate(CoordinatorEntity[AerexCoordinator], ClimateEntity):
    """Raumklima-Steuerung der PHK180: Solltemperatur + Betriebsart."""

    _attr_has_entity_name = True
    _attr_name = "Raumklima"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 15.0
    _attr_max_temp = 30.0
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
    _attr_preset_modes = ALL_PRESETS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Aerex {MODEL}",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.temp_raum

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.soll_temp_raum

    @property
    def hvac_mode(self) -> HVACMode:
        mode = self.coordinator.data.betriebsmode or 0
        return BETRIEBSART_TO_HVAC.get(mode, HVACMode.AUTO)

    @property
    def preset_mode(self) -> str | None:
        mode = self.coordinator.data.betriebsmode or 0
        return BETRIEBSART_TO_PRESET.get(mode, PRESET_AUTO_ZEIT)

    async def async_set_temperature(self, **kwargs) -> None:
        ziel = kwargs.get("temperature")
        aktuell = self.coordinator.data.soll_temp_raum
        if ziel is not None and aktuell is not None:
            await self.coordinator.client.async_set_raumsolltemperatur(ziel, aktuell)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        betriebsart = HVAC_TO_BETRIEBSART.get(hvac_mode, 3)
        await self.coordinator.client.async_set_betriebsart(betriebsart)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        betriebsart = PRESET_TO_BETRIEBSART.get(preset_mode, 3)
        await self.coordinator.client.async_set_betriebsart(betriebsart)
        await self.coordinator.async_request_refresh()
