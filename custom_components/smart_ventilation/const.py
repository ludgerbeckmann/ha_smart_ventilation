"""Konstanten für die Smart Lüftungsassistent Integration."""

DOMAIN = "smart_ventilation"

CONF_ROOM_NAME = "room_name"
CONF_CLIMATE_ENTITY = "climate_entity"
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
CONF_MOBILE_NOTIFY_SERVICE = "mobile_notify_service"

NOTIFY_METHOD_SONOS = "sonos"
NOTIFY_METHOD_MOBILE = "mobile_app"

DEFAULT_TEMP_ATTRIBUTE = "current_temperature"
DEFAULT_TEMP_THRESHOLD_OPEN = 24.0
DEFAULT_TEMP_THRESHOLD_CLOSE = 21.0
DEFAULT_HUMIDITY_THRESHOLD_OPEN = 60.0
DEFAULT_HUMIDITY_THRESHOLD_CLOSE = 50.0
