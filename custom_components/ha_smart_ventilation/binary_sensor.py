"""Binary Sensor Plattform: 'Lüften empfohlen' pro Raum."""
from __future__ import annotations

import logging
import math
from collections import deque
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AC_ENTITY,
    CONF_CO2_ENTITY,
    CONF_CO2_THRESHOLD_CLOSE,
    CONF_CO2_THRESHOLD_OPEN,
    CONF_DEHUMIDIFIER_ENTITY,
    CONF_FROST_DEBOUNCE_MINUTES,
    CONF_FROST_PROTECTION_TEMP,
    CONF_HEAT_PROTECTION_TEMP,
    CONF_NO_WINDOW,
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_PRIORITY_OVER_DURATION,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_MAX_OPEN_DURATION_WINTER,
    CONF_MIN_SURPLUS_POWER,
    CONF_MOBILE_ENABLED,
    CONF_MOBILE_NOTIFY_ENTITY,
    CONF_MOBILE_TARGETS,
    CONF_MSG_CLOSE_CO2,
    CONF_MSG_CLOSE_DEFAULT,
    CONF_MSG_CLOSE_DURATION,
    CONF_MSG_CLOSE_FROST,
    CONF_MSG_CLOSE_HEAT,
    CONF_MSG_CLOSE_HUMIDITY,
    CONF_MSG_CLOSE_OUTDOOR_WARMER,
    CONF_MSG_OPEN_CO2,
    CONF_MSG_OPEN_HUMIDITY,
    CONF_MSG_OPEN_TEMP,
    CONF_MSG_REMINDER,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_PERSISTENT_ENABLED,
    CONF_POWER_ENTITY,
    CONF_POWER_GRACE_PERIOD,
    CONF_PRESENCE_ENTITY,
    CONF_REMINDER_INTERVAL,
    CONF_ROOM_NAME,
    CONF_SHOWER_DETECTION_ENABLED,
    CONF_SHOWER_RISE_THRESHOLD,
    CONF_SHUTTER_ENTITY,
    CONF_SONOS_ENTITY,
    CONF_TEMP_ATTRIBUTE,
    CONF_TEMP_MARGIN,
    CONF_TEMP_SOURCE_ENTITY,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_TTS_ENTITY,
    CONF_TTS_PLAYBACK_MODE,
    CONF_TTS_VOLUME,
    CONF_WINDOW_ENTITY,
    CONF_WINTER_OUTDOOR_THRESHOLD,
    DEFAULT_CO2_THRESHOLD_CLOSE,
    DEFAULT_CO2_THRESHOLD_OPEN,
    DEFAULT_FROST_DEBOUNCE_MINUTES,
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_HEAT_PROTECTION_TEMP,
    DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION,
    DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
    DEFAULT_HUMIDITY_THRESHOLD_OPEN,
    DEFAULT_MAX_OPEN_DURATION_WINTER,
    DEFAULT_MIN_SURPLUS_POWER,
    DEFAULT_MSG_CLOSE_CO2,
    DEFAULT_MSG_CLOSE_DEFAULT,
    DEFAULT_MSG_CLOSE_DURATION,
    DEFAULT_MSG_CLOSE_FROST,
    DEFAULT_MSG_CLOSE_HEAT,
    DEFAULT_MSG_CLOSE_HUMIDITY,
    DEFAULT_MSG_CLOSE_OUTDOOR_WARMER,
    DEFAULT_MSG_OPEN_CO2,
    DEFAULT_MSG_OPEN_HUMIDITY,
    DEFAULT_MSG_OPEN_TEMP,
    DEFAULT_MSG_REMINDER,
    DEFAULT_POWER_GRACE_PERIOD,
    DEFAULT_REMINDER_INTERVAL,
    DEFAULT_SHOWER_DETECTION_ENABLED,
    DEFAULT_SHOWER_RISE_THRESHOLD,
    DEFAULT_TEMP_ATTRIBUTE,
    DEFAULT_TEMP_MARGIN,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DEFAULT_TTS_PLAYBACK_MODE,
    DEFAULT_TTS_VOLUME,
    DEFAULT_WINTER_OUTDOOR_THRESHOLD,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
    SHOWER_RISE_LOOKBACK_MINUTES,
    TTS_PLAYBACK_MODE_PAUSE,
)

_LOGGER = logging.getLogger(__name__)

