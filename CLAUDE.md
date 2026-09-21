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
import yaml, jinja2, jinja2.sandbox
data = yaml.safe_load(card_yaml_text)
env = jinja2.sandbox.SandboxedEnvironment(
    trim_blocks=True, lstrip_blocks=True, undefined=jinja2.StrictUndefined
)
tmpl = env.from_string(data["content"])
output = tmpl.render(states=FakeStatesObj(), now=lambda: ..., as_local=lambda dt: dt)
```

**Wichtig: `undefined=jinja2.StrictUndefined` nicht vergessen** (siehe
Nachtrag unten) - ohne das fängt dieser Test einen ganzen Fehlertyp nicht.

Trotz dieses Tests bleiben CSS/Rendering-Details (Abstände, Style-Filterung)
nicht zuverlässig vorhersagbar - dafür bräuchte es eine echte
Home-Assistant-Instanz.

**Nachtrag (nach 0.41.0, reiner Dashboard-Karten-Fix ohne eigenen
Versionsbump):** Ein neues Attribut (`luftentfeuchter_tank_fehler`,
nur gesetzt, falls für den Raum ein Tankstatus-Sensor konfiguriert ist)
wurde in der Karte ohne das sonst überall befolgte `a.attr is defined`-
Muster referenziert (`... if a.luftentfeuchter_tank_fehler else ...`).
Der Fehler lief in der eigenen Sandbox-Simulation klaglos durch - ein
`dict` (unser `FakeState.attributes`) liefert bei fehlendem Key über
Jinja2s normale, nachsichtige `Undefined`-Klasse einfach einen falsy
Wert zurück. In der echten Home-Assistant-Oberfläche crashte die Karte
dagegen mit `UndefinedError: 'ReadOnlyDict object' has no attribute
'luftentfeuchter_tank_fehler'` - HAs eigene Jinja-Umgebung behandelt
einen fehlenden Attributzugriff dort strenger. Reproduziert und der Fix
bestätigt durch `undefined=jinja2.StrictUndefined` in der Simulation
(dann schlägt exakt derselbe Fehler auch lokal fehl, der Fix mit
`is defined`-Guard besteht dagegen). Lektion: Die eigene Simulation war
bis dahin **nachsichtiger** als die echte Oberfläche, nicht strenger -
das Gegenteil der bis dahin angenommenen Richtung ("Simulation fängt
das meiste ab, Rendering-Details bleiben ungewiss"). Ab sofort immer
`StrictUndefined` verwenden, damit ein fehlender `is defined`-Guard bei
einem neuen/optionalen Attribut zuverlässig schon lokal auffällt, nicht
erst beim Nutzer in der echten Karte.

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

**Nachtrag (0.49.0, reiner Dashboard-Karten-Fix ohne eigenen
Versionsbump):** Weitere Verfeinerung derselben Farblogik - der Nutzer
bat darum, den CO2-zu-niedrig-Fall (`co2_close_exception`) nicht mehr
orange, sondern **grün** darzustellen (Icon am Raumnamen UND
Empfehlungstext/Werte-Hervorhebung), da hierbei ohnehin kein
Handlungsbedarf besteht - orange bleibt seitdem ausschließlich Räumen
ohne Fenster vorbehalten. Endgültige Logik damit: 🟢 (passt **oder**
CO2-Schließen-Ausnahme) / 🟠 (Raum ohne Fenster) / 🔴 (Mismatch aus
echtem, handlungsrelevanten Grund). Technisch: an allen drei Stellen, an
denen bisher `no_window or co2_close_exception` gemeinsam die
orange-Farbe auslösten, wurde `co2_close_exception` aus dieser
Oder-Verknüpfung herausgelöst und stattdessen der grün-Bedingung
hinzugefügt (`is_match or co2_close_exception` bzw. `highlight_ok or
co2_close_exception`) - `no_window` allein entscheidet jetzt noch über
Orange. Lektion: Eine als "Ausnahme von Rot" eingeführte Zwischenfarbe
(hier: Orange für "technischer Mismatch, aber unproblematisch") ist kein
Selbstzweck - wenn sich im Nachhinein herausstellt, dass ein Fall davon
eigentlich näher an "alles in Ordnung" liegt als an "Achtung nötig",
lohnt sich die Rückfrage, ob er nicht direkt in die Grün-Kategorie
gehört, statt dauerhaft in einer Zwischenfarbe zu verbleiben, die
ursprünglich für einen anderen, strukturell unterschiedlichen Fall
(Raum ohne Fenster) gedacht war.

**18. Die Web-Benachrichtigung hatte ein "clean notification"-Muster
(automatisches Auflösen, sobald sich eine Empfehlung erledigt hat)
längst über `persistent_notification.dismiss`, das App-Push aber nicht
(0.42.0).** Auf die Anforderung, dieselbe Klarheit auch für Push
sicherzustellen, ergaben sich zwei separate Auslöser, nicht nur einer:
(a) ein echter Zustandswechsel der Empfehlung selbst (spiegelbildlich
zum bereits bestehenden Verhalten der Web-Benachrichtigung) und (b) der
Fall, dass die Person das Fenster bereits von sich aus bedient hat,
während die zugrunde liegenden Werte sich noch gar nicht normalisiert
haben - hier bleibt `self._attr_is_on` unverändert (kein
Zustandswechsel), nur `_window_action_needed()` wechselt von "Aktion
nötig" zu "bereits erledigt". Fix: Home Assistants App-Benachrichtigung
unterstützt genau dafür einen `tag` im `data`-Feld von
`notify.send_message` - eine neue Nachricht mit demselben `tag` ersetzt
eine bereits angezeigte automatisch (praktisch z. B. bei "bitte öffnen"
→ "bitte schließen", ohne zwei Benachrichtigungen gleichzeitig stehen zu
lassen), und `message: "clear_notification"` mit demselben `tag` löst
sie ganz ohne Ersatz auf. `_mobile_notification_active` (nicht über
Neustarts hinweg wiederhergestellt, bewusst wie bereits `_last_notified_at`
- siehe Kommentar dort) verfolgt, ob aktuell überhaupt eine Push-
Benachrichtigung offen "aussteht"; `_maybe_clear_mobile_notification()`
prüft nach **jeder** Neubewertung (nicht nur bei einem Zustandswechsel,
da auch der Fensterkontakt selbst eine verfolgte, Neubewertungen
auslösende Entität ist) einheitlich `_window_action_needed(self._attr_is_on)`
und deckt damit beide Fälle (a) und (b) mit derselben Prüfung ab, statt
zwei getrennte Sonderfälle zu behandeln. Lektion: Wenn ein Kanal (hier:
Web-Benachrichtigung) bereits ein "löst sich automatisch auf"-Muster
implementiert, das ein anderer, strukturell ähnlicher Kanal (hier: Push)
noch nicht hat, prüfen, ob die Bedingung für "erledigt" beim zweiten
Kanal wirklich identisch mit einem Zustandswechsel ist, wie beim ersten
- hier war sie es nicht: die Fensterkontakt-Bedienung allein reicht
bereits aus, ganz ohne dass sich die eigentliche Empfehlung selbst
ändert.

**Nachtrag (0.43.0):** Direkt nach 0.42.0 fragte der Nutzer, ob dasselbe
auch für die persistente Web-Benachrichtigung gilt - Antwort: nein, war
es nicht. Fall (a) (echter Zustandswechsel) war für die Web-Benachrichtigung
schon immer über `persistent_notification.dismiss` in `_notify()` abgedeckt
gewesen (das bestand ja schon vor 0.42.0 und war gerade das Vorbild für den
Push-Fix) - aber Fall (b) (Fensterkontakt allein löst das Bedürfnis auf,
ohne dass sich `self._attr_is_on` ändert) wurde beim Push-Fix nur für den
Push-Kanal ergänzt, nicht für die Web-Benachrichtigung, obwohl dieselbe
Begründung identisch auch dort gilt. Fix: `_maybe_clear_mobile_notification()`
zu `_maybe_clear_notifications()` verallgemeinert - prüft weiterhin
einmalig `_window_action_needed(self._attr_is_on)`, löst bei Erfüllung
aber beide Kanäle auf, sofern jeweils eine eigene `_..._notification_active`-
Flag aktiv ist (`_mobile_notification_active`, neu:
`_persistent_notification_active`, von `_notify()` bei Create/Dismiss
gepflegt). `_mobile_notification_tag()` in `_notification_id()`
umbenannt, da der Bezeichner jetzt für beide Kanäle gemeinsam verwendet
wird (als `tag` bei Push, als `notification_id` bei der Web-
Benachrichtigung - beide nutzten ohnehin schon denselben String). Lektion,
die Lektion 18 präzisiert: Wird ein "löst sich automatisch auf"-Muster für
einen zweiten Kanal um einen neuen Auslösefall erweitert, der ohne
Zustandswechsel auskommt, gilt dieser neue Fall grundsätzlich für JEDEN
Kanal mit demselben Muster gleichermaßen, nicht nur für den Kanal, an dem
die Erweiterung gerade konkret bemerkt/angefragt wurde - beim Ergänzen
also sofort prüfen, ob ein struktur-identischer Nachbar-Kanal (hier: die
Web-Benachrichtigung, die dasselbe Grundmuster schon hatte) denselben
neuen Fall ebenfalls braucht, statt das erst auf explizite Nachfrage
nachzuholen.

**19. `luftentfeuchter_an`/`klimaanlage_an` zeigten nicht den echten
Gerätezustand, sondern nur "hat DIESE Integration das Gerät zuletzt
selbst geschaltet" (0.44.0).** Nutzer-Meldung: "die Klimaanlage ist aktiv
aber es wird nicht auf dem Dashboard angezeigt". Ursache: `_dehumidifier_state`/
`_ac_state` sind rein interne, für `_update_single_device()` gedachte
"zuletzt selbst kommandiert"-Tracker (Zweck: keine doppelten
turn_on/turn_off-Aufrufe, siehe `current is not True`/`current is not
False`-Prüfungen) - sie wurden aber 1:1 auch als Wert für die angezeigten
Attribute `luftentfeuchter_an`/`klimaanlage_an` verwendet. Schaltete der
Nutzer die Klimaanlage manuell oder eine andere Automation sie ein, blieb
`_ac_state` unverändert `False`/`None` (die Integration selbst hat ja
nichts geschaltet) - die Karte zeigte weiterhin ⚫, obwohl das Gerät
tatsächlich lief. Fix: neue Methode `_is_device_on(entity_id)` liest den
Zustand jetzt live direkt von der konfigurierten Geräte-Entität (analog
zum bereits bestehenden Live-Read-Muster für `luftentfeuchter_tank_fehler`,
siehe Nachtrag zu Lektion 7) - unabhängig davon, wer das Gerät geschaltet
hat. Da `climate`-Entitäten (Klimaanlage) kein binäres on/off-`state`-
Schema wie `switch`/`humidifier` haben, sondern echte Betriebsmodi
(`cool`/`heat`/`auto`/... vs. `off`), prüft die Methode dort auf
"Zustand ungleich `off`" statt auf "Zustand gleich `on`". Die internen
`_dehumidifier_state`/`_ac_state`-Tracker selbst bleiben unverändert für
die Steuerungslogik in `_update_single_device()` zuständig - nur die für
die Karte exponierten Attribute wurden auf Live-Lesen umgestellt.
Lektion: Ein intern für eine ganz andere Aufgabe (hier: Idempotenz beim
Schalten) gepflegter Zustands-Tracker beantwortet nicht automatisch die
Frage, die ein nach außen exponiertes Anzeige-Attribut mit ähnlichem
Namen eigentlich beantworten soll ("ist das Gerät an?" vs. "habe ICH es
zuletzt angeschaltet?") - bei jedem Attribut, das für ein Dashboard
gedacht ist, prüfen, ob es wirklich den live abfragbaren Ist-Zustand
widerspiegelt, nicht nur einen internen Kontrollfluss-Zwischenstand.

**20. Ein bewusst dokumentiertes Verhalten kann trotzdem ein Bug bleiben,
wenn es die Nutzer-Erwartung enttäuscht (0.45.0).** Beim Bearbeiten eines
bestehenden Raums (Options-Flow) sitzen das Feld "HA-Bereich" und die
davon abhängigen, gefilterten Sensor-/Geräte-Auswahllisten im selben,
einstufigen Formular - anders als beim Neuanlegen, wo der Bereich in
einem eigenen ersten Schritt gewählt wird (siehe `async_step_user` vs.
`async_step_room`). Home-Assistant-Formulare sind innerhalb eines
einzigen `async_show_form()`-Renderings nicht reaktiv: Auswahllisten
lassen sich nicht live neu berechnen, wenn der Nutzer nur ein anderes
Feld im selben, noch offenen Formular ändert. Der Code nutzte deshalb
bewusst den **gespeicherten** Bereich für die Filterung - mit einem
erklärenden Hinweistext direkt am Feld ("ändern wirkt sich erst beim
nächsten Öffnen dieses Formulars aus") und einem ausführlichen Absatz in
der README. Ein Nutzer meldete das Verhalten trotzdem als Problem
("erst muss ich die Konfiguration speichern und neu öffnen") - er hatte
den Hinweistext entweder nicht gelesen oder ihn zwar gelesen, aber als
unnötige Einschränkung statt als Erklärung wahrgenommen. Fix: Home
Assistant erlaubt zwar keine live-reaktiven Formulare, aber ein Submit
muss nicht zwingend sofort speichern - `async_step_room()` vergleicht
den gerade übermittelten Bereich (`submitted_area_id`) mit dem Bereich,
der die aktuell angezeigten Listen gefiltert hat
(`self._room_filter_area_id`, ein Instanzattribut, das über die Schritte
desselben Flows hinweg erhalten bleibt - analog zum bereits bestehenden
Muster `self._area_id` im Config-Flow). Weichen beide voneinander ab
(Bereich wurde gerade geändert), wird NICHT gespeichert, sondern
dasselbe Formular mit den bereits gemachten übrigen Eingaben und den neu
nach dem geänderten Bereich gefilterten Auswahllisten erneut angezeigt -
ein zweites, unverändertes Speichern übernimmt die Änderungen dann
tatsächlich. Für den häufigen Fall (kein Bereichswechsel) bleibt es beim
bisherigen einzigen Speichern ohne Zwischenschritt. Lektion: Eine im Code
und in der Doku sauber erklärte Einschränkung ist kein Ersatz dafür, sie
tatsächlich zu beheben, wenn eine Behebung möglich ist (hier: über einen
impliziten Submit-Zwischenschritt statt einer echten Live-Reaktivität,
die Home-Assistant-Formulare grundsätzlich nicht bieten) - "gut
dokumentiert" und "kein Bug mehr" sind zwei verschiedene Dinge.

**21. `should_close` musste in "Sicherheit" und "Komfort" aufgeteilt
werden, um eine raumweite Abschaltung nur des Komfort-Teils zu erlauben
(0.46.0).** Auf Nutzerwunsch: eine Schiebetür im Esszimmer, deren
Fensterkontakt den tatsächlichen Zustand nicht zuverlässig widerspiegelt,
sowie ein Raum (Flur OG), in dem eine Klimaanlage die Kühlung ohnehin
unabhängig vom Fenster übernimmt - in beiden Fällen ist eine "bitte
schließen"-Empfehlung nicht sinnvoll umsetzbar bzw. störend. Neue
Raum-Option `CONF_DISABLE_CLOSE_RECOMMENDATION` ("Schließempfehlung
deaktivieren"). Wichtig dabei: `should_close` war bis dahin eine flache
Oder-Verknüpfung aus sieben Einzelbedingungen
(`close_by_temp/humidity/co2/summer_outdoor/duration/frost/heat`) ohne
Unterscheidung zwischen "reiner Komfort" und "Sicherheit" - ein
pauschales `should_close and not disable_close_recommendation` hätte
also auch `close_by_frost`/`close_by_heat` mit abgeschaltet, was gegen
das in diesem Projekt durchgehend befolgte Prinzip verstoßen hätte, dass
Frost-/Hitzeschutz als Sicherheitsmechanismen NIE durch eine
Komfort-Einstellung deaktivierbar sein dürfen (siehe Lektionen 2, 11,
12). Fix: `should_close = close_by_frost or close_by_heat or (not
disable_close_recommendation and (close_by_temp or close_by_humidity or
close_by_co2 or close_by_summer_outdoor or close_by_duration))` - Frost-/
Hitzeschutz stehen jetzt explizit VOR der Klammer und bleiben so in
jedem Fall wirksam, nur die fünf reinen Komfort-Bedingungen (inkl.
Winter-Höchstdauer und Sommer-Fall - beides Energiespar-/Komfort-, keine
Sicherheits-Heuristiken) werden gemeinsam abgeschaltet. Öffnen-
Empfehlungen (`should_open`) sind von der neuen Option unberührt - nur
die "bereits offen, jetzt bitte schließen"-Seite entfällt. Lektion: Bevor
eine neue "Bedingung X abschalten"-Option eingeführt wird, die eine
bereits bestehende Oder-Verknüpfung mehrerer Einzelbedingungen betrifft,
erst prüfen, ob innerhalb dieser Verknüpfung Sicherheits- und reine
Komfort-Gründe vermischt sind - ein pauschales Ausklammern der GESAMTEN
Verknüpfung würde sonst versehentlich auch Sicherheitsmechanismen mit
abschalten, die von der Nutzerabsicht gar nicht gemeint waren.

**22. Eine neue Backend-Option wirkt sich nicht automatisch auf die
Dashboard-Karte aus, wenn diese ihre Werte komplett eigenständig live
berechnet (0.47.2).** Direkt nach Lektion 21 meldete der Nutzer (mit
Screenshot): Im Esszimmer wurde trotz aktivierter "Schließempfehlung
deaktivieren"-Option weiterhin ein CO2-Auslöser mit "Schließen"-Empfehlung
angezeigt (orange). Ursache: Die Dashboard-Karte berechnet Auslöser und
Empfehlung für Temperatur/Luftfeuchtigkeit/CO2 seit Lektion 13 bewusst
**komplett live** aus den angezeigten Messwerten/Schwellen, unabhängig vom
tatsächlichen `should_close` der Integration - genau das macht die Karte
robust gegenüber veralteten `letzter_grund`-Werten (siehe Lektion 13), hat
aber als Kehrseite: Sie wusste schlicht nichts von der neuen, rein im
Backend (`_evaluate()`) wirksamen `disable_close_recommendation`-Option und
berechnete den CO2-Komfort-Auslöser unverändert weiter. Ein Backend-Fix
allein (Lektion 21) reicht also nicht, wenn ein zweiter, unabhängiger
"Konsument" derselben Entscheidung (hier: die Karte) eigene, parallele
Logik hat. Fix: neues Attribut `schliessempfehlung_deaktiviert` (nur
gesetzt, wenn aktiv, analog zu `hat_fenster`) in `extra_state_attributes`
ergänzt; die Karte prüft es jetzt genauso wie die Integration selbst -
Frost-/Hitzeschutz (`frost_live`/`heat_live`) bleiben davon unberührt,
nur die Komfort-Auslöser (`comfort_close`, aus Temperatur/Feuchtigkeit/
CO2/Winter-Höchstdauer/Sommer-Fall zusammengesetzt) werden bei aktiver
Option auf `''` gesetzt - identisch zum Sicherheit/Komfort-Split im
Backend. Lektion: Wann immer eine neue Bedingung eingeführt wird, die
eine Empfehlung beeinflusst, UND die Dashboard-Karte dieselbe Art von
Empfehlung bereits unabhängig live nachrechnet (wie seit Lektion 13 für
Temperatur/Feuchtigkeit/CO2/Frost/Hitze der Fall), sofort mitprüfen, ob
die Karte diese neue Bedingung ebenfalls als Attribut braucht - sonst
klafft zwischen "was die Integration tatsächlich empfiehlt" und "was die
Karte anzeigt" eine Lücke, die dem Nutzer nur zufällig aus genau dem
Blickwinkel auffällt, aus dem er gerade die neue Option nutzt.

**23. Der Außenluft-Vergleich für Luftfeuchtigkeit (`outdoor_drier_enough`)
war nur ein Öffnen-Gate, kein fortlaufend geprüfter Zustand - anders als
beim strukturell identischen Temperatur-Fall (0.48.0).** Nutzer-Frage (mit
Screenshot, Raum Badezimmer): "warum soll das Fenster geöffnet werden,
obwohl die absolute Luftfeuchtigkeit draußen höher ist als drinnen?" -
angezeigt waren 11,9 g/m³ innen gegen 13,4 g/m³ außen, die Karte zeigte
trotzdem "Öffnen" mit Auslöser "Luftfeuchtigkeit". Ursache: `outdoor_drier_enough`
(siehe absolute-vs-relative-Feuchtigkeit-Vergleich, README) wird nur
einmalig beim Übergang von "aus" nach "an" geprüft (`open_by_humidity`,
Teil von `should_open`) - ist die Empfehlung erst einmal aktiv, bleibt sie
bestehen, bis eine der "echten" Schließbedingungen (`close_by_humidity`:
Innen-Luftfeuchtigkeit unter die Schließen-Schwelle) greift. Wird die
Außenluft NACH dem Öffnen absolut feuchter als die Innenluft (z. B. weil es
zu regnen beginnt), gibt es dafür keine Schließbedingung - die Empfehlung
bleibt fälschlich "Öffnen" bestehen, obwohl Lüften die Luftfeuchtigkeit
jetzt nur noch verschlimmern würde. Auffällig: Für Temperatur existiert
genau diese Absicherung bereits (`close_by_summer_outdoor`/`outdoor_warmer_again`
- schließt, wenn die Außentemperatur nach dem Öffnen wieder über die
Innentemperatur + Toleranz-Marge steigt), für Luftfeuchtigkeit fehlte das
strukturell identische Pendant einfach. Fix: neue Bedingung
`outdoor_humidity_confirmed_worse`/`close_by_humidity_outdoor_reversal`,
1:1 nach demselben Muster wie `close_by_summer_outdoor` (schließt nicht,
solange Temperatur oder CO2 noch Lüftungsbedarf anzeigen; reiner
Komfort-Grund, daher über `CONF_DISABLE_CLOSE_RECOMMENDATION` weiterhin
abschaltbar, siehe Lektion 21). Bewusst NUR bei vollständig vorliegenden
Innen-/Außenwerten aktiv, nicht schon bei fehlendem Sensor/Messwert -
anders als beim konservativen Öffnen-Gate (Lektion 2) ist ein fehlender
Wert hier kein Sicherheits-, sondern ein reiner Komfort-Fall, der ohne
positive Bestätigung nicht vorsorglich schließen soll. Neuer Grund-Code
`outdoor_wetter` (Nachricht `CONF_MSG_CLOSE_OUTDOOR_WETTER`, Werte als
absolute Luftfeuchtigkeit in g/m³ statt %, da genau dieser Vergleich die
Bedingung auslöst) - analog zu `outdoor_warmer` von der Dashboard-Karte
nur als Rückfallwert aus `letzter_grund` behandelt (nicht live
nachrechenbar, siehe Lektion 13), inkl. Hervorhebung der passenden
Außen-Zelle (hier: absolute Luftfeuchtigkeit außen, nicht die relative %-
Spalte, da diese die tatsächlich auslösende Größe ist). Lektion: Wird für
eine Größe (hier: Temperatur) ein "Außenluft-Vorteil ist nach dem Öffnen
wieder verschwunden"-Schließmechanismus eingeführt, prüfen, ob eine
strukturell identische zweite Größe (hier: Luftfeuchtigkeit, die genauso
einen einmaligen Außenluft-Vergleich als Öffnen-Gate nutzt) denselben
Mechanismus ebenfalls braucht - ein Öffnen-Gate, das nur beim Übergang
geprüft wird, ist implizit eine Momentaufnahme, die durch spätere
Änderungen der Außenbedingungen ungültig werden kann, ohne dass der Code
das von sich aus bemerkt.

**24. Der Luftentfeuchter lief bislang komplett unabhängig vom
Fenster-Status - auf Nutzer-Nachfrage ("gibt es da noch etwas zu
optimieren, z. B. Berücksichtigung absoluter Luftfeuchtigkeit?") wurde
daraus eine gezielte Pausier-Bedingung, kein genereller
Fenster-Kopplungs-Automatismus (0.49.0).** Auf die (rein informative)
Frage, welche Kriterien beim Ein-/Ausschalten des Luftentfeuchters
mitwirken, folgte die exploratorische Frage nach Optimierungspotenzial.
Erster eigener Vorschlag ("bei offenem Fenster grundsätzlich pausieren")
wäre zu grob gewesen: ein offenes Fenster allein sagt nichts darüber aus,
ob das Lüften die Entfeuchtung unterstützt oder ihr entgegenwirkt - das
hängt exakt von demselben absoluten Außen-/Innen-Luftfeuchtigkeits-
Vergleich ab, der bereits die Fenster-Öffnen-Empfehlung gattet
(`outdoor_drier_enough`, siehe Lektion 23). Der Nutzer korrigierte das
selbst treffend: "ist das Fenster offen und die Luft draußen trockener,
kann der Luftentfeuchter weiterlaufen" - das bereits vorhandene
`outdoor_drier_enough`-Flag ließ sich dafür 1:1 wiederverwenden (keine
doppelte Vergleichslogik nötig), kombiniert mit einem neuen
`_is_window_confirmed_open()`-Helper (bewusst NICHT der bereits
bestehende `_window_action_needed()` - der beantwortet eine andere Frage
für einen anderen Zweck und liefert bei fehlenden Daten absichtlich das
Gegenteil, `True`). Ergebnis: `dehumidifier_pause_open_window = window
offen UND NICHT outdoor_drier_enough` - pausiert bei bestätigt
feuchterer Außenluft ebenso wie bei fehlenden Werten (konservativ, wie
`outdoor_drier_enough` es für sein eigentliches Öffnen-Gate ohnehin
schon vorsieht), bleibt aber wie bisher komplett unbeeinflusst, sobald
entweder kein Fensterkontakt-Sensor oder gar kein
Außen-Luftfeuchtigkeitssensor konfiguriert ist. Lektion: Bei einer
exploratorischen "was könnte man optimieren"-Frage den ersten eigenen,
naheliegenden Vorschlag nicht overengineeren, aber auch nicht zu simpel
lassen - der Nutzer hat hier selbst den entscheidenden Verfeinerungs-
Schritt (welcher Vergleich genau?) beigesteuert; wichtig war, das
bereits vorhandene, für einen strukturell identischen Zweck (Fenster-
Öffnen-Gate) längst etablierte Flag wiederzuerkennen und direkt
wiederzuverwenden, statt eine zweite, eigene Vergleichslogik für den
Luftentfeuchter zu bauen.

**25. Eine zweite, vom Haupt-Sensor abgeleitete Entität führt eine
Reihenfolge-Abhängigkeit beim gleichzeitigen Hinzufügen ein, die leicht zu
übersehen ist (0.50.0).** Auf Nutzerwunsch: der Haupt-Sensor sollte
umbenannt werden (`"Lüften empfohlen ‹Raum›"` → `"‹Raum›
Lüftungsempfehlung"` - reiner `_attr_name`-Wechsel, die Entity-ID bereits
bestehender Räume bleibt dabei unverändert, da sie beim Anlegen einmalig
aus dem damaligen Namen abgeleitet und danach in der Entity-Registry
fixiert wird, nicht bei jedem Neustart neu generiert) und die
Duscherkennung sollte zusätzlich zum bestehenden `duschen_erkannt`-
Attribut eine eigene Entität `"‹Raum› Dusche aktiv"` bekommen - nur
vorhanden, wenn die Duscherkennung für den Raum aktiviert ist. Die neue
Entität (`SmartVentilationShowerBinarySensor`) hat bewusst keinen eigenen
Zustand, sondern liest live `room_sensor.showering` (neue Property) und
wird vom Haupt-Sensor bei jeder Neubewertung mit aktualisiert
(`self._shower_sensor.async_write_ha_state()`, Referenz über
`attach_shower_sensor()` nach dem Anlegen beider Entitäten gesetzt).
Stolperfalle dabei: `async_setup_entry()` übergibt beide Entitäten in
einem einzigen `async_add_entities([room_sensor, shower_sensor])`-Aufruf
- Home Assistant fügt Entitäten aus einem solchen Aufruf nicht garantiert
streng nacheinander hinzu, und der Haupt-Sensor ruft in seinem eigenen
`async_added_to_hass()` bereits synchron `await self._evaluate()` auf,
was sofort `self._shower_sensor.async_write_ha_state()` auslösen würde -
zu diesem Zeitpunkt könnte `shower_sensor.hass` je nach Ausführungsreihen-
folge noch `None` sein (Absturz). Fix: der Schreibaufruf beim Haupt-Sensor
wird mit `self._shower_sensor.hass is not None` abgesichert (überspringt
den allerersten Schreibversuch im Zweifelsfall einfach), UND der
Dusche-Sensor bekommt eine eigene `async_added_to_hass()`, die seinen
Zustand einmalig selbst schreibt, sobald er vollständig hinzugefügt ist -
so kommt der korrekte Startzustand über einen der beiden Wege in jedem
Fall zustande, unabhängig von der tatsächlichen Hinzufüge-Reihenfolge.
Bei diagnostics.py ergab sich eine zweite, verwandte Stolperfalle: die
bisherige Ein-Entität-pro-Raum-Annahme (`next(reg_entry.entity_id for
reg_entry in ...)`, nimmt einfach die erste gefundene Entität) trifft
jetzt für Räume mit aktivierter Duscherkennung nicht mehr zu - ohne Fix
hätte die Diagnose-Datei nicht-deterministisch mal den Haupt-, mal den
Dusche-Sensor als "die" Entität des Raums zeigen können. Fix: gezielt
über die feste `unique_id`-Namenskonvention (`..._lueften_empfohlen` vs.
`..._dusche_aktiv`) auseinandergehalten, statt sich auf Registrierungs-
Reihenfolge zu verlassen. Lektion: Sobald eine Integration von "genau
eine Entität pro Config-Entry" zu "möglicherweise mehrere" wechselt,
jede Stelle im Code prüfen, die bisher stillschweigend genau eine
Entität pro Eintrag angenommen hat (hier: sowohl die
Hinzufüge-Reihenfolge zwischen den Entitäten selbst als auch ein
komplett anderes Modul, das dieselbe Annahme über die Entity-Registry
traf) - eine solche Annahme muss nicht im selben Codepfad stehen wie die
Änderung, die sie bricht.

