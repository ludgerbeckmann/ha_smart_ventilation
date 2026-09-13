"""Smart Ventilation - Home Assistant Integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_IS_GLOBAL, DOMAIN, GLOBAL_ENTRY_ID_KEY

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet einen Raum oder die globalen Einstellungen ein."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    if entry.data.get(CONF_IS_GLOBAL):
        # Die globalen Einstellungen erzeugen keine eigene Entität - sie
        # dienen nur als Fallback-Datenquelle für die Raum-Entitäten
        # (siehe binary_sensor.py). Kein Platform-Forward nötig.
        hass.data[DOMAIN][GLOBAL_ENTRY_ID_KEY] = entry.entry_id
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))
        return True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernt einen Raum oder die globalen Einstellungen wieder."""
    if entry.data.get(CONF_IS_GLOBAL):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if hass.data[DOMAIN].get(GLOBAL_ENTRY_ID_KEY) == entry.entry_id:
            hass.data[DOMAIN].pop(GLOBAL_ENTRY_ID_KEY, None)
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Bei Optionsänderung neu laden.

    Für die globalen Einstellungen aktualisiert das nur hass.data[DOMAIN][...]
    (kein Platform-Reload nötig). Raum-Entitäten lesen die globalen Werte bei
    jeder Neubewertung live aus hass.data - sie übernehmen Änderungen also
    spätestens beim nächsten 5-Minuten-Tick automatisch, auch ohne eigenen
    Reload.
    """
    if entry.data.get(CONF_IS_GLOBAL):
        hass.data[DOMAIN][entry.entry_id] = entry.data
        return
    await hass.config_entries.async_reload(entry.entry_id)
