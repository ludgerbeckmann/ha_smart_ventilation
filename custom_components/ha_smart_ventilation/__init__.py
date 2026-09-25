"""Smart Climate - Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.loader import async_get_integration

from .const import (
    CONF_IS_GLOBAL,
    CONF_MOBILE_ENABLED,
    CONF_NOTIFY_METHOD,
    CONF_PERSISTENT_ENABLED,
    CONF_ROOM_NAME,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
    GLOBAL_ROOM_NAME,
    LEGACY_GLOBAL_ROOM_NAME,
    NOTIFY_METHOD_MOBILE,
    NOTIFY_METHOD_PERSISTENT,
    VERSION_KEY,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["binary_sensor", "switch"]

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


def _migrate_legacy_notify_method(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migriert Raum-Einträge von der historischen, einmalig beim Speichern
    berechneten CONF_NOTIFY_METHOD-Liste (siehe Git-Historie/CLAUDE.md) auf
    die seitdem verwendeten CONF_MOBILE_ENABLED/CONF_PERSISTENT_ENABLED-
    Felder.

    Ohne diese Migration bleiben Räume, die seit jener Umstellung nie neu
    gespeichert wurden, dauerhaft ohne aktive Benachrichtigung: _effective()
    findet für CONF_MOBILE_ENABLED/CONF_PERSISTENT_ENABLED weder einen
    Raum- noch einen globalen Wert (beide fehlen im alten Datenformat
    komplett) und fällt auf den fest einprogrammierten Standard False
    zurück - selbst wenn der Raum weiterhin ein konfiguriertes
    Benachrichtigungsziel (mobile_targets) hat.

    Läuft bei jedem Setup, ist aber nach der ersten Migration wirkungslos,
    da CONF_NOTIFY_METHOD danach nicht mehr im Eintrag vorhanden ist.
    """
    if entry.data.get(CONF_IS_GLOBAL):
        return
    legacy_methods = entry.data.get(CONF_NOTIFY_METHOD)
    if legacy_methods is None:
        return

    new_data = dict(entry.data)
    if CONF_MOBILE_ENABLED not in new_data:
        new_data[CONF_MOBILE_ENABLED] = NOTIFY_METHOD_MOBILE in legacy_methods
    if CONF_PERSISTENT_ENABLED not in new_data:
        new_data[CONF_PERSISTENT_ENABLED] = NOTIFY_METHOD_PERSISTENT in legacy_methods
    new_data.pop(CONF_NOTIFY_METHOD, None)

    _LOGGER.debug(
        "Migriere veraltete notify_method-Liste (%s) für Raum %s auf "
        "mobile_enabled=%s/persistent_enabled=%s",
        legacy_methods,
        entry.title,
        new_data[CONF_MOBILE_ENABLED],
        new_data[CONF_PERSISTENT_ENABLED],
    )
    hass.config_entries.async_update_entry(entry, data=new_data)


def _migrate_global_entry_title(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migriert den Titel/CONF_ROOM_NAME-Wert des automatisch angelegten
    globalen Eintrags von der historischen Bezeichnung "- Smart Ventilation
    Optionen -" auf die seit dem Anzeigenamen-Rename (0.59.0, siehe
    CLAUDE.md Lektion 43) aktuelle "- Smart Climate Optionen -".

    Nur der Anzeigename ändert sich - GLOBAL_SETTINGS_UNIQUE_ID (und damit
    die entry_id) bleibt unverändert, weshalb hier eine einfache
    async_update_entry() reicht statt eine echte Migration mit neuem
    Eintrag zu benötigen. Ohne diesen Fix würde eine bereits bestehende
    Installation den alten Titel dauerhaft behalten, da async_create_entry
    den Titel nur beim allerersten Anlegen setzt (siehe Lektion 10:
    ein Rename trifft nie automatisch bereits gespeicherte Einträge).
    """
    if not entry.data.get(CONF_IS_GLOBAL):
        return
    if entry.data.get(CONF_ROOM_NAME) != LEGACY_GLOBAL_ROOM_NAME:
        return

    new_data = dict(entry.data)
    new_data[CONF_ROOM_NAME] = GLOBAL_ROOM_NAME
    _LOGGER.debug("Migriere globalen Eintragstitel auf %s", GLOBAL_ROOM_NAME)
    hass.config_entries.async_update_entry(
        entry, title=GLOBAL_ROOM_NAME, data=new_data
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
    _create_global_settings_entry(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet einen Raum oder die allgemeinen Einstellungen ein."""
    _migrate_legacy_notify_method(hass, entry)
    _migrate_global_entry_title(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    if entry.data.get(CONF_IS_GLOBAL):
        # Die allgemeinen Einstellungen erzeugen keine eigene Entität - sie
        # dienen nur als Fallback-Datenquelle für die Raum-Entitäten
        # (siehe binary_sensor.py). Kein Platform-Forward nötig.
        hass.data[DOMAIN][GLOBAL_ENTRY_ID_KEY] = entry.entry_id
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
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if hass.data[DOMAIN].get(GLOBAL_ENTRY_ID_KEY) == entry.entry_id:
            hass.data[DOMAIN].pop(GLOBAL_ENTRY_ID_KEY, None)
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
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
        return
    await hass.config_entries.async_reload(entry.entry_id)