**26. Eine Bereichs-Filterung auf Auswahllisten (Lektion 9) darf den
bereits gespeicherten Wert eines Felds nie ausschließen - sonst wird ein
Raum permanent unspeicherbar, sobald sich die Bereichs-Zuordnung einer
Entität irgendwo in Home Assistant ändert (0.51.1).** Nutzer-Meldung:
"ich kann die Einstellungen im Esszimmer nicht speichern" - er wollte die
CO2-/Luftfeuchtigkeits-Sensoren entfernen, da diese dem HA-Bereich des
Raums nicht mehr zugeordnet waren, bekam aber `value must be one of
[...] at 'sensors.humidity_entity'`/`'sensors.co2_entity'` - für BEIDE
Felder, obwohl er nur etwas entfernen wollte. Zusätzlich, unabhängig
gemeldet: beim Ändern des HA-Bereichs im Raum-Formular musste er
"zweimal auf OK drücken", damit gespeichert wird. Beides hatte dieselbe
Ursache: `_area_include_entities()` (Lektion 9) berechnet die erlaubte
Auswahlliste für einen `EntitySelector` ausschließlich aus den aktuell
dem Bereich zugeordneten Entitäten passender Domain - der über
`_entity_marker()` als `default=` vorbelegte, bereits gespeicherte Wert
eines Felds wurde dabei nicht automatisch mit aufgenommen. Fällt eine
zuvor gültige Auswahl (z. B. durch eine nachträgliche Bereichs-Umsortierung
in Home Assistant selbst, oder einen geänderten Raum-Bereich) aus dieser
Liste heraus, validiert Home Assistants Data-Entry-Flow den vorbelegten
Schema-Default schon beim bloßen erneuten Anzeigen/Absenden des
Formulars gegen die neue, engere Liste - und zwar BEVOR die eigentliche
`async_step_room()`-Logik (inkl. der in Lektion 20 beschriebenen
"Bereich geändert, Formular neu anzeigen"-Prüfung) überhaupt zum Zug
kommt. Der zweite Bug (zweimal OK) war daher kein eigenständiges
Problem, sondern derselbe Absturz an einer anderen Stelle: der erste
Submit nach einem Bereichswechsel crashte hart statt wie in Lektion 20
vorgesehen sauber neu zu rendern, sobald irgendein bereits gesetztes
Feld durch den neuen Bereich aus der Auswahlliste fiel. Fix:
`_area_include_entities()` bekommt einen neuen, optionalen Parameter
`current_values` und nimmt diesen (String oder Liste) immer zusätzlich
in die erlaubte Liste auf - unabhängig davon, ob der Wert noch dem
Bereich zugeordnet ist. Alle Aufrufer übergeben jetzt den/die aktuellen
Wert(e) des jeweiligen Felds aus `defaults`; bei geteilten Include-Listen
(z. B. `sensor_include` für sowohl `CONF_HUMIDITY_ENTITY` als auch
`CONF_CO2_ENTITY`, `window_include` für sowohl `CONF_WINDOW_ENTITY` als
auch `CONF_DEHUMIDIFIER_TANK_FULL_ENTITY`) werden beide Werte als Liste
übergeben. Wichtige Nebenbedingung beim Fix: `area_entities is None`
(kein Bereich gewählt) liefert weiterhin bedingungslos `None` (keine
Einschränkung) zurück, unabhängig von `current_values` - eine erste,
zu grobe Fassung des Fixes prüfte stattdessen nur `not area_entities`
und hätte dadurch sowohl "kein Bereich gewählt" als auch "Bereich
gewählt, aber leer" (zwei laut Lektion 9 bewusst unterschiedliche Fälle)
gleichbehandelt und im ersten Fall fälschlich auf nur den aktuellen Wert
eingeschränkt, statt weiterhin alle Entitäten anzubieten - durch einen
lokalen Test dieser drei Fälle (kein Bereich / leerer Bereich mit
Altwert / leerer Bereich ohne Altwert) vor dem Commit gefunden und
korrigiert. Lektion: Eine Auswahlliste, die aus einem *aktuell*
berechneten Zustand (hier: Bereichs-Zuordnung) gebaut wird, muss den
bereits gespeicherten Wert eines Felds immer als gültige Option
mit-garantieren, auch wenn er nach der aktuellen Berechnung eigentlich
nicht mehr dazugehören würde - sonst wird aus einer reinen
UI-Komfortfunktion (weniger Auswahl-Rauschen) ein Datenverlust-Risiko:
ein Raum, dessen Konfiguration nur noch teilweise zur aktuellen
HA-Bereichs-Struktur passt, muss trotzdem weiterhin änderbar (und sei es
nur, um genau dieses veraltete Feld zu leeren) bleiben.

