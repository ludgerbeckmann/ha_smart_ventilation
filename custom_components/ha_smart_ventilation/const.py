"""Konstanten für die Smart Ventilation Integration."""

DOMAIN = "ha_smart_ventilation"

CONF_ROOM_NAME = "room_name"
CONF_TEMP_SOURCE_ENTITY = "temperature_source_entity"
CONF_TEMP_ATTRIBUTE = "temperature_attribute"
CONF_HUMIDITY_ENTITY = "humidity_entity"
CONF_OUTDOOR_TEMP_ENTITY = "outdoor_temp_entity"
CONF_WINDOW_ENTITY = "window_entity"
CONF_TEMP_THRESHOLD_OPEN = "temp_threshold_open"
CONF_TEMP_THRESHOLD_CLOSE = "temp_threshold_close"
CONF_HUMIDITY_THRESHOLD_OPEN = "humidity_threshold_open"
CONF_HUMIDITY_THRESHOLD_CLOSE = "humidity_threshold_close"
CONF_NOTIFY_METHOD = "notify_method"
CONF_SONOS_ENTITY = "sonos_entity"
CONF_TTS_ENTITY = "tts_entity"
CONF_MOBILE_NOTIFY_ENTITY = "mobile_notify_entity"

NOTIFY_METHOD_SONOS = "sonos"
NOTIFY_METHOD_MOBILE = "mobile_app"

# Entitäten, die als Innentemperatur-Quelle ausgewählt werden können.
# "climate" nutzt ein Attribut (siehe CONF_TEMP_ATTRIBUTE), alle anderen
# Domains lesen direkt den Entitätszustand als Temperaturwert.
TEMP_SOURCE_DOMAINS = ["climate", "sensor", "number", "input_number"]

DEFAULT_TEMP_ATTRIBUTE = "current_temperature"
COMMON_TEMP_ATTRIBUTES = [
    "current_temperature",
    "temperature",
    "target_temperature",
]

DEFAULT_TEMP_THRESHOLD_OPEN = 24.0
DEFAULT_TEMP_THRESHOLD_CLOSE = 21.0
DEFAULT_HUMIDITY_THRESHOLD_OPEN = 60.0
DEFAULT_HUMIDITY_THRESHOLD_CLOSE = 50.0
