"""Konstanten für die Smart Ventilation Integration."""

DOMAIN = "ha_smart_ventilation"

# Marker im Config-Entry-Data, der eine Entry als "Allgemeine Einstellungen"
# statt als Raum kennzeichnet. Davon darf es maximal eine geben. Der
# angezeigte Name/Titel kommt - wie bei einem Raum - vom vom Nutzer
# eingegebenen CONF_ROOM_NAME ("virtueller Raum").
CONF_IS_GLOBAL = "is_global"
GLOBAL_SETTINGS_UNIQUE_ID = "ha_smart_ventilation_global_settings"
# Schlüssel in hass.data[DOMAIN], unter dem die entry_id der globalen
# Einstellungen (falls vorhanden) hinterlegt wird.
GLOBAL_ENTRY_ID_KEY = "_global_entry_id"

CONF_ROOM_NAME = "room_name"
CONF_TEMP_SOURCE_ENTITY = "temperature_source_entity"
CONF_TEMP_ATTRIBUTE = "temperature_attribute"
# Standard False (bestehende Räume verhalten sich unverändert - sie haben
# ein Fenster). True = dieser Raum hat KEIN Fenster - es werden nie
# Öffnen-/Schließen-Benachrichtigungen erzeugt, die Geräte-Steuerung
# (Luftentfeuchter/Klimaanlage) läuft trotzdem normal anhand der
# Sensorwerte weiter.
CONF_NO_WINDOW = "no_window"
CONF_HUMIDITY_ENTITY = "humidity_entity"
CONF_OUTDOOR_TEMP_ENTITY = "outdoor_temp_entity"
# Nur in den globalen Einstellungen ("Smart Ventilation Options") verfügbar,
# nicht pro Raum überschreibbar - wie CONF_OUTDOOR_TEMP_ENTITY.
CONF_OUTDOOR_HUMIDITY_ENTITY = "outdoor_humidity_entity"
CONF_WINDOW_ENTITY = "window_entity"
CONF_TEMP_THRESHOLD_OPEN = "temp_threshold_open"
CONF_TEMP_THRESHOLD_CLOSE = "temp_threshold_close"
CONF_HUMIDITY_THRESHOLD_OPEN = "humidity_threshold_open"
CONF_HUMIDITY_THRESHOLD_CLOSE = "humidity_threshold_close"
CONF_NOTIFY_METHOD = "notify_method"
CONF_SONOS_ENTITY = "sonos_entity"
CONF_TTS_ENTITY = "tts_entity"
# Aktivierungs-Checkboxen im Raum-Formular (Abschnitt "Benachrichtigungs-
# methoden") - ersetzen die frühere Mehrfachauswahl als eigenständiges Feld.
CONF_SONOS_ENABLED = "sonos_enabled"
CONF_MOBILE_ENABLED = "mobile_enabled"
CONF_PERSISTENT_ENABLED = "persistent_enabled"
CONF_MOBILE_NOTIFY_ENTITY = "mobile_notify_entity"
CONF_PRESENCE_ENTITY = "presence_entity"
# Liste von {mobile_notify_entity, presence_entity}-Paaren - ersetzt die
# frühere gemeinsame Mehrfachauswahl, damit die Anwesenheitsprüfung pro
# Person/Gerät statt pauschal für alle Notify-Ziele gilt.
CONF_MOBILE_TARGETS = "mobile_targets"

# TTS-Wiedergabe (nur global einstellbar, nicht pro Raum überschreibbar)
CONF_TTS_VOLUME = "tts_volume"
CONF_TTS_PLAYBACK_MODE = "tts_playback_mode"
TTS_PLAYBACK_MODE_PAUSE = "pause"
TTS_PLAYBACK_MODE_OVERLAY = "overlay"
DEFAULT_TTS_VOLUME = 40  # Prozent
DEFAULT_TTS_PLAYBACK_MODE = TTS_PLAYBACK_MODE_OVERLAY

# Erweiterte Lüftungslogik
CONF_TEMP_MARGIN = "temp_margin"
CONF_FROST_PROTECTION_TEMP = "frost_protection_temp"
CONF_WINTER_OUTDOOR_THRESHOLD = "winter_outdoor_threshold"
CONF_MAX_OPEN_DURATION_WINTER = "max_open_duration_winter_minutes"
CONF_REMINDER_INTERVAL = "reminder_interval_minutes"

