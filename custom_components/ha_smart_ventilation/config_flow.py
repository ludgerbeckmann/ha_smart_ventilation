"""Config- und Options-Flow für Smart Climate."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .const import (
    AC_DOMAINS,
    CONF_AC_ENTITY,
    CONF_AREA_ID,
    CONF_CO2_ENTITY,
    CONF_CO2_THRESHOLD_CLOSE,
    CONF_CO2_THRESHOLD_OPEN,
    CONF_DEHUMIDIFIER_ENTITY,
    CONF_DEHUMIDIFIER_TANK_FULL_ENTITY,
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
    CONF_HEATING_SCHEDULE_ENABLED,
    CONF_HEATING_STANDBY_TEMP,
    CONF_HEATING_THRESHOLD_TEMP,
    CONF_HEATING_USE_TEMP_SOURCE,
    CONF_HEAT_PROTECTION_TEMP,
    CONF_NO_WINDOW,
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_PRIORITY_OVER_DURATION,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_IS_GLOBAL,
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
    CONF_TTS_PLAYBACK_MODE,
    CONF_TTS_VOLUME,
    CONF_WINDOW_ENTITY,
    CONF_WINTER_OUTDOOR_THRESHOLD,
    COMMON_TEMP_ATTRIBUTES,
    DEFAULT_CO2_THRESHOLD_CLOSE,
    DEFAULT_CO2_THRESHOLD_OPEN,
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
    DEFAULT_SUMMER_MODE_THRESHOLD_TEMP,
    DEFAULT_TEMP_ATTRIBUTE,
    DEFAULT_TEMP_MARGIN,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DEFAULT_TTS_PLAYBACK_MODE,
    DEFAULT_TTS_VOLUME,
    DEFAULT_WINTER_OUTDOOR_THRESHOLD,
    DEHUMIDIFIER_DOMAINS,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
    GLOBAL_ROOM_NAME,
    GLOBAL_SETTINGS_UNIQUE_ID,
    HEATING_DOMAINS,
    PRESENCE_DOMAINS,
    SHUTTER_DOMAINS,
    SUMMER_MODE_FORECAST_DOMAINS,
    TEMP_SOURCE_DOMAINS,
    TTS_PLAYBACK_MODE_OVERLAY,
    TTS_PLAYBACK_MODE_PAUSE,
)

SECTION_NOTIFY = "notify"
# Raum-Formular: EIN gemeinsamer Abschnitt für Sensoren UND optional
# gesteuerte Geräte (siehe _build_room_schema) - eine climate-Entität kann
# beide Rollen zugleich ausfüllen (Temperatur-Quelle und Heizung), getrennte
# Abschnitte hätten sie zweimal zur Auswahl gezwungen. In der globalen
# Formular (_build_global_edit_schema) bezeichnet dieselbe Konstante
# weiterhin nur den dortigen, unabhängigen "Sensoren"-Abschnitt.
SECTION_SENSORS = "sensors"
SECTION_PARAMETERS = "parameters"
SECTION_MESSAGES = "messages"

# Alle im Raum-Formular über _entity_marker(..., required=False) erzeugten
# EntitySelector-Felder (siehe _build_room_schema). Anders als Zahlen-/
# Text-Felder ohne festen Schema-default (_override_selector) übermittelt
# Home Assistants Formular ein geleertes EntitySelector-Feld nicht als
# leeren/None-Wert, sondern lässt den Schlüssel im gesendeten user_input
# komplett weg - der einfache {**current, **defaults}-Merge in
# async_step_room würde einen zuvor gesetzten Wert dadurch fälschlich
# unverändert beibehalten, selbst wenn der Nutzer das Feld sichtbar
# geleert hat. Für genau diese Felder wird der Merge deshalb gesondert
# behandelt (siehe async_step_room).
ROOM_OPTIONAL_ENTITY_KEYS = (
    CONF_SONOS_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_CO2_ENTITY,
    CONF_WINDOW_ENTITY,
    CONF_SHUTTER_ENTITY,
    CONF_DEHUMIDIFIER_ENTITY,
    CONF_DEHUMIDIFIER_TANK_FULL_ENTITY,
    CONF_AC_ENTITY,
    CONF_HEATING_ENTITY,
    CONF_HEATING_PRESENCE_ENTITIES,
)

# Reine Flow-interne Checkbox in den globalen Einstellungen (siehe
# async_step_global) - wird nie in den Config-Entry übernommen, sondern vor
# dem Speichern wieder herausgenommen. Kein CONF_*-Konstante in const.py,
# da es sich um keinen gespeicherten Wert handelt.
RESET_TO_DEFAULTS_KEY = "reset_to_defaults"

# Schwellenwerte und weitere Zahlen-Parameter mit Pfeil-hoch/-runter-Steuerung.
# Beim Bearbeiten der GLOBALEN Einstellungen immer mit Standardwert
# vorausgefüllt und beim Leeren automatisch wieder aufgefüllt (siehe
# _threshold_selector / _apply_threshold_defaults). Auf RAUM-Ebene dagegen
# echt optional (siehe _override_selector) - leer bedeutet "globalen Wert
# verwenden".
_THRESHOLD_FIELDS = {
    CONF_TEMP_THRESHOLD_OPEN: (DEFAULT_TEMP_THRESHOLD_OPEN, -20, 40, 0.5, "°C"),
    CONF_TEMP_THRESHOLD_CLOSE: (DEFAULT_TEMP_THRESHOLD_CLOSE, -20, 40, 0.5, "°C"),
    CONF_HUMIDITY_THRESHOLD_OPEN: (DEFAULT_HUMIDITY_THRESHOLD_OPEN, 0, 100, 1, "%"),
    CONF_HUMIDITY_THRESHOLD_CLOSE: (DEFAULT_HUMIDITY_THRESHOLD_CLOSE, 0, 100, 1, "%"),
    CONF_CO2_THRESHOLD_OPEN: (DEFAULT_CO2_THRESHOLD_OPEN, 400, 5000, 50, "ppm"),
    CONF_CO2_THRESHOLD_CLOSE: (DEFAULT_CO2_THRESHOLD_CLOSE, 400, 5000, 50, "ppm"),
    CONF_TEMP_MARGIN: (DEFAULT_TEMP_MARGIN, 0, 5, 0.5, "°C"),
    CONF_FROST_PROTECTION_TEMP: (DEFAULT_FROST_PROTECTION_TEMP, -20, 15, 0.5, "°C"),
    CONF_FROST_DEBOUNCE_MINUTES: (DEFAULT_FROST_DEBOUNCE_MINUTES, 0, 60, 1, "min"),
    CONF_HEAT_PROTECTION_TEMP: (DEFAULT_HEAT_PROTECTION_TEMP, 20, 45, 0.5, "°C"),
    CONF_WINTER_OUTDOOR_THRESHOLD: (DEFAULT_WINTER_OUTDOOR_THRESHOLD, -10, 20, 0.5, "°C"),
    CONF_MAX_OPEN_DURATION_WINTER: (DEFAULT_MAX_OPEN_DURATION_WINTER, 5, 120, 5, "min"),
    CONF_REMINDER_INTERVAL: (DEFAULT_REMINDER_INTERVAL, 0, 180, 5, "min"),
    CONF_MIN_SURPLUS_POWER: (DEFAULT_MIN_SURPLUS_POWER, 0, 10000, 100, "W"),
    CONF_POWER_GRACE_PERIOD: (DEFAULT_POWER_GRACE_PERIOD, 0, 120, 5, "min"),
    CONF_TTS_VOLUME: (DEFAULT_TTS_VOLUME, 0, 100, 5, "%"),
    CONF_SHOWER_RISE_THRESHOLD: (DEFAULT_SHOWER_RISE_THRESHOLD, 0.2, 10, 0.1, "%/min"),
    CONF_HEATING_THRESHOLD_TEMP: (DEFAULT_HEATING_THRESHOLD_TEMP, 10, 25, 0.5, "°C"),
    CONF_HEATING_COMFORT_TEMP: (DEFAULT_HEATING_COMFORT_TEMP, 10, 28, 0.5, "°C"),
    CONF_HEATING_STANDBY_TEMP: (DEFAULT_HEATING_STANDBY_TEMP, 5, 25, 0.5, "°C"),
    CONF_HEATING_NIGHT_TEMP: (DEFAULT_HEATING_NIGHT_TEMP, 5, 25, 0.5, "°C"),
    CONF_SUMMER_MODE_THRESHOLD_TEMP: (DEFAULT_SUMMER_MODE_THRESHOLD_TEMP, 5, 30, 0.5, "°C"),
}

# Zeitfelder für den optionalen Heizungs-Zeitplan (CONF_HEATING_SCHEDULE_
# ENABLED) - Werte als "HH:MM:SS"-String (selector.TimeSelector()-Format).
# Analoges Muster zu _THRESHOLD_FIELDS/_threshold_selector/_override_
# selector (siehe _time_selector/_time_override_selector unten), nur ohne
# min/max/step/unit, die ein TimeSelector nicht braucht.
_TIME_FIELDS = {
    CONF_HEATING_COMFORT_START_WEEKDAY: DEFAULT_HEATING_COMFORT_START_WEEKDAY,
    CONF_HEATING_COMFORT_END_WEEKDAY: DEFAULT_HEATING_COMFORT_END_WEEKDAY,
    CONF_HEATING_COMFORT_START_WEEKEND: DEFAULT_HEATING_COMFORT_START_WEEKEND,
    CONF_HEATING_COMFORT_END_WEEKEND: DEFAULT_HEATING_COMFORT_END_WEEKEND,
    CONF_HEATING_NIGHT_START_WEEKDAY: DEFAULT_HEATING_NIGHT_START_WEEKDAY,
    CONF_HEATING_NIGHT_END_WEEKDAY: DEFAULT_HEATING_NIGHT_END_WEEKDAY,
    CONF_HEATING_NIGHT_START_WEEKEND: DEFAULT_HEATING_NIGHT_START_WEEKEND,
    CONF_HEATING_NIGHT_END_WEEKEND: DEFAULT_HEATING_NIGHT_END_WEEKEND,
}

# Die achtzehn "echten" Schwellenwert-/Lüftungs-Parameter - identisch mit
# dem Inhalt des Raum-Abschnitts "Parameter". min_surplus_power/
# power_grace_period gehören beim Raum bewusst zum Geräte-Abschnitt, nicht
# hierher.
_CORE_PARAMETER_KEYS = (
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_CO2_THRESHOLD_OPEN,
    CONF_CO2_THRESHOLD_CLOSE,
    CONF_TEMP_MARGIN,
    CONF_FROST_PROTECTION_TEMP,
    CONF_FROST_DEBOUNCE_MINUTES,
    CONF_HEAT_PROTECTION_TEMP,
    CONF_WINTER_OUTDOOR_THRESHOLD,
    CONF_MAX_OPEN_DURATION_WINTER,
    CONF_REMINDER_INTERVAL,
    CONF_SHOWER_RISE_THRESHOLD,
    CONF_HEATING_THRESHOLD_TEMP,
    CONF_HEATING_COMFORT_TEMP,
    CONF_HEATING_STANDBY_TEMP,
    CONF_HEATING_NIGHT_TEMP,
    CONF_SUMMER_MODE_THRESHOLD_TEMP,
)


def _entity_marker(
    key: str, defaults: dict | None, required: bool = True
) -> vol.Marker:
    """Erzeugt vol.Required/vol.Optional - inkl. Vorbelegung mit dem aktuellen
    Wert, falls beim Bearbeiten eines bestehenden Eintrags einer vorliegt.

    Für optionale Felder wird die Vorbelegung bewusst NICHT über ein echtes
    `default=` gesetzt, sondern wie bei _override_selector() über
    `description={"suggested_value": ...}` - ein `vol.Optional(key,
    default=value)` verankert `value` als festen Schema-Fallback, auf den
    Home Assistants Formular ein sichtbar geleertes Feld beim erneuten
    Anzeigen/Speichern immer wieder zurückfallen lässt. Das Feld ließ sich
    dadurch in der Praxis nie wirklich leeren, unabhängig davon, wie der
    Merge in async_step_room() mit dem übermittelten user_input umgeht
    (siehe ROOM_OPTIONAL_ENTITY_KEYS) - der Fehler saß schon in der
    Formular-Definition selbst, bevor überhaupt etwas übermittelt wird."""
    defaults = defaults or {}
    value = defaults.get(key)
    marker_cls = vol.Required if required else vol.Optional
    if value in (None, "", []):
        return marker_cls(key)
    if required:
        return marker_cls(key, default=value)
    return marker_cls(key, description={"suggested_value": value})


def _threshold_selector(key: str, defaults: dict | None) -> tuple[vol.Marker, object]:
    """Immer vorausgefüllt (mit aktuellem Wert oder Standardwert) - für die
    globalen Einstellungen, wo beim Leeren automatisch wieder der
    Standardwert greift (siehe _apply_threshold_defaults)."""
    defaults = defaults or {}
    default_value, min_v, max_v, step, unit = _THRESHOLD_FIELDS[key]
    current = defaults.get(key, default_value)
    marker = vol.Optional(key, description={"suggested_value": current})
    field_selector = selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            min=min_v,
            max=max_v,
            step=step,
            unit_of_measurement=unit,
        )
    )
    return marker, field_selector


def _override_selector(key: str, defaults: dict | None) -> tuple[vol.Marker, object]:
    """Für RAUM-Einstellungen: echt optional, kein erzwungener Standardwert.
    Leer = die globale Einstellung (bzw. deren Standardwert) gilt."""
    defaults = defaults or {}
    _default_value, min_v, max_v, step, unit = _THRESHOLD_FIELDS[key]
    current = defaults.get(key)
    kwargs = {}
    if current not in (None, ""):
        kwargs["description"] = {"suggested_value": current}
    marker = vol.Optional(key, **kwargs)
    field_selector = selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            min=min_v,
            max=max_v,
            step=step,
            unit_of_measurement=unit,
        )
    )
    return marker, field_selector


def _time_selector(key: str, defaults: dict | None) -> tuple[vol.Marker, object]:
    """Immer vorausgefüllt (mit aktuellem Wert oder Standardwert) - für die
    globalen Einstellungen, analog zu _threshold_selector()."""
    defaults = defaults or {}
    current = defaults.get(key) or _TIME_FIELDS[key]
    marker = vol.Optional(key, description={"suggested_value": current})
    return marker, selector.TimeSelector()


def _time_override_selector(key: str, defaults: dict | None) -> tuple[vol.Marker, object]:
    """Für RAUM-Einstellungen: echt optional, kein erzwungener Standardwert -
    analog zu _override_selector(). Leer = die globale Einstellung (bzw.
    deren Standardwert) gilt.

    Nutzt bewusst KEIN default= (Lektion 28) - der einfache
    {**current, **defaults}-Merge in async_step_room geht davon aus, dass
    ein geleertes TimeSelector-Feld (wie Zahlen-/Text-Felder, nicht wie
    EntitySelector - siehe ROOM_OPTIONAL_ENTITY_KEYS) als leerer Wert
    übermittelt wird, nicht als fehlender Schlüssel. Sollte sich das als
    falsch herausstellen (bislang nicht mit einer echten Home-Assistant-
    Instanz verifiziert), braucht es dieselbe Sonderbehandlung wie
    ROOM_OPTIONAL_ENTITY_KEYS."""
    defaults = defaults or {}
    current = defaults.get(key)
    kwargs = {}
    if current:
        kwargs["description"] = {"suggested_value": current}
    marker = vol.Optional(key, **kwargs)
    return marker, selector.TimeSelector()


def _global_config(hass) -> dict:
    """Liefert die Daten der globalen Einstellungen (falls vorhanden) - via
    hass.data, genau wie binary_sensor.py:_global_config()/diagnostics.py
    (hier gibt es keine Entität, die self._config hätte)."""
    domain_data = hass.data.get(DOMAIN, {})
    global_entry_id = domain_data.get(GLOBAL_ENTRY_ID_KEY)
    if not global_entry_id:
        return {}
    return domain_data.get(global_entry_id) or {}


def _room_override_placeholders(hass) -> dict[str, str]:
    """description_placeholders fürs Raum-Formular: für jedes per
    _override_selector() bzw. _tri_state_bool_selector() überschreibbare
    Feld der aktuell wirksame globale Wert (globale Einstellung, sonst
    deren Standardwert) als Text - zeigt im Formular per data_description
    an, worauf sich ein leer gelassenes Feld gerade bezieht, ohne das Feld
    selbst vorzubelegen (das würde beim Speichern einen Override
    einfrieren, siehe _override_selector)."""
    global_data = _global_config(hass)
    placeholders = {}
    for key, (default_value, _min, _max, _step, unit) in _THRESHOLD_FIELDS.items():
        value = global_data.get(key)
        if value in (None, ""):
            value = default_value
        placeholders[f"global_{key}"] = f"{value} {unit}".strip()
    for key, default_value in _TIME_FIELDS.items():
        value = global_data.get(key) or default_value
        placeholders[f"global_{key}"] = value[:5]
    for key, default_value in (
        (CONF_MOBILE_ENABLED, False),
        (CONF_PERSISTENT_ENABLED, False),
        (CONF_HUMIDITY_PRIORITY_OVER_DURATION, DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION),
        (CONF_HEATING_SCHEDULE_ENABLED, False),
    ):
        value = global_data.get(key)
        if value is None:
            value = default_value
        placeholders[f"global_{key}"] = "Ja" if value else "Nein"
    targets = global_data.get(CONF_MOBILE_TARGETS) or []
    target_entities = [
        t.get(CONF_MOBILE_NOTIFY_ENTITY) for t in targets if t.get(CONF_MOBILE_NOTIFY_ENTITY)
    ]
    placeholders[f"global_{CONF_MOBILE_TARGETS}"] = (
        ", ".join(target_entities) if target_entities else "keine"
    )
    return placeholders


def _tri_state_bool_selector(
    key: str, defaults: dict | None, yes_label: str, no_label: str
) -> tuple[vol.Marker, object]:
    """Für RAUM-Einstellungen: echte Ja/Nein/Leer-Auswahl (Dropdown) für
    einen booleschen Override. Leer = die globale Einstellung gilt - anders
    als ein normaler Ein/Aus-Schalter kann ein Dropdown auch 'nichts
    ausgewählt' darstellen."""
    defaults = defaults or {}
    current = defaults.get(key)
    kwargs = {}
    if current is not None:
        kwargs["default"] = "true" if current else "false"
    marker = vol.Optional(key, **kwargs)
    field_selector = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value="true", label=yes_label),
                selector.SelectOptionDict(value="false", label=no_label),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )
    return marker, field_selector


_MESSAGE_FIELD_DEFAULTS = {
    CONF_MSG_OPEN_HUMIDITY: DEFAULT_MSG_OPEN_HUMIDITY,
    CONF_MSG_OPEN_CO2: DEFAULT_MSG_OPEN_CO2,
    CONF_MSG_OPEN_TEMP: DEFAULT_MSG_OPEN_TEMP,
    CONF_MSG_CLOSE_DEFAULT: DEFAULT_MSG_CLOSE_DEFAULT,
    CONF_MSG_CLOSE_HUMIDITY: DEFAULT_MSG_CLOSE_HUMIDITY,
    CONF_MSG_CLOSE_CO2: DEFAULT_MSG_CLOSE_CO2,
    CONF_MSG_CLOSE_FROST: DEFAULT_MSG_CLOSE_FROST,
    CONF_MSG_CLOSE_HEAT: DEFAULT_MSG_CLOSE_HEAT,
    CONF_MSG_CLOSE_DURATION: DEFAULT_MSG_CLOSE_DURATION,
    CONF_MSG_CLOSE_OUTDOOR_WARMER: DEFAULT_MSG_CLOSE_OUTDOOR_WARMER,
    CONF_MSG_CLOSE_OUTDOOR_WETTER: DEFAULT_MSG_CLOSE_OUTDOOR_WETTER,
    CONF_MSG_REMINDER: DEFAULT_MSG_REMINDER,
}


def _apply_threshold_defaults(data: dict) -> dict:
    """Füllt geleerte Schwellenwert- und Benachrichtigungstext-Felder mit
    ihrem Standardwert auf. Wird ausschließlich für die globalen
    Einstellungen verwendet - auf Raumebene bleiben leere Felder bewusst
    leer (= 'globalen Wert nutzen')."""
    for key, (default_value, *_rest) in _THRESHOLD_FIELDS.items():
        if data.get(key) in (None, ""):
            data[key] = default_value
    for key, default_value in _TIME_FIELDS.items():
        if data.get(key) in (None, ""):
            data[key] = default_value
    for key, default_value in _MESSAGE_FIELD_DEFAULTS.items():
        if data.get(key) in (None, ""):
            data[key] = default_value
    return data


def _flatten_step_data(data: dict) -> dict:
    """Führt die verschachtelten Sections wieder zu einem flachen Dict
    zusammen. Sections sind nur eine visuelle Gruppierung im Formular -
    intern arbeiten wir weiterhin mit einem flachen dict."""
    section_keys = (SECTION_NOTIFY, SECTION_SENSORS, SECTION_PARAMETERS, SECTION_MESSAGES)
    flat = {k: v for k, v in data.items() if k not in section_keys}
    for key in section_keys:
        flat.update(data.get(key) or {})

    # Tri-State-Dropdown liefert "true"/"false" als String - in echtes bool
    # umwandeln (fehlt der Schlüssel, bleibt er unberührt = "global nutzen")
    for tri_state_key in (
        CONF_HUMIDITY_PRIORITY_OVER_DURATION,
        CONF_MOBILE_ENABLED,
        CONF_PERSISTENT_ENABLED,
        CONF_HEATING_SCHEDULE_ENABLED,
    ):
        value = flat.get(tri_state_key)
        if value in ("true", "false"):
            flat[tri_state_key] = value == "true"

    return flat


