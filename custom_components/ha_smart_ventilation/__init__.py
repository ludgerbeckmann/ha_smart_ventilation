"""Smart Climate - Home Assistant Integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.start import async_at_started
from homeassistant.loader import async_get_integration

from .const import (
    CONF_CO2_THRESHOLD_CLOSE,
    CONF_CO2_THRESHOLD_OPEN,
    CONF_DASH_WINDOW_FILL,
    CONF_DASH_WINDOW_FILL_ACTION,
    CONF_DASH_WINDOW_FILL_NOTICE,
    CONF_HUMIDITY_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN,
    CONF_IS_GLOBAL,
    CONF_ROOM_TYPE,
    CONF_ROOM_TYPE_PROFILES,
    CONF_ROOM_TYPE_THRESHOLDS_MIGRATED,
    CONF_TEMP_THRESHOLD_CLOSE,
    CONF_TEMP_THRESHOLD_OPEN,
    CONF_USAGE_LEARNING_DEFAULT_MIGRATED,
    CONF_USAGE_LEARNING_ENABLED,
    DASHBOARD_SIGNAL,
    DEFAULT_CO2_THRESHOLD_CLOSE,
    DEFAULT_CO2_THRESHOLD_OPEN,
    DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
    DEFAULT_HUMIDITY_THRESHOLD_OPEN,
    DEFAULT_TEMP_THRESHOLD_CLOSE,
    DEFAULT_TEMP_THRESHOLD_OPEN,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
    ROOM_STATUS_KEY,
    ROOM_TYPE_FALLBACK,
    ROOM_TYPE_KEYS,
    ROOM_TYPE_LABELS,
    ROOM_TYPE_THRESHOLD_KEYS,
    VERSION_KEY,
    room_type_value,
)
from .dashboard import async_install_bubble_module

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["binary_sensor", "sensor"]
# Die allgemeinen Einstellungen haben nur den Außen-Sensor (absolute
# Luftfeuchtigkeit), keinen binary_sensor.
GLOBAL_PLATFORMS: list[str] = ["sensor"]

# Eigenständige JS-Custom-Card (parallel zur README-Markdown/Jinja-Karte
# nutzbar, siehe CLAUDE.md) - wird automatisch als Lovelace-Ressource
# registriert, damit der Nutzer keine eigene resources:-URL im Dashboard
# eintragen muss.
CARD_JS_FILENAME = "smart-climate-card.js"
CARD_URL_PATH = f"/{DOMAIN}/{CARD_JS_FILENAME}"

# Diese Integration lässt sich ausschließlich über den Config-Flow (UI)
# einrichten, nicht über configuration.yaml - hassfest verlangt trotzdem
# ein CONFIG_SCHEMA, sobald async_setup implementiert ist.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _create_global_settings_entry(hass: HomeAssistant) -> None:
    """Stößt das (interne, formularlose) Anlegen des Eintrags "Smart
    Climate Optionen" an, falls noch keiner existiert. Läuft als
    Hintergrund-Task, damit der Aufrufer (async_setup/async_remove_entry)
    nicht blockiert."""
    already_exists = any(
        entry.data.get(CONF_IS_GLOBAL)
        for entry in hass.config_entries.async_entries(DOMAIN)
    )
    if already_exists:
        return
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={},
        )
    )


# Schlüssel, die der Code nicht mehr liest (entfernte Felder früherer Versionen).
# Gespeicherte Einträge behalten sie sonst für immer. "dash_window_fill" fehlt
# hier absichtlich: _migrate_window_fill() übernimmt seinen Wert vorher.
_OBSOLETE_KEYS = (
    "notify_method",
    "dash_cycle",
    "dash_color_comfort",
    "dash_color_standby",
    "dash_color_eco",
    "dash_color_protection",
    "dash_color_summer",
    "dash_color_hot",
    "dash_color_warm",
    "dash_color_cold",
    "dash_color_cover",
    "dash_color_tint_hint",
    "dash_color_tint_action",
    "heating_comfort_end_weekday",
    "heating_comfort_end_weekend",
    "heating_night_end_weekday",
    "heating_night_end_weekend",
)


def _purge_obsolete_keys(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Entfernt einmalig Schlüssel entfernter Felder aus dem Eintrag."""
    if not any(key in entry.data for key in _OBSOLETE_KEYS):
        return
    new_data = {k: v for k, v in entry.data.items() if k not in _OBSOLETE_KEYS}
    hass.config_entries.async_update_entry(entry, data=new_data)


