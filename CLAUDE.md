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
eingebettetem HTML - andere, rein präsentative Attribute/Tags dagegen
nicht.** `<div style="height: 6px;">` oder `<hr style="...">` werden zu
wirkungslosen/leeren Standard-Tags reduziert. Funktioniert haben
stattdessen: `<mark>` (Hervorhebung, gelber Hintergrund statt frei wählbarer
Farbe), `<small>` (Schriftgröße, mehrfach verschachtelbar für kompakteren
Abstand), `<br>`, `<hr>` (ohne Attribute), reiner Zeichentext, sowie -
vom Nutzer in der echten Oberfläche bestätigt - `<font color="red">`
(frei wählbare Textfarbe über das alte, rein präsentative `color`-Attribut,
das offenbar NICHT wie `style` gefiltert wird) und `<strong>` (Fettschrift,
reines Standard-Tag ohne jedes Attribut). Noch
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

**10. Ein Architektur-Refactor macht bereits gespeicherte Config-Entry-Daten
nicht automatisch mit.** Die Umstellung von der historischen
`CONF_NOTIFY_METHOD`-Liste (einmalig beim Speichern berechnet) auf die
live über `_effective()` aufgelösten `CONF_MOBILE_ENABLED`/
`CONF_PERSISTENT_ENABLED`-Felder hat für Räume, die seitdem nie neu
gespeichert wurden, keinen der beiden neuen Schlüssel gesetzt - `_effective()`
fand dafür weder einen Raum- noch einen globalen Wert und fiel auf den
fest einprogrammierten Standard `False` zurück. Ergebnis: Räume mit
weiterhin korrekt konfiguriertem Benachrichtigungsziel (`mobile_targets`)
blieben stumm, ohne dass Config-Flow/Options-Flow oder die Anzeige einen
Hinweis darauf gaben - das alte Feld existierte im gespeicherten
Config-Entry einfach unverändert weiter, nur wird es vom neuen Code
nirgends mehr gelesen. Gefunden über eine vom Nutzer hochgeladene
Diagnose-Datei (`entry_data.notify_method` vorhanden, `mobile_enabled`
fehlend). Fix: `_migrate_legacy_notify_method()` in `__init__.py`, läuft
bei jedem `async_setup_entry` einmalig pro Eintrag (danach wirkungslos, da
`CONF_NOTIFY_METHOD` entfernt wird). Lektion: Bei jeder Umstellung von
einem "einmalig berechnet und gespeichert" - auf ein "live aufgelöst"-Muster
(oder allgemein bei jedem Feld-Rename/-Ersatz) explizit prüfen, ob
bestehende, nie neu gespeicherte Einträge dadurch stillschweigend in einen
anderen Zustand fallen - und wenn ja, eine Migration in `async_setup_entry`
ergänzen, nicht nur auf "wird beim nächsten Speichern schon aktualisiert"
hoffen.