def _entities_for_area(hass, area_id: str | None) -> set[str] | None:
    """Liefert alle Entity-IDs, die (direkt oder über ihr Gerät) dem
    angegebenen HA-Bereich zugeordnet sind - None, falls kein Bereich
    übergeben wurde. Eine leere Menge (Bereich existiert, aber ohne
    zugeordnete Entitäten) wird bewusst von None unterschieden, hat aber am
    Aufrufer (_area_include_entities) dieselbe Wirkung: keine Einschränkung."""
    if not area_id:
        return None
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    entity_ids: set[str] = set()
    for entity in entity_registry.entities.values():
        entity_area_id = entity.area_id
        if entity_area_id is None and entity.device_id:
            device = device_registry.async_get(entity.device_id)
            entity_area_id = device.area_id if device else None
        if entity_area_id == area_id:
            entity_ids.add(entity.entity_id)
    return entity_ids


def _area_include_entities(
    area_entities: set[str] | None,
    domains: str | list[str],
    current_values: str | list[str] | None = None,
) -> list[str] | None:
    """Schränkt einen EntitySelector auf die dem gewählten Bereich
    zugeordneten Entitäten der passenden Domain(s) ein - liefert None (=
    keine Einschränkung, alle Entitäten wie bisher wählbar), falls kein
    Bereich gewählt wurde oder der Bereich keine passende Entität enthält.
    Ohne diesen Fallback könnte ein Raum, dessen Sensoren (noch) keinem
    HA-Bereich zugeordnet sind, plötzlich gar keine Auswahl mehr anbieten.

    `current_values` (der/die aktuell für dieses Feld gespeicherte(n)
    Wert(e)) wird der erlaubten Liste immer zusätzlich hinzugefügt, auch
    falls die Entität (mehr) nicht dem Bereich zugeordnet ist - z. B. weil
    sie nachträglich in Home Assistant einem anderen Bereich zugewiesen
    wurde, oder der Raum-Bereich selbst geändert wurde. Ohne das würde
    schon das bloße erneute Anzeigen des Formulars mit einem
    "value must be one of [...]"-Validierungsfehler fehlschlagen, da der
    per `_entity_marker()` vorbelegte Wert nicht mehr in der Auswahlliste
    steckt - unabhängig davon, ob der Nutzer dieses Feld überhaupt ändern
    wollte. Der Raum bliebe dadurch dauerhaft unspeicherbar, bis der Wert
    von Hand (z. B. über die YAML-Konfiguration) entfernt wird."""
    extra = (
        [current_values]
        if isinstance(current_values, str)
        else list(current_values or [])
    )
    extra = [e for e in extra if e]
    if area_entities is None:
        # Kein Bereich gewählt - keine Einschränkung, unabhängig von extra.
        return None
    allowed_domains = (domains,) if isinstance(domains, str) else tuple(domains)
    filtered = [
        entity_id
        for entity_id in area_entities
        if entity_id.split(".", 1)[0] in allowed_domains
    ]
    combined = list(dict.fromkeys(filtered + extra))
    return combined or None


def _build_area_schema() -> vol.Schema:
    """Erster Schritt beim Anlegen eines neuen Raums: HA-Bereich wählen
    (optional). Dient ausschließlich dazu, im zweiten Schritt (Formular aus
    _build_room_schema) den Raumnamen vorzubelegen und die Sensor-/
    Geräte-Auswahllisten auf die dem Bereich zugeordneten Entitäten
    einzuschränken."""
    return vol.Schema({vol.Optional(CONF_AREA_ID): selector.AreaSelector()})