# Wie oft (während "Lüften empfohlen" aktiv ist) die Winter-Höchstdauer und
# eine mögliche Erinnerung erneut geprüft werden.
_TICK_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt die binary_sensor Entität für den konfigurierten Raum an."""
    async_add_entities([SmartVentilationBinarySensor(hass, entry)])


class SmartVentilationBinarySensor(BinarySensorEntity, RestoreEntity):
    """True = Lüften wird gerade empfohlen (Fenster sollte offen sein).

    Berücksichtigte Logik:
    - Luftfeuchtigkeit je Raum (unabhängig von Temperatur/Jahreszeit)
    - Öffnen, wenn drinnen zu warm UND draußen spürbar kühler ist
      (Toleranz-Marge gegen Flackern bei Werten nahe der Schwelle)
    - Schließen, sobald draußen wieder spürbar wärmer ist als drinnen
      (Sommer-Nachtkühlung: abends öffnen, morgens schließen) - außer es
      wird gerade noch aus Feuchtigkeitsgründen gelüftet
    - Frost-/Hitzeschutz: unterhalb bzw. oberhalb einer Außentemperatur-
      Grenze wird nie geöffnet, ein bereits offener Zustand wird sofort
      geschlossen - unabhängig vom eigentlichen Öffnen-Grund (Temperatur,
      Luftfeuchtigkeit oder CO2)
    - Winter-Höchstdauer: bei kalter Außentemperatur wird nach einer
      einstellbaren Zeit automatisch zum Schließen aufgefordert, um
      übermäßigen Wärmeverlust zu vermeiden
    - Optionale, wiederkehrende Erinnerung, falls die Empfehlung ignoriert wird
    """

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

        self._open_since = None
        self._last_notified_at = None
        self._last_reason: str | None = None
        self._unsub_tick = None

        # Zuletzt kommandierter Soll-Zustand der optionalen Geräte.
        # None = noch nicht initial synchronisiert.
        self._dehumidifier_state: bool | None = None
        self._ac_state: bool | None = None

        # Seit wann die Einspeiseleistung ununterbrochen zu niedrig ist,
        # während das jeweilige Gerät läuft (für die Abschalt-Verzögerung).
        self._dehumidifier_low_power_since = None
        self._ac_low_power_since = None

        # Seit wann die Außentemperatur ununterbrochen auf/unter der
        # Frostschutz-Grenze liegt (für den Debounce, siehe _evaluate()) -
        # nur für tatsächliche Messwerte, nicht für einen fehlenden Sensor.
        self._frost_cold_since = None

        # Rollierendes Zeitfenster (Zeitpunkt, Luftfeuchtigkeit) für die
        # Duscherkennung - siehe _update_shower_detection().
        self._humidity_samples: deque[tuple] = deque()
        self._showering = False

    @property
    def extra_state_attributes(self) -> dict:
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
        co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY))
        outdoor_temp = self._get_float_state(self._effective(CONF_OUTDOOR_TEMP_ENTITY, None))
        outdoor_humidity = self._get_float_state(
            self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        )

        attrs = {
            "raum": self._config[CONF_ROOM_NAME],
            "temperatur_quelle": self._config[CONF_TEMP_SOURCE_ENTITY],
            "innentemperatur": indoor_temp,
            "schwelle_temperatur_oeffnen": self._effective(
                CONF_TEMP_THRESHOLD_OPEN, DEFAULT_TEMP_THRESHOLD_OPEN
            ),
            "schwelle_temperatur_schliessen": self._effective(
                CONF_TEMP_THRESHOLD_CLOSE, DEFAULT_TEMP_THRESHOLD_CLOSE
            ),
        }
        if self._config.get(CONF_NO_WINDOW, False):
            # Nur gesetzt, wenn "kein Fenster" - Standardfall (Fenster
            # vorhanden) fügt bewusst nichts hinzu, um bestehende Dashboards
            # nicht zu verändern.
            attrs["hat_fenster"] = False
        if outdoor_temp is not None:
            attrs["aussentemperatur"] = outdoor_temp
        if self._config.get(CONF_HUMIDITY_ENTITY):
            attrs["luftfeuchtigkeit"] = humidity
            attrs["schwelle_feuchtigkeit_oeffnen"] = self._effective(
                CONF_HUMIDITY_THRESHOLD_OPEN, DEFAULT_HUMIDITY_THRESHOLD_OPEN
            )
            attrs["schwelle_feuchtigkeit_schliessen"] = self._effective(
                CONF_HUMIDITY_THRESHOLD_CLOSE, DEFAULT_HUMIDITY_THRESHOLD_CLOSE
            )
        if self._config.get(CONF_CO2_ENTITY):
            attrs["co2"] = co2
            attrs["schwelle_co2_oeffnen"] = self._effective(
                CONF_CO2_THRESHOLD_OPEN, DEFAULT_CO2_THRESHOLD_OPEN
            )
            attrs["schwelle_co2_schliessen"] = self._effective(
                CONF_CO2_THRESHOLD_CLOSE, DEFAULT_CO2_THRESHOLD_CLOSE
            )
        if self._config.get(CONF_SHOWER_DETECTION_ENABLED, DEFAULT_SHOWER_DETECTION_ENABLED):
            attrs["duschen_erkannt"] = self._showering
        if outdoor_humidity is not None:
            attrs["aussen_luftfeuchtigkeit"] = outdoor_humidity
        if humidity is not None and indoor_temp is not None:
            attrs["absolute_luftfeuchtigkeit"] = round(
                self._absolute_humidity(indoor_temp, humidity), 1
            )
        if outdoor_humidity is not None and outdoor_temp is not None:
            attrs["aussen_absolute_luftfeuchtigkeit"] = round(
                self._absolute_humidity(outdoor_temp, outdoor_humidity), 1
            )
        if self._config.get(CONF_TEMP_ATTRIBUTE):
            attrs["temperatur_attribut"] = self._config[CONF_TEMP_ATTRIBUTE]
        if self._config.get(CONF_WINDOW_ENTITY):
            attrs["fensterkontakt_entity"] = self._config[CONF_WINDOW_ENTITY]

        # Effektiv wirksame Benachrichtigungsmethoden - für Dashboards, die
        # anzeigen wollen, worüber ein Raum tatsächlich benachrichtigt.
        # Sprachausgabe ist aktiv, sobald der Raum mindestens einen
        # Lautsprecher ausgewählt hat - kein eigener Ja/Nein-Schalter mehr,
        # keine globale Einstellung.
        sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
        if sonos_entities:
            attrs["sprachausgabe_aktiv"] = True
            attrs["sprachausgabe_lautsprecher"] = sonos_entities
        if self._effective(CONF_MOBILE_ENABLED, False):
            attrs["app_aktiv"] = True
            app_targets = [
                t.get(CONF_MOBILE_NOTIFY_ENTITY)
                for t in self._get_mobile_targets()
                if t.get(CONF_MOBILE_NOTIFY_ENTITY)
            ]
            if app_targets:
                attrs["app_ziele"] = app_targets
        if self._effective(CONF_PERSISTENT_ENABLED, False):
            attrs["persistent_aktiv"] = True
        if self._open_since is not None:
            attrs["empfehlung_aktiv_seit"] = self._open_since.isoformat()
        if self._last_notified_at is not None:
            attrs["letzte_benachrichtigung"] = self._last_notified_at.isoformat()
        if self._last_reason is not None:
            attrs["letzter_grund"] = self._last_reason
        if self._config.get(CONF_DEHUMIDIFIER_ENTITY):
            attrs["luftentfeuchter_an"] = bool(self._dehumidifier_state)
        if self._config.get(CONF_AC_ENTITY):
            attrs["klimaanlage_an"] = bool(self._ac_state)
        return attrs

    async def async_added_to_hass(self) -> None:
        """Beobachtet relevante Entitäten und stellt zunächst den Zustand
        von vor einem Neustart wieder her (RestoreEntity) - ohne das würde
        jede Neubewertung nach einem Neustart immer von "aus" ausgehen und
        bei aktuell noch gültigen Bedingungen fälschlich einen Zustands-
        wechsel (und damit eine Benachrichtigung) auslösen, obwohl sich
        nichts geändert hat.
        """
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == "on"
            attrs = last_state.attributes
            if "empfehlung_aktiv_seit" in attrs:
                self._open_since = dt_util.parse_datetime(
                    attrs["empfehlung_aktiv_seit"]
                )
            if "letzter_grund" in attrs and attrs["letzter_grund"] != "frost_unavailable":
                # "frost_unavailable" ist ein seit 0.35.0 entfernter Grund-Code
                # (siehe CLAUDE.md, Lektion 11) - ohne diesen Ausschluss würde
                # ein vor dem Update gespeicherter, seitdem nie neu berechneter
                # Wert (Raum bleibt durchgehend "aus", solange der Sensor
                # weiterhin fehlt, also ohne neuen Zustandswechsel) bei jedem
                # Neustart unverändert wiederhergestellt und weiterhin als
                # veralteter Auslöser angezeigt.
                self._last_reason = attrs["letzter_grund"]
            if "luftentfeuchter_an" in attrs:
                self._dehumidifier_state = bool(attrs["luftentfeuchter_an"])
            if "klimaanlage_an" in attrs:
                self._ac_state = bool(attrs["klimaanlage_an"])

        tracked = [self._config[CONF_TEMP_SOURCE_ENTITY]]
        for key in (
            CONF_HUMIDITY_ENTITY,
            CONF_CO2_ENTITY,
            CONF_WINDOW_ENTITY,
            CONF_POWER_ENTITY,
        ):
            value = self._config.get(key)
            if value:
                tracked.append(value)

        # Außentemperatur/-luftfeuchtigkeit kommen ausschließlich aus "Smart
        # Ventilation Options" - direkt verfolgen, falls beim Hinzufügen
        # bereits gesetzt (siehe Hinweis in der README zur Reaktivität bei
        # reiner Startreihenfolge-Abhängigkeit).
        outdoor_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        if outdoor_entity:
            tracked.append(outdoor_entity)
        outdoor_humidity_entity = self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        if outdoor_humidity_entity:
            tracked.append(outdoor_humidity_entity)

        self.async_on_remove(
            async_track_state_change_event(self.hass, tracked, self._handle_state_change)
        )
        # Läuft dauerhaft (nicht nur während "Lüften empfohlen" aktiv ist):
        # wird auch für die Geräte-Steuerung benötigt, z. B. um nach
        # unzureichender Einspeiseleistung später erneut zu prüfen.
        self._unsub_tick = async_track_time_interval(
            self.hass, self._handle_tick, _TICK_INTERVAL
        )
        self.async_on_remove(self._stop_tick_timer)
        await self._evaluate()

    @callback
    def _handle_state_change(self, event: Event) -> None:
        self.hass.async_create_task(self._evaluate())

    def _stop_tick_timer(self) -> None:
        if self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None

    @callback
    def _handle_tick(self, now) -> None:
        self.hass.async_create_task(self._evaluate())

    def _global_config(self) -> dict:
        """Liefert die Daten der globalen Einstellungen (falls vorhanden)."""
        domain_data = self.hass.data.get(DOMAIN, {})
        global_entry_id = domain_data.get(GLOBAL_ENTRY_ID_KEY)
        if not global_entry_id:
            return {}
        return domain_data.get(global_entry_id) or {}

    def _effective(self, key: str, hardcoded_default):
        """Ermittelt den wirksamen Wert für ein überschreibbares Feld:
        1. Raum-Override (falls im Raum gesetzt), sonst
        2. globale Einstellung (falls vorhanden und gesetzt), sonst
        3. fest einprogrammierter Standardwert.
        """
        room_value = self._config.get(key)
        if room_value not in (None, ""):
            return room_value
        global_value = self._global_config().get(key)
        if global_value not in (None, ""):
            return global_value
        return hardcoded_default

    def _effective_list(self, key: str) -> list:
        """Wie _effective(), aber für Listen: eine leere Liste zählt
        (anders als bei _effective()) als 'nicht gesetzt' und führt zum
        Fallback auf die globale Einstellung."""
        room_value = self._config.get(key)
        if room_value:
            return list(room_value)
        global_value = self._global_config().get(key)
        return list(global_value) if global_value else []

    @staticmethod
    def _absolute_humidity(temp_c: float, rh_percent: float) -> float:
        """Berechnet die absolute Luftfeuchtigkeit (g/m³) aus Temperatur (°C)
        und relativer Luftfeuchtigkeit (%) über die Magnus-Formel.

        Wird für den Außen-/Innenvergleich benötigt: relative Luftfeuchtigkeit
        allein ist irreführend, da kalte Luft bei hoher RH% trotzdem absolut
        sehr trocken sein kann (klassischer Winter-Lüften-Effekt) und warme
        Luft bei niedriger RH% absolut trotzdem mehr Wasser enthalten kann.
        """
        saturation_vapor_pressure = 6.112 * math.exp(
            (17.62 * temp_c) / (243.12 + temp_c)
        )
        vapor_pressure = (rh_percent / 100) * saturation_vapor_pressure
        return 216.7 * vapor_pressure / (273.15 + temp_c)

    def _update_shower_detection(self, humidity: float | None, now) -> bool:
        """Erkennt ein laufendes Duschen rein anhand des Anstiegs der
        Luftfeuchtigkeit über ein rollierendes Zeitfenster (siehe
        SHOWER_RISE_LOOKBACK_MINUTES) - kein zusätzlicher Sensor nötig.

        Lüften direkt während des Duschens bringt nichts (es entsteht
        weiter Dampf) - solange der Anstieg anhält, wird angenommen, dass
        noch geduscht wird. Sobald der Anstieg wieder unter die Schwelle
        fällt (Dusche vorbei, Luftfeuchtigkeit stabilisiert sich oder
        sinkt), gilt das Duschen als beendet.
        """
        if humidity is None:
            self._humidity_samples.clear()
            return False

        self._humidity_samples.append((now, humidity))
        cutoff = now - timedelta(minutes=SHOWER_RISE_LOOKBACK_MINUTES)
        while len(self._humidity_samples) > 1 and self._humidity_samples[0][0] < cutoff:
            self._humidity_samples.popleft()

        oldest_time, oldest_value = self._humidity_samples[0]
        elapsed_minutes = (now - oldest_time).total_seconds() / 60
        if elapsed_minutes < 1:
            # Noch nicht genug Historie, um einen Anstieg zu beurteilen -
            # permissiv wie bei "nicht konfiguriert" (siehe CLAUDE.md).
            return False

        rise_rate = (humidity - oldest_value) / elapsed_minutes
        threshold = self._effective(
            CONF_SHOWER_RISE_THRESHOLD, DEFAULT_SHOWER_RISE_THRESHOLD
        )
        return rise_rate >= threshold

    def _window_action_needed(self, target_open: bool) -> bool:
        """Prüft, ob eine Benachrichtigung überhaupt nötig ist, oder ob das
        Fenster laut Fensterkontakt-Sensor bereits im gewünschten Zustand ist.

        Ohne konfigurierten Fensterkontakt (oder bei unbekanntem/
        unverfügbarem Zustand) wird sicherheitshalber immer benachrichtigt.
        Erwartete Konvention: Zustand "on" = Fenster offen, "off" = zu
        (Standard bei binary_sensor mit device_class window/door/opening).
        """
        window_entity = self._config.get(CONF_WINDOW_ENTITY)
        if not window_entity:
            return True
        state = self.hass.states.get(window_entity)
        if state is None or state.state not in ("on", "off"):
            return True
        is_open = state.state == "on"
        return is_open != target_open

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

    async def _evaluate(self) -> None:  # noqa: C901 - bewusst als ein Ablauf gehalten
        """Prüft alle Bedingungen und aktualisiert ggf. den Zustand."""
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
        co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY))
        outdoor_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        outdoor_temp = self._get_float_state(outdoor_entity)
        outdoor_humidity_entity = self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        outdoor_humidity = self._get_float_state(outdoor_humidity_entity)

        temp_open = self._effective(CONF_TEMP_THRESHOLD_OPEN, DEFAULT_TEMP_THRESHOLD_OPEN)
        temp_close = self._effective(CONF_TEMP_THRESHOLD_CLOSE, DEFAULT_TEMP_THRESHOLD_CLOSE)
        hum_open = self._effective(CONF_HUMIDITY_THRESHOLD_OPEN, DEFAULT_HUMIDITY_THRESHOLD_OPEN)
        hum_close = self._effective(CONF_HUMIDITY_THRESHOLD_CLOSE, DEFAULT_HUMIDITY_THRESHOLD_CLOSE)
        co2_open = self._effective(CONF_CO2_THRESHOLD_OPEN, DEFAULT_CO2_THRESHOLD_OPEN)
        co2_close = self._effective(CONF_CO2_THRESHOLD_CLOSE, DEFAULT_CO2_THRESHOLD_CLOSE)
        margin = self._effective(CONF_TEMP_MARGIN, DEFAULT_TEMP_MARGIN)
        frost_temp = self._effective(CONF_FROST_PROTECTION_TEMP, DEFAULT_FROST_PROTECTION_TEMP)
        frost_debounce_minutes = self._effective(
            CONF_FROST_DEBOUNCE_MINUTES, DEFAULT_FROST_DEBOUNCE_MINUTES
        )
        heat_temp = self._effective(CONF_HEAT_PROTECTION_TEMP, DEFAULT_HEAT_PROTECTION_TEMP)
        winter_threshold = self._effective(
            CONF_WINTER_OUTDOOR_THRESHOLD, DEFAULT_WINTER_OUTDOOR_THRESHOLD
        )
        max_duration = self._effective(
            CONF_MAX_OPEN_DURATION_WINTER, DEFAULT_MAX_OPEN_DURATION_WINTER
        )
        reminder_interval = self._effective(
            CONF_REMINDER_INTERVAL, DEFAULT_REMINDER_INTERVAL
        )
        has_window = not self._config.get(CONF_NO_WINDOW, False)

        # --- Grundbedingungen ---
        humidity_needs_open = humidity is not None and humidity >= hum_open
        humidity_needs_close = humidity is not None and humidity <= hum_close
        co2_needs_open = co2 is not None and co2 >= co2_open
        co2_needs_close = co2 is not None and co2 <= co2_close
        temp_needs_open = indoor_temp is not None and indoor_temp >= temp_open
        temp_needs_close = indoor_temp is not None and indoor_temp <= temp_close

        # --- Frostschutz: harte Grenze ---
        # Ist ein Außentemperatur-Sensor konfiguriert, aber aktuell nicht
        # verfügbar (z. B. während Home Assistant startet/stoppt, wenn
        # andere Integrationen noch laden), wird sicherheitshalber so
        # getan, als könnte Frost vorliegen (blockiert das Öffnen) - statt
        # das fälschlich wie "kein Sensor konfiguriert" zu behandeln.
        # frost_sensor_missing unterscheidet den konservativen Fallback
        # (Sensor konfiguriert, aber gerade unavailable/unknown) von einer
        # tatsächlich niedrigen Außentemperatur - beide lösen weiterhin
        # gleichermaßen frost_block aus (sicherer Standard bleibt
        # unverändert), aber nur Ersteres bekommt unten einen eigenen,
        # ehrlichen Auslöser-Grund statt fälschlich "frost" zu melden.
        frost_sensor_missing = outdoor_entity is not None and outdoor_temp is None
        frost_block = outdoor_entity is not None and (
            outdoor_temp is None or outdoor_temp <= frost_temp
        )

        # --- Debounce für das tatsächliche Schließen wegen Frost ---
        # Ein einzelner Ausreißer-Messwert (Sensor-Glitch) soll nicht sofort
        # eine bereits aktive Öffnen-Empfehlung samt Benachrichtigung
        # beenden. Das reine Blockieren des Öffnens (frost_block oben)
        # bleibt bewusst sofort/ungebounct - konservativ zu bleiben ist
        # risikofrei. Nur der fehlende Sensor (frost_sensor_missing) bleibt
        # ebenfalls sofort wirksam, da es dort keinen Messwert gibt, der
        # "anhalten" könnte. frost_debounce_minutes <= 0 schaltet den
        # Debounce komplett ab (sofortiges Schließen wie zuvor).
        frost_real_cold = outdoor_temp is not None and outdoor_temp <= frost_temp
        if frost_real_cold:
            if self._frost_cold_since is None:
                self._frost_cold_since = dt_util.utcnow()
        else:
            self._frost_cold_since = None
        frost_cold_confirmed = frost_real_cold and (
            frost_debounce_minutes <= 0
            or (
                self._frost_cold_since is not None
                and (dt_util.utcnow() - self._frost_cold_since).total_seconds() / 60
                >= frost_debounce_minutes
            )
        )

        # --- Hitzeschutz: harte Grenze, Pendant zum Frostschutz ---
        # Oberhalb dieser Außentemperatur wird nie geöffnet - Lüften würde
        # absehbar nur noch Hitze hereinlassen, unabhängig davon, ob
        # eigentlich wegen Temperatur, Luftfeuchtigkeit oder CO2 gelüftet
        # werden sollte. Anders als beim Frostschutz wird eine fehlende
        # Außentemperatur hier NICHT als "zu heiß" gewertet (das übernimmt
        # bereits frost_block als konservativer Fallback) - sonst würde ein
        # einzelner fehlender Messwert beide Schutzmechanismen gleichzeitig
        # auslösen, ohne zusätzlichen Nutzen.
        heat_block = outdoor_entity is not None and (
            outdoor_temp is not None and outdoor_temp >= heat_temp
        )

        # --- Öffnen: drinnen zu warm UND draußen spürbar kühler ---
        # Kein Außentemperatur-Sensor konfiguriert = wie bisher permissiv
        # (Vergleich entfällt, Lüften wird angenommen zu helfen). Ist aber
        # ein Sensor konfiguriert und nur gerade nicht verfügbar, wird das
        # KONSERVATIV behandelt (kein Öffnen auf dieser Basis) - sonst
        # könnte eine kurzzeitige Nichtverfügbarkeit (z. B. beim Neustart
        # von Home Assistant) fälschlich eine Öffnen-Empfehlung samt
        # Benachrichtigung auslösen, nur weil der Vergleich mangels Daten
        # übersprungen wird.
        outdoor_cooler_enough = outdoor_entity is None or (
            outdoor_temp is not None
            and indoor_temp is not None
            and outdoor_temp <= indoor_temp - margin
        )
        # --- Öffnen wegen Feuchtigkeit nur, wenn es draußen auch trockener
        # ist als drinnen - sonst würde Lüften die Situation verschlimmern.
        # Vergleich über ABSOLUTE Luftfeuchtigkeit (g/m³), nicht über die
        # relative: kalte Luft mit hoher RH% ist absolut oft trotzdem sehr
        # trocken (typischer Winter-Lüften-Effekt) - ein reiner RH%-Vergleich
        # würde in diesem, praktisch sehr häufigen Fall fälschlich vom
        # Lüften abraten. Kein Außen-Luftfeuchtigkeitssensor konfiguriert =
        # wie bisher permissiv (Vergleich entfällt). Ist ein Sensor
        # konfiguriert, aber gerade nicht verfügbar (oder fehlen sonstige
        # nötige Werte), wird das - wie beim Temperatur-Vergleich oben -
        # KONSERVATIV behandelt, nicht permissiv.
        outdoor_drier_enough = outdoor_humidity_entity is None or (
            outdoor_humidity is not None
            and humidity is not None
            and indoor_temp is not None
            and outdoor_temp is not None
            and self._absolute_humidity(outdoor_temp, outdoor_humidity)
            < self._absolute_humidity(indoor_temp, humidity)
        )

        # --- Duscherkennung: solange die Luftfeuchtigkeit gerade schnell
        # ansteigt (typisch beim Duschen), wird die Öffnen-Empfehlung wegen
        # Luftfeuchtigkeit zurückgehalten - Lüften währenddessen bringt
        # nichts. Optional, Standard aus (siehe _update_shower_detection).
        # Nur pro Raum einstellbar, keine globale Einstellung.
        shower_detection_enabled = self._config.get(
            CONF_SHOWER_DETECTION_ENABLED, DEFAULT_SHOWER_DETECTION_ENABLED
        )
        self._showering = (
            self._update_shower_detection(humidity, dt_util.utcnow())
            if shower_detection_enabled
            else False
        )

        open_by_temp = temp_needs_open and outdoor_cooler_enough
        open_by_humidity = (
            humidity_needs_open and outdoor_drier_enough and not self._showering
        )
        # CO2 braucht - anders als Temperatur/Luftfeuchtigkeit - keinen
        # Außenluft-Vergleich: Außenluft liegt praktisch immer bei ~420 ppm,
        # also weit unter jeder sinnvollen Innenschwelle - Lüften hilft hier
        # immer.
        open_by_co2 = co2_needs_open

        # --- Schutz vor Schließen aus einem anderen Grund: bleibt für jede
        # der drei Größen (Temperatur, Luftfeuchtigkeit, CO2) aktiv, solange
        # sie die jeweilige SCHLIESSEN-Schwelle noch nicht erreicht hat -
        # nicht nur bis sie unter die (höhere) ÖFFNEN-Schwelle fällt. Ohne
        # diese Unterscheidung würde die Empfehlung bei Werten zwischen den
        # beiden Schwellen (z. B. Luftfeuchtigkeit zwischen 50 % und 60 %
        # bei Standard-Schwellen) ständig zwischen "wegen Temperatur/CO2
        # schließen" und "wegen Luftfeuchtigkeit wieder öffnen" hin- und
        # herflackern, sobald zufällig gleichzeitig eine andere
        # Schließbedingung erfüllt ist - obwohl die Luftfeuchtigkeit die
        # ganze Zeit über unverändert im Lüftungsbedarf-Bereich blieb.
        # Symmetrisch für alle drei Größen: jede schützt die beiden anderen
        # davor, allein deswegen zu schließen.
        temp_still_needed = open_by_temp or (
            self._attr_is_on and indoor_temp is not None and not temp_needs_close
        )
        humidity_still_needed = open_by_humidity or (
            self._attr_is_on and humidity is not None and not humidity_needs_close
        )
        co2_still_needed = open_by_co2 or (
            self._attr_is_on and co2 is not None and not co2_needs_close
        )

        # Ohne Fenster in diesem Raum gibt es grundsätzlich nichts zu öffnen
        # oder zu schließen - die Empfehlungs-/Benachrichtigungslogik entfällt
        # komplett. Die oben berechneten temp_needs_*/humidity_needs_*-Flags
        # bleiben aber unverändert für die Geräte-Steuerung (Luftentfeuchter/
        # Klimaanlage) nutzbar, die weiter unten unabhängig davon läuft.
        if not has_window:
            if self._attr_is_on:
                self._attr_is_on = False
                self._open_since = None
                self._last_reason = None
                self._last_notified_at = None
            # Immer schreiben (nicht nur bei Zustandswechsel), damit die
            # angezeigten Attribute (z. B. aktuelle Luftfeuchtigkeit) stets
            # den aktuellen Sensorwert zeigen und nicht auf dem Stand des
            # letzten Wechsels "einfrieren".
            self.async_write_ha_state()
            await self._update_devices(
                temp_needs_open=temp_needs_open,
                temp_needs_close=temp_needs_close,
                humidity_needs_open=humidity_needs_open,
                humidity_needs_close=humidity_needs_close,
                outdoor_cooler_enough=outdoor_cooler_enough,
            )
            return

        should_open = (
            open_by_temp or open_by_humidity or open_by_co2
        ) and not frost_block and not heat_block

        # --- Schließen: Sommer-Fall (draußen wieder spürbar wärmer) ---
        outdoor_warmer_again = (
            outdoor_temp is not None
            and indoor_temp is not None
            and outdoor_temp >= indoor_temp + margin
        )
        close_by_summer_outdoor = (
            self._attr_is_on
            and outdoor_warmer_again
            and not humidity_still_needed
            and not co2_still_needed
        )

        # --- Schließen: Winter-Höchstdauer ---
        # Ob dabei ein noch bestehender Feuchtigkeits-/CO2-Lüftungsbedarf
        # Vorrang hat (Standard) oder die Höchstdauer strikt durchgesetzt
        # wird, ist konfigurierbar (Raum-Override möglich, sonst globale
        # Einstellung).
        humidity_priority = self._effective(
            CONF_HUMIDITY_PRIORITY_OVER_DURATION,
            DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION,
        )
        winter_conditions = outdoor_temp is not None and outdoor_temp <= winter_threshold
        open_duration_minutes = None
        if self._attr_is_on and self._open_since is not None:
            open_duration_minutes = (
                dt_util.utcnow() - self._open_since
            ).total_seconds() / 60
        close_by_duration = (
            self._attr_is_on
            and winter_conditions
            and open_duration_minutes is not None
            and open_duration_minutes >= max_duration
            and not (humidity_priority and (humidity_still_needed or co2_still_needed))
        )

        # --- Schließen: Frost-/Hitzeschutz erzwingt sofortiges Schließen ---
        # close_by_frost nutzt bewusst NICHT frost_block direkt, sondern
        # frost_sensor_missing (sofort) bzw. frost_cold_confirmed (erst nach
        # Debounce) - siehe deren Definition oben.
        close_by_frost = self._attr_is_on and (frost_sensor_missing or frost_cold_confirmed)
        close_by_heat = self._attr_is_on and heat_block

        # Jede der drei reinen Schließbedingungen (Temperatur, Luftfeuchtigkeit,
        # CO2) wird nicht angewendet, solange eine der beiden ANDEREN Größen
        # noch Lüftungsbedarf anzeigt - sonst würde direkt im Anschluss
        # wieder eine "bitte öffnen"-Empfehlung deswegen folgen (Schließen-
        # dann-sofort-wieder-Öffnen-Flackern). Frost-/Hitzeschutz sowie der
        # Sommer-Fall/Winter-Höchstdauer sind davon unabhängig (siehe dort).
        close_by_temp = (
            temp_needs_close and not humidity_still_needed and not co2_still_needed
        )
        close_by_humidity = (
            humidity_needs_close and not temp_still_needed and not co2_still_needed
        )
        close_by_co2 = (
            co2_needs_close and not temp_still_needed and not humidity_still_needed
        )

        should_close = (
            close_by_temp
            or close_by_humidity
            or close_by_co2
            or close_by_summer_outdoor
            or close_by_duration
            or close_by_frost
            or close_by_heat
        )

        # Ein einziger strukturierter Debug-Log-Eintrag pro Neubewertung mit
        # allen Zwischenergebnissen - aktivierbar ganz ohne eigenes Feature
        # über Home Assistants Standardmechanismus (Einstellungen → Geräte &
        # Dienste → Smart Ventilation → Zahnrad am jeweiligen Raum →
        # Debug-Protokollierung aktivieren, oder global über `logger:` in
        # der configuration.yaml für
        # custom_components.ha_smart_ventilation). Gedacht, um Flacker-
        # artige Probleme (wiederholtes Öffnen/Schließen) anhand der
        # Logzeilen nachvollziehen zu können, ohne die Entscheidungskette
        # gedanklich (oder im Chat) durchspielen zu müssen.
        _LOGGER.debug(
            "%s: is_on=%s indoor_temp=%s outdoor_temp=%s humidity=%s co2=%s | "
            "needs open/close: temp=%s/%s hum=%s/%s co2=%s/%s | "
            "open_by: temp=%s hum=%s co2=%s | frost_block=%s (sensor_missing=%s cold_confirmed=%s) heat_block=%s | "
            "still_needed: temp=%s hum=%s co2=%s | "
            "close_by: temp=%s hum=%s co2=%s summer=%s duration=%s frost=%s heat=%s | "
            "should_open=%s should_close=%s",
            self._config[CONF_ROOM_NAME],
            self._attr_is_on,
            indoor_temp,
            outdoor_temp,
            humidity,
            co2,
            temp_needs_open,
            temp_needs_close,
            humidity_needs_open,
            humidity_needs_close,
            co2_needs_open,
            co2_needs_close,
            open_by_temp,
            open_by_humidity,
            open_by_co2,
            frost_block,
            frost_sensor_missing,
            frost_cold_confirmed,
            heat_block,
            temp_still_needed,
            humidity_still_needed,
            co2_still_needed,
            close_by_temp,
            close_by_humidity,
            close_by_co2,
            close_by_summer_outdoor,
            close_by_duration,
            close_by_frost,
            close_by_heat,
            should_open,
            should_close,
        )

        new_state = self._attr_is_on
        reason = None
        silent_frost_close = False

        if should_open and not self._attr_is_on:
            new_state = True
            if open_by_temp:
                reason = "temp"
            elif open_by_humidity:
                reason = "humidity"
            else:
                reason = "co2"
        elif should_close and self._attr_is_on:
            new_state = False
            if close_by_frost:
                if frost_sensor_missing:
                    # Kein tatsächlicher Messwert, nur ein konservativer
                    # Sicherheits-Fallback (siehe frost_sensor_missing oben) -
                    # das Schließen bleibt aus Sicherheitsgründen bestehen,
                    # aber ohne eigenen Auslöser/Benachrichtigung, da es sich
                    # um kein echtes Ereignis handelt, das gemeldet werden
                    # sollte (typischerweise nur durch einen HA-Neustart
                    # bedingt).
                    silent_frost_close = True
                else:
                    reason = "frost"
            elif close_by_heat:
                reason = "heat"
            elif close_by_duration:
                reason = "duration"
            elif close_by_humidity:
                reason = "humidity"
            elif close_by_co2:
                reason = "co2"
            elif close_by_temp:
                reason = "temp"
            elif close_by_summer_outdoor:
                reason = "outdoor_warmer"

        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self._last_reason = None if silent_frost_close else reason
            if new_state:
                self._open_since = dt_util.utcnow()
            else:
                self._open_since = None
            self.async_write_ha_state()
            if silent_frost_close:
                self._last_notified_at = None
            elif self._window_action_needed(new_state):
                self._last_notified_at = dt_util.utcnow()
                await self._notify(new_state, reason)
            else:
                # Fensterkontakt zeigt bereits den gewünschten Zustand
                # (offen/geschlossen) - keine Benachrichtigung nötig.
                self._last_notified_at = None
            await self._update_devices(
                temp_needs_open=temp_needs_open,
                temp_needs_close=temp_needs_close,
                humidity_needs_open=humidity_needs_open,
                humidity_needs_close=humidity_needs_close,
                outdoor_cooler_enough=outdoor_cooler_enough,
            )
            return

        await self._update_devices(
            temp_needs_open=temp_needs_open,
            temp_needs_close=temp_needs_close,
            humidity_needs_open=humidity_needs_open,
            humidity_needs_close=humidity_needs_close,
            outdoor_cooler_enough=outdoor_cooler_enough,
        )

        # Immer schreiben (nicht nur bei Zustandswechsel), damit die
        # angezeigten Attribute (z. B. aktuelle Temperatur/Luftfeuchtigkeit)
        # stets den aktuellen Sensorwert zeigen und nicht auf dem Stand des
        # letzten Wechsels "einfrieren".
        self.async_write_ha_state()

        # Kein Zustandswechsel - ggf. Erinnerung, falls die Empfehlung seit
        # längerem aktiv ist und ignoriert wird. Zeigt der Fensterkontakt
        # (falls konfiguriert) bereits den gewünschten Zustand, wird nicht
        # erinnert - das Fenster wurde ja offensichtlich schon entsprechend
        # bedient.
        if (
            self._attr_is_on
            and reminder_interval
            and reminder_interval > 0
            and self._window_action_needed(True)
        ):
            if self._last_notified_at is None:
                self._last_notified_at = dt_util.utcnow()
            elapsed = (dt_util.utcnow() - self._last_notified_at).total_seconds() / 60
            if elapsed >= reminder_interval:
                self._last_notified_at = dt_util.utcnow()
                await self._notify(True, "reminder")

    @staticmethod
    def _as_list(value) -> list:
        """Normalisiert Config-Werte zu einer Liste (abwärtskompatibel zu
        älteren Konfigurationen, die noch einen einzelnen String speichern)."""
        if not value:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def _check_power_ok(self) -> bool:
        """Prüft, ob genug Einspeiseleistung für den Gerätestart vorhanden ist.

        Leistungssensor und Mindestschwelle können pro Raum überschrieben
        werden, fallen sonst auf die globalen Einstellungen zurück. Ohne
        Leistungssensor (weder Raum noch global) ist die Bedingung immer
        erfüllt. Gilt ausschließlich fürs Einschalten - das Ausschalten ist
        davon nie abhängig.
        """
        power_entity = self._effective(CONF_POWER_ENTITY, None)
        if not power_entity:
            return True
        power_value = self._get_float_state(power_entity)
        min_power = self._effective(CONF_MIN_SURPLUS_POWER, DEFAULT_MIN_SURPLUS_POWER)
        return power_value is not None and power_value >= min_power

    async def _set_device_state(self, entity_id: str, turn_on: bool) -> None:
        """Schaltet eine Geräte-Entität ein/aus (funktioniert generisch für
        switch, humidifier und climate, da alle turn_on/turn_off unterstützen)."""
        domain = entity_id.split(".")[0]
        service = "turn_on" if turn_on else "turn_off"
        try:
            await self.hass.services.async_call(
                domain, service, {"entity_id": entity_id}, blocking=False
            )
        except HomeAssistantError:
            _LOGGER.warning(
                "Konnte %s nicht %s (Raum %s)",
                entity_id,
                "einschalten" if turn_on else "ausschalten",
                self._config[CONF_ROOM_NAME],
            )

    async def _update_devices(
        self,
        *,
        temp_needs_open: bool,
        temp_needs_close: bool,
        humidity_needs_open: bool,
        humidity_needs_close: bool,
        outdoor_cooler_enough: bool,
    ) -> None:
        """Steuert optionalen Luftentfeuchter und optionale Klimaanlage.

        - Luftentfeuchter: an bei hoher Luftfeuchtigkeit, aus bei niedriger -
          unabhängig vom Fenster-Status.
        - Klimaanlage: an, wenn drinnen zu warm UND Lüften nicht helfen würde
          (draußen nicht kühler) - ergänzt also die Fensterlogik, statt sie zu
          duplizieren. Aus, sobald die Zieltemperatur erreicht ist oder Lüften
          wieder ausreicht. Ist ein Rollladen hinterlegt, fährt dieser beim
          Einschalten herunter und beim Ausschalten wieder hoch.
        - Ein konfigurierter Leistungssensor blockiert das Einschalten. Ist ein
          Gerät bereits an, wird es erst nach Ablauf der Abschalt-Verzögerung
          wegen dauerhaft zu geringer Einspeisung wieder ausgeschaltet.
        """
        await self._update_single_device(
            entity_key=CONF_DEHUMIDIFIER_ENTITY,
            state_attr="_dehumidifier_state",
            low_power_attr="_dehumidifier_low_power_since",
            want_on=humidity_needs_open,
            want_off=humidity_needs_close,
        )
        await self._update_single_device(
            entity_key=CONF_AC_ENTITY,
            state_attr="_ac_state",
            low_power_attr="_ac_low_power_since",
            want_on=temp_needs_open and not outdoor_cooler_enough,
            want_off=temp_needs_close or outdoor_cooler_enough,
            shutter_key=CONF_SHUTTER_ENTITY,
        )

    async def _update_single_device(
        self,
        *,
        entity_key: str,
        state_attr: str,
        low_power_attr: str,
        want_on: bool,
        want_off: bool,
        shutter_key: str | None = None,
    ) -> None:
        entity_id = self._config.get(entity_key)
        if not entity_id:
            return

        current = getattr(self, state_attr)
        power_entity_configured = bool(self._effective(CONF_POWER_ENTITY, None))
        power_ok = self._check_power_ok()
        grace_minutes = self._effective(
            CONF_POWER_GRACE_PERIOD, DEFAULT_POWER_GRACE_PERIOD
        )

        # Verzögertes Abschalten: erst wenn die Einspeisung ununterbrochen
        # seit mindestens "grace_minutes" zu niedrig ist, wird ein bereits
        # laufendes Gerät deswegen abgeschaltet.
        force_off_due_to_power = False
        if current is True and power_entity_configured:
            if power_ok:
                setattr(self, low_power_attr, None)
            else:
                low_since = getattr(self, low_power_attr)
                if low_since is None:
                    setattr(self, low_power_attr, dt_util.utcnow())
                else:
                    elapsed = (dt_util.utcnow() - low_since).total_seconds() / 60
                    if elapsed >= grace_minutes:
                        force_off_due_to_power = True

        if (want_off or force_off_due_to_power) and current is not False:
            await self._set_device_state(entity_id, False)
            setattr(self, state_attr, False)
            setattr(self, low_power_attr, None)
            if shutter_key:
                await self._set_shutter(self._config.get(shutter_key), close=False)
            self.async_write_ha_state()
        elif want_on and not force_off_due_to_power and current is not True:
            if power_ok:
                await self._set_device_state(entity_id, True)
                setattr(self, state_attr, True)
                setattr(self, low_power_attr, None)
                if shutter_key:
                    await self._set_shutter(self._config.get(shutter_key), close=True)
                self.async_write_ha_state()
            # sonst: noch nicht genug Einspeiseleistung - beim nächsten
            # Tick (spätestens alle 5 Minuten) wird erneut geprüft.

    async def _set_shutter(self, shutter_entity: str | None, *, close: bool) -> None:
        """Fährt eine optionale Fenstersperre/Rollladen herunter/hoch (an die
        Klimaanlage gekoppelt: zu/gesperrt beim Einschalten, auf/entsperrt
        beim Ausschalten).

        Unterstützt zwei Entity-Typen:
        - cover: close_cover / open_cover
        - switch: turn_on (= herunterfahren + sperren) / turn_off (= hoch)
        """
        if not shutter_entity:
            return

        domain = shutter_entity.split(".")[0]
        if domain == "switch":
            service = "turn_on" if close else "turn_off"
        else:
            service = "close_cover" if close else "open_cover"

        try:
            await self.hass.services.async_call(
                domain, service, {"entity_id": shutter_entity}, blocking=False
            )
        except HomeAssistantError:
            _LOGGER.warning(
                "Konnte Fenstersperre/Rollladen %s nicht steuern (Raum %s)",
                shutter_entity,
                self._config[CONF_ROOM_NAME],
            )

    @staticmethod
    def _format_measurement(value: float | None, unit: str, decimals: int = 0) -> str:
        """Formatiert einen Mess- oder Schwellenwert inkl. Einheit für die
        Platzhalter {wert}/{schwelle} in den Benachrichtigungstexten."""
        if value is None:
            return "–"
        try:
            return f"{float(value):.{decimals}f} {unit}"
        except (TypeError, ValueError):
            return str(value)

    def _measurement_context(
        self, context_reason: str | None, opening: bool
    ) -> tuple[str, str]:
        """Liefert (aktueller Wert, Schwellenwert) - fertig formatiert inkl.
        Einheit - für die Platzhalter {wert}/{schwelle}, passend zum
        jeweiligen Grund und zur Richtung (Öffnen/Schließen: Öffnen- und
        Schließen-Schwelle unterscheiden sich bei Temperatur/Luftfeuchtigkeit/
        CO2)."""
        if context_reason == "humidity":
            humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
            threshold = self._effective(
                CONF_HUMIDITY_THRESHOLD_OPEN if opening else CONF_HUMIDITY_THRESHOLD_CLOSE,
                DEFAULT_HUMIDITY_THRESHOLD_OPEN if opening else DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
            )
            return (
                self._format_measurement(humidity, "%"),
                self._format_measurement(threshold, "%"),
            )
        if context_reason == "co2":
            co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY))
            threshold = self._effective(
                CONF_CO2_THRESHOLD_OPEN if opening else CONF_CO2_THRESHOLD_CLOSE,
                DEFAULT_CO2_THRESHOLD_OPEN if opening else DEFAULT_CO2_THRESHOLD_CLOSE,
            )
            return (
                self._format_measurement(co2, "ppm"),
                self._format_measurement(threshold, "ppm"),
            )
        if context_reason == "frost":
            outdoor_temp = self._get_float_state(
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
            )
            threshold = self._effective(
                CONF_FROST_PROTECTION_TEMP, DEFAULT_FROST_PROTECTION_TEMP
            )
            return (
                self._format_measurement(outdoor_temp, "°C", 1),
                self._format_measurement(threshold, "°C", 1),
            )
        if context_reason == "heat":
            outdoor_temp = self._get_float_state(
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
            )
            threshold = self._effective(
                CONF_HEAT_PROTECTION_TEMP, DEFAULT_HEAT_PROTECTION_TEMP
            )
            return (
                self._format_measurement(outdoor_temp, "°C", 1),
                self._format_measurement(threshold, "°C", 1),
            )
        if context_reason == "outdoor_warmer":
            outdoor_temp = self._get_float_state(
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
            )
            indoor_temp = self._get_indoor_temperature()
            return (
                self._format_measurement(outdoor_temp, "°C", 1),
                self._format_measurement(indoor_temp, "°C", 1),
            )
        if context_reason == "duration":
            elapsed = None
            if self._open_since is not None:
                elapsed = (dt_util.utcnow() - self._open_since).total_seconds() / 60
            threshold = self._effective(
                CONF_MAX_OPEN_DURATION_WINTER, DEFAULT_MAX_OPEN_DURATION_WINTER
            )
            return (
                self._format_measurement(elapsed, "min"),
                self._format_measurement(threshold, "min"),
            )
        # "temp" oder unbekannt/None -> Innentemperatur vs. Temperatur-Schwelle
        indoor_temp = self._get_indoor_temperature()
        threshold = self._effective(
            CONF_TEMP_THRESHOLD_OPEN if opening else CONF_TEMP_THRESHOLD_CLOSE,
            DEFAULT_TEMP_THRESHOLD_OPEN if opening else DEFAULT_TEMP_THRESHOLD_CLOSE,
        )
        return (
            self._format_measurement(indoor_temp, "°C", 1),
            self._format_measurement(threshold, "°C", 1),
        )

    def _build_message(self, should_ventilate: bool, reason: str | None) -> str:
        room = self._config[CONF_ROOM_NAME]

        if should_ventilate:
            if reason == "humidity":
                template = self._effective(
                    CONF_MSG_OPEN_HUMIDITY, DEFAULT_MSG_OPEN_HUMIDITY
                )
            elif reason == "co2":
                template = self._effective(CONF_MSG_OPEN_CO2, DEFAULT_MSG_OPEN_CO2)
            else:
                template = self._effective(CONF_MSG_OPEN_TEMP, DEFAULT_MSG_OPEN_TEMP)
            wert, schwelle = self._measurement_context(reason, opening=True)
        elif reason == "frost":
            template = self._effective(CONF_MSG_CLOSE_FROST, DEFAULT_MSG_CLOSE_FROST)
            wert, schwelle = self._measurement_context("frost", opening=False)
        elif reason == "heat":
            template = self._effective(CONF_MSG_CLOSE_HEAT, DEFAULT_MSG_CLOSE_HEAT)
            wert, schwelle = self._measurement_context("heat", opening=False)
        elif reason == "duration":
            template = self._effective(
                CONF_MSG_CLOSE_DURATION, DEFAULT_MSG_CLOSE_DURATION
            )
            wert, schwelle = self._measurement_context("duration", opening=False)
        elif reason == "humidity":
            template = self._effective(
                CONF_MSG_CLOSE_HUMIDITY, DEFAULT_MSG_CLOSE_HUMIDITY
            )
            wert, schwelle = self._measurement_context("humidity", opening=False)
        elif reason == "co2":
            template = self._effective(CONF_MSG_CLOSE_CO2, DEFAULT_MSG_CLOSE_CO2)
            wert, schwelle = self._measurement_context("co2", opening=False)
        elif reason == "outdoor_warmer":
            template = self._effective(
                CONF_MSG_CLOSE_OUTDOOR_WARMER, DEFAULT_MSG_CLOSE_OUTDOOR_WARMER
            )
            wert, schwelle = self._measurement_context("outdoor_warmer", opening=False)
        elif reason == "reminder":
            template = self._effective(CONF_MSG_REMINDER, DEFAULT_MSG_REMINDER)
            wert, schwelle = self._measurement_context(self._last_reason, opening=True)
        else:
            template = self._effective(
                CONF_MSG_CLOSE_DEFAULT, DEFAULT_MSG_CLOSE_DEFAULT
            )
            wert, schwelle = self._measurement_context("temp", opening=False)

        try:
            return template.format(raum=room, wert=wert, schwelle=schwelle)
        except (KeyError, ValueError, IndexError):
            # Fehlerhafter Platzhalter in einem selbst angepassten Text -
            # lieber den unformatierten Text senden als die Benachrichtigung
            # ganz zu verlieren.
            _LOGGER.warning(
                "Benachrichtigungstext für Raum %s enthält einen ungültigen "
                "Platzhalter - wird unverändert gesendet: %s",
                room,
                template,
            )
            return template

    def _is_present(self, presence_entity: str | None) -> bool:
        """Prüft, ob die zu einem Notify-Ziel gehörende Person/das Gerät
        zuhause ist. Ohne Anwesenheits-Entität ist die Bedingung immer
        erfüllt (Push wird wie bisher immer gesendet)."""
        if not presence_entity:
            return True
        state = self.hass.states.get(presence_entity)
        if state is None:
            return True
        return state.state == "home"

    def _get_mobile_targets(self) -> list[dict]:
        """Liefert die Liste der {mobile_notify_entity, presence_entity}-Paare
        - Raum-Override falls gesetzt, sonst die globale Liste.

        Abwärtskompatibel: ältere Konfigurationen, die noch die frühere
        flache Mehrfachauswahl (CONF_MOBILE_NOTIFY_ENTITY als Liste/String)
        gespeichert haben, werden automatisch in die neue Struktur überführt
        - ohne Anwesenheitsprüfung, also wie bisher immer gesendet.
        """
        targets = self._effective_list(CONF_MOBILE_TARGETS)
        if targets:
            return targets
        legacy = self._as_list(self._config.get(CONF_MOBILE_NOTIFY_ENTITY))
        return [{CONF_MOBILE_NOTIFY_ENTITY: entity_id} for entity_id in legacy]

    async def _play_tts(
        self, sonos_entities: list[str], tts_entity: str, message: str
    ) -> None:
        """Spielt die Ansage ab - inkl. global konfigurierter Lautstärke und
        Pausieren/Überlagern der vorhandenen Wiedergabe.

        Hinweis: `tts.speak` selbst unterstützt keine Lautstärkeangabe: die
        Lautstärke wird deshalb vorher separat per media_player.volume_set
        gesetzt und danach NICHT automatisch zurückgesetzt. Beim Pausieren
        wird die vorherige Wiedergabe ebenfalls nicht automatisch
        fortgesetzt - das ist plattformübergreifend nicht zuverlässig lösbar.
        """
        volume_percent = self._effective(CONF_TTS_VOLUME, DEFAULT_TTS_VOLUME)
        playback_mode = self._effective(CONF_TTS_PLAYBACK_MODE, DEFAULT_TTS_PLAYBACK_MODE)

        try:
            await self.hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": sonos_entities,
                    "volume_level": max(0.0, min(100.0, float(volume_percent))) / 100,
                },
                blocking=False,
            )
        except (HomeAssistantError, TypeError, ValueError):
            _LOGGER.debug(
                "Konnte Lautstärke für %s nicht setzen (Raum %s)",
                sonos_entities,
                self._config[CONF_ROOM_NAME],
            )

        if playback_mode == TTS_PLAYBACK_MODE_PAUSE:
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "media_pause",
                    {"entity_id": sonos_entities},
                    blocking=False,
                )
            except HomeAssistantError:
                # Best effort - z. B. wenn gerade nichts läuft/pausierbar ist
                _LOGGER.debug(
                    "Konnte Wiedergabe auf %s nicht pausieren (Raum %s)",
                    sonos_entities,
                    self._config[CONF_ROOM_NAME],
                )

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

    async def _notify(self, should_ventilate: bool, reason: str | None) -> None:
        """Verschickt die Benachrichtigung per Sprachausgabe, App-Push
        und/oder persistenter Web-Benachrichtigung.

        Sprachausgabe ist aktiv, sobald der Raum mindestens einen
        Lautsprecher ausgewählt hat (reine Raum-Einstellung, kein globaler
        Fallback). App-Push und persistente Benachrichtigung werden dagegen
        bei jedem Aufruf live über _effective() ermittelt (Raum-Override,
        sonst globale Einstellung) - genau wie bei den Schwellenwerten.
        Änderungen an den globalen Benachrichtigungseinstellungen wirken
        sich also auch auf Räume aus, die dafür keinen eigenen Override
        gesetzt haben, ohne dass der Raum neu gespeichert werden muss.

        Alle Methoden können gleichzeitig aktiv sein, und jede Methode
        (außer der Web-Benachrichtigung) kann mehrere Ziel-Entitäten haben
        (mehrere Lautsprecher bzw. mehrere notify.*-Entitäten) - in dem
        Fall werden alle bedient.
        """
        room = self._config[CONF_ROOM_NAME]
        message = self._build_message(should_ventilate, reason)

        # Sprachausgabe ist aktiv, sobald der Raum mindestens einen
        # Lautsprecher ausgewählt hat - kein eigener Ja/Nein-Schalter mehr,
        # keine globale Einstellung.
        sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
        mobile_enabled = self._effective(CONF_MOBILE_ENABLED, False)
        persistent_enabled = self._effective(CONF_PERSISTENT_ENABLED, False)

        if sonos_entities:
            tts_entity = self._effective(CONF_TTS_ENTITY, None)
            if tts_entity:
                await self._play_tts(sonos_entities, tts_entity, message)
            else:
                _LOGGER.warning(
                    "Sprachausgabe-Lautsprecher ausgewählt, aber keine "
                    "TTS-Entity konfiguriert (%s)",
                    room,
                )

        if mobile_enabled:
            targets = self._get_mobile_targets()
            if not targets:
                _LOGGER.warning(
                    "Keine notify-Entität für Raum %s konfiguriert", room
                )
            else:
                for target in targets:
                    entity_id = target.get(CONF_MOBILE_NOTIFY_ENTITY)
                    if not entity_id:
                        continue
                    presence_entity = target.get(CONF_PRESENCE_ENTITY)
                    if self._is_present(presence_entity):
                        await self.hass.services.async_call(
                            "notify",
                            "send_message",
                            {
                                "entity_id": entity_id,
                                "title": "Lüften",
                                "message": message,
                            },
                            blocking=False,
                        )
                    else:
                        _LOGGER.debug(
                            "Push an %s in Raum %s übersprungen - "
                            "Person/Gerät nicht zuhause",
                            entity_id,
                            room,
                        )

        if persistent_enabled:
            notification_id = f"smart_ventilation_{self._entry.entry_id}"
            if should_ventilate:
                # Erstellt die Benachrichtigung oder aktualisiert eine
                # bereits vorhandene mit derselben notification_id (z. B.
                # bei einer Erinnerung) - keine Duplikate im Verlauf.
                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "notification_id": notification_id,
                        "title": "Lüften",
                        "message": message,
                    },
                    blocking=False,
                )
            else:
                # Löst die Benachrichtigung automatisch auf, sobald sich
                # die Empfehlung erledigt hat.
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": notification_id},
                    blocking=False,
                )
