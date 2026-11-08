# Smart Climate für Home Assistant

[![Validate](https://github.com/ludgerbeckmann/ha_smart_ventilation/actions/workflows/validate.yml/badge.svg)](https://github.com/ludgerbeckmann/ha_smart_ventilation/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/ludgerbeckmann/ha_smart_ventilation.svg)](https://github.com/ludgerbeckmann/ha_smart_ventilation/releases/)
[![GitHub license](https://img.shields.io/github/license/ludgerbeckmann/ha_smart_ventilation.svg)](https://github.com/ludgerbeckmann/ha_smart_ventilation/blob/main/LICENSE)

Eine Custom Integration für Home Assistant, die pro Raum das Raumklima
überwacht: Sie empfiehlt, **wann gelüftet werden sollte** (Innen-/Außentemperatur,
Luftfeuchtigkeit, CO2), steuert optional **Luftentfeuchter, Klimaanlage und
Heizung** und zeigt alles in einer **Dashboard-Karte** an. Bei Änderungen
benachrichtigt sie per **Sprachausgabe** (z. B. Sonos oder jede andere
`media_player`-Entität), **App-Push** und/oder **persistenter Benachrichtigung**.

## Was sie kann

- **Lüftungsempfehlung je Raum** (`binary_sensor`): öffnen oder schließen, mit
  Frost-/Hitzeschutz, Außenluft-Vergleich (absolute Luftfeuchtigkeit) und
  Fensterkontakt-Abgleich
- **Benachrichtigungen** per Sprachausgabe, Push und Web - mit Nachtruhe,
  Erinnerung und automatischem Auflösen
- **Duscherkennung** und Ansage bei zu langer Dusche
- **Luftentfeuchter und Klimaanlage** automatisch schalten (auch abhängig von
  Photovoltaik-Einspeisung)
- **Heizung** mit Comfort-/Standby-/Nacht-Profilen, Zeitplan, Presets,
  Anwesenheit, Fensterpause, Sommerbetrieb, Raumtypen und gelernter Raumnutzung
- **Zusätzliche Sensoren**: absolute Luftfeuchtigkeit, Taupunkt, Raumstatus (Ampel)
- **Dashboard-Karte** (wird automatisch mitgeliefert) mit Raum-Dialog sowie ein
  optionales **Bubble-Card-Modul**

## Installation

### Über HACS (empfohlen)

1. HACS öffnen und nach **Smart Climate** suchen. Falls die Integration dort
   noch nicht gelistet ist: Menü (⋮) → *Benutzerdefinierte Repositories* →
   `https://github.com/ludgerbeckmann/ha_smart_ventilation`, Kategorie
   **Integration**
2. "Smart Climate" installieren
3. Home Assistant neu starten

### Manuell

1. Ordner `custom_components/ha_smart_ventilation` in den
   Home-Assistant-Konfigurationsordner kopieren
   (`<config>/custom_components/ha_smart_ventilation`)
2. Home Assistant neu starten

## Schnellstart

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Smart Climate**.
   Beim ersten Start entsteht automatisch der Eintrag **"- Smart Climate Optionen -"**
   mit den globalen Einstellungen (Außensensoren, Schwellenwerte, Benachrichtigungen).
   Dort zuerst die Außentemperatur und -luftfeuchtigkeit eintragen.
2. **Raum hinzufügen**: Name, Innentemperatur-Quelle und optional Luftfeuchtigkeit,
   CO2, Fensterkontakt und Geräte wählen. Alles, was du im Raum leer lässt,
   übernimmt die globale Einstellung.
3. **Dashboard**: Die Karte `custom:smart-climate-card` wird automatisch
   registriert. Im Dashboard-Editor eine Karte hinzufügen und **Custom: Smart Climate Karte** wählen.
   Nach einem Update die Companion-App vollständig neu starten (Cache).
4. Optional: Bubble-Card-Modul, Heizung, Duscherkennung und Raumtypen einrichten.

## Dokumentation

| Thema | Inhalt |
|---|---|
| [Einrichtung und Einstellungen](docs/einrichtung.md) | Raum hinzufügen, globale Einstellungen, Bearbeiten, HA-Bereich |
| [Logik im Detail](docs/logik.md) | Wann wird geöffnet/geschlossen, Frost-/Hitzeschutz, Duscherkennung, absolute vs. relative Luftfeuchtigkeit |
| [Geräte und Heizung](docs/geraete-und-heizung.md) | Luftentfeuchter, Klimaanlage, Heizung, Sommer-/Winterbetrieb, Zeitplan, Raumtypen, gelernte Nutzung |
| [Sensoren und Attribute](docs/sensoren.md) | Entitäten pro Raum, Taupunkt, Raumstatus, Attribute für eigene Automationen |
| [Dashboard-Karte und Bubble-Card-Modul](docs/dashboard.md) | Aufbau, Farben, Raum-Dialog, Bubble-Card-Modul |
| [Fehlersuche und Hinweise](docs/fehlersuche.md) | Diagnose herunterladen, häufige Probleme, Hinweise |
| [Entwicklung](docs/entwicklung.md) | Releases und Workflows (nur für Maintainer) |

## Hilfe und Fehler melden

Fehler und Wünsche bitte als [Issue](https://github.com/ludgerbeckmann/ha_smart_ventilation/issues)
melden - am besten mit der Diagnose-Datei (siehe [Fehlersuche](docs/fehlersuche.md)).

Lizenz: [MIT](LICENSE)
