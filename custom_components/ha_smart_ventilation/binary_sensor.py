"""Binary Sensor Plattform: 'Lüften empfohlen' pro Raum."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_MOBILE_NOTIFY_ENTITY,
    CONF_NOTIFY_METHOD,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_ROOM_NAME,
    CONF_SONOS_ENTITY,
    CONF_TEMP_ATTRIBUTE,
    CONF_TEMP_SOURCE_ENTITY,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_TTS_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_TEMP_ATTRIBUTE,
    NOTIFY_METHOD_MOBILE,
    NOTIFY_METHOD_SONOS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt die binary_sensor Entität für den konfigurierten Raum an."""
    async_add_entities([SmartVentilationBinarySensor(hass, entry)])


class SmartVentilationBinarySensor(BinarySensorEntity):
    """True = Lüften wird gerade empfohlen (Fenster sollte offen sein)."""

    _attr_device_class = BinarySensorDeviceClass.OPENING
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._config = entry.data
        room = self._config[CONF_ROOM_NAME]

        self._attr_name = f"Lüften empfohlen {room}"
        self._attr_unique_id = f"{entry.entry_id}_lueften_empfohlen"
        self._attr_is_on = False

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {
            "raum": self._config[CONF_ROOM_NAME],
            "temperatur_quelle": self._config[CONF_TEMP_SOURCE_ENTITY],
        }
        if self._config.get(CONF_TEMP_ATTRIBUTE):
            attrs["temperatur_attribut"] = self._config[CONF_TEMP_ATTRIBUTE]
        return attrs

    async def async_added_to_hass(self) -> None:
        """Beobachtet relevante Entitäten und berechnet initialen Zustand."""
        tracked = [
            self._config[CONF_TEMP_SOURCE_ENTITY],
            self._config[CONF_OUTDOOR_TEMP_ENTITY],
        ]
        for key in (CONF_HUMIDITY_ENTITY, CONF_WINDOW_ENTITY):
            value = self._config.get(key)
            if value:
                tracked.append(value)

        self.async_on_remove(
            async_track_state_change_event(self.hass, tracked, self._handle_state_change)
        )
        await self._evaluate()

    @callback
    def _handle_state_change(self, event: Event) -> None:
        self.hass.async_create_task(self._evaluate())

    def _get_float_state(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _get_indoor_temperature(self) -> float | None:
        entity_id = self._config[CONF_TEMP_SOURCE_ENTITY]
        domain = entity_id.split(".")[0]
        state = self.hass.states.get(entity_id)
        if state is None:
            return None

        if domain == "climate":
            attribute = self._config.get(CONF_TEMP_ATTRIBUTE) or DEFAULT_TEMP_ATTRIBUTE
            value = state.attributes.get(attribute)
        else:
            # sensor / number / input_number: Zustand direkt als Temperatur lesen
            if state.state in ("unknown", "unavailable"):
                return None
            value = state.state

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def _evaluate(self) -> None:
        """Prüft Schwellenwerte und aktualisiert ggf. den Zustand."""
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
        outdoor_temp = self._get_float_state(self._config[CONF_OUTDOOR_TEMP_ENTITY])

        temp_open = self._config[CONF_TEMP_THRESHOLD_OPEN]
        temp_close = self._config[CONF_TEMP_THRESHOLD_CLOSE]
        hum_open = self._config[CONF_HUMIDITY_THRESHOLD_OPEN]
        hum_close = self._config[CONF_HUMIDITY_THRESHOLD_CLOSE]

        should_open = False
        should_close = False

        if indoor_temp is not None and indoor_temp >= temp_open:
            # Nur öffnen, wenn draußen kühler ist als drinnen (oder Außenwert
            # gerade nicht verfügbar ist)
            if outdoor_temp is None or outdoor_temp < indoor_temp:
                should_open = True
        if humidity is not None and humidity >= hum_open:
            should_open = True

        if indoor_temp is not None and indoor_temp <= temp_close:
            should_close = True
        if humidity is not None and humidity <= hum_close:
            should_close = True

        new_state = self._attr_is_on
        if should_open and not self._attr_is_on:
            new_state = True
        elif should_close and self._attr_is_on:
            new_state = False

        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self.async_write_ha_state()
            await self._notify(new_state)

    @staticmethod
    def _as_list(value) -> list:
        """Normalisiert Config-Werte zu einer Liste (abwärtskompatibel zu
        älteren Konfigurationen, die noch einen einzelnen String speichern)."""
        if not value:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    async def _notify(self, should_ventilate: bool) -> None:
        """Verschickt die Benachrichtigung per Sonos-TTS und/oder App-Push.

        Beide Methoden können gleichzeitig konfiguriert sein, und jede
        Methode kann mehrere Ziel-Entitäten haben (mehrere Sonos-Lautsprecher
        bzw. mehrere notify.*-Entitäten) - in dem Fall werden alle bedient.
        """
        room = self._config[CONF_ROOM_NAME]
        message = (
            f"Bitte das Fenster im {room} zum Lüften öffnen."
            if should_ventilate
            else f"Bitte das Fenster im {room} wieder schließen."
        )

        methods = self._config.get(CONF_NOTIFY_METHOD) or []

        if NOTIFY_METHOD_SONOS in methods:
            sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
            tts_entity = self._config.get(CONF_TTS_ENTITY)
            if sonos_entities and tts_entity:
                await self.hass.services.async_call(
                    "tts",
                    "speak",
                    {
                        "entity_id": tts_entity,
                        "media_player_entity_id": sonos_entities,
                        "message": message,
                    },
                    blocking=False,
                )
            else:
                _LOGGER.warning(
                    "Sonos-Benachrichtigung konfiguriert, aber Sonos- oder "
                    "TTS-Entity fehlt (%s)",
                    room,
                )

        if NOTIFY_METHOD_MOBILE in methods:
            notify_entities = self._as_list(self._config.get(CONF_MOBILE_NOTIFY_ENTITY))
            if notify_entities:
                await self.hass.services.async_call(
                    "notify",
                    "send_message",
                    {
                        "entity_id": notify_entities,
                        "title": "Lüften",
                        "message": message,
                    },
                    blocking=False,
                )
            else:
                _LOGGER.warning(
                    "Keine notify-Entität für Raum %s konfiguriert", room
                )
