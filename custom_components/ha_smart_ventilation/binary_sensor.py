"""Binary Sensor Plattform: 'Lüften empfohlen' pro Raum."""
from __future__ import annotations

import asyncio
import logging
import math
from collections import deque
from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CO2_WARM_OUTDOOR_OVERRIDE_FACTOR,
    CONF_AC_ENTITY,
    CONF_CO2_ENTITY,
    CONF_CO2_THRESHOLD_CLOSE,
    CONF_CO2_THRESHOLD_OPEN,
    CONF_DEHUMIDIFIER_ENTITY,
    CONF_DEHUMIDIFIER_TANK_FULL_ENTITY,
    CONF_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED,
    CONF_DEVICE_MAX_RUNTIME_COOLDOWN_MINUTES,
    CONF_DEVICE_MAX_RUNTIME_HIGH_SURPLUS_MINUTES,
    CONF_DEVICE_MAX_RUNTIME_MINUTES,
    CONF_DEVICE_WINDOW_CONFLICT_NOTIFICATION_ENABLED,
    CONF_DISABLE_CLOSE_RECOMMENDATION,
    CONF_FROST_DEBOUNCE_MINUTES,
    CONF_FROST_PROTECTION_TEMP,
    CONF_HEATING_COMFORT_END_WEEKDAY,
    CONF_HEATING_COMFORT_END_WEEKEND,
    CONF_HEATING_COMFORT_START_WEEKDAY,
    CONF_HEATING_COMFORT_START_WEEKEND,
    CONF_HEATING_COMFORT_TEMP,
    CONF_HEATING_ENTITY,
    CONF_HEATING_NIGHT_END_WEEKDAY,
    CONF_HEATING_NIGHT_END_WEEKEND,
    CONF_HEATING_NIGHT_START_WEEKDAY,
    CONF_HEATING_NIGHT_START_WEEKEND,
    CONF_HEATING_NIGHT_TEMP,
    CONF_HEATING_PRESENCE_ENTITIES,
    CONF_HEATING_PRESET_BUILDING_PROTECTION,
    CONF_HEATING_PRESET_COMFORT,
    CONF_HEATING_PRESET_NIGHT,
    CONF_HEATING_PRESET_STANDBY,
    CONF_HEATING_SCHEDULE_ENABLED,
    CONF_HEATING_STANDBY_TEMP,
    CONF_HEATING_THRESHOLD_TEMP,
    CONF_HEATING_USE_PRESET_MODE,
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
    CONF_MSG_DEVICE_WINDOW_CONFLICT,
    CONF_MSG_OPEN_CO2,
    CONF_MSG_OPEN_HUMIDITY,
    CONF_MSG_OPEN_TEMP,
    CONF_MSG_REMINDER,
    CONF_MSG_SHOWER_LONG,
    CONF_MSG_TANK_FULL,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_PERSISTENT_ENABLED,
    CONF_POWER_ENTITY,
    CONF_POWER_GRACE_PERIOD,
    CONF_PRESENCE_ENTITY,
    CONF_REMINDER_INTERVAL,
    CONF_ROOM_NAME,
    CONF_SHOWER_DETECTION_ENABLED,
    CONF_SHOWER_MAX_DURATION,
    CONF_SHOWER_RISE_THRESHOLD,
    CONF_SHUTTER_ENTITY,
    CONF_SONOS_ENTITY,
    CONF_SUMMER_MODE_FORECAST_ATTRIBUTE,
    CONF_SUMMER_MODE_FORECAST_ENTITY,
    CONF_SUMMER_MODE_SWITCH_ENTITY,
    CONF_SUMMER_MODE_THRESHOLD_TEMP,
    CONF_TEMP_ATTRIBUTE,
    CONF_TEMP_MARGIN,
    CONF_TEMP_SOURCE_ENTITY,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_TTS_ENTITY,
    CONF_TTS_LIGHT_ENTITY,
    CONF_TTS_PLAYBACK_MODE,
    CONF_TTS_QUIET_END,
    CONF_TTS_QUIET_HOURS_ENABLED,
    CONF_TTS_QUIET_START,
    CONF_TTS_VOLUME,
    CONF_WINDOW_ENTITY,
    CONF_WINTER_OUTDOOR_THRESHOLD,
    DEFAULT_CO2_THRESHOLD_CLOSE,
    DEFAULT_CO2_THRESHOLD_OPEN,
    DEFAULT_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED,
    DEFAULT_DEVICE_MAX_RUNTIME_COOLDOWN_MINUTES,
    DEFAULT_DEVICE_MAX_RUNTIME_HIGH_SURPLUS_MINUTES,
    DEFAULT_DEVICE_MAX_RUNTIME_MINUTES,
    DEFAULT_DEVICE_WINDOW_CONFLICT_NOTIFICATION_ENABLED,
    DEFAULT_FROST_DEBOUNCE_MINUTES,
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_HEATING_COMFORT_END_WEEKDAY,
    DEFAULT_HEATING_COMFORT_END_WEEKEND,
    DEFAULT_HEATING_COMFORT_START_WEEKDAY,
    DEFAULT_HEATING_COMFORT_START_WEEKEND,
    DEFAULT_HEATING_COMFORT_TEMP,
    DEFAULT_HEATING_NIGHT_END_WEEKDAY,
    DEFAULT_HEATING_NIGHT_END_WEEKEND,
    DEFAULT_HEATING_NIGHT_START_WEEKDAY,
    DEFAULT_HEATING_NIGHT_START_WEEKEND,
    DEFAULT_HEATING_NIGHT_TEMP,
    DEFAULT_HEATING_STANDBY_TEMP,
    DEFAULT_HEATING_THRESHOLD_TEMP,
    DEFAULT_HEATING_USE_PRESET_MODE,
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
    DEFAULT_MSG_DEVICE_WINDOW_CONFLICT,
    DEFAULT_MSG_OPEN_CO2,
    DEFAULT_MSG_OPEN_HUMIDITY,
    DEFAULT_MSG_OPEN_TEMP,
    DEFAULT_MSG_REMINDER,
    DEFAULT_MSG_SHOWER_LONG,
    DEFAULT_MSG_TANK_FULL,
    DEFAULT_POWER_GRACE_PERIOD,
    DEFAULT_REMINDER_INTERVAL,
    DEFAULT_SHOWER_DETECTION_ENABLED,
    DEFAULT_SHOWER_MAX_DURATION,
    DEFAULT_SHOWER_RISE_THRESHOLD,
    DEFAULT_SUMMER_MODE_THRESHOLD_TEMP,
    DEFAULT_TEMP_ATTRIBUTE,
    DEFAULT_TEMP_MARGIN,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DEFAULT_TTS_PLAYBACK_MODE,
    DEFAULT_TTS_QUIET_END,
    DEFAULT_TTS_QUIET_HOURS_ENABLED,
    DEFAULT_TTS_QUIET_START,
    DEFAULT_TTS_VOLUME,
    DEFAULT_WINTER_OUTDOOR_THRESHOLD,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
    SHOWER_MIN_HISTORY_MINUTES,
    SHOWER_MIN_RISE_POINTS,
    SHOWER_RISE_LOOKBACK_MINUTES,
    TTS_PLAYBACK_MODE_PAUSE,
    VERSION_KEY,
)

_LOGGER = logging.getLogger(__name__)

# Wie oft (während "Lüften empfohlen" aktiv ist) die Winter-Höchstdauer und
# eine mögliche Erinnerung erneut geprüft werden.
_TICK_INTERVAL = timedelta(minutes=5)

# Anzahl der Einträge im Attribut `push_verlauf` (neueste zuerst).
_PUSH_LOG_SIZE = 8
# Anzahl der Einträge im Attribut `dusche_verlauf` (neueste zuerst).
_SHOWER_LOG_SIZE = 6
# Rückblick/Obergrenze für die Verlaufsabfrage des Fensterkontakts (siehe
# _async_lookup_window_since): neueste Zustände der letzten 30 Tage.
_WINDOW_HISTORY_DAYS = 30
_WINDOW_HISTORY_LIMIT = 500


def _window_since_from_history(
    rows: list[tuple[str, "datetime"]], current: str
) -> "datetime | None":
    """Seit wann steht der Fensterkontakt ununterbrochen im Zustand `current`?

    `rows` sind (Zustand, last_changed)-Paare aus der Verlaufsdatenbank.
    Phasen mit "unavailable"/"unknown" (typisch bei jedem Neustart) werden
    übersprungen: Gesucht ist der erste on/off-Eintrag mit `current` nach
    dem letzten Eintrag mit dem Gegenteil. None, wenn es kein Gegenteil im
    Rückblick gibt oder `current` danach (noch) nicht eingetragen ist
    (die Datenbank schreibt mit einigen Sekunden Verzögerung)."""
    onoff = [(st, ts) for st, ts in sorted(rows, key=lambda r: r[1]) if st in ("on", "off")]
    last_other = None
    for idx, (st, _ts) in enumerate(onoff):
        if st != current:
            last_other = idx
    if last_other is None:
        return None
    for st, ts in onoff[last_other + 1 :]:
        if st == current:
            return ts
    return None

