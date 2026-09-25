"""Konstanten für die Smart Climate Integration."""

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
# Schlüssel in hass.data[DOMAIN], unter dem die aktuell installierte
# Versionsnummer (aus manifest.json) für die Dashboard-Karte hinterlegt
# wird (siehe __init__.py:async_setup / binary_sensor.py:extra_state_attributes).
VERSION_KEY = "_integration_version"

# Name des automatisch angelegten globalen Eintrags (CONF_ROOM_NAME-Wert,
# gleichzeitig der angezeigte Entry-Titel). Seit dem Anzeigenamen-Rename auf
# "Smart Climate" (0.59.0) - siehe __init__.py:_migrate_global_entry_title()
# für die Migration bereits bestehender Installationen und CLAUDE.md
# Lektion 43. LEGACY_GLOBAL_ROOM_NAME wird ausschließlich von dieser
# Migration benötigt.
GLOBAL_ROOM_NAME = "- Smart Climate Optionen -"
LEGACY_GLOBAL_ROOM_NAME = "- Smart Ventilation Optionen -"

CONF_ROOM_NAME = "room_name"
# Optional: die HA-Bereich-ID (area_registry), aus der beim Anlegen der
# Raumname vorbelegt und die Sensor-/Geräte-Auswahllisten auf die dem
# Bereich zugeordneten Entitäten eingeschränkt wurden. Rein eine
# Config-Flow-Komfortfunktion - wird zur Laufzeit (binary_sensor.py) nicht
# ausgewertet. Kein Pflichtfeld, da nicht jeder Raum einem HA-Bereich
# entsprechen muss.
CONF_AREA_ID = "area_id"
CONF_TEMP_SOURCE_ENTITY = "temperature_source_entity"
CONF_TEMP_ATTRIBUTE = "temperature_attribute"
# Standard False (bestehende Räume verhalten sich unverändert - sie haben
# ein Fenster). True = dieser Raum hat KEIN Fenster - es werden nie
# Öffnen-/Schließen-Benachrichtigungen erzeugt, die Geräte-Steuerung
# (Luftentfeuchter/Klimaanlage) läuft trotzdem normal anhand der
# Sensorwerte weiter.
CONF_NO_WINDOW = "no_window"
CONF_HUMIDITY_ENTITY = "humidity_entity"
# CO2-Sensor (ppm) - analog zur Luftfeuchtigkeit, aber ohne Außenluft-
# Vergleich: Außenluft liegt praktisch immer bei ~420 ppm, also weit unter
# jeder sinnvollen Innenschwelle - Lüften hilft bei CO2 immer.
CONF_CO2_ENTITY = "co2_entity"
CONF_OUTDOOR_TEMP_ENTITY = "outdoor_temp_entity"
# Nur in den globalen Einstellungen ("Smart Climate Optionen") verfügbar,
# nicht pro Raum überschreibbar - wie CONF_OUTDOOR_TEMP_ENTITY.
CONF_OUTDOOR_HUMIDITY_ENTITY = "outdoor_humidity_entity"
CONF_WINDOW_ENTITY = "window_entity"
# Standard False. True = für diesen Raum wird nie "bitte schließen"
# empfohlen (Temperatur/Luftfeuchtigkeit/CO2/Winter-Höchstdauer/Sommer-Fall
# bleiben ohne Wirkung auf das Schließen) - gedacht für Räume, in denen eine
# Schließen-Empfehlung nicht sinnvoll umsetzbar ist, z. B. weil der
# Fensterkontakt den tatsächlichen Zustand nicht zuverlässig widerspiegelt
# (z. B. eine Schiebetür) oder weil eine Klimaanlage die Kühlung ohnehin
# unabhängig vom Fenster übernimmt. Frost-/Hitzeschutz bleiben davon
# UNBERÜHRT und schließen weiterhin sofort - das sind Sicherheits-, keine
# reinen Komfort-Bedingungen. Öffnen-Empfehlungen sind ebenfalls unberührt.
CONF_DISABLE_CLOSE_RECOMMENDATION = "disable_close_recommendation"
CONF_TEMP_THRESHOLD_OPEN = "temp_threshold_open"
CONF_TEMP_THRESHOLD_CLOSE = "temp_threshold_close"
CONF_HUMIDITY_THRESHOLD_OPEN = "humidity_threshold_open"
CONF_HUMIDITY_THRESHOLD_CLOSE = "humidity_threshold_close"
CONF_CO2_THRESHOLD_OPEN = "co2_threshold_open"
CONF_CO2_THRESHOLD_CLOSE = "co2_threshold_close"
CONF_NOTIFY_METHOD = "notify_method"
CONF_SONOS_ENTITY = "sonos_entity"
CONF_TTS_ENTITY = "tts_entity"
# Aktivierungs-Checkbox im Raum-Formular (Abschnitt "Benachrichtigungs-
# methoden") - ersetzt die frühere Mehrfachauswahl als eigenständiges Feld.
# Sprachausgabe hat keine eigene Checkbox mehr - sie ist aktiv, sobald
# mindestens ein Lautsprecher (CONF_SONOS_ENTITY) ausgewählt ist.
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
CONF_HEAT_PROTECTION_TEMP = "heat_protection_temp"
CONF_WINTER_OUTDOOR_THRESHOLD = "winter_outdoor_threshold"
CONF_MAX_OPEN_DURATION_WINTER = "max_open_duration_winter_minutes"
CONF_REMINDER_INTERVAL = "reminder_interval_minutes"
CONF_FROST_DEBOUNCE_MINUTES = "frost_debounce_minutes"

