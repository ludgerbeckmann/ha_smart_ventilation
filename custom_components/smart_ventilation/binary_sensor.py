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
    CONF_CLIMATE_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_MOBILE_NOTIFY_SERVICE,
    CONF_NOTIFY_METHOD,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_ROOM_NAME,
    CONF_SONOS_ENTITY,
    CONF_TEMP_ATTRIBUTE,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_TTS_ENTITY,
    CONF_WINDOW_ENTITY,
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
        return {
            "raum": self._config[CONF_ROOM_NAME],
            "temperatur_quelle": self._config[CONF_CLIMATE_ENTITY],
            "temperatur_attribut": self._config.get(
                CONF_TEMP_ATTRIBUTE, "current_temperature"
            ),
        }

    async def async_added_to_hass(self) -> None:
        """Beobachtet relevante Entitäten und berechnet initialen Zustand."""
        tracked = [self._config[CONF_CLIMATE_ENTITY]]
        for key in (
            CONF_HUMIDITY_ENTITY,
            CONF_OUTDOOR_TEMP_ENTITY,
            CONF_WINDOW_ENTITY,
        ):
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
        climate_entity = self._config[CONF_CLIMATE_ENTITY]
        attribute = self._config.get(CONF_TEMP_ATTRIBUTE, "current_temperature")
        state = self.hass.states.get(climate_entity)
        if state is None:
            return None
        value = state.attributes.get(attribute)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    async def _evaluate(self) -> None:
        """Prüft Schwellenwerte und aktualisiert ggf. den Zustand."""
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
        outdoor_temp = self._get_float_state(
            self._config.get(CONF_OUTDOOR_TEMP_ENTITY)
        )

        temp_open = self._config[CONF_TEMP_THRESHOLD_OPEN]
        temp_close = self._config[CONF_TEMP_THRESHOLD_CLOSE]
        hum_open = self._config[CONF_HUMIDITY_THRESHOLD_OPEN]
        hum_close = self._config[CONF_HUMIDITY_THRESHOLD_CLOSE]

        should_open = False
        should_close = False

        if indoor_temp is not None and indoor_temp >= temp_open:
            # Nur öffnen, wenn draußen kühler ist (oder keine Außentemperatur bekannt ist)
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

    async def _notify(self, should_ventilate: bool) -> None:
        """Verschickt die Benachrichtigung per Sonos-TTS oder App-Push."""
        room = self._config[CONF_ROOM_NAME]
        message = (
            f"Bitte das Fenster im {room} zum Lüften öffnen."
            if should_ventilate
            else f"Bitte das Fenster im {room} wieder schließen."
        )

        method = self._config.get(CONF_NOTIFY_METHOD, NOTIFY_METHOD_MOBILE)

        if method == NOTIFY_METHOD_SONOS:
            sonos_entity = self._config.get(CONF_SONOS_ENTITY)
            tts_entity = self._config.get(CONF_TTS_ENTITY)
            if sonos_entity and tts_entity:
                await self.hass.services.async_call(
                    "tts",
                    "speak",
                    {
                        "entity_id": tts_entity,
                        "media_player_entity_id": sonos_entity,
                        "message": message,
                    },
                    blocking=False,
                )
            else:
                _LOGGER.warning(
                    "Sonos-Benachrichtigung konfiguriert, aber Sonos- oder TTS-Entity fehlt (%s)",
                    room,
                )
        else:
            service = self._config.get(CONF_MOBILE_NOTIFY_SERVICE)
            if service:
                await self.hass.services.async_call(
                    "notify",
                    service,
                    {
                        "title": "Lüften",
                        "message": message,
                    },
                    blocking=False,
                )
            else:
                _LOGGER.warning(
                    "Keine mobile Notify-Service für Raum %s konfiguriert", room
                )