SERVICE_SEND_TEST_PUSH = "send_test_push"


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

    # Entity-Dienst zum Debuggen der Push-Zustellung (siehe
    # SmartVentilationBinarySensor.async_send_test_push). Mehrfaches
    # Registrieren (je Raum-Eintrag) ist bei Entity-Diensten üblich.
    async_get_current_platform().async_register_entity_service(
        SERVICE_SEND_TEST_PUSH, {}, "async_send_test_push"
    )


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
        # Kurzprotokoll der letzten Push-Versuche/-Entscheidungen (neueste
        # zuerst), als Attribut `push_verlauf` sichtbar - nicht über
        # Neustarts hinweg wiederhergestellt (reine Debug-Hilfe).
        self._push_log: deque[str] = deque(maxlen=_PUSH_LOG_SIZE)
        # Kurzprotokoll der letzten Duscherkennungen (Start/Ende, neueste
        # zuerst) als Attribut `dusche_verlauf` - Diagnose-Hilfe für
        # Fehlalarme, nicht über Neustarts hinweg wiederhergestellt.
        self._shower_log: deque[str] = deque(maxlen=_SHOWER_LOG_SIZE)
        self._shower_last_eval: tuple[float, float, float] | None = None
        # Zeitpunkt, seit dem diese Entität ihre Werte verfolgt (Start/Neuladen)
        # - im Protokoll als "nach Start" angegeben.
        self._started_at = dt_util.utcnow()
        self._last_reason: str | None = None
        # Zeitpunkt des letzten ECHTEN Empfehlungswechsels - anders als
        # last_changed der Entität selbst (das Home Assistant bei jedem
        # Neustart auf den Neustart-Zeitpunkt zurücksetzt, siehe README)
        # über RestoreEntity erhalten, da nur beim tatsächlichen Wechsel
        # neu gesetzt (analog zu _open_since).
        self._last_state_change_at = None
        self._unsub_tick = None
        # Zeitpunkt, seit dem der Fensterkontakt im aktuellen Zustand steht
        # (`_window_since_state`): aus der Verlaufsdatenbank gelesen (übersteht
        # Neustarts, bei denen last_changed des Sensors zurückgesetzt wird)
        # bzw. bei einem echten Wechsel im Betrieb direkt übernommen. None,
        # falls unbekannt - die Karte nutzt dann ihren eigenen Rückfall.
        self._window_since: datetime | None = None
        self._window_since_state: str | None = None

        # Ob aktuell eine Push- bzw. persistente Web-Benachrichtigung
        # angezeigt wird, die noch nicht durch eine "clean notification"
        # aufgelöst wurde - siehe _maybe_clear_notifications().
        self._mobile_notification_active = False
        self._persistent_notification_active = False

        # Zuletzt bekannter Wassertank-Status (None = noch nicht initial
        # synchronisiert) sowie eigene "clean notification"-Tracker für die
        # Tank-Benachrichtigung (CONF_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED)
        # - unabhängig von den obigen beiden, da eine eigene notification_id/
        # tag verwendet wird (siehe _tank_notification_id()).
        self._tank_full_state: bool | None = None
        self._tank_mobile_notification_active = False
        self._tank_persistent_notification_active = False

        # Analoges "clean notification"-Muster für die Fenster-Gerät-
        # Konflikt-Benachrichtigung
        # (CONF_DEVICE_WINDOW_CONFLICT_NOTIFICATION_ENABLED, siehe
        # _check_device_window_conflict()) -
        # eigene Tracker-Trios für Luftentfeuchter und Klimaanlage, da beide
        # Konflikte unabhängig voneinander auftreten/enden können. Bewusst
        # NICHT über RestoreEntity wiederhergestellt (wie bereits
        # _mobile_notification_active/_persistent_notification_active) -
        # bleibt die Situation über einen Neustart hinweg bestehen, kann die
        # Benachrichtigung danach einmalig erneut auftauchen, statt dafür
        # eine eigene Wiederherstellungs-Infrastruktur zu brauchen.
        self._dehumidifier_window_conflict_state = False
        self._dehumidifier_window_conflict_mobile_active = False
        self._dehumidifier_window_conflict_persistent_active = False
        self._ac_window_conflict_state = False
        self._ac_window_conflict_mobile_active = False
        self._ac_window_conflict_persistent_active = False

        # Zuletzt kommandierter Soll-Zustand der optionalen Geräte.
        # None = noch nicht initial synchronisiert.
        self._dehumidifier_state: bool | None = None
        self._ac_state: bool | None = None
        # "comfort"/"standby"/"night"/"building_protection" = zuletzt
        # gesetzter Sollwert bzw. Preset, None = noch nicht initial
        # synchronisiert - siehe _update_heating().
        self._heating_state: str | None = None

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

        # Höchstlaufzeit-Begrenzung (CONF_DEVICE_MAX_RUNTIME_MINUTES, siehe
        # _update_single_device()) - seit wann das jeweilige Gerät LIVE
        # ununterbrochen läuft (nicht über Neustarts hinweg wiederhergestellt,
        # analog zu den Leistungs-Trackern oben - nach einem Neustart beginnt
        # die Zählung neu), sowie bis wann eine nach einem Zwangs-Abschalten
        # erzwungene Ruhezeit gilt.
        self._dehumidifier_max_runtime_since = None
        self._dehumidifier_max_runtime_cooldown_until = None
        self._ac_max_runtime_since = None
        self._ac_max_runtime_cooldown_until = None

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
        # True, sobald für die aktuell laufende Dusche schon die Duschdauer-
        # Ansage (CONF_SHOWER_MAX_DURATION) ausgelöst wurde - einmal pro Dusche,
        # wird beim Ende der Dusche zurückgesetzt. Nicht über Neustarts
        # persistiert; stattdessen wird bei einer wiederhergestellten
        # laufenden Dusche vorsorglich True gesetzt (keine Doppelansage).
        self._shower_long_announced = False

        # Dauer des letzten abgeschlossenen Laufs in Minuten (Dashboard-
        # Karte, Spalte "Laufzeit" - zeigt diese, solange das Gerät gerade
        # aus ist, statt nur "–") - beim jeweiligen Aus-Übergang neben
        # `_on_since` gepflegt, siehe extra_state_attributes()/_evaluate().
        self._dehumidifier_last_runtime_minutes = None
        self._ac_last_runtime_minutes = None
        self._heating_last_runtime_minutes = None
        self._shower_last_runtime_minutes = None
        # Startzeitpunkt der zuletzt erkannten Dusche (bleibt nach dem Ende
        # stehen, anders als `_shower_on_since`) - Dashboard-Karte, Zeile
        # "Dusche" der Gerätetabelle.
        self._shower_last_start = None

    def attach_shower_sensor(
        self, shower_sensor: "SmartVentilationShowerBinarySensor"
    ) -> None:
        """Verknüpft den separaten 'Dusche aktiv'-Sensor mit diesem Raum -
        siehe async_setup_entry()."""
        self._shower_sensor = shower_sensor

    @property
    def icon(self) -> str:
        return "mdi:window-open-variant" if self._attr_is_on else "mdi:window-closed-variant"

    @property
    def showering(self) -> bool:
        """Aktueller Duscherkennungs-Zustand - vom separaten 'Dusche aktiv'-
        Sensor gelesen (siehe SmartVentilationShowerBinarySensor)."""
        return self._showering

    @staticmethod
    def _co2_blocked_by_warm_outdoor(
        co2: float,
        co2_open: float,
        outdoor_temp: float | None,
        temp_open: float,
    ) -> bool:
        """CO2 öffnet nicht, solange die Außenluft wärmer ist als die
        Temperatur-Obergrenze (Lüften würde den Raum aufheizen) - außer der
        CO2-Wert liegt deutlich über der Öffnen-Schwelle (Faktor
        CO2_WARM_OUTDOOR_OVERRIDE_FACTOR), dann hat die Luftqualität Vorrang.
        Ohne (verfügbaren) Außentemperaturwert kein Block: die Luftqualität
        soll nicht von einem Sensorausfall abhängen (siehe CLAUDE.md
        Lektion 67)."""
        return (
            outdoor_temp is not None
            and outdoor_temp > temp_open
            and co2 <= co2_open * CO2_WARM_OUTDOOR_OVERRIDE_FACTOR
        )

    def _live_reasons(
        self,
        indoor_temp: float | None,
        humidity: float | None,
        co2: float | None,
        outdoor_temp: float | None,
        outdoor_humidity: float | None,
    ) -> tuple[list[str], str]:
        """Für die Dashboard-Karte: welche der drei Öffnen-Gründe (Temperatur/
        Luftfeuchtigkeit/CO2) aktuell live zutreffen (mehrere gleichzeitig
        möglich, siehe CLAUDE.md Lektion 61) sowie ein einzelner, live
        berechneter Schließen-Grund (hier kann strukturell nur einer
        "gewinnen", siehe Lektion 30/61).

        Bewusst KEINE Wiederverwendung der should_open/should_close-Booleans
        aus _evaluate() - diese sind zusätzlich vom aktuellen Zustand
        (self._attr_is_on), Außenluft-Gates und Hysterese abhängig, hier
        geht es dagegen um einen zustandsunabhängigen "liegt der Messwert
        gerade außerhalb des Normalbereichs"-Vergleich, den die Karte für
        ihren Fenster-Mismatch-Abgleich unabhängig von der eigentlichen
        Empfehlung braucht. Die Außenluft-Gates der Öffnen-Gründe gelten
        dabei wie im Backend (siehe CLAUDE.md Lektion 67), damit die Karte
        keinen Auslöser zeigt, der die Empfehlung gar nicht auslöst."""
        temp_open = self._effective(CONF_TEMP_THRESHOLD_OPEN, DEFAULT_TEMP_THRESHOLD_OPEN)
        temp_close = self._effective(CONF_TEMP_THRESHOLD_CLOSE, DEFAULT_TEMP_THRESHOLD_CLOSE)
        # Live-Pendants zu outdoor_cooler_enough/outdoor_drier_enough
        # (siehe _evaluate()) - verhindern, dass "outdoor_warmer"/
        # "outdoor_wetter" direkt nach dem Öffnen aufblitzen, obwohl die
        # Außenluft nach demselben Live-Maßstab, der dort das Öffnen-Gate
        # bildet, noch vorteilhaft ist (siehe CLAUDE.md Lektion 65 - dieselbe
        # Übergangszonen-Inkonsistenz wie im Backend, hier für die Karte).
        margin = self._effective(CONF_TEMP_MARGIN, DEFAULT_TEMP_MARGIN)
        outdoor_cooler_enough_live = (
            outdoor_temp is not None
            and indoor_temp is not None
            and outdoor_temp <= indoor_temp - margin
        )
        outdoor_drier_enough_live = (
            outdoor_humidity is not None
            and humidity is not None
            and indoor_temp is not None
            and outdoor_temp is not None
            and self._absolute_humidity(outdoor_temp, outdoor_humidity)
            < self._absolute_humidity(indoor_temp, humidity)
        )

        # Öffnen-Gründe nur, wenn auch das Backend sie als Öffnen-Grund
        # wertet (Außenluft-Gates aus _evaluate(): ohne konfigurierten
        # Außensensor permissiv, sonst nur bei bestätigtem Vorteil) - sonst
        # zeigt die Karte einen Auslöser, der die Empfehlung gar nicht
        # auslöst (siehe CLAUDE.md Lektion 67).
        outdoor_temp_configured = bool(self._effective(CONF_OUTDOOR_TEMP_ENTITY, None))
        outdoor_humidity_configured = bool(
            self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        )
        open_reasons: list[str] = []
        if (
            indoor_temp is not None
            and indoor_temp > temp_open
            and (not outdoor_temp_configured or outdoor_cooler_enough_live)
        ):
            open_reasons.append("temp")

        hum_open = hum_close = None
        if self._config.get(CONF_HUMIDITY_ENTITY):
            hum_open = self._effective(
                CONF_HUMIDITY_THRESHOLD_OPEN, DEFAULT_HUMIDITY_THRESHOLD_OPEN
            )
            hum_close = self._effective(
                CONF_HUMIDITY_THRESHOLD_CLOSE, DEFAULT_HUMIDITY_THRESHOLD_CLOSE
            )
            if (
                humidity is not None
                and humidity > hum_open
                and (not outdoor_humidity_configured or outdoor_drier_enough_live)
            ):
                open_reasons.append("humidity")

        co2_close = None
        if self._config.get(CONF_CO2_ENTITY):
            co2_open = self._effective(CONF_CO2_THRESHOLD_OPEN, DEFAULT_CO2_THRESHOLD_OPEN)
            co2_close = self._effective(CONF_CO2_THRESHOLD_CLOSE, DEFAULT_CO2_THRESHOLD_CLOSE)
            if (
                co2 is not None
                and co2 > co2_open
                and not self._co2_blocked_by_warm_outdoor(
                    co2, co2_open, outdoor_temp, temp_open
                )
            ):
                open_reasons.append("co2")

        frost_temp = self._effective(CONF_FROST_PROTECTION_TEMP, DEFAULT_FROST_PROTECTION_TEMP)
        heat_temp = self._effective(CONF_HEAT_PROTECTION_TEMP, DEFAULT_HEAT_PROTECTION_TEMP)
        frost_live = outdoor_temp is not None and outdoor_temp <= frost_temp
        heat_live = outdoor_temp is not None and outdoor_temp >= heat_temp
        no_close_rec = self._config.get(CONF_DISABLE_CLOSE_RECOMMENDATION, False)

        close_reason = ""
        if frost_live:
            close_reason = "frost"
        elif heat_live:
            close_reason = "heat"
        elif not no_close_rec:
            if hum_close is not None and humidity is not None and humidity < hum_close:
                close_reason = "humidity"
            elif co2_close is not None and co2 is not None and co2 < co2_close:
                close_reason = "co2"
            elif indoor_temp is not None and indoor_temp < temp_close:
                close_reason = "temp"
            elif (
                outdoor_temp is not None
                and outdoor_temp > temp_open
                and not outdoor_cooler_enough_live
            ):
                close_reason = "outdoor_warmer"
            elif (
                hum_open is not None
                and outdoor_humidity is not None
                and outdoor_temp is not None
                and indoor_temp is not None
                and self._absolute_humidity(outdoor_temp, outdoor_humidity)
                > self._absolute_humidity(indoor_temp, hum_open)
                and not outdoor_drier_enough_live
            ):
                close_reason = "outdoor_wetter"
            elif self._last_reason == "duration":
                close_reason = "duration"

        return open_reasons, close_reason

    @property
    def extra_state_attributes(self) -> dict:
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY), decimals=0)
        co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY), decimals=0)
        outdoor_temp_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        outdoor_temp = self._get_float_state(outdoor_temp_entity, decimals=1)
        outdoor_humidity = self._get_float_state(
            self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None), decimals=0
        )
        offene_gruende, schliessgrund_live = self._live_reasons(
            indoor_temp, humidity, co2, outdoor_temp, outdoor_humidity
        )

        attrs = {
            "raum": self._config[CONF_ROOM_NAME],
            "innentemperatur": indoor_temp,
            "schwelle_temperatur_oeffnen": self._effective(
                CONF_TEMP_THRESHOLD_OPEN, DEFAULT_TEMP_THRESHOLD_OPEN
            ),
            "schwelle_temperatur_schliessen": self._effective(
                CONF_TEMP_THRESHOLD_CLOSE, DEFAULT_TEMP_THRESHOLD_CLOSE
            ),
            # Für die Dashboard-Karte (siehe README) - ersetzt die bisherige,
            # in der Jinja-Vorlage selbst nachgebaute Live-Neuberechnung
            # dieser Gründe aus diversen Rohwert-/Schwellen-Attributen (siehe
            # CLAUDE.md, "Custom-Card"-Überlegung): temp/humidity/co2 können
            # gleichzeitig als Öffnen-Grund zutreffen (Lektion 61), auf der
            # Schließen-Seite gewinnt strukturell immer nur einer.
            "offene_gruende": offene_gruende,
            "schliessgrund_live": schliessgrund_live,
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
            if self._shower_on_since is not None:
                attrs["dusche_seit"] = self._shower_on_since.isoformat()
            if self._shower_last_start is not None:
                attrs["dusche_letzter_start"] = self._shower_last_start.isoformat()
            if self._shower_last_runtime_minutes is not None:
                attrs["dusche_letzte_laufzeit"] = self._shower_last_runtime_minutes
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
        if humidity is not None and indoor_temp is not None:
            dew = self._dew_point(indoor_temp, humidity)
            if dew is not None:
                attrs["taupunkt"] = round(dew, 1)
        if outdoor_humidity is not None and outdoor_temp is not None:
            dew = self._dew_point(outdoor_temp, outdoor_humidity)
            if dew is not None:
                attrs["aussen_taupunkt"] = round(dew, 1)
        # Entity-IDs der angezeigten Werte/Geräte - die JS-Karte öffnet damit
        # per Klick die Detailansicht (more-info) der jeweiligen Entität.
        linked_entities = {
            "innentemperatur": self._config.get(CONF_TEMP_SOURCE_ENTITY),
            "luftfeuchtigkeit": self._config.get(CONF_HUMIDITY_ENTITY),
            "co2": self._config.get(CONF_CO2_ENTITY),
            "aussentemperatur": outdoor_temp_entity,
            "aussen_luftfeuchtigkeit": self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None),
            "fenster": self._config.get(CONF_WINDOW_ENTITY),
            "luftentfeuchter": self._config.get(CONF_DEHUMIDIFIER_ENTITY),
            "luftentfeuchter_tank": self._config.get(CONF_DEHUMIDIFIER_TANK_FULL_ENTITY),
            "klimaanlage": self._config.get(CONF_AC_ENTITY),
            "heizung": self._get_heating_entity_id(),
            "sommermodus": self._effective(CONF_SUMMER_MODE_SWITCH_ENTITY, None),
            "absolute_luftfeuchtigkeit": self._sensor_entity_id(
                self._entry.entry_id, "absolute_luftfeuchtigkeit"
            ),
            "aussen_absolute_luftfeuchtigkeit": self._sensor_entity_id(
                self.hass.data.get(DOMAIN, {}).get(GLOBAL_ENTRY_ID_KEY),
                "aussen_absolute_luftfeuchtigkeit",
            ),
            "taupunkt": self._sensor_entity_id(self._entry.entry_id, "taupunkt"),
            "aussen_taupunkt": self._sensor_entity_id(
                self.hass.data.get(DOMAIN, {}).get(GLOBAL_ENTRY_ID_KEY),
                "aussen_taupunkt",
            ),
            "dusche": (
                self._shower_sensor.entity_id if self._shower_sensor is not None else None
            ),
        }
        attrs["entitaeten"] = {k: v for k, v in linked_entities.items() if v}

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
        if self._last_state_change_at is not None:
            attrs["letzter_wechsel"] = self._last_state_change_at.isoformat()
        window_entity = self._config.get(CONF_WINDOW_ENTITY)
        if window_entity and self._window_since is not None:
            window_state = self.hass.states.get(window_entity)
            if window_state is not None and window_state.state == self._window_since_state:
                attrs["fenster_seit"] = self._window_since.isoformat()
        if self._last_notified_at is not None:
            attrs["letzte_benachrichtigung"] = self._last_notified_at.isoformat()
        if self._push_log:
            attrs["push_verlauf"] = list(self._push_log)
        if self._shower_log:
            attrs["dusche_verlauf"] = list(self._shower_log)
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
                if self._dehumidifier_on_since is not None:
                    self._dehumidifier_last_runtime_minutes = int(
                        (dt_util.utcnow() - self._dehumidifier_on_since).total_seconds()
                        / 60
                    )
                self._dehumidifier_on_since = None
            attrs["luftentfeuchter_an"] = dehumidifier_on
            if self._dehumidifier_last_runtime_minutes is not None:
                attrs["luftentfeuchter_letzte_laufzeit"] = (
                    self._dehumidifier_last_runtime_minutes
                )
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
                if self._ac_on_since is not None:
                    self._ac_last_runtime_minutes = int(
                        (dt_util.utcnow() - self._ac_on_since).total_seconds() / 60
                    )
                self._ac_on_since = None
            attrs["klimaanlage_an"] = ac_on
            if self._ac_last_runtime_minutes is not None:
                attrs["klimaanlage_letzte_laufzeit"] = self._ac_last_runtime_minutes
            attrs["klimaanlage_grund"] = self._ac_reason
        heating_entity = self._get_heating_entity_id()
        if heating_entity and not self._device_entity_missing(heating_entity):
            # "heizung_modus" ist nicht wie bei Luftentfeuchter/Klimaanlage
            # ein einfaches Ein/Aus, sondern eine von vier Stufen (Comfort/
            # Standby/Nacht/Gebäudeschutz). Bei aktiver Preset-Steuerung
            # (siehe CONF_HEATING_USE_PRESET_MODE) wird dafür direkt der
            # live vom Gerät gemeldete preset_mode zurück auf unsere vier
            # Bezeichner gemappt - genauer als eine Temperatur-Näherung,
            # da z. B. ein vom Nutzer direkt am Thermostat gewählter,
            # unbekannter Preset ehrlich als "kein bekannter Modus" (None)
            # erkannt wird statt geraten zu werden. Ohne (wirksame)
            # Preset-Steuerung bleibt es bei der ursprünglichen Näherung
            # "welchem der drei Sollwerte (Comfort/Standby/Nacht) der
            # aktuell eingestellte Sollwert am nächsten liegt" (Lektion
            # 19/33/40) - Gebäudeschutz kennt dabei keinen eigenen
            # Zahlen-Sollwert, kommt in dieser Näherung also nie vor.
            # "heizung_an" bleibt als einfaches Ein/Aus für die
            # Geräte-Tabelle erhalten (an = Comfort, aus = jede andere
            # Stufe - alle "zurückgefahren").
            if self._heating_preset_mode_effective(heating_entity):
                heating_mode_active = self._get_heating_mode_from_live_preset(heating_entity)
                current_target = self._get_heating_target_temperature(heating_entity)
            else:
                comfort_temp = self._effective(CONF_HEATING_COMFORT_TEMP, DEFAULT_HEATING_COMFORT_TEMP)
                standby_temp = self._effective(CONF_HEATING_STANDBY_TEMP, DEFAULT_HEATING_STANDBY_TEMP)
                night_temp = self._effective(CONF_HEATING_NIGHT_TEMP, DEFAULT_HEATING_NIGHT_TEMP)
                current_target = self._get_heating_target_temperature(heating_entity)
                if current_target is None:
                    heating_mode_active = None
                else:
                    heating_mode_active = min(
                        ("comfort", comfort_temp),
                        ("standby", standby_temp),
                        ("night", night_temp),
                        key=lambda pair: abs(current_target - pair[1]),
                    )[0]
            if heating_mode_active == "comfort":
                if self._heating_on_since is None:
                    self._heating_on_since = dt_util.utcnow()
                attrs["heizung_seit"] = self._heating_on_since.isoformat()
            else:
                if self._heating_on_since is not None:
                    self._heating_last_runtime_minutes = int(
                        (dt_util.utcnow() - self._heating_on_since).total_seconds() / 60
                    )
                self._heating_on_since = None
            attrs["heizung_an"] = heating_mode_active == "comfort"
            if self._heating_last_runtime_minutes is not None:
                attrs["heizung_letzte_laufzeit"] = self._heating_last_runtime_minutes
            attrs["heizung_modus"] = heating_mode_active
            attrs["heizung_zieltemperatur"] = current_target
            attrs["heizung_grund"] = self._heating_reason
        summer_mode_entity = self._effective(CONF_SUMMER_MODE_SWITCH_ENTITY, None)
        if summer_mode_entity and not self._device_entity_missing(summer_mode_entity):
            attrs["sommermodus_an"] = self._is_summer_mode_active()
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
            if "letzter_wechsel" in attrs:
                self._last_state_change_at = dt_util.parse_datetime(
                    attrs["letzter_wechsel"]
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
            if "luftentfeuchter_tank_fehler" in attrs:
                # Verhindert eine erneute Tank-Benachrichtigung direkt nach
                # jedem Neustart, solange der Tank ununterbrochen voll
                # bleibt (siehe _check_tank_full()) - analog zur Wieder-
                # herstellung von _dehumidifier_state/_ac_state direkt
                # darunter.
                self._tank_full_state = bool(attrs["luftentfeuchter_tank_fehler"])
            if "luftentfeuchter_an" in attrs:
                self._dehumidifier_state = bool(attrs["luftentfeuchter_an"])
            if "klimaanlage_an" in attrs:
                self._ac_state = bool(attrs["klimaanlage_an"])
            if "heizung_modus" in attrs and attrs["heizung_modus"] in (
                "comfort",
                "standby",
                "night",
                "building_protection",
            ):
                self._heating_state = attrs["heizung_modus"]
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
                self._shower_long_announced = self._shower_on_since is not None
            if "dusche_letzter_start" in attrs:
                self._shower_last_start = dt_util.parse_datetime(
                    attrs["dusche_letzter_start"]
                )
            elif self._shower_on_since is not None:
                self._shower_last_start = self._shower_on_since
            # Letzte abgeschlossene Laufzeit wiederherstellen (sonst würde
            # die Dashboard-Karte nach jedem Neustart, bevor der nächste
            # Lauf beendet ist, wieder auf "–" zurückfallen).
            if "luftentfeuchter_letzte_laufzeit" in attrs:
                self._dehumidifier_last_runtime_minutes = attrs[
                    "luftentfeuchter_letzte_laufzeit"
                ]
            if "klimaanlage_letzte_laufzeit" in attrs:
                self._ac_last_runtime_minutes = attrs["klimaanlage_letzte_laufzeit"]
            if "heizung_letzte_laufzeit" in attrs:
                self._heating_last_runtime_minutes = attrs["heizung_letzte_laufzeit"]
            if "dusche_letzte_laufzeit" in attrs:
                self._shower_last_runtime_minutes = attrs["dusche_letzte_laufzeit"]

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
        # Climate Optionen" - direkt verfolgen, falls beim Hinzufügen
        # bereits gesetzt (siehe Hinweis in der README zur Reaktivität bei
        # reiner Startreihenfolge-Abhängigkeit).
        outdoor_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        if outdoor_entity:
            tracked.append(outdoor_entity)
        outdoor_humidity_entity = self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        if outdoor_humidity_entity:
            tracked.append(outdoor_humidity_entity)

        # Der Wassertank-Sensor wird - anders als Luftentfeuchter/Klimaanlage/
        # Heizung (siehe Lektion 19/31, bewusst nicht verfolgt, da nur live in
        # extra_state_attributes gelesen) - hier gezielt verfolgt, aber NUR
        # wenn die Tank-Benachrichtigung aktiviert ist: Für diesen neuen Zweck
        # (siehe _check_tank_full()) wird eine zeitnahe Reaktion auf das
        # Vollwerden gebraucht, nicht nur eine gelegentliche Aktualisierung
        # der Dashboard-Anzeige.
        if self._config.get(CONF_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED):
            tank_full_entity = self._config.get(CONF_DEHUMIDIFIER_TANK_FULL_ENTITY)
            if tank_full_entity:
                tracked.append(tank_full_entity)

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
        # Echter Fensterwechsel im Betrieb (auch über "nicht verfügbar"
        # hinweg): last_changed des neuen Zustands ist dann der richtige
        # Zeitpunkt. Direkt nach dem Start (noch nichts bekannt) liest
        # _evaluate() stattdessen die Verlaufsdatenbank.
        new_state = event.data.get("new_state")
        if (
            new_state is not None
            and event.data.get("entity_id") == self._config.get(CONF_WINDOW_ENTITY)
            and new_state.state in ("on", "off")
            and self._window_since_state is not None
            and new_state.state != self._window_since_state
        ):
            self._window_since = new_state.last_changed
            self._window_since_state = new_state.state
        self.hass.async_create_task(self._evaluate())

    async def _async_lookup_window_since(
        self, entity_id: str, current: str
    ) -> datetime | None:
        """Liest aus der Verlaufsdatenbank, seit wann der Fensterkontakt im
        Zustand `current` steht (None, falls nicht ermittelbar - z. B. Recorder
        nicht geladen, Entität ausgeschlossen oder kein Wechsel im Rückblick)."""
        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.history import (
                state_changes_during_period,
            )

            start = dt_util.utcnow() - timedelta(days=_WINDOW_HISTORY_DAYS)
            result = await get_instance(self.hass).async_add_executor_job(
                lambda: state_changes_during_period(
                    self.hass,
                    start,
                    entity_id=entity_id,
                    no_attributes=True,
                    descending=True,
                    limit=_WINDOW_HISTORY_LIMIT,
                    include_start_time_state=False,
                )
            )
            rows = [(st.state, st.last_changed) for st in result.get(entity_id, [])]
        except Exception:  # noqa: BLE001 - Verlauf ist nur eine Komfort-Anzeige
            _LOGGER.debug("Fensterverlauf für %s nicht lesbar", entity_id, exc_info=True)
            return None
        return _window_since_from_history(rows, current)

    async def _async_update_window_since(self) -> None:
        """Ermittelt einmal je Fensterzustand den Zeitpunkt aus dem Verlauf
        (beim Start); spätere Wechsel übernimmt _handle_state_change."""
        window_entity = self._config.get(CONF_WINDOW_ENTITY)
        if not window_entity:
            return
        state = self.hass.states.get(window_entity)
        if state is None or state.state not in ("on", "off"):
            return
        if self._window_since_state == state.state:
            return
        self._window_since_state = state.state
        self._window_since = None
        # Im Hintergrund, damit eine langsame Datenbank (z. B. direkt nach dem
        # Start) die erste Neubewertung nicht aufhält.
        self._entry.async_create_background_task(
            self.hass,
            self._async_resolve_window_since(window_entity, state.state),
            f"{DOMAIN}_window_since_{self._entry.entry_id}",
        )

    async def _async_resolve_window_since(self, entity_id: str, current: str) -> None:
        since = await self._async_lookup_window_since(entity_id, current)
        # Zwischenzeitlich echter Wechsel (siehe _handle_state_change)? Dann
        # ist der Wert veraltet und wird verworfen.
        if since is None or self._window_since_state != current:
            return
        self._window_since = since
        if self.hass is not None and self.entity_id:
            self.async_write_ha_state()

    def _stop_tick_timer(self) -> None:
        if self._unsub_tick is not None:
            self._unsub_tick()
            self._unsub_tick = None

    @callback
    def _handle_tick(self, now) -> None:
        self.hass.async_create_task(self._evaluate())

    def _sensor_entity_id(self, entry_id: str | None, suffix: str) -> str | None:
        """Entity-ID eines von dieser Integration angelegten Sensors (über die
        Entity-Registry, feste unique_id-Konvention) - None, falls es ihn nicht
        (mehr) gibt."""
        if not entry_id:
            return None
        return er.async_get(self.hass).async_get_entity_id(
            "sensor", DOMAIN, f"{entry_id}_{suffix}"
        )

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

    @staticmethod
    def _dew_point(temp_c: float, rh_percent: float) -> float | None:
        """Taupunkt (°C) aus Temperatur (°C) und relativer Luftfeuchtigkeit (%)
        über die Magnus-Formel (dieselben Konstanten wie _absolute_humidity).
        None bei 0 % Luftfeuchtigkeit (Taupunkt nicht definiert)."""
        if rh_percent <= 0:
            return None
        gamma = math.log(rh_percent / 100) + (17.62 * temp_c) / (243.12 + temp_c)
        return 243.12 * gamma / (17.62 - gamma)

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
        if elapsed_minutes < SHOWER_MIN_HISTORY_MINUTES:
            # Noch nicht genug Historie, um einen Anstieg zu beurteilen
            # (z. B. direkt nach einem Start/Neuladen) - permissiv wie bei
            # "nicht konfiguriert" (siehe CLAUDE.md).
            return False

        rise_rate = (humidity - oldest_value) / elapsed_minutes
        self._shower_last_eval = (rise_rate, elapsed_minutes, oldest_value)
        if humidity - oldest_value < SHOWER_MIN_RISE_POINTS:
            # Zu kleiner Gesamtanstieg - normales Sensorrauschen/Schwankung,
            # auch wenn die Rate über kurze Zeit rechnerisch hoch wirkt.
            return False
        threshold = self._effective(
            CONF_SHOWER_RISE_THRESHOLD, DEFAULT_SHOWER_RISE_THRESHOLD
        )
        return rise_rate >= threshold

    def _shower_log_add(self, text: str) -> None:
        stamp = dt_util.as_local(dt_util.utcnow()).strftime("%d.%m. %H:%M:%S")
        self._shower_log.appendleft(f"{stamp} {text}")
        _LOGGER.debug("Duscherkennung (%s): %s", self._config[CONF_ROOM_NAME], text)

    def _log_shower_start(self, humidity: float | None) -> None:
        """Protokolliert, WARUM die Duscherkennung gerade anschlägt (Rate,
        Beobachtungsdauer, Verlauf, Fensterzustand, Zeit seit Start) - für
        die Diagnose von Fehlalarmen (Attribut `dusche_verlauf`)."""
        parts = [f"Start: Feuchte {humidity} %"]
        if self._shower_last_eval is not None:
            rate, elapsed, oldest = self._shower_last_eval
            parts.append(
                f"Anstieg {rate:.1f} %/min über {elapsed:.1f} min (von {oldest} %)"
            )
        window_entity = self._config.get(CONF_WINDOW_ENTITY)
        window_state = self.hass.states.get(window_entity) if window_entity else None
        parts.append(f"Fenster {window_state.state if window_state else '–'}")
        since_start = (dt_util.utcnow() - self._started_at).total_seconds() / 60
        parts.append(f"{since_start:.1f} min nach Start")
        samples = ", ".join(
            f"{dt_util.as_local(t).strftime('%H:%M:%S')}={v}"
            for t, v in list(self._humidity_samples)[-8:]
        )
        parts.append(f"Verlauf: {samples}")
        self._shower_log_add("; ".join(parts))

    def _log_shower_end(self, humidity: float | None) -> None:
        minutes = (
            (dt_util.utcnow() - self._shower_on_since).total_seconds() / 60
            if self._shower_on_since is not None
            else 0
        )
        self._shower_log_add(f"Ende nach {minutes:.1f} min: Feuchte {humidity} %")

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

    @staticmethod
    def _time_in_window(current, start_str: str, end_str: str) -> bool:
        """Prüft, ob "current" (datetime.time) innerhalb des Zeitfensters
        [start, end) liegt - inklusive Mitternachts-Wraparound (start >
        end, z. B. 22:00:00-06:00:00, wie beim typischen Nacht-Fenster).
        Ungültige/leere Zeitstrings werden permissiv als "trifft nicht zu"
        behandelt (kein Absturz bei fehlerhafter Konfiguration)."""
        start = dt_util.parse_time(start_str) if start_str else None
        end = dt_util.parse_time(end_str) if end_str else None
        if start is None or end is None:
            return False
        if start <= end:
            return start <= current < end
        return current >= start or current < end

    def _is_tts_quiet_hours_active(self) -> bool:
        """True, wenn die Sprachausgabe-Nachtruhe (CONF_TTS_QUIET_HOURS_
        ENABLED) für diesen Raum aktiv ist UND die aktuelle Uhrzeit im
        konfigurierten Zeitfenster liegt. Betrifft ausschließlich die
        Sprachausgabe (siehe _notify()/_notify_tank_full()) - App-Push und
        persistente Benachrichtigung laufen unverändert weiter (Lektion 16:
        "silent" für einen Kanal bedeutet nicht automatisch "silent" für
        alle)."""
        if not self._effective(
            CONF_TTS_QUIET_HOURS_ENABLED, DEFAULT_TTS_QUIET_HOURS_ENABLED
        ):
            return False
        start = self._effective(CONF_TTS_QUIET_START, DEFAULT_TTS_QUIET_START)
        end = self._effective(CONF_TTS_QUIET_END, DEFAULT_TTS_QUIET_END)
        return self._time_in_window(dt_util.now().time(), start, end)

    def _is_tts_light_off(self) -> bool:
        """True, wenn für diesen Raum eine Licht-Entität
        (CONF_TTS_LIGHT_ENTITY) konfiguriert ist UND diese aktuell
        bestätigt "aus" meldet -
        unterdrückt in diesem Fall die Sprachausgabe (siehe _notify()/
        _notify_tank_full()). Betrifft ausschließlich die Sprachausgabe,
        analog zu _is_tts_quiet_hours_active() (Lektion 16).

        Bewusst PERMISSIV bei unbekanntem/nicht verfügbarem Lichtzustand
        (liefert dann False, die Ansage bleibt aktiv) - anders als z. B.
        beim Frostschutz ist Unsicherheit hier nicht sicherheitsrelevant,
        sondern reiner Komfort, eine konservative Behandlung wäre also
        unnötig. Ohne konfigurierte Entität immer False (unverändertes
        Verhalten wie bisher)."""
        light_entity = self._config.get(CONF_TTS_LIGHT_ENTITY)
        if not light_entity:
            return False
        state = self.hass.states.get(light_entity)
        return state is not None and state.state == "off"

    def _get_scheduled_heating_mode(self) -> str:
        """Bestimmt den vom Heizungs-Zeitplan (CONF_HEATING_SCHEDULE_ENABLED)
        für den aktuellen Zeitpunkt erzwungenen Modus - "comfort", "night"
        oder "standby" (außerhalb beider Fenster). Nur relevant, wenn der
        Zeitplan aktiv ist (siehe _evaluate()) - dort ersetzt das Ergebnis
        dann die reine Schwellenwert-Logik aus Lektion 40 vollständig, das
        Zeitfenster erzwingt den Sollwert unabhängig von der Innentemperatur
        (Nutzerentscheidung, siehe CLAUDE.md Lektion 44).

        Werktag/Wochenende getrennt (dt_util.now().weekday() >= 5 = Samstag/
        Sonntag), da sich z. B. der Aufstehzeitpunkt am Wochenende typisch
        verschiebt. Bei sich überlappender (fehlerhafter) Konfiguration hat
        das Nacht- vor dem Comfort-Fenster Vorrang - im Regelfall ergänzen
        sich beide Fenster pro Wochentyp ohnehin lückenlos zu 24 Stunden
        (siehe die DEFAULT_HEATING_*-Zeitwerte in const.py)."""
        now = dt_util.now()
        current_time = now.time()
        is_weekend = now.weekday() >= 5

        if is_weekend:
            night_start = self._effective(
                CONF_HEATING_NIGHT_START_WEEKEND, DEFAULT_HEATING_NIGHT_START_WEEKEND
            )
            night_end = self._effective(
                CONF_HEATING_NIGHT_END_WEEKEND, DEFAULT_HEATING_NIGHT_END_WEEKEND
            )
            comfort_start = self._effective(
                CONF_HEATING_COMFORT_START_WEEKEND, DEFAULT_HEATING_COMFORT_START_WEEKEND
            )
            comfort_end = self._effective(
                CONF_HEATING_COMFORT_END_WEEKEND, DEFAULT_HEATING_COMFORT_END_WEEKEND
            )
        else:
            night_start = self._effective(
                CONF_HEATING_NIGHT_START_WEEKDAY, DEFAULT_HEATING_NIGHT_START_WEEKDAY
            )
            night_end = self._effective(
                CONF_HEATING_NIGHT_END_WEEKDAY, DEFAULT_HEATING_NIGHT_END_WEEKDAY
            )
            comfort_start = self._effective(
                CONF_HEATING_COMFORT_START_WEEKDAY, DEFAULT_HEATING_COMFORT_START_WEEKDAY
            )
            comfort_end = self._effective(
                CONF_HEATING_COMFORT_END_WEEKDAY, DEFAULT_HEATING_COMFORT_END_WEEKDAY
            )

        if self._time_in_window(current_time, night_start, night_end):
            return "night"
        if self._time_in_window(current_time, comfort_start, comfort_end):
            return "comfort"
        return "standby"

    def _is_summer_mode_active(self) -> bool:
        """Liefert den aktuellen Live-Zustand des unter
        CONF_SUMMER_MODE_SWITCH_ENTITY ausgewählten, bereits vorhandenen
        Schalters (CLAUDE.md Lektion 46/47 - KEINE von dieser Integration
        selbst erzeugte Entität, siehe _update_summer_mode()). Permissiv
        False (Winterbetrieb, Heizung läuft normal), falls keine Entität
        konfiguriert ist, sie fehlt, oder ihr Zustand gerade unbekannt/
        nicht verfügbar ist."""
        entity_id = self._effective(CONF_SUMMER_MODE_SWITCH_ENTITY, None)
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        if state is None or state.state not in ("on", "off"):
            return False
        return state.state == "on"

    def _get_summer_mode_forecast_temperature(self) -> float | None:
        """Liest den aktuellen Vorhersagewert aus der global konfigurierten
        Vorhersage-Entität (CONF_SUMMER_MODE_FORECAST_ENTITY) - entweder
        direkt aus deren state (kein Attribut konfiguriert) oder aus dem
        über CONF_SUMMER_MODE_FORECAST_ATTRIBUTE benannten Attribut, analog
        zum bestehenden Muster für CONF_TEMP_SOURCE_ENTITY/
        CONF_TEMP_ATTRIBUTE. None, falls keine Vorhersage-Entität
        konfiguriert ist, sie fehlt/nicht verfügbar ist, oder sich der Wert
        nicht in eine Zahl umwandeln lässt - _update_summer_mode() lässt
        den ausgewählten Schalter in diesem Fall bewusst unverändert (weder
        Sicherheits- noch Komfort-relevant, ein falsches Timing ist hier
        unkritisch)."""
        entity_id = self._effective(CONF_SUMMER_MODE_FORECAST_ENTITY, None)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        attribute = self._effective(CONF_SUMMER_MODE_FORECAST_ATTRIBUTE, None)
        raw_value = state.attributes.get(attribute) if attribute else state.state
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return None

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

    def _get_device_live_state(self, entity_id: str) -> bool | None:
        """Wie _is_device_on(), aber für die Idempotenz-Prüfung in
        _update_single_device() gedacht statt für die Dashboard-Anzeige:
        liefert None bei unavailable/unknown, statt beides wie
        _is_device_on() zu False zusammenzufassen - "wissen wir nicht"
        muss hier von "ist aus" unterscheidbar bleiben, sonst würde bei
        jeder kurzen Nichtverfügbarkeit unnötig ein Befehl gegen eine
        gerade nicht antwortende Entität wiederholt (siehe CLAUDE.md
        Lektion 56, analog zu _get_heating_target_temperature())."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
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

    def _heating_supports_preset_mode(self, entity_id: str) -> bool:
        """True, wenn die Heizungs-Entität preset_mode überhaupt
        unterstützt (ClimateEntityFeature.PRESET_MODE) - Grundlage für die
        Opt-out-Absicherung von CONF_HEATING_USE_PRESET_MODE (Standard
        Ja): Entitäten ohne diese Unterstützung bleiben automatisch bei
        der reinen Sollwert-Steuerung, ganz ohne dass der Nutzer etwas
        einstellen müsste."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        supported_features = state.attributes.get("supported_features", 0)
        return bool(supported_features & ClimateEntityFeature.PRESET_MODE)

    def _heating_preset_mode_effective(self, entity_id: str) -> bool:
        """True, wenn für diesen Raum tatsächlich über preset_mode statt
        über einen Zahlen-Sollwert gesteuert/angezeigt werden soll - nur,
        wenn CONF_HEATING_USE_PRESET_MODE (Standard Ja) nicht explizit auf
        "Nein" gesetzt UND die Entität preset_mode tatsächlich
        unterstützt."""
        if not self._effective(CONF_HEATING_USE_PRESET_MODE, DEFAULT_HEATING_USE_PRESET_MODE):
            return False
        return self._heating_supports_preset_mode(entity_id)

    def _get_heating_preset_name(self, mode: str) -> str:
        """Liefert den für `mode` ("comfort"/"standby"/"night"/
        "building_protection") konfigurierten preset_mode-Namen der
        Heizungs-Entität - leer, falls für diesen Modus (noch) kein
        Preset-Name hinterlegt ist (siehe CONF_HEATING_PRESET_*-Konstanten
        in const.py); _update_heating() fällt in diesem Fall für genau
        diesen Modus auf die Sollwert-Steuerung zurück."""
        key = {
            "comfort": CONF_HEATING_PRESET_COMFORT,
            "standby": CONF_HEATING_PRESET_STANDBY,
            "night": CONF_HEATING_PRESET_NIGHT,
            "building_protection": CONF_HEATING_PRESET_BUILDING_PROTECTION,
        }[mode]
        return self._effective(key, "") or ""

    def _get_heating_live_preset_mode(self, entity_id: str) -> str | None:
        """Liest den aktuell am Heizungs-Gerät eingestellten preset_mode
        live aus - dient der Idempotenz-Prüfung in _update_heating(),
        analog zu _get_heating_target_temperature() für die reine
        Sollwert-Steuerung."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        return state.attributes.get("preset_mode")

    def _get_heating_mode_from_live_preset(self, entity_id: str) -> str | None:
        """Ordnet den live vom Gerät gemeldeten preset_mode einem unserer
        vier Bezeichner zu (Umkehrung von _get_heating_preset_name()) -
        liefert None, wenn das Gerät gerade einen anderen, uns nicht
        bekannten Preset meldet (z. B. vom Nutzer direkt am Thermostat
        gewählt) oder preset_mode (noch) nicht lesbar ist - bewusst kein
        Rateversuch wie bei der Temperatur-Näherung."""
        current_preset = self._get_heating_live_preset_mode(entity_id)
        if not current_preset:
            return None
        for mode in ("comfort", "standby", "night", "building_protection"):
            if self._get_heating_preset_name(mode) == current_preset:
                return mode
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

    def _get_float_state(
        self, entity_id: str | None, decimals: int | None = None
    ) -> float | None:
        """Liest einen Sensorwert als float. `decimals` rundet direkt beim
        Einlesen (z. B. auf die auch angezeigte/verglichene Genauigkeit) -
        damit Entscheidungslogik, Dashboard-Anzeige und Benachrichtigungs-
        text nie mit unterschiedlich präzisen Werten desselben Sensors
        arbeiten (sonst könnte die Karte z. B. "55 %" zeigen, während intern
        noch mit 55.4 % verglichen wird)."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            value = float(state.state)
        except ValueError:
            return None
        return round(value, decimals) if decimals is not None else value

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
            # Auf 1 Nachkommastelle gerundet - dieselbe Genauigkeit, mit der
            # die Innentemperatur überall angezeigt/verglichen wird (siehe
            # _get_float_state()).
            return round(float(value), 1)
        except (TypeError, ValueError):
            return None

    async def _evaluate(self) -> None:  # noqa: C901 - bewusst als ein Ablauf gehalten
        """Prüft alle Bedingungen und aktualisiert ggf. den Zustand."""
        await self._async_update_window_since()
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY), decimals=0)
        co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY), decimals=0)
        outdoor_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        outdoor_temp = self._get_float_state(outdoor_entity, decimals=1)
        outdoor_humidity_entity = self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        outdoor_humidity = self._get_float_state(outdoor_humidity_entity, decimals=0)

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
        # Bewusst strikt (>/<), nicht inklusiv (>=/<=): Der Schwellenwert
        # selbst gilt noch als Teil des Normalbereichs ("öffnet ab hier"/
        # "schließt ab hier" meint "sobald überschritten", nicht "bei
        # exaktem Erreichen"), siehe CLAUDE.md Lektion 61.
        humidity_needs_open = humidity is not None and humidity > hum_open
        humidity_needs_close = humidity is not None and humidity < hum_close
        co2_needs_open = co2 is not None and co2 > co2_open
        co2_needs_close = co2 is not None and co2 < co2_close
        temp_needs_open = indoor_temp is not None and indoor_temp > temp_open
        temp_needs_close = indoor_temp is not None and indoor_temp < temp_close

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
        # --- Heizung: drei feste Sollwerte (Comfort/Standby/Nacht) statt
        # einfachem Ein/Aus, wie für Heizungen üblich - siehe
        # CONF_HEATING_COMFORT_TEMP/CONF_HEATING_STANDBY_TEMP/
        # CONF_HEATING_NIGHT_TEMP in const.py. Pausiert (Standby) mit
        # höchster Priorität, solange das Fenster bestätigt offen ist
        # (_is_window_confirmed_open(), dasselbe Muster wie bei der
        # Luftentfeuchter-Pausierung - gegen ein offenes Fenster zu heizen
        # verschwendet nur Energie) - unabhängig davon, ob der Zeitplan
        # aktiv ist oder nicht, da das ein Pausier-, kein Komfort-Grund ist.
        #
        # Anwesenheit (_is_heating_presence_away(), nur relevant, wenn
        # mindestens eine Anwesenheits-Entität konfiguriert ist) ist KEIN
        # gleichrangiger Pausier-Grund wie Fenster/Sommerbetrieb, sondern
        # verhindert ausdrücklich NUR den Wechsel in den Comfort-Modus - der
        # ansonsten "natürliche" Zielmodus (Zeitplan-Fenster ODER
        # Schwellenwert-Logik) wird dafür zunächst ganz normal berechnet und
        # erst danach auf Standby herabgestuft, falls er "comfort" ergeben
        # hätte. Standby, Gebäudeschutz und Eco/Nacht laufen bei Abwesenheit
        # dadurch unverändert normal weiter (Nutzerentscheidung) - anders als
        # Fenster/Sommerbetrieb, die den Modus unabhängig vom eigentlich
        # gewollten Ziel erzwingen.
        #
        # Ist der Zeitplan aktiv (CONF_HEATING_SCHEDULE_ENABLED,
        # 0.60.0/Lektion 44), erzwingt das jeweilige Zeitfenster den Modus
        # unabhängig von der Innentemperatur (_get_scheduled_heating_mode(),
        # Nutzerentscheidung - siehe dort). Sonst gilt weiterhin exakt die
        # ursprüngliche Lektion-40-Schwellenwert-Logik: Comfort unterhalb
        # der Schwelle, Standby erst ab Schwelle + Toleranz-Marge (Hysterese,
        # dieselbe margin wie bei den anderen Temperaturvergleichen) -
        # dazwischen sowie bei fehlendem indoor_temp bleibt der zuletzt
        # gesetzte Sollwert unverändert (heating_target_mode = None) - anders
        # als beim Frostschutz ist ein falsches Timing hier nicht
        # sicherheitsrelevant, nur unkomfortabel, ein Umschalten ohne
        # verlässlichen Messwert also nicht gerechtfertigt.
        #
        # --- Sommer-/Winterbetrieb (0.61.0/Lektion 46/47): EIN bereits
        # vorhandener, unter CONF_SUMMER_MODE_SWITCH_ENTITY ausgewählter
        # Schalter (KEINE eigene Entität dieser Integration) pausiert bei
        # Aktivierung die Heizung ALLER Räume gleichzeitig. Automatisch
        # anhand einer Vorhersage-Temperatur geschaltet (Hysterese über
        # dieselbe Toleranz-Marge wie bei den anderen Temperaturvergleichen)
        # - bewusst mit den GLOBALEN Werten für Schwelle/Marge, nicht
        # self._effective() (das würde bei einem Raum-Override eine je nach
        # Raum unterschiedliche Entscheidung für ein und dieselbe gemeinsame
        # Entität liefern können). want_summer_mode wird NICHT einfach aus
        # dem Vergleich berechnet, sondern fällt in der Totzone (und ohne
        # verfügbare Vorhersage) auf den aktuellen Live-Zustand des
        # Schalters zurück: das lässt sowohl einen manuellen Schaltvorgang
        # als auch den zuletzt automatisch gesetzten Zustand unangetastet,
        # bis die Vorhersage eine der beiden Grenzen eindeutig über-/
        # unterschreitet. Ohne konfigurierten Schalter bleibt es bei False
        # (kein Einfluss).
        summer_mode_forecast = self._get_summer_mode_forecast_temperature()
        summer_mode_current = self._is_summer_mode_active()
        global_config = self._global_config()
        summer_mode_threshold = global_config.get(
            CONF_SUMMER_MODE_THRESHOLD_TEMP, DEFAULT_SUMMER_MODE_THRESHOLD_TEMP
        )
        summer_mode_margin = global_config.get(CONF_TEMP_MARGIN, DEFAULT_TEMP_MARGIN)
        if summer_mode_forecast is not None and summer_mode_forecast >= (
            summer_mode_threshold + summer_mode_margin
        ):
            want_summer_mode = True
        elif summer_mode_forecast is not None and summer_mode_forecast < (
            summer_mode_threshold - summer_mode_margin
        ):
            want_summer_mode = False
        else:
            want_summer_mode = summer_mode_current
        # Nutzt bewusst die frisch entschiedene want_summer_mode direkt als
        # Pausier-Grund, nicht den (u. U. noch veralteten) summer_mode_current
        # von vor dem Schreiben in _update_summer_mode() - eine Grenz-
        # überschreitung wirkt sich so noch in DIESEM Bewertungslauf auf die
        # Heizung aus, ohne einen Zyklus Verzögerung.
        heating_summer_mode_active = want_summer_mode

        window_confirmed_open = self._is_window_confirmed_open()
        heating_presence_away = self._is_heating_presence_away()
        heating_schedule_enabled = self._effective(CONF_HEATING_SCHEDULE_ENABLED, False)
        # "Gebäudeschutz" (Preset, kein eigener Zahlen-Sollwert) ersetzt
        # Standby bewusst NUR beim Pausier-Grund "Fenster offen" - bei
        # aktivem Sommerbetrieb bleibt es bei Standby (Nutzerentscheidung).
        if window_confirmed_open:
            heating_target_mode = "building_protection"
        elif heating_summer_mode_active:
            heating_target_mode = "standby"
        elif heating_schedule_enabled:
            heating_target_mode = self._get_scheduled_heating_mode()
        elif indoor_temp is not None and indoor_temp < heating_threshold:
            heating_target_mode = "comfort"
        elif indoor_temp is not None and indoor_temp >= heating_threshold + margin:
            heating_target_mode = "standby"
        else:
            heating_target_mode = None

        # Anwesenheit greift erst HIER, nachdem der eigentlich gewollte
        # Zielmodus feststeht (Zeitplan/Schwelle/Sommerbetrieb/Fenster) -
        # sie verhindert ausdrücklich nur den Wechsel in Comfort, alle
        # anderen bereits ermittelten Modi (Standby/Nacht/Gebäudeschutz)
        # bleiben unverändert. Siehe Kommentar oben.
        heating_presence_blocked_comfort = (
            heating_presence_away and heating_target_mode == "comfort"
        )
        if heating_presence_blocked_comfort:
            heating_target_mode = "standby"

        # --- Rein informative Ein-/Ausschalt-Gründe für Luftentfeuchter/
        # Klimaanlage (Dashboard-Karte, neue Geräte-Tabelle, siehe README) -
        # spiegeln dieselbe Priorität wie want_on/want_off in
        # _update_devices() wider, haben selbst aber keine Steuerungswirkung.
        # Live bei jeder Neubewertung neu gesetzt (wie self._showering),
        # nicht nur bei einem tatsächlichen Zustandswechsel.
        if self._config.get(CONF_DEHUMIDIFIER_ENTITY):
            if not self._config.get(CONF_HUMIDITY_ENTITY):
                self._dehumidifier_reason = "kein Feuchtigkeitssensor konfiguriert"
            elif (
                self._dehumidifier_max_runtime_cooldown_until is not None
                and dt_util.utcnow() < self._dehumidifier_max_runtime_cooldown_until
            ):
                self._dehumidifier_reason = (
                    "Ruhezeit nach Höchstlaufzeit, bis "
                    + dt_util.as_local(
                        self._dehumidifier_max_runtime_cooldown_until
                    ).strftime("%H:%M")
                )
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
            if (
                self._ac_max_runtime_cooldown_until is not None
                and dt_util.utcnow() < self._ac_max_runtime_cooldown_until
            ):
                self._ac_reason = (
                    "Ruhezeit nach Höchstlaufzeit, bis "
                    + dt_util.as_local(self._ac_max_runtime_cooldown_until).strftime(
                        "%H:%M"
                    )
                )
            elif temp_needs_close:
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
            elif heating_presence_blocked_comfort:
                self._heating_reason = "pausiert: niemand zuhause (kein Comfort)"
            elif heating_summer_mode_active:
                self._heating_reason = "pausiert: Sommerbetrieb aktiv"
            elif heating_schedule_enabled:
                self._heating_reason = {
                    "comfort": "Zeitfenster: Comfort",
                    "night": "Zeitfenster: Nacht",
                    "standby": "Zeitfenster: Standby",
                }[heating_target_mode]
            elif heating_target_mode == "comfort":
                self._heating_reason = "Innentemperatur unter Schwelle, Comfort"
            elif heating_target_mode == "standby":
                self._heating_reason = "Innentemperatur über Schwelle, Standby"
            else:
                self._heating_reason = "im Sollbereich, hält letzten Zustand"
        # --- Schließen: Außenluft ist inzwischen (wieder) absolut feuchter
        # als der Normalbereich (Feuchtigkeits-Öffnen-Schwelle, umgerechnet
        # in absolute Luftfeuchtigkeit über die aktuelle Innentemperatur) -
        # das Pendant zu outdoor_warmer_again weiter unten, nur für
        # Luftfeuchtigkeit statt Temperatur. Vergleicht bewusst NICHT mehr
        # gegen den aktuellen Live-Innenwert (siehe Git-Historie vor diesem
        # "Normalbereich"-Umbau), sondern gegen dieselbe Schwelle, die auch
        # das Öffnen auslöst - identisches Prinzip wie bei der Temperatur:
        # Erst wenn die Außenluft selbst außerhalb des Normalbereichs liegt,
        # macht Lüften die Lage schlechter statt besser. outdoor_drier_enough
        # oben gilt nur einmalig als Öffnen-Gate; einmal geöffnet, wird dieser
        # Vergleich sonst nicht mehr erneut geprüft - eine bereits aktive
        # "bitte öffnen"-Empfehlung wegen Luftfeuchtigkeit bliebe sonst auch
        # dann bestehen, wenn Lüften die Luftfeuchtigkeit längst nur noch
        # verschlimmern würde. Bewusst NUR bei vollständig vorliegenden
        # Werten ausgelöst (nicht schon bei fehlendem Sensor/Messwert - anders
        # als beim konservativen Öffnen-Gate oben ist "wir wissen es nicht"
        # hier kein Sicherheits-, sondern ein reiner Komfort-Fall, der ohne
        # positive Bestätigung nicht vorsorglich schließen soll). `humidity`
        # bleibt bewusst als reines Scope-Gate erhalten (Mechanismus nur für
        # Räume mit konfiguriertem Innen-Feuchtigkeitssensor), fließt aber
        # nicht mehr selbst in den Vergleich ein.
        outdoor_humidity_confirmed_worse = (
            outdoor_humidity_entity is not None
            and outdoor_humidity is not None
            and humidity is not None
            and indoor_temp is not None
            and outdoor_temp is not None
            and self._absolute_humidity(outdoor_temp, outdoor_humidity)
            > self._absolute_humidity(indoor_temp, hum_open)
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
                self._shower_last_start = self._shower_on_since
                self._log_shower_start(humidity)
        else:
            if self._shower_on_since is not None:
                self._shower_last_runtime_minutes = int(
                    (dt_util.utcnow() - self._shower_on_since).total_seconds() / 60
                )
                self._log_shower_end(humidity)
            self._shower_on_since = None
            self._shower_long_announced = False
        await self._check_shower_too_long()
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
        # Außenluft-Vergleich der Luftqualität selbst: Außenluft liegt
        # praktisch immer bei ~420 ppm, also weit unter jeder sinnvollen
        # Innenschwelle. Lüften kann aber den Raum aufheizen: liegt die
        # Außentemperatur über der Temperatur-Obergrenze, öffnet CO2 nur bei
        # deutlich erhöhtem Wert (siehe _co2_blocked_by_warm_outdoor).
        open_by_co2 = co2_needs_open and not self._co2_blocked_by_warm_outdoor(
            co2, co2_open, outdoor_temp, temp_open
        )

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
                heating_target_mode=heating_target_mode,
                want_summer_mode=want_summer_mode,
            )
            return

        should_open = (
            open_by_temp or open_by_humidity or open_by_co2
        ) and not frost_block and not heat_block

        # --- Schließen: Sommer-Fall (draußen wieder spürbar wärmer) ---
        # Vergleicht bewusst NICHT mehr gegen die aktuelle Live-Innentemperatur
        # + Toleranz-Marge (siehe Git-Historie), sondern gegen die Öffnen-
        # Schwelle des Raums selbst ("Normalbereich"-Obergrenze) - erst wenn
        # die Außenluft selbst außerhalb dieses Normalbereichs liegt, macht
        # Lüften die Lage schlechter statt besser. Vermeidet damit den Fall,
        # dass eine noch gar nicht kritische, aber knapp unter der Öffnen-
        # Schwelle liegende Innentemperatur bereits eine Schließempfehlung
        # auslöst, sobald die Außentemperatur diese knapp übersteigt.
        outdoor_warmer_again = outdoor_temp is not None and outdoor_temp > temp_open
        # Blockiert bewusst NUR, wenn Luftfeuchtigkeit/CO2 AKTUELL selbst
        # noch eine Öffnen-Bedingung erfüllen (open_by_humidity/open_by_co2),
        # nicht schon, wenn sie nur noch nicht bis zur eigenen Schließen-
        # Schwelle gefallen sind (die breitere *_still_needed-Hysterese, die
        # für die drei PRIMÄREN Schließgründe unten weiterhin richtig ist,
        # um deren eigenes Geflacker zu verhindern) - sonst blockiert z. B.
        # eine noch nicht ganz abgeklungene Luftfeuchtigkeit diesen
        # Außenluft-Mechanismus, obwohl sie gar nicht der Grund fürs
        # aktuelle Offenbleiben war (siehe CLAUDE.md Lektion 30/61).
        # Zusätzlich `not outdoor_cooler_enough`: Verhindert ein Geflacker
        # direkt nach dem Öffnen - `outdoor_cooler_enough` (Öffnen-Gate)
        # vergleicht gegen den aktuellen LIVE-Innenwert, `outdoor_warmer_again`
        # dagegen bewusst gegen die feste Öffnen-Schwelle (siehe deren
        # Kommentar). Direkt beim Öffnen liegen beide Referenzwerte dicht
        # beieinander - fällt die Außentemperatur in die schmale Lücke
        # dazwischen, würde ohne diese Zusatzbedingung sofort wieder
        # geschlossen, obwohl das Öffnen-Gate die Außenluft gerade erst als
        # (knapp) kühler genug bewertet hat. Kann eine bestehende Dauerschleife
        # (öffnen → sofort schließen → sofort wieder öffnen → ...) auslösen,
        # solange die Außentemperatur in dieser Lücke verharrt.
        close_by_summer_outdoor = (
            self._attr_is_on
            and outdoor_warmer_again
            and not open_by_humidity
            and not open_by_co2
            and not outdoor_cooler_enough
        )

        # --- Schließen: Pendant zu close_by_summer_outdoor, nur für
        # Luftfeuchtigkeit statt Temperatur (siehe outdoor_humidity_confirmed_worse
        # oben) - schließt nicht, solange Temperatur oder CO2 AKTUELL selbst
        # noch eine Öffnen-Bedingung erfüllen (siehe Kommentar oben). Zusätzlich
        # `not outdoor_drier_enough` - identische Begründung wie bei
        # close_by_summer_outdoor oben, nur für Luftfeuchtigkeit statt
        # Temperatur.
        close_by_humidity_outdoor_reversal = (
            self._attr_is_on
            and outdoor_humidity_confirmed_worse
            and not open_by_temp
            and not open_by_co2
            and not outdoor_drier_enough
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
        # Dienste → Smart Climate → Zahnrad am jeweiligen Raum →
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

        # Wassertank-Benachrichtigung - bewusst als eigener, von der
        # eigentlichen Lüftungsempfehlung komplett unabhängiger Schritt VOR
        # der should_open/should_close-Verzweigung, damit sie in JEDEM
        # Neubewertungs-Durchlauf geprüft wird, unabhängig davon, welcher
        # der beiden Zweige unten folgt.
        await self._check_tank_full()
        await self._check_device_window_conflict(
            humidity_needs_open=humidity_needs_open,
            temp_needs_open=temp_needs_open,
            outdoor_drier_enough=outdoor_drier_enough,
            outdoor_cooler_enough=outdoor_cooler_enough,
        )

        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self._last_reason = None if silent_frost_close else reason
            self._last_state_change_at = dt_util.utcnow()
            if new_state:
                self._open_since = dt_util.utcnow()
            else:
                self._open_since = None
            self.async_write_ha_state()
            if silent_frost_close or silent_co2_close:
                self._last_notified_at = None
                self._log_push(
                    "keine Benachrichtigung (bewusst still: "
                    + (
                        "Frostschutz-Sensor fehlt"
                        if silent_frost_close
                        else "CO2 wieder im Normalbereich"
                    )
                    + ")"
                )
            elif self._window_action_needed(new_state):
                self._last_notified_at = dt_util.utcnow()
                await self._notify(new_state, reason)
            else:
                # Fensterkontakt zeigt bereits den gewünschten Zustand
                # (offen/geschlossen) - keine Benachrichtigung nötig.
                self._last_notified_at = None
                self._log_push(
                    "keine Benachrichtigung: Fensterkontakt zeigt bereits den "
                    f"Zielzustand ({'Öffnen' if new_state else 'Schließen'})"
                )
            await self._maybe_clear_notifications()
            await self._update_devices(
                temp_needs_open=temp_needs_open,
                temp_needs_close=temp_needs_close,
                humidity_needs_open=humidity_needs_open,
                humidity_needs_close=humidity_needs_close,
                outdoor_cooler_enough=outdoor_cooler_enough,
                dehumidifier_pause_open_window=dehumidifier_pause_open_window,
                heating_target_mode=heating_target_mode,
                want_summer_mode=want_summer_mode,
            )
            return

        await self._update_devices(
            temp_needs_open=temp_needs_open,
            temp_needs_close=temp_needs_close,
            humidity_needs_open=humidity_needs_open,
            humidity_needs_close=humidity_needs_close,
            outdoor_cooler_enough=outdoor_cooler_enough,
            dehumidifier_pause_open_window=dehumidifier_pause_open_window,
            heating_target_mode=heating_target_mode,
            want_summer_mode=want_summer_mode,
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
        heating_target_mode: str | None,
        want_summer_mode: bool,
    ) -> None:
        """Steuert optionalen Luftentfeuchter, optionale Klimaanlage,
        optionale Heizung und den globalen Sommer-/Winterbetrieb-Schalter.

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
        - Heizung: kein Ein/Aus, sondern Umschalten zwischen Comfort-/
          Standby-/Nacht-Sollwert (siehe _update_heating()) - heating_target_
          mode wurde in _evaluate() bereits final entschieden (inkl. Fenster-/
          Anwesenheits-/Sommermodus-Pausierung und optionalem Zeitplan);
          None = unverändert lassen (Totzone/fehlender Messwert).
        - Sommer-/Winterbetrieb: EIN bereits vorhandener, global unter
          CONF_SUMMER_MODE_SWITCH_ENTITY ausgewählter Schalter wird
          automatisch anhand einer Vorhersage-Temperatur ein-/
          ausgeschaltet (siehe _update_summer_mode()) - keine eigene
          Entität dieser Integration, bleibt jederzeit auch manuell
          bedienbar.
        - Ein konfigurierter Leistungssensor blockiert das Einschalten von
          Luftentfeuchter/Klimaanlage. Ist ein Gerät bereits an, wird es erst
          nach Ablauf der Abschalt-Verzögerung wegen dauerhaft zu geringer
          Einspeisung wieder ausgeschaltet. Heizung und Sommer-/
          Winterbetrieb-Schalter sind davon unberührt.
        """
        await self._update_single_device(
            entity_key=CONF_DEHUMIDIFIER_ENTITY,
            state_attr="_dehumidifier_state",
            low_power_attr="_dehumidifier_low_power_since",
            want_on=humidity_needs_open and not dehumidifier_pause_open_window,
            want_off=humidity_needs_close or dehumidifier_pause_open_window,
            runtime_since_attr="_dehumidifier_max_runtime_since",
            cooldown_until_attr="_dehumidifier_max_runtime_cooldown_until",
        )
        await self._update_single_device(
            entity_key=CONF_AC_ENTITY,
            state_attr="_ac_state",
            low_power_attr="_ac_low_power_since",
            want_on=temp_needs_open and not outdoor_cooler_enough,
            want_off=temp_needs_close or outdoor_cooler_enough,
            shutter_key=CONF_SHUTTER_ENTITY,
            runtime_since_attr="_ac_max_runtime_since",
            cooldown_until_attr="_ac_max_runtime_cooldown_until",
        )
        await self._update_summer_mode(want_summer_mode=want_summer_mode)
        await self._update_heating(target_mode=heating_target_mode)

    async def _update_single_device(
        self,
        *,
        entity_key: str,
        state_attr: str,
        low_power_attr: str,
        want_on: bool,
        want_off: bool,
        shutter_key: str | None = None,
        runtime_since_attr: str | None = None,
        cooldown_until_attr: str | None = None,
    ) -> None:
        entity_id = self._config.get(entity_key)
        if not entity_id:
            return
        if self._device_entity_missing(entity_id):
            # Integrationseintrag deaktiviert oder Entität sonst komplett
            # entfernt - kein Steuerversuch gegen eine nicht existierende
            # Entität, und die internen Tracker werden zurückgesetzt, damit
            # bei Rückkehr der Entität eine sauber neue Synchronisierung
            # stattfindet, statt auf einem veralteten Zustand aufzusetzen.
            setattr(self, state_attr, None)
            setattr(self, low_power_attr, None)
            if runtime_since_attr is not None:
                setattr(self, runtime_since_attr, None)
            if cooldown_until_attr is not None:
                setattr(self, cooldown_until_attr, None)
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
        # Maßgeblich ist der LIVE gelesene Gerätezustand, nicht nur der
        # interne Tracker: Ein von Hand/anderer Automation eingeschaltetes
        # oder nach einem Neustart nicht mehr zugeordnetes Gerät (Tracker
        # None/False) lief sonst bei zu geringer Einspeisung unbegrenzt weiter.
        live_state = self._get_device_live_state(entity_id)
        device_running = live_state is True or (current is True and live_state is None)
        force_off_due_to_power = False
        if device_running and power_entity_configured:
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
        elif live_state is False:
            setattr(self, low_power_attr, None)

        # Der interne Tracker allein bestätigt nur, dass ein Befehl
        # erfolgreich AN Home Assistant übergeben wurde - nicht, dass das
        # Gerät ihn auch tatsächlich übernommen hat (siehe CLAUDE.md
        # Lektion 47/56: bei instabiler Funk-/Zigbee-Anbindung kann ein
        # Befehl unbemerkt verschluckt werden). Der live gelesene
        # Gerätezustand entscheidet deshalb zusätzlich mit, ob ein Befehl
        # als bereits erledigt gilt - ist er gerade nicht lesbar
        # (unavailable/unknown), bleibt es beim reinen Tracker-Vergleich,
        # um kein Kommando gegen eine gerade nicht antwortende Entität zu
        # wiederholen.
        off_confirmed = current is False and live_state is not True
        on_confirmed = current is True and live_state is not False

        # Höchstlaufzeit-Begrenzung (CONF_DEVICE_MAX_RUNTIME_MINUTES) -
        # verfolgt die tatsächliche, LIVE abgefragte Laufzeit (nicht den
        # internen Tracker "current", der nur bestätigt, dass wir zuletzt
        # "an" kommandiert haben, siehe Lektion 47/56). Ein vorhandener
        # Einspeiseleistungs-Überschuss (Leistung mindestens so hoch wie die
        # Mindesteinspeiseleistung, nur mit Leistungssensor) verwendet eine
        # EIGENE Höchstlaufzeit (CONF_DEVICE_MAX_RUNTIME_HIGH_SURPLUS_MINUTES,
        # Standard 0 = unbegrenzt wie bisher); bei geringer Einspeiseleistung
        # bzw. ohne Leistungssensor gilt CONF_DEVICE_MAX_RUNTIME_MINUTES.
        force_off_due_to_max_runtime = False
        if runtime_since_attr is not None:
            if live_state is True:
                if getattr(self, runtime_since_attr) is None:
                    setattr(self, runtime_since_attr, dt_util.utcnow())
            elif live_state is False:
                setattr(self, runtime_since_attr, None)
            # live_state is None (Entität kurz nicht lesbar): Timer bleibt
            # unverändert stehen - sonst würde ein einzelner Ausrutscher die
            # bereits gelaufene Zeit verschleiern (analog zur on_confirmed/
            # off_confirmed-Behandlung von "nicht lesbar" oben).

            runtime_since = getattr(self, runtime_since_attr)
            if power_entity_configured and power_ok:
                max_minutes = self._effective(
                    CONF_DEVICE_MAX_RUNTIME_HIGH_SURPLUS_MINUTES,
                    DEFAULT_DEVICE_MAX_RUNTIME_HIGH_SURPLUS_MINUTES,
                )
            else:
                max_minutes = self._effective(
                    CONF_DEVICE_MAX_RUNTIME_MINUTES, DEFAULT_DEVICE_MAX_RUNTIME_MINUTES
                )
            if (
                max_minutes > 0
                and runtime_since is not None
                and (dt_util.utcnow() - runtime_since).total_seconds() / 60
                >= max_minutes
            ):
                force_off_due_to_max_runtime = True
                if cooldown_until_attr is not None:
                    cooldown_minutes = self._effective(
                        CONF_DEVICE_MAX_RUNTIME_COOLDOWN_MINUTES,
                        DEFAULT_DEVICE_MAX_RUNTIME_COOLDOWN_MINUTES,
                    )
                    setattr(
                        self,
                        cooldown_until_attr,
                        dt_util.utcnow() + timedelta(minutes=cooldown_minutes),
                    )

        # Ruhezeit nach einem Zwangs-Abschalten wegen Höchstlaufzeit - ohne
        # diese würde das Gerät bei weiterhin hoher Luftfeuchtigkeit/
        # Temperatur sofort wieder einschalten und die Begrenzung wäre
        # wirkungslos.
        block_on_due_to_cooldown = False
        if cooldown_until_attr is not None:
            cooldown_until = getattr(self, cooldown_until_attr)
            if cooldown_until is not None:
                if dt_util.utcnow() < cooldown_until:
                    block_on_due_to_cooldown = True
                else:
                    setattr(self, cooldown_until_attr, None)

        if (
            want_off or force_off_due_to_power or force_off_due_to_max_runtime
        ) and not off_confirmed:
            await self._set_device_state(entity_id, False)
            setattr(self, state_attr, False)
            setattr(self, low_power_attr, None)
            if shutter_key:
                await self._set_shutter(self._config.get(shutter_key), close=False)
            self.async_write_ha_state()
        elif (
            want_on
            and not force_off_due_to_power
            and not block_on_due_to_cooldown
            and not on_confirmed
        ):
            if power_ok:
                await self._set_device_state(entity_id, True)
                setattr(self, state_attr, True)
                setattr(self, low_power_attr, None)
                if shutter_key:
                    await self._set_shutter(self._config.get(shutter_key), close=True)
                self.async_write_ha_state()
            # sonst: noch nicht genug Einspeiseleistung - beim nächsten
            # Tick (spätestens alle 5 Minuten) wird erneut geprüft.

    async def _update_heating(self, *, target_mode: str | None) -> None:
        """Steuert eine optionale Heizung über vier feste Stufen (Comfort/
        Standby/Nacht/Gebäudeschutz, siehe const.py) statt eines einfachen
        Ein/Aus wie bei Luftentfeuchter/Klimaanlage - für Heizungen ist das
        die übliche Betriebsart. target_mode wurde in _evaluate() bereits
        final entschieden (Priorität Fenster/Anwesenheit/Sommermodus vor
        Zeitplan vor Schwellenwert-Hysterese) - None bedeutet "unverändert
        lassen" (Totzone der Schwellenwert-Hysterese oder fehlender
        Innentemperatur-Messwert, siehe _evaluate()).

        Ist Preset-Steuerung wirksam (siehe _heating_preset_mode_effective())
        UND für target_mode ein Preset-Name konfiguriert, wird
        climate.set_preset_mode gerufen - sonst (kein Preset-Name für genau
        diesen Modus hinterlegt, z. B. Gebäudeschutz, oder Preset-Steuerung
        insgesamt nicht wirksam) wie bisher über climate.set_temperature
        (Gebäudeschutz nutzt dafür ersatzweise den Standby-Sollwert, da es
        dafür keinen eigenen Zahlen-Sollwert gibt).

        self._heating_state merkt sich zwar weiterhin den zuletzt
        kommandierten Modus (vermeidet unnötige Wiederholungen bei
        unverändertem target_mode), reicht als alleinige Idempotenz-Prüfung
        aber nicht: sowohl climate.set_temperature als auch
        climate.set_preset_mode laufen mit blocking=True, das bestätigt nur,
        dass Home Assistant den Service-Aufruf erfolgreich verarbeitet hat -
        bei einer instabilen Funk-/Zigbee-Anbindung kann das Gerät den
        Befehl trotzdem nie tatsächlich übernehmen, ohne dass das hier als
        Fehler ankommt. Deshalb zusätzlich der live vom Gerät gelesene
        Sollwert/preset_mode gegen den gewünschten Wert geprüft - weicht er
        ab, wird der Befehl erneut geschickt, auch wenn sich target_mode
        gegenüber self._heating_state nicht geändert hat. Ist der aktuelle
        Wert gerade nicht lesbar (Entität kurz nicht verfügbar), bleibt es
        beim reinen Tracker-Vergleich, um kein Kommando gegen eine gerade
        nicht antwortende Entität zu wiederholen."""
        entity_id = self._get_heating_entity_id()
        if not entity_id:
            return
        if self._device_entity_missing(entity_id):
            self._heating_state = None
            return
        if target_mode is None:
            return

        if self._heating_preset_mode_effective(entity_id):
            preset_name = self._get_heating_preset_name(target_mode)
            if preset_name:
                current_preset = self._get_heating_live_preset_mode(entity_id)
                already_confirmed = current_preset is None or current_preset == preset_name
                if target_mode == self._heating_state and already_confirmed:
                    return
                await self._set_heating_preset_mode(entity_id, preset_name)
                self._heating_state = target_mode
                return
            # Kein Preset-Name für diesen einzelnen Modus hinterlegt - fällt
            # NUR für diesen Aufruf auf die Sollwert-Steuerung unten zurück.

        temperature = self._effective(
            {
                "comfort": CONF_HEATING_COMFORT_TEMP,
                "standby": CONF_HEATING_STANDBY_TEMP,
                "night": CONF_HEATING_NIGHT_TEMP,
                "building_protection": CONF_HEATING_STANDBY_TEMP,
            }[target_mode],
            {
                "comfort": DEFAULT_HEATING_COMFORT_TEMP,
                "standby": DEFAULT_HEATING_STANDBY_TEMP,
                "night": DEFAULT_HEATING_NIGHT_TEMP,
                "building_protection": DEFAULT_HEATING_STANDBY_TEMP,
            }[target_mode],
        )
        current_target = self._get_heating_target_temperature(entity_id)
        already_confirmed = current_target is None or abs(current_target - temperature) < 0.05
        if target_mode == self._heating_state and already_confirmed:
            return

        await self._set_heating_temperature(entity_id, temperature)
        self._heating_state = target_mode

    async def _update_summer_mode(self, *, want_summer_mode: bool) -> None:
        """Schaltet den unter CONF_SUMMER_MODE_SWITCH_ENTITY ausgewählten,
        bereits vorhandenen Schalter (CLAUDE.md Lektion 46/47 - KEINE
        eigene Entität dieser Integration) - nur, wenn sich der Zielzustand
        vom aktuellen Live-Zustand unterscheidet (idempotent, analog zu
        _update_single_device()/_update_heating()). Dadurch bleibt ein
        manueller Schaltvorgang ebenso wie der zuletzt automatisch gesetzte
        Zustand unangetastet, solange want_summer_mode (siehe _evaluate())
        sich nicht ändert. Da mehrere Räume unabhängig voneinander dieselbe
        Entscheidung (siehe _evaluate(): global statt raum-effektiv
        berechnete Schwelle/Marge) treffen und denselben Schalter ansteuern
        können, ist ein redundanter, aber harmloser Schreibversuch mehrerer
        Räume im selben Bewertungslauf möglich - dank Idempotenz-Prüfung
        hier bleibt das folgenlos."""
        entity_id = self._effective(CONF_SUMMER_MODE_SWITCH_ENTITY, None)
        if not entity_id or self._device_entity_missing(entity_id):
            return
        current = self._is_summer_mode_active()
        if want_summer_mode and not current:
            await self._set_summer_mode_switch(entity_id, True)
        elif not want_summer_mode and current:
            await self._set_summer_mode_switch(entity_id, False)

    async def _set_summer_mode_switch(self, entity_id: str, turn_on: bool) -> None:
        try:
            await self.hass.services.async_call(
                "switch",
                "turn_on" if turn_on else "turn_off",
                {"entity_id": entity_id},
                blocking=False,
            )
        except HomeAssistantError:
            _LOGGER.warning(
                "Konnte Sommer-/Winterbetrieb-Schalter %s nicht %s (Raum %s)",
                entity_id,
                "einschalten" if turn_on else "ausschalten",
                self._config[CONF_ROOM_NAME],
            )

    async def _set_heating_temperature(self, entity_id: str, temperature: float) -> None:
        """Setzt den Sollwert einer Heizungs-climate-Entität.

        blocking=True (anders als _set_device_state()/_set_shutter(), die
        bewusst blocking=False verwenden) - climate.set_temperature validiert
        den übergebenen Wert gegen das Schema der Ziel-Entität (u. a.
        min_temp/max_temp/target_temp_step), ein Validierungsfehler passiert
        bei blocking=False in einem unbeobachteten Hintergrund-Task und würde
        vom try/except hier nicht abgefangen (siehe CLAUDE.md, Lektion 35).

        Bewusst `except Exception` statt nur `except HomeAssistantError`
        (Nachtrag zu Lektion 35, 0.64.x): Ein Schema-Validierungsfehler von
        hass.services.async_call() ist KEINE HomeAssistantError-Unterklasse
        (beobachtet als `probatio.error.MultipleInvalid: not a valid option
        at 'data'`, unverändert durchgereicht aus homeassistant/core.py) -
        `except HomeAssistantError` allein ließ genau diesen Fehler trotz
        blocking=True weiterhin bis zum unbeobachteten Task durchreichen.
        Der try-Block enthält ausschließlich diesen einen Service-Aufruf,
        ein bewusst breiter Except-Typ maskiert hier keine anderen Fehler."""
        try:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"entity_id": entity_id, "temperature": temperature},
                blocking=True,
            )
        except Exception:  # noqa: BLE001 - siehe Docstring oben
            _LOGGER.warning(
                "Konnte Sollwert für Heizung %s nicht auf %s setzen (Raum %s)",
                entity_id,
                temperature,
                self._config[CONF_ROOM_NAME],
            )

    async def _set_heating_preset_mode(self, entity_id: str, preset_mode: str) -> None:
        """Setzt den preset_mode einer Heizungs-climate-Entität - analog zu
        _set_heating_temperature() (blocking=True, siehe Lektion 35: ein
        Schema-Validierungsfehler, z. B. ein preset_mode, den die Entität
        aktuell nicht in ihrer preset_modes-Liste führt, muss synchron
        ankommen, um ihn hier abzufangen statt als "Task exception was
        never retrieved" im Log zu landen).

        `except Exception` statt nur `except HomeAssistantError` - siehe
        Docstring von _set_heating_temperature() (Nachtrag zu Lektion 35)."""
        try:
            await self.hass.services.async_call(
                "climate",
                "set_preset_mode",
                {"entity_id": entity_id, "preset_mode": preset_mode},
                blocking=True,
            )
        except Exception:  # noqa: BLE001 - siehe Docstring oben
            _LOGGER.warning(
                "Konnte Preset für Heizung %s nicht auf %s setzen (Raum %s)",
                entity_id,
                preset_mode,
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
            humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY), decimals=0)
            threshold = self._effective(
                CONF_HUMIDITY_THRESHOLD_OPEN if opening else CONF_HUMIDITY_THRESHOLD_CLOSE,
                DEFAULT_HUMIDITY_THRESHOLD_OPEN if opening else DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
            )
            return (
                self._format_measurement(humidity, "%"),
                self._format_measurement(threshold, "%"),
            )
        if context_reason == "co2":
            co2 = self._get_float_state(self._config.get(CONF_CO2_ENTITY), decimals=0)
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
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None), decimals=1
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
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None), decimals=1
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
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None), decimals=1
            )
            indoor_temp = self._get_indoor_temperature()
            return (
                self._format_measurement(outdoor_temp, "°C", 1),
                self._format_measurement(indoor_temp, "°C", 1),
            )
        if context_reason == "outdoor_wetter":
            outdoor_humidity = self._get_float_state(
                self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None), decimals=0
            )
            outdoor_temp = self._get_float_state(
                self._effective(CONF_OUTDOOR_TEMP_ENTITY, None), decimals=1
            )
            indoor_temp = self._get_indoor_temperature()
            humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY), decimals=0)
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
        persistent_enabled = self._effective(CONF_PERSISTENT_ENABLED, False)

        if sonos_entities:
            tts_entity = self._effective(CONF_TTS_ENTITY, None)
            if tts_entity:
                if self._is_tts_quiet_hours_active():
                    _LOGGER.debug(
                        "Sprachausgabe in Raum %s wegen Nachtruhe unterdrückt",
                        room,
                    )
                elif self._is_tts_light_off():
                    _LOGGER.debug(
                        "Sprachausgabe in Raum %s unterdrückt, da das "
                        "konfigurierte Licht aus ist",
                        room,
                    )
                else:
                    await self._play_tts(sonos_entities, tts_entity, message)
            else:
                _LOGGER.warning(
                    "Sprachausgabe-Lautsprecher ausgewählt, aber keine "
                    "TTS-Entity konfiguriert (%s)",
                    room,
                )

        # Fester tag pro Raum (Standard von _send_mobile_push): eine neue
        # Benachrichtigung ersetzt auf dem Gerät automatisch eine ggf. noch
        # angezeigte ältere (z. B. "bitte öffnen" -> "bitte schließen"), und
        # markiert, dass hier ggf. noch eine "clean notification" fällig
        # wird (siehe _maybe_clear_notifications()).
        if await self._push_to_targets(
            message,
            title=self._notification_title("Lüften"),
            log_label=(
                "Erinnerung"
                if reason == "reminder"
                else ("Öffnen" if should_ventilate else "Schließen")
            ),
        ):
            self._mobile_notification_active = True

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
                        "title": self._notification_title("Lüften"),
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

    def _notification_title(self, base: str) -> str:
        """Titel für Push und persistente Benachrichtigung: Raumname zuerst,
        dann die eigentliche Überschrift ("Wohnzimmer – Lüften"), damit der
        Raum auch in der Push-Vorschau sofort erkennbar ist."""
        return f"{self._config[CONF_ROOM_NAME]} – {base}"

    def _notification_id(self) -> str:
        """Fester, raumeindeutiger Bezeichner - als notification_id für die
        persistente Web-Benachrichtigung und als tag für Push-
        Benachrichtigungen. Erlaubt in beiden Fällen sowohl das Ersetzen
        einer bereits angezeigten Benachrichtigung durch eine neue als auch
        das gezielte Auflösen (persistent_notification.dismiss bzw.
        clear_notification)."""
        return f"smart_ventilation_{self._entry.entry_id}"

    def _tank_notification_id(self) -> str:
        """Wie _notification_id(), aber eigenständig für die Wassertank-
        Benachrichtigung (siehe _notify_tank_full()) - verhindert, dass eine
        Tank-Benachrichtigung eine gerade angezeigte Lüftungsempfehlung (oder
        umgekehrt) auf demselben Gerät überschreibt, da beide sonst densel-
        ben tag/dieselbe notification_id teilen würden."""
        return f"{self._notification_id()}_tank"

    async def _send_mobile_push(
        self,
        entity_id: str,
        message: str,
        *,
        title: str | None = None,
        tag: str | None = None,
    ) -> str | None:
        """Verschickt eine App-Push-Nachricht an ein einzelnes notify-Ziel.

        WICHTIG (CLAUDE.md Lektion 66): Der Entity-Dienst `notify.send_message`
        akzeptiert ausschließlich `message` und `title` - ein `data`-Feld
        (und damit `tag`/`clear_notification` der Companion-App) wird von
        Home Assistant mit "not a valid option at 'data'" abgelehnt. Genau
        das ließ bis 0.79.0 JEDEN Push scheitern. Ersetzen/Auflösen einer
        Benachrichtigung (`tag`, "clean notification", Lektion 18) kennt nur
        der klassische Companion-Dienst `notify.mobile_app_<gerät>`. Deshalb:

        1. Existiert für das Ziel ein passender `notify.mobile_app_*`-Dienst
           (siehe _mobile_app_service_name()), wird er mit `data.tag`
           aufgerufen - volle Funktion inkl. Ersetzen und Auflösen.
        2. Sonst geht die Nachricht über `notify.send_message` OHNE `data`
           raus: sie kommt an, lässt sich aber nicht ersetzen/auflösen. Ein
           "clear_notification" wird dann gar nicht gesendet (es würde als
           Klartext-Nachricht angezeigt).

        Bewusst `blocking=True`, obwohl der Rest dieser Integration
        Geräte-Steuerbefehle üblicherweise mit `blocking=False` abfeuert:
        Ein Schema-Fehler muss synchron in diesem `await` ankommen, um hier
        abgefangen zu werden (Lektion 35). `except Exception` statt nur
        `except HomeAssistantError`: die Schema-Validierung wirft
        `MultipleInvalid`, keine HomeAssistantError-Unterklasse (Lektion 35,
        Nachtrag). Der try-Block enthält ausschließlich den einen
        Service-Aufruf, ein breiter Except-Typ maskiert hier nichts anderes.

        Liefert None bei Erfolg (aus Sicht von Home Assistant - ob das
        Gerät die Nachricht tatsächlich anzeigt, ist damit nicht belegt),
        sonst den Fehlertext. Jeder Versuch landet im `push_verlauf` (mit
        dem genutzten Weg); das reine Auflösen ("clear_notification") nur
        im Fehlerfall, um den Verlauf nicht mit Routine-Einträgen zu
        füllen."""
        is_clear = message == "clear_notification"
        service = self._mobile_app_service_name(entity_id)
        if service is not None:
            call_domain, call_service = "notify", service
            data: dict = {
                "message": message,
                "data": {"tag": tag or self._notification_id()},
            }
            via = f"über notify.{service}"
        else:
            if is_clear:
                _LOGGER.debug(
                    "Auflösen für %s übersprungen: kein notify.mobile_app_*-"
                    "Dienst gefunden, ohne tag nicht möglich",
                    entity_id,
                )
                return None
            call_domain, call_service = "notify", "send_message"
            data = {"entity_id": entity_id, "message": message}
            via = (
                "ohne tag (kein notify.mobile_app_*-Dienst zu diesem Ziel "
                "gefunden - Ersetzen/Auflösen nicht möglich)"
            )
        if title is not None:
            data["title"] = title
        try:
            await self.hass.services.async_call(
                call_domain, call_service, data, blocking=True
            )
        except Exception as err:  # noqa: BLE001 - siehe Docstring oben
            error = f"{type(err).__name__}: {err}"
            self._log_push(
                f"FEHLER beim Senden an {entity_id} {via}: {error}",
                level=logging.WARNING,
            )
            return error
        if not is_clear:
            self._log_push(
                f"gesendet an {entity_id} {via} ({title or 'ohne Titel'})"
            )
        return None

    def _mobile_app_service_name(self, entity_id: str) -> str | None:
        """Ermittelt zu einem notify-Ziel (Entität der Companion App) den
        klassischen Dienstnamen `mobile_app_<gerät>` unter der `notify`-
        Domain, falls dieser existiert - nur er unterstützt `data`
        (`tag`, `clear_notification`), siehe _send_mobile_push().

        Kandidaten: der aus dem Gerätenamen (Geräteregister) abgeleitete
        Slug, danach der Objekt-Teil der Entity-ID selbst (bei Companion-App-
        Entitäten stimmt beides in aller Regel überein). Gilt nur, wenn der
        Dienst tatsächlich registriert ist."""
        candidates: list[str] = []
        try:
            entry = er.async_get(self.hass).async_get(entity_id)
            if entry is not None and entry.device_id:
                device = dr.async_get(self.hass).async_get(entry.device_id)
                if device is not None:
                    for name in (device.name, device.name_by_user):
                        if name:
                            candidates.append(slugify(name))
        except Exception:  # noqa: BLE001 - reine Komfort-Ermittlung
            _LOGGER.debug("Geräteregister-Abfrage für %s fehlgeschlagen", entity_id)
        candidates.append(entity_id.split(".", 1)[-1])
        for candidate in candidates:
            service = f"mobile_app_{candidate}"
            if self.hass.services.has_service("notify", service):
                return service
        return None

    def _log_push(self, text: str, *, level: int = logging.INFO) -> None:
        """Hängt einen Eintrag (neueste zuerst) an den `push_verlauf` an,
        schreibt ihn ins Log und aktualisiert den Zustand, damit das
        Attribut sofort sichtbar ist."""
        stamp = dt_util.as_local(dt_util.utcnow()).strftime("%d.%m. %H:%M:%S")
        self._push_log.appendleft(f"{stamp} {text}")
        _LOGGER.log(level, "Push (%s): %s", self._config[CONF_ROOM_NAME], text)
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    async def _push_to_targets(
        self,
        message: str,
        *,
        title: str,
        log_label: str,
        tag: str | None = None,
    ) -> bool:
        """Sendet `message` an alle konfigurierten App-Push-Ziele des Raums
        (Raum-Override bzw. globale Liste) und protokolliert jede
        Entscheidung im `push_verlauf` - auch die, NICHT zu senden (Push
        wirksam deaktiviert, kein Ziel konfiguriert, Anwesenheits-Entität
        steht nicht auf "home"), die früher still übergangen wurden.

        Liefert True, wenn Push aktiv ist und mindestens ein Ziel
        konfiguriert war (damit der Aufrufer eine spätere "clean
        notification" einplanen kann), unabhängig davon, ob die
        Anwesenheitsprüfung einzelne Ziele übersprungen hat."""
        if not self._effective(CONF_MOBILE_ENABLED, False):
            self._log_push(
                f"nicht gesendet ({log_label}): App-Push ist wirksam "
                "deaktiviert (weder im Raum noch global aktiviert)"
            )
            return False
        targets = [
            t for t in self._get_mobile_targets() if t.get(CONF_MOBILE_NOTIFY_ENTITY)
        ]
        if not targets:
            self._log_push(
                f"nicht gesendet ({log_label}): keine notify-Entität "
                "konfiguriert",
                level=logging.WARNING,
            )
            return False
        for target in targets:
            entity_id = target[CONF_MOBILE_NOTIFY_ENTITY]
            presence_entity = target.get(CONF_PRESENCE_ENTITY)
            if self._is_present(presence_entity):
                await self._send_mobile_push(
                    entity_id, message, title=title, tag=tag
                )
            else:
                presence_state = self.hass.states.get(presence_entity)
                self._log_push(
                    f"übersprungen ({log_label}): {entity_id} - "
                    "Anwesenheits-Entität steht auf "
                    f"'{presence_state.state if presence_state else 'unbekannt'}'"
                    ", nicht auf 'home'"
                )
        return True

    async def async_send_test_push(self) -> None:
        """Entity-Dienst `send_test_push`: schickt eine Test-Nachricht über
        exakt denselben Sendeweg (`_send_mobile_push`) an alle App-Push-
        Ziele des Raums - unabhängig davon, ob Push für den Raum aktiv ist
        oder die Person gerade zuhause ist - und protokolliert zusätzlich
        je Ziel, ob eine ECHTE Benachrichtigung jetzt gesendet würde. Ein
        Sendefehler wird dem Aufrufer als Fehler gemeldet (sichtbar in den
        Entwicklerwerkzeugen)."""
        room = self._config[CONF_ROOM_NAME]
        targets = [
            t for t in self._get_mobile_targets() if t.get(CONF_MOBILE_NOTIFY_ENTITY)
        ]
        if not targets:
            self._log_push(
                "Test: keine notify-Entität konfiguriert (weder im Raum noch "
                "global)",
                level=logging.WARNING,
            )
            raise HomeAssistantError(
                f"Raum {room}: keine notify-Entität für App-Push konfiguriert"
            )
        enabled = self._effective(CONF_MOBILE_ENABLED, False)
        failures: list[str] = []
        for target in targets:
            entity_id = target[CONF_MOBILE_NOTIFY_ENTITY]
            error = await self._send_mobile_push(
                entity_id,
                f"Test-Push aus Raum {room}",
                title=self._notification_title("Smart Climate Test"),
                tag=f"{self._notification_id()}_test",
            )
            if error is not None:
                failures.append(f"{entity_id}: {error}")
                continue
            if not enabled:
                verdict = "NICHT gesendet: App-Push ist wirksam deaktiviert"
            elif not self._is_present(target.get(CONF_PRESENCE_ENTITY)):
                verdict = "NICHT gesendet: Anwesenheits-Entität steht nicht auf 'home'"
            else:
                verdict = "würde gesendet"
            self._log_push(
                f"Test an {entity_id} von Home Assistant angenommen - echte "
                f"Benachrichtigung {verdict}"
            )
        if failures:
            raise HomeAssistantError(
                "Test-Push fehlgeschlagen: " + "; ".join(failures)
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

    async def _check_shower_too_long(self) -> None:
        """Sprachansage, sobald die erkannte Dusche länger als
        CONF_SHOWER_MAX_DURATION Minuten ununterbrochen läuft - einmal pro
        Dusche (self._shower_long_announced). Nur Sprachausgabe (keine
        App-/Web-Benachrichtigung, Nutzerwunsch) und nur, wenn für den Raum
        Lautsprecher und eine TTS-Entität vorhanden sind; Nachtruhe und
        Licht-aus-Regel gelten wie bei der Wassertank-Ansage. Ist die Ansage
        durch Nachtruhe/Licht unterdrückt, gilt sie trotzdem als erledigt -
        sonst würde sie mitten in der Dusche nachgeholt, sobald die
        Nachtruhe endet. Standard 0 = aus."""
        max_minutes = self._effective(CONF_SHOWER_MAX_DURATION, DEFAULT_SHOWER_MAX_DURATION)
        if (
            not max_minutes
            or not self._showering
            or self._shower_on_since is None
            or self._shower_long_announced
        ):
            return
        minutes = int(
            (dt_util.utcnow() - self._shower_on_since).total_seconds() / 60
        )
        if minutes < max_minutes:
            return
        self._shower_long_announced = True
        sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
        tts_entity = self._effective(CONF_TTS_ENTITY, None)
        if (
            not sonos_entities
            or not tts_entity
            or self._is_tts_quiet_hours_active()
            or self._is_tts_light_off()
        ):
            return
        room = self._config[CONF_ROOM_NAME]
        template = self._effective(CONF_MSG_SHOWER_LONG, DEFAULT_MSG_SHOWER_LONG)
        try:
            message = template.format(raum=room, wert=minutes, schwelle=max_minutes)
        except (KeyError, ValueError, IndexError):
            _LOGGER.warning(
                "Duschdauer-Ansagetext für Raum %s enthält einen ungültigen "
                "Platzhalter - wird unverändert gesendet: %s",
                room,
                template,
            )
            message = template
        await self._play_tts(sonos_entities, tts_entity, message)

    async def _check_tank_full(self) -> None:
        """Prüft bei jeder Neubewertung, ob sich der Wassertank-Status des
        Luftentfeuchters geändert hat, und benachrichtigt bei Bedarf (siehe
        CONF_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED) - komplett unabhängig
        von der eigentlichen Lüftungsempfehlung. Ohne konfigurierten
        Tank-Sensor oder ohne aktivierte Benachrichtigung bleibt
        _tank_full_state unverändert auf None, es passiert nichts."""
        tank_full_entity = self._config.get(CONF_DEHUMIDIFIER_TANK_FULL_ENTITY)
        if not tank_full_entity or not self._config.get(
            CONF_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED,
            DEFAULT_DEHUMIDIFIER_TANK_NOTIFICATION_ENABLED,
        ):
            return
        tank_state = self.hass.states.get(tank_full_entity)
        tank_full = tank_state is not None and tank_state.state == "on"
        if tank_full != self._tank_full_state:
            self._tank_full_state = tank_full
            await self._notify_tank_full(tank_full)

    async def _notify_tank_full(self, tank_full: bool) -> None:
        """Benachrichtigt über den vollen Wassertank des Luftentfeuchters -
        nutzt dieselben, für den Raum aktuell wirksamen Kanäle wie die
        Lüftungsempfehlung (_notify()), aber mit eigenem Text
        (CONF_MSG_TANK_FULL) und eigener notification_id/tag (siehe
        _tank_notification_id()), damit sich beide Benachrichtigungen nicht
        gegenseitig überschreiben. Löst sich automatisch wieder auf, sobald
        der Tank wieder als "leer" gemeldet wird (analog zum "Clean
        Notification"-Muster, Lektion 18/43), unabhängig vom Zustand der
        eigentlichen Lüftungsempfehlung."""
        room = self._config[CONF_ROOM_NAME]
        sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
        persistent_enabled = self._effective(CONF_PERSISTENT_ENABLED, False)

        if not tank_full:
            if self._tank_mobile_notification_active:
                for target in self._get_mobile_targets():
                    entity_id = target.get(CONF_MOBILE_NOTIFY_ENTITY)
                    if entity_id:
                        await self._send_mobile_push(
                            entity_id,
                            "clear_notification",
                            tag=self._tank_notification_id(),
                        )
                self._tank_mobile_notification_active = False
            if self._tank_persistent_notification_active:
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": self._tank_notification_id()},
                    blocking=False,
                )
                self._tank_persistent_notification_active = False
            return

        template = self._effective(CONF_MSG_TANK_FULL, DEFAULT_MSG_TANK_FULL)
        try:
            message = template.format(raum=room)
        except (KeyError, ValueError, IndexError):
            _LOGGER.warning(
                "Wassertank-Benachrichtigungstext für Raum %s enthält einen "
                "ungültigen Platzhalter - wird unverändert gesendet: %s",
                room,
                template,
            )
            message = template

        if sonos_entities:
            tts_entity = self._effective(CONF_TTS_ENTITY, None)
            if (
                tts_entity
                and not self._is_tts_quiet_hours_active()
                and not self._is_tts_light_off()
            ):
                await self._play_tts(sonos_entities, tts_entity, message)

        if await self._push_to_targets(
            message,
            title=self._notification_title("Wassertank"),
            log_label="Wassertank voll",
            tag=self._tank_notification_id(),
        ):
            self._tank_mobile_notification_active = True

        if persistent_enabled:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "notification_id": self._tank_notification_id(),
                    "title": self._notification_title("Wassertank"),
                    "message": message,
                },
                blocking=False,
            )
            self._tank_persistent_notification_active = True

    def _dehumidifier_window_conflict_notification_id(self) -> str:
        """Wie _tank_notification_id(), aber eigenständig für die
        Fenster-Konflikt-Benachrichtigung des Luftentfeuchters (siehe
        _check_device_window_conflict())."""
        return f"{self._notification_id()}_dehum_window_conflict"

    def _ac_window_conflict_notification_id(self) -> str:
        """Wie _dehumidifier_window_conflict_notification_id(), aber für die
        Klimaanlage - eigener Bezeichner, damit sich beide Fenster-Konflikt-
        Benachrichtigungen nicht gegenseitig überschreiben, falls in einem
        Raum sowohl Luftentfeuchter als auch Klimaanlage konfiguriert sind
        und beide Konflikte gleichzeitig auftreten."""
        return f"{self._notification_id()}_ac_window_conflict"

    async def _check_device_window_conflict(
        self,
        *,
        humidity_needs_open: bool,
        temp_needs_open: bool,
        outdoor_drier_enough: bool,
        outdoor_cooler_enough: bool,
    ) -> None:
        """Prüft bei jeder Neubewertung, ob ein konfigurierter Luftentfeuchter
        und/oder eine konfigurierte Klimaanlage bei offenem Fenster gegen
        nachströmende, ungünstigere Außenluft ankämpft (siehe
        CONF_DEVICE_WINDOW_CONFLICT_NOTIFICATION_ENABLED) - komplett
        unabhängig von der eigentlichen Lüftungsempfehlung, da diese hier
        durchaus bereits "aus"/neutral sein kann (should_close hat in diesem
        Zustand keine Wirkung mehr, siehe CLAUDE.md).

        Bewusst UNABHÄNGIG vom Einspeiseleistungs-Überschuss (anders als
        dehumidifier_pause_open_window/das reine Einschalten selbst) - das
        Schließen des Fensters hilft dem Gerät, sein Ziel tatsächlich zu
        erreichen, auch wenn der Betrieb gerade "kostenlos" ist.

        Luftentfeuchter und Klimaanlage werden unabhängig voneinander
        geprüft und benachrichtigt (eigene Zustands-Tracker/Notification-
        IDs) - beide Konflikte können gleichzeitig, aber auch zeitlich
        versetzt auftreten und enden."""
        if not self._config.get(
            CONF_DEVICE_WINDOW_CONFLICT_NOTIFICATION_ENABLED,
            DEFAULT_DEVICE_WINDOW_CONFLICT_NOTIFICATION_ENABLED,
        ):
            return
        window_open = self._is_window_confirmed_open()

        if self._config.get(CONF_DEHUMIDIFIER_ENTITY):
            conflict = window_open and humidity_needs_open and not outdoor_drier_enough
            if conflict != self._dehumidifier_window_conflict_state:
                self._dehumidifier_window_conflict_state = conflict
                await self._notify_device_window_conflict(
                    conflict,
                    mobile_active_attr="_dehumidifier_window_conflict_mobile_active",
                    persistent_active_attr="_dehumidifier_window_conflict_persistent_active",
                    notification_id=self._dehumidifier_window_conflict_notification_id(),
                    device_label="Luftentfeuchter",
                )

        if self._config.get(CONF_AC_ENTITY):
            conflict = window_open and temp_needs_open and not outdoor_cooler_enough
            if conflict != self._ac_window_conflict_state:
                self._ac_window_conflict_state = conflict
                await self._notify_device_window_conflict(
                    conflict,
                    mobile_active_attr="_ac_window_conflict_mobile_active",
                    persistent_active_attr="_ac_window_conflict_persistent_active",
                    notification_id=self._ac_window_conflict_notification_id(),
                    device_label="Klimaanlage",
                )

    async def _notify_device_window_conflict(
        self,
        conflict: bool,
        *,
        mobile_active_attr: str,
        persistent_active_attr: str,
        notification_id: str,
        device_label: str,
    ) -> None:
        """Benachrichtigt über einen Fenster-Gerät-Konflikt (siehe
        _check_device_window_conflict()) - nutzt dieselben, für den Raum
        aktuell wirksamen Kanäle wie die Lüftungsempfehlung (_notify()),
        aber mit eigenem Text (CONF_MSG_DEVICE_WINDOW_CONFLICT) und eigener
        notification_id/eigenem tag, parametrisiert über mobile_active_attr/
        persistent_active_attr/notification_id, damit dieselbe Methode für
        Luftentfeuchter UND Klimaanlage wiederverwendet werden kann, ohne
        sich gegenseitig zu überschreiben. Löst sich automatisch wieder auf
        ("clean notification", Lektion 18/43/62), sobald der Konflikt nicht
        mehr besteht."""
        room = self._config[CONF_ROOM_NAME]
        sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
        persistent_enabled = self._effective(CONF_PERSISTENT_ENABLED, False)

        if not conflict:
            if getattr(self, mobile_active_attr):
                for target in self._get_mobile_targets():
                    entity_id = target.get(CONF_MOBILE_NOTIFY_ENTITY)
                    if entity_id:
                        await self._send_mobile_push(
                            entity_id, "clear_notification", tag=notification_id
                        )
                setattr(self, mobile_active_attr, False)
            if getattr(self, persistent_active_attr):
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": notification_id},
                    blocking=False,
                )
                setattr(self, persistent_active_attr, False)
            return

        template = self._effective(
            CONF_MSG_DEVICE_WINDOW_CONFLICT, DEFAULT_MSG_DEVICE_WINDOW_CONFLICT
        )
        try:
            message = template.format(raum=room, geraet=device_label)
        except (KeyError, ValueError, IndexError):
            _LOGGER.warning(
                "Benachrichtigungstext für Fenster-Gerät-Konflikt in Raum "
                "%s enthält einen ungültigen Platzhalter - wird unverändert "
                "gesendet: %s",
                room,
                template,
            )
            message = template

        if sonos_entities:
            tts_entity = self._effective(CONF_TTS_ENTITY, None)
            if (
                tts_entity
                and not self._is_tts_quiet_hours_active()
                and not self._is_tts_light_off()
            ):
                await self._play_tts(sonos_entities, tts_entity, message)

        if await self._push_to_targets(
            message,
            title=self._notification_title("Fenster schließen"),
            log_label=f"Fenster-Konflikt {device_label}",
            tag=notification_id,
        ):
            setattr(self, mobile_active_attr, True)

        if persistent_enabled:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "notification_id": notification_id,
                    "title": self._notification_title("Fenster schließen"),
                    "message": message,
                },
                blocking=False,
            )
            setattr(self, persistent_active_attr, True)


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

    @property
    def icon(self) -> str:
        return "mdi:shower" if self.is_on else "mdi:shower-head"

    async def async_added_to_hass(self) -> None:
        """Schreibt einmalig den aktuellen Zustand, sobald diese Entität
        vollständig hinzugefügt ist - unabhängig davon, ob der Haupt-Sensor
        (der ansonsten bei jeder Neubewertung mit aktualisiert, siehe
        attach_shower_sensor()) zu diesem Zeitpunkt bereits selbst
        hinzugefügt wurde (Reihenfolge nicht garantiert)."""
        await super().async_added_to_hass()
        self.async_write_ha_state()
