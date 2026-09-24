"""Binary Sensor Plattform: 'Lüften empfohlen' pro Raum."""
from __future__ import annotations

import asyncio
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
    CONF_DEHUMIDIFIER_TANK_FULL_ENTITY,
    CONF_DISABLE_CLOSE_RECOMMENDATION,
    CONF_FROST_DEBOUNCE_MINUTES,
    CONF_FROST_PROTECTION_TEMP,
    CONF_HEATING_COMFORT_TEMP,
    CONF_HEATING_ENTITY,
    CONF_HEATING_PRESENCE_ENTITIES,
    CONF_HEATING_STANDBY_TEMP,
    CONF_HEATING_THRESHOLD_TEMP,
    CONF_HEATING_USE_TEMP_SOURCE,
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
    CONF_MSG_CLOSE_OUTDOOR_WETTER,
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
    DEFAULT_HEATING_COMFORT_TEMP,
    DEFAULT_HEATING_STANDBY_TEMP,
    DEFAULT_HEATING_THRESHOLD_TEMP,
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
    DEFAULT_MSG_CLOSE_OUTDOOR_WETTER,
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
    VERSION_KEY,
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
    """Legt die binary_sensor Entität(en) für den konfigurierten Raum an -
    den Haupt-Sensor immer, den separaten "Dusche aktiv"-Sensor nur, falls
    die Duscherkennung für diesen Raum aktiviert ist."""
    room_sensor = SmartVentilationBinarySensor(hass, entry)
    entities: list[BinarySensorEntity] = [room_sensor]
    if entry.data.get(CONF_SHOWER_DETECTION_ENABLED, DEFAULT_SHOWER_DETECTION_ENABLED):
        shower_sensor = SmartVentilationShowerBinarySensor(entry, room_sensor)
        room_sensor.attach_shower_sensor(shower_sensor)
        entities.append(shower_sensor)
    async_add_entities(entities)


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

        self._attr_name = f"{room} Lüftungsempfehlung"
        self._attr_unique_id = f"{entry.entry_id}_lueften_empfohlen"
        self._attr_is_on = False

        # Optionaler, separater "Dusche aktiv"-Sensor (siehe async_setup_entry
        # unten) - nur gesetzt, falls die Duscherkennung für diesen Raum
        # aktiviert ist. Referenz wird nach dem Anlegen beider Entitäten via
        # attach_shower_sensor() gesetzt, damit _evaluate() dessen Zustand
        # bei jeder Neubewertung mit aktualisieren kann.
        self._shower_sensor: "SmartVentilationShowerBinarySensor | None" = None

        self._open_since = None
        self._last_notified_at = None
        self._last_reason: str | None = None
        self._unsub_tick = None

        # Ob aktuell eine Push- bzw. persistente Web-Benachrichtigung
        # angezeigt wird, die noch nicht durch eine "clean notification"
        # aufgelöst wurde - siehe _maybe_clear_notifications().
        self._mobile_notification_active = False
        self._persistent_notification_active = False

        # Zuletzt kommandierter Soll-Zustand der optionalen Geräte.
        # None = noch nicht initial synchronisiert.
        self._dehumidifier_state: bool | None = None
        self._ac_state: bool | None = None
        # True = zuletzt Comfort-Sollwert gesetzt, False = Standby, None =
        # noch nicht initial synchronisiert - siehe _update_heating().
        self._heating_state: bool | None = None

        # Rein informativer Ein-/Ausschalt-Grund für die Dashboard-Karte
        # (neue Geräte-Tabelle, siehe README) - live bei jeder Neubewertung
        # in _evaluate() gesetzt, keine Steuerungswirkung.
        self._dehumidifier_reason = ""
        self._ac_reason = ""
        self._heating_reason = ""

        # Seit wann die Einspeiseleistung ununterbrochen zu niedrig ist,
        # während das jeweilige Gerät läuft (für die Abschalt-Verzögerung).
        self._dehumidifier_low_power_since = None
        self._ac_low_power_since = None

        # Seit wann frost_block ununterbrochen aktiv ist (für den Debounce,
        # siehe _evaluate()) - gilt gleichermaßen für einen tatsächlich
        # niedrigen Messwert UND einen fehlenden Außensensor.
        self._frost_block_since = None

        # Rollierendes Zeitfenster (Zeitpunkt, Luftfeuchtigkeit) für die
        # Duscherkennung - siehe _update_shower_detection().
        self._humidity_samples: deque[tuple] = deque()
        self._showering = False

        # Seit wann Luftentfeuchter/Klimaanlage/Heizung/Dusche ununterbrochen
        # aktiv sind (Dashboard-Karte, Spalte "Laufzeit") - Luftentfeuchter/
        # Klimaanlage/Heizung werden live in extra_state_attributes gepflegt
        # (dort wird ohnehin schon der Live-Zustand für die Anzeige gelesen,
        # siehe Lektion 19), Dusche in _evaluate() neben self._showering.
        self._dehumidifier_on_since = None
        self._ac_on_since = None
        self._heating_on_since = None
        self._shower_on_since = None

    def attach_shower_sensor(
        self, shower_sensor: "SmartVentilationShowerBinarySensor"
    ) -> None:
        """Verknüpft den separaten 'Dusche aktiv'-Sensor mit diesem Raum -
        siehe async_setup_entry()."""
        self._shower_sensor = shower_sensor

    @property
    def showering(self) -> bool:
        """Aktueller Duscherkennungs-Zustand - vom separaten 'Dusche aktiv'-
        Sensor gelesen (siehe SmartVentilationShowerBinarySensor)."""
        return self._showering

    @property
    def extra_state_attributes(self) -> dict:
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
        co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY))
        outdoor_temp_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        outdoor_temp = self._get_float_state(outdoor_temp_entity)
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
        integration_version = self.hass.data.get(DOMAIN, {}).get(VERSION_KEY)
        if integration_version:
            # Nur für die Dashboard-Karte (Versionsanzeige) - identisch für
            # jeden Raum, da es sich um die Version der gesamten Integration
            # handelt, nicht um eine Raum-Eigenschaft.
            attrs["integration_version"] = integration_version
        if self._config.get(CONF_NO_WINDOW, False):
            # Nur gesetzt, wenn "kein Fenster" - Standardfall (Fenster
            # vorhanden) fügt bewusst nichts hinzu, um bestehende Dashboards
            # nicht zu verändern.
            attrs["hat_fenster"] = False
        if self._config.get(CONF_DISABLE_CLOSE_RECOMMENDATION, False):
            # Nur gesetzt, wenn aktiv - Dashboard-Karten berechnen Auslöser/
            # Empfehlung sonst komplett live aus Messwerten/Schwellen (siehe
            # README), unabhängig vom tatsächlichen should_close in
            # _evaluate(). Ohne dieses Attribut würde eine Karte für diesen
            # Raum weiterhin eine reine Komfort-Schließempfehlung (Temperatur/
            # Feuchtigkeit/CO2/Winter-Höchstdauer) anzeigen, obwohl der Raum
            # genau das deaktiviert hat. Frost-/Hitzeschutz bleiben davon
            # unberührt.
            attrs["schliessempfehlung_deaktiviert"] = True
        if outdoor_temp is not None:
            attrs["aussentemperatur"] = outdoor_temp
        if outdoor_temp_entity:
            # Nur für Dashboard-Karten (Live-Auswertung "Frostschutz"/
            # "Hitzeschutz" ohne Rückgriff auf das historische letzter_grund) -
            # unabhängig vom aktuellen Sensorwert, damit die Schwelle auch bei
            # kurzzeitig fehlendem Sensor sichtbar bleibt.
            attrs["schwelle_frostschutz"] = self._effective(
                CONF_FROST_PROTECTION_TEMP, DEFAULT_FROST_PROTECTION_TEMP
            )
            attrs["schwelle_hitzeschutz"] = self._effective(
                CONF_HEAT_PROTECTION_TEMP, DEFAULT_HEAT_PROTECTION_TEMP
            )
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
            if self._shower_on_since is not None:
                attrs["dusche_seit"] = self._shower_on_since.isoformat()
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
        if self._config.get(
            CONF_DEHUMIDIFIER_ENTITY
        ) and not self._device_entity_missing(self._config[CONF_DEHUMIDIFIER_ENTITY]):
            dehumidifier_on = self._is_device_on(self._config[CONF_DEHUMIDIFIER_ENTITY])
            if dehumidifier_on:
                if self._dehumidifier_on_since is None:
                    self._dehumidifier_on_since = dt_util.utcnow()
                attrs["luftentfeuchter_seit"] = self._dehumidifier_on_since.isoformat()
            else:
                self._dehumidifier_on_since = None
            attrs["luftentfeuchter_an"] = dehumidifier_on
            attrs["luftentfeuchter_grund"] = self._dehumidifier_reason
        tank_full_entity = self._config.get(CONF_DEHUMIDIFIER_TANK_FULL_ENTITY)
        if tank_full_entity:
            # Rein informativ für die Dashboard-Karte (Zusatz "(Fehler)" beim
            # Luftentfeuchter-Status) - live gelesen, kein RestoreEntity nötig,
            # da es sich um eine fremde, bereits selbst zustandsbehaftete
            # Entität handelt, keinen internen Zustand dieser Integration.
            tank_full_state = self.hass.states.get(tank_full_entity)
            attrs["luftentfeuchter_tank_fehler"] = (
                tank_full_state is not None and tank_full_state.state == "on"
            )
        if self._config.get(CONF_AC_ENTITY) and not self._device_entity_missing(
            self._config[CONF_AC_ENTITY]
        ):
            ac_on = self._is_device_on(self._config[CONF_AC_ENTITY])
            if ac_on:
                if self._ac_on_since is None:
                    self._ac_on_since = dt_util.utcnow()
                attrs["klimaanlage_seit"] = self._ac_on_since.isoformat()
            else:
                self._ac_on_since = None
            attrs["klimaanlage_an"] = ac_on
            attrs["klimaanlage_grund"] = self._ac_reason
        heating_entity = self._get_heating_entity_id()
        if heating_entity and not self._device_entity_missing(heating_entity):
            # "an" bedeutet hier nicht (wie bei Luftentfeuchter/Klimaanlage)
            # ein einfaches Ein/Aus, sondern ob der aktuell am Gerät
            # eingestellte Sollwert näher am Comfort- als am
            # Standby-Sollwert liegt - live vom Gerät gelesen (Lektion 19/33:
            # eine andere Automation oder der Nutzer selbst könnte den
            # Sollwert direkt am Thermostat geändert haben, ohne dass diese
            # Integration davon weiß).
            comfort_temp = self._effective(CONF_HEATING_COMFORT_TEMP, DEFAULT_HEATING_COMFORT_TEMP)
            standby_temp = self._effective(CONF_HEATING_STANDBY_TEMP, DEFAULT_HEATING_STANDBY_TEMP)
            current_target = self._get_heating_target_temperature(heating_entity)
            heating_comfort_active = current_target is not None and abs(
                current_target - comfort_temp
            ) < abs(current_target - standby_temp)
            if heating_comfort_active:
                if self._heating_on_since is None:
                    self._heating_on_since = dt_util.utcnow()
                attrs["heizung_seit"] = self._heating_on_since.isoformat()
            else:
                self._heating_on_since = None
            attrs["heizung_an"] = heating_comfort_active
            attrs["heizung_zieltemperatur"] = current_target
            attrs["heizung_grund"] = self._heating_reason
            attrs["schwelle_heizung"] = self._effective(
                CONF_HEATING_THRESHOLD_TEMP, DEFAULT_HEATING_THRESHOLD_TEMP
            )
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
            if "heizung_an" in attrs:
                self._heating_state = bool(attrs["heizung_an"])
            # Laufzeit-Zeitstempel wiederherstellen (sonst zeigt die
            # Dashboard-Karte nach jedem Neustart fälschlich "0 Min", obwohl
            # das Gerät schon länger läuft) - werden beim nächsten Lesen von
            # extra_state_attributes sofort korrigiert, falls das Gerät
            # zwischenzeitlich tatsächlich aus war (siehe dort).
            if "luftentfeuchter_seit" in attrs:
                self._dehumidifier_on_since = dt_util.parse_datetime(
                    attrs["luftentfeuchter_seit"]
                )
            if "klimaanlage_seit" in attrs:
                self._ac_on_since = dt_util.parse_datetime(attrs["klimaanlage_seit"])
            if "heizung_seit" in attrs:
                self._heating_on_since = dt_util.parse_datetime(attrs["heizung_seit"])
            if "dusche_seit" in attrs:
                self._shower_on_since = dt_util.parse_datetime(attrs["dusche_seit"])

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

    def _is_window_confirmed_open(self) -> bool:
        """Liest den Fensterkontakt-Sensor live und liefert True nur bei
        einer tatsächlichen Bestätigung "offen" - ohne konfigurierten
        Fensterkontakt oder bei unbekanntem/unverfügbarem Zustand wird
        permissiv False zurückgegeben (kein Grund, davon auszugehen, dass
        das Fenster offen ist). Für die Luftentfeuchter-Pausier-Logik
        gedacht (siehe _update_devices()) - bewusst unabhängig von
        _window_action_needed(), das eine andere Frage beantwortet
        (Benachrichtigung nötig?) und bei fehlenden Daten absichtlich das
        Gegenteil (True) liefert.
        """
        window_entity = self._config.get(CONF_WINDOW_ENTITY)
        if not window_entity:
            return False
        state = self.hass.states.get(window_entity)
        if state is None or state.state not in ("on", "off"):
            return False
        return state.state == "on"

    def _is_heating_presence_away(self) -> bool:
        """True nur, wenn für die Heizung mindestens eine Anwesenheits-
        Entität konfiguriert ist UND ALLE davon bestätigt "not_home" melden.

        Meldet mindestens eine "home", oder ist der Zustand einer von ihnen
        gerade unbekannt/nicht verfügbar, wird permissiv False zurückgegeben
        (kein Grund, die Heizung deswegen zu pausieren) - ein einzelner
        GPS-Aussetzer eines Trackers soll nicht fälschlich die Heizung
        abschalten. Ohne konfigurierte Entität immer False (keine
        Auswirkung, wie bisher)."""
        entities = self._config.get(CONF_HEATING_PRESENCE_ENTITIES) or []
        if not entities:
            return False
        for entity_id in entities:
            state = self.hass.states.get(entity_id)
            if state is None or state.state != "not_home":
                return False
        return True

    def _is_device_on(self, entity_id: str) -> bool:
        """Liest den tatsächlichen Live-Zustand einer Geräte-Entität
        (Luftentfeuchter/Klimaanlage) für die Dashboard-Anzeige - unabhängig
        davon, ob DIESE Integration das Gerät zuletzt selbst ein-/
        ausgeschaltet hat (dafür dienen weiterhin die intern getrackten
        _dehumidifier_state/_ac_state, siehe _update_single_device()).
        Ohne diesen Live-Read zeigte die Karte ein manuell oder von einer
        anderen Automation eingeschaltetes Gerät fälschlich als "aus" an.

        `switch`/`humidifier` nutzen das binäre "on"/"off"-Schema; `climate`
        dagegen echte Betriebsmodi (z. B. "cool"/"heat"/"auto") - dort
        bedeutet "an" jeder Zustand außer "off".
        """
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return False
        if entity_id.split(".")[0] == "climate":
            return state.state != "off"
        return state.state == "on"

    def _get_heating_entity_id(self) -> str | None:
        """Liefert die für die Heizungssteuerung tatsächlich zu verwendende
        Entity-ID.

        Ist CONF_HEATING_USE_TEMP_SOURCE aktiv, wird die bereits als
        Innentemperatur-Quelle gewählte Entität wiederverwendet, statt eine
        zweite, eigene Auswahl in CONF_HEATING_ENTITY zu verlangen - erspart
        die doppelte Auswahl derselben climate-Entität. Nur wirksam, wenn
        diese Entität tatsächlich aus der "climate"-Domain kommt (siehe
        HEATING_DOMAINS) - eine sensor-/number-/input_number-Temperaturquelle
        unterstützt kein climate.set_temperature und wird daher wie "keine
        Heizung konfiguriert" behandelt (permissiv, kein Formularfehler).
        CONF_HEATING_ENTITY selbst bleibt bei aktivem Schalter unbeachtet."""
        if self._config.get(CONF_HEATING_USE_TEMP_SOURCE, False):
            temp_source = self._config[CONF_TEMP_SOURCE_ENTITY]
            return temp_source if temp_source.split(".")[0] == "climate" else None
        return self._config.get(CONF_HEATING_ENTITY)

    def _get_heating_target_temperature(self, entity_id: str) -> float | None:
        """Liest den aktuell am Heizungs-Gerät eingestellten Sollwert
        (Attribut "temperature") live aus - dient sowohl der Dashboard-
        Anzeige als auch der Bestimmung, ob das Gerät gerade näher am
        Comfort- oder am Standby-Sollwert steht (siehe extra_state_attributes)."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        try:
            return float(state.attributes.get("temperature"))
        except (TypeError, ValueError):
            return None

    def _device_entity_missing(self, entity_id: str) -> bool:
        """True, wenn die Entität komplett aus dem Zustandsautomaten
        verschwunden ist - z. B. weil ihr Integrationseintrag deaktiviert
        wurde. Anders als eine bloß vorübergehende "unavailable"/"unknown"-
        Meldung (Gerät kurz offline, Entität aber weiterhin registriert,
        siehe _is_device_on()) gibt es hier gar keine Entität mehr, die
        gesteuert werden könnte - das Gerät soll dann für die aktuelle
        Neubewertung komplett unberücksichtigt bleiben, nicht nur als "aus"
        angezeigt werden.
        """
        return self.hass.states.get(entity_id) is None

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
        heating_threshold = self._effective(
            CONF_HEATING_THRESHOLD_TEMP, DEFAULT_HEATING_THRESHOLD_TEMP
        )
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
        # Ein einzelner Ausreißer-Messwert oder eine kurze Sensor-
        # Nichtverfügbarkeit (Sensor-Glitch, typischerweise durch einen
        # HA-Neustart bedingt - der Außensensor lädt noch, siehe Lektion 2)
        # soll nicht sofort eine bereits aktive Öffnen-Empfehlung samt
        # Benachrichtigung beenden. Gilt daher gleichermaßen für einen
        # tatsächlich niedrigen Messwert UND für einen fehlenden Sensor -
        # beide Fälle lösen frost_block gleichermaßen aus (siehe oben) und
        # werden hier über EINEN gemeinsamen Zeitstempel verfolgt, seit wann
        # frost_block ununterbrochen aktiv ist. Das reine Blockieren des
        # Öffnens (frost_block oben) bleibt dagegen bewusst sofort/
        # ungebounct - konservativ zu bleiben ist risikofrei.
        # frost_debounce_minutes <= 0 schaltet den Debounce komplett ab
        # (sofortiges Schließen wie vor 0.36.0).
        if frost_block:
            if self._frost_block_since is None:
                self._frost_block_since = dt_util.utcnow()
        else:
            self._frost_block_since = None
        frost_block_confirmed = frost_block and (
            frost_debounce_minutes <= 0
            or (
                self._frost_block_since is not None
                and (dt_util.utcnow() - self._frost_block_since).total_seconds() / 60
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
        # --- Luftentfeuchter pausieren, solange das Fenster offen ist UND
        # die Außenluft dabei nicht hilft (nicht absolut trockener als
        # drinnen) - sonst arbeitet er nur gegen ständig nachströmende
        # feuchte Luft an und verschwendet Energie. Nutzt bewusst dasselbe
        # outdoor_drier_enough-Flag wie die Fenster-Öffnen-Empfehlung (keine
        # doppelte Vergleichslogik): ohne Außen-Luftfeuchtigkeitssensor
        # bleibt es wie bisher permissiv (nie pausiert), mit Sensor pausiert
        # es sowohl bei bestätigt feuchterer Außenluft als auch - konservativ
        # - bei fehlenden Werten. Ist das Fenster geschlossen, hat diese
        # Bedingung keine Wirkung - der Luftentfeuchter läuft dann weiterhin
        # rein nach den Innen-Luftfeuchtigkeits-Schwellen.
        #
        # Ausnahme: Ist genug Einspeiseleistung vorhanden (derselbe Check wie
        # beim eigentlichen Einschalten, siehe _check_power_ok()), entfällt
        # das Energiespar-Argument dieser Pausierung - überschüssige, sonst
        # ungenutzte Leistung zu verbrauchen ist kein Verlust, auch wenn der
        # Luftentfeuchter dabei "nur" gegen nachströmende feuchte Luft
        # ankämpft. Nur relevant, wenn überhaupt ein Leistungssensor
        # konfiguriert ist - ohne Sensor bleibt die Pausierung unverändert
        # wirksam (nicht permissiv, siehe _check_power_ok()s eigener
        # Rückgabewert `True` ohne konfigurierten Sensor).
        power_entity_configured = bool(self._effective(CONF_POWER_ENTITY, None))
        dehumidifier_pause_open_window = (
            self._is_window_confirmed_open()
            and not outdoor_drier_enough
            and not (power_entity_configured and self._check_power_ok())
        )
        # --- Heizung: zwei feste Sollwerte (Comfort/Standby) statt einfachem
        # Ein/Aus, wie für Heizungen üblich - siehe CONF_HEATING_COMFORT_TEMP/
        # CONF_HEATING_STANDBY_TEMP in const.py. Comfort unterhalb der
        # Schwelle, Standby erst ab Schwelle + Toleranz-Marge (Hysterese,
        # dieselbe margin wie bei den anderen Temperaturvergleichen) - dazwischen
        # bleibt der zuletzt gesetzte Sollwert unverändert. Ist indoor_temp
        # gerade nicht verfügbar, wird bewusst NICHTS geändert (weder Comfort
        # noch Standby) - anders als beim Frostschutz ist ein falsches Timing
        # hier nicht sicherheitsrelevant, nur unkomfortabel, ein Umschalten
        # ohne verlässlichen Messwert also nicht gerechtfertigt.
        # Pausiert (Standby) zusätzlich, solange das Fenster bestätigt offen
        # ist (_is_window_confirmed_open(), dasselbe Muster wie bei der
        # Luftentfeuchter-Pausierung) - gegen ein offenes Fenster zu heizen
        # verschwendet nur Energie. Ebenso pausiert (Standby), solange
        # niemand zuhause ist (_is_heating_presence_away()) - nur relevant,
        # wenn mindestens eine Anwesenheits-Entität konfiguriert ist.
        window_confirmed_open = self._is_window_confirmed_open()
        heating_presence_away = self._is_heating_presence_away()
        want_heating_comfort = (
            indoor_temp is not None
            and indoor_temp < heating_threshold
            and not window_confirmed_open
            and not heating_presence_away
        )
        want_heating_standby = (
            window_confirmed_open
            or heating_presence_away
            or (indoor_temp is not None and indoor_temp >= heating_threshold + margin)
        )

        # --- Rein informative Ein-/Ausschalt-Gründe für Luftentfeuchter/
        # Klimaanlage (Dashboard-Karte, neue Geräte-Tabelle, siehe README) -
        # spiegeln dieselbe Priorität wie want_on/want_off in
        # _update_devices() wider, haben selbst aber keine Steuerungswirkung.
        # Live bei jeder Neubewertung neu gesetzt (wie self._showering),
        # nicht nur bei einem tatsächlichen Zustandswechsel.
        if self._config.get(CONF_DEHUMIDIFIER_ENTITY):
            if not self._config.get(CONF_HUMIDITY_ENTITY):
                self._dehumidifier_reason = "kein Feuchtigkeitssensor konfiguriert"
            elif humidity_needs_close:
                self._dehumidifier_reason = "Luftfeuchtigkeit unter Schwelle"
            elif dehumidifier_pause_open_window:
                self._dehumidifier_reason = (
                    "pausiert: Fenster offen, Außenluft nicht trockener"
                )
            elif humidity_needs_open:
                self._dehumidifier_reason = "Luftfeuchtigkeit über Schwelle"
            else:
                self._dehumidifier_reason = "im Sollbereich, hält letzten Zustand"
            if self._effective(CONF_POWER_ENTITY, None) and not self._check_power_ok():
                self._dehumidifier_reason += " (Einspeiseleistung zu gering)"
        if self._config.get(CONF_AC_ENTITY):
            if temp_needs_close:
                self._ac_reason = "Innentemperatur unter Schwelle"
            elif outdoor_cooler_enough:
                self._ac_reason = (
                    "Lüften reicht aus (Außenluft kühler)"
                    if temp_needs_open
                    else "im Sollbereich, hält letzten Zustand"
                )
            elif temp_needs_open:
                self._ac_reason = "Innentemperatur über Schwelle"
            else:
                self._ac_reason = "im Sollbereich, hält letzten Zustand"
            if self._effective(CONF_POWER_ENTITY, None) and not self._check_power_ok():
                self._ac_reason += " (Einspeiseleistung zu gering)"
        if self._get_heating_entity_id():
            if window_confirmed_open:
                self._heating_reason = "pausiert: Fenster offen"
            elif heating_presence_away:
                self._heating_reason = "pausiert: niemand zuhause"
            elif want_heating_standby:
                self._heating_reason = "Innentemperatur über Schwelle, Standby"
            elif want_heating_comfort:
                self._heating_reason = "Innentemperatur unter Schwelle, Comfort"
            else:
                self._heating_reason = "im Sollbereich, hält letzten Zustand"
        # --- Schließen: Außenluft ist inzwischen (wieder) absolut feuchter
        # als die Innenluft - das Pendant zu outdoor_warmer_again weiter
        # unten, nur für Luftfeuchtigkeit statt Temperatur. outdoor_drier_enough
        # oben gilt nur einmalig als Öffnen-Gate; einmal geöffnet, wird dieser
        # Vergleich sonst nicht mehr erneut geprüft - eine bereits aktive
        # "bitte öffnen"-Empfehlung wegen Luftfeuchtigkeit bliebe sonst auch
        # dann bestehen, wenn Lüften die Luftfeuchtigkeit längst nur noch
        # verschlimmern würde. Bewusst NUR bei vollständig vorliegenden
        # Werten ausgelöst (nicht schon bei fehlendem Sensor/Messwert - anders
        # als beim konservativen Öffnen-Gate oben ist "wir wissen es nicht"
        # hier kein Sicherheits-, sondern ein reiner Komfort-Fall, der ohne
        # positive Bestätigung nicht vorsorglich schließen soll).
        outdoor_humidity_confirmed_worse = (
            outdoor_humidity_entity is not None
            and outdoor_humidity is not None
            and humidity is not None
            and indoor_temp is not None
            and outdoor_temp is not None
            and self._absolute_humidity(outdoor_temp, outdoor_humidity)
            >= self._absolute_humidity(indoor_temp, humidity)
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
        if self._showering:
            if self._shower_on_since is None:
                self._shower_on_since = dt_util.utcnow()
        else:
            self._shower_on_since = None
        if self._shower_sensor is not None and self._shower_sensor.hass is not None:
            # hass kann bei der allerersten Bewertung noch None sein, falls
            # beide Entitäten gerade erst gleichzeitig hinzugefügt werden
            # (Reihenfolge zwischen den beiden async_added_to_hass()-Aufrufen
            # nicht garantiert) - der Shower-Sensor schreibt seinen eigenen
            # Startzustand in diesem Fall selbst (siehe dort), spätestens der
            # nächste Tick/Zustandswechsel holt den Rest nach.
            self._shower_sensor.async_write_ha_state()

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
                dehumidifier_pause_open_window=dehumidifier_pause_open_window,
                want_heating_comfort=want_heating_comfort,
                want_heating_standby=want_heating_standby,
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

        # --- Schließen: Pendant zu close_by_summer_outdoor, nur für
        # Luftfeuchtigkeit statt Temperatur (siehe outdoor_humidity_confirmed_worse
        # oben) - schließt nicht, solange Temperatur oder CO2 noch
        # Lüftungsbedarf anzeigen, analog zu den anderen Schließ-Bedingungen.
        close_by_humidity_outdoor_reversal = (
            self._attr_is_on
            and outdoor_humidity_confirmed_worse
            and not temp_still_needed
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
        # frost_block_confirmed (erst nach Debounce, siehe oben) - gilt für
        # fehlenden Sensor UND echten niedrigen Messwert gleichermaßen.
        close_by_frost = self._attr_is_on and frost_block_confirmed
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

        # Auf Raumwunsch abschaltbar: Temperatur/Luftfeuchtigkeit/CO2/
        # Winter-Höchstdauer/Sommer-Fall sind reine Komfort-Empfehlungen und
        # werden komplett übersprungen, wenn eine "bitte schließen"-
        # Empfehlung für diesen Raum nicht sinnvoll umsetzbar ist (z. B.
        # unzuverlässiger Fensterkontakt oder eine Klimaanlage, die die
        # Kühlung ohnehin übernimmt) - siehe CONF_DISABLE_CLOSE_RECOMMENDATION
        # in const.py. Frost-/Hitzeschutz sind davon bewusst AUSGENOMMEN:
        # das sind Sicherheits-, keine Komfort-Bedingungen und schließen
        # weiterhin immer sofort.
        disable_close_recommendation = self._config.get(
            CONF_DISABLE_CLOSE_RECOMMENDATION, False
        )
        should_close = close_by_frost or close_by_heat or (
            not disable_close_recommendation
            and (
                close_by_temp
                or close_by_humidity
                or close_by_co2
                or close_by_summer_outdoor
                or close_by_humidity_outdoor_reversal
                or close_by_duration
            )
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
            "open_by: temp=%s hum=%s co2=%s | frost_block=%s (sensor_missing=%s block_confirmed=%s) heat_block=%s | "
            "still_needed: temp=%s hum=%s co2=%s | "
            "close_by: temp=%s hum=%s co2=%s summer=%s hum_outdoor_reversal=%s duration=%s frost=%s heat=%s | "
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
            frost_block_confirmed,
            heat_block,
            temp_still_needed,
            humidity_still_needed,
            co2_still_needed,
            close_by_temp,
            close_by_humidity,
            close_by_co2,
            close_by_summer_outdoor,
            close_by_humidity_outdoor_reversal,
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
            elif close_by_humidity_outdoor_reversal:
                reason = "outdoor_wetter"

        # Schließen wegen CO2 (Rückkehr unter die Schließen-Schwelle) ist
        # anders als Frost-/Hitzeschutz kein Sicherheitsrisiko - niedriges
        # CO2 ist unproblematisch, es gibt dafür keine "zu niedrig"-Gefahr.
        # Der Grund bleibt trotzdem ehrlich "co2" (anders als
        # silent_frost_close - hier gibt es einen echten Messwert, keine
        # irreführende Anzeige zu vermeiden), nur die Benachrichtigung
        # entfällt, da kein zwingender Handlungsbedarf besteht.
        silent_co2_close = reason == "co2" and should_close and self._attr_is_on

        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self._last_reason = None if silent_frost_close else reason
            if new_state:
                self._open_since = dt_util.utcnow()
            else:
                self._open_since = None
            self.async_write_ha_state()
            if silent_frost_close or silent_co2_close:
                self._last_notified_at = None
            elif self._window_action_needed(new_state):
                self._last_notified_at = dt_util.utcnow()
                await self._notify(new_state, reason)
            else:
                # Fensterkontakt zeigt bereits den gewünschten Zustand
                # (offen/geschlossen) - keine Benachrichtigung nötig.
                self._last_notified_at = None
            await self._maybe_clear_notifications()
            await self._update_devices(
                temp_needs_open=temp_needs_open,
                temp_needs_close=temp_needs_close,
                humidity_needs_open=humidity_needs_open,
                humidity_needs_close=humidity_needs_close,
                outdoor_cooler_enough=outdoor_cooler_enough,
                dehumidifier_pause_open_window=dehumidifier_pause_open_window,
                want_heating_comfort=want_heating_comfort,
                want_heating_standby=want_heating_standby,
            )
            return

        await self._update_devices(
            temp_needs_open=temp_needs_open,
            temp_needs_close=temp_needs_close,
            humidity_needs_open=humidity_needs_open,
            humidity_needs_close=humidity_needs_close,
            outdoor_cooler_enough=outdoor_cooler_enough,
            dehumidifier_pause_open_window=dehumidifier_pause_open_window,
            want_heating_comfort=want_heating_comfort,
            want_heating_standby=want_heating_standby,
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

        # Auch ohne Zustandswechsel der Empfehlung selbst kann sich eine
        # laufende Benachrichtigung erledigt haben - z. B. wenn die Person
        # das Fenster bereits geöffnet/geschlossen hat, die zugrunde
        # liegenden Werte sich aber noch nicht normalisiert haben
        # (Fensterkontakt ist eine verfolgte Entität, löst also ebenfalls
        # eine Neubewertung aus).
        await self._maybe_clear_notifications()

    async def _maybe_clear_notifications(self) -> None:
        """Löst eine zuvor gesendete Push- und/oder persistente Web-
        Benachrichtigung auf, sobald der Fensterkontakt bereits den aktuell
        gewünschten Zustand erreicht hat - unabhängig davon, ob dies durch
        einen echten Zustandswechsel der Empfehlung ausgelöst wurde (dann
        übernimmt das für die Web-Benachrichtigung bereits
        persistent_notification.dismiss in _notify() selbst) oder die
        Person das Fenster einfach bereits von sich aus bedient hat, ohne
        dass sich die Empfehlung selbst ändert - dafür ist diese zentrale
        Prüfung nötig, da sie nicht an einen Zustandswechsel gebunden ist
        und für beide Kanäle gleichermaßen gelten soll."""
        if self._window_action_needed(self._attr_is_on):
            return
        if self._mobile_notification_active:
            await self._clear_mobile_notification()
        if self._persistent_notification_active:
            await self._clear_persistent_notification()

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
        dehumidifier_pause_open_window: bool,
        want_heating_comfort: bool,
        want_heating_standby: bool,
    ) -> None:
        """Steuert optionalen Luftentfeuchter, optionale Klimaanlage und
        optionale Heizung.

        - Luftentfeuchter: an bei hoher Luftfeuchtigkeit, aus bei niedriger -
          unabhängig vom Fenster-Status, außer das Fenster ist offen UND die
          Außenluft ist dabei nicht absolut trockener als drinnen
          (dehumidifier_pause_open_window - siehe _evaluate()) - dann
          pausiert er, statt gegen nachströmende feuchte Luft zu arbeiten.
        - Klimaanlage: an, wenn drinnen zu warm UND Lüften nicht helfen würde
          (draußen nicht kühler) - ergänzt also die Fensterlogik, statt sie zu
          duplizieren. Aus, sobald die Zieltemperatur erreicht ist oder Lüften
          wieder ausreicht. Ist ein Rollladen hinterlegt, fährt dieser beim
          Einschalten herunter und beim Ausschalten wieder hoch.
        - Heizung: kein Ein/Aus, sondern Umschalten zwischen einem Comfort-
          und einem Standby-Sollwert (siehe _update_heating()) - pausiert
          (Standby) zusätzlich bei bestätigt offenem Fenster.
        - Ein konfigurierter Leistungssensor blockiert das Einschalten von
          Luftentfeuchter/Klimaanlage. Ist ein Gerät bereits an, wird es erst
          nach Ablauf der Abschalt-Verzögerung wegen dauerhaft zu geringer
          Einspeisung wieder ausgeschaltet. Die Heizung ist davon unberührt.
        """
        await self._update_single_device(
            entity_key=CONF_DEHUMIDIFIER_ENTITY,
            state_attr="_dehumidifier_state",
            low_power_attr="_dehumidifier_low_power_since",
            want_on=humidity_needs_open and not dehumidifier_pause_open_window,
            want_off=humidity_needs_close or dehumidifier_pause_open_window,
        )
        await self._update_single_device(
            entity_key=CONF_AC_ENTITY,
            state_attr="_ac_state",
            low_power_attr="_ac_low_power_since",
            want_on=temp_needs_open and not outdoor_cooler_enough,
            want_off=temp_needs_close or outdoor_cooler_enough,
            shutter_key=CONF_SHUTTER_ENTITY,
        )
        await self._update_heating(
            want_comfort=want_heating_comfort,
            want_standby=want_heating_standby,
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
        if self._device_entity_missing(entity_id):
            # Integrationseintrag deaktiviert oder Entität sonst komplett
            # entfernt - kein Steuerversuch gegen eine nicht existierende
            # Entität, und der interne Soll-Zustand-Tracker wird
            # zurückgesetzt, damit bei Rückkehr der Entität eine sauber
            # neue Synchronisierung stattfindet, statt auf einem
            # veralteten Zustand aufzusetzen.
            setattr(self, state_attr, None)
            setattr(self, low_power_attr, None)
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

    async def _update_heating(self, *, want_comfort: bool, want_standby: bool) -> None:
        """Steuert eine optionale Heizung über zwei feste Sollwerte (Comfort/
        Standby, siehe const.py) statt eines einfachen Ein/Aus wie bei
        Luftentfeuchter/Klimaanlage - für Heizungen ist das die übliche
        Betriebsart. want_standby hat Vorrang vor want_comfort (analog zu
        want_off vs. want_on in _update_single_device())."""
        entity_id = self._get_heating_entity_id()
        if not entity_id:
            return
        if self._device_entity_missing(entity_id):
            self._heating_state = None
            return

        current = self._heating_state
        if want_standby and current is not False:
            standby_temp = self._effective(
                CONF_HEATING_STANDBY_TEMP, DEFAULT_HEATING_STANDBY_TEMP
            )
            await self._set_heating_temperature(entity_id, standby_temp)
            self._heating_state = False
        elif want_comfort and not want_standby and current is not True:
            comfort_temp = self._effective(
                CONF_HEATING_COMFORT_TEMP, DEFAULT_HEATING_COMFORT_TEMP
            )
            await self._set_heating_temperature(entity_id, comfort_temp)
            self._heating_state = True

    async def _set_heating_temperature(self, entity_id: str, temperature: float) -> None:
        """Setzt den Sollwert einer Heizungs-climate-Entität.

        blocking=True (anders als _set_device_state()/_set_shutter(), die
        bewusst blocking=False verwenden) - climate.set_temperature validiert
        den übergebenen Wert gegen das Schema der Ziel-Entität (u. a.
        min_temp/max_temp/target_temp_step), ein Validierungsfehler passiert
        bei blocking=False in einem unbeobachteten Hintergrund-Task und würde
        vom try/except hier nicht abgefangen (siehe CLAUDE.md, Lektion 35)."""
        try:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"entity_id": entity_id, "temperature": temperature},
                blocking=True,
            )
        except HomeAssistantError:
            _LOGGER.warning(
                "Konnte Sollwert für Heizung %s nicht auf %s setzen (Raum %s)",
                entity_id,
                temperature,
                self._config[CONF_ROOM_NAME],
            )

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
        if context_reason == "outdoor_wetter":
            outdoor_humidity = self._get_float_state(
                self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
            )
            outdoor_temp = self._get_float_state(
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
            )
            indoor_temp = self._get_indoor_temperature()
            humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
            outdoor_abs = (
                self._absolute_humidity(outdoor_temp, outdoor_humidity)
                if outdoor_temp is not None and outdoor_humidity is not None
                else None
            )
            indoor_abs = (
                self._absolute_humidity(indoor_temp, humidity)
                if indoor_temp is not None and humidity is not None
                else None
            )
            return (
                self._format_measurement(outdoor_abs, "g/m³", 1),
                self._format_measurement(indoor_abs, "g/m³", 1),
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
        elif reason == "outdoor_wetter":
            template = self._effective(
                CONF_MSG_CLOSE_OUTDOOR_WETTER, DEFAULT_MSG_CLOSE_OUTDOOR_WETTER
            )
            wert, schwelle = self._measurement_context("outdoor_wetter", opening=False)
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

    def _get_current_volumes(self, entity_ids: list[str]) -> dict[str, float]:
        """Liest die aktuelle Lautstärke jedes Lautsprechers, BEVOR sie für
        die Ansage überschrieben wird - Grundlage für das automatische
        Zurücksetzen danach (siehe _restore_tts_volume()). Lautsprecher, die
        aktuell keinen numerischen `volume_level` melden (z. B. gerade aus
        oder nicht verfügbar), werden ausgelassen - für sie wird später auch
        nichts zurückgesetzt."""
        volumes: dict[str, float] = {}
        for entity_id in entity_ids:
            state = self.hass.states.get(entity_id)
            if state is None:
                continue
            volume = state.attributes.get("volume_level")
            if isinstance(volume, (int, float)):
                volumes[entity_id] = float(volume)
        return volumes

    async def _restore_tts_volume(
        self, original_volumes: dict[str, float], message: str
    ) -> None:
        """Setzt die Lautstärke je Lautsprecher nach der Ansage auf den
        zuvor gelesenen Wert zurück.

        `tts.speak` liefert kein plattformübergreifend zuverlässiges
        "Wiedergabe beendet"-Ereignis (dieselbe Einschränkung, die
        _play_tts() bereits für das nicht automatisch fortgesetzte
        Pausieren dokumentiert) - daher wird die ungefähre Sprechdauer aus
        der Nachrichtenlänge geschätzt (rund 150 Wörter/Minute plus eine
        Pufferzeit für TTS-Generierung/Netzwerk) und entsprechend lange
        gewartet, bevor zurückgesetzt wird. Läuft als eigener
        Hintergrund-Task (siehe _play_tts()), damit die Neubewertung nicht
        auf die geschätzte Ansagedauer warten muss."""
        word_count = len(message.split())
        estimated_seconds = max(2.0, word_count / 2.5) + 1.5
        await asyncio.sleep(estimated_seconds)
        for entity_id, volume in original_volumes.items():
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": entity_id, "volume_level": volume},
                    blocking=False,
                )
            except (HomeAssistantError, TypeError, ValueError):
                _LOGGER.debug(
                    "Konnte Lautstärke für %s nicht zurücksetzen (Raum %s)",
                    entity_id,
                    self._config[CONF_ROOM_NAME],
                )

    async def _play_tts(
        self, sonos_entities: list[str], tts_entity: str, message: str
    ) -> None:
        """Spielt die Ansage ab - inkl. global konfigurierter Lautstärke und
        Pausieren/Überlagern der vorhandenen Wiedergabe.

        Hinweis: `tts.speak` selbst unterstützt keine Lautstärkeangabe: die
        Lautstärke wird deshalb vorher separat per media_player.volume_set
        gesetzt und nach der (geschätzten) Ansagedauer automatisch wieder
        auf den vorherigen Wert zurückgesetzt (siehe _restore_tts_volume()).
        Beim Pausieren wird die vorherige Wiedergabe dagegen weiterhin nicht
        automatisch fortgesetzt - das ist plattformübergreifend nicht
        zuverlässig lösbar.
        """
        volume_percent = self._effective(CONF_TTS_VOLUME, DEFAULT_TTS_VOLUME)
        playback_mode = self._effective(CONF_TTS_PLAYBACK_MODE, DEFAULT_TTS_PLAYBACK_MODE)
        original_volumes = self._get_current_volumes(sonos_entities)

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

        if original_volumes:
            self.hass.async_create_task(
                self._restore_tts_volume(original_volumes, message)
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
                # Fester tag pro Raum: eine neue Benachrichtigung ersetzt auf
                # dem Gerät automatisch eine ggf. noch angezeigte ältere
                # (z. B. "bitte öffnen" -> "bitte schließen"), und markiert,
                # dass hier ggf. noch eine "clean notification" fällig wird
                # (siehe _maybe_clear_notifications()).
                self._mobile_notification_active = True
                for target in targets:
                    entity_id = target.get(CONF_MOBILE_NOTIFY_ENTITY)
                    if not entity_id:
                        continue
                    presence_entity = target.get(CONF_PRESENCE_ENTITY)
                    if self._is_present(presence_entity):
                        await self._send_mobile_push(
                            entity_id, message, title="Lüften"
                        )
                    else:
                        _LOGGER.debug(
                            "Push an %s in Raum %s übersprungen - "
                            "Person/Gerät nicht zuhause",
                            entity_id,
                            room,
                        )

        if persistent_enabled:
            notification_id = self._notification_id()
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
                self._persistent_notification_active = True
            else:
                # Löst die Benachrichtigung automatisch auf, sobald sich
                # die Empfehlung erledigt hat.
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": notification_id},
                    blocking=False,
                )
                self._persistent_notification_active = False

    def _notification_id(self) -> str:
        """Fester, raumeindeutiger Bezeichner - als notification_id für die
        persistente Web-Benachrichtigung und als tag für Push-
        Benachrichtigungen. Erlaubt in beiden Fällen sowohl das Ersetzen
        einer bereits angezeigten Benachrichtigung durch eine neue als auch
        das gezielte Auflösen (persistent_notification.dismiss bzw.
        clear_notification)."""
        return f"smart_ventilation_{self._entry.entry_id}"

    async def _send_mobile_push(
        self, entity_id: str, message: str, *, title: str | None = None
    ) -> None:
        """Verschickt eine App-Push-Nachricht an eine einzelne notify-
        Entität, inkl. `tag` im `data`-Feld für das "clean notification"-
        Muster (siehe _notify()/_clear_mobile_notification(), Lektion 18).

        Bewusst `blocking=True`, obwohl der Rest dieser Integration
        Geräte-Steuerbefehle üblicherweise mit `blocking=False` abfeuert:
        Nicht jede notify-Entität unterstützt ein `data`-Feld (nur echte
        Companion-App-Entitäten tun das zuverlässig) - lehnt die
        Ziel-Entität es per Schema ab, muss der Fehler synchron in diesem
        `await` ankommen, um ihn hier abzufangen. Mit `blocking=False`
        passiert die Schema-Validierung dagegen in einem intern erzeugten,
        von uns nicht beobachteten Task - ein solcher Fehler landet dann
        unabhängig von jedem try/except als "Task exception was never
        retrieved" im Log, wiederholt bei jeder Neubewertung (siehe
        Lektion 35)."""
        data = {
            "entity_id": entity_id,
            "message": message,
            "data": {"tag": self._notification_id()},
        }
        if title is not None:
            data["title"] = title
        try:
            await self.hass.services.async_call(
                "notify", "send_message", data, blocking=True
            )
        except HomeAssistantError:
            _LOGGER.warning(
                "Konnte Push-Benachrichtigung an %s nicht senden (Raum %s) "
                "- unterstützt diese notify-Entität ein `data`-Feld mit "
                "`tag` (z. B. eine Companion-App-Entität)?",
                entity_id,
                self._config[CONF_ROOM_NAME],
            )

    async def _clear_mobile_notification(self) -> None:
        """Löst eine zuvor gesendete Push-Benachrichtigung auf allen
        konfigurierten Zielgeräten auf ("clean notification") - unabhängig
        von der aktuellen Anwesenheit, da ein clear_notification an ein
        Gerät ohne passende (oder bereits aufgelöste) Benachrichtigung
        wirkungslos, aber unschädlich ist."""
        for target in self._get_mobile_targets():
            entity_id = target.get(CONF_MOBILE_NOTIFY_ENTITY)
            if not entity_id:
                continue
            await self._send_mobile_push(entity_id, "clear_notification")
        self._mobile_notification_active = False

    async def _clear_persistent_notification(self) -> None:
        """Löst eine zuvor erstellte persistente Web-Benachrichtigung auf
        ("clean notification") - identisches Muster zu
        _clear_mobile_notification(), nur eben nicht an einen
        Zustandswechsel der Empfehlung gebunden (den deckt bereits
        _notify() über should_ventilate=False ab)."""
        await self.hass.services.async_call(
            "persistent_notification",
            "dismiss",
            {"notification_id": self._notification_id()},
            blocking=False,
        )
        self._persistent_notification_active = False


class SmartVentilationShowerBinarySensor(BinarySensorEntity):
    """True = aktuell wird geduscht (siehe Duscherkennung in
    SmartVentilationBinarySensor._update_shower_detection()).

    Rein abgeleitete Anzeige-Entität ohne eigenen Zustand - liest den
    Duscherkennungs-Wert live vom Haupt-Sensor des Raums (`room_sensor`)
    und wird von diesem bei jeder Neubewertung mit aktualisiert (siehe
    attach_shower_sensor() dort). Nur vorhanden, wenn die Duscherkennung
    für diesen Raum aktiviert ist (siehe async_setup_entry()).
    """

    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_should_poll = False

    def __init__(
        self, entry: ConfigEntry, room_sensor: SmartVentilationBinarySensor
    ) -> None:
        self._room_sensor = room_sensor
        room = entry.data[CONF_ROOM_NAME]
        self._attr_name = f"{room} Dusche aktiv"
        self._attr_unique_id = f"{entry.entry_id}_dusche_aktiv"

    @property
    def is_on(self) -> bool:
        return self._room_sensor.showering

    async def async_added_to_hass(self) -> None:
        """Schreibt einmalig den aktuellen Zustand, sobald diese Entität
        vollständig hinzugefügt ist - unabhängig davon, ob der Haupt-Sensor
        (der ansonsten bei jeder Neubewertung mit aktualisiert, siehe
        attach_shower_sensor()) zu diesem Zeitpunkt bereits selbst
        hinzugefügt wurde (Reihenfolge nicht garantiert)."""
        await super().async_added_to_hass()
        self.async_write_ha_state()
