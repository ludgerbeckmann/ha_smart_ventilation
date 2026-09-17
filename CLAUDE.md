# CLAUDE.md – Projektkontext für Claude Code

Diese Datei fasst zusammen, was in einer ausführlichen Entwicklungs-Session
mit Claude (claude.ai-Chat) zu diesem Projekt erarbeitet wurde – gedacht als
Einstiegspunkt, damit Claude Code nicht bei null anfängt. Sie ersetzt nicht
die README.md (die ist die eigentliche Nutzerdokumentation), sondern
ergänzt sie um Dinge, die nur "hinter den Kulissen" während der Entwicklung
wichtig wurden.

## Projektüberblick

Home-Assistant Custom Integration `ha_smart_ventilation` ("Smart
Ventilation"): pro Raum ein `binary_sensor.lueften_empfohlen_<raum>`, der
anhand von Innen-/Außentemperatur und -luftfeuchtigkeit empfiehlt, ob
gelüftet werden sollte. Zusätzlich optionale Steuerung von Luftentfeuchter
und Klimaanlage, sowie drei Benachrichtigungswege (Sprachausgabe/TTS, App
Push, persistente Web-Benachrichtigung).

Aktuelle Version: siehe `custom_components/ha_smart_ventilation/manifest.json`.
GitHub: `ludgerbeckmann/ha_smart_ventilation` (Domain `ha_smart_ventilation`).

## Dateistruktur (Kurzreferenz)

```
custom_components/ha_smart_ventilation/
├── __init__.py          # Setup/Unload, automatisches Anlegen + sofortiges
│                          Neuanlegen des globalen Eintrags bei Löschung
├── binary_sensor.py     # Kernlogik: Bewertung, Benachrichtigung, Geräte
├── config_flow.py       # Config-/Options-Flow für Räume + globale Optionen
├── const.py             # Alle CONF_*/DEFAULT_*-Konstanten
├── diagnostics.py       # "Diagnose herunterladen" - Config + Live-Zustand
│                          referenzierter Sensoren, zur Ferndiagnose
├── strings.json / translations/{de,en}.json
brand/                   # Icons (Root UND custom_components/.../brand/ - beide nötig)
.github/release.yml               # Release-Notes-Kategorisierung
.github/workflows/auto-release.yml # Automatisches Tag+Release bei Versionsbump
README.md                # Vollständige Nutzerdokumentation inkl. Dashboard-Karte
```

## Zentrales Architekturprinzip: `_effective()`

Praktisch jeder konfigurierbare Wert (Schwellenwerte, Sensoren,
Benachrichtigungsmethoden) folgt demselben Muster:

1. Raum-Override, falls im Raum explizit gesetzt
2. sonst globale Einstellung aus dem Eintrag "Smart Ventilation Optionen"
   (`CONF_IS_GLOBAL: True`, feste `unique_id` über `GLOBAL_SETTINGS_UNIQUE_ID`)
3. sonst fest einprogrammierter `DEFAULT_*`-Wert

Implementiert in `binary_sensor.py` als `self._effective(key, hardcoded_default)`
(für Skalare/Booleans) und `self._effective_list(key)` (für Listen - eine
leere Liste zählt dort anders als bei `_effective()` als "nicht gesetzt").

**Wichtig:** Diese Auflösung passiert **live bei jeder Neubewertung**, nicht
einmalig beim Speichern. Änderungen an den globalen Einstellungen wirken
sich also automatisch auf alle Räume ohne eigenen Override aus, ohne dass
der Raum neu gespeichert werden muss. Das gilt inzwischen auch für die
Benachrichtigungsmethoden (Sonos/App/Persistent) - ursprünglich wurde dafür
einmalig eine `CONF_NOTIFY_METHOD`-Liste beim Speichern berechnet und
gespeichert; das wurde bewusst auf Live-Auflösung umgestellt, siehe Git-Historie.

Die globalen Einstellungen selbst werden automatisch angelegt (`__init__.py`:
`async_setup` + `async_step_import` in `config_flow.py`) und bei Löschung
über `async_remove_entry` sofort neu erzeugt - der Eintrag soll laut
Anforderung immer existieren. Home Assistant erlaubt grundsätzlich das
Löschen jedes Eintrags; das kann nicht verhindert werden, nur die sofortige
Neuerstellung danach.

## Bekannte Stolperfallen / gelernte Lektionen

**1. `py_compile` prüft keine fehlenden Imports.** Ein Name, der nur in
einer Funktion referenziert, aber nirgends importiert wird, fällt bei
reiner Syntaxprüfung nicht auf (führte einmal zu einem Bug, der ALLE Räume
lahmgelegt hat: fehlende `DEFAULT_TEMP_THRESHOLD_OPEN` etc.). Nach jeder
Änderung an `binary_sensor.py` oder `config_flow.py` zusätzlich prüfen:

```python
import re
content = open("binary_sensor.py").read()  # oder config_flow.py
import_match = re.search(r"from \.const import \(\n(.*?)\n\)", content, re.DOTALL)
imported = set(re.findall(r"[A-Z][A-Z0-9_]*", import_match.group(1)))
all_used = set(re.findall(r"\b(CONF_[A-Z0-9_]+|DEFAULT_[A-Z0-9_]+|NOTIFY_METHOD_[A-Z0-9_]+|TTS_PLAYBACK_MODE_[A-Z0-9_]+|GLOBAL_[A-Z0-9_]+|DOMAIN)\b", content))
print("Fehlend:", sorted(all_used - imported))
```

**2. Sensor-Ausfall beim Neustart ≠ "nicht konfiguriert".** Ein
konfigurierter, aber gerade `unavailable`/`unknown` gemeldeter
Außensensor (typisch während Home Assistant startet/stoppt, wenn andere
Integrationen noch laden) darf **nicht** wie "gar kein Sensor konfiguriert"
behandelt werden. Für "gar nicht konfiguriert" ist eine **permissive**
Standardannahme richtig (z. B. "Lüften hilft vermutlich"); für
"konfiguriert, aber gerade keine Daten" muss es **konservativ** sein
(kein Öffnen auf dieser Basis, Frostschutz blockiert vorsorglich) - sonst
gibt's Fehlalarme bei jedem Neustart. Siehe `frost_block`,
`outdoor_cooler_enough`, `outdoor_drier_enough` in `binary_sensor.py`.

**3. `RestoreEntity` ist Pflicht.** Ohne Zustandswiederherstellung über
Neustarts hinweg startet die Entität immer bei "aus" und erkennt bei der
ersten Neubewertung fälschlich einen Zustandswechsel (samt
Benachrichtigung), obwohl sich nichts geändert hat.

**4. Home Assistants Jinja-Sandbox blockiert mutierende Methoden.**
`list.append()`, `dict.update()` etc. funktionieren in Templates (z. B.
Dashboard-Karten) NICHT - `SecurityError: access to attribute 'append' of
'list' object is unsafe`. Strings müssen über `~`-Verkettung und bedingte
Ausdrücke aufgebaut werden, nicht über Listen mit Append-Schleifen.

**5. Home Assistants Markdown-Karte filtert das `style`-Attribut aus
eingebettetem HTML.** `<div style="height: 6px;">` oder `<hr style="...">`
werden zu wirkungslosen/leeren Standard-Tags reduziert. Funktioniert haben
stattdessen: `<mark>` (Hervorhebung, gelber Hintergrund statt frei wählbarer
Farbe), `<small>` (Schriftgröße, mehrfach verschachtelbar für kompakteren
Abstand), `<br>`, `<hr>` (ohne Attribute), und reiner Zeichentext. Noch
nicht abschließend getestet, ob es noch weitere Einschränkungen gibt -
falls Karten-Änderungen nicht wirken, zuerst prüfen ob ein Style-Attribut
im Spiel ist.

**6. YAML-Folding (`content: >` in Karten-YAML) faltet Zeilenumbrüche zu
Leerzeichen**, außer bei Zeilen mit zusätzlicher Einrückung. Mehrzeilige
Jinja-Tags (z. B. ein `{% for %}` über 3 Zeilen mit `|`-Filtern) sind daher
riskant und haben einmal zu `TemplateSyntaxError: unexpected end of
template, expected ')'` geführt. Seitdem: **ein Jinja-Tag pro Zeile**,
konsequent bei gleicher Einrückung.

**7. Vor jeder Dashboard-Karten-Änderung lokal testen**, nicht blind an den
Nutzer schicken - Home Assistant selbst steht nicht zur Verfügung, aber
eine Kombination aus `PyYAML` (simuliert das echte Card-YAML-Folding) und
`jinja2.sandbox.SandboxedEnvironment` (simuliert Home Assistants
Jinja-Einschränkungen) fängt die meisten Fehler zuverlässig ab, bevor der
Nutzer sie in der echten Oberfläche entdeckt:

```python
import yaml, jinja2.sandbox
data = yaml.safe_load(card_yaml_text)
env = jinja2.sandbox.SandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
tmpl = env.from_string(data["content"])
output = tmpl.render(states=FakeStatesObj(), now=lambda: ..., as_local=lambda dt: dt)
```

Trotz dieses Tests bleiben CSS/Rendering-Details (Abstände, Style-Filterung)
nicht zuverlässig vorhersagbar - dafür bräuchte es eine echte
Home-Assistant-Instanz.

**8. `{platzhalter}` in `strings.json`/`translations/*.json` niemals als
reinen Beispieltext in `description`/`data_description` schreiben - auch
nicht in einfachen Anführungszeichen escaped.** Home Assistants Frontend
rendert diese Texte über ICU MessageFormat (formatjs) - jedes `{wort}`
darin wird als echter, zu befüllender Platzhalter interpretiert, nicht
als Literal. Ohne übergebenen Wert zeigt die Oberfläche statt des Texts
einen Fehler wie `[formatjs Error: MISSING_VALUE] The intl string context
variable "raum" was not provided...`. Betroffen war z. B. die
Beschreibung der Benachrichtigungstexte, die `{raum}`/`{wert}`/
`{schwelle}` als Beispiel nennt.

Der ursprüngliche Fix (`'{raum}'` in einfachen Anführungszeichen, laut
ICU-Syntax reiner Text) behob zwar den formatjs-Fehler im Frontend, fiel
aber bei der ersten Einrichtung von `.github/workflows/validate.yml`
(hassfest) durch: hassfest hat eine eigene, unabhängige Regel
(`script/hassfest/translations.py`,
`RE_PLACEHOLDER_IN_SINGLE_QUOTES = re.compile(r"'{\w+}'")`), die genau
dieses `'{wort}'`-Muster als Fehler ablehnt ("the string should not
contain placeholders inside single quotes") - unabhängig davon, ob
tatsächlich `description_placeholders` übergeben werden. Ein rohes,
unescaped `{wort}` wäre für hassfest zwar erlaubt, würde aber wieder den
ursprünglichen formatjs-Fehler auslösen, da wir keine
`description_placeholders` übergeben (das sind reine Beispieltexte,
keine echten Config-Flow-Platzhalter).

**Endgültiger Fix:** ASCII-geschweifte Klammern in diesen
Beschreibungstexten komplett vermeiden und durch optisch ähnliche, aber
syntaktisch unauffällige Fullwidth-Klammern ersetzen: `｛raum｝` (U+FF5B/
FF5D) statt `{raum}` oder `'{raum}'`. Weder ICU MessageFormat noch
hassfests Regex reagieren auf diese Zeichen, sie sehen für Lesende aber
weiterhin fast identisch aus. Betrifft ausschließlich diese
Beschreibungstexte in `strings.json`/`translations/*.json` - die
eigentlichen, vom Nutzer editierbaren Benachrichtigungsvorlagen
(`DEFAULT_MSG_*` in `const.py`) sind reine Python-Strings und verwenden
`{raum}` etc. ganz normal unescaped für `str.format()`.

**Allgemeinere Lektion:** `validate.yml` (hassfest + HACS) existierte
lange nicht in diesem Repo - Änderungen an `manifest.json`, `hacs.json`
und `strings.json`/`translations/*.json` wurden vorher nie gegen die
tatsächlichen hassfest-/HACS-Schemas geprüft. Bekannte, dadurch erst
nachträglich aufgefallene Verstöße: `manifest.json`-Schlüssel müssen
nach `domain`/`name` strikt alphabetisch sortiert sein; `hacs.json`
erlaubt nur eine feste Schlüsselmenge (`content_in_root`, `country`,
`filename`, `hacs`, `hide_default_branch`, `homeassistant`,
`persistent_directory`, `render_readme`, `zip_release`, `name`) - ein
früher hinzugefügtes `domains`-Feld existiert dort schlicht nicht und
lässt die HACS-Validierung mit "extra keys not allowed" fehlschlagen;
eine Integration mit `async_setup` (siehe `__init__.py`) braucht ein
`CONFIG_SCHEMA` (hier `cv.config_entry_only_config_schema(DOMAIN)`,
da ausschließlich über den Config-Flow einrichtbar). Bei künftigen
Änderungen an diesen Dateien: `validate.yml`-Ergebnis auf `main`
abwarten/prüfen, nicht nur `py_compile`/den Import-Check.

**9. Nicht jede im Raum-Formular referenzierte Entität ist tatsächlich
an den HA-Bereich dieses Raums gebunden.** Beim Einführen der
Bereichs-basierten Sensor-Filterung (`config_flow.py`:
`_area_include_entities`) wurde die Filterung versehentlich auch auf
die **Anwesenheits-Entität** (`person`/`device_tracker`) bei den
Benachrichtigungszielen angewendet. Das ist konzeptionell falsch: eine
Person bzw. ihr Tracking-Gerät ist ortsungebunden und wird in HA so gut
wie nie einem Raum-Bereich zugeordnet - die Filterung lief in der Praxis
entweder ins Leere (Fallback auf unbeschränkt, harmlos) oder, schlimmer,
schränkte die Auswahl auf eine dort zufällig zugeordnete, aber völlig
falsche Entität ein, sodass die eigentlich gewünschte Person gar nicht
mehr wählbar war. Lektion: Vor dem Anwenden einer Bereichs-Filterung auf
ein Feld erst prüfen, ob die dahinterliegende Entität überhaupt sinnvoll
einem Raum zugeordnet sein kann (Sensoren/Lautsprecher/Aktoren: ja -
Personen/Geräte-Tracker: nein).

## Versionierung & Release

- Semantic Versioning in `manifest.json` (`version`): Patch für
  Bugfixes/Textänderungen, Minor für neue Features, Major für Breaking
  Changes. Bei **jeder** Änderung anheben.
- `.github/workflows/auto-release.yml` erstellt bei jeder Änderung an
  `manifest.json` (`version`-Feld) auf `main` automatisch Tag + GitHub
  Release mit kategorisierten Notes (`.github/release.yml`) - erfordert
  "Read and write permissions" unter Settings → Actions → General
  (einmalig einzurichten, sonst 403-Fehler).

## Offene/mögliche nächste Schritte

- Home-Assistant-Brands-Repo-Aufnahme / offizielle HACS-Aufnahme (Prozess
  wurde besprochen, aber noch nicht durchgeführt - siehe README für Details)
- Konfigurierbare Benachrichtigungstexte sind seit Version 0.27.0 nur
  **global** einstellbar, nicht pro Raum - Codepfad (`_effective()`) würde
  einen Raum-Override ohne weitere Änderung bereits unterstützen, dafür
  fehlt aktuell nur die UI im Raum-Formular.
- Dashboard-Karte (siehe README, Abschnitt "Attribute für eine
  Statusübersicht") ist bewusst NICHT Teil des Integrations-Codes, sondern
  wird separat vom Nutzer in eine Home-Assistant-Dashboard-Karte
  eingefügt - Änderungen daran erfordern keinen Versionsbump/kein Release.
