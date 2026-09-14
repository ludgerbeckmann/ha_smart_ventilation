"""Binary Sensor Plattform: 'Lüften empfohlen' pro Raum."""
from __future__ import annotations

import logging
import math
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
    CONF_DEHUMIDIFIER_ENTITY,
    CONF_FROST_PROTECTION_TEMP,
    CONF_NO_WINDOW,
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_PRIORITY_OVER_DURATION,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_MAX_OPEN_DURATION_WINTER,
    CONF_MIN_SURPLUS_POWER,
    CONF_MOBILE_NOTIFY_ENTITY,
    CONF_MOBILE_TARGETS,
    CONF_NOTIFY_METHOD,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_POWER_ENTITY,
    CONF_POWER_GRACE_PERIOD,
    CONF_PRESENCE_ENTITY,
    CONF_REMINDER_INTERVAL,
    CONF_ROOM_NAME,
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
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION,
    DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
    DEFAULT_HUMIDITY_THRESHOLD_OPEN,
    DEFAULT_MAX_OPEN_DURATION_WINTER,
    DEFAULT_MIN_SURPLUS_POWER,
    DEFAULT_POWER_GRACE_PERIOD,
    DEFAULT_REMINDER_INTERVAL,
    DEFAULT_TEMP_ATTRIBUTE,
    DEFAULT_TEMP_MARGIN,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DEFAULT_TTS_PLAYBACK_MODE,
    DEFAULT_TTS_VOLUME,
    DEFAULT_WINTER_OUTDOOR_THRESHOLD,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
    NOTIFY_METHOD_MOBILE,
    NOTIFY_METHOD_PERSISTENT,
    NOTIFY_METHOD_SONOS,
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
    - Frostschutz: unterhalb einer Außentemperatur wird nie geöffnet, ein
      bereits offener Zustand wird sofort geschlossen
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

    @property
    def extra_state_attributes(self) -> dict:
        indoor_temp = self._get_indoor_temperature()
        humidity = self._get_float_state(self._config.get(CONF_HUMIDITY_ENTITY))
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
        if outdoor_humidity is not None:
            attrs["aussen_luftfeuchtigkeit"] = outdoor_humidity
        if self._config.get(CONF_TEMP_ATTRIBUTE):
            attrs["temperatur_attribut"] = self._config[CONF_TEMP_ATTRIBUTE]
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
            if "letzter_grund" in attrs:
                self._last_reason = attrs["letzter_grund"]
            if "luftentfeuchter_an" in attrs:
                self._dehumidifier_state = bool(attrs["luftentfeuchter_an"])
            if "klimaanlage_an" in attrs:
                self._ac_state = bool(attrs["klimaanlage_an"])

        tracked = [self._config[CONF_TEMP_SOURCE_ENTITY]]
        for key in (CONF_HUMIDITY_ENTITY, CONF_WINDOW_ENTITY, CONF_POWER_ENTITY):
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
        outdoor_entity = self._effective(CONF_OUTDOOR_TEMP_ENTITY, None)
        outdoor_temp = self._get_float_state(outdoor_entity)
        outdoor_humidity_entity = self._effective(CONF_OUTDOOR_HUMIDITY_ENTITY, None)
        outdoor_humidity = self._get_float_state(outdoor_humidity_entity)

        temp_open = self._effective(CONF_TEMP_THRESHOLD_OPEN, DEFAULT_TEMP_THRESHOLD_OPEN)
        temp_close = self._effective(CONF_TEMP_THRESHOLD_CLOSE, DEFAULT_TEMP_THRESHOLD_CLOSE)
        hum_open = self._effective(CONF_HUMIDITY_THRESHOLD_OPEN, DEFAULT_HUMIDITY_THRESHOLD_OPEN)
        hum_close = self._effective(CONF_HUMIDITY_THRESHOLD_CLOSE, DEFAULT_HUMIDITY_THRESHOLD_CLOSE)
        margin = self._effective(CONF_TEMP_MARGIN, DEFAULT_TEMP_MARGIN)
        frost_temp = self._effective(CONF_FROST_PROTECTION_TEMP, DEFAULT_FROST_PROTECTION_TEMP)
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
        temp_needs_open = indoor_temp is not None and indoor_temp >= temp_open
        temp_needs_close = indoor_temp is not None and indoor_temp <= temp_close

        # --- Frostschutz: harte Grenze ---
        frost_block = outdoor_temp is not None and outdoor_temp <= frost_temp

        # --- Öffnen: drinnen zu warm UND draußen spürbar kühler ---
        outdoor_cooler_enough = outdoor_temp is None or (
            indoor_temp is not None and outdoor_temp <= indoor_temp - margin
        )
        # --- Öffnen wegen Feuchtigkeit nur, wenn es draußen auch trockener
        # ist als drinnen - sonst würde Lüften die Situation verschlimmern.
        # Vergleich über ABSOLUTE Luftfeuchtigkeit (g/m³), nicht über die
        # relative: kalte Luft mit hoher RH% ist absolut oft trotzdem sehr
        # trocken (typischer Winter-Lüften-Effekt) - ein reiner RH%-Vergleich
        # würde in diesem, praktisch sehr häufigen Fall fälschlich vom
        # Lüften abraten. Ohne Außen-Luftfeuchtigkeitssensor (oder fehlenden
        # Temperaturwerten) wird das wie bisher nicht geprüft und einfach
        # angenommen, dass Lüften hilft.
        outdoor_drier_enough = True
        if (
            outdoor_humidity is not None
            and humidity is not None
            and indoor_temp is not None
            and outdoor_temp is not None
        ):
            indoor_abs_humidity = self._absolute_humidity(indoor_temp, humidity)
            outdoor_abs_humidity = self._absolute_humidity(outdoor_temp, outdoor_humidity)
            outdoor_drier_enough = outdoor_abs_humidity < indoor_abs_humidity
        open_by_temp = temp_needs_open and outdoor_cooler_enough
        open_by_humidity = humidity_needs_open and outdoor_drier_enough

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

        should_open = (open_by_temp or open_by_humidity) and not frost_block

        # --- Schließen: Sommer-Fall (draußen wieder spürbar wärmer) ---
        outdoor_warmer_again = (
            outdoor_temp is not None
            and indoor_temp is not None
            and outdoor_temp >= indoor_temp + margin
        )
        close_by_summer_outdoor = (
            self._attr_is_on and outdoor_warmer_again and not open_by_humidity
        )

        # --- Schließen: Winter-Höchstdauer ---
        # Ob dabei ein noch bestehender Feuchtigkeits-Lüftungsbedarf Vorrang
        # hat (Standard) oder die Höchstdauer strikt durchgesetzt wird, ist
        # konfigurierbar (Raum-Override möglich, sonst globale Einstellung).
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
            and not (humidity_priority and open_by_humidity)
        )

        # --- Schließen: Frostschutz erzwingt sofortiges Schließen ---
        close_by_frost = self._attr_is_on and frost_block

        # Reine Temperatur-Schließbedingung nicht anwenden, solange die
        # Luftfeuchtigkeit noch Lüftungsbedarf anzeigt - sonst würde direkt
        # im Anschluss wieder eine "bitte öffnen"-Empfehlung wegen der
        # Feuchtigkeit folgen (Schließen-dann-sofort-wieder-Öffnen-Flackern).
        close_by_temp = temp_needs_close and not open_by_humidity

        should_close = (
            close_by_temp
            or humidity_needs_close
            or close_by_summer_outdoor
            or close_by_duration
            or close_by_frost
        )

        new_state = self._attr_is_on
        reason = None

        if should_open and not self._attr_is_on:
            new_state = True
            reason = "humidity" if open_by_humidity and not open_by_temp else "temp"
        elif should_close and self._attr_is_on:
            new_state = False
            if close_by_frost:
                reason = "frost"
            elif close_by_duration:
                reason = "duration"
            elif humidity_needs_close:
                reason = "humidity"
            elif close_by_temp:
                reason = "temp"
            elif close_by_summer_outdoor:
                reason = "outdoor_warmer"

        if new_state != self._attr_is_on:
            self._attr_is_on = new_state
            self._last_reason = reason
            if new_state:
                self._open_since = dt_util.utcnow()
            else:
                self._open_since = None
            self.async_write_ha_state()
            if self._window_action_needed(new_state):
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

    def _build_message(self, should_ventilate: bool, reason: str | None) -> str:
        room = self._config[CONF_ROOM_NAME]

        if should_ventilate:
            if reason == "humidity":
                return (
                    f"Bitte das Fenster im {room} öffnen - die Luftfeuchtigkeit "
                    "ist zu hoch."
                )
            return (
                f"Bitte das Fenster im {room} zum Lüften öffnen - drinnen ist "
                "es wärmer als draußen."
            )

        if reason == "frost":
            return f"Bitte das Fenster im {room} wegen Frostgefahr wieder schließen."
        if reason == "duration":
            return (
                f"Das Fenster im {room} ist schon eine Weile offen - bitte wegen "
                "der Kälte draußen wieder schließen."
            )
        if reason == "humidity":
            return (
                f"Die Luftfeuchtigkeit im {room} ist wieder im normalen Bereich - "
                "Fenster kann geschlossen werden."
            )
        if reason == "outdoor_warmer":
            return (
                f"Draußen ist es jetzt wärmer als im {room} - bitte Fenster "
                "wieder schließen."
            )
        if reason == "reminder":
            return f"Erinnerung: Das Fenster im {room} sollte noch geöffnet sein."
        return f"Bitte das Fenster im {room} wieder schließen."

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
        """Liefert die Liste der {mobile_notify_entity, presence_entity}-Paare.

        Abwärtskompatibel: ältere Konfigurationen, die noch die frühere
        flache Mehrfachauswahl (CONF_MOBILE_NOTIFY_ENTITY als Liste/String)
        gespeichert haben, werden automatisch in die neue Struktur überführt
        - ohne Anwesenheitsprüfung, also wie bisher immer gesendet.
        """
        targets = self._config.get(CONF_MOBILE_TARGETS)
        if targets:
            return list(targets)
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

        Alle Methoden können gleichzeitig konfiguriert sein, und jede
        Methode (außer der Web-Benachrichtigung) kann mehrere Ziel-
        Entitäten haben (mehrere Lautsprecher bzw. mehrere
        notify.*-Entitäten) - in dem Fall werden alle bedient.
        """
        room = self._config[CONF_ROOM_NAME]
        message = self._build_message(should_ventilate, reason)
        methods = self._config.get(CONF_NOTIFY_METHOD) or []

        if NOTIFY_METHOD_SONOS in methods:
            sonos_entities = self._as_list(self._config.get(CONF_SONOS_ENTITY))
            tts_entity = self._effective(CONF_TTS_ENTITY, None)
            if sonos_entities and tts_entity:
                await self._play_tts(sonos_entities, tts_entity, message)
            else:
                _LOGGER.warning(
                    "Sprachausgabe konfiguriert, aber Lautsprecher- oder "
                    "TTS-Entity fehlt (%s)",
                    room,
                )

        if NOTIFY_METHOD_MOBILE in methods:
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

        if NOTIFY_METHOD_PERSISTENT in methods:
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