**27. Direkt nach Lektion 26 gemeldet: Ein geleertes EntitySelector-Feld
lässt sich zwar scheinbar erfolgreich speichern, der alte Wert ist aber
beim nächsten Öffnen wieder da (0.51.2).** Nachdem Lektion 26 das
"gar nicht speicherbar"-Problem behoben hatte, meldete der Nutzer den
nächsten Schritt desselben Vorgangs: "ich kann die Sensoren im Raum zwar
entfernen und auch die Einstellungen speichern, aber beim erneuten
Aufruf der Einstellungen sind diese wieder da" (Esszimmer,
CO2-/Luftfeuchtigkeits-Sensor). Ursache: `async_step_room()` im
Options-Flow merged bislang mit `new_data = {**current, **defaults}` -
"neue Eingaben überschreiben bestehende Werte". Das setzt voraus, dass
JEDES vom Formular abgedeckte Feld beim Absenden im `user_input` steckt,
und sei es als leerer/`None`-Wert - für Zahlen-/Text-Felder ohne festen
Schema-`default` (`_override_selector`, siehe Lektion 14) stimmt das
auch, und genau darauf verließ sich der bisherige Kommentar an dieser
Stelle ("Ein Feld, das jetzt leer gelassen wurde, entfernt eine zuvor
gesetzte Raum-Override wieder"). Für `EntitySelector`-Felder
(`_entity_marker(..., required=False)`) gilt das aber NICHT: Home
Assistants Formular lässt ein geleertes Entity-Feld beim Absenden
komplett weg, statt es als leer/`None` mitzuschicken - der Schlüssel
fehlt in `defaults` dann schlicht komplett. Der Merge behält in diesem
Fall den alten Wert aus `current` unverändert bei, da nur tatsächlich
vorhandene Schlüssel in `defaults` etwas überschreiben - "erfolgreich
gespeichert" täuschte also nur vor, weil der Options-Flow ohne
Fehlermeldung durchlief (der weggelassene Schlüssel ist ja gültig,
schließlich `required=False`), während im Hintergrund schlicht nichts
geändert wurde. Fix: neue Konstante `ROOM_OPTIONAL_ENTITY_KEYS` listet
alle acht über `_entity_marker(..., required=False)` erzeugten
Entity-Felder des Raum-Formulars (`CONF_SONOS_ENTITY`,
`CONF_HUMIDITY_ENTITY`, `CONF_CO2_ENTITY`, `CONF_WINDOW_ENTITY`,
`CONF_SHUTTER_ENTITY`, `CONF_DEHUMIDIFIER_ENTITY`,
`CONF_DEHUMIDIFIER_TANK_FULL_ENTITY`, `CONF_AC_ENTITY`) - direkt nach dem
bisherigen Merge wird für jeden dieser Schlüssel geprüft, ob `defaults`
dafür einen echten (truthy) Wert enthält; falls nicht (weggelassen ODER
explizit leer übermittelt - beide Fälle einheitlich behandelt), wird der
Schlüssel aus `new_data` entfernt, statt den alten Wert stehen zu
lassen. Die Neuanlage eines Raums (`ConfigFlow.async_step_room()`)
ist von diesem Bug nicht betroffen, da dort `data=defaults` direkt ohne
Merge mit einem bestehenden Eintrag verwendet wird - es gibt schlicht
nichts Altes, das stehen bleiben könnte. Lektion, die Lektion 10
präzisiert: Ein flacher `{**current, **defaults}`-Merge ist nur sicher,
wenn ALLE Formularfelder garantiert immer im `user_input` stecken - das
ist bei Home-Assistant-Selectoren nicht einheitlich der Fall
(Zahlen-/Text-Felder ja, `EntitySelector` nein); bei jedem neuen
optionalen Feldtyp explizit prüfen (nicht annehmen), ob ein geleertes
Feld als leerer Wert oder als fehlender Schlüssel übermittelt wird,
bevor man sich auf einen einfachen Merge verlässt.

**28. Lektionen 26/27 hatten den Merge im Options-Flow repariert - der
eigentliche Fehler saß aber schon eine Ebene tiefer, in der
Formular-Definition selbst (0.51.3).** Nutzer-Rückmeldung nach 0.51.2:
"die werte lassen sich immer noch nicht entfernen. merkwürdig ist auch,
dass nach entfernen der sensoren aus den feldern in den feldern
weiterhin der sensorname drinsteht" - das zweite Detail war der
entscheidende Hinweis: Das Feld zeigte den alten Sensornamen nicht nur
nach dem Speichern und erneuten Öffnen wieder an (das hätte noch zur
bisherigen Diagnose gepasst), sondern offenbar bereits beim bloßen
erneuten Anzeigen des Formulars. Ursache: `_entity_marker()` belegte ein
optionales EntitySelector-Feld mit einem aktuell gesetzten Wert bislang
über ein echtes `vol.Optional(key, default=value)` vor - genau das
Muster, vor dem `_override_selector()`s eigener Docstring seit jeher
warnt ("echt optional, kein erzwungener Standardwert"), hier aber nicht
befolgt. Ein `default=` in einer Voluptuous-Marker verankert `value` als
festen Schema-Fallback; Home Assistants Formular-Frontend behandelt ein
sichtbar geleertes Feld mit einem solchen Schema-Default nicht als "jetzt
leer", sondern fällt beim Rendern/Absenden auf genau diesen Fallback
zurück - das Feld ließ sich dadurch praktisch nie wirklich leeren, ganz
unabhängig davon, wie sauber der Merge in `async_step_room()` mit dem
übermittelten `user_input` umging. Die Lektionen 26 und 27 hatten damit
zwar zwei echte, für sich genommen valide Bugs behoben (Auswahllisten-
Filterung schloss den gespeicherten Wert aus; der Merge ignorierte
fehlende Schlüssel nicht korrekt) - aber der eigentliche, vom Nutzer
beobachtete Effekt ("Wert kommt immer wieder zurück") hatte seine
Ursache in einer dritten, bis dahin nicht untersuchten Stelle: der
Schema-Definition selbst, noch bevor überhaupt ein Submit stattfindet.
Fix: `_entity_marker()` verwendet für optionale Felder jetzt wie
`_override_selector()` ausschließlich `description={"suggested_value":
value}` statt `default=value` - der aktuelle Wert wird weiterhin zur
Vorbelegung angezeigt, aber ohne Schema-Fallback, auf den ein geleertes
Feld zurückspringen könnte. Die Lektion-27-Absicherung im Merge
(`ROOM_OPTIONAL_ENTITY_KEYS`) bleibt zusätzlich bestehen und schadet
nicht - unabhängig davon, ob ein geleertes Feld jetzt als leerer Wert
oder weiterhin als fehlender Schlüssel übermittelt wird, greift sie
in beiden Fällen korrekt. Lektion: Ein vom Nutzer nebenbei erwähntes
Detail ("das Feld zeigt den alten Wert schon beim Ansehen wieder an",
nicht erst nach einem erneuten Laden aus dem Speicher) kann die
tatsächliche Fehlerebene präziser eingrenzen als der zuerst gemeldete
Haupteffekt ("lässt sich nicht entfernen") - und ein bereits reparierter
Bug in einer Schicht (hier: Merge-Logik) beweist nicht, dass es nicht
noch einen zweiten, unabhängigen Bug in einer anderen Schicht (hier: der
Formular-Schema-Definition selbst) für denselben beobachteten Effekt
gibt. Bei jeder "Default vs. Suggested-Value"-Entscheidung für ein
optionales Home-Assistant-Formularfeld gilt seitdem durchgängig: nur
echte Pflichtfelder bekommen `default=`, alles andere ausschließlich
`suggested_value` - dieselbe Regel, die `_override_selector()` schon
immer befolgt hatte, aber bis 0.51.3 nicht konsequent auch auf
`_entity_marker()` übertragen wurde.

**29. Der "Totzone neutral"-Fix für die Dashboard-Karte war nur für die
Schließen-Seite vollständig umgesetzt - die Öffnen-Seite fiel weiterhin
unbegrenzt auf den historischen `letzter_grund` zurück (reiner
Dashboard-Karten-Fix, `card_version` 11 → 12, kein Versionsbump nötig).**
Nutzer-Meldung (Esszimmer, Screenshot): Nachdem die CO2-/Luftfeuchtigkeits-
Sensoren aus dem Raum entfernt worden waren (siehe Lektionen 26-28), zeigte
die Karte weiterhin "Öffnen" mit Auslöser "Luftfeuchtigkeit" und einem
Zeitstempel vom selben Tag - obwohl in der Werte-Tabelle darunter gar keine
Luftfeuchtigkeits-Zeile mehr auftauchte (Attribut nicht mehr vorhanden, da
kein Sensor mehr konfiguriert). Die Innentemperatur (22.1 °C) lag zwischen
Schließen- (21.0 °C) und Öffnen-Schwelle (23.0 °C), CO2 (870 ppm) ebenso
zwischen den Schwellen (800/1000 ppm) - keine der beiden verbleibenden
Größen rechtfertigte aktuell ein "Öffnen". Ursache: `live_grund_open`
(bestimmt den Auslöser-Code, wenn der Sensor-Zustand `on`/"Öffnen" ist)
prüfte zwar korrekt `temp_needs_open`/`hum_needs_open`/`co2_needs_open`,
fiel aber im `else`-Zweig unbegrenzt auf `grund_code` (den historischen,
u. U. längst veralteten `letzter_grund`) zurück - anders als das
strukturell identische `comfort_close` auf der Schließen-Seite, das seinen
Rückfallwert bewusst auf die drei einzigen Fälle beschränkt, die sich
wirklich nicht live nachrechnen lassen (`duration`/`outdoor_warmer`/
`outdoor_wetter`, alle drei ausschließlich Schließen-Gründe, siehe README-
Abschnitt "Hervorhebung des ausschlaggebenden Werts"). Für die Öffnen-Seite
gibt es aber gar keinen strukturell entsprechenden Fall: Temperatur,
Luftfeuchtigkeit und CO2 sind als Öffnen-Gründe IMMER live nachrechenbar,
sobald der jeweilige Sensor konfiguriert ist - `grund_code` konnte dort
also nur noch als Krücke für exakt die "Totzone"-Situation dienen, die der
bereits früher eingeführte, in der README ausführlich dokumentierte
Neutral-Mechanismus ("trifft weder ein Live-Check noch dieser Rückfallwert
zu, zeigt die Karte konsequent überall neutral '–'") eigentlich verhindern
sollte. Die README-Dokumentation selbst beschrieb das korrekte Verhalten
bereits akkurat ("`letzter_grund` dient nur noch als Rückfallwert für die
DREI Fälle...") - nur der Code für die Öffnen-Seite hielt sich nicht
daran. Fix: `live_grund_open`s letzter Zweig von `grund_code` auf `''`
geändert - Öffnen-Auslöser werden dadurch ausschließlich live berechnet,
ganz ohne Rückfallwert, symmetrisch zur bereits korrekten Beschränkung auf
der Schließen-Seite. Lokal mit zwei Szenarien gegengetestet (Jinja-Sandbox
mit `StrictUndefined`, siehe Lektion 7): der gemeldete Esszimmer-Fall
zeigt jetzt korrekt neutral (🟢, Empfehlung/Auslöser/Uhrzeit alle "–"),
ein echter, weiterhin live zutreffender Luftfeuchtigkeits-Öffnen-Grund
(Badezimmer-Testfall) bleibt unverändert korrekt rot/orange markiert.
Lektion: Ein als "Totzone neutral"/"live statt historisch"-Prinzip
eingeführter Rückfallwert-Filter (hier: `close_fallback`, beschränkt auf
die drei nicht-live-berechenbaren Gründe) muss bei JEDER Stelle greifen,
an der `letzter_grund` sonst noch unbegrenzt durchgereicht wird - eine
zweite, strukturell parallele Stelle (hier: die Öffnen-Seite derselben
`highlight_code`-Berechnung) kann denselben Bug unabhängig von der bereits
gefixten Stelle enthalten, obwohl die dazugehörige README-Doku bereits das
insgesamt korrekte Verhalten beschreibt - eine korrekt dokumentierte
Absicht ist kein Beleg dafür, dass der Code sie an jeder relevanten Stelle
auch tatsächlich umsetzt.

**30. Nicht jeder "Fenster steht schon richtig, Werte aber noch außerhalb
der Norm"-Fall ist gleich orange - bei den beiden Außenluft-Umkehr-Gründen
ist der Zustand bereits final, nicht nur "wartend" (reiner
Dashboard-Karten-Fix, `card_version` 12 → 13, kein Versionsbump nötig).**
Nutzer-Frage (Badezimmer, Screenshot): Öffnen-Empfehlung wegen
Luftfeuchtigkeit (61 % > 60 %-Schwelle), obwohl die absolute
Luftfeuchtigkeit draußen (11,5 g/m³) höher lag als drinnen (11,1 g/m³) -
Lüften hätte die relative Luftfeuchtigkeit also gar nicht gesenkt. Die
Antwort ergab: Der dafür zuständige Schließen-Mechanismus
(`close_by_humidity_outdoor_reversal`, Lektion 23) blockierte in diesem
Fall, weil `temp_still_needed` bereits `True` war - nicht weil die
Temperatur tatsächlich noch Lüftungsbedarf anzeigte (`open_by_temp` war
`False`, die Innentemperatur lag klar unter der Öffnen-Schwelle), sondern
weil sie schlicht noch nicht bis zur eigenen Schließen-Schwelle gefallen
war. Das ist ein separates, hier nicht behobenes Verhalten (die Schutz-
Logik wurde absichtlich 1:1 von den drei primären Schließgründen für
`close_by_summer_outdoor`/`close_by_humidity_outdoor_reversal`
übernommen, siehe deren Kommentare) - die zweite Nachfrage bezog sich
aber auf einen zweiten, tatsächlich schon in Produktion beobachteten Fall
im Büro, wo dieser Mechanismus BEREITS korrekt gegriffen hatte
(Auslöser "Außen feuchter", Fenster schon geschlossen, Zustand passt) und
trotzdem nur orange statt grün angezeigt wurde. Nutzer-Einschätzung dazu:
Dieser Zustand ist bereits **endgültig**, nicht nur "wartend" - anders
begründet als die bereits bestehende Grün-Ausnahme für CO2 (Lektion 16/17:
niedriges CO2 ist kein Sicherheitsrisiko, daher irrelevant ob das Fenster
überhaupt matcht), aber im Ergebnis ebenso rechtfertigend: Bei den drei
primären Größen (Temperatur/Luftfeuchtigkeit/CO2) bezieht sich die
Orange-Bedeutung ("Fenster passt schon, Werte aber noch außerhalb der
Norm") auf einen INNENWERT, der sich durch die bereits erfolgte
Fenster-Aktion irgendwann normalisieren wird ("wartend"). Bei
"Außen wärmer"/"Außen feuchter" (`outdoor_warmer`/`outdoor_wetter`) ist
die hervorgehobene Zelle dagegen die AUSSEN-Zelle (siehe Lektion 23) - die
ändert sich unabhängig vom eigenen Fensterzustand, es gibt also nichts,
"worauf" das Fenster warten würde: Bleibt es geschlossen, bleibt der
Zustand exakt so, bis sich die Außenbedingungen von selbst ändern - kein
Unterschied zu "sofort" vs. "in 10 Minuten". Wichtiger Unterschied zur
CO2-Ausnahme: Die neue `outdoor_final_exception` gilt NUR, wenn das
Fenster tatsächlich matcht (`is_match`) - anders als bei CO2 (wo Grün
unabhängig vom Fensterzustand gilt, da Lüften trotz niedrigem CO2 nie
schadet) verschlimmert Weiterlüften hier tatsächlich die Lage
(Luftfeuchtigkeit/Temperatur von draußen), ein Fenster-Mismatch bei
diesen beiden Gründen bleibt daher weiterhin korrekt **rot**, nicht grün.
Fix: `outdoor_final_exception` (analog zu `co2_close_exception`, aber
zusätzlich an `is_match` gebunden) ersetzt `match_icon`/`highlight_open`
von Orange auf Grün, ausschließlich innerhalb des ohnehin schon
vorhandenen Match-Zweigs. Lokal mit Match- und Mismatch-Fall
gegengetestet (Jinja-Sandbox, `StrictUndefined`). Lektion: "Fenster passt
schon, Werte noch außerhalb der Norm" ist nicht immer dasselbe
Orange-Muster - entscheidend ist, ob die hervorgehobene Größe durch die
bereits erfolgte Aktion selbst noch beeinflusst/normalisiert werden kann
(Innenwert, "wartend" → Orange) oder komplett extern ist und sich ohnehin
nicht durch das eigene Fenster ändert (Außenwert, bereits "endgültig" →
Grün, aber nur im Match-Fall, da hier - anders als bei der CO2-Ausnahme -
ein Mismatch tatsächlich schadet statt nur überflüssig zu sein).

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
  eingefügt - Änderungen daran erfordern keinen `manifest.json`-
  Versionsbump/kein Release. Seit 0.50.0 hat die Karte aber eine eigene,
  unabhängige Versionierung (Start bei `card_version = 1`, Konstante ganz
  am Anfang der Jinja-Vorlage): muss bei **jeder** inhaltlichen Änderung
  an der Karte hochgezählt werden, zusammen mit dem "Aktuelle
  Karten-Version: N"-Hinweis direkt über dem Codeblock im README - dient
  dem Nutzer als Selbstdiagnose (Übersichts-Tabelle zeigt "Karte: N" im
  Dashboard), ob seine eingefügte Karte noch dem aktuellen Stand
  entspricht, da die Karte (anders als der Code) nie automatisch
  aktualisiert wird.
- **Nutzer-Vorgabe (0.50.0+):** Bei jeder Änderung an der Dashboard-Karte
  zusätzlich zum README-Diff immer den vollständigen, aktuellen YAML-Code
  direkt im Chat posten (als Code-Block, nicht nur als angehängte Datei) -
  damit er ohne Dateizugriff/Download direkt kopiert werden kann. Grund:
  ein per `SendUserFile` verschicktes YAML allein hatte beim Nutzer zu
  Unsicherheit geführt, ob wirklich der neueste Stand eingefügt wurde.
