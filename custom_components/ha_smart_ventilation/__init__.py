"""Smart Ventilation - Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import CONF_IS_GLOBAL, DOMAIN, GLOBAL_ENTRY_ID_KEY

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["binary_sensor"]

# Diese Integration lässt sich ausschließlich über den Config-Flow (UI)
# einrichten, nicht über configuration.yaml - hassfest verlangt trotzdem
# ein CONFIG_SCHEMA, sobald async_setup implementiert ist.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _create_global_settings_entry(hass: HomeAssistant) -> None:
    """Stößt das (interne, formularlose) Anlegen des Eintrags "Smart
    Ventilation Options" an, falls noch keiner existiert. Läuft als
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


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Läuft einmal beim (ersten) Setup der Integration in dieser
    Home-Assistant-Sitzung. Stellt sicher, dass der Eintrag "Smart
    Ventilation Options" existiert - z. B. nach einem Neustart, falls er
    aus irgendeinem Grund fehlt."""
    _create_global_settings_entry(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet einen Raum oder die allgemeinen Einstellungen ein."""
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