**11. Ein einzelner Grund-Code darf nicht zwei unterschiedliche Ursachen
verdecken.** `frost_block` (siehe Lektion 2) blockiert absichtlich
gleichermaßen bei tatsächlich niedriger Außentemperatur UND bei
komplett fehlendem Messwert (Sensor `unavailable`/`unknown`) - beides
sollte weiterhin identisch vorsorglich schließen (das ist richtig so).
Der resultierende `reason`/`letzter_grund`-Wert war aber in beiden
Fällen identisch `"frost"`, wodurch Benachrichtigung und Dashboard eine
konkrete Frostgefahr meldeten ("die Außentemperatur liegt mit {wert}
auf/unter der Frostschutz-Grenze"), obwohl in Wahrheit gar kein
Messwert vorlag - irreführend, gerade weil dieser Fall typischerweise
durch einen Neustart ausgelöst wird (siehe Lektion 2) und die
Außentemperatur zu dem Zeitpunkt oft gar nicht niedrig ist. Erster Fix (0.34.0): `frost_sensor_missing` als eigene Variable neben
`frost_block` eingeführt, die zwei einzelnen Fälle in unterschiedliche
`reason`-Werte aufgeteilt (`"frost"` vs. `"frost_unavailable"`) und dafür
einen eigenen, ehrlichen Benachrichtigungstext
(`CONF_MSG_CLOSE_FROST_UNAVAILABLE`) sowie einen eigenen
Dashboard-Auslöser-Text ergänzt.

Nutzer-Feedback nach diesem ersten Fix: auch der eigene, "ehrliche" Text
war noch zu viel - ein Auslöser-Eintrag ("Frostschutz (Sensor n.
verfügbar)") in der Empfehlungs-Tabelle bei jedem Neustart wurde weiterhin
als störendes Rauschen empfunden, nicht als nützliche Information. Zweiter,
endgültiger Fix: `frost_sensor_missing` löst zwar weiterhin das
vorsorgliche Schließen aus (Sicherheit bleibt unverändert bestehen), aber
`_last_reason` wird für diesen Fall explizit auf `None` gesetzt statt auf
`"frost_unavailable"`, und die Benachrichtigung wird komplett unterdrückt
(`silent_frost_close` in `binary_sensor.py`) - dadurch verschwundene, jetzt
tote Textbausteine (`CONF_MSG_CLOSE_FROST_UNAVAILABLE`,
`msg_close_frost_unavailable` in `strings.json`/`translations/*.json`,
das zugehörige Optionsfeld) wurden komplett entfernt statt nur
unbenutzt liegen zu lassen. Lektion: Wann immer ein und dieselbe Aktion
(hier: schließen) aus einem "echten" Grund und einem "wir wissen es
nicht, spielen aber sicher"-Grund ausgelöst werden kann, muss die
konservative Sicherheitsmaßnahme selbst (hier: das Schließen)
unverändert bestehen bleiben - ob sie aber überhaupt eine sichtbare
Meldung/einen Tabelleneintrag verdient, ist eine **separate** Frage, die
der Nutzer entscheidet, nicht automatisch mit "ja, aber ehrlich
formuliert" zu beantworten ist.

**Nachtrag (0.35.1), erneutes Beispiel für Lektion 10:** Direkt nach dem
zweiten Fix meldete der Nutzer, der alte Auslöser-Text erscheine
weiterhin. Ursache: `letzter_grund="frost_unavailable"` war in genau
diesem Raum schon **vor** dem Update gespeichert worden, und
`_last_reason` wird ausschließlich innerhalb des
Zustandswechsel-Zweigs (`if new_state != self._attr_is_on:`) neu
berechnet. Bleibt der Sensor weiterhin dauerhaft nicht verfügbar, bleibt
der Raum durchgehend "aus" - es gibt also gar keinen neuen
Zustandswechsel, der den veralteten Wert überschreiben könnte. Bei jedem
Neustart stellt `RestoreEntity` (`async_added_to_hass`) den alten,
längst obsoleten Attributwert einfach unverändert wieder her. Fix:
Beim Wiederherstellen wird der Wert `"frost_unavailable"` explizit
ausgeschlossen (wie ein nicht vorhandenes Attribut behandelt, `_last_reason`
bleibt `None`). Lektion, die Lektion 10 präzisiert: Es reicht nicht, nur
Felder zu betrachten, die komplett fehlen können ("nie neu gespeichert,
seit der Rename passiert ist") - auch ein Wert, der schlicht **niemals
neu berechnet wird**, weil die zugehörige Bedingung (hier: ein
Zustandswechsel) einfach nicht eintritt, bleibt für immer auf dem
Stand vor dem Update stehen. Bei jedem entfernten `reason`-/Code-Wert
diesen Fall explizit prüfen: kann die Entität in einem Zustand
"stecken bleiben", in dem der alte Wert nie neu geschrieben wird?

**12. Frost-/Hitzeschutz brauchte eine Debounce-Zeit für das erzwungene
Schließen, nicht nur für das Blockieren des Öffnens (0.36.0).** Nutzer-
Meldung: der Frostschutz schließt "zu schnell" - Nachfrage ergab, dass die
tatsächliche Außentemperatur nachts noch weit von der Frostschutz-Grenze
entfernt war, ein Flackern nahe der Schwelle also ausgeschlossen werden
konnte. Wahrscheinlichste Ursache: ein einzelner unplausibler
Ausreißer-Messwert einer der (hier: drei kombinierten) Außentemperatur-
Quellen, auf den `frost_block`/`close_by_frost` bis dahin ungefiltert und
sofort reagierte - jeder einzelne Messwert unterhalb der Grenze reichte,
um eine bereits aktive Öffnen-Empfehlung samt Benachrichtigung zu beenden.
Die eigentliche Fehlerursache ließ sich nachträglich nicht mehr zweifelsfrei
belegen (weder das HA-Systemlog noch der Logbuch-Export enthielten den
fraglichen Zeitpunkt - Logbuch protokolliert bei `device_class: opening`
grundsätzlich keine "Schließen"-Ereignisse, nur "Öffnen"), das Debounce-
Konzept wurde aber unabhängig davon als sinnvolle generelle Absicherung
umgesetzt.

Fix: `_frost_cold_since` (Zeitstempel, analog zum bereits vorhandenen
Muster `_dehumidifier_low_power_since`/`_ac_low_power_since` für die
Einspeiseleistung) verfolgt, seit wann die Außentemperatur *ununterbrochen*
tatsächlich (nicht: fehlend) auf/unter der Frostschutz-Grenze liegt. Das
erzwungene Schließen (`close_by_frost`) greift für einen echten Messwert
erst, wenn das neue, konfigurierbare `CONF_FROST_DEBOUNCE_MINUTES`
(Standard 10 Minuten, 0 = deaktiviert, per `_effective()` raum- oder
global überschreibbar) erreicht ist. Bewusst **nicht** debounct: das reine
Blockieren einer neuen Öffnen-Empfehlung (`frost_block`, bleibt sofort
wirksam - konservativ zu bleiben ist risikofrei) und der Fall eines
fehlenden Sensors (`frost_sensor_missing`, bleibt ebenfalls sofort und
weiterhin stumm wirksam, siehe Lektion 11 - dort gibt es keinen Messwert,
der "anhalten" könnte). Lektion: Ein Debounce/Hysterese-Bedarf betrifft oft
nur eine von mehreren Verwendungen ein und derselben Bedingung
(hier: `frost_block`) - die konservative "Öffnen blockieren"-Seite einer
Sicherheitsbedingung braucht i. d. R. keine Verzögerung (das Risiko eines
zu späten Blockierens ist einseitig), während die aktive "bereits offenen
Zustand beenden"-Seite von einem einzelnen Ausreißer-Messwert unnötig
Fehlalarme auslösen kann - beide Seiten sollten daher nicht automatisch
denselben Debounce-Wert erben, sondern einzeln bewertet werden.

**Nachtrag (0.36.1), Korrektur der eigenen Lektion 12:** Nutzer-Meldung,
mehrere Räume seien nach einem HA-Neustart wieder "auf Frostschutz"
gegangen - mit Diagnose-Beleg (aktuelle Außentemperatur 13,8 °C, weit über
der Grenze, Auslöser trotzdem "Frostschutz" mit Zeitstempel exakt zur
Neustart-Zeit). Der ursprüngliche Fix (0.36.0) hatte den fehlenden-Sensor-
Fall bewusst OHNE Debounce gelassen ("dort gibt es keinen Messwert, der
anhalten könnte") - das war zu kurz gedacht: Man kann sehr wohl verfolgen,
seit wann ein Sensor ununterbrochen fehlt, genau wie bei einem echten
Messwert. Ein HA-Neustart ist zudem der typische Moment, in dem der
Außensensor kurzzeitig noch lädt (siehe Lektion 2) - also genau der Fall,
den der fehlende-Sensor-Zweig unverzögert durchließ und der (bei mehreren
Räumen mit demselben globalen Außensensor) gleich mehrere Räume auf einmal
betraf. Fix: `_frost_cold_since` zu `_frost_block_since` verallgemeinert -
verfolgt jetzt, seit wann `frost_block` (die Bedingung, die sowohl einen
echten niedrigen Messwert als auch einen fehlenden Sensor abdeckt)
ununterbrochen aktiv ist, statt zwei getrennte Fälle mit unterschiedlicher
Verzögerung zu behandeln. `frost_sensor_missing` wird weiterhin separat
ausgewertet, aber nur noch dafür, ob das schließlich erzwungene Schließen
einen Auslöser-Eintrag bekommt (echter Messwert) oder stumm bleibt
(fehlender Sensor) - nicht mehr dafür, ob überhaupt gewartet wird.
Lektion, die Lektion 12 präzisiert: "Es gibt hier keinen Wert, der
anhalten könnte" ist kein Grund, einen Debounce auszulassen - man kann
genauso gut verfolgen, wie lange ein *Zustand* (hier: "kein Wert
vorhanden") anhält, wie man einen *Messwert* verfolgt. Vor jeder
bewussten Asymmetrie zwischen zwei Fällen derselben Bedingung noch einmal
prüfen, ob die Begründung wirklich zwei unterschiedliche Risikoprofile
beschreibt - oder nur eine vermeidbare Vereinfachung ist.

**13. Ein "historischer Grund" ist nicht dasselbe wie ein "aktuell
gültiger Grund" - und die Dashboard-Karte hatte das lange durcheinander
geworfen (0.37.0).** Direkt im Anschluss an Lektion 12 meldete der Nutzer
(Raum Küche): Auslöser zeigte "Frostschutz" mit Zeitstempel exakt zum
letzten Neustart, obwohl die aktuelle Außentemperatur (14,3 °C) meilenweit
über der Frostschutz-Grenze lag - der Debounce-Fix allein hatte das
zugrundeliegende Anzeige-Problem also nicht gelöst, nur seine Häufigkeit
verringert. Ursache: `letzter_grund` wird ausschließlich beim tatsächlichen
Zustandswechsel geschrieben (siehe Lektionen 10/11) und bleibt danach exakt
so stehen, bis der nächste echte Wechsel passiert - unabhängig davon, ob
die ursprüngliche Ursache (hier: ein einzelner Ausreißer-Messwert oder eine
kurze Sensor-Nichtverfügbarkeit beim Neustart, siehe Lektion 12) längst
nicht mehr zutrifft. Für Temperatur/Luftfeuchtigkeit/CO2 wurde das bereits
in einem früheren Schritt behoben (Auslöser + Hervorhebung live aus den
angezeigten Werten/Schwellen berechnet, nicht aus `letzter_grund`) - für
Frost-/Hitzeschutz fehlte dafür aber bis dahin schlicht die Datenbasis: die
Frostschutz-/Hitzeschutz-Grenze war kein Dashboard-Attribut, die Karte
konnte "ist es aktuell wirklich kalt/heiß genug" also gar nicht selbst
nachrechnen und musste sich auf die (potenziell veraltete) Historie
verlassen. Fix: `schwelle_frostschutz`/`schwelle_hitzeschutz` als neue,
schlanke Attribute ergänzt (nur die beiden Zahlenwerte, kein zusätzlicher
Zustand) - die Karte prüft Frost/Hitze jetzt genauso live wie die anderen
drei Größen (aktuelle Außentemperatur gegen die neue Schwelle), in der
korrekten Priorität (Frost/Hitze vor Luftfeuchtigkeit/CO2/Temperatur, wie
in `binary_sensor.py`). `letzter_grund` bleibt nur noch Rückfallwert für
die zwei Fälle, die sich wirklich nicht aus angezeigten Werten
nachrechnen lassen (Winter-Höchstdauer, Sommer-Fall - dafür fehlen
Toleranz-Marge bzw. bisherige Öffnungsdauer als Attribut; das könnte man
grundsätzlich ebenso ergänzen, wurde hier aber als seltenerer Fall
zurückgestellt). Lektion: Bei jeder auf `letzter_grund` (oder allgemein
einem nur-bei-Zustandswechsel geschriebenen Attribut) basierenden
Anzeige zuerst fragen, ob eine **live** Neuberechnung aus bereits
vorhandenen oder leicht ergänzbaren Attributen möglich ist, bevor man
sich mit dem historischen Wert (und seiner unvermeidlichen Staleness)
abfindet - ein Debounce/Filter an der Quelle (wie in Lektion 12) macht
das Problem seltener, löst aber nicht das grundsätzliche Anzeige-Problem
"zeigt Vergangenheit, wo Gegenwart gemeint ist".

**14. `description_placeholders` mit echten `{platzhalter}` ist der
Normalfall - Lektion 8s Fullwidth-Klammer-Trick ist nur ein Workaround
für Text OHNE echte Platzhalterbefüllung (0.38.0).** Bei der Frage "wie
zeigt man im Raum-Formular den aktuell wirksamen globalen Wert an, an dem
man sich beim Setzen eines Overrides orientieren kann" wurde `data_description`
(HA-Hinweistext je Formularfeld) mit einem echten, pro Formularaufruf neu
berechneten `{global_<feldname>}`-Platzhalter kombiniert: `config_flow.py`
liest dafür bei jedem `async_show_form()` für den Raum-Schritt (sowohl
Config- als auch Options-Flow) über `_room_override_placeholders()` den
aktuellen Wert aus den globalen Einstellungen (bzw. dessen Standardwert)
für jedes per `_override_selector()` überschreibbare Feld aus und übergibt
ihn als `description_placeholders`. Anders als bei Lektion 8 muss hier
NICHT auf Fullwidth-Klammern (`｛｜｝`) ausgewichen werden - die dortige
Regel greift nur, wenn ein `{wort}` im Text steht, OHNE dass tatsächlich
ein passender Wert übergeben wird (reiner Beispieltext); hier wird der
Wert bei jedem Rendern des Formulars neu und korrekt befüllt, also ist
ein echtes, unescapetes `{global_temp_threshold_open}` genau richtig und
nötig (führt weder zu einem formatjs- noch zu einem hassfest-Fehler).
Wichtig: der aktuelle globale Wert wird NUR im Hinweistext angezeigt,
NICHT über `suggested_value` ins leere Feld vorbefüllt - das würde beim
Speichern ohne Änderung einen Override auf genau diesen Wert einfrieren
(dauerhaft losgelöst von künftigen Änderungen der globalen Einstellung),
statt wie gewollt "leer = folgt weiterhin live der globalen Einstellung"
zu bleiben (siehe `_override_selector()`).

**15. Über eine `{% for %}`-Schleife hinweg zählen/akkumulieren geht in
Home Assistants Jinja-Sandbox nur über `namespace()`, nicht über normales
`{% set %}` (0.39.0).** Für eine Übersichts-Tabelle am Kartenanfang
(Anzahl Räume je Icon-Status 🟢/🟠/🔴) mussten Werte aus JEDER
Schleifen-Iteration aufsummiert werden - ein normales `{% set count = ... %}`
scheidet dafür aus, weil (anders als bei `{% if %}`, siehe frühere
Erfahrung mit `match_icon`/`highlight_ok`) ein `{% for %}` in Jinja pro
Durchlauf einen eigenen Scope aufmacht; Änderungen darin gehen nach jeder
Iteration wieder verloren. Jinja2s `namespace()`-Objekt ist genau dafür
gedacht und wird von Home Assistants Sandbox ausdrücklich erlaubt (anders
als z. B. `list.append()`, siehe Lektion 4) - `{% set ns = namespace(...) %}`
vor der Schleife, darin `{% set ns.attr = ... %}` zum Fortschreiben.
Genutzt außerdem, um die einzelnen Raum-Blöcke selbst erst in `ns.rooms`
zu sammeln (statt sie direkt pro Iteration auszugeben) - nötig, weil die
Übersichts-Tabelle VOR der Raumliste erscheinen soll, ihre Werte (die
Zählung) aber erst NACH Durchlauf aller Räume feststehen; erst nach
`{% endfor %}` wird die endgültige Reihenfolge (Übersicht, dann
`ns.rooms`) ausgegeben.

Für die dabei ebenfalls neu angezeigte Versionsnummer wurde bewusst
NICHT die Version fest im Karten-Text hinterlegt (müsste bei jedem
Release manuell im Dashboard nachgezogen werden) und auch nicht separat
in `const.py` dupliziert (zweite Quelle der Wahrheit, könnte von
`manifest.json` abweichen) - stattdessen liest `__init__.py:async_setup()`
sie einmalig zur Laufzeit über Home Assistants eigene
`homeassistant.loader.async_get_integration(hass, DOMAIN)` aus (liefert
u. a. `.version`, direkt aus `manifest.json` geparst) und legt sie unter
einem neuen `hass.data[DOMAIN]`-Schlüssel (`VERSION_KEY`, analog zum
bereits bestehenden `GLOBAL_ENTRY_ID_KEY`-Muster) ab; `binary_sensor.py`
liest das nur noch synchron aus und exponiert es als
`integration_version`-Attribut (identisch für jeden Raum). `manifest.json`
bleibt dadurch die einzige Stelle, an der die Version tatsächlich steht.

**16. Nicht jeder "echte" Schließen-Grund ist gleich dringend - manche
dürfen ohne Benachrichtigung bleiben, ohne dafür "silent" wie in Lektion 11
zu sein (0.40.0).** Auf die Frage, ob es für CO2 einen "zu niedrig"-
Gefahrenfall gibt (analog zu Frost/Hitze bei der Temperatur): nein - ein
CO2-Wert unter der Schließen-Schwelle bedeutet nur "Luftqualität wieder
gut genug", kein Sicherheitsrisiko. Der Nutzer folgerte daraus: das
Schließen wegen CO2-Rückgang sollte dann auch nicht zwingend eine
Benachrichtigung erzeugen. Wichtiger Unterschied zu Lektion 11
(`silent_frost_close`): dort gab es GAR KEINEN echten Messwert (Sensor
fehlte), weshalb sowohl die Benachrichtigung als auch der `reason`/
`letzter_grund`-Wert selbst unterdrückt wurden (`_last_reason = None`),
um keine irreführende Anzeige zu erzeugen. Hier dagegen gibt es einen
echten, korrekten Messwert - `reason = "co2"` bleibt ehrlich gesetzt
(Diagnose/Dashboard funktionieren unverändert), nur die Benachrichtigung
selbst entfällt (`silent_co2_close` in `binary_sensor.py`, gesetzt bevor
`_attr_is_on` überschrieben wird, da die Prüfung `should_close and
self._attr_is_on` denselben - dann bereits veralteten - Zustand braucht
wie die vorausgehende `elif`-Kette). Lektion: "Silent" (keine Anzeige)
und "keine Benachrichtigung" sind zwei unabhängige Entscheidungen, die
aus unterschiedlichen Gründen getroffen werden - fehlender Messwert
(Lektion 11) rechtfertigt beides, ein echter, nur nicht dringender
Messwert rechtfertigt nur Letzteres.

**17. "Alle rot angezeigten Daten sollen orange werden" war zu breit
interpretiert - die eigentliche Absicht war viel enger (Dashboard-Karte,
kein Versionsbump nötig, Backend-Teil weiterhin 0.40.0).**
Nach der Frage "gibt es für CO2 einen zu niedrigen Wert" (Antwort: nein,
siehe Lektion 16) sagte der Nutzer, das solle "auch nicht zwingend eine
Benachrichtigung erzeugen" und "außerdem alle rot angezeigten Daten nur
orange dargestellt werden". Eine Rückfrage (AskUserQuestion) dazu, ob
damit wirklich jeder rote Zustand kartenweit gemeint sei, wurde mit "ja"
beantwortet - entsprechend wurde Rot zunächst komplett aus der
Kartenlogik entfernt (nur noch 🟢/🟠, siehe Git-Historie). Direkt danach
korrigierte der Nutzer das explizit: orange sollte **nur** für den
CO2-zu-niedrig-Fall gelten, alle anderen bisher roten Fälle (echter
Fenster-Mismatch aus einem anderen Grund) sollten **rot bleiben** - nur
das schon zuvor (0.39.0) bestehende, unabhängige Orange für Räume ohne
Fenster sollte unverändert bleiben. Endgültige Logik: 🟢 (passt) / 🔴
(Mismatch aus echtem Grund) / 🟠 (Mismatch, aber der gewinnende Auslöser
ist CO2-Schließen oder der Raum hat kein Fenster) - `co2_close_exception`
im Karten-Template, analog zu `silent_co2_close` im Backend. Lektion: Eine
"ja"-Antwort auf eine klärende Rückfrage validiert nur die konkret
gestellte Frage, nicht automatisch die davor formulierte, oft unpräzise
gemeinte Ursprungsanweisung - bei einer sprachlich absoluten Formulierung
("alle", "immer", "nie") im Nachgang einer engeren, konkreten Beobachtung
(hier: die CO2-Erkenntnis) lohnt sich eine zweite, noch konkretere
Rückfrage ("nur für X, oder wirklich überall?"), bevor eine
kartenweite Änderung umgesetzt wird - auch wenn die erste Rückfrage
bereits explizit "ja, überall" bestätigt hat.

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
