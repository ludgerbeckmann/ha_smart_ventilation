"""Config- und Options-Flow für Smart Ventilation."""
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
    CONF_FROST_PROTECTION_TEMP,
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
    CONF_MSG_CLOSE_FROST_UNAVAILABLE,
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
    COMMON_TEMP_ATTRIBUTES,
    DEFAULT_CO2_THRESHOLD_CLOSE,
    DEFAULT_CO2_THRESHOLD_OPEN,
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
    DEFAULT_MSG_CLOSE_FROST_UNAVAILABLE,
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
    DEHUMIDIFIER_DOMAINS,
    DOMAIN,
    GLOBAL_SETTINGS_UNIQUE_ID,
    PRESENCE_DOMAINS,
    SHUTTER_DOMAINS,
    TEMP_SOURCE_DOMAINS,
    TTS_PLAYBACK_MODE_OVERLAY,
    TTS_PLAYBACK_MODE_PAUSE,
)

SECTION_NOTIFY = "notify"
SECTION_SENSORS = "sensors"
SECTION_DEVICES = "devices"
SECTION_PARAMETERS = "parameters"
SECTION_MESSAGES = "messages"

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
    CONF_HEAT_PROTECTION_TEMP: (DEFAULT_HEAT_PROTECTION_TEMP, 20, 45, 0.5, "°C"),
    CONF_WINTER_OUTDOOR_THRESHOLD: (DEFAULT_WINTER_OUTDOOR_THRESHOLD, -10, 20, 0.5, "°C"),
    CONF_MAX_OPEN_DURATION_WINTER: (DEFAULT_MAX_OPEN_DURATION_WINTER, 5, 120, 5, "min"),
    CONF_REMINDER_INTERVAL: (DEFAULT_REMINDER_INTERVAL, 0, 180, 5, "min"),
    CONF_MIN_SURPLUS_POWER: (DEFAULT_MIN_SURPLUS_POWER, 0, 10000, 100, "W"),
    CONF_POWER_GRACE_PERIOD: (DEFAULT_POWER_GRACE_PERIOD, 0, 120, 5, "min"),
    CONF_TTS_VOLUME: (DEFAULT_TTS_VOLUME, 0, 100, 5, "%"),
    CONF_SHOWER_RISE_THRESHOLD: (DEFAULT_SHOWER_RISE_THRESHOLD, 0.2, 10, 0.1, "%/min"),
}

# Die dreizehn "echten" Schwellenwert-/Lüftungs-Parameter - identisch mit
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
    CONF_HEAT_PROTECTION_TEMP,
    CONF_WINTER_OUTDOOR_THRESHOLD,
    CONF_MAX_OPEN_DURATION_WINTER,
    CONF_REMINDER_INTERVAL,
    CONF_SHOWER_RISE_THRESHOLD,
)


def _entity_marker(
    key: str, defaults: dict | None, required: bool = True
) -> vol.Marker:
    """Erzeugt vol.Required/vol.Optional - inkl. Vorbelegung mit dem aktuellen
    Wert, falls beim Bearbeiten eines bestehenden Eintrags einer vorliegt."""
    defaults = defaults or {}
    value = defaults.get(key)
    marker_cls = vol.Required if required else vol.Optional
    if value not in (None, "", []):
        return marker_cls(key, default=value)
    return marker_cls(key)


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
    CONF_MSG_CLOSE_FROST_UNAVAILABLE: DEFAULT_MSG_CLOSE_FROST_UNAVAILABLE,
    CONF_MSG_CLOSE_HEAT: DEFAULT_MSG_CLOSE_HEAT,
    CONF_MSG_CLOSE_DURATION: DEFAULT_MSG_CLOSE_DURATION,
    CONF_MSG_CLOSE_OUTDOOR_WARMER: DEFAULT_MSG_CLOSE_OUTDOOR_WARMER,
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
    for key, default_value in _MESSAGE_FIELD_DEFAULTS.items():
        if data.get(key) in (None, ""):
            data[key] = default_value
    return data


