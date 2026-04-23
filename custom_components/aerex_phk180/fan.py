"""Fan-Plattform für Aerex PHK180 – Lüftungsstufen.

Steuerung via: POST/GET index.htm mit Parameter P[225][0] = 0..4
  0 = Aus
  1 = Feuchteschutz Lüftung
  2 = Reduzierte Lüftung
  3 = Nennlüftung
  4 = Intensivlüftung
"""
from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerexCoordinator
from .const import DOMAIN, MANUFACTURER, MODEL

# Lüftungsstufen: Name im CGX → Gerätewert
STUFE_NAME_TO_VALUE = {
    "Aus":          0,
    "Feuchteschutz": 1,
    "Reduziert":    2,
    "Nenn":         3,
    "Intensiv":     4,
}

# Prozentwerte für HA Fan-Entity (gleichmäßig verteilt auf 5 Stufen)
STUFE_VALUE_TO_PCT = {
    0: 0,
    1: 25,
    2: 50,
    3: 75,
    4: 100,
}

PCT_TO_STUFE_VALUE = {
    0:   0,
    25:  1,
    50:  2,
    75:  3,
    100: 4,
}

PRESET_MODES = ["Aus", "Feuchteschutz", "Reduziert", "Nenn", "Intensiv"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AerexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AerexFan(coordinator, entry)])


class AerexFan(CoordinatorEntity[AerexCoordinator], FanEntity):
    """Lüftungsstufen-Steuerung der Aerex PHK180."""

    _attr_has_entity_name = True
    _attr_name = "Lüftung"
    _attr_icon = "mdi:air-filter"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = PRESET_MODES
    _attr_speed_count = 4   # 4 aktive Stufen (ohne Aus)

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fan"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Aerex {MODEL}",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    def _current_stufe_value(self) -> int:
        """Gibt den numerischen Stufenwert (0–4) zurück."""
        name = self.coordinator.data.fan_mode or "Aus"
        return STUFE_NAME_TO_VALUE.get(name, 0)

    async def _set_stufe(self, value: int) -> None:
        """Sendet die Lüftungsstufe ans Gerät."""
        await self.coordinator.client.async_set_luftstufe(value)
        await self.coordinator.async_request_refresh()

    # --- State ---

    @property
    def is_on(self) -> bool:
        return self._current_stufe_value() > 0

    @property
    def percentage(self) -> int | None:
        return STUFE_VALUE_TO_PCT.get(self._current_stufe_value())

    @property
    def preset_mode(self) -> str | None:
        return self.coordinator.data.fan_mode or "Aus"

    # --- Commands ---

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs) -> None:
        if preset_mode:
            value = STUFE_NAME_TO_VALUE.get(preset_mode, 3)
        elif percentage is not None:
            # Nächste Stufe zum gewünschten Prozentsatz finden
            value = min(PCT_TO_STUFE_VALUE.items(), key=lambda x: abs(x[0] - percentage))[1]
            value = max(value, 1)   # mindestens Feuchteschutz, nicht Aus
        else:
            value = 3               # Default: Nennlüftung
        await self._set_stufe(value)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_stufe(0)

    async def async_set_percentage(self, percentage: int) -> None:
        value = min(PCT_TO_STUFE_VALUE.items(), key=lambda x: abs(x[0] - percentage))[1]
        await self._set_stufe(value)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        value = STUFE_NAME_TO_VALUE.get(preset_mode, 3)
        await self._set_stufe(value)