# Optionale Geräte-Steuerung
CONF_DEHUMIDIFIER_ENTITY = "dehumidifier_entity"
# Optional: ein binary_sensor, der "an" meldet, sobald der Tank des
# Luftentfeuchters voll ist/einen Fehler hat - nur zur Anzeige (Dashboard-
# Karte), keine Auswirkung auf die Lüftungs-/Geräte-Logik selbst.
CONF_DEHUMIDIFIER_TANK_FULL_ENTITY = "dehumidifier_tank_full_entity"
CONF_AC_ENTITY = "ac_entity"
# Heizung: bewusst nur "climate"-Entitäten (siehe HEATING_DOMAINS) - anders
# als Luftentfeuchter/Klimaanlage kein einfaches Ein/Aus, sondern zwei feste
# Sollwerte (Comfort/Standby, siehe CONF_HEATING_COMFORT_TEMP/
# CONF_HEATING_STANDBY_TEMP), wie für Heizungen typisch. Braucht dafür
# climate.set_temperature, das nur climate-Entitäten unterstützen.
CONF_HEATING_ENTITY = "heating_entity"
# Standard False. True = die bereits als Innentemperatur-Quelle (CONF_
# TEMP_SOURCE_ENTITY) gewählte Entität wird zusätzlich als Heizungs-Gerät
# verwendet, statt eine zweite, eigene Entität in CONF_HEATING_ENTITY
# auszuwählen - erspart die doppelte Auswahl derselben climate-Entität für
# Räume, in denen dieselbe Entität sowohl die Innentemperatur liefert als
# auch geheizt werden soll. Nur wirksam, wenn die Temperaturquelle
# tatsächlich eine climate-Entität ist (siehe HEATING_DOMAINS) - sonst wie
# "keine Heizung konfiguriert" behandelt (permissiv, kein Formularfehler).
# CONF_HEATING_ENTITY selbst bleibt bei aktivem Schalter wirkungslos.
CONF_HEATING_USE_TEMP_SOURCE = "heating_use_temp_source"
# Unterhalb dieser Innentemperatur wird auf den Comfort-Sollwert geschaltet;
# ab Erreichen von CONF_HEATING_THRESHOLD_TEMP + CONF_TEMP_MARGIN (dieselbe
# Toleranz-Marge wie bei den anderen Temperaturvergleichen) wieder auf den
# Standby-Sollwert - dazwischen bleibt der zuletzt gesetzte Sollwert
# unverändert (Hysterese, verhindert Flackern nahe der Schwelle).
CONF_HEATING_THRESHOLD_TEMP = "heating_threshold_temp"
CONF_HEATING_COMFORT_TEMP = "heating_comfort_temp"
CONF_HEATING_STANDBY_TEMP = "heating_standby_temp"
# Optionale Liste von person-/device_tracker-Entitäten (Mehrfachauswahl,
# analog zu CONF_SONOS_ENTITY) - ist mindestens eine konfiguriert, pausiert
# die Heizung (Standby), solange ALLE davon bestätigt "not_home" melden;
# meldet mindestens eine "home", oder ist der Zustand einer von ihnen
# gerade unbekannt/nicht verfügbar, läuft die Heizung normal weiter
# (permissiv - ein GPS-Aussetzer soll nicht fälschlich die Heizung
# abschalten). Ohne konfigurierte Entität keine Auswirkung (wie bisher).
CONF_HEATING_PRESENCE_ENTITIES = "heating_presence_entities"
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

DEFAULT_TEMP_THRESHOLD_OPEN = 23.0
DEFAULT_TEMP_THRESHOLD_CLOSE = 21.0
DEFAULT_HUMIDITY_THRESHOLD_OPEN = 60.0
DEFAULT_HUMIDITY_THRESHOLD_CLOSE = 50.0