def _flatten_step_data(data: dict) -> dict:
    """Führt die verschachtelten Sections wieder zu einem flachen Dict
    zusammen. Sections sind nur eine visuelle Gruppierung im Formular -
    intern arbeiten wir weiterhin mit einem flachen dict."""
    section_keys = (SECTION_NOTIFY, SECTION_SENSORS, SECTION_DEVICES, SECTION_PARAMETERS, SECTION_MESSAGES)
    flat = {k: v for k, v in data.items() if k not in section_keys}
    for key in section_keys:
        flat.update(data.get(key) or {})

    # Tri-State-Dropdown liefert "true"/"false" als String - in echtes bool
    # umwandeln (fehlt der Schlüssel, bleibt er unberührt = "global nutzen")
    for tri_state_key in (
        CONF_HUMIDITY_PRIORITY_OVER_DURATION,
        CONF_MOBILE_ENABLED,
        CONF_PERSISTENT_ENABLED,
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
    area_entities: set[str] | None, domains: str | list[str]
) -> list[str] | None:
    """Schränkt einen EntitySelector auf die dem gewählten Bereich
    zugeordneten Entitäten der passenden Domain(s) ein - liefert None (=
    keine Einschränkung, alle Entitäten wie bisher wählbar), falls kein
    Bereich gewählt wurde oder der Bereich keine passende Entität enthält.
    Ohne diesen Fallback könnte ein Raum, dessen Sensoren (noch) keinem
    HA-Bereich zugeordnet sind, plötzlich gar keine Auswahl mehr anbieten."""
    if not area_entities:
        return None
    allowed_domains = (domains,) if isinstance(domains, str) else tuple(domains)
    filtered = [
        entity_id
        for entity_id in area_entities
        if entity_id.split(".", 1)[0] in allowed_domains
    ]
    return filtered or None


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
    """Formular für einen Raum: Raumname, danach vier Abschnitte
    ('Benachrichtigungsmethoden', 'Sensoren', 'Parameter', 'Geräte' -
    Parameter und Geräte standardmäßig eingeklappt, da optional).

    Im Abschnitt "Benachrichtigungsmethoden" aktiviert eine Checkbox die
    App-Benachrichtigung; das zugehörige Feld steht direkt darunter im
    selben Abschnitt (Home-Assistant-Formulare können Felder nicht
    abhängig von einer Checkbox ein-/ausblenden - es ist daher immer
    sichtbar, wird aber nur ausgewertet, wenn die Checkbox aktiviert ist).
    Sprachausgabe hat keine eigene Checkbox - sie ist aktiv, sobald
    mindestens ein Lautsprecher ausgewählt ist.

    Die Felder in 'Parameter' sowie Leistungsschwelle/-verzögerung im
    Geräte-Abschnitt sind echt optional: leer gelassen wird der Wert aus
    den allgemeinen Einstellungen übernommen (siehe Eintrag "Smart
    Ventilation Options").

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

    # App-Push und persistente Benachrichtigung sind überschreibbare
    # Raum-Einstellungen: leer gelassen gilt die globale Einstellung aus
    # "Smart Ventilation Optionen" (siehe _tri_state_bool_selector).
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

    sonos_include = _area_include_entities(area_entities, "media_player")

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
                                    selector.EntitySelectorConfig(domain="notify")
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
            }
        ),
        {"collapsed": False},
    )

    temp_source_include = _area_include_entities(area_entities, TEMP_SOURCE_DOMAINS)
    sensor_include = _area_include_entities(area_entities, "sensor")
    window_include = _area_include_entities(area_entities, "binary_sensor")

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
            }
        ),
        {"collapsed": False},
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
                heat_marker: heat_sel,
                winter_marker: winter_sel,
                duration_marker: duration_sel,
                priority_marker: priority_sel,
                reminder_marker: reminder_sel,
                shower_threshold_marker: shower_threshold_sel,
            }
        ),
        {"collapsed": True},
    )

    dehumidifier_include = _area_include_entities(area_entities, DEHUMIDIFIER_DOMAINS)
    ac_include = _area_include_entities(area_entities, AC_DOMAINS)
    shutter_include = _area_include_entities(area_entities, SHUTTER_DOMAINS)

    # Ans Ende verschoben und standardmäßig eingeklappt, da optional und nur
    # für einen Teil der Räume relevant
    fields[vol.Required(SECTION_DEVICES)] = section(
        vol.Schema(
            {
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
                    CONF_AC_ENTITY, defaults, required=False
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=AC_DOMAINS,
                        **({"include_entities": ac_include} if ac_include else {}),
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
                power_marker: power_sel,
                grace_marker: grace_sel,
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

    parameter_fields[
        vol.Required(
            CONF_HUMIDITY_PRIORITY_OVER_DURATION,
            default=defaults.get(
                CONF_HUMIDITY_PRIORITY_OVER_DURATION,
                DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION,
            ),
        )
    ] = selector.BooleanSelector()

    return vol.Schema(
        {
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
                                                domain="notify"
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
                {"collapsed": False},
            ),
            vol.Required(SECTION_PARAMETERS): section(
                vol.Schema(parameter_fields), {"collapsed": False}
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
                            CONF_MSG_CLOSE_FROST_UNAVAILABLE,
                            default=defaults.get(
                                CONF_MSG_CLOSE_FROST_UNAVAILABLE,
                                DEFAULT_MSG_CLOSE_FROST_UNAVAILABLE,
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
    globale Einstellung aus "Smart Ventilation Optionen" gilt) - fehlende
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
    Ventilation Options') werden NICHT über diesen nutzergesteuerten Flow
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
        )

    async def async_step_import(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Wird ausschließlich intern von __init__.py (async_setup) beim
        allerersten Start automatisch ausgelöst, um den Eintrag "Smart
        Ventilation Options" anzulegen - keine Benutzerinteraktion, keine
        eigene Formularanzeige."""
        await self.async_set_unique_id(GLOBAL_SETTINGS_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        data = _apply_threshold_defaults(
            {CONF_IS_GLOBAL: True, CONF_ROOM_NAME: "- Smart Ventilation Optionen -"}
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

        if user_input is not None:
            defaults = _flatten_step_data(user_input)
            error = _validate_room_submission(defaults)
            if error:
                errors["base"] = error
            else:
                # Bestehende Werte behalten, neue Eingaben überschreiben sie.
                # Ein Feld, das jetzt leer gelassen wurde, entfernt eine
                # zuvor gesetzte Raum-Override wieder (zurück auf "global").
                new_data = {**current, **defaults}
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                    title=new_data[CONF_ROOM_NAME],
                )
                return self.async_create_entry(title="", data={})

        # Die Filterung nutzt bewusst den GESPEICHERTEN Bereich (aus
        # config_entry.data), nicht einen hier gerade erst ausgewählten -
        # ein hier geänderter Bereich wirkt sich also erst beim nächsten
        # Öffnen dieses Formulars auf die Auswahllisten aus (siehe Hinweis
        # im Feld selbst). Ein einstufiges Formular wie bisher bleibt damit
        # für den häufigen Fall (nur einen Schwellenwert anpassen) ohne
        # zusätzlichen Zwischenschritt möglich.
        area_entities = _entities_for_area(
            self.hass, current.get(CONF_AREA_ID)
        )

        return self.async_show_form(
            step_id="room",
            data_schema=_build_room_schema(
                defaults, area_entities=area_entities, show_area_selector=True
            ),
            errors=errors,
        )

    async def async_step_global(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        current = dict(self.config_entry.data)

        if user_input is not None:
            flat = _apply_threshold_defaults(_flatten_step_data(user_input))
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