def _build_room_schema(
    defaults: dict | None = None,
    area_entities: set[str] | None = None,
    show_area_selector: bool = False,
) -> vol.Schema:
    """Formular für einen Raum: Raumname, danach drei Abschnitte in dieser
    Reihenfolge - 'Sensoren & Geräte', 'Benachrichtigungen & Anwesenheit',
    'Parameter' (alle standardmäßig eingeklappt). 'Sensoren & Geräte' fasst
    die Mess-Entitäten UND die optional automatisch gesteuerten Geräte
    (Luftentfeuchter/Klimaanlage/Heizung) in einem Abschnitt zusammen -
    beide Themen überschneiden sich (z. B. eine climate-Entität kann sowohl
    Temperatur-Quelle als auch Heizungs-Gerät sein, siehe
    CONF_HEATING_USE_TEMP_SOURCE), getrennte Abschnitte hätten sonst eine
    Entität ggf. an zwei Stellen zur Auswahl gezwungen. Bewusst VOR
    'Benachrichtigungen & Anwesenheit' platziert (nicht mehr wie früher als
    erster Abschnitt), da diese für die Heizungs-Anwesenheitsprüfung auf
    Konzepte aus 'Sensoren & Geräte' aufbaut.

    Im Abschnitt "Benachrichtigungen & Anwesenheit" (früher
    "Benachrichtigungsmethoden" - umbenannt, da jetzt auch die
    Anwesenheits-Entitäten für die Heizungs-Pausierung hier stehen, siehe
    CONF_HEATING_PRESENCE_ENTITIES) aktiviert eine Checkbox die App-
    Benachrichtigung; das zugehörige Feld steht direkt darunter im selben
    Abschnitt (Home-Assistant-Formulare können Felder nicht abhängig von
    einer Checkbox ein-/ausblenden - es ist daher immer sichtbar, wird aber
    nur ausgewertet, wenn die Checkbox aktiviert ist). Sprachausgabe hat
    keine eigene Checkbox - sie ist aktiv, sobald mindestens ein
    Lautsprecher ausgewählt ist.

    Die Felder in 'Parameter' sowie Leistungsschwelle/-verzögerung im
    Geräte-Abschnitt sind echt optional: leer gelassen wird der Wert aus
    den allgemeinen Einstellungen übernommen (siehe Eintrag "Smart
    Climate Optionen").

    `defaults` wird sowohl beim Neuanlegen (leer/teilweise befüllt nach
    einem Formularfehler) als auch beim nachträglichen Bearbeiten eines
    bestehenden Eintrags (vollständig mit den aktuellen Werten) genutzt.

    `area_entities` (falls angegeben) schränkt die Sensor-/Geräte-
    Auswahllisten auf die einem HA-Bereich zugeordneten Entitäten ein
    (siehe _entities_for_area/_area_include_entities) - Domains ohne
    passende Entität im Bereich bleiben unbeschränkt.

    `show_area_selector` zeigt zusätzlich ein Feld zur (Neu-)Auswahl des
    HA-Bereichs an - beim Neuanlegen (Options-Flow: async_step_room) NICHT
    nötig, da der Bereich dort bereits in einem eigenen ersten Schritt
    gewählt wurde; beim Bearbeiten (Options-Flow) dagegen schon, da es dort
    keinen eigenen ersten Schritt gibt.
    """
    defaults = defaults or {}
    area_marker, area_sel = None, None
    if show_area_selector:
        current_area = defaults.get(CONF_AREA_ID)
        area_marker = (
            vol.Optional(CONF_AREA_ID, default=current_area)
            if current_area
            else vol.Optional(CONF_AREA_ID)
        )
        area_sel = selector.AreaSelector()

    temp_open_marker, temp_open_sel = _override_selector(CONF_TEMP_THRESHOLD_OPEN, defaults)
    temp_close_marker, temp_close_sel = _override_selector(CONF_TEMP_THRESHOLD_CLOSE, defaults)
    hum_open_marker, hum_open_sel = _override_selector(CONF_HUMIDITY_THRESHOLD_OPEN, defaults)
    hum_close_marker, hum_close_sel = _override_selector(CONF_HUMIDITY_THRESHOLD_CLOSE, defaults)
    co2_open_marker, co2_open_sel = _override_selector(CONF_CO2_THRESHOLD_OPEN, defaults)
    co2_close_marker, co2_close_sel = _override_selector(CONF_CO2_THRESHOLD_CLOSE, defaults)
    margin_marker, margin_sel = _override_selector(CONF_TEMP_MARGIN, defaults)
    frost_marker, frost_sel = _override_selector(CONF_FROST_PROTECTION_TEMP, defaults)
    frost_debounce_marker, frost_debounce_sel = _override_selector(
        CONF_FROST_DEBOUNCE_MINUTES, defaults
    )
    heat_marker, heat_sel = _override_selector(CONF_HEAT_PROTECTION_TEMP, defaults)
    winter_marker, winter_sel = _override_selector(CONF_WINTER_OUTDOOR_THRESHOLD, defaults)
    duration_marker, duration_sel = _override_selector(CONF_MAX_OPEN_DURATION_WINTER, defaults)
    reminder_marker, reminder_sel = _override_selector(CONF_REMINDER_INTERVAL, defaults)
    power_marker, power_sel = _override_selector(CONF_MIN_SURPLUS_POWER, defaults)
    grace_marker, grace_sel = _override_selector(CONF_POWER_GRACE_PERIOD, defaults)
    priority_marker, priority_sel = _tri_state_bool_selector(
        CONF_HUMIDITY_PRIORITY_OVER_DURATION,
        defaults,
        yes_label="Ja – Luftfeuchtigkeit/CO2 haben Vorrang",
        no_label="Nein – Winter-Höchstdauer hat Vorrang",
    )
    shower_threshold_marker, shower_threshold_sel = _override_selector(
        CONF_SHOWER_RISE_THRESHOLD, defaults
    )
    tts_volume_marker, tts_volume_sel = _override_selector(CONF_TTS_VOLUME, defaults)
    heating_threshold_marker, heating_threshold_sel = _override_selector(
        CONF_HEATING_THRESHOLD_TEMP, defaults
    )
    heating_comfort_marker, heating_comfort_sel = _override_selector(
        CONF_HEATING_COMFORT_TEMP, defaults
    )
    heating_standby_marker, heating_standby_sel = _override_selector(
        CONF_HEATING_STANDBY_TEMP, defaults
    )
    heating_night_marker, heating_night_sel = _override_selector(
        CONF_HEATING_NIGHT_TEMP, defaults
    )
    heating_schedule_marker, heating_schedule_sel = _tri_state_bool_selector(
        CONF_HEATING_SCHEDULE_ENABLED,
        defaults,
        yes_label="Ja – Zeitfenster erzwingen den Sollwert",
        no_label="Nein – reine Schwellenwert-Logik",
    )
    time_field_markers = {
        key: _time_override_selector(key, defaults) for key in _TIME_FIELDS
    }

    # App-Push und persistente Benachrichtigung sind überschreibbare
    # Raum-Einstellungen: leer gelassen gilt die globale Einstellung aus
    # "Smart Climate Optionen" (siehe _tri_state_bool_selector).
    # Sprachausgabe hat keinen eigenen Schalter mehr - sie ist aktiv, sobald
    # unten mindestens ein Lautsprecher ausgewählt ist.
    mobile_marker, mobile_sel = _tri_state_bool_selector(
        CONF_MOBILE_ENABLED, defaults, yes_label="Ja", no_label="Nein"
    )
    persistent_marker, persistent_sel = _tri_state_bool_selector(
        CONF_PERSISTENT_ENABLED, defaults, yes_label="Ja", no_label="Nein"
    )

    fields: dict = {}
    if show_area_selector:
        fields[area_marker] = area_sel
    fields[vol.Required(CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, ""))] = str

    temp_source_include = _area_include_entities(
        area_entities, TEMP_SOURCE_DOMAINS, defaults.get(CONF_TEMP_SOURCE_ENTITY)
    )
    sensor_include = _area_include_entities(
        area_entities,
        "sensor",
        [defaults.get(CONF_HUMIDITY_ENTITY), defaults.get(CONF_CO2_ENTITY)],
    )
    window_include = _area_include_entities(
        area_entities,
        "binary_sensor",
        [
            defaults.get(CONF_WINDOW_ENTITY),
            defaults.get(CONF_DEHUMIDIFIER_TANK_FULL_ENTITY),
        ],
    )
    shutter_include = _area_include_entities(
        area_entities, SHUTTER_DOMAINS, defaults.get(CONF_SHUTTER_ENTITY)
    )
    dehumidifier_include = _area_include_entities(
        area_entities, DEHUMIDIFIER_DOMAINS, defaults.get(CONF_DEHUMIDIFIER_ENTITY)
    )
    ac_include = _area_include_entities(
        area_entities, AC_DOMAINS, defaults.get(CONF_AC_ENTITY)
    )
    heating_include = _area_include_entities(
        area_entities, HEATING_DOMAINS, defaults.get(CONF_HEATING_ENTITY)
    )

    # "Sensoren & Geräte" - ein gemeinsamer Abschnitt für Mess-Entitäten UND
    # optional automatisch gesteuerte Geräte (siehe Docstring oben): eine
    # climate-Entität kann beide Rollen gleichzeitig ausfüllen (Temperatur-
    # Quelle UND Heizung, siehe CONF_HEATING_USE_TEMP_SOURCE direkt beim
    # Heizungs-Feld unten), getrennte Abschnitte hätten sie zweimal zur
    # Auswahl gezwungen.
    fields[vol.Required(SECTION_SENSORS)] = section(
        vol.Schema(
            {
                _entity_marker(
                    CONF_TEMP_SOURCE_ENTITY, defaults
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=TEMP_SOURCE_DOMAINS,
                        **(
                            {"include_entities": temp_source_include}
                            if temp_source_include
                            else {}
                        ),
                    )
                ),
                vol.Optional(
                    CONF_TEMP_ATTRIBUTE,
                    default=defaults.get(
                        CONF_TEMP_ATTRIBUTE, DEFAULT_TEMP_ATTRIBUTE
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=COMMON_TEMP_ATTRIBUTES,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                _entity_marker(
                    CONF_HUMIDITY_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        **({"include_entities": sensor_include} if sensor_include else {}),
                    )
                ),
                vol.Optional(
                    CONF_SHOWER_DETECTION_ENABLED,
                    default=defaults.get(
                        CONF_SHOWER_DETECTION_ENABLED, DEFAULT_SHOWER_DETECTION_ENABLED
                    ),
                ): selector.BooleanSelector(),
                _entity_marker(
                    CONF_CO2_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        **({"include_entities": sensor_include} if sensor_include else {}),
                    )
                ),
                vol.Optional(
                    CONF_NO_WINDOW, default=defaults.get(CONF_NO_WINDOW, False)
                ): selector.BooleanSelector(),
                _entity_marker(
                    CONF_WINDOW_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="binary_sensor",
                        **({"include_entities": window_include} if window_include else {}),
                    )
                ),
                _entity_marker(
                    CONF_SHUTTER_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=SHUTTER_DOMAINS,
                        **(
                            {"include_entities": shutter_include}
                            if shutter_include
                            else {}
                        ),
                    )
                ),
                vol.Optional(
                    CONF_DISABLE_CLOSE_RECOMMENDATION,
                    default=defaults.get(CONF_DISABLE_CLOSE_RECOMMENDATION, False),
                ): selector.BooleanSelector(),
                _entity_marker(
                    CONF_DEHUMIDIFIER_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=DEHUMIDIFIER_DOMAINS,
                        **(
                            {"include_entities": dehumidifier_include}
                            if dehumidifier_include
                            else {}
                        ),
                    )
                ),
                _entity_marker(
                    CONF_DEHUMIDIFIER_TANK_FULL_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="binary_sensor",
                        **({"include_entities": window_include} if window_include else {}),
                    )
                ),
                _entity_marker(
                    CONF_AC_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=AC_DOMAINS,
                        **({"include_entities": ac_include} if ac_include else {}),
                    )
                ),
                vol.Optional(
                    CONF_HEATING_USE_TEMP_SOURCE,
                    default=defaults.get(CONF_HEATING_USE_TEMP_SOURCE, False),
                ): selector.BooleanSelector(),
                _entity_marker(
                    CONF_HEATING_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=HEATING_DOMAINS,
                        **(
                            {"include_entities": heating_include}
                            if heating_include
                            else {}
                        ),
                    )
                ),
                power_marker: power_sel,
                grace_marker: grace_sel,
            }
        ),
        {"collapsed": True},
    )

    sonos_include = _area_include_entities(
        area_entities, "media_player", defaults.get(CONF_SONOS_ENTITY)
    )

    # "Benachrichtigungen & Anwesenheit" - bewusst NACH "Sensoren & Geräte"
    # platziert (siehe Docstring oben): die Anwesenheits-Entitäten für die
    # Heizungs-Pausierung gehören inhaltlich zu den Benachrichtigungsmethoden
    # (beide drehen sich um Personen/Geräte-Tracker), nicht zu den
    # Mess-/Steuer-Entitäten oben. CONF_HEATING_PRESENCE_ENTITIES bewusst
    # OHNE Bereichs-Filterung (wie CONF_PRESENCE_ENTITY im Objekt-Selector
    # unten) - eine Person/ihr Tracking-Gerät ist ortsungebunden und so gut
    # wie nie einem HA-Bereich zugeordnet (siehe Lektion 9).
    fields[vol.Required(SECTION_NOTIFY)] = section(
        vol.Schema(
            {
                _entity_marker(
                    CONF_SONOS_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player",
                        multiple=True,
                        **({"include_entities": sonos_include} if sonos_include else {}),
                    )
                ),
                tts_volume_marker: tts_volume_sel,
                mobile_marker: mobile_sel,
                vol.Optional(
                    CONF_MOBILE_TARGETS, default=defaults.get(CONF_MOBILE_TARGETS) or []
                ): selector.ObjectSelector(
                    selector.ObjectSelectorConfig(
                        multiple=True,
                        label_field=CONF_MOBILE_NOTIFY_ENTITY,
                        description_field=CONF_PRESENCE_ENTITY,
                        fields={
                            CONF_MOBILE_NOTIFY_ENTITY: {
                                "label": "Notify-Entität",
                                "required": True,
                                "selector": selector.EntitySelector(
                                    selector.EntitySelectorConfig(
                                        domain="notify", integration="mobile_app"
                                    )
                                ),
                            },
                            CONF_PRESENCE_ENTITY: {
                                "label": "Anwesenheits-Entität (optional)",
                                "required": False,
                                "selector": selector.EntitySelector(
                                    selector.EntitySelectorConfig(
                                        domain=PRESENCE_DOMAINS
                                    )
                                ),
                            },
                        },
                    )
                ),
                persistent_marker: persistent_sel,
                _entity_marker(
                    CONF_HEATING_PRESENCE_ENTITIES, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=PRESENCE_DOMAINS,
                        multiple=True,
                    )
                ),
            }
        ),
        {"collapsed": True},
    )

    fields[vol.Required(SECTION_PARAMETERS)] = section(
        vol.Schema(
            {
                temp_open_marker: temp_open_sel,
                temp_close_marker: temp_close_sel,
                hum_open_marker: hum_open_sel,
                hum_close_marker: hum_close_sel,
                co2_open_marker: co2_open_sel,
                co2_close_marker: co2_close_sel,
                margin_marker: margin_sel,
                frost_marker: frost_sel,
                frost_debounce_marker: frost_debounce_sel,
                heat_marker: heat_sel,
                winter_marker: winter_sel,
                duration_marker: duration_sel,
                priority_marker: priority_sel,
                reminder_marker: reminder_sel,
                shower_threshold_marker: shower_threshold_sel,
                heating_threshold_marker: heating_threshold_sel,
                heating_comfort_marker: heating_comfort_sel,
                heating_standby_marker: heating_standby_sel,
                heating_night_marker: heating_night_sel,
                heating_schedule_marker: heating_schedule_sel,
                **{
                    marker: sel
                    for marker, sel in time_field_markers.values()
                },
            }
        ),
        {"collapsed": True},
    )

    return vol.Schema(fields)