# CO2 in ppm. 1000 ppm ist die gängige Empfehlung für "spätestens jetzt
# lüften" (z. B. Umweltbundesamt), 800 ppm als Schließen-Schwelle ergibt
# dieselbe relative Hysterese wie bei der Luftfeuchtigkeit (60/50).
DEFAULT_CO2_THRESHOLD_OPEN = 1000.0
DEFAULT_CO2_THRESHOLD_CLOSE = 800.0

# Toleranz-Marge (°C) bei allen Außen-/Innentemperatur-Vergleichen, um
# Flackern der Empfehlung bei Werten nahe der Schwelle zu vermeiden.
DEFAULT_TEMP_MARGIN = 1.0

# Unterhalb dieser Außentemperatur wird nie geöffnet (Frostschutz); ein
# bereits geöffneter Zustand wird auf "Schließen" gesetzt, sobald die
# Außentemperatur ununterbrochen für mindestens DEFAULT_FROST_DEBOUNCE_MINUTES
# darunter liegt (siehe unten) - das reine Blockieren des Öffnens greift
# dagegen weiterhin sofort, ohne Verzögerung.
DEFAULT_FROST_PROTECTION_TEMP = 0.0

# Mindestdauer (Minuten), die die Außentemperatur ununterbrochen auf/unter
# der Frostschutz-Grenze liegen muss, bevor ein bereits geöffneter Zustand
# tatsächlich auf "Schließen" gesetzt wird. Schützt vor einem einzelnen
# unplausiblen Ausreißer-Messwert (Sensor-Glitch), der sonst sofort und ohne
# echten Grund schließen würde. 0 = kein Debounce, sofortiges Schließen wie
# vor Einführung dieser Einstellung.
DEFAULT_FROST_DEBOUNCE_MINUTES = 10

# Oberhalb dieser Außentemperatur wird nie geöffnet (Hitzeschutz, Pendant
# zum Frostschutz) - Lüften würde absehbar nur noch Hitze hereinlassen und
# die Innentemperatur weiter über die Schwelle treiben, unabhängig davon,
# ob eigentlich wegen Temperatur, Luftfeuchtigkeit oder CO2 gelüftet werden
# sollte. Ein bereits geöffneter Zustand wird sofort auf "Schließen"
# gesetzt.
DEFAULT_HEAT_PROTECTION_TEMP = 30.0

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

# Nur "climate" - Comfort/Standby-Sollwerte (climate.set_temperature)
# funktionieren nur mit echten climate-Entitäten, anders als das einfache
# Ein/Aus von Luftentfeuchter/Klimaanlage.
HEATING_DOMAINS = ["climate"]

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

# Typische Wohnraum-Heizungswerte: Standby knapp unter, Comfort knapp über
# der Schwelle - siehe CONF_HEATING_THRESHOLD_TEMP in const.py oben.
DEFAULT_HEATING_THRESHOLD_TEMP = 20.0
DEFAULT_HEATING_COMFORT_TEMP = 21.0
DEFAULT_HEATING_STANDBY_TEMP = 17.0

# Priorität bei Konflikt zwischen Winter-Höchstdauer und noch bestehendem
# Feuchtigkeits-Lüftungsbedarf. True (Standard) = Luftfeuchtigkeit hat
# Vorrang (Winter-Höchstdauer wird bei Bedarf ignoriert). False = die
# Winter-Höchstdauer wird strikt durchgesetzt, auch bei noch hoher
# Luftfeuchtigkeit. Frostschutz hat davon unabhängig immer Vorrang.
CONF_HUMIDITY_PRIORITY_OVER_DURATION = "humidity_priority_over_duration"
DEFAULT_HUMIDITY_PRIORITY_OVER_DURATION = True

# Duscherkennung: verzögert die Öffnen-Empfehlung wegen Luftfeuchtigkeit,
# solange die Luftfeuchtigkeit gerade schnell ansteigt (typisch beim
# Duschen) - Lüften direkt während des Duschens bringt nichts, da weiter
# Dampf entsteht. Erkennung rein anhand des Anstiegs des bereits
# konfigurierten Luftfeuchtigkeitssensors, kein zusätzlicher Sensor nötig.
# Standard aus, nur pro Raum einstellbar (Abschnitt "Sensoren") - keine
# globale Einstellung, da nur für Räume mit Dusche/Badewanne relevant.
CONF_SHOWER_DETECTION_ENABLED = "shower_detection_enabled"
CONF_SHOWER_RISE_THRESHOLD = "shower_rise_threshold"
DEFAULT_SHOWER_DETECTION_ENABLED = False
# %-Punkte relative Luftfeuchtigkeit pro Minute, oberhalb der ein laufendes
# Duschen angenommen wird.
DEFAULT_SHOWER_RISE_THRESHOLD = 1.5
# Zeitfenster (Minuten), über das der Anstieg gemessen wird - je kürzer,
# desto schneller reagiert die Erkennung auf ein Ende des Duschens, aber
# desto störanfälliger gegen kurze Messschwankungen. Bewusst fest verdrahtet,
# nicht über die UI einstellbar.
SHOWER_RISE_LOOKBACK_MINUTES = 10

