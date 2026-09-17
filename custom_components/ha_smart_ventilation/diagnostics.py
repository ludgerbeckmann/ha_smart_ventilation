"""Diagnostics-Unterstützung für Smart Ventilation.

Über "Diagnose herunterladen" im Drei-Punkte-Menü eines Eintrags
(Einstellungen → Geräte & Dienste → Smart Ventilation) als JSON-Datei
abrufbar. Liefert die Konfiguration dieses Eintrags (personenbezogene
Anwesenheits-/Notify-Ziele bereinigt) sowie - bei einem Raum - zusätzlich
den aktuellen Entitäts-Zustand samt aller Attribute und eine
Momentaufnahme aller referenzierten Roh-Sensoren (inkl. der globalen
Außensensoren). Gedacht, um Flacker-/Benachrichtigungsprobleme anhand
einer heruntergeladenen Datei nachvollziehen zu können, ohne dass Werte
oder Log-Auszüge von Hand abgeschrieben werden müssen.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_CO2_ENTITY,
    CONF_HUMIDITY_ENTITY,
    CONF_IS_GLOBAL,
    CONF_MOBILE_NOTIFY_ENTITY,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMP_ENTITY,
    CONF_PRESENCE_ENTITY,
    CONF_TEMP_SOURCE_ENTITY,
    CONF_WINDOW_ENTITY,
    DOMAIN,
    GLOBAL_ENTRY_ID_KEY,
)

# Personenbezogene Ziel-Entitäten (verraten, welche Person/welches Gerät
# hinterlegt ist) - alle anderen Config-Werte (Schwellenwerte,
# Sensor-Entity-IDs, Raumname) werden für die Ferndiagnose gebraucht und
# sind nicht in vergleichbarer Weise sensibel.
TO_REDACT = {CONF_PRESENCE_ENTITY, CONF_MOBILE_NOTIFY_ENTITY}


def _snapshot(hass: HomeAssistant, entity_id: str | None) -> dict[str, Any] | None:
    """Momentaufnahme (Zustand + Attribute) einer referenzierten Entität -
    None, falls keine hinterlegt ist. Zeigt bei einem "unavailable"/
    "unknown"-Sensor auch dessen Attribute, statt nur den davon
    abgeleiteten, bereits von Smart Ventilation verarbeiteten Wert."""
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return {"entity_id": entity_id, "state": None, "attributes": None}
    return {
        "entity_id": entity_id,
        "state": state.state,
        "attributes": dict(state.attributes),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Diagnose-Daten für einen einzelnen Eintrag (Raum oder die
    globalen Einstellungen)."""
    diagnostics: dict[str, Any] = {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
    }

    if entry.data.get(CONF_IS_GLOBAL):
        # Die globalen Einstellungen erzeugen keine eigene Entität - hier
        # ist die (bereinigte) Konfiguration bereits die vollständige
        # Diagnose.
        return diagnostics

    entity_id = next(
        (
            reg_entry.entity_id
            for reg_entry in er.async_entries_for_config_entry(
                er.async_get(hass), entry.entry_id
            )
        ),
        None,
    )
    entity_state = hass.states.get(entity_id) if entity_id else None
    diagnostics["entity"] = (
        {
            "entity_id": entity_id,
            "state": entity_state.state,
            "attributes": dict(entity_state.attributes),
        }
        if entity_state is not None
        else None
    )

    # Außentemperatur/-luftfeuchtigkeit stehen nur in den globalen
    # Einstellungen, nicht im Raum-Eintrag selbst (siehe binary_sensor.py:
    # _global_config()) - hier über denselben hass.data-Umweg nachschlagen.
    global_entry_id = hass.data.get(DOMAIN, {}).get(GLOBAL_ENTRY_ID_KEY)
    global_data = (
        hass.data.get(DOMAIN, {}).get(global_entry_id, {}) if global_entry_id else {}
    )

    config = entry.data
    diagnostics["referenced_sensors"] = {
        "temperature_source": _snapshot(hass, config.get(CONF_TEMP_SOURCE_ENTITY)),
        "humidity": _snapshot(hass, config.get(CONF_HUMIDITY_ENTITY)),
        "co2": _snapshot(hass, config.get(CONF_CO2_ENTITY)),
        "window": _snapshot(hass, config.get(CONF_WINDOW_ENTITY)),
        "outdoor_temperature": _snapshot(
            hass, global_data.get(CONF_OUTDOOR_TEMP_ENTITY)
        ),
        "outdoor_humidity": _snapshot(
            hass, global_data.get(CONF_OUTDOOR_HUMIDITY_ENTITY)
        ),
    }

    return diagnostics
