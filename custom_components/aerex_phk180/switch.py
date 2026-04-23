"""Switch-Plattform für Aerex PHK180."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Awaitable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerexCoordinator
from .aerex_client import AerexData, AerexPHK180Client
from .const import DOMAIN, MANUFACTURER, MODEL


@dataclass(frozen=True, kw_only=True)
class AerexSwitchDescription(SwitchEntityDescription):
    is_on_fn:  Callable[[AerexData], bool] = lambda d: False
    turn_on_fn:  Callable[[AerexPHK180Client], Awaitable[bool]] = lambda c: c.async_toggle_stosslüftung(True)
    turn_off_fn: Callable[[AerexPHK180Client], Awaitable[bool]] = lambda c: c.async_toggle_stosslüftung(False)


SWITCHES: tuple[AerexSwitchDescription, ...] = (
    AerexSwitchDescription(
        key="stosslüftung",
        name="Stoßlüftung",
        icon="mdi:weather-windy",
        is_on_fn=lambda d: d.stosslüftung_aktiv,
        turn_on_fn=lambda c: c.async_toggle_stosslüftung(True),
        turn_off_fn=lambda c: c.async_toggle_stosslüftung(False),
    ),
    AerexSwitchDescription(
        key="jahreszeit_sommer",
        name="Sommerbetrieb",
        icon="mdi:weather-sunny",
        is_on_fn=lambda d: (d.jahreszeit or 0) == 1,
        turn_on_fn=lambda c: c.async_toggle_jahreszeit(True),
        turn_off_fn=lambda c: c.async_toggle_jahreszeit(False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AerexCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(AerexSwitch(coordinator, desc, entry) for desc in SWITCHES)


class AerexSwitch(CoordinatorEntity[AerexCoordinator], SwitchEntity):
    entity_description: AerexSwitchDescription
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
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs) -> None:
        await self.entity_description.turn_on_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.entity_description.turn_off_fn(self.coordinator.client)
        await self.coordinator.async_request_refresh()