# Konfigurierbare Benachrichtigungstexte (nur in den globalen Einstellungen
# "Smart Climate Optionen" - {raum} wird durch den jeweiligen Raumnamen
# ersetzt). Über _effective() aufgelöst wie die anderen Werte - technisch
# wäre damit sogar ein zukünftiger Raum-Override ohne weitere Codeänderung
# möglich, aktuell aber bewusst nur global im Formular angeboten.
CONF_MSG_OPEN_HUMIDITY = "msg_open_humidity"
CONF_MSG_OPEN_CO2 = "msg_open_co2"
CONF_MSG_OPEN_TEMP = "msg_open_temp"
CONF_MSG_CLOSE_FROST = "msg_close_frost"
CONF_MSG_CLOSE_HEAT = "msg_close_heat"
CONF_MSG_CLOSE_DURATION = "msg_close_duration"
CONF_MSG_CLOSE_HUMIDITY = "msg_close_humidity"
CONF_MSG_CLOSE_CO2 = "msg_close_co2"
CONF_MSG_CLOSE_OUTDOOR_WARMER = "msg_close_outdoor_warmer"
CONF_MSG_CLOSE_OUTDOOR_WETTER = "msg_close_outdoor_wetter"
CONF_MSG_CLOSE_DEFAULT = "msg_close_default"
CONF_MSG_REMINDER = "msg_reminder"

DEFAULT_MSG_OPEN_HUMIDITY = (
    "Bitte das Fenster im {raum} öffnen - die Luftfeuchtigkeit liegt mit "
    "{wert} über dem Schwellenwert von {schwelle}."
)
DEFAULT_MSG_OPEN_CO2 = (
    "Bitte das Fenster im {raum} öffnen - der CO2-Wert liegt mit {wert} "
    "über dem Schwellenwert von {schwelle}."
)
DEFAULT_MSG_OPEN_TEMP = (
    "Bitte das Fenster im {raum} zum Lüften öffnen - die Innentemperatur "
    "liegt mit {wert} über dem Schwellenwert von {schwelle}, draußen ist "
    "es kühler."
)
DEFAULT_MSG_CLOSE_FROST = (
    "Bitte das Fenster im {raum} wegen Frostgefahr wieder schließen - die "
    "Außentemperatur liegt mit {wert} auf/unter der Frostschutz-Grenze "
    "von {schwelle}."
)
DEFAULT_MSG_CLOSE_HEAT = (
    "Bitte das Fenster im {raum} wieder schließen - draußen ist es mit "
    "{wert} zu heiß, um sinnvoll zu lüften (Hitzeschutz-Grenze: "
    "{schwelle})."
)
DEFAULT_MSG_CLOSE_DURATION = (
    "Das Fenster im {raum} ist schon {wert} offen - bitte wegen der Kälte "
    "draußen wieder schließen (Höchstdauer: {schwelle})."
)
DEFAULT_MSG_CLOSE_HUMIDITY = (
    "Die Luftfeuchtigkeit im {raum} liegt mit {wert} wieder im normalen "
    "Bereich (Schwellenwert: {schwelle}) - Fenster kann geschlossen "
    "werden."
)
DEFAULT_MSG_CLOSE_CO2 = (
    "Der CO2-Wert im {raum} liegt mit {wert} wieder im normalen Bereich "
    "(Schwellenwert: {schwelle}) - Fenster kann geschlossen werden."
)
DEFAULT_MSG_CLOSE_OUTDOOR_WARMER = (
    "Draußen ist es mit {wert} jetzt wärmer als im {raum} ({schwelle}) - "
    "bitte Fenster wieder schließen."
)
DEFAULT_MSG_CLOSE_OUTDOOR_WETTER = (
    "Draußen ist die Luft mit {wert} inzwischen feuchter als im {raum} "
    "({schwelle}) - Lüften würde die Luftfeuchtigkeit jetzt erhöhen statt "
    "senken, bitte Fenster wieder schließen."
)
DEFAULT_MSG_CLOSE_DEFAULT = (
    "Bitte das Fenster im {raum} wieder schließen - die Innentemperatur "
    "liegt mit {wert} auf/unter dem Schwellenwert von {schwelle}."
)
DEFAULT_MSG_REMINDER = (
    "Erinnerung: Das Fenster im {raum} sollte noch geöffnet sein "
    "({wert}, Schwellenwert {schwelle})."
)
