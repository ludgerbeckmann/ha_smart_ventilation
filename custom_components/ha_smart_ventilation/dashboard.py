"""Dashboard-Darstellung: Einstellungen für das Bubble-Card-Modul
"climate_status" und Installation der Moduldatei.

Die Einstellungen kommen aus den allgemeinen Einstellungen ("Smart Climate
Optionen", Abschnitt "Dashboard-Darstellung") und werden als fertige
CSS-Werte in den Attributen des Sensors "Smart Climate Darstellung"
bereitgestellt. Das Modul liest sie live aus hass.states; fehlt ein Wert,
gilt der Standard im Modul (siehe bubble/climate_status.yaml).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import (
    CONF_DASH_BAR_WIDTH,
    CONF_DASH_BORDER_WIDTH,
    CONF_DASH_COLOR_COLD,
    CONF_DASH_COLOR_COMFORT,
    CONF_DASH_COLOR_COVER,
    CONF_DASH_COLOR_ECO,
    CONF_DASH_COLOR_HOT,
    CONF_DASH_COLOR_PROTECTION,
    CONF_DASH_COLOR_STANDBY,
    CONF_DASH_COLOR_SUMMER,
    CONF_DASH_COLOR_TINT_ACTION,
    CONF_DASH_COLOR_TINT_HINT,
    CONF_DASH_COLOR_WARM,
    CONF_DASH_COVER_BAR,
    CONF_DASH_COVER_SIDE,
    CONF_DASH_CYCLE,
    CONF_DASH_EXTRA_1,
    CONF_DASH_EXTRA_2,
    CONF_DASH_EXTRA_SIZE,
    CONF_DASH_HEAT_BAR,
    CONF_DASH_HEAT_SIDE,
    CONF_DASH_LINE_HEIGHT,
    CONF_DASH_TINT,
    CONF_SUMMER_MODE_SWITCH_ENTITY,
    DASH_EXTRA_OPTIONS,
    DASH_SIDE_OPTIONS,
    DEFAULT_DASH_BAR_WIDTH,
    DEFAULT_DASH_BORDER_WIDTH,
    DEFAULT_DASH_COVER_BAR,
    DEFAULT_DASH_COVER_SIDE,
    DEFAULT_DASH_CYCLE,
    DEFAULT_DASH_EXTRA_1,
    DEFAULT_DASH_EXTRA_2,
    DEFAULT_DASH_EXTRA_SIZE,
    DEFAULT_DASH_HEAT_BAR,
    DEFAULT_DASH_HEAT_SIDE,
    DEFAULT_DASH_LINE_HEIGHT,
    DEFAULT_DASH_TINT,
)

_LOGGER = logging.getLogger(__name__)

MODULE_ID = "climate_status"
MODULE_FILENAME = f"{MODULE_ID}.yaml"
MODULE_TEMPLATE = Path(__file__).parent / "bubble" / MODULE_FILENAME
# Muss zur "version:"-Zeile in bubble/climate_status.yaml passen (Test prüft es).
MODULE_VERSION_LABEL = "v3.0"

# Deckkraft des Hintergrunds (fest, wie im bisherigen Modul)
_TINT_HINT_ALPHA = 0.2
_TINT_ACTION_ALPHA = 0.25

# Farbfeld -> (Attributname, Deckkraft oder None)
_COLOR_ATTRS = (
    (CONF_DASH_COLOR_COMFORT, "farbe_komfort", None),
    (CONF_DASH_COLOR_STANDBY, "farbe_standby", None),
    (CONF_DASH_COLOR_ECO, "farbe_eco", None),
    (CONF_DASH_COLOR_PROTECTION, "farbe_gebaeudeschutz", None),
    (CONF_DASH_COLOR_SUMMER, "farbe_sommer", None),
    (CONF_DASH_COLOR_HOT, "farbe_heiss", None),
    (CONF_DASH_COLOR_WARM, "farbe_warm", None),
    (CONF_DASH_COLOR_COLD, "farbe_kalt", None),
    (CONF_DASH_COLOR_COVER, "farbe_rollladen", None),
    (CONF_DASH_COLOR_TINT_HINT, "farbe_hinweis", _TINT_HINT_ALPHA),
    (CONF_DASH_COLOR_TINT_ACTION, "farbe_handlungsbedarf", _TINT_ACTION_ALPHA),
)


def _css_color(value, alpha: float | None) -> str | None:
    """Wandelt einen Farbwähler-Wert ([r, g, b]) in einen CSS-Wert um;
    None bei leer/ungültig (dann gilt der Standard des Moduls)."""
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None
    try:
        r, g, b = (max(0, min(255, int(round(float(v))))) for v in value)
    except (TypeError, ValueError):
        return None
    if alpha is None:
        return f"rgb({r}, {g}, {b})"
    return f"rgba({r}, {g}, {b}, {alpha})"


def _num(value, default, minimum, maximum) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    return max(minimum, min(maximum, number))


def _fmt(number: float) -> str:
    return str(int(number)) if float(number).is_integer() else str(number)


def build_dashboard_attributes(data: dict) -> dict:
    """Baut die Attribute des Darstellungs-Sensors aus den allgemeinen
    Einstellungen. Alle Werte sind fertige CSS-Werte bzw. Schlüsselwörter
    (Booleans als "1"/"0"); nicht gesetzte Farben fehlen komplett."""
    heat_side = data.get(CONF_DASH_HEAT_SIDE, DEFAULT_DASH_HEAT_SIDE)
    cover_side = data.get(CONF_DASH_COVER_SIDE, DEFAULT_DASH_COVER_SIDE)
    if heat_side not in DASH_SIDE_OPTIONS:
        heat_side = DEFAULT_DASH_HEAT_SIDE
    if cover_side not in DASH_SIDE_OPTIONS:
        cover_side = DEFAULT_DASH_COVER_SIDE

    extra_1 = data.get(CONF_DASH_EXTRA_1, DEFAULT_DASH_EXTRA_1)
    extra_2 = data.get(CONF_DASH_EXTRA_2, DEFAULT_DASH_EXTRA_2)
    if extra_1 not in DASH_EXTRA_OPTIONS:
        extra_1 = DEFAULT_DASH_EXTRA_1
    if extra_2 not in DASH_EXTRA_OPTIONS:
        extra_2 = DEFAULT_DASH_EXTRA_2
    if extra_1 != "off" and extra_1 == extra_2:
        # derselbe Wert zweimal ergäbe zwei identische Phasen
        extra_2 = "off"

    def flag(key: str, default: bool) -> str:
        return "1" if data.get(key, default) else "0"

    attrs: dict = {
        "hintergrund": flag(CONF_DASH_TINT, DEFAULT_DASH_TINT),
        "balken_heizung": flag(CONF_DASH_HEAT_BAR, DEFAULT_DASH_HEAT_BAR),
        "balken_rollladen": flag(CONF_DASH_COVER_BAR, DEFAULT_DASH_COVER_BAR),
        "balken_heizung_seite": "rechts" if heat_side == "right" else "links",
        "balken_rollladen_seite": "rechts" if cover_side == "right" else "links",
        "balkenbreite": f"{_fmt(_num(data.get(CONF_DASH_BAR_WIDTH), DEFAULT_DASH_BAR_WIDTH, 2, 24))}px",
        "rahmenbreite": f"{_fmt(_num(data.get(CONF_DASH_BORDER_WIDTH), DEFAULT_DASH_BORDER_WIDTH, 0, 6))}px",
        "zeilenhoehe": f"{_fmt(_num(data.get(CONF_DASH_LINE_HEIGHT), DEFAULT_DASH_LINE_HEIGHT, 20, 120))}px",
        "schrift_zusatz": f"{_fmt(_num(data.get(CONF_DASH_EXTRA_SIZE), DEFAULT_DASH_EXTRA_SIZE, 40, 150) / 100)}em",
        "wechselintervall": f"{_fmt(_num(data.get(CONF_DASH_CYCLE), DEFAULT_DASH_CYCLE, 4, 60))}s",
        "wechselwert_1": extra_1,
        "wechselwert_2": extra_2,
    }
    for key, attr, alpha in _COLOR_ATTRS:
        css = _css_color(data.get(key), alpha)
        if css:
            attrs[attr] = css
    summer = data.get(CONF_SUMMER_MODE_SWITCH_ENTITY)
    if summer:
        attrs["sommerbetrieb_schalter"] = summer
    return attrs


def module_version_tuple(text: str) -> tuple[int, ...] | None:
    """Liest die Modulversion ("version: v3.0") aus dem YAML-Text."""
    match = re.search(r"^\s{0,4}version:\s*['\"]?v?(\d+(?:\.\d+)*)", text, re.MULTILINE)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def install_module_file(config_dir: str, template_text: str) -> str:
    """Schreibt das Modul nach <config>/bubble_card/modules/. Läuft im
    Executor. Liefert eine kurze Statusmeldung (für das Log):
    "no_folder", "up_to_date", "unreadable", "installed" oder "updated"."""
    modules_dir = Path(config_dir) / "bubble_card" / "modules"
    if not modules_dir.is_dir():
        return "no_folder"
    target = modules_dir / MODULE_FILENAME
    new_version = module_version_tuple(template_text)
    status = "installed"
    if target.exists():
        try:
            old_text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return "unreadable"
        old_version = module_version_tuple(old_text)
        if old_version is not None and new_version is not None and old_version >= new_version:
            return "up_to_date"
        # Vorherige Fassung einmalig sichern (außerhalb von modules/, damit
        # Bubble Card sie nicht als Modul einliest).
        suffix = ".".join(str(p) for p in old_version) if old_version else "alt"
        backup = modules_dir.parent / f"{MODULE_ID}_v{suffix}.yaml.bak"
        if not backup.exists():
            backup.write_text(old_text, encoding="utf-8")
        status = "updated"
    tmp = target.with_suffix(".yaml.tmp")
    tmp.write_text(template_text, encoding="utf-8")
    tmp.replace(target)
    return status


async def async_install_bubble_module(hass: HomeAssistant) -> None:
    """Legt die mitgelieferte Moduldatei an bzw. aktualisiert sie (nur wenn
    der Ordner von Bubble Card Tools existiert und die vorhandene Version
    älter ist). Jeder Fehler wird nur geloggt."""
    try:
        template_text = await hass.async_add_executor_job(
            MODULE_TEMPLATE.read_text, "utf-8"
        )
        status = await hass.async_add_executor_job(
            install_module_file, hass.config.config_dir, template_text
        )
    except Exception:  # noqa: BLE001 - darf das Setup nie verhindern
        _LOGGER.warning("Konnte das Bubble-Card-Modul nicht installieren", exc_info=True)
        return
    if status in ("installed", "updated"):
        _LOGGER.info(
            "Bubble-Card-Modul %s %s - bei Bedarf Browser/App neu laden",
            MODULE_ID,
            "angelegt" if status == "installed" else "aktualisiert",
        )
    else:
        _LOGGER.debug("Bubble-Card-Modul: %s", status)
