"""Config Flow für den Smart Lüftungsassistenten."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_MOBILE_NOTIFY_SERVICE,
    CONF_NOTIFY_METHOD,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_ROOM_NAME,
    CONF_SONOS_ENTITY,
    CONF_TEMP_ATTRIBUTE,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_TTS_ENTITY,
    CONF_WINDOW_ENTITY,
    DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
    DEFAULT_HUMIDITY_THRESHOLD_OPEN,
    DEFAULT_TEMP_ATTRIBUTE,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DOMAIN,
    NOTIFY_METHOD_MOBILE,
    NOTIFY_METHOD_SONOS,
)


def _build_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_ROOM_NAME, default=defaults.get(CONF_ROOM_NAME, "")
            ): str,
            vol.Required(CONF_CLIMATE_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate")
            ),
            vol.Optional(
                CONF_TEMP_ATTRIBUTE,
                default=defaults.get(CONF_TEMP_ATTRIBUTE, DEFAULT_TEMP_ATTRIBUTE),
            ): str,
            vol.Optional(CONF_HUMIDITY_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_OUTDOOR_TEMP_ENTITY): selector.EntitySelector(
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
                default=defaults.get(CONF_NOTIFY_METHOD, NOTIFY_METHOD_MOBILE),
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
                    ]
                )
            ),
            vol.Optional(CONF_SONOS_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Optional(CONF_TTS_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
            vol.Optional(CONF_MOBILE_NOTIFY_SERVICE): str,
        }
    )


class SmartVentilationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow: pro Durchlauf wird ein Raum eingerichtet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = f"{user_input[CONF_ROOM_NAME]}_{user_input[CONF_CLIMATE_ENTITY]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            if user_input.get(CONF_NOTIFY_METHOD) == NOTIFY_METHOD_SONOS and not (
                user_input.get(CONF_SONOS_ENTITY) and user_input.get(CONF_TTS_ENTITY)
            ):
                errors["base"] = "sonos_config_missing"
            elif user_input.get(
                CONF_NOTIFY_METHOD
            ) == NOTIFY_METHOD_MOBILE and not user_input.get(
                CONF_MOBILE_NOTIFY_SERVICE
            ):
                errors["base"] = "mobile_config_missing"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_ROOM_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )
