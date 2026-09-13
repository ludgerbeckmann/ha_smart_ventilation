"""Config- und Options-Flow für Smart Ventilation."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .const import (
    AC_DOMAINS,
    CONF_AC_ENTITY,
    CONF_DEHUMIDIFIER_ENTITY,
    CONF_FROST_PROTECTION_TEMP,
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_MAX_OPEN_DURATION_WINTER,
    CONF_MIN_SURPLUS_POWER,
    CONF_MOBILE_NOTIFY_ENTITY,
    CONF_MOBILE_TARGETS,
    CONF_NOTIFY_METHOD,
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
    CONF_WINDOW_ENTITY,
    CONF_WINTER_OUTDOOR_THRESHOLD,
    COMMON_TEMP_ATTRIBUTES,
    DEFAULT_FROST_PROTECTION_TEMP,
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
    DEFAULT_WINTER_OUTDOOR_THRESHOLD,
    DEHUMIDIFIER_DOMAINS,
    DOMAIN,
    NOTIFY_METHOD_MOBILE,
    NOTIFY_METHOD_SONOS,
    PRESENCE_DOMAINS,
    SHUTTER_DOMAINS,
    TEMP_SOURCE_DOMAINS,
)

SECTION_SENSORS = "sensors"
SECTION_DEVICES = "devices"
SECTION_PARAMETERS = "parameters"

# Schwellenwerte und weitere Parameter: Anzeige als Zahlenfeld mit
# Pfeil-hoch/-runter (Spinner), vorausgefüllt mit dem Standardwert. Wird das
# Feld komplett geleert, greift beim Speichern automatisch wieder der
# Standardwert (siehe _apply_threshold_defaults).
_THRESHOLD_FIELDS = {
    CONF_TEMP_THRESHOLD_OPEN: (DEFAULT_TEMP_THRESHOLD_OPEN, -20, 40, 0.5, "°C"),
    CONF_TEMP_THRESHOLD_CLOSE: (DEFAULT_TEMP_THRESHOLD_CLOSE, -20, 40, 0.5, "°C"),
    CONF_HUMIDITY_THRESHOLD_OPEN: (DEFAULT_HUMIDITY_THRESHOLD_OPEN, 0, 100, 1, "%"),
    CONF_HUMIDITY_THRESHOLD_CLOSE: (DEFAULT_HUMIDITY_THRESHOLD_CLOSE, 0, 100, 1, "%"),
    CONF_TEMP_MARGIN: (DEFAULT_TEMP_MARGIN, 0, 5, 0.5, "°C"),
    CONF_FROST_PROTECTION_TEMP: (DEFAULT_FROST_PROTECTION_TEMP, -20, 15, 0.5, "°C"),
    CONF_WINTER_OUTDOOR_THRESHOLD: (DEFAULT_WINTER_OUTDOOR_THRESHOLD, -10, 20, 0.5, "°C"),
    CONF_MAX_OPEN_DURATION_WINTER: (DEFAULT_MAX_OPEN_DURATION_WINTER, 5, 120, 5, "min"),
    CONF_REMINDER_INTERVAL: (DEFAULT_REMINDER_INTERVAL, 0, 180, 5, "min"),
    CONF_MIN_SURPLUS_POWER: (DEFAULT_MIN_SURPLUS_POWER, 0, 10000, 100, "W"),
    CONF_POWER_GRACE_PERIOD: (DEFAULT_POWER_GRACE_PERIOD, 0, 120, 5, "min"),
}


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
    """Baut Marker + NumberSelector (Box-Modus mit Pfeiltasten) für ein
    Schwellenwert-Feld. Nutzt 'suggested_value' statt 'default': der Wert ist
    vorausgefüllt und editierbar, kann aber auch komplett geleert werden -
    _apply_threshold_defaults() füllt ihn dann beim Speichern wieder auf."""
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


def _apply_threshold_defaults(data: dict) -> dict:
    """Füllt geleerte Schwellenwert-Felder mit ihrem Standardwert auf."""
    for key, (default_value, *_rest) in _THRESHOLD_FIELDS.items():
        if data.get(key) in (None, ""):
            data[key] = default_value
    return data


def _flatten_step_data(data: dict) -> dict:
    """Führt die verschachtelten Sections wieder zu einem flachen Dict
    zusammen. Sections sind nur eine visuelle Gruppierung im Formular -
    intern arbeiten wir weiterhin mit einem flachen dict."""
    section_keys = (SECTION_SENSORS, SECTION_DEVICES, SECTION_PARAMETERS)
    flat = {k: v for k, v in data.items() if k not in section_keys}
    for key in section_keys:
        flat.update(data.get(key) or {})
    return _apply_threshold_defaults(flat)


def _build_user_schema(defaults: dict | None = None) -> vol.Schema:
    """Hauptschritt: Raumname ganz am Anfang, danach die Benachrichtigungs-
    methode(n) und drei Abschnitte ('Sensoren', 'Parameter', 'Geräte' - der
    Geräte-Abschnitt steht zuletzt und ist standardmäßig eingeklappt, da er
    optional ist und nur für einen Teil der Räume relevant sein dürfte).

    `defaults` wird sowohl beim Neuanlegen (leer/teilweise befüllt nach
    einem Formularfehler) als auch beim nachträglichen Bearbeiten eines
    bestehenden Eintrags (vollständig mit den aktuellen Werten) genutzt.
    """
    defaults = defaults or {}

    temp_open_marker, temp_open_sel = _threshold_selector(CONF_TEMP_THRESHOLD_OPEN, defaults)
    temp_close_marker, temp_close_sel = _threshold_selector(CONF_TEMP_THRESHOLD_CLOSE, defaults)
    hum_open_marker, hum_open_sel = _threshold_selector(CONF_HUMIDITY_THRESHOLD_OPEN, defaults)
    hum_close_marker, hum_close_sel = _threshold_selector(CONF_HUMIDITY_THRESHOLD_CLOSE, defaults)
    margin_marker, margin_sel = _threshold_selector(CONF_TEMP_MARGIN, defaults)
    frost_marker, frost_sel = _threshold_selector(CONF_FROST_PROTECTION_TEMP, defaults)
    winter_marker, winter_sel = _threshold_selector(CONF_WINTER_OUTDOOR_THRESHOLD, defaults)
    duration_marker, duration_sel = _threshold_selector(CONF_MAX_OPEN_DURATION_WINTER, defaults)
    reminder_marker, reminder_sel = _threshold_selector(CONF_REMINDER_INTERVAL, defaults)
    power_marker, power_sel = _threshold_selector(CONF_MIN_SURPLUS_POWER, defaults)
    grace_marker, grace_sel = _threshold_selector(CONF_POWER_GRACE_PERIOD, defaults)

    return vol.Schema(
        {
            # Raumname ganz am Anfang des Formulars
            vol.Required(
                CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, "")
            ): str,
            vol.Required(
                CONF_NOTIFY_METHOD,
                default=defaults.get(CONF_NOTIFY_METHOD, [NOTIFY_METHOD_MOBILE]),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=NOTIFY_METHOD_SONOS,
                            label="Sprachausgabe (z. B. Sonos)",
                        ),
                        selector.SelectOptionDict(
                            value=NOTIFY_METHOD_MOBILE,
                            label="Home Assistant Companion App (Push)",
                        ),
                    ],
                    multiple=True,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required(SECTION_SENSORS): section(
                vol.Schema(
                    {
                        _entity_marker(
                            CONF_TEMP_SOURCE_ENTITY, defaults
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=TEMP_SOURCE_DOMAINS)
                        ),
                        # Immer sichtbar (nicht nur bei climate-Entitäten). Wird
                        # zur Laufzeit nur ausgewertet, wenn die gewählte
                        # Entität tatsächlich eine climate-Entität ist - bei
                        # anderen Entitäten wird der Wert ignoriert und
                        # stattdessen direkt der Entitätszustand verwendet.
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
                            selector.EntitySelectorConfig(domain="sensor")
                        ),
                        _entity_marker(
                            CONF_OUTDOOR_TEMP_ENTITY, defaults
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="sensor")
                        ),
                        _entity_marker(
                            CONF_WINDOW_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="binary_sensor")
                        ),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(SECTION_PARAMETERS): section(
                vol.Schema(
                    {
                        temp_open_marker: temp_open_sel,
                        temp_close_marker: temp_close_sel,
                        hum_open_marker: hum_open_sel,
                        hum_close_marker: hum_close_sel,
                        margin_marker: margin_sel,
                        frost_marker: frost_sel,
                        winter_marker: winter_sel,
                        duration_marker: duration_sel,
                        reminder_marker: reminder_sel,
                    }
                ),
                {"collapsed": False},
            ),
            # Ans Ende verschoben und standardmäßig eingeklappt, da optional
            # und nur für einen Teil der Räume relevant
            vol.Required(SECTION_DEVICES): section(
                vol.Schema(
                    {
                        _entity_marker(
                            CONF_DEHUMIDIFIER_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=DEHUMIDIFIER_DOMAINS)
                        ),
                        _entity_marker(
                            CONF_AC_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=AC_DOMAINS)
                        ),
                        _entity_marker(
                            CONF_SHUTTER_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain=SHUTTER_DOMAINS)
                        ),
                        _entity_marker(
                            CONF_POWER_ENTITY, defaults, required=False
                        ): selector.EntitySelector(
                            selector.EntitySelectorConfig(domain="sensor")
                        ),
                        power_marker: power_sel,
                        grace_marker: grace_sel,
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def _build_sonos_schema(defaults: dict | None = None) -> vol.Schema:
    return vol.Schema(
        {
            # Mehrfachauswahl: Ansage kann gleichzeitig auf mehreren
            # Lautsprechern erfolgen
            _entity_marker(CONF_SONOS_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", multiple=True)
            ),
            _entity_marker(CONF_TTS_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
        }
    )


def _build_mobile_schema(defaults: dict | None = None) -> vol.Schema:
    """App-Benachrichtigung: Liste von Notify-Ziel + optionaler Anwesenheits-
    Entität. Jedes Ziel kann individuell an eine Person/ein Gerät gekoppelt
    werden - die Push-Nachricht geht an ein Ziel nur, wenn die zugehörige
    Anwesenheits-Entität (falls gesetzt) 'home' meldet.
    """
    defaults = defaults or {}
    current_targets = defaults.get(CONF_MOBILE_TARGETS) or []

    return vol.Schema(
        {
            vol.Required(
                CONF_MOBILE_TARGETS, default=current_targets
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
        }
    )


class _NotifyFlowMixin:
    """Gemeinsame Schrittlogik für Config- und Options-Flow.

    Nach dem Hauptschritt werden - abhängig von der Auswahl bei
    CONF_NOTIFY_METHOD - nacheinander nur die passenden Folgeschritte
    gezeigt (Sprachausgabe und/oder App).
    """

    _data: dict
    _pending_notify_methods: list[str]

    async def async_step_notify_sonos(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if not (
                user_input.get(CONF_SONOS_ENTITY) and user_input.get(CONF_TTS_ENTITY)
            ):
                errors["base"] = "sonos_config_missing"
            else:
                self._data.update(user_input)
                return await self._async_step_next()

        return self.async_show_form(
            step_id="notify_sonos",
            data_schema=_build_sonos_schema(self._data),
            errors=errors,
        )

    async def async_step_notify_mobile(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            targets = user_input.get(CONF_MOBILE_TARGETS) or []
            valid_targets = [
                t for t in targets if t.get(CONF_MOBILE_NOTIFY_ENTITY)
            ]
            if not valid_targets:
                errors["base"] = "mobile_config_missing"
            else:
                self._data.update(user_input)
                self._data[CONF_MOBILE_TARGETS] = valid_targets
                return await self._async_step_next()

        return self.async_show_form(
            step_id="notify_mobile",
            data_schema=_build_mobile_schema(self._data),
            errors=errors,
        )

    async def _async_step_next(self) -> config_entries.FlowResult:
        """Arbeitet die noch offenen Benachrichtigungsschritte der Reihe nach ab."""
        if NOTIFY_METHOD_SONOS in self._pending_notify_methods:
            self._pending_notify_methods.remove(NOTIFY_METHOD_SONOS)
            return await self.async_step_notify_sonos()

        if NOTIFY_METHOD_MOBILE in self._pending_notify_methods:
            self._pending_notify_methods.remove(NOTIFY_METHOD_MOBILE)
            return await self.async_step_notify_mobile()

        return self._finish()

    def _finish(self) -> config_entries.FlowResult:
        raise NotImplementedError


class SmartVentilationConfigFlow(
    config_entries.ConfigFlow, _NotifyFlowMixin, domain=DOMAIN
):
    """Config Flow: pro Durchlauf wird ein neuer Raum eingerichtet.

    Ablauf:
      1. user            - Benachrichtigungsmethode(n), Raumname, Sensoren, Parameter
      2. notify_sonos     - nur falls "Sprachausgabe" ausgewählt wurde
      3. notify_mobile    - nur falls "App" ausgewählt wurde
      4. Eintrag wird angelegt
    """

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}
        self._pending_notify_methods: list[str] = []

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        defaults: dict | None = None

        if user_input is not None:
            defaults = _flatten_step_data(user_input)
            methods = defaults.get(CONF_NOTIFY_METHOD) or []

            if not methods:
                errors["base"] = "notify_method_required"
            else:
                unique_id = (
                    f"{defaults[CONF_ROOM_NAME]}_"
                    f"{defaults[CONF_TEMP_SOURCE_ENTITY]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                self._data = defaults
                self._pending_notify_methods = list(methods)
                return await self._async_step_next()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(defaults),
            errors=errors,
        )

    def _finish(self) -> config_entries.FlowResult:
        return self.async_create_entry(
            title=self._data[CONF_ROOM_NAME], data=self._data
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "SmartVentilationOptionsFlow":
        return SmartVentilationOptionsFlow()


class SmartVentilationOptionsFlow(config_entries.OptionsFlow, _NotifyFlowMixin):
    """Options-Flow: bearbeitet einen bereits bestehenden Raum-Eintrag.

    Nutzt denselben mehrstufigen Ablauf wie beim Neuanlegen, alle Felder
    werden dabei mit den aktuell gespeicherten Werten vorbelegt.
    """

    def __init__(self) -> None:
        self._data: dict = {}
        self._pending_notify_methods: list[str] = []

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        current = dict(self.config_entry.data)
        defaults = current

        if user_input is not None:
            defaults = _flatten_step_data(user_input)
            methods = defaults.get(CONF_NOTIFY_METHOD) or []

            if not methods:
                errors["base"] = "notify_method_required"
            else:
                # Bestehende Werte behalten, neue Eingaben überschreiben sie
                self._data = {**current, **defaults}
                self._pending_notify_methods = list(methods)
                return await self._async_step_next()

        return self.async_show_form(
            step_id="init",
            data_schema=_build_user_schema(defaults),
            errors=errors,
        )

    def _finish(self) -> config_entries.FlowResult:
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=self._data,
            title=self._data[CONF_ROOM_NAME],
        )
        # Options-Flows speichern selbst keine eigenen "options" - die
        # eigentliche Aktualisierung ist bereits über async_update_entry
        # oben erfolgt. Der registrierte update_listener sorgt für den
        # automatischen Reload der Integration mit den neuen Werten.
        return self.async_create_entry(title="", data={})
