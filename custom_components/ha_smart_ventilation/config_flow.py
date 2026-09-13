"""Config Flow für Smart Ventilation."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
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


def _build_user_schema(defaults: dict | None = None) -> vol.Schema:
    """Hauptschritt: Raum, Temperaturquelle, Schwellenwerte, Benachrichtigungs-
    methode(n). Die konkreten Zugangsdaten für Sonos/App folgen in eigenen
    Schritten - je nachdem, was hier ausgewählt wird.
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, "")
            ): str,
            vol.Required(CONF_TEMP_SOURCE_ENTITY): selector.EntitySelector(
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
            vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_OUTDOOR_TEMP_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_WINDOW_ENTITY): selector.EntitySelector(
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


def _build_sonos_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SONOS_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Required(CONF_TTS_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
        }
    )


def _build_mobile_schema() -> vol.Schema:
    return vol.Schema(
        {
            # Dropdown mit allen verfügbaren notify.* Entitäten
            vol.Required(CONF_MOBILE_NOTIFY_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="notify")
            ),
        }
    )


class SmartVentilationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow: pro Durchlauf wird ein Raum eingerichtet.

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

    async def async_step_notify_sonos(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Erscheint nur, wenn 'Sonos' als Benachrichtigungsmethode gewählt wurde."""
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
            data_schema=_build_sonos_schema(),
            errors=errors,
        )

    async def async_step_notify_mobile(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Erscheint nur, wenn 'App' als Benachrichtigungsmethode gewählt wurde."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_MOBILE_NOTIFY_ENTITY):
                errors["base"] = "mobile_config_missing"
            else:
                self._data.update(user_input)
                return await self._async_step_next()

        return self.async_show_form(
            step_id="notify_mobile",
            data_schema=_build_mobile_schema(),
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

        return self.async_create_entry(
            title=self._data[CONF_ROOM_NAME], data=self._data
        )
