"""Config- und Options-Flow für Smart Ventilation."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    COMMON_TEMP_ATTRIBUTES,
    DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
    DEFAULT_HUMIDITY_THRESHOLD_OPEN,
    DEFAULT_TEMP_ATTRIBUTE,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DOMAIN,
    NOTIFY_METHOD_MOBILE,
    NOTIFY_METHOD_SONOS,
    TEMP_SOURCE_DOMAINS,
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


def _build_user_schema(defaults: dict | None = None) -> vol.Schema:
    """Hauptschritt: Raum, Temperaturquelle, Schwellenwerte, Benachrichtigungs-
    methode(n). Die konkreten Zugangsdaten für Sonos/App folgen in eigenen
    Schritten - je nachdem, was hier ausgewählt wird.

    `defaults` wird sowohl beim Neuanlegen (leer/teilweise befüllt nach
    einem Formularfehler) als auch beim nachträglichen Bearbeiten eines
    bestehenden Eintrags (vollständig mit den aktuellen Werten) genutzt.
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, "")
            ): str,
            _entity_marker(CONF_TEMP_SOURCE_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=TEMP_SOURCE_DOMAINS)
            ),
            # Immer sichtbar (nicht nur bei climate-Entitäten). Wird zur
            # Laufzeit nur ausgewertet, wenn die gewählte Entität tatsächlich
            # eine climate-Entität mit passendem Attribut ist - bei anderen
            # Entitäten (sensor, number, input_number) wird der Wert ignoriert
            # und stattdessen direkt der Entitätszustand verwendet.
            vol.Optional(
                CONF_TEMP_ATTRIBUTE,
                default=defaults.get(CONF_TEMP_ATTRIBUTE, DEFAULT_TEMP_ATTRIBUTE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COMMON_TEMP_ATTRIBUTES,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            _entity_marker(
                CONF_HUMIDITY_ENTITY, defaults, required=False
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            _entity_marker(CONF_OUTDOOR_TEMP_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _entity_marker(
                CONF_WINDOW_ENTITY, defaults, required=False
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(
                CONF_TEMP_THRESHOLD_OPEN,
                default=defaults.get(
                    CONF_TEMP_THRESHOLD_OPEN, DEFAULT_TEMP_THRESHOLD_OPEN
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_TEMP_THRESHOLD_CLOSE,
                default=defaults.get(
                    CONF_TEMP_THRESHOLD_CLOSE, DEFAULT_TEMP_THRESHOLD_CLOSE
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_HUMIDITY_THRESHOLD_OPEN,
                default=defaults.get(
                    CONF_HUMIDITY_THRESHOLD_OPEN, DEFAULT_HUMIDITY_THRESHOLD_OPEN
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_HUMIDITY_THRESHOLD_CLOSE,
                default=defaults.get(
                    CONF_HUMIDITY_THRESHOLD_CLOSE, DEFAULT_HUMIDITY_THRESHOLD_CLOSE
                ),
            ): vol.Coerce(float),
            vol.Required(
                CONF_NOTIFY_METHOD,
                default=defaults.get(CONF_NOTIFY_METHOD, [NOTIFY_METHOD_MOBILE]),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=NOTIFY_METHOD_SONOS, label="Sonos (Sprachausgabe)"
                        ),
                        selector.SelectOptionDict(
                            value=NOTIFY_METHOD_MOBILE,
                            label="Home Assistant App (Push)",
                        ),
                    ],
                    multiple=True,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
    )


def _build_sonos_schema(defaults: dict | None = None) -> vol.Schema:
    return vol.Schema(
        {
            # Mehrfachauswahl: Ansage kann gleichzeitig auf mehreren
            # Sonos-Lautsprechern erfolgen
            _entity_marker(CONF_SONOS_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", multiple=True)
            ),
            _entity_marker(CONF_TTS_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
        }
    )


def _build_mobile_schema(defaults: dict | None = None) -> vol.Schema:
    return vol.Schema(
        {
            # Mehrfachauswahl: mehrere notify.* Entitäten (z. B. mehrere
            # Familienmitglieder/Geräte) gleichzeitig benachrichtigen
            _entity_marker(
                CONF_MOBILE_NOTIFY_ENTITY, defaults
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="notify", multiple=True)
            ),
        }
    )


class _NotifyFlowMixin:
    """Gemeinsame Schrittlogik für Config- und Options-Flow.

    Nach dem Hauptschritt werden - abhängig von der Auswahl bei
    CONF_NOTIFY_METHOD - nacheinander nur die passenden Folgeschritte
    gezeigt (Sonos und/oder App).
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
            if not user_input.get(CONF_MOBILE_NOTIFY_ENTITY):
                errors["base"] = "mobile_config_missing"
            else:
                self._data.update(user_input)
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
      1. user            - Grunddaten + Auswahl der Benachrichtigungsmethode(n)
      2. notify_sonos     - nur falls "Sonos" ausgewählt wurde
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

        if user_input is not None:
            methods = user_input.get(CONF_NOTIFY_METHOD) or []

            if not methods:
                errors["base"] = "notify_method_required"
            else:
                unique_id = (
                    f"{user_input[CONF_ROOM_NAME]}_"
                    f"{user_input[CONF_TEMP_SOURCE_ENTITY]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                self._data = user_input
                self._pending_notify_methods = list(methods)
                return await self._async_step_next()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(user_input),
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

        if user_input is not None:
            methods = user_input.get(CONF_NOTIFY_METHOD) or []

            if not methods:
                errors["base"] = "notify_method_required"
            else:
                # Bestehende Werte behalten, neue Eingaben überschreiben sie
                self._data = {**current, **user_input}
                self._pending_notify_methods = list(methods)
                return await self._async_step_next()

        return self.async_show_form(
            step_id="init",
            data_schema=_build_user_schema(user_input or current),
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