# Optionale Geräte-Steuerung
CONF_DEHUMIDIFIER_ENTITY = "dehumidifier_entity"
CONF_AC_ENTITY = "ac_entity"
CONF_SHUTTER_ENTITY = "shutter_entity"
CONF_POWER_ENTITY = "power_entity"
CONF_MIN_SURPLUS_POWER = "min_surplus_power_watts"
CONF_POWER_GRACE_PERIOD = "power_grace_period_minutes"

NOTIFY_METHOD_SONOS = "sonos"
NOTIFY_METHOD_MOBILE = "mobile_app"
NOTIFY_METHOD_PERSISTENT = "persistent"

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

# Toleranz-Marge (°C) bei allen Außen-/Innentemperatur-Vergleichen, um
# Flackern der Empfehlung bei Werten nahe der Schwelle zu vermeiden.
DEFAULT_TEMP_MARGIN = 1.0

# Unterhalb dieser Außentemperatur wird nie geöffnet (Frostschutz); ein
# bereits geöffneter Zustand wird sofort auf "Schließen" gesetzt.
DEFAULT_FROST_PROTECTION_TEMP = 0.0

# Unterhalb dieser Außentemperatur gilt die Situation als "Winter" - dann
# greift die maximale Öffnungsdauer, um Wärmeverlust zu begrenzen.
DEFAULT_WINTER_OUTDOOR_THRESHOLD = 5.0

# Maximale Dauer (Minuten), die bei "Winter"-Bedingungen geöffnet bleiben darf,
# bevor automatisch zum Schließen aufgefordert wird.
DEFAULT_MAX_OPEN_DURATION_WINTER = 20

# Erinnerungsintervall (Minuten), falls die Empfehlung ignoriert wird.
# 0 = deaktiviert.
DEFAULT_REMINDER_INTERVAL = 0

# Domains, aus denen ein Luftentfeuchter bzw. eine Klimaanlage gewählt werden
# kann. "switch" deckt einfache Steckdosen-gesteuerte Geräte ab, "humidifier"
# native HA-Luftentfeuchter-Entitäten, "climate" native Klimaanlagen.
DEHUMIDIFIER_DOMAINS = ["switch", "humidifier"]
AC_DOMAINS = ["climate", "switch"]

# Fenstersperre/Rollladen: entweder eine "cover"-Entität (auf/zu) oder eine
# "switch"-Entität (1 = herunterfahren+sperren, 0 = hochfahren+entsperren).
SHUTTER_DOMAINS = ["cover", "switch"]

# Anwesenheitsprüfung für Push-Benachrichtigungen: person- oder
# device_tracker-Entität.
PRESENCE_DOMAINS = ["person", "device_tracker"]

# Mindest-Einspeiseleistung (Watt), ab der ein Gerät eingeschaltet werden
# darf, falls ein Leistungssensor konfiguriert ist. 0 = jede vorhandene
# Einspeisung reicht aus. Gilt nur für das Einschalten, nicht fürs Ausschalten.
DEFAULT_MIN_SURPLUS_POWER = 0.0

# Verzögerung (Minuten), bevor ein bereits laufendes Gerät wegen dauerhaft zu
# geringer Einspeisung abgeschaltet wird. Verhindert Abschalten bei kurzen
# Einspeise-Schwankungen (z. B. vorbeiziehende Wolke).
DEFAULT_POWER_GRACE_PERIOD = 15

# Priorität bei Konflikt zwischen Winter-Höchstdauer und noch bestehendem
# Feuchtigkeits-Lüftungsbedarf. True (Standard) = Luftfeuchtigkeit hat
# Vorrang (Winter-Höchstdauer wird bei Bedarf ignoriert). False = die
# Winter-Höchstdauer wird strikt durchgesetzt, auch bei noch hoher
# Luftfeuchtigkeit. Frostschutz hat davon unabhängig immer Vorrang.
CONF_HUMIDITY_PRIORITY_OVER_DURATION = "humidity_priority_over_duration"
DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION = True
