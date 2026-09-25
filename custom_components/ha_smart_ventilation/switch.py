"""Switch Plattform: 'Sommermodus' pro Raum (pausiert automatisch die Heizung)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_HEATING_ENTITY,
    CONF_HEATING_USE_TEMP_SOURCE,
    CONF_ROOM_NAME,
    SUMMER_MODE_UNIQUE_ID_SUFFIX,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt die Sommermodus-switch-Entität nur für Räume mit konfigurierter
    Heizung an (kein Zweck ohne Heizung, siehe binary_sensor.py:
    _update_summer_mode())."""
    if entry.data.get(CONF_HEATING_ENTITY) or entry.data.get(
        CONF_HEATING_USE_TEMP_SOURCE
    ):
        async_add_entities([SmartClimateSummerModeSwitch(entry)])


class SmartClimateSummerModeSwitch(SwitchEntity, RestoreEntity):
    """An = Sommermodus aktiv, die Heizung dieses Raums pausiert (Standby).

    Rein passive Entität ohne eigene Steuerungslogik - der eigentliche
    Automatik-Entscheid (Vorhersage-Temperatur gegen Schwelle, siehe
    CONF_SUMMER_MODE_FORECAST_ENTITY/CONF_SUMMER_MODE_THRESHOLD_TEMP)
    passiert im Haupt-Sensor des Raums (binary_sensor.py:
    _update_summer_mode()), der diese Entität wie jedes andere Gerät über
    einen normalen switch.turn_on/switch.turn_off-Serviceaufruf schaltet -
    dieselbe Instanz nimmt gleichermaßen einen manuellen Schaltvorgang über
    die Oberfläche entgegen (async_turn_on/async_turn_off), es gibt also nur
    EINEN Zustand, nicht zwei getrennte "automatisch" und "manuell"
    Zustände. Ein manueller Schaltvorgang bleibt dadurch bestehen, bis die
    Automatik ihn selbst wieder überschreibt (Hysterese in
    _update_summer_mode() - identisches Idempotenz-Muster wie bei
    Luftentfeuchter/Klimaanlage/Heizung: ein bereits erreichter Zielzustand
    wird nicht erneut per Serviceaufruf gesetzt)."""

    _attr_should_poll = False
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, entry: ConfigEntry) -> None:
        room = entry.data[CONF_ROOM_NAME]
        self._attr_name = f"{room} Sommermodus"
        self._attr_unique_id = f"{entry.entry_id}_{SUMMER_MODE_UNIQUE_ID_SUFFIX}"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
