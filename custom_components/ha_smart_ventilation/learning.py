"""Nutzungserkennung je Raum (Stufe 2, siehe CLAUDE.md Lektion 131).

Ein Raum gilt in einer Stunde als "genutzt", wenn mindestens eines seiner
Nutzungs-Signale (Licht, später Präsenz) an war und - falls Personen
hinterlegt sind - mindestens eine Person zuhause war. Gezählt wird je
Tagestyp ("wd" Werktag / "we" Wochenende bzw. freier Tag) und Stunde. Das
ist bewusst einfache Statistik, kein Machine Learning: nachvollziehbar,
lokal und ohne Trainingsphase.

Der Verlauf je Tag ist ein String aus 24 Zeichen: "1" genutzt, "0"
beobachtet und nicht genutzt, "-" nicht beobachtet.
"""

from __future__ import annotations

import bisect
import logging
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

KEEP_DAYS = 28
# Mindestanzahl beobachteter Vergleichstage derselben Art für eine Stunde,
# bevor ihr Ergebnis als belastbar gilt.
MIN_HOUR_SAMPLES = 2
BACKFILL_STEP_MINUTES = 10
_EMPTY_DAY = "-" * 24


class UsageProfile:
    """Reine Datenhaltung und Auswertung (ohne Home-Assistant-Abhängigkeit)."""

    def __init__(self, days: dict | None = None) -> None:
        self.days: dict[str, dict[str, str]] = {}
        for key, value in (days or {}).items():
            bits = value.get("h") if isinstance(value, dict) else None
            kind = value.get("t") if isinstance(value, dict) else None
            if isinstance(bits, str) and len(bits) == 24 and kind in ("wd", "we"):
                self.days[key] = {"t": kind, "h": bits}

    def to_dict(self) -> dict:
        return {"days": self.days}

    def mark(self, date_str: str, day_type: str, hour: int, used: bool) -> bool:
        """Trägt eine Live-Beobachtung ein. "1" bleibt bestehen (innerhalb
        einer Stunde zählt, dass der Raum irgendwann genutzt wurde). Gibt
        True zurück, wenn sich etwas geändert hat."""
        day = self.days.get(date_str)
        if day is None:
            day = {"t": day_type, "h": _EMPTY_DAY}
            self.days[date_str] = day
        changed = False
        if day["t"] != day_type:
            day["t"] = day_type
            changed = True
        old = day["h"][hour]
        new = "1" if used else ("0" if old == "-" else old)
        if new != old:
            day["h"] = day["h"][:hour] + new + day["h"][hour + 1 :]
            changed = True
        return changed

    def merge_backfill(self, date_str: str, day_type: str, bits: str) -> None:
        """Übernimmt rückwirkend berechnete Stunden, ohne bereits live
        beobachtete zu überschreiben."""
        day = self.days.setdefault(date_str, {"t": day_type, "h": _EMPTY_DAY})
        merged = "".join(
            old if old != "-" else new for old, new in zip(day["h"], bits)
        )
        day["h"] = merged

    def prune(self, today: str) -> None:
        keys = sorted(self.days)
        for key in keys:
            if key < _date_minus(today, KEEP_DAYS):
                del self.days[key]

    def observed_days(self) -> int:
        """Tage mit mindestens einer beobachteten Stunde."""
        return sum(1 for d in self.days.values() if d["h"] != _EMPTY_DAY)

    def hour_stats(self, day_type: str, hour: int, exclude: str | None = None) -> tuple[int, int]:
        """(genutzt, beobachtet) für diese Stunde an Tagen dieses Typs."""
        used = observed = 0
        for key, day in self.days.items():
            if day["t"] != day_type or key == exclude:
                continue
            bit = day["h"][hour]
            if bit == "-":
                continue
            observed += 1
            if bit == "1":
                used += 1
        return used, observed

    def is_used(
        self,
        day_type: str,
        hour: int,
        threshold_percent: float,
        min_days: int,
        exclude: str | None = None,
    ) -> bool | None:
        """True/False, ob die Stunde typischerweise genutzt wird; None, wenn
        noch nicht genug gelernt wurde (Mindest-Lernzeit oder zu wenige
        Vergleichstage dieser Stunde)."""
        if self.observed_days() < min_days:
            return None
        used, observed = self.hour_stats(day_type, hour, exclude)
        if observed < MIN_HOUR_SAMPLES:
            return None
        return used * 100 >= threshold_percent * observed

    def windows(
        self, day_type: str, threshold_percent: float, min_days: int
    ) -> list[tuple[int, int]] | None:
        """Zusammenhängende Nutzungszeiten als (Start, Ende) in Stunden
        (Ende exklusiv). None, solange nicht genug gelernt wurde."""
        flags = [self.is_used(day_type, h, threshold_percent, min_days) for h in range(24)]
        if all(f is None for f in flags):
            return None
        result: list[tuple[int, int]] = []
        start = None
        for hour, flag in enumerate(flags + [False]):
            if flag and start is None:
                start = hour
            elif not flag and start is not None:
                result.append((start, hour))
                start = None
        return result


def _date_minus(date_str: str, days: int) -> str:
    return (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")


def format_windows(windows: list[tuple[int, int]] | None) -> str:
    """"6–8 und 15–22 Uhr" bzw. "keine Nutzung"; "" ohne Ergebnis."""
    if windows is None:
        return ""
    if not windows:
        return "keine Nutzung"
    return " und ".join(f"{s}–{e}" for s, e in windows) + " Uhr"


def backfill_days(
    usage_rows: dict[str, list[tuple[datetime, str]]],
    person_rows: dict[str, list[tuple[datetime, str]]],
    start: datetime,
    end: datetime,
    weekend_of,
) -> dict[str, tuple[str, str]]:
    """Berechnet aus Verlaufsdaten die Stundenbits je Tag.

    `usage_rows`/`person_rows`: je Entität zeitlich sortierte (Zeit, Zustand).
    `weekend_of(date)` liefert True für Wochenende. Es wird alle
    BACKFILL_STEP_MINUTES abgetastet; Stunden vor dem frühesten bekannten
    Zustand eines Nutzungs-Signals bleiben unbeobachtet ("-").
    Rückgabe: {Datum: (Tagestyp, Bits)}."""
    firsts = [rows[0][0] for rows in usage_rows.values() if rows]
    if not firsts:
        return {}
    known_from = min(firsts)
    times = {eid: [t for t, _ in rows] for eid, rows in {**usage_rows, **person_rows}.items()}

    def state_at(eid: str, rows, moment: datetime):
        idx = bisect.bisect_right(times[eid], moment) - 1
        return rows[idx][1] if idx >= 0 else None

    hours: dict[str, list[str]] = {}
    step = timedelta(minutes=BACKFILL_STEP_MINUTES)
    moment = start
    while moment < end:
        if moment >= known_from:
            lights_on = any(
                state_at(eid, rows, moment) == "on" for eid, rows in usage_rows.items()
            )
            if person_rows:
                someone_home = any(
                    state_at(eid, rows, moment) in ("home", None, "unknown", "unavailable")
                    for eid, rows in person_rows.items()
                )
            else:
                someone_home = True
            key = moment.strftime("%Y-%m-%d")
            bits = hours.setdefault(key, list(_EMPTY_DAY))
            hour = moment.hour
            if lights_on and someone_home:
                bits[hour] = "1"
            elif bits[hour] == "-":
                bits[hour] = "0"
        moment += step
    return {
        key: ("we" if weekend_of(datetime.strptime(key, "%Y-%m-%d")) else "wd", "".join(bits))
        for key, bits in hours.items()
    }
