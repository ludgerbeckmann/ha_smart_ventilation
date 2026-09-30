"""Sensor Plattform: absolute Luftfeuchtigkeit (g/m³) pro Raum und außen.

Die absolute Luftfeuchtigkeit wird - wie schon für die Lüftungsentscheidung
und die Dashboard-Karte - aus Temperatur und relativer Luftfeuchtigkeit über
die Magnus-Formel berechnet (siehe
SmartVentilationBinarySensor._absolute_humidity). Als eigene Entität steht
sie zusätzlich für Verlauf/Diagramme, die Detailansicht (Klick in der
Karte) und Automationen zur Verfügung.

- Pro Raum: "‹Raum› Absolute Luftfeuchtigkeit", nur wenn für den Raum ein
  Luftfeuchtigkeitssensor konfiguriert ist (Innentemperatur/Feuchte aus den
  Raum-Einstellungen).
- Außen: "Außen Absolute Luftfeuchtigkeit", hängt am Eintrag "Smart Climate
  Optionen" und nutzt den dort konfigurierten Außentemperatur-/
  Außenluftfeuchtigkeitssensor.
"""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .binary_sensor import SmartVentilationBinarySensor
from .const import (
    CONF_HUMIDITY_ENTITY,
    CONF_IS_GLOBAL,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_ROOM_NAME,
    CONF_TEMP_ATTRIBUTE,
    CONF_TEMP_SOURCE_ENTITY,
    DEFAULT_TEMP_ATTRIBUTE,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
)

# Der Außensensor liest seine Quellen aus den globalen Einstellungen, die sich
# ohne Neuladen des Eintrags ändern können - der Abruf stellt sicher, dass auch
# eine geänderte Sensorauswahl übernommen wird.
SCAN_INTERVAL = timedelta(minutes=5)

UNIT = "g/m³"


def read_float(hass: HomeAssistant, entity_id: str | None, decimals: int) -> float | None:
    """Liest einen Sensorwert als gerundeten float (None bei fehlend/unbekannt).
    Gleiche Rundung wie in der Entscheidungslogik/Anzeige der Raum-Entität
    (Luftfeuchtigkeit ganzzahlig, Temperatur eine Nachkommastelle)."""
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable"):
        return None
    try:
        return round(float(state.state), decimals)
    except ValueError:
        return None


def read_temperature(
    hass: HomeAssistant, entity_id: str | None, attribute: str | None
) -> float | None:
    """Liest eine Temperatur - bei climate-Entitäten aus dem Attribut
    (Standard current_temperature), sonst aus dem Zustand."""
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    if entity_id.split(".")[0] == "climate":
        value = state.attributes.get(attribute or DEFAULT_TEMP_ATTRIBUTE)
    else:
        if state.state in ("unknown", "unavailable"):
            return None
        value = state.state
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def absolute_humidity(temp_c: float | None, rh_percent: float | None) -> float | None:
    if temp_c is None or rh_percent is None:
        return None
    return round(SmartVentilationBinarySensor._absolute_humidity(temp_c, rh_percent), 1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt je Raum (mit Luftfeuchtigkeitssensor) bzw. für die allgemeinen
    Einstellungen (Außen) den Sensor für die absolute Luftfeuchtigkeit an."""
    if entry.data.get(CONF_IS_GLOBAL):
        async_add_entities([OutdoorAbsoluteHumiditySensor(hass, entry)])
    elif entry.data.get(CONF_HUMIDITY_ENTITY):
        async_add_entities([RoomAbsoluteHumiditySensor(entry)])


class _AbsoluteHumiditySensor(SensorEntity):
    _attr_native_unit_of_measurement = UNIT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:water-percent"

    def _source_entities(self) -> list[str]:
        raise NotImplementedError

    def _subscribe(self) -> None:
        """(Neu) abonnieren: Zustandswechsel der Quell-Entitäten."""
        sources = tuple(e for e in self._source_entities() if e)
        if sources == getattr(self, "_subscribed", None):
            return
        unsub = getattr(self, "_unsub", None)
        if unsub is not None:
            unsub()
            self._unsub = None
        self._subscribed = sources
        if sources:
            self._unsub = async_track_state_change_event(
                self.hass, list(sources), self._handle_source_change
            )

    @callback
    def _handle_source_change(self, event) -> None:
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._subscribe()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        unsub = getattr(self, "_unsub", None)
        if unsub is not None:
            unsub()
            self._unsub = None


class RoomAbsoluteHumiditySensor(_AbsoluteHumiditySensor):
    """Absolute Luftfeuchtigkeit eines Raums (aus Innentemperatur + Feuchte)."""

    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._config = entry.data
        self._attr_name = f"{entry.data[CONF_ROOM_NAME]} Absolute Luftfeuchtigkeit"
        self._attr_unique_id = f"{entry.entry_id}_absolute_luftfeuchtigkeit"

    def _source_entities(self) -> list[str]:
        return [
            self._config.get(CONF_TEMP_SOURCE_ENTITY),
            self._config.get(CONF_HUMIDITY_ENTITY),
        ]

    @property
    def native_value(self) -> float | None:
        return absolute_humidity(
            read_temperature(
                self.hass,
                self._config.get(CONF_TEMP_SOURCE_ENTITY),
                self._config.get(CONF_TEMP_ATTRIBUTE),
            ),
            read_float(self.hass, self._config.get(CONF_HUMIDITY_ENTITY), 0),
        )


class OutdoorAbsoluteHumiditySensor(_AbsoluteHumiditySensor):
    """Absolute Außenluftfeuchtigkeit (aus den globalen Außensensoren)."""

    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry_id = entry.entry_id
        self._attr_name = "Außen Absolute Luftfeuchtigkeit"
        self._attr_unique_id = f"{entry.entry_id}_aussen_absolute_luftfeuchtigkeit"

    def _global_config(self) -> dict:
        domain_data = self.hass.data.get(DOMAIN, {})
        return domain_data.get(self._entry_id) or {}

    def _source_entities(self) -> list[str]:
        config = self._global_config()
        return [config.get(CONF_OUTDOOR_TEMP_ENTITY), config.get(CONF_OUTDOOR_HUMIDITY_ENTITY)]

    async def async_update(self) -> None:
        # Geänderte Sensorauswahl in den globalen Einstellungen übernehmen.
        self._subscribe()

    @property
    def native_value(self) -> float | None:
        config = self._global_config()
        return absolute_humidity(
            read_temperature(self.hass, config.get(CONF_OUTDOOR_TEMP_ENTITY), None),
            read_float(self.hass, config.get(CONF_OUTDOOR_HUMIDITY_ENTITY), 0),
        )
