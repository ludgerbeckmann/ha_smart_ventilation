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
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, "")
            ): str,
            vol.Required(CONF_TEMP_SOURCE_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=TEMP_SOURCE_DOMAINS)
            ),
            vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            # Außentemperatur ist Pflicht: entscheidend für sinnvolles Lüften
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
            # Mehrfachauswahl: Sonos und App können gleichzeitig aktiv sein
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
            vol.Optional(CONF_SONOS_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Optional(CONF_TTS_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
            # Dropdown mit allen verfügbaren notify.* Entitäten
            vol.Optional(CONF_MOBILE_NOTIFY_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="notify")
            ),
        }
    )


def _build_attribute_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_TEMP_ATTRIBUTE,
                default=defaults.get(CONF_TEMP_ATTRIBUTE, DEFAULT_TEMP_ATTRIBUTE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=COMMON_TEMP_ATTRIBUTES,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


class SmartVentilationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow: pro Durchlauf wird ein Raum eingerichtet."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            methods = user_input.get(CONF_NOTIFY_METHOD) or []

            if not methods:
                errors["base"] = "notify_method_required"
            elif NOTIFY_METHOD_SONOS in methods and not (
                user_input.get(CONF_SONOS_ENTITY) and user_input.get(CONF_TTS_ENTITY)
            ):
                errors["base"] = "sonos_config_missing"
            elif NOTIFY_METHOD_MOBILE in methods and not user_input.get(
                CONF_MOBILE_NOTIFY_ENTITY
            ):
                errors["base"] = "mobile_config_missing"
            else:
                unique_id = (
                    f"{user_input[CONF_ROOM_NAME]}_"
                    f"{user_input[CONF_TEMP_SOURCE_ENTITY]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                self._data = user_input

                # Attribut-Auswahl nur relevant für climate-Entitäten
                source_domain = user_input[CONF_TEMP_SOURCE_ENTITY].split(".")[0]
                if source_domain == "climate":
                    return await self.async_step_attribute()

                self._data[CONF_TEMP_ATTRIBUTE] = None
                return self.async_create_entry(
                    title=self._data[CONF_ROOM_NAME], data=self._data
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(user_input),
            errors=errors,
        )

    async def async_step_attribute(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Zweiter Schritt: Temperatur-Attribut, nur für climate-Entitäten."""
        if user_input is not None:
            self._data[CONF_TEMP_ATTRIBUTE] = user_input[CONF_TEMP_ATTRIBUTE]
            return self.async_create_entry(
                title=self._data[CONF_ROOM_NAME], data=self._data
            )

        return self.async_show_form(
            step_id="attribute",
            data_schema=_build_attribute_schema(),
            description_placeholders={
                "entity_id": self._data[CONF_TEMP_SOURCE_ENTITY]
            },
        )