def _build_global_edit_schema(defaults: dict | None = None) -> vol.Schema:
    """Formular zum nachträglichen Bearbeiten der allgemeinen Einstellungen
    (Options-Flow): Sensoren/TTS-Wiedergabe/Leistungssensor in einem
    Abschnitt, die Schwellenwertparameter in einem eigenen - analog zum
    "Parameter"-Abschnitt bei den Raum-Einstellungen. Der Name/Titel dieses
    Eintrags ist hier bewusst nicht änderbar (nicht notwendig)."""
    defaults = defaults or {}
    volume_marker, volume_sel = _threshold_selector(CONF_TTS_VOLUME, defaults)
    power_marker, power_sel = _threshold_selector(CONF_MIN_SURPLUS_POWER, defaults)
    grace_marker, grace_sel = _threshold_selector(CONF_POWER_GRACE_PERIOD, defaults)

    parameter_fields = {}
    for key in _CORE_PARAMETER_KEYS:
        marker, sel = _threshold_selector(key, defaults)
        parameter_fields[marker] = sel
    for key in _TIME_FIELDS:
        marker, sel = _time_selector(key, defaults)
        parameter_fields[marker] = sel

    parameter_fields[
        vol.Required(
            CONF_HUMIDITY_PRIORITY_OVER_DURATION,
            default=defaults.get(
                CONF_HUMIDITY_PRIORITY_OVER_DURATION,
                DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION,
            ),
        )
    ] = selector.BooleanSelector()
    parameter_fields[
        vol.Required(
            CONF_HEATING_SCHEDULE_ENABLED,
            default=defaults.get(CONF_HEATING_SCHEDULE_ENABLED, False),
        )
    ] = selector.BooleanSelector()

    return vol.Schema(
        {
            vol.Required(
                RESET_TO_DEFAULTS_KEY, default=False
            ): selector.BooleanSelector(),
            vol.Required(SECTION_SENSORS): section(
                vol.Schema(
                    {
                        _entity_marker(
                            CONF_OUTDOOR_TEMP_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="sensor")
                        ),
                        _entity_marker(
                            CONF_OUTDOOR_HUMIDITY_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="sensor")
                        ),
                        _entity_marker(
                            CONF_SUMMER_MODE_FORECAST_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=SUMMER_MODE_FORECAST_DOMAINS
                            )
                        ),
                        _entity_marker(
                            CONF_SUMMER_MODE_FORECAST_ATTRIBUTE, defaults, required=False
                        ): selector.TextSelector(),
                        _entity_marker(
                            CONF_SUMMER_MODE_SWITCH_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="switch")
                        ),
                        _entity_marker(
                            CONF_TTS_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="tts")
                        ),
                        volume_marker: volume_sel,
                        vol.Required(
                            CONF_TTS_PLAYBACK_MODE,
                            default=defaults.get(
                                CONF_TTS_PLAYBACK_MODE, DEFAULT_TTS_PLAYBACK_MODE
                            ),
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[
                                    selector.SelectOptionDict(
                                        value=TTS_PLAYBACK_MODE_OVERLAY,
                                        label="Vorhandene Wiedergabe überlagern",
                                    ),
                                    selector.SelectOptionDict(
                                        value=TTS_PLAYBACK_MODE_PAUSE,
                                        label="Vorhandene Wiedergabe pausieren",
                                    ),
                                ],
                                mode=selector.SelectSelectorMode.LIST,
                            )
                        ),
                        _entity_marker(
                            CONF_POWER_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="sensor")
                        ),
                        power_marker: power_sel,
                        grace_marker: grace_sel,
                        vol.Required(
                            CONF_MOBILE_ENABLED,
                            default=defaults.get(CONF_MOBILE_ENABLED, False),
                        ): selector.BooleanSelector(),
                        vol.Optional(
                            CONF_MOBILE_TARGETS,
                            default=defaults.get(CONF_MOBILE_TARGETS) or [],
                        ): selector.ObjectSelector(
                            selector.ObjectSelectorConfig(
                                multiple=True,
                                label_field=CONF_MOBILE_NOTIFY_ENTITY,
                                description_field=CONF_PRESENCE_ENTITY,
                                fields={
                                    CONF_MOBILE_NOTIFY_ENTITY: {
                                        "label": "Notify-Entität",
                                        "required": True,
                                        "selector": selector.EntitySelector(
                                            selector.EntitySelectorConfig(
                                                domain="notify",
                                                integration="mobile_app",
                                            )
                                        ),
                                    },
                                    CONF_PRESENCE_ENTITY: {
                                        "label": "Anwesenheits-Entität (optional)",
                                        "required": False,
                                        "selector": selector.EntitySelector(
                                            selector.EntitySelectorConfig(
                                                domain=PRESENCE_DOMAINS
                                            )
                                        ),
                                    },
                                },
                            )
                        ),
                        vol.Required(
                            CONF_PERSISTENT_ENABLED,
                            default=defaults.get(CONF_PERSISTENT_ENABLED, False),
                        ): selector.BooleanSelector(),
                    }
                ),
                {"collapsed": True},
            ),
            vol.Required(SECTION_PARAMETERS): section(
                vol.Schema(parameter_fields), {"collapsed": True}
            ),
            vol.Required(SECTION_MESSAGES): section(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_MSG_OPEN_HUMIDITY,
                            default=defaults.get(
                                CONF_MSG_OPEN_HUMIDITY, DEFAULT_MSG_OPEN_HUMIDITY
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(
                                multiline=True, type=selector.TextSelectorType.TEXT
                            )
                        ),
                        vol.Required(
                            CONF_MSG_OPEN_CO2,
                            default=defaults.get(
                                CONF_MSG_OPEN_CO2, DEFAULT_MSG_OPEN_CO2
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_OPEN_TEMP,
                            default=defaults.get(
                                CONF_MSG_OPEN_TEMP, DEFAULT_MSG_OPEN_TEMP
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_DEFAULT,
                            default=defaults.get(
                                CONF_MSG_CLOSE_DEFAULT, DEFAULT_MSG_CLOSE_DEFAULT
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_HUMIDITY,
                            default=defaults.get(
                                CONF_MSG_CLOSE_HUMIDITY, DEFAULT_MSG_CLOSE_HUMIDITY
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_CO2,
                            default=defaults.get(
                                CONF_MSG_CLOSE_CO2, DEFAULT_MSG_CLOSE_CO2
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_FROST,
                            default=defaults.get(
                                CONF_MSG_CLOSE_FROST, DEFAULT_MSG_CLOSE_FROST
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_HEAT,
                            default=defaults.get(
                                CONF_MSG_CLOSE_HEAT, DEFAULT_MSG_CLOSE_HEAT
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_DURATION,
                            default=defaults.get(
                                CONF_MSG_CLOSE_DURATION, DEFAULT_MSG_CLOSE_DURATION
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_OUTDOOR_WARMER,
                            default=defaults.get(
                                CONF_MSG_CLOSE_OUTDOOR_WARMER,
                                DEFAULT_MSG_CLOSE_OUTDOOR_WARMER,
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_CLOSE_OUTDOOR_WETTER,
                            default=defaults.get(
                                CONF_MSG_CLOSE_OUTDOOR_WETTER,
                                DEFAULT_MSG_CLOSE_OUTDOOR_WETTER,
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                        vol.Required(
                            CONF_MSG_REMINDER,
                            default=defaults.get(
                                CONF_MSG_REMINDER, DEFAULT_MSG_REMINDER
                            ),
                        ): selector.TextSelector(
                            selector.TextSelectorConfig(multiline=True)
                        ),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def _validate_room_submission(defaults: dict) -> str | None:
    """Bereinigt die Benachrichtigungs-Zieleinträge. Gibt keinen Fehler mehr
    zurück, da jede der drei Methoden jetzt leer gelassen werden kann (=
    globale Einstellung aus "Smart Climate Optionen" gilt) - fehlende
    Ziel-Entitäten führen zur Laufzeit nur zu einem Log-Hinweis, nicht zu
    einem blockierenden Formularfehler. Innentemperatur wird bereits vom
    Formular selbst als Pflichtfeld erzwungen."""
    targets = defaults.get(CONF_MOBILE_TARGETS)
    if targets:
        defaults[CONF_MOBILE_TARGETS] = [
            t for t in targets if t.get(CONF_MOBILE_NOTIFY_ENTITY)
        ]
    return None


class SmartVentilationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow für Räume. Die allgemeinen Einstellungen ('Smart
    Climate Optionen') werden NICHT über diesen nutzergesteuerten Flow
    angelegt, sondern automatisch beim allerersten Start von Home Assistant
    (siehe __init__.py: async_setup) über async_step_import."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Erster Schritt: optional einen HA-Bereich wählen. Dient nur dazu,
        im zweiten Schritt (async_step_room) den Raumnamen vorzubelegen und
        die Sensor-/Geräte-Auswahllisten auf den Bereich einzuschränken -
        wird deshalb hier selbst noch nicht in den Config-Entry
        übernommen. Kein eigenes __init__ nötig - das Attribut wird hier
        beim ersten (einzigen) Aufruf dieses Schritts gesetzt, bevor
        async_step_room es liest."""
        if user_input is not None:
            self._area_id = user_input.get(CONF_AREA_ID) or None
            return await self.async_step_room()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_area_schema(),
        )

    async def async_step_room(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        defaults: dict = {}
        area_id = getattr(self, "_area_id", None)

        if user_input is not None:
            defaults = _flatten_step_data(user_input)
            error = _validate_room_submission(defaults)

            if error:
                errors["base"] = error
            else:
                defaults[CONF_AREA_ID] = area_id
                unique_id = (
                    f"{defaults[CONF_ROOM_NAME]}_"
                    f"{defaults[CONF_TEMP_SOURCE_ENTITY]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=defaults[CONF_ROOM_NAME], data=defaults
                )
        elif area_id:
            area = ar.async_get(self.hass).async_get_area(area_id)
            if area is not None:
                defaults[CONF_ROOM_NAME] = area.name

        area_entities = _entities_for_area(self.hass, area_id)

        return self.async_show_form(
            step_id="room",
            data_schema=_build_room_schema(defaults, area_entities=area_entities),
            errors=errors,
            description_placeholders=_room_override_placeholders(self.hass),
        )

    async def async_step_import(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Wird ausschließlich intern von __init__.py (async_setup) beim
        allerersten Start automatisch ausgelöst, um den Eintrag "Smart
        Climate Optionen" anzulegen - keine Benutzerinteraktion, keine
        eigene Formularanzeige."""
        await self.async_set_unique_id(GLOBAL_SETTINGS_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        data = _apply_threshold_defaults(
            {CONF_IS_GLOBAL: True, CONF_ROOM_NAME: GLOBAL_ROOM_NAME}
        )
        return self.async_create_entry(title=data[CONF_ROOM_NAME], data=data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "SmartVentilationOptionsFlow":
        return SmartVentilationOptionsFlow()


class SmartVentilationOptionsFlow(config_entries.OptionsFlow):
    """Options-Flow: bearbeitet einen bestehenden Eintrag - je nachdem, ob es
    sich um einen Raum oder um die allgemeinen Einstellungen handelt, wird
    ein anderes Formular gezeigt. Der Typ selbst (Raum vs. allgemeine
    Einstellungen) lässt sich nachträglich nicht mehr ändern."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        if self.config_entry.data.get(CONF_IS_GLOBAL):
            return await self.async_step_global(user_input)
        return await self.async_step_room(user_input)

    async def async_step_room(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        current = dict(self.config_entry.data)
        defaults = current

        # Bereich, mit dem die aktuell angezeigten Auswahllisten gefiltert
        # wurden/werden - zu Beginn der gespeicherte, nach einer
        # Bereichs-Änderung (siehe unten) der zuletzt vom Nutzer gewählte.
        if not hasattr(self, "_room_filter_area_id"):
            self._room_filter_area_id = current.get(CONF_AREA_ID)

        if user_input is not None:
            defaults = _flatten_step_data(user_input)
            submitted_area_id = defaults.get(CONF_AREA_ID) or None

            if submitted_area_id != self._room_filter_area_id:
                # Der Bereich wurde gerade erst geändert: noch nicht
                # speichern, sondern zunächst nur die Auswahllisten mit dem
                # neuen Bereich neu berechnen und das Formular mit den
                # bereits gemachten übrigen Eingaben erneut anzeigen - ohne
                # das würden Sensor-/Geräte-Listen trotz Änderung weiterhin
                # auf den alten Bereich eingeschränkt bleiben (siehe
                # CLAUDE.md, Lektion 20).
                self._room_filter_area_id = submitted_area_id
            else:
                error = _validate_room_submission(defaults)
                if error:
                    errors["base"] = error
                else:
                    # Bestehende Werte behalten, neue Eingaben überschreiben sie.
                    # Ein Feld, das jetzt leer gelassen wurde, entfernt eine
                    # zuvor gesetzte Raum-Override wieder (zurück auf "global").
                    new_data = {**current, **defaults}
                    # EntitySelector-Felder werden beim Leeren nicht mit
                    # übermittelt, sondern fehlen komplett in defaults (anders
                    # als Zahlen-/Text-Felder) - der obige Merge würde einen
                    # zuvor gesetzten Wert sonst fälschlich beibehalten, siehe
                    # ROOM_OPTIONAL_ENTITY_KEYS.
                    for key in ROOM_OPTIONAL_ENTITY_KEYS:
                        if not defaults.get(key):
                            new_data.pop(key, None)
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data=new_data,
                        title=new_data[CONF_ROOM_NAME],
                    )
                    return self.async_create_entry(title="", data={})

        area_entities = _entities_for_area(self.hass, self._room_filter_area_id)

        return self.async_show_form(
            step_id="room",
            data_schema=_build_room_schema(
                defaults, area_entities=area_entities, show_area_selector=True
            ),
            errors=errors,
            description_placeholders=_room_override_placeholders(self.hass),
        )

    async def async_step_global(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        current = dict(self.config_entry.data)

        if user_input is not None:
            flat = _flatten_step_data(user_input)
            if flat.pop(RESET_TO_DEFAULTS_KEY, False):
                # Ignoriert, was aktuell in den Schwellenwert-/Text-Feldern
                # steht, und lässt _apply_threshold_defaults sie unten wie
                # bei geleerten Feldern mit dem einprogrammierten Standard
                # auffüllen. Ausgewählte Entitäten, Sprachausgabe-Modus und
                # Benachrichtigungsmethoden bleiben bewusst unberührt - das
                # sind funktionale Einstellungen, keine Kalibrierungswerte.
                for key in _THRESHOLD_FIELDS:
                    flat[key] = None
                for key in _MESSAGE_FIELD_DEFAULTS:
                    flat[key] = None
            flat = _apply_threshold_defaults(flat)
            flat[CONF_IS_GLOBAL] = True
            # Name/Titel bleibt unverändert - im Formular nicht editierbar
            flat[CONF_ROOM_NAME] = current.get(
                CONF_ROOM_NAME, self.config_entry.title
            )
            if flat.get(CONF_MOBILE_TARGETS):
                flat[CONF_MOBILE_TARGETS] = [
                    t
                    for t in flat[CONF_MOBILE_TARGETS]
                    if t.get(CONF_MOBILE_NOTIFY_ENTITY)
                ]
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=flat,
                title=self.config_entry.title,
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="global",
            data_schema=_build_global_edit_schema(current),
        )