def _migrate_usage_learning_default(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hebt "Gelernte Zeiten verwenden" im globalen Eintrag einmalig auf Ja
    (neuer Standard seit 1.16.0, CLAUDE.md Lektion 137). Das globale
    Formular speichert den früheren Standard Nein immer mit ab, ein bloß
    geänderter DEFAULT_*-Wert erreicht bestehende Einträge also nicht
    (Lektion 10). Der Marker verhindert, dass ein danach bewusst gesetztes
    Nein erneut überschrieben wird."""
    if not entry.data.get(CONF_IS_GLOBAL):
        return
    if entry.data.get(CONF_USAGE_LEARNING_DEFAULT_MIGRATED):
        return
    new_data = dict(entry.data)
    new_data[CONF_USAGE_LEARNING_ENABLED] = True
    new_data[CONF_USAGE_LEARNING_DEFAULT_MIGRATED] = True
    hass.config_entries.async_update_entry(entry, data=new_data)


def _migrate_window_fill(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Übernimmt die Fensterfarbe aus 1.20.0 (ein Feld) einmalig in die
    beiden neuen Felder (Handlungsbedarf/Hinweis, 1.21.0)."""
    if not entry.data.get(CONF_IS_GLOBAL):
        return
    if CONF_DASH_WINDOW_FILL not in entry.data:
        return
    new_data = dict(entry.data)
    old = new_data.pop(CONF_DASH_WINDOW_FILL)
    new_data.setdefault(CONF_DASH_WINDOW_FILL_ACTION, old)
    new_data.setdefault(CONF_DASH_WINDOW_FILL_NOTICE, old)
    hass.config_entries.async_update_entry(entry, data=new_data)


# Bisherige globale Standardwerte der Lüftungsschwellen (für die Umstellung
# auf Raumtypen, falls im globalen Eintrag nichts gespeichert war).
_OLD_GLOBAL_THRESHOLD_DEFAULTS = {
    CONF_TEMP_THRESHOLD_OPEN: DEFAULT_TEMP_THRESHOLD_OPEN,
    CONF_TEMP_THRESHOLD_CLOSE: DEFAULT_TEMP_THRESHOLD_CLOSE,
    CONF_HUMIDITY_THRESHOLD_OPEN: DEFAULT_HUMIDITY_THRESHOLD_OPEN,
    CONF_HUMIDITY_THRESHOLD_CLOSE: DEFAULT_HUMIDITY_THRESHOLD_CLOSE,
    CONF_CO2_THRESHOLD_OPEN: DEFAULT_CO2_THRESHOLD_OPEN,
    CONF_CO2_THRESHOLD_CLOSE: DEFAULT_CO2_THRESHOLD_CLOSE,
}


def _same_value(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def _migrate_room_type_thresholds(hass: HomeAssistant) -> None:
    """Einmalige Umstellung auf Raumtypen ohne globale Ebene (1.35.0,
    CLAUDE.md Lektion 183). Läuft in async_setup, also bevor die Einträge
    eingerichtet werden, und braucht dafür noch die alten globalen Werte:

    - Räume ohne gültigen Raumtyp bekommen "Nebenraum".
    - Raum-Overrides werden gelöscht, wenn sie dem Wert des Raumtyps
      entsprechen; bei den Lüftungsschwellen auch, wenn sie nur den
      bisherigen globalen Wert wiederholten (kein bewusstes Abweichen).
    - Der globale Eintrag verliert die vom Raumtyp übernommenen Schlüssel.
    Der Marker im globalen Eintrag verhindert eine Wiederholung."""
    entries = hass.config_entries.async_entries(DOMAIN)
    global_entry = next((e for e in entries if e.data.get(CONF_IS_GLOBAL)), None)
    if global_entry is None or global_entry.data.get(CONF_ROOM_TYPE_THRESHOLDS_MIGRATED):
        return
    global_data = dict(global_entry.data)
    profiles = global_data.get(CONF_ROOM_TYPE_PROFILES)
    for entry in entries:
        if entry.data.get(CONF_IS_GLOBAL):
            continue
        data = dict(entry.data)
        changed = False
        room_type = data.get(CONF_ROOM_TYPE)
        if room_type not in ROOM_TYPE_LABELS:
            room_type = ROOM_TYPE_FALLBACK
            data[CONF_ROOM_TYPE] = room_type
            changed = True
        for key in ROOM_TYPE_KEYS:
            if data.get(key) in (None, ""):
                continue
            _applies, type_value = room_type_value(profiles, room_type, key)
            redundant = _same_value(data[key], type_value)
            if not redundant and key in ROOM_TYPE_THRESHOLD_KEYS:
                old_global = global_data.get(key)
                if old_global in (None, ""):
                    old_global = _OLD_GLOBAL_THRESHOLD_DEFAULTS[key]
                redundant = _same_value(data[key], old_global)
            if redundant:
                del data[key]
                changed = True
        if changed:
            _LOGGER.info(
                "Raumtyp-Umstellung für %s: %s",
                entry.title,
                {k: entry.data.get(k) for k in entry.data if k not in data or data[k] != entry.data[k]},
            )
            hass.config_entries.async_update_entry(entry, data=data)
    for key in ROOM_TYPE_KEYS:
        global_data.pop(key, None)
    global_data[CONF_ROOM_TYPE_THRESHOLDS_MIGRATED] = True
    hass.config_entries.async_update_entry(global_entry, data=global_data)


def _get_lovelace_resources(hass: HomeAssistant):
    """Liefert die Lovelace-Ressourcen-Sammlung oder None.

    Home Assistant legt sie unter hass.data["lovelace"] ab - in älteren
    Versionen als Dict (Schlüssel "resources"), in neueren als typisiertes
    Objekt (Attribut ``resources``). Beides wird defensiv unterstützt."""
    data = hass.data.get("lovelace")
    if data is None:
        return None
    if isinstance(data, dict):
        return data.get("resources")
    return getattr(data, "resources", None)


def _split_resource_url(url: str) -> tuple[str, str]:
    path, _, query = str(url).partition("?")
    return path, query


async def _async_ensure_lovelace_resource(hass: HomeAssistant, version: str) -> None:
    """Trägt die Karte als Lovelace-Ressource ein (nur Storage-Modus).

    Bewusst NICHT entfernend: Beim Löschen der Integration bleibt der Eintrag
    stehen und muss von Hand gelöscht werden (siehe README, Abschnitt
    "Dashboard-Karte"). Ein vom Nutzer selbst angelegter Eintrag für denselben
    Pfad ohne ``?v=`` bleibt unangetastet. Jeder Fehler wird nur geloggt, da
    dies auf Home-Assistant-Interna beruht (keine dokumentierte API)."""
    try:
        resources = _get_lovelace_resources(hass)
        # YAML-Modus: Sammlung ist schreibgeschützt (kein async_create_item).
        if resources is None or not hasattr(resources, "async_create_item"):
            _LOGGER.debug(
                "Lovelace-Ressourcen nicht im Storage-Modus - Karte wird nur "
                "über add_extra_js_url geladen."
            )
            return
        if not getattr(resources, "loaded", True):
            await resources.async_load()
            resources.loaded = True

        target_url = f"{CARD_URL_PATH}?v={version}"
        ours = None
        for item in resources.async_items() or []:
            path, query = _split_resource_url(item.get("url", ""))
            if path != CARD_URL_PATH:
                continue
            if not query.startswith("v="):
                # Vom Nutzer selbst angelegt - nicht anfassen.
                return
            if ours is None:
                ours = item
        if ours is None:
            await resources.async_create_item({"res_type": "module", "url": target_url})
            _LOGGER.info("Dashboard-Karte als Lovelace-Ressource eingetragen: %s", target_url)
        elif ours.get("url") != target_url:
            await resources.async_update_item(
                ours["id"], {"res_type": "module", "url": target_url}
            )
            _LOGGER.info("Lovelace-Ressource der Dashboard-Karte aktualisiert: %s", target_url)
    except Exception:  # noqa: BLE001 - darf das Setup nie verhindern
        _LOGGER.warning(
            "Konnte die Dashboard-Karte nicht automatisch als Lovelace-Ressource "
            "eintragen - bitte von Hand unter Einstellungen > Dashboards > "
            "Ressourcen hinzufügen (siehe README).",
            exc_info=True,
        )


async def _register_frontend_card(hass: HomeAssistant, integration) -> None:
    """Registriert die eigenständige JS-Custom-Card (siehe
    custom_components/ha_smart_ventilation/www/smart-climate-card.js)
    automatisch als statischen Pfad + Lovelace-Ressource.

    Bewusst mit einem breiten try/except abgesichert: Ein Fehler hierbei
    (z. B. eine zukünftig geänderte Home-Assistant-Frontend-API) darf
    niemals das eigentliche Setup der Integration (Sensoren/Steuerung)
    verhindern - die Karte ist ein rein optionales Zusatzangebot, parallel
    zur bereits bestehenden Markdown/Jinja-Karte im README.

    Der Versions-Query-Parameter (?v=...) sorgt dafür, dass der Browser
    nach einem Integrations-Update nicht die alte JS-Datei aus dem Cache
    verwendet - analog zum bereits bestehenden Muster für die Karten-
    Versionsanzeige (VERSION_KEY).

    Die Datei wird mit Cache-Headern ausgeliefert (cache_headers=True):
    Die URL ändert sich mit jeder Version, daher ist langes Cachen sicher.
    Ohne Cache musste die App die Karte bei jedem Start neu laden - bei
    langsamer Verbindung (VPN, Funkloch) schlug das Laden gelegentlich fehl
    ("Custom element doesn't exist"), siehe CLAUDE.md Lektion 102.
    """
    try:
        js_path = Path(integration.file_path) / "www" / CARD_JS_FILENAME
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL_PATH, str(js_path), cache_headers=True)]
        )
        version = str(integration.version) if integration.version is not None else "0"
        add_extra_js_url(hass, f"{CARD_URL_PATH}?v={version}")

        # Zusätzlich als Lovelace-Ressource (nach dem Start, wenn Lovelace
        # geladen ist) - extra_module_url allein lud die Karte gelegentlich
        # nicht (CLAUDE.md Lektion 104).
        async def _ensure(_hass: HomeAssistant) -> None:
            await _async_ensure_lovelace_resource(hass, version)

        async_at_started(hass, _ensure)
    except Exception:  # noqa: BLE001 - siehe Docstring: darf das Setup nie verhindern
        _LOGGER.warning(
            "Konnte die eigenständige Dashboard-Karte (smart-climate-card.js) "
            "nicht als Lovelace-Ressource registrieren - die bisherige "
            "Markdown/Jinja-Karte (siehe README) ist davon unberührt.",
            exc_info=True,
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Läuft einmal beim (ersten) Setup der Integration in dieser
    Home-Assistant-Sitzung. Stellt sicher, dass der Eintrag "Smart
    Climate Optionen" existiert - z. B. nach einem Neustart, falls er
    aus irgendeinem Grund fehlt."""
    hass.data.setdefault(DOMAIN, {})
    # Für die Dashboard-Karte (Versionsanzeige) - liest die tatsächlich
    # installierte Version aus manifest.json, statt sie separat im Code zu
    # duplizieren (single source of truth bleibt manifest.json).
    integration = await async_get_integration(hass, DOMAIN)
    if integration.version is not None:
        hass.data[DOMAIN][VERSION_KEY] = str(integration.version)
    await _register_frontend_card(hass, integration)
    # Bubble-Card-Modul "climate_status" mitliefern/aktualisieren (nur wenn
    # Bubble Card Tools seinen Modul-Ordner angelegt hat).
    hass.async_create_task(async_install_bubble_module(hass))
    _migrate_room_type_thresholds(hass)
    _create_global_settings_entry(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet einen Raum oder die allgemeinen Einstellungen ein."""
    _migrate_usage_learning_default(hass, entry)
    _migrate_window_fill(hass, entry)
    _purge_obsolete_keys(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    if entry.data.get(CONF_IS_GLOBAL):
        # Die allgemeinen Einstellungen dienen vor allem als Fallback-
        # Datenquelle für die Raum-Entitäten (siehe binary_sensor.py) und
        # erzeugen nur den Sensor "Außen Absolute Luftfeuchtigkeit" (siehe
        # sensor.py).
        hass.data[DOMAIN][GLOBAL_ENTRY_ID_KEY] = entry.entry_id
        await hass.config_entries.async_forward_entry_setups(entry, GLOBAL_PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))
        return True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt einen Raum oder die allgemeinen Einstellungen wieder
    (Reload/Deaktivieren - NICHT die endgültige Löschung, dafür siehe
    async_remove_entry)."""
    if entry.data.get(CONF_IS_GLOBAL):
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, GLOBAL_PLATFORMS
        )
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id, None)
            if hass.data[DOMAIN].get(GLOBAL_ENTRY_ID_KEY) == entry.entry_id:
                hass.data[DOMAIN].pop(GLOBAL_ENTRY_ID_KEY, None)
        return unload_ok

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Zwischengespeicherten Raumstatus verwerfen (der Sensor würde sonst
        # nach einem Reload kurz einen veralteten Wert zeigen).
        hass.data[DOMAIN].get(ROOM_STATUS_KEY, {}).pop(entry.entry_id, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird von Home Assistant aufgerufen, wenn ein Eintrag endgültig
    gelöscht wird (im Unterschied zu async_unload_entry, das auch bei
    Reload/Deaktivieren läuft).

    Für die allgemeinen Einstellungen: sofort automatisch neu anlegen, da
    dieser Eintrag laut Wunsch immer vorhanden sein soll. Home Assistant
    erlaubt zwar grundsätzlich das Löschen jedes Eintrags (das lässt sich
    nicht unterbinden) - der Eintrag erscheint dadurch aber unmittelbar
    wieder, mit den Standardwerten.
    """
    if entry.data.get(CONF_IS_GLOBAL):
        _create_global_settings_entry(hass)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Bei Optionsänderung neu laden.

    Für die allgemeinen Einstellungen aktualisiert das nur
    hass.data[DOMAIN][...] (kein Platform-Reload nötig). Raum-Entitäten
    lesen die Werte bei jeder Neubewertung live aus hass.data - sie
    übernehmen Änderungen also spätestens beim nächsten 5-Minuten-Tick
    automatisch, auch ohne eigenen Reload.
    """
    if entry.data.get(CONF_IS_GLOBAL):
        hass.data[DOMAIN][entry.entry_id] = entry.data
        # Darstellungs-Sensor (Bubble-Card-Modul) neu schreiben lassen.
        async_dispatcher_send(hass, DASHBOARD_SIGNAL)
        return
    await hass.config_entries.async_reload(entry.entry_id)
