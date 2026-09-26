# CLAUDE.md – Projektkontext für Claude Code

Diese Datei fasst zusammen, was in einer ausführlichen Entwicklungs-Session
mit Claude (claude.ai-Chat) zu diesem Projekt erarbeitet wurde – gedacht als
Einstiegspunkt, damit Claude Code nicht bei null anfängt. Sie ersetzt nicht
die README.md (die ist die eigentliche Nutzerdokumentation), sondern
ergänzt sie um Dinge, die nur "hinter den Kulissen" während der Entwicklung
wichtig wurden.

## Projektüberblick

Home-Assistant Custom Integration `ha_smart_ventilation` (Anzeigename seit
0.59.0 "Smart Climate", technischer Domain-Name unverändert
`ha_smart_ventilation`, siehe Lektion 43): pro Raum ein
`binary_sensor.lueften_empfohlen_<raum>`, der
anhand von Innen-/Außentemperatur und -luftfeuchtigkeit empfiehlt, ob
gelüftet werden sollte. Zusätzlich optionale Steuerung von Luftentfeuchter,
Klimaanlage und Heizung (Comfort-/Standby-Sollwerte), sowie drei
Benachrichtigungswege (Sprachausgabe/TTS, App Push, persistente
Web-Benachrichtigung).

Aktuelle Version: siehe `custom_components/ha_smart_ventilation/manifest.json`.
GitHub: `ludgerbeckmann/ha_smart_ventilation` (Domain `ha_smart_ventilation`).

## Feste Arbeitsanweisungen (immer befolgen, ohne erneute Aufforderung)

- **Vor jeder inhaltlichen Umsetzung (Code-Änderung, neue/geänderte
  Config-Flow-Felder, neue Entitäten, Doku-Änderungen mit Verhaltens-
  Auswirkung) zuerst eine kurze Zusammenfassung der geplanten Umsetzung im
  Chat posten und auf Bestätigung/Korrektur durch den Nutzer warten, bevor
  mit Branch/Commit/PR begonnen wird** (seit 0.60.0, vom Nutzer
  ausdrücklich gewünscht: "es macht mehr Sinn, dass du zukünftig zuerst
  bei Änderungen diese Zusammenfassung ausgibst, bevor es umgesetzt wird,
  um nochmal sicherzustellen, dass alles wie erwartet umgesetzt wird").
  Die Zusammenfassung nennt knapp: welche Dateien/Bereiche betroffen sind,
  welche neuen Optionen/Entitäten/Konstanten entstehen, wie sich das
  Verhalten ändert, und - bei Unklarheiten im Auftrag - welche Annahmen
  getroffen wurden. Kein vollständiger Implementierungsplan mit Codezeilen
  nötig, aber genug, damit der Nutzer Scope und Ansatz vorab erkennen und
  bei Bedarf korrigieren kann, BEVOR Code geschrieben wird - nicht erst im
  fertigen Diff/PR. Gilt für jede inhaltliche Änderung, nicht nur
  besonders große oder mehrdeutige; eine bereits laufende `AskUserQuestion`-
  Rückfrage zur Scope-Klärung ersetzt diese Zusammenfassung nicht
  automatisch, da sie meist nur einzelne Unklarheiten klärt, nicht den
  gesamten geplanten Umsetzungsumfang. Rein exploratorische Fragen ("was
  hältst du von X", siehe bereits bestehende allgemeine Regel dazu)
  bleiben davon unberührt - dort wird ohnehin nicht ungefragt umgesetzt.
- **Dashboard-Karte, bei jeder inhaltlichen Änderung (seit 0.50.0, vom
  Nutzer wiederholt bestätigt):**
  1. `card_version` in der Jinja-Vorlage hochzählen und den "Aktuelle
     Karten-Version: N"-Hinweis im README direkt darüber mitziehen (siehe
     "Versionierung & Release" unten).
  2. Ausschließlich den **Inhalt des `content:`-Abschnitts** (die
     Jinja-Zeilen selbst, ohne die umgebenden `type: markdown`/`title:`/
     `content: >`-YAML-Hüllzeilen) zusätzlich zum README-Diff **direkt als
     Text in der Chat-Antwort posten**, in einem Markdown-Code-Block -
     nicht nur als angehängte Datei (`SendUserFile`), nicht nur per
     Verweis auf die README, und **nicht über die Ausgabe eines Bash-/
     Tool-Aufrufs** (z. B. `cat`) - Tool-Ergebnisse werden dem Nutzer
     nicht angezeigt, nur die eigene Textausgabe der Antwort selbst. Gilt
     für JEDE Änderung an der Karte, auch kleine/kosmetische - unabhängig
     davon, ob dafür ein `manifest.json`-Versionsbump nötig ist. Grund: ein
     rein per Datei-Anhang verschicktes YAML hatte beim Nutzer zu
     Unsicherheit geführt, ob wirklich der neueste Stand eingefügt wurde;
     eine über einen Tool-Aufruf ausgegebene Datei kam beim Nutzer
     überhaupt nicht an; der komplette YAML-Rahmen (`type:`/`title:`) ist
     für den Nutzer irrelevant, da er nur den `content:`-Teil in seine
     bereits bestehende Karte einfügt.
  3. Vor dem Posten immer lokal in der Jinja-Sandbox testen (siehe
     Lektion 7) - `StrictUndefined` nicht vergessen.

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
2. sonst globale Einstellung aus dem Eintrag "Smart Climate Optionen"
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

**31. Laufzeit-Tracking für Luftentfeuchter/Klimaanlage/Dusche - bewusst
innerhalb von `extra_state_attributes` statt in `_evaluate()` (0.52.0).**
Neue Dashboard-Spalte "Laufzeit" (seit wann das jeweilige Gerät
ununterbrochen läuft bzw. die Duscherkennung anschlägt). Für
Luftentfeuchter/Klimaanlage naheliegend wäre gewesen, den Zeitstempel wie
üblich in `_evaluate()` zu pflegen (siehe `_open_since`,
`_frost_block_since`) - das würde hier aber zu denselben Inkonsistenzen
führen, die Lektion 19 für `luftentfeuchter_an`/`klimaanlage_an` bereits
beheben musste: `_evaluate()` läuft nur bei einer Zustandsänderung einer
verfolgten Eingangs-Entität (Temperatur/Feuchtigkeit/CO2/Fenster/...),
NICHT bei einer Zustandsänderung der Geräte-Entität selbst (die wird
absichtlich nicht verfolgt, siehe `async_added_to_hass()`), Lektion 19
hat `_is_device_on()` deshalb als Live-Read direkt in
`extra_state_attributes` verankert. Ein separat in `_evaluate()`
gepflegter Laufzeit-Zeitstempel würde also potenziell veraltet neben
einem live-aktuellen `luftentfeuchter_an` stehen (z. B. Gerät gerade
manuell eingeschaltet, aber `_evaluate()` noch nicht erneut gelaufen -
"an" zeigt schon `true`, "seit wann" wäre noch `None`/veraltet). Fix:
`_dehumidifier_on_since`/`_ac_on_since` werden direkt neben dem
ohnehin schon vorhandenen `_is_device_on()`-Aufruf in
`extra_state_attributes` selbst gepflegt (Transition erkannt, sobald der
Live-Wert `True` wird; auf `None` zurückgesetzt, sobald er `False` ist) -
beide Werte bleiben dadurch untereinander und mit `luftentfeuchter_an`
zwangsläufig konsistent, da sie aus demselben Live-Read im selben Moment
stammen. Eine Zustandsmutation innerhalb einer Property ist unüblich,
hier aber unproblematisch: der Vorgang ist idempotent (wiederholtes Lesen
ohne echte Zustandsänderung des Geräts ändert nichts) und exakt das
Muster, das `_is_device_on()` an dieser Stelle bereits etabliert hat. Für
die Dusche gilt das nicht - `self._showering` wird bereits in
`_evaluate()` gesetzt (dort steht ohnehin schon der aktuelle
Feuchtigkeits-Messwert zur Verfügung), daher `_shower_on_since` direkt
dort neben `self._showering` gepflegt, keine Notwendigkeit für den
Property-Ansatz. Wie bei `_open_since` (Lektion 3) werden alle drei
Zeitstempel über `RestoreEntity` wiederhergestellt, damit nach einem
Neustart nicht fälschlich "0 Min" angezeigt wird, obwohl ein Gerät schon
länger lief - ein falsch wiederhergestellter Wert (Gerät zwischenzeitlich
tatsächlich aus) korrigiert sich beim nächsten Lesen von
`extra_state_attributes` bzw. der nächsten `_evaluate()` sofort selbst.
Lektion: Wenn ein Attribut aus einem bereits etablierten Live-Read
abgeleitet wird (hier: "seit wann" aus demselben `_is_device_on()`, der
auch "an" liefert), muss die Pflege an genau derselben Stelle erfolgen,
sonst kann leicht ein zweiter, unabhängiger Wert entstehen, der mit dem
ersten desynchronisiert - ein reines "wo pflegen wir sonst Zeitstempel"-
Muster (hier: `_evaluate()`) ist keine Garantie dafür, dass es für JEDEN
neuen Zeitstempel die richtige Stelle ist.

**32. Die "bereits gelöst, nicht nur wartend"-Grünfärbung eines
Schließen-Auslösers (Lektion 30) war nur für Räume MIT Fenster
umgesetzt - bei Räumen ohne Fenster griff sie überhaupt nicht, weil
deren Farblogik in einem eigenen, komplett getrennten Codezweig steht
(reiner Dashboard-Karten-Fix, `card_version` 18 → 19, kein
Versionsbump nötig).** Nutzer-Meldung (Flur KG, kein Fenster
konfiguriert): Auslöser "Luftfeuchtigkeit" mit bereits unter die
Schließen-Schwelle gefallenem Wert (54,6 % < 55 %-Schwelle), Karte
zeigte trotzdem weiterhin 🟠 statt 🟢 - obwohl genau dieser Fall bei
einem Raum MIT Fenster durch Lektion 30 (`comfort_close_resolved_exception`)
bereits korrekt grün würde. Ursache: Die Berechnung von `match_icon` für
Räume ohne Fenster läuft in einer eigenen Zeile VOR dem `{% if
window_entity %}`-Block (`'🟠 ' if no_window else '🔴 '` als reiner
Fallback) und wusste von `comfort_close_resolved_exception` nichts - die
Variable wurde zwar schon berechnet, aber nur innerhalb des
Fenster-Blocks tatsächlich ausgewertet (`is_match` als zusätzliche
Bedingung), der für fensterlose Räume nie betreten wird. Fix:
`no_window_resolved = no_window and comfort_close_resolved_exception`
(ohne `is_match`-Bedingung, da es dafür kein Fenster gibt) wird jetzt
zusätzlich in die 🟢-Bedingung von sowohl `match_icon` als auch
`highlight_open` aufgenommen - symmetrisch zur bereits bestehenden
CO2-Ausnahme, die ja ebenfalls unabhängig vom Fensterzustand gilt.
Dabei ergab die Rückfrage beim Nutzer eine wichtige Einschränkung, die
über die reine Symmetrie zu Lektion 30 hinausgeht: Ist speziell
Luftfeuchtigkeit der Auslöser UND für den Raum ein Luftentfeuchter
konfiguriert, soll es trotzdem bei 🟠 bleiben
(`no_window_dehum_exception`, geprüft über dieselbe `a.luftentfeuchter_an
is defined`-Markierung wie schon in der Geräte-Tabelle) - der
Luftfeuchtigkeitswert hängt hier eng mit dem Luftentfeuchter zusammen
und soll bewusst sichtbar bleiben, statt in Grün zu verschwinden, auch
wenn er die Schließen-Schwelle bereits erreicht hat. Andere
Schließen-Gründe (Temperatur, Außen wärmer/feuchter) sind von dieser
Ausnahme nicht betroffen, ebenso wenig Luftfeuchtigkeit in Räumen ohne
Luftentfeuchter. Lektion: Eine Farb-/Zustandslogik, die für den
Fenster-Fall bereits korrekt implementiert ist (Lektion 30), aber in
einem strukturell getrennten Codezweig für einen anderen Fall (hier:
kein Fenster, siehe bereits Lektion 17) eine eigene, parallele
Berechnung hat, überträgt sich nicht automatisch - bei jeder neuen
"eigentlich schon gelöst"-Ausnahme prüfen, ob sie in JEDEM Zweig
greifen muss, der dieselbe Grundfrage (hier: Auslöser ist ein
Schließen-Grund) unabhängig behandelt.

**33. `_is_device_on()` (Lektion 19) behandelte eine komplett aus dem
Zustandsautomaten verschwundene Geräte-Entität identisch zu einer bloß
vorübergehend nicht verfügbaren - beides ergab "aus", nicht "gar nicht
berücksichtigen" (0.52.1).** Nutzerwunsch: Wird der Integrationseintrag
der Klimaanlage deaktiviert (Entität dadurch komplett aus
`hass.states` entfernt, nicht nur `unavailable` gemeldet), soll die
Klimaanlage für diesen Raum vollständig unberücksichtigt bleiben - kein
Steuerversuch, keine Geräte-Tabellen-Zeile im Dashboard. Bisher lieferte
`self.hass.states.get(entity_id) is None` (Integrationseintrag
deaktiviert) und `state.state in ("unknown", "unavailable")` (Entität
registriert, Gerät nur kurz offline) in `_is_device_on()` beide `False`
zurück - für die reine "an"-Anzeige richtig (Lektion 19), aber
`extra_state_attributes` exponierte trotzdem weiterhin
`luftentfeuchter_an`/`klimaanlage_an` (nur als `False`) sowie den
zugehörigen `_grund`-Text, wodurch die Dashboard-Karte weiterhin eine
(inhaltlich müßige) Geräte-Zeile zeigte - und `_update_single_device()`
versuchte weiterhin, `turn_on`/`turn_off` gegen eine nicht mehr
existierende Entität aufzurufen (dank vorhandenem
`try/except HomeAssistantError` zwar folgenlos, aber unnötig). Fix:
neue Methode `_device_entity_missing(entity_id)` (`hass.states.get(...)
is None`) - bewusst als eigene, von `_is_device_on()` unabhängige
Prüfung, da beide Fälle unterschiedliche Antworten auf unterschiedliche
Fragen liefern müssen ("ist das Gerät an?" bleibt bei jeder
Nichtverfügbarkeit `False`; "soll das Gerät überhaupt berücksichtigt
werden?" nur bei tatsächlichem Verschwinden `False`). Eingesetzt an
zwei Stellen: (1) `extra_state_attributes` - die
Luftentfeuchter-/Klimaanlage-Blöcke werden komplett übersprungen (keine
Attribute gesetzt), sobald die jeweilige Entität fehlt, wodurch die
Geräte-Tabellen-Zeile automatisch verschwindet (sie hängt an
`a.luftentfeuchter_an is defined` bzw. `a.klimaanlage_an is defined`
im Karten-Template) - kein Karten-Update nötig, da die Karte diese
Bedingung strukturell schon immer korrekt abgefragt hat, nur die
Python-Seite lieferte bisher immer einen Wert. (2)
`_update_single_device()` - früher Rücksprung ohne Steuerversuch,
zusätzlich wird der interne Soll-Zustand-Tracker (`_dehumidifier_state`/
`_ac_state`) auf `None` zurückgesetzt, damit bei Rückkehr der Entität
(Integrationseintrag wieder aktiviert) keine veraltete Annahme über den
zuletzt kommandierten Zustand übernommen wird, sondern eine echte
Neusynchronisierung stattfindet. Bewusst symmetrisch für Luftentfeuchter
UND Klimaanlage umgesetzt, obwohl nur die Klimaanlage konkret gemeldet
wurde - beide teilen sich exakt denselben Code (`_is_device_on()`,
`_update_single_device()`), eine Asymmetrie zwischen ihnen wäre eine
willkürliche Lücke gewesen (vgl. Lektion 18/43: ein Fix für einen
strukturell identischen zweiten Kanal sofort mitziehen, nicht erst auf
explizite Nachfrage). Lektion: "Nicht verfügbar" und "Entität existiert
nicht mehr" sind zwei unterschiedliche Tatsachen, auch wenn eine
einzelne Prüfung (hier: `_is_device_on()`) für IHREN Zweck (reine
An/Aus-Anzeige) beide korrekt gleich behandeln durfte - ein zweiter,
strukturell andersartiger Verwendungszweck (hier: "soll überhaupt
etwas angezeigt/gesteuert werden") kann dieselbe Unterscheidung
brauchen, die die erste Prüfung bewusst verwischt hat, und verdient
dann eine eigene, zusätzliche Prüfung statt einer Anpassung der
bestehenden.

**34. Das Energiespar-Argument hinter `dehumidifier_pause_open_window`
(Lektion 24) gilt nicht mehr, sobald ohnehin überschüssige
Einspeiseleistung verfügbar ist (0.53.0).** Auf Nutzerwunsch: Der
Luftentfeuchter soll bei zu hoher Luftfeuchtigkeit auch bei offenem
Fenster starten, sofern genug Einspeiseleistung vorhanden ist. Die
bestehende Pausierung (Lektion 24) begründet sich rein energetisch -
gegen ständig nachströmende, nicht trockenere Außenluft anzuarbeiten
verschwendet sonst unnötig Strom. Ist aber ohnehin PV-Überschuss
vorhanden, der andernfalls ungenutzt bliebe (bzw. eingespeist würde),
entfällt genau dieses Argument - der Luftentfeuchter zu betreiben
kostet dann effektiv nichts zusätzlich. Fix: `dehumidifier_pause_open_window`
prüft jetzt zusätzlich `not (power_entity_configured and
self._check_power_ok())` - identischer Leistungs-Check wie beim
eigentlichen Einschalten in `_update_single_device()`. Wichtig dabei:
Die Ausnahme greift nur, wenn tatsächlich ein Leistungssensor
konfiguriert ist (`power_entity_configured`) - ohne Sensor bleibt die
Pausierung unverändert bestehen, da `_check_power_ok()` ohne
konfigurierten Sensor selbst immer `True` liefert (siehe seine eigene
Dokumentation, "ohne Leistungssensor immer erfüllt") - ein naives
`not self._check_power_ok()` ohne diese zusätzliche Prüfung hätte die
gesamte Lektion-24-Pausierung für alle Nutzer OHNE Leistungssensor
versehentlich abgeschaltet, obwohl die neue Ausnahme explizit nur für
den Fall "es ist tatsächlich Überschuss da" gedacht war, nicht für "es
gibt keine Information darüber". Lektion: Bei einer Bedingung, die eine
bestehende Sicherheits- oder Sparsamkeits-Maßnahme unter einer neuen
Voraussetzung aufhebt, immer explizit prüfen, ob diese Voraussetzung
selbst einen "harmlosen Standardwert" hat, der bei fehlender Konfiguration
greift (hier: `_check_power_ok() == True` ohne Sensor) - sonst wird aus
einer eng gemeinten Ausnahme ("nur wenn wir wirklich wissen, dass
Überschuss da ist") versehentlich eine viel zu breite ("immer, außer
wir wissen, dass es NICHT reicht").

**35. `hass.services.async_call(..., blocking=False)` lässt einen
Schema-Validierungsfehler NICHT im aufrufenden `try/except` landen - der
Fehler passiert in einem intern erzeugten, unbeobachteten Task und wird
erst beim Garbage Collector als "Task exception was never retrieved"
sichtbar (0.53.1).** Nutzer-Meldung: Log zeigt 2432 Vorkommnisse
derselben Fehlermeldung seit einem bestimmten Zeitpunkt, Traceback über
`_notify()` → `hass.services.async_call("notify", "send_message", ...)`
→ `probatio.error.MultipleInvalid: not a valid option at 'data'`
(Schema-Validierung lehnt das `data`-Feld komplett ab). Ursache: Die als
"App-Benachrichtigungsziel" konfigurierte notify-Entität ist offenbar
keine echte Companion-App-Entität (z. B. eine E-Mail- oder
Messenger-notify-Entität), die kein `data`-Feld unterstützt - diese
Integration übergibt dort aber immer `data: {"tag": ...}` fürs "clean
notification"-Muster (Lektion 18). Der eigentliche Konfigurationsfehler
beim Nutzer ist damit klar, aber das viel dringendere technische Problem
war der Umgang damit: Der Aufruf lief mit `blocking=False` (wie überall
sonst in dieser Integration für Geräte-Steuerbefehle üblich, siehe
`_set_device_state()`/`_set_shutter()`) - dabei validiert Home Assistant
das `service_data`-Schema nicht synchron im aufrufenden `await`, sondern
innerhalb eines intern erzeugten, von uns nicht referenzierten
`asyncio.Task`. Ein `try/except HomeAssistantError` um den `await` herum
(wie es `_set_device_state()`/`_set_shutter()` bereits für den Fall
"Service/Entity existiert nicht" korrekt einsetzen - DAS passiert
nämlich synchron, noch vor dem Erzeugen des Tasks) fängt einen
SCHEMA-Validierungsfehler deshalb nicht ab - er entkommt komplett am
eigenen Fehlerbehandlungscode vorbei und taucht erst an, wenn Python den
verwaisten Task aufräumt, mit generischer "Task exception was never
retrieved"-Meldung statt einer hilfreichen, raum-/entitätsbezogenen
Warnung - und das bei JEDER Neubewertung erneut, nicht nur einmalig.
Fix: neue Methode `_send_mobile_push()` bündelt beide bisherigen
`notify.send_message`-Aufrufstellen (`_notify()` fürs eigentliche
Senden, `_clear_mobile_notification()` fürs Auflösen - identisches
Muster, siehe Lektion 18/43) und ruft mit `blocking=True` auf, wodurch
ein Validierungsfehler jetzt synchron im `await` ankommt und vom
`except HomeAssistantError` abgefangen wird - stattdessen eine einzelne,
klare `_LOGGER.warning()` pro betroffenem Ziel ("unterstützt diese
notify-Entität ein `data`-Feld mit `tag`?"), die dem Nutzer sofort sagt,
was zu tun ist (richtige Companion-App-Entität auswählen), statt
2432 kryptische Tracebacks. Lektion: `blocking=False` plus
`try/except` ist kein allgemein sicheres Muster, um Fehler bei
`hass.services.async_call()` abzufangen - es fängt nur Fehler, die VOR
dem Erzeugen des Hintergrund-Tasks auftreten (Service-/Entity-Existenz),
nicht aber Fehler AUS der eigentlichen Service-Ausführung (Schema-
Validierung, Handler-Exceptions) - dafür ist zwingend `blocking=True`
nötig, mit dem entsprechenden (meist vernachlässigbaren) Laufzeit-
Overhead, das tatsächliche Warten auf den Abschluss des Service-Aufrufs.

**36. Die Auswahlliste für App-Benachrichtigungsziele filterte nur auf
die `notify`-Domain, nicht auf Companion-App-Entitäten speziell -
direkte Folge von Lektion 35 (0.53.2).** Nach dem Fix für die
Log-Flut (Lektion 35) fragte der Nutzer folgerichtig, ob die
Integration nicht von vornherein verhindern sollte, dass eine
ungeeignete notify-Entität überhaupt auswählbar ist. Bisher nutzten
beide betroffenen `EntitySelector`-Definitionen (Raum-Formular in
`_build_room_schema()` sowie die globalen Standard-Ziele in
`_build_global_edit_schema()`) nur `domain="notify"` - das umfasst
JEDE notify-Integration (E-Mail, Messenger, etc.), nicht nur die Home
Assistant Companion App, deren notify-Entitäten zuverlässig das für
das "Clean Notification"-Muster (Lektion 18) benötigte `data`-Feld mit
`tag` unterstützen. Fix: `EntitySelectorConfig` bekommt zusätzlich
`integration="mobile_app"` - schränkt die im Formular angebotene Liste
auf tatsächliche Companion-App-Ziele ein. Wichtige Abgrenzung zu den
Lektionen 26-28 (dort verursachte ein zu enger `include_entities`-Filter
handfeste Speicher-Bugs für bereits gespeicherte, jetzt aus der Liste
gefallene Werte): `domain`/`integration`-Filter bei `EntitySelector`
sind in Home Assistant reine Frontend-Hinweise für den Auswahldialog -
anders als `include_entities`/`exclude_entities` werden sie von der
Selector-eigenen Schema-Validierung beim Absenden NICHT durchgesetzt.
Ein bereits gespeichertes, nicht-Companion-App-Ziel (z. B. aus einer
Zeit vor diesem Fix, oder nachträglich per YAML gesetzt) bleibt daher
weiterhin gültig und speicherbar - nur die Auswahl NEUER Ziele über das
Formular wird eingeschränkt. Trotzdem kein Vollschutz: Weiterhin
möglich bleibt ein Companion-App-Ziel, das der Nutzer nachträglich
außerhalb dieser Integration löscht/umbenennt, oder eine zukünftige
Notify-Integration, die sich fälschlich als `mobile_app` meldet - Lektion 35s
Warnung beim tatsächlichen Sendeversuch bleibt deshalb bewusst als
zweite Absicherungsebene bestehen, nicht nur als Übergangslösung. Lektion:
Nicht jeder scheinbar strengere Selector-Filter (`domain`, `integration`,
`device_class`) hat dieselbe Durchsetzungsstärke wie `include_entities`/
`exclude_entities` - bevor ein neuer Filter als Fix für "falsche
Werte gar nicht erst anbieten" eingeführt wird, prüfen, ob er rein
UI-seitig wirkt (dann bleibt zusätzlich eine echte Validierung/Fehler-
behandlung nötig, wie hier durch Lektion 35 bereits vorhanden) oder ob
er tatsächlich in die Schema-Validierung eingreift (dann gilt die
Lektion-26-Vorsicht: den bereits gespeicherten Wert immer mit
einschließen).

**37. Die Ansage-Lautstärke wurde vor `tts.speak` gesetzt, aber nie wieder
zurückgesetzt - bewusst dokumentiert, aber ein Nutzer bemerkte es
trotzdem als Problem (0.54.0).** Nutzerfrage: "kann es sein dass die
Lautstärke bei Ausgabe über Lautsprecher nicht wieder zurückgesetzt wird
auf den ursprünglichen Wert?" - Antwort: ja, exakt so, und zwar seit
jeher bewusst so dokumentiert (`_play_tts()`-Docstring und README:
"danach nicht automatisch zurückgesetzt - die Lautsprecher bleiben auf
dieser Lautstärke stehen"). Strukturell verwandt mit Lektion 20 (ein
dokumentiertes Verhalten ist kein Beleg dafür, dass es nicht trotzdem
als Bug empfunden wird) - hier aber ohne vorherige Fehlinterpretation
einer Rückfrage, sondern eine direkte, zutreffende Vermutung des
Nutzers. Fix: `_get_current_volumes()` liest vor dem Setzen der
Ansage-Lautstärke den aktuellen `volume_level` jedes Lautsprechers aus
dem Zustandsautomaten (Lautsprecher ohne numerischen Wert, z. B. aktuell
aus, werden ausgelassen - für sie wird später auch nichts
zurückgesetzt). Die eigentliche Schwierigkeit war nicht das Merken des
Werts, sondern das Zurücksetzen **danach**: `tts.speak` liefert kein
plattformübergreifend zuverlässiges "Wiedergabe beendet"-Ereignis - genau
dieselbe Einschränkung, die den Docstring bereits davon abhält, das
Pausieren/Fortsetzen (siehe README, "Pausieren vs. Überlagern")
automatisch zu synchronisieren. Für die Lautstärke wurde hier trotzdem
eine pragmatische Lösung gewählt, statt es wie beim Pausieren ganz
offenzulassen: `_restore_tts_volume()` schätzt die Sprechdauer aus der
Nachrichtenlänge (rund 150 Wörter/Minute plus Pufferzeit für TTS-
Generierung/Netzwerk) und wartet entsprechend lange, bevor sie
zurücksetzt - als eigener, über `hass.async_create_task()` losgelöster
Hintergrund-Task, damit `_notify()`/`_evaluate()` nicht auf die
geschätzte Ansagedauer warten. Bewusst als Heuristik akzeptiert (keine
exakte Synchronisation nötig, ein paar Sekunden Abweichung bei sehr
langen Ansagen oder einem langsamen TTS-Dienst sind unkritisch) - anders
als z. B. bei Frostschutz (Lektion 2/11/12), wo Fehleinschätzungen
sicherheitsrelevant wären, geht es hier nur um Nutzerkomfort. Lektion:
Nicht jede "plattformübergreifend nicht zuverlässig lösbar"-Einschränkung
(hier: kein Wiedergabe-Ende-Ereignis) bedeutet automatisch "also gar
nicht lösbar" - wo für einen strukturell ähnlichen Fall (Pausieren)
bereits bewusst auf eine Lösung verzichtet wurde, kann für einen
anderen Fall (Lautstärke) trotzdem eine hinreichend gute Heuristik
(Zeitschätzung) angemessen sein, wenn die Konsequenz eines leicht
falschen Timings gering ist.

**38. `_room_override_placeholders()` (Lektion 14) deckte nur die
Zahlen-Overrides aus `_THRESHOLD_FIELDS` ab - die Tri-State-Bool-
Overrides (`_tri_state_bool_selector()`) und der Listen-Override
`mobile_targets` hatten nie einen "Aktuell global: X"-Hinweis bekommen,
und die Sprachausgabe-Lautstärke war überhaupt nicht raum-überschreibbar
(0.55.0).** Nutzer-Nachfrage direkt im Anschluss an Lektion 37 (drei
Punkte in einer Nachricht): (a) "im Bereich Benachrichtigungsmethoden
fehlt die Info was der aktuelle Standardwert ist, wenn ein Feld leer
gelassen wird - ist das auch woanders noch der Fall?", (b) "die
Lautstärke für Sprachausgabe kann noch nicht je Raum geändert werden",
(c) "bitte testweise alle Abschnitte standardmäßig eingeklappt
darstellen".

Zu (a): `_room_override_placeholders()` iterierte seit Lektion 14 nur
über `_THRESHOLD_FIELDS` (reine Zahlenwerte mit Einheit) - `mobile_enabled`/
`persistent_enabled` (`_tri_state_bool_selector()`) und `mobile_targets`
(eine Liste von Notify-Zielen) wurden dabei nie berücksichtigt, obwohl
ihre `data_description`-Texte im Formular exakt dasselbe "Leer = globale
Einstellung verwenden"-Muster verwenden wie die Zahlenfelder - nur ohne
den Zusatz, WAS diese globale Einstellung aktuell ist. Bei der gezielten
Suche nach weiteren Stellen mit derselben Lücke ("ist das auch woanders
noch der Fall?") fand sich eine dritte, strukturell identische Stelle im
Abschnitt "Parameter": `humidity_priority_over_duration` (ebenfalls
`_tri_state_bool_selector()`) hatte denselben Text-Baustein ohne
Ist-Wert-Angabe. Fix: `_room_override_placeholders()` erweitert um einen
zweiten Durchlauf für die drei Tri-State-Bool-Felder (`CONF_MOBILE_ENABLED`,
`CONF_PERSISTENT_ENABLED`, `CONF_HUMIDITY_PRIORITY_OVER_DURATION` - liefert
"Ja"/"Nein" als Text) sowie eine eigene Behandlung für `CONF_MOBILE_TARGETS`
(Liste der global hinterlegten `notify.*`-Entity-IDs, kommagetrennt, sonst
"keine"). Alle sechs betroffenen `data_description`-Texte in
`strings.json`/`translations/{de,en}.json` (je zweimal: Config- und
Options-Flow-Schritt "room") um "Aktuell global: ｛global_x｝" ergänzt -
mit echten, unescapten Platzhaltern wie bei den Zahlenfeldern (Lektion 14
gilt unverändert: Fullwidth-Klammern/Lektion 8 nur für Text OHNE echte
Platzhalterbefüllung, hier wird aber echt befüllt).

Zu (b): Der Codepfad unterstützte einen Raum-Override für
`CONF_TTS_VOLUME` bereits vollständig, ohne dass es hier eine eigene
Änderung dafür brauchte - `_play_tts()` liest die Lautstärke schon
immer über `self._effective(CONF_TTS_VOLUME, DEFAULT_TTS_VOLUME)`
(Raum-Override → global → Standardwert), und `CONF_TTS_VOLUME` steckte
schon lange in `_THRESHOLD_FIELDS` (dadurch bekam es schon vorher
automatisch einen `global_tts_volume`-Platzhalter, obwohl das Feld
selbst im Raum-Formular gar nicht existierte). Es fehlte ausschließlich
die UI: `_build_room_schema()` erzeugte nie einen `_override_selector()`
für dieses Feld. Exakt dasselbe Muster wie die bereits in CLAUDE.md
("Offene/mögliche nächste Schritte") vermerkte Lücke bei den
Benachrichtigungstexten ("Codepfad würde einen Raum-Override bereits
unterstützen, dafür fehlt nur die UI") - hier aber jetzt behoben statt nur
vermerkt. Fix: neues Feld im Abschnitt "Benachrichtigungsmethoden" (direkt
nach der Lautsprecher-Auswahl, da inhaltlich zusammengehörig), per
`_override_selector(CONF_TTS_VOLUME, defaults)` - dieselbe Handvoll
Zeilen wie bei jedem anderen der zwölf bestehenden Overrides, keine
Backend-Änderung nötig.

Zu (c): `section(..., {"collapsed": bool})` wird an sieben Stellen für
sechs verschiedene Abschnitte gesetzt (Raum: Benachrichtigungsmethoden/
Sensoren waren `False`, Parameter/Geräte bereits `True`; global:
Sensoren/Parameter waren `False`, Benachrichtigungstexte bereits `True`) -
auf Nutzerwunsch alle auf `True` gesetzt, ausdrücklich "testweise" (siehe
Wortlaut), also potenziell wieder rückgängig zu machen, falls sich das in
der echten Oberfläche nicht bewährt - keine strukturelle Änderung, rein
kosmetisch am Formular.

`manifest.json` 0.54.0 → 0.55.0 (Minor wegen des neuen Raum-Overrides für
die Sprachausgabe-Lautstärke - alle drei Punkte kamen gebündelt in einer
Nachricht, daher ein einzelner Bump für alle drei zusammen). Lektion: Wird
eine wiederkehrende Formular-Lücke (hier: fehlender "Aktuell global"-
Hinweis) für einen Feldtyp gefixt (Zahlenfelder, Lektion 14), aber ein
zweiter, strukturell ähnlicher Feldtyp (Tri-State-Bool, Listen) folgt
demselben "Leer = global"-Textmuster, ohne dass die ursprüngliche
Fix-Funktion ihn mit abdeckt - eine gezielte Nutzer-Nachfrage ("ist das
auch woanders noch der Fall?") ist der zuverlässigste Weg, solche Lücken
zu finden, weil sie nicht am Feldnamen, sondern am **Muster** der
Formularstruktur (hier: `_tri_state_bool_selector()`/Objekt-Listen vs.
`_override_selector()`) hängen.

**39. `no_window_dehum_exception` (Lektion 32) wieder entfernt - der
Nutzer entschied sich nach Rückfrage bewusst gegen die eigene, erst kurz
zuvor eingeführte Ausnahme (reiner Dashboard-Karten-Fix, `card_version`
19 → 20, kein Versionsbump nötig).** Nutzer-Frage zu einem konkreten
Fall (Flur KG, fensterlos, Luftfeuchtigkeit 55 % = Schließen-Schwelle,
Luftentfeuchter konfiguriert und korrekt aus): "warum geht der
Luftentfeuchter nicht an?" (beantwortet: Schwelle korrekt erreicht,
kein Bug) - direkt gefolgt von "warum wird der Raum dann orange
angezeigt?". Antwort verwies auf die bestehende, bewusst so gebaute
Ausnahme aus Lektion 32 (Luftfeuchtigkeit + konfigurierter
Luftentfeuchter in fensterlosen Räumen bleibt 🟠 statt 🟢). Auf die
Rückfrage, ob diese Ausnahme entfernt werden soll, antwortete der
Nutzer "Ja" - Fix: `no_window_dehum_exception` und die zugehörige
Sonderbehandlung in `no_window_resolved` ersatzlos entfernt, `no_window_resolved
= no_window and comfort_close_resolved_exception` (wieder identisch zum
ursprünglichen Symmetrie-Fix aus Lektion 32, vor der Verfeinerung).
Fensterlose Räume mit gelöstem Luftfeuchtigkeits-Schließen-Grund zeigen
jetzt wieder unbedingt 🟢, unabhängig davon, ob ein Luftentfeuchter
konfiguriert ist - der Gerätezustand selbst (⚫/🔴 in der Geräte-Tabelle)
bleibt als eigene, unabhängige Information ja ohnehin sichtbar. Lokal
gegengetestet (Jinja-Sandbox, `StrictUndefined`): Flur-KG-Fall jetzt 🟢,
Öffnen-Grund-Regression weiterhin 🟠, Fenster-Match-Regression weiterhin
🟢. Lektion: Eine erst kürzlich auf Zuruf eingeführte Verfeinerung ist
nicht in Stein gemeißelt - konfrontiert mit einem konkreten Fall, der
sie auslöst, kann der Nutzer die ursprüngliche Entscheidung revidieren;
die eigentliche Lektion aus 32 (dass "Aktion nötig, aber nicht über das
Fenster" bei Geräte-Rückkopplung eine eigene Betrachtung verdienen
könnte) bleibt als Erfahrungswert dieser Session erhalten, auch wenn die
daraus abgeleitete Karten-Sonderregel selbst nicht von Dauer war.

**40. Eine Heizungs-Erweiterung sollte laut Nutzer-Vorgabe "wie empfohlen"
(minimal, analog zur Klimaanlage) umgesetzt werden, aber trotzdem mit
typischen HVAC-Parametern statt reinem Ein/Aus (0.56.0).** Ausgangsfrage
des Nutzers: eine Erweiterung der Integration ums Heizen, im Zusammenhang
damit auch eine Umbenennung zu "Smart Climate" - dazu vorab die Antwort,
dass Umbenennen (Domain-Wechsel) riskant/breaking ist (keine In-Place-
Migration in Home Assistant) und empfohlen wurde, das von der reinen
Heizungs-Funktion zu entkoppeln und zunächst nur Letztere unter dem
bestehenden Namen umzusetzen - vom Nutzer bestätigt. Für den Umfang der
Heizungs-Funktion selbst wurde dabei auch eine externe Referenz
herangezogen (ein vom Nutzer verlinktes, sehr umfangreiches Blueprint für
Heizungssteuerung) - dessen Funktionsumfang (native Thermostat-Kalibrierung
je Hersteller, PID-Ventilsteuerung, Geofencing/Proximity, Party-Modus,
Verkalkungsschutz, mehrere parallele Scheduler) wurde bewusst als zu breit
für die minimalistische Philosophie dieses Projekts eingeschätzt und nur
ein kleiner Teil (Gerät analog zur Klimaanlage, Fenster-Pausierung,
Wiederverwendung der Frostschutz-Logik-Muster, Comfort/Standby-Sollwerte)
zur Übernahme vorgeschlagen - der Nutzer bestätigte per Rückfrage die
kleinste der drei angebotenen Optionen ("Minimal: Heizung an/aus wie
Klimaanlage"), ergänzte aber explizit: "Es sollte aber typisch für das
Heizen HVAC Parameter wie Standby, Comfort, etc. geben" - die "minimale"
Umsetzung sollte also kein reines Ein/Aus sein, sondern von Anfang an zwei
feste Sollwerte kennen, wie bei Heizungen üblich.

Technische Entscheidung, die daraus folgte: `_update_heating()` nutzt
bewusst NICHT die bestehende `_update_single_device()`/`_set_device_state()`-
Abstraktion (turn_on/turn_off), die für Luftentfeuchter/Klimaanlage
gemeinsam verwendet wird - eine Heizung braucht `climate.set_temperature`
mit einem konkreten Zielwert, kein einfaches Ein/Aus. Comfort/Standby als
zwei feste, konfigurierbare Sollwerte (`CONF_HEATING_COMFORT_TEMP`/
`CONF_HEATING_STANDBY_TEMP`) statt eines einzelnen "Heizung an"-Sollwerts
plus separatem Ein/Aus - bewusst EIN neuer Schwellenwert
(`CONF_HEATING_THRESHOLD_TEMP`), nicht die Wiederverwendung von
`CONF_TEMP_THRESHOLD_CLOSE`, da die Heizungs-Schwelle typischerweise
deutlich unterhalb der Lüftungs-Schließen-Schwelle liegt und ein eigener,
unabhängiger Wert sein soll. `climate.set_temperature` wurde
`climate.set_preset_mode` vorgezogen, obwohl "Comfort"/"Standby" nach
Preset-Namen klingt - Preset-Modi sind zwischen climate-Integrationen
unterschiedlicher Hersteller nicht standardisiert (anders als
`temperature`, das praktisch jede climate-Entität mit `SUPPORT_TARGET_TEMPERATURE`
unterstützt), ein fester Sollwert ist daher die portablere Wahl. Bewusst
auf `climate.set_hvac_mode` verzichtet - die Heizung setzt voraus, dass
die Entität bereits im gewünschten Heiz-Betriebsmodus steht; das Ändern
des Betriebsmodus selbst hätte den Eingriff über reine Sollwert-Steuerung
hinaus erweitert (siehe README).

Zwei bereits etablierte Muster wurden bewusst wiederverwendet statt neu zu
erfinden: (1) Fenster-Pausierung über das bestehende
`_is_window_confirmed_open()` (aus Lektion 24, dort für die
Luftentfeuchter-Pausierung eingeführt) - gegen ein offenes Fenster zu
heizen verschwendet genauso Energie wie das dort behandelte Gegenstück.
(2) Live-Lese-Prinzip aus Lektion 19/33: das Attribut `heizung_an` liest
NICHT den internen `_heating_state`-Tracker (der dient wie bei
Luftentfeuchter/Klimaanlage nur der Idempotenz beim eigenen Schalten),
sondern vergleicht den aktuell am Gerät eingestellten Sollwert (`state.
attributes.temperature`, live von der climate-Entität gelesen) gegen
Comfort-/Standby-Sollwert - erkennt so auch eine Sollwert-Änderung durch
eine andere Automation oder den Nutzer direkt am Thermostat. Anders als
bei Luftentfeuchter/Klimaanlage (dort liefert der reine `state.state`-
Vergleich "an"/"aus" bereits das Live-Signal) gibt es für die Heizung kein
so einfaches Äquivalent - der `hvac_mode` einer climate-Entität sagt nichts
über Comfort/Standby aus, da diese Integration ihn nie ändert. Bewusst
KEINE Debounce/Hysterese-Zeitverzögerung wie beim Frostschutz (Lektion 12)
eingeführt - stattdessen eine reine Werte-Hysterese (Comfort unterhalb der
Schwelle, Standby erst ab Schwelle + Toleranz-Marge, dazwischen bleibt der
zuletzt gesetzte Sollwert unverändert), da hier kein Sicherheitsrisiko
durch einen einzelnen Ausreißer-Messwert vorliegt, sondern nur Komfort -
fehlt der Innentemperatur-Messwert, wird bewusst gar nichts geändert
(weder Comfort noch Standby), da ein falsches Timing hier anders als beim
Frostschutz nicht sicherheitsrelevant ist.

Die Dashboard-Karte bekam eine neue Geräte-Tabellen-Zeile "Heizung"
(`card_version` 20 → 21) nach demselben Muster wie Luftentfeuchter/
Klimaanlage, ergänzt um den aktuellen Sollwert in Klammern in der
"Grund"-Spalte (da "an"/"aus" hier weniger aussagekräftig ist als bei
einem echten Ein/Aus-Gerät). Lektion: Eine vom Nutzer als "minimal"
bezeichnete Umsetzung ist nicht automatisch die technisch einfachste
(reines Ein/Aus) - der Nutzer hat hier explizit nachgesteuert, dass
"minimal im Funktionsumfang" (kein Geofencing, keine Kalibrierung, kein
Party-Modus) nicht "minimal in der Bedienlogik" (kein simples Ein/Aus)
bedeuten sollte, weil Comfort/Standby-Sollwerte für eine Heizung als
Grundausstattung gelten, nicht als Zusatzfeature. Gleichzeitig ließen sich
für die eigentliche Umsetzung fast ausschließlich bereits etablierte
Muster (Fenster-Pausierung, Live-Lese-Prinzip, Raum-Override/global/
Standard-Auflösung über `_effective()`) wiederverwenden - der Umfang der
Aufgabe lag nicht im Erfinden neuer Konzepte, sondern im sorgfältigen
Übertragen bestehender auf einen strukturell neuen Anwendungsfall
(Sollwert-Steuerung statt Ein/Aus).

**41. Nutzer-Frage "muss ich die Heizung erst konfigurieren?" führte zur
Erkenntnis, dass zwei unabhängige Formularfelder dieselbe Entität doppelt
verlangten - Fix: Wiederverwendungs-Schalter PLUS Zusammenlegung der
beiden betroffenen Abschnitte (0.57.0).** Nachdem Lektion 40 die Heizung
eingeführt hatte, meldete der Nutzer, in der Geräte-Tabelle fehle die
Heizungs-Zeile - Antwort: `CONF_HEATING_ENTITY` ist ein separates Feld,
noch nicht konfiguriert. Der Nutzer wandte ein, es sei doch für jeden Raum
bereits eine `climate`-Entität als Innentemperatur-Quelle hinterlegt -
sollte die nicht automatisch nutzbar sein? Antwort: Nein, absichtlich
nicht - die Temperaturquelle wird nur passiv gelesen, die Heizung dagegen
aktiv gesteuert (`climate.set_temperature`); eine automatische
Wiederverwendung wäre eine stille Rechteausweitung auf eine Entität, die
der Nutzer nur zum Ablesen ausgewählt hatte (dasselbe Prinzip gilt schon
lange bei der Klimaanlage, `CONF_AC_ENTITY`). Der Nutzer fand das
nachvollziehbar, aber trotzdem unpraktisch: dieselbe Entität an zwei
Stellen im Formular auswählen zu müssen sei unsinnig, und schlug zwei
Änderungen zugleich vor: (a) die Abschnitte "Sensoren" und "Geräte" im
Raum-Formular zusammenlegen, UND (b) einen Schalter einführen, der die
Temperaturquelle direkt fürs Heizen wiederverwendet. Eine Rückfrage
(AskUserQuestion) klärte den Umfang, da beide Vorschläge unterschiedlich
riskant sind (ein reiner Schalter ist eine kleine, lokale Ergänzung; das
Zusammenlegen zweier Abschnitte berührt die gesamte Formular-Struktur
inkl. `strings.json`/`translations/*.json` und README) - der Nutzer
wollte ausdrücklich **beides**, den Wiederverwendungs-Schalter aber
bewusst nur für die Heizung, nicht für die Klimaanlage.

Technisch zwei getrennte Änderungen: (1) `SECTION_DEVICES` komplett
entfernt, seine Felder (Luftentfeuchter, Tankstatus-Sensor, Klimaanlage,
Heizung, Leistungsschwelle/-verzögerung) wandern in denselben
`vol.Schema`-Dict wie die bisherigen `SECTION_SENSORS`-Felder - technisch
nur ein Zusammenführen zweier Dicts vor dem `section()`-Aufruf, da Home-
Assistant-Formular-Sections rein UI-seitige Gruppierungen sind und beim
Speichern ohnehin zu einem flachen Dict zusammengeführt werden
(`_flatten_step_data`) - bereits gespeicherte Config-Entry-Daten sind
davon unberührt, keine Migration nötig. (2) Neue Option
`CONF_HEATING_USE_TEMP_SOURCE` (Checkbox, Standard aus) - aktiviert,
liefert ein neuer Helper `_get_heating_entity_id()` in `binary_sensor.py`
die bereits als `CONF_TEMP_SOURCE_ENTITY` gewählte Entität als
Heizungs-Ziel zurück, aber NUR, wenn diese tatsächlich aus der
`climate`-Domain kommt (`HEATING_DOMAINS`) - eine `sensor`-/`number`-/
`input_number`-Temperaturquelle liefert stattdessen `None` (wie "keine
Heizung konfiguriert" behandelt, bewusst permissiv statt ein
Formularfehler, da eine harte Validierung eine neue Fehlertext-
Infrastruktur gebraucht hätte, für einen Fall, der sich ohnehin von
selbst als "wirkungslos" zeigt). Alle bisherigen direkten Lesezugriffe
auf `CONF_HEATING_ENTITY` in `binary_sensor.py` (Attribut-Property,
Grund-Text-Block, `_update_heating()`) wurden durch Aufrufe dieses
Helpers ersetzt - `CONF_HEATING_ENTITY` selbst bleibt bei aktivem
Schalter im Formular sichtbar (Home-Assistant-Formulare können Felder
nicht abhängig von einer Checkbox ausblenden, siehe Muster bei
"Benachrichtigungsmethoden"), wird aber nicht mehr gelesen - deshalb im
Formular-Hinweistext ausdrücklich als "wird ignoriert, falls ... aktiviert
ist" markiert, damit ein Nutzer nicht denkt, eine zusätzliche eigene
Heizungs-Entität hätte weiterhin Wirkung.

Lektion: Eine als "Sicherheitsprinzip" erkannte Trennung (hier: passives
Lesen vs. aktives Steuern derselben Entitätsrolle) ist eine korrekte
Erklärung für das AKTUELLE Verhalten, aber keine automatische
Rechtfertigung dafür, dem Nutzer die doppelte Auswahl zuzumuten, wenn sich
beides mit einer expliziten Opt-in-Option (statt einer stillen Annahme)
vereinen lässt - das Sicherheitsprinzip (nie eine nur zum Lesen gewählte
Entität automatisch steuern) bleibt dabei vollständig gewahrt, da der
Nutzer die Wiederverwendung selbst UND bewusst aktivieren muss. Zusätzlich:
Bei einer AskUserQuestion mit mehreren Teilfragen kann der Nutzer
durchaus "alles" auf die Umfangsfrage antworten, aber bei einer der
Teilfragen (hier: soll der Mechanismus auch für die Klimaanlage gelten)
trotzdem selektiv einschränken - Antworten aus einer Mehrfachauswahl-
Rückfrage einzeln und nicht pauschal interpretieren.

**42. Anwesenheitsprüfung für die Heizung - bewusst NICHT dieselbe
`CONF_PRESENCE_ENTITY` wiederverwendet, die es für App-Benachrichtigungs-
ziele schon gibt, sondern ein eigenes, unabhängiges Feld (0.58.0).**
Nutzerwunsch: Die Heizung soll pro Raum auch danach gehen, ob überhaupt
jemand zuhause ist - vorgeschlagen wurde dafür, den Abschnitt
"Benachrichtigungsmethoden" umzubenennen und ein Personenfeld dort
einzubauen, sowie den Abschnitt "Sensoren & Geräte" davor zu verschieben.
Zwei Rückfragen klärten den Umfang vorab: Mehrfachauswahl (mehrere
Personen, "irgendjemand zuhause" reicht zum Heizen) statt nur einer
Entität, und ein permissiver Fallback bei unbekanntem/nicht verfügbarem
Anwesenheits-Zustand (weiterheizen, nicht pausieren) - beide vom Nutzer
mit der jeweils empfohlenen Option bestätigt.

Technische Entscheidung: Es gibt in diesem Projekt bereits eine
`CONF_PRESENCE_ENTITY` - aber die gehört zu einem einzelnen Eintrag in
`CONF_MOBILE_TARGETS` (App-Benachrichtigungsziele) und beantwortet eine
andere Frage ("soll GENAU DIESES Push-Ziel benachrichtigt werden") als
die neue Anforderung ("soll überhaupt geheizt werden"). Eine
Wiederverwendung hätte zwei konzeptionell unabhängige Entscheidungen
(wen benachrichtigen? wann heizen?) künstlich verkoppelt - ändert man an
einer Stelle die Personen-Auswahl, wäre unklar/überraschend, dass sich
dadurch auch die andere Bedingung mitändert. Neue, eigene Konstante
`CONF_HEATING_PRESENCE_ENTITIES` (Liste, Mehrfachauswahl wie
`CONF_SONOS_ENTITY`) - bewusst OHNE Bereichs-Filterung (Lektion 9: eine
Person/ihr Tracking-Gerät ist ortsungebunden). Neuer Helper
`_is_heating_presence_away()` liefert `True` nur, wenn mindestens eine
Entität konfiguriert ist UND ALLE davon exakt `state == "not_home"`
melden - ein fehlender/unbekannter Zustand einer einzelnen Entität
reicht, um `False` (weiterheizen) zurückzugeben, exakt wie vom Nutzer
gewählt. Eingebunden in `want_heating_comfort`/`want_heating_standby`
genau wie die bereits bestehende Fenster-Pausierung
(`window_confirmed_open`) - beide sind gleichrangige "Pausier"-Gründe,
mit derselben Priorität in der Grund-Text-Ausgabe (`_heating_reason`).
Kein neues Dashboard-Attribut nötig - der Pausier-Grund erscheint bereits
über das bestehende `heizung_grund`-Attribut (Dashboard-Karte unverändert,
kein `card_version`-Bump).

Zur UI-Umstrukturierung: Der Abschnitt "Benachrichtigungsmethoden" wurde
zu "Benachrichtigungen & Anwesenheit" umbenannt (die neue
Anwesenheits-Liste passt inhaltlich dorthin, nicht zu "Sensoren &
Geräte") und - wie vom Nutzer gewünscht - hinter "Sensoren & Geräte"
verschoben (Reihenfolge jetzt: Sensoren & Geräte → Benachrichtigungen &
Anwesenheit → Parameter). Technisch nur eine Frage der Position im
Python-`fields`-Dict (Home-Assistant-Formulare rendern Abschnitte in der
Dict-Einfügereihenfolge) - die JSON-`sections`-Struktur in
`strings.json`/`translations/*.json` selbst ist unabhängig von dieser
Reihenfolge (dort zählt nur der Section-Key, nicht die Position im
JSON-Dokument), musste also nur inhaltlich (Name, neues Feld), nicht
strukturell angepasst werden. Lektion: Ein bereits vorhandenes Feld mit
ähnlichem Namen und Domain (`CONF_PRESENCE_ENTITY`) ist kein Grund, es
für eine neue, semantisch andere Fragestellung wiederzuverwenden, auch
wenn beide dieselbe Entitätsart (`person`/`device_tracker`) betreffen -
entscheidend ist, ob die zugrunde liegende Entscheidung dieselbe ist
("wen benachrichtigen" vs. "wann heizen" sind zwei verschiedene
Entscheidungen, auch wenn beide auf Anwesenheit basieren).

**43. Anzeigenamen-Rename zu "Smart Climate" - bewusst NUR der Anzeigename,
nicht die technische Domain, mit eigener Migration für den Titel des
automatisch angelegten globalen Eintrags (0.59.0).** Nutzerwunsch (Teil
eines größeren, gebündelten Feature-Requests, siehe Lektion 44/45): "Der
Anzeigename der Integration soll überall Smart Climate lauten." Direkt vor
dieser Umsetzung stand bereits Lektion 40 (0.56.0), die von einem
vollständigen Domain-Wechsel zu "Smart Climate" explizit abgeraten hatte -
ein Domain-Rename (`ha_smart_ventilation` → `ha_smart_climate`) ist in Home
Assistant kein In-Place-Vorgang, sondern würde für jeden Nutzer alle
Entity-IDs/unique_ids ändern (Breaking Change, Dashboards/Automationen mit
den alten `binary_sensor.lueften_empfohlen_*`-IDs würden brechen) und einen
Neuinstall statt eines einfachen Updates erfordern. Per Rückfrage
(AskUserQuestion) bestätigte der Nutzer explizit die empfohlene, risikoarme
Auslegung: "Nur Anzeigename" - der `domain`-Wert in `manifest.json` sowie
alle Entity-IDs/unique_ids bleiben unverändert, geändert wird ausschließlich
sichtbarer Text (`manifest.json`/`hacs.json` `"name"`-Feld,
`strings.json`/`translations/*.json` Titel und `data_description`-Texte,
README.md, sowie der über `_apply_threshold_defaults()` beim automatischen
Anlegen gesetzte `CONF_ROOM_NAME`-Wert "- Smart Ventilation Optionen -" des
globalen Eintrags, jetzt "- Smart Climate Optionen -" über die neue
Konstante `GLOBAL_ROOM_NAME` in `const.py`).

Wichtige Ergänzung, die über eine reine Text-Suche-und-Ersetzen-Aktion
hinausging: Der Titel des globalen Eintrags wird - wie bei jedem
Config-Entry - nur EINMALIG bei `async_create_entry()` aus `CONF_ROOM_NAME`
gesetzt (siehe `async_step_import()` in `config_flow.py`); eine bereits
bestehende Installation hätte den alten Titel "- Smart Ventilation
Optionen -" dauerhaft behalten, exakt dieselbe Klasse Bug wie in Lektion 10
("ein Architektur-Refactor macht bereits gespeicherte Config-Entry-Daten
nicht automatisch mit"). Fix: neue Funktion
`_migrate_global_entry_title()` in `__init__.py`, 1:1 nach dem Muster von
`_migrate_legacy_notify_method()` - läuft bei jedem `async_setup_entry()`,
prüft ob `entry.data[CONF_ROOM_NAME]` noch exakt der alten,
`LEGACY_GLOBAL_ROOM_NAME`-Konstante entspricht, und ruft in diesem Fall
`hass.config_entries.async_update_entry(entry, title=GLOBAL_ROOM_NAME,
data=new_data)` auf - sowohl `data` (wirkt sich auf zukünftige, aus
`entry.data` gelesene Werte aus) als auch das separate `title`-Feld
(bestimmt die in der Oberfläche unter "Geräte & Dienste" angezeigte
Bezeichnung - ändert sich NICHT automatisch mit, wenn nur `data` aktualisiert
wird, da Home Assistant beide als unabhängige Felder eines Config-Entry
führt) müssen dafür explizit gesetzt werden. Nach der ersten Migration
wirkungslos (der Titel entspricht danach nicht mehr
`LEGACY_GLOBAL_ROOM_NAME`). GLOBAL_SETTINGS_UNIQUE_ID (und damit die
entry_id selbst) bleibt davon unberührt - es handelt sich um denselben
Eintrag, nur mit neuem Anzeigenamen, nicht um einen Neuanlegen-Vorgang.

Bewusst NICHT verändert: Python-interne Bezeichner wie Klassennamen
(`SmartVentilationBinarySensor`, `SmartVentilationShowerBinarySensor`) -
diese sind nirgends für den Nutzer sichtbar und tragen kein Risiko, anders
als der DOMAIN-Wert oder Entity-IDs; ein Rename hätte hier nur unnötigen
Diff-Umfang ohne jeden Nutzen erzeugt. Ebenso unverändert: alle
GitHub-Repo-/Dokumentations-URLs (`ludgerbeckmann/ha_smart_ventilation`) -
der Repo-Name selbst ist nicht Teil dieses Requests und eine
GitHub-Repo-Umbenennung ein separater, deutlich risikoreicherer Vorgang
(zwar behält GitHub alte URLs als Redirect, aber lokale Clones/CI-Badges/
HACS-Referenzen auf den Repo-Pfad wären betroffen). Lektion: "Nur der
Anzeigename" ist eine präzise, technisch umsetzbare Grenze, die sich
scharf von einem echten Domain-Rename abgrenzen lässt (Lektion 40 hatte
diese Grenze schon vorgezeichnet, hier wurde sie erstmals tatsächlich
gezogen) - innerhalb dieser Grenze bleibt aber trotzdem eine echte
Migration nötig, sobald irgendein Anzeigetext (hier: der Eintragstitel)
einmalig beim Anlegen aus einem zum Rename-Zeitpunkt bereits fest
gespeicherten Wert berechnet wurde, statt bei jedem Lesen live neu
gebildet zu werden - genau die in Lektion 10 etablierte Unterscheidung
zwischen "wird beim nächsten Speichern schon aktuell" (falsch) und
"braucht eine explizite Migration" (richtig).

**44. Heizungs-Zeitplan: "Zeitfenster erzwingt Modus" ersetzt die
Schwellenwert-Logik nur bei aktiviertem Schalter, mit einem dritten
Sollwert (Nacht) und getrennten Werktag-/Wochenende-Fenstern (0.60.0).**
Teil desselben gebündelten Feature-Requests wie Lektion 43/45. Nutzerwunsch:
"Es sollten Zeiten definiert werden können, wann zum Beispiel Standby,
Komfort oder Nachtmodus aktiv sein soll. Diese Zeiten im Punkt oder
Abschnitt Parameter verfügbar machen, auch bei Bedarf pro Raum anpassbar.
Ansonsten gilt die globale Einstellung." Drei Rückfragen (AskUserQuestion)
klärten den Umfang vorab: (1) Zeitfenster erzwingt den Sollwert unabhängig
von der Innentemperatur (nicht bloß als zusätzliche Bedingung neben der
Schwelle) - vom Nutzer bestätigt. (2) Die Granularität: kein einzelnes
Zeitfenster-Paar, sondern - abweichend von beiden angebotenen Optionen -
"zwei Zeitfenster aber unterschiedlich für Werktag und Wochenende", also
acht statt zwei Zeitfelder. (3) Der Rename-Umfang (siehe Lektion 43).

Zentrale Architektur-Entscheidung: `CONF_HEATING_SCHEDULE_ENABLED`
(Tri-State-Bool, raum-überschreibbar wie jede andere Einstellung, globaler
Standard `False`) entscheidet, WELCHE der beiden grundverschiedenen
Logiken in `_evaluate()` überhaupt läuft - bei `False` exakt die
unveränderte Lektion-40-Schwellenwert-Hysterese (volle
Rückwärtskompatibilität für alle bestehenden Installationen, die den
Zeitplan nicht aktivieren), bei `True` vollständig ersetzt durch
`_get_scheduled_heating_mode()` (reine Zeitfenster-Logik, Innentemperatur
komplett irrelevant). Kein Versuch, beide Logiken zu einer einzigen
Kaskade zu verschmelzen (z. B. "Zeitfenster ODER Schwelle") - das hätte
das vom Nutzer explizit gewählte "erzwingt" (Option 1) verwässert und
wäre nur schwer vorhersehbar gewesen, wenn beide Kriterien
unterschiedliche Modi verlangen. `_heating_state` (Idempotenz-Tracker für
`_update_heating()`) wurde dafür von `bool | None` (Comfort/Standby) auf
`str | None` (`"comfort"`/`"standby"`/`"night"`) erweitert - eine dritte
feste Sollwert-Stufe lässt sich mit einem einzelnen Bool nicht mehr
abbilden.

Pausier-Gründe (Fenster offen/niemand zuhause/Sommermodus aktiv, siehe
Lektion 45) haben in JEDEM Fall - Zeitplan aktiv oder nicht - höchste
Priorität und erzwingen sofort Standby; sie stehen bewusst VOR der
Verzweigung zwischen Zeitplan- und Schwellenwert-Logik, nicht als
Sonderfall innerhalb einer der beiden (identisches Muster zu Lektion 21:
Sicherheits-/Pausier-Gründe dürfen nie versehentlich mit einer
Komfort-Umschaltung mit-deaktiviert werden).

Acht statt zwei Zeitfelder (`CONF_HEATING_COMFORT_START/END_WEEKDAY/
WEEKEND`, `CONF_HEATING_NIGHT_START/END_WEEKDAY/WEEKEND`) brauchten einen
komplett neuen Selector-Typ - `selector.TimeSelector()`, Werte als
`"HH:MM:SS"`-String, weder Zahl noch Entity. Neue Helfer-Paare
`_time_selector()`/`_time_override_selector()` sowie eine eigene
`_TIME_FIELDS`-Registry, 1:1 nach dem bereits etablierten Muster von
`_threshold_selector()`/`_override_selector()`/`_THRESHOLD_FIELDS`
gespiegelt (inkl. Erweiterung von `_room_override_placeholders()` und
`_apply_threshold_defaults()` um diese neuen Felder, wie in Lektion 14/38
für jeden neuen überschreibbaren Feldtyp gefordert). Offene, nicht mit
einer echten Home-Assistant-Instanz verifizierte Annahme: Ob ein
geleertes `TimeSelector`-Feld beim Absenden als leerer Wert (wie
Zahlen-/Text-Felder) oder als fehlender Schlüssel (wie `EntitySelector`,
siehe Lektion 27) übermittelt wird, ließ sich in dieser Umgebung nicht
gegen eine echte Instanz testen - `_time_override_selector()` trägt dazu
einen expliziten Kommentar, der auf `ROOM_OPTIONAL_ENTITY_KEYS` als
Fallback-Fix verweist, falls sich Lektion 27 hier doch wiederholen sollte.

Mitternachts-Wraparound (`_time_in_window()`, z. B. Nacht-Fenster
22:00–06:00) über denselben simplen `start > end`-Vergleichs-Trick gelöst,
den viele Zeitfenster-Implementierungen nutzen - kein neues Konzept, aber
in dieser Integration erstmals gebraucht (alle bisherigen
Zeit-/Datumsvergleiche waren reine Dauer- oder Zeitpunkt-Vergleiche, keine
wiederkehrenden Tageszeit-Fenster). Bei sich überlappender (fehlerhafter)
Konfiguration hat das Nacht- vor dem Comfort-Fenster Vorrang - eine
bewusste, aber letztlich beliebige Tie-Break-Entscheidung, da die
Standard-Zeitfenster (siehe `DEFAULT_HEATING_*` in `const.py`) sich pro
Wochentyp ohnehin lückenlos zu 24 Stunden ergänzen und eine Überlappung
nur bei individueller Fehlkonfiguration auftreten sollte. Lektion: Eine
"erzwingt statt ergänzt"-Design-Entscheidung (Rückfrage 1) verlangt einen
eigenen Ein-/Ausschalter für die GESAMTE alternative Logik, nicht nur eine
zusätzliche Bedingung innerhalb der bestehenden - sonst lässt sich
rückwärtskompatibles Verhalten für Nutzer, die das neue Feature nicht
wollen, nicht mehr sauber garantieren.

**45. Sommermodus-Schalter: bewusst als generische Anfrage nach einem
Binärsensor gestartet, aber durch Rückfrage zu einer echten,
UI-schaltbaren `switch`-Entität mit automatischer, aber
überschreibbarer Vorhersage-Logik geworden (0.60.0).** Teil desselben
gebündelten Feature-Requests wie Lektion 43/44. Ursprüngliche
Formulierung: "eine Entität für den Sommermodus, ein Binärsensor, der
geschaltet werden kann" - ein technischer Widerspruch (`binary_sensor` ist
in Home Assistant grundsätzlich read-only, nicht durch den Nutzer
schaltbar). Rückfrage (AskUserQuestion) klärte das zugunsten der
naheliegenden Auflösung: eine echte `switch`-Entität. Direkt im Anschluss,
noch bevor Task 3 (Sommermodus) begonnen wurde, meldete sich der Nutzer
mit einer Präzisierung, die den ursprünglichen Plan ("rein manuell
bedienbarer Schalter") grundlegend änderte: "Der Switch soll aber
definitiv automatisch geschaltet werden. Es sollte da ja bei mir schon
Vorkehrungen in Home Assistant geben" - mitsamt einer eigenen, bereits
produktiv laufenden Template-Sensor-Konfiguration, die `weather.
get_forecasts` periodisch aufruft und das Ergebnis in mehreren
Template-Sensoren als Attribute/State ablegt.

Diese vom Nutzer mitgelieferte Konfiguration löste eine zunächst in einer
kurzen exploratorischen Antwort (siehe Session-Verlauf) selbst
aufgeworfene technische Sorge auf: eine direkte `weather.get_forecasts`-
Anbindung wäre der erste Sensor-Zugriff dieser Integration gewesen, der
nicht über einen einfachen `hass.states.get()`-Read funktioniert (Wetter-
Vorhersagen sind in Home Assistant ein Service-Aufruf mit
Response-Variable, kein Attribut/state einer Entität) - spürbar
aufwändiger als jede bestehende Sensor-Anbindung dieser Integration.
Da der Nutzer aber bereits selbst eine Template-Sensor-Brücke pflegt, die
das Vorhersage-Ergebnis in gewöhnliche state-/Attribut-Werte umwandelt,
entfällt diese Komplexität komplett - `CONF_SUMMER_MODE_FORECAST_ENTITY`
(global-only, wie `CONF_OUTDOOR_TEMP_ENTITY`) plus optionales
`CONF_SUMMER_MODE_FORECAST_ATTRIBUTE` (leer = state direkt lesen) lesen
eine beliebige, vom Nutzer selbst bereitgestellte `sensor`-/`weather`-
Entität genauso wie jeden anderen Sensor dieser Integration - exakt
dasselbe `CONF_TEMP_ATTRIBUTE`-Muster wie bei `CONF_TEMP_SOURCE_ENTITY`,
nur ein zweites Mal angewendet.

Die verbleibende Design-Frage war die Kombination "automatisch UND
weiterhin manuell bedienbar" - kein Widerspruch, aber ein Interaktions-
Problem: Wessen Wille gewinnt, wenn Automatik und Nutzer sich
widersprechen? Gelöst über dasselbe Idempotenz-Muster, das
`_update_single_device()` für Luftentfeuchter/Klimaanlage bereits
etabliert hatte (Lektion 19 u. a.): Die Automatik (`_update_summer_mode()`
in `binary_sensor.py`) schaltet den Schalter nur dann per
`switch.turn_on`/`switch.turn_off`-Serviceaufruf um, wenn sich ihre
Entscheidung (`want_summer_mode`, aus einem Schwellenwert-Vergleich mit
Toleranz-Marge-Hysterese) vom aktuellen LIVE-Zustand des Schalters
unterscheidet - in der Totzone der Hysterese sowie ohne verfügbaren
Vorhersagewert bleibt der Schalter unangetastet, gleich ob sein aktueller
Zustand zuletzt automatisch oder manuell gesetzt wurde. Ein manueller
Schaltvorgang des Nutzers "gewinnt" dadurch implizit, bis die Vorhersage
eine der beiden Grenzen tatsächlich über-/unterschreitet - keine explizite
"Override"-Markierung nötig, weil Automatik und manuelle Bedienung
DIESELBE Entität ohne zweite, private Zustandskopie teilen (anders als bei
Luftentfeuchter/Klimaanlage, wo Automatik und Gerät zwei getrennte,
externe Objekte sind - hier ist die switch-Entität selbst ein Erzeugnis
dieser Integration, es gibt nur einen Zustand).

Cross-Plattform-Referenz zwischen `binary_sensor.py` (trifft die
Entscheidung) und der neuen `switch.py`-Plattform (hält den Zustand) über
die Entity-Registry gelöst (`er.async_get(hass).async_get_entity_id(
"switch", DOMAIN, unique_id)`), nicht über einen direkten Python-
Objektverweis wie beim Dusche-Sensor (Lektion 25) - Lektion 25 hatte genau
diesen direkten Verweis als Quelle einer Reihenfolge-Abhängigkeit beim
gleichzeitigen `async_add_entities()` beider Entitäten identifiziert;
zwei unabhängige, per `async_setup_entry()` separat eingerichtete
Plattformen (bereits seit Lektion 25 als riskanter eingeschätzt als
zwei Entitäten derselben Plattform) machen das umso wichtiger. Der
etablierte, dominante Zugriffsweg dieser Integration auf JEDE fremde
Entität ist ohnehin ein normaler State-/Service-Zugriff über ihre
entity_id (wie bei Luftentfeuchter/Klimaanlage/Heizung/Fensterkontakt) -
die Sommermodus-switch-Entität wird hier bewusst genauso behandelt wie
ein "externes" Gerät, obwohl sie von derselben Integration erzeugt wird.

Lektion: Eine erste, in sich widersprüchliche Nutzeranforderung
("Binärsensor, der geschaltet werden kann") ist ein zuverlässiges Signal,
dass die eigentliche Absicht noch nicht vollständig erfasst ist - die
Rückfrage klärte den unmittelbaren Widerspruch, aber die tatsächlich
gewollte Interaktion (automatisch UND überschreibbar) wurde erst durch
eine zweite, unaufgeforderte Nutzer-Präzisierung sichtbar. Ebenso: Eine
selbst aufgeworfene technische Sorge (Komplexität einer Wetter-Service-
Anbindung) kann sich durch zusätzlichen Kontext vom Nutzer (hier: eine
bereits bestehende Brücken-Lösung) komplett auflösen, ohne dass die
Integration selbst komplexer werden muss - die richtige Reaktion ist dann,
die bereits etablierte, einfachste Zugriffsart (State-Read) unverändert
wiederzuverwenden, statt die ursprünglich befürchtete Komplexität
vorsorglich doch selbst zu bauen.

**46. Lektion 45s Sommermodus-Switch (pro Raum, von dieser Integration
selbst angelegt) wurde direkt im Anschluss durch zwei Nutzer-Korrekturen
auf eine grundlegend andere Architektur umgestellt - ein global gültiger,
bereits vorhandener Schalter, den diese Integration aktiv steuert
(0.61.0).** Nutzerfrage direkt nach Lektion 45: "Wo ist der Schalter für
die Umschaltung zwischen Sommer und Winter? Dieser soll ausschließlich in
den globalen Einstellungen definiert werden können." - bereits diese erste
Präzisierung widersprach der gerade erst umgesetzten Pro-Raum-Architektur
(je eine eigene switch-Entität "‹Raum› Sommermodus" pro Raum mit
konfigurierter Heizung). Ich begann daraufhin zunächst, eine neue, global
verortete, aber weiterhin von dieser Integration selbst erzeugte
Automatik-Entität zu bauen (Stufe 1) - der Nutzer korrigierte das sofort:
"Es geht darum, einen vorhandenen Switch in den globalen
Konfigurationseinstellungen zu hinterlegen, nicht selber einen Sensor
bereitzustellen, über den das von extern gesteuert werden kann." Ich
interpretierte das daraufhin als "rein passiv lesen" (Stufe 2, analog zu
`CONF_OUTDOOR_TEMP_ENTITY`) und fragte per Rückfrage, ob die bereits
gebaute Vorhersage-Automatik-Logik dafür entfernt werden solle - auch das
traf nicht zu: "Dieser Schalter soll von der Integration kontrolliert
werden. Somit muss die Logik auch erhalten bleiben." Erst diese dritte
Präzisierung ergab die tatsächlich gemeinte, konsistente Architektur
(Stufe 3): ein global konfigurierbarer `CONF_SUMMER_MODE_SWITCH_ENTITY`
(EntitySelector, domain `switch`) referenziert eine **bereits vorhandene**
Entität, die diese Integration **aktiv steuert** - exakt dasselbe Muster
wie `CONF_DEHUMIDIFIER_ENTITY`/`CONF_AC_ENTITY`/`CONF_HEATING_ENTITY`
(Entitäten, die gesteuert, nicht selbst angelegt werden), nur eben global
statt pro Raum. Die bereits gebaute Vorhersage+Schwelle+Hysterese-Logik aus
Lektion 45 blieb dabei vollständig erhalten (nur ihr Ziel wechselte von
"eigene Entität schreiben" zu "fremde Entität per Service-Aufruf
steuern") - `switch.py` (die selbst angelegte Entität) wurde komplett
gelöscht, `_update_summer_mode()` ruft stattdessen `switch.turn_on`/
`switch.turn_off` idempotent gegen die konfigurierte Fremd-Entität auf
(identisches "nur schreiben, wenn Ziel vom aktuellen Live-Zustand
abweicht"-Muster wie bei Luftentfeuchter/Klimaanlage/Heizung).

Eine bei der Umstellung auf global-only neu entstehende Gefahr, die bei
Lektion 45s Pro-Raum-Variante gar nicht existierte: Läuft die
Schwellenwert-/Marge-Prüfung weiterhin über das normale
`self._effective()` (Raum-Override → global → Standard), könnten
verschiedene Räume mit unterschiedlichen Overrides für denselben
gemeinsamen, jetzt raumübergreifenden Schalter unterschiedliche
Entscheidungen berechnen und sich gegenseitig überschreiben. Fix:
`CONF_SUMMER_MODE_THRESHOLD_TEMP`/`CONF_TEMP_MARGIN` werden für diese
Entscheidung bewusst NICHT über `_effective()`, sondern direkt über
`self._global_config().get(...)` gelesen - erzwingt für alle Räume
denselben Wert. Der zuvor existierende Raum-Override für die
Sommermodus-Schwelle (Formularfeld im Abschnitt "Parameter" des
Raum-Formulars) wurde konsequenterweise wieder entfernt. Da nun mehrere
Räume unabhängig voneinander denselben Schreibversuch gegen dieselbe
externe Entität auslösen können (jeder Raum wertet bei jeder eigenen
Neubewertung dieselbe globale Entscheidung erneut aus), ist ein
redundanter, aber dank Idempotenz-Prüfung harmloser Mehrfach-Schreibversuch
im selben Bewertungslauf explizit als unproblematisch dokumentiert, statt
z. B. künstlich nur "den ersten Raum" dafür zuständig zu machen.

Lektion: Eine Nutzer-Korrektur direkt im Anschluss an eine gerade erst
umgesetzte Funktion ist kein Zeichen für "knapp daneben", sondern kann
bedeuten, dass die zugrunde liegende Anforderung fundamental anders gemeint
war, als die erste Umsetzung sie verstanden hat - hier waren sogar zwei
aufeinanderfolgende Korrekturen nötig (erst "kein eigener Sensor", dann
"aber die Logik muss erhalten bleiben"), weil die erste Korrektur allein
noch zwei unterschiedliche Auflösungen zuließ (rein passiv lesen vs. aktiv
steuern) und meine eigene Zwischenannahme (passiv) genau die falsche traf.
Der zuverlässigste Weg, die tatsächlich gemeinte Architektur zu finden, war
hier nicht das Raten einer dritten eigenen Variante, sondern der Abgleich
mit einem bereits im Code etablierten, strukturell identischen Muster
(Luftentfeuchter/Klimaanlage/Heizung: vorhandene Entität aktiv steuern) -
sobald die Rückfrage-Antwort ("die Logik muss erhalten bleiben") dieses
Muster erkennbar machte, ergab sich der Rest der Umsetzung praktisch von
selbst, ohne weitere Rückfrage nötig zu haben.

**47. `_update_heating()`s Idempotenz-Prüfung verglich nur gegen den
eigenen "zuletzt kommandiert"-Tracker, nicht gegen den tatsächlichen
Live-Sollwert am Gerät - bei einer instabilen Funkverbindung blieb ein
nie angekommener Befehl dadurch unbemerkt für immer unwiederholt
(0.61.2).** Nutzer-Beobachtung (Dashboard-Screenshot, Badezimmer): Die
Geräte-Tabelle zeigte trotz aktivem globalem Sommerbetrieb-Schalter
weiterhin 🔴 "Heizung an", mit Grund-Text "pausiert: Sommermodus aktiv
(21.0 °C)" - der in Klammern angezeigte, live gelesene Sollwert
entsprach exakt dem Comfort-Wert, nicht dem bei Sommerbetrieb
eigentlich gewünschten Standby-Wert (17.0 °C). Der Nutzer lieferte dazu
selbst den entscheidenden Kontext: Das Heizungs-Stellventil in diesem
Raum ist über eine gerade instabile Funkverbindung angebunden.

Ursache: `heizung_an`/`heizung_modus`/`heizung_zieltemperatur` sind wie
bei Luftentfeuchter/Klimaanlage (Lektion 19/33) korrekt als Live-Read
vom Gerät umgesetzt - das ist nicht das Problem. Das eigentliche Problem
lag in `_update_heating()` selbst: Ein `climate.set_temperature`-Befehl
wurde nur gesendet, wenn sich `target_mode` gegenüber dem rein internen
`self._heating_state`-Tracker geändert hatte - unabhängig davon, ob das
Gerät den zuletzt gesendeten Befehl tatsächlich übernommen hatte.
`_set_heating_temperature()` läuft zwar bewusst mit `blocking=True`
(Lektion 35, um Schema-Validierungsfehler synchron abzufangen) - das
bestätigt aber nur, dass Home Assistants eigene Service-Verarbeitung
fehlerfrei durchlief, nicht, dass ein per Zigbee/Funk angebundenes Gerät
den Befehl auch physisch empfangen und umgesetzt hat. Kam der Befehl bei
instabiler Verbindung nie an, dachte die Integration trotzdem "erledigt"
(`self._heating_state` wurde bereits auf den neuen Modus gesetzt) und
wiederholte den Befehl bei keiner der folgenden Neubewertungen erneut -
das Gerät blieb dauerhaft auf dem alten Sollwert stehen, ohne dass ein
weiterer Versuch unternommen wurde.

Strukturell identisches Muster wie bei Lektion 46 (dort: der neue
globale Sommerbetrieb-Schalter verglich bewusst gegen den Live-Zustand
statt einen internen Tracker, gerade weil er auch manuell bedienbar
bleiben sollte) - hier ging es zwar nicht um manuelle Bedienung, aber um
denselben grundsätzlichen Fehler: ein rein intern gepflegter "das habe
ich doch schon erledigt"-Zustand ist kein Beleg dafür, dass die reale
Welt (das Gerät) diesen Zustand auch tatsächlich erreicht hat. Fix:
`_update_heating()` liest zusätzlich zum Tracker-Vergleich den aktuellen
Live-Sollwert (`_get_heating_target_temperature()`) und vergleicht ihn
(mit kleiner Toleranz von 0.05 °C gegen Rundungsdifferenzen) mit dem
gewünschten Wert - weicht er ab, wird der Befehl erneut geschickt, auch
wenn `target_mode` sich gegenüber `self._heating_state` nicht geändert
hat. Ist der Live-Sollwert gerade nicht lesbar (Entität kurz nicht
verfügbar), bleibt es bewusst beim reinen Tracker-Vergleich - sonst
würde bei jeder kurzen Nichtverfügbarkeit unnötig ein Befehl gegen eine
gerade nicht antwortende Entität wiederholt. Betrifft nur die Heizung -
`_update_single_device()` (Luftentfeuchter/Klimaanlage) hat denselben
rein-internen Tracker-Vergleich, wurde hier aber nicht mit angefasst, da
kein konkreter Fall dafür gemeldet wurde; sollte sich ein analoges
Symptom dort zeigen, gilt dieselbe Lektion.

Lektion: Ein Service-Aufruf mit `blocking=True`, der fehlerfrei
durchläuft, beweist nur, dass Home Assistant den Aufruf verarbeitet hat
- bei jeder Anbindung über ein unzuverlässiges Transportmedium (Funk,
Zigbee, WLAN-Geräte mit eigener Firmware) ist das keine Garantie, dass
das Zielgerät den Befehl auch tatsächlich übernommen hat. Eine
Idempotenz-Prüfung, die nur den eigenen zuletzt gesendeten Befehl
verfolgt (statt den tatsächlichen, live abfragbaren Zielzustand zu
vergleichen), kann einen einmal verschluckten Befehl für immer
unbemerkt lassen, statt ihn bei der nächsten Gelegenheit zu wiederholen
- wann immer ein Gerät live abfragbar ist (hier: `temperature`-Attribut
der climate-Entität), sollte genau dieser Wert die Grundlage für "muss
ich nochmal senden?" sein, nicht nur die eigene Erinnerung an den
letzten Sendeversuch.

**48. Formular-Umbau auf Nutzer-Nachfrage: Erinnerungsintervall gehört
inhaltlich zu den Benachrichtigungen, nicht zu den Schwellenwerten - und
der globale Abschnitt hieß dafür bereits zu eng (0.62.0).** Drei
Wünsche in einer Nachricht: (1) "Die Option Erinnerungsintervall in den
Abschnitt Benachrichtigungen… verschieben", (2) eine Frage, ob für
climate-Entitäten auch ein anderes Attribut als `current_temperature`
üblich ist, (3) "Den Schalter und das Auswahlfeld für die Heizung bitte
hoch verschieben unterhalb der Temperaturauswahldialoge". Bei (1) fehlte
zunächst die Zielsektion für die globalen Einstellungen - dort gibt es
keinen Abschnitt "Benachrichtigungen", nur "Sensoren"/"Parameter"/
"Benachrichtigungstexte" (SECTION_MESSAGES). Rückfrage klärte das: "Bennen
in den globalen Einstellungen den Abschnitt Benachrichtigungstexte in
Benachrichtigungen um und verschieben die Option dorthin" - passt inhaltlich
gut, da `msg_reminder` (der bei diesem Intervall verschickte Text) ohnehin
schon in diesem Abschnitt steht; das Erinnerungsintervall bekommt damit
seinen dazugehörigen Text als direkten Nachbarn, statt isoliert bei den
übrigen Lüftungs-Schwellenwerten zu stehen.

Technisch zwei getrennte, unabhängige Verschiebungen: Für den Raum wandert
`CONF_REMINDER_INTERVAL` von `SECTION_PARAMETERS` zu `SECTION_NOTIFY`
(direkt nach `persistent_marker`, vor den Heizungs-Anwesenheits-Entitäten) -
reine Positionsänderung im `fields`-Dict, der Marker selbst
(`_override_selector`) bleibt unverändert. Für die globalen Einstellungen
war es aufwändiger, weil `CONF_REMINDER_INTERVAL` dort bisher Teil der
gemeinsam mit einer Schleife erzeugten `_CORE_PARAMETER_KEYS`-Liste war
(18 Einträge, alle über `_threshold_selector()` in einem Durchlauf
erzeugt) - der Schlüssel wurde aus dieser Liste entfernt und bekam
stattdessen einen eigenen `_threshold_selector()`-Aufruf (analog zu
`volume_marker`/`power_marker`/`grace_marker`, die aus demselben Grund
schon lange einzeln erzeugt werden), damit er gezielt in
`SECTION_MESSAGES` statt in den generisch über `parameter_fields`
befüllten `SECTION_PARAMETERS` eingefügt werden konnte. Die
"Auf Standardwerte zurücksetzen"-Checkbox funktioniert dabei unverändert
weiter, ohne eigene Anpassung: Sie iteriert weiterhin über
`_THRESHOLD_FIELDS` (eine von `_CORE_PARAMETER_KEYS` unabhängige, für die
Reset-Logik zuständige Registry, die `CONF_REMINDER_INTERVAL` immer noch
enthält) - der Reset wirkt also unabhängig davon, in welchem Formular-
Abschnitt ein Feld gerade angezeigt wird.

Zu (2): `current_temperature` ist kein zufällig gewählter Default,
sondern ein von Home Assistants `ClimateEntity`-Basisklasse fest
vorgegebenes Attribut, das praktisch jede climate-Integration identisch
implementiert - anders als z. B. Gerätenamen oder Attribut-Einheiten gibt
es hier keine herstellerspezifische Varianz zu erwarten. Die frei
editierbare Auswahlliste (`custom_value=True`) ist entsprechend eher ein
Sicherheitsnetz für den seltenen Sonderfall als ein häufig benötigtes
Feature. Direkt im Anschluss schlug der Nutzer vor, das Auswahlfeld
"Temperatur-Attribut" wegen genau dieser Standardisierung komplett zu
entfernen ("da nicht benötigt") - davon wurde abgeraten: Ein bereits
gespeicherter, vom Standard abweichender Wert (z. B. für eine nicht ganz
standardkonforme Custom-Integration) würde beim Entfernen des Felds
stillschweigend ignoriert und stattdessen wieder der hart codierte
Standard verwendet - dieselbe Gefahrenklasse wie in Lektion 26 (eine
Auswahlmöglichkeit einzuschränken darf nie einen bereits gespeicherten,
funktionierenden Wert unerreichbar machen). Stattdessen vorgeschlagen und
noch offen: nur den vermutlich falschen dritten Vorschlagswert
`target_temperature` (kein offizielles HA-Climate-Attribut, der Sollwert
heißt dort `temperature`) aus der Liste zu entfernen - das schränkt keine
bereits funktionierende Konfiguration ein, sondern entfernt nur eine
vermutlich irreführende Option, die noch nie sinnvoll genutzt worden sein
kann.

Zu (3): Reine Positionsänderung innerhalb von `SECTION_SENSORS` im
Raum-Formular - `CONF_HEATING_USE_TEMP_SOURCE` (Checkbox) und
`CONF_HEATING_ENTITY` (EntitySelector) wandern von ihrer bisherigen
Position (nach der Klimaanlage, vor Leistungsschwelle/-verzögerung) direkt
hinter `CONF_TEMP_ATTRIBUTE` - passt inhaltlich besser, da beide Felder
sich unmittelbar auf die direkt darüber gewählte Innentemperatur-Quelle
beziehen (siehe `CONF_HEATING_USE_TEMP_SOURCE`s Funktionsweise). Keine
Auswirkung auf `strings.json`/`translations/*.json` (dieselben Labels,
nur andere Position im Python-`fields`-Dict) oder auf `heating_include`
(unverändert einmalig vorher berechnet, nur an der neuen Stelle
referenziert).

Lektion: Bei einer Bitte, ein Feld "in den Abschnitt X verschieben" nie
automatisch annehmen, dass der Zielabschnitt in JEDEM betroffenen
Formular (hier: Raum UND global) bereits unter demselben Namen und mit
derselben Funktion existiert - eine kurze Rückfrage deckte hier auf, dass
der globale Abschnitt “Benachrichtigungen” schlicht noch nicht existierte
(er hieß enger “Benachrichtigungstexte”) und selbst erst durch Umbenennung
und Erweiterung geschaffen werden musste. Außerdem, anknüpfend an
Lektion 26: Ein Vorschlag, ein ganzes Auswahlfeld zu entfernen, weil der
Standardwert "eigentlich immer passt", übersieht leicht, dass "eigentlich
immer" nicht "garantiert immer" bedeutet - die vorsichtigere Änderung
(nur eine einzelne, vermutlich falsche Option aus der Vorschlagsliste
entfernen) erreicht das gewünschte Aufräumen, ohne einen bereits
funktionierenden Sonderfall zu riskieren.

**49. Home Assistants "Erweiterter Modus" (`show_advanced_options`) wurde
mit Version 2026.6 komplett entfernt - ein eigener Formular-Abschnitt
"Erweitert" musste das als projektinterne Lösung ersetzen, mit einem
Stolperstein an einer Stelle, die mit dem eigentlichen Feld-Verschieben
nichts zu tun hatte (0.63.0).** Auf die Frage, wo in HA der erweiterte
Modus aktiviert wird (Nutzer fand die Option in seinem Profil nicht,
obwohl Admin), ergab eine Websuche: Der komplette Mechanismus (Profil-
Schalter, `show_advanced_options`, alles was er steuerte) wurde in
Version 2026.6 entfernt - schrittweise über ein Jahr abgebaut, weil ein
einzelner binärer Schalter zu viele unzusammenhängende Dinge bündelte.
`FlowHandler.show_advanced_options` existiert zwar noch (liefert während
der Übergangszeit bis 2027.6 unconditional `True`), taugt aber nicht mehr
für neue, gezielte "nur bei Bedarf sichtbar"-Logik. Der bereits zuvor
angedachte Plan (seltene Optionen hinter `show_advanced_options`
verstecken) war damit hinfällig - stattdessen wurde ein neuer,
projekteigener Formular-Abschnitt **"Erweitert"** (`SECTION_ADVANCED`)
sowohl im Raum- als auch im globalen Formular eingeführt, in den acht
selten geänderte Fein-Tuning-Felder verschoben wurden: Temperatur-
Attribut, Toleranz-Marge, Frostschutz-Debounce, Priorität bei
Winter-Höchstdauer, Dusch-Anstiegsschwelle, Leistungsschwelle/
-verzögerung (alle sechs sowohl Raum- als auch global-seitig), zusätzlich
global das Sommermodus-Vorhersage-Attribut. Bewusst NICHT verschoben (auf
expliziten Nutzerwunsch, nachdem der erste Vorschlag mehr Felder
enthielt): TTS-Wiedergabemodus und der komplette Heizungs-Zeitplan
(Umschalter + 8 Zeitfenster + Nachttemperatur) - beide blieben in ihren
angestammten Abschnitten.

Stolperstein: `_flatten_step_data()` führt die von Home Assistant
verschachtelt übermittelten Section-Dicts wieder zu einem flachen Dict
zusammen, iteriert dafür aber über eine hart codierte `section_keys`-Tupel
(bis dahin `SECTION_NOTIFY, SECTION_SENSORS, SECTION_PARAMETERS,
SECTION_MESSAGES`). Ein neuer Abschnitt bekommt dadurch nicht automatisch
denselben Merge - ohne `SECTION_ADVANCED` in dieses Tupel aufzunehmen,
wären alle acht neu verschobenen Felder beim Speichern schlicht
verschwunden (weder im `flat`-Dict noch damit im Config-Entry gelandet),
obwohl das Formular selbst syntaktisch korrekt gewesen wäre und keinen
Fehler geworfen hätte - ein Bug, der erst beim tatsächlichen Speichern
aufgefallen wäre, nicht beim bloßen Anzeigen des Formulars. Gefunden durch
gezieltes Durchsuchen nach jeder Stelle, die die bisherigen vier
`SECTION_*`-Konstanten als vollständige Aufzählung behandelt (`grep
"SECTION_"`), nicht nur durch das Anpassen der beiden Schema-Bau-Funktionen
selbst. Die etablierten, section-unabhängigen Helfer
(`_room_override_placeholders()`, `_apply_threshold_defaults()`, die
"Auf Standardwerte zurücksetzen"-Logik) blieben dagegen unverändert
korrekt, da sie ohnehin über `_THRESHOLD_FIELDS`/`_TIME_FIELDS` iterieren,
nicht über eine Section-Struktur.

Lektion: Ein neuer Formular-Abschnitt ist nicht nur an den zwei
offensichtlichen Stellen zu verdrahten (die beiden `_build_*_schema()`-
Funktionen, die ihn im UI erzeugen) - jede Stelle im Code, die die Menge
der existierenden Abschnitte als vollständige, hart codierte Aufzählung
behandelt (hier: eine einzelne `section_keys`-Tupel-Definition), muss den
neuen Abschnitt ebenfalls kennen, sonst werden dort verschachtelte Werte
beim Verarbeiten des `user_input` unbemerkt verworfen. Ein gezielter
`grep` nach dem Namens-Präfix der bestehenden Konstanten (hier
`SECTION_`) vor dem Abschluss einer solchen Änderung deckt solche
Stellen zuverlässiger auf als das Nachvollziehen des Kontrollflusses aus
dem Kopf.

**50. Heizungs-Presets (KNX & Co.) statt Sollwert - bewusst als Opt-out
(Standard an), nicht Opt-in, mit Laufzeit-Fähigkeitsprüfung als
Sicherheitsnetz (0.64.0).** Nutzerwunsch: "Da dies über KNX so gehandhabt
wird, bitte definitiv diese Presets anzeigen und auch steuern und nicht
direkt die Temperatur." - direkte Folge einer vorherigen Frage, warum ein
Home-Assistant-seitiges "Gebäudeschutz"-Preset in dieser Integration nicht
auftaucht (Antwort: `preset_mode` wird bewusst nie gelesen/gesetzt, siehe
Lektion 40 - Preset-Namen sind herstellerabhängig, ein reiner Zahlen-
Sollwert ist portabler). Drei Rückfragen klärten den Umfang: (1) Opt-in
oder Opt-out - der Nutzer wählte explizit **Opt-out** (Standard Ja, mit
Möglichkeit zum Abschalten), nicht das von mir empfohlene Opt-in (Standard
Nein). Das barg ein Rückwärtskompatibilitäts-Risiko, das im ursprünglichen
Vorschlag nicht vorgesehen war: Ein globaler Standard "Ja" hätte für JEDE
bestehende Installation ohne Preset-Unterstützung am Gerät sofort einen
`climate.set_preset_mode`-Aufruf gegen eine Entität ausgelöst, die das
gar nicht kann. Fix dafür: `_heating_preset_mode_effective()` prüft vor
jeder Verwendung zusätzlich zur Einstellung selbst, ob die konkrete
Heizungs-Entität `preset_mode` überhaupt unterstützt
(`ClimateEntityFeature.PRESET_MODE` in `supported_features`) - nur dann
greift der Opt-out-Standard tatsächlich; ohne Unterstützung bleibt es
automatisch bei der bisherigen Sollwert-Steuerung, ganz ohne dass eine
bestehende Installation etwas einstellen müsste. (2) Die Zuordnung der
vier Preset-Namen (Komfort/Standby/Nacht/Gebäudeschutz) zu den
herstellerabhängigen `preset_mode`-Strings - Kombination aus beidem: vier
Dropdown-Felder mit den tatsächlich von der gewählten Heizungs-Entität
gemeldeten `preset_modes`, automatisch vorbelegt per Schlüsselwort-Suche
(z. B. "eco"/"night"/"nacht" für die Nacht-Stufe), aber frei editierbar
(`custom_value=True`) für den Fall einer falschen Vermutung oder einer
gerade nicht erreichbaren Entität. (3) "Gebäudeschutz" (ein bei Home
Assistant/KNX gebräuchlicher vierter Zustand ohne eigenen Zahlen-Sollwert
in dieser Integration) sollte NICHT wie zunächst vorgeschlagen alle drei
bestehenden Pausier-Gründe (Fenster offen/Abwesenheit/Sommerbetrieb)
ersetzen, sondern ausschließlich "Fenster offen" - Abwesenheit und
Sommerbetrieb bleiben bewusst Standby. Ohne hinterlegten Preset-Namen für
einen einzelnen Zustand (z. B. Gebäudeschutz gar nicht konfiguriert) fällt
`_update_heating()` für GENAU diesen Aufruf auf die Sollwert-Steuerung
zurück (Gebäudeschutz nutzt dafür ersatzweise den Standby-Sollwert, da es
keinen eigenen gibt) - eine teilweise Konfiguration (z. B. nur
Gebäudeschutz als Preset, der Rest über Sollwerte) bleibt dadurch möglich.

Bei aktiver Preset-Steuerung wird auch die Anzeige (`heizung_modus`)
umgestellt: statt der bisherigen Näherung "welchem der drei Sollwerte
liegt der aktuelle Zahlen-Sollwert am nächsten" (Lektion 19/33/40) wird
direkt der live vom Gerät gemeldete `preset_mode` zurück auf einen unserer
vier Bezeichner gemappt - liefert ehrlich `None`, wenn das Gerät gerade
einen uns unbekannten Preset meldet, statt geraten zu werden. Lektion: Bei
einer expliziten Nutzer-Entscheidung gegen die empfohlene, rückwärts-
kompatiblere Variante (hier: Opt-out statt Opt-in) muss das Sicherheitsnetz
dafür an einer TIEFEREN Stelle eingebaut werden (hier: eine zur Laufzeit
geprüfte Geräte-Fähigkeit, nicht nur eine Konfigurationsoption) - die
Rückwärtskompatibilität für Installationen, die das neue Verhalten gar
nicht wollen/können, darf nicht allein von der (hier bewusst permissiv
gewählten) Standardeinstellung abhängen.

**Nachtrag (0.64.x):** Direkt im Anschluss meldete der Nutzer eine
scheinbar unabhängige Beobachtung (Heizung in einem Raum bleibt trotz
aktivem Sommerbetrieb auf Comfort-Sollwert stehen) und lieferte dazu ein
Home-Assistant-Log. Die Analyse deckte einen unabhängigen, aber
strukturell verwandten Bug auf - siehe Lektion 35, Nachtrag.

**35 (Nachtrag), 0.64.x: `except HomeAssistantError` fängt einen Schema-
Validierungsfehler von `hass.services.async_call()` NICHT ab - Lektion
35s eigentliches Ziel wurde dadurch trotz des `blocking=True`-Fixes
verfehlt, ohne dass das bis zu einem echten Log-Beleg auffiel.** Im vom
Nutzer hochgeladenen Log fand sich weiterhin exakt die in Lektion 35
beschriebene Fehlermeldung (`probatio.error.MultipleInvalid: not a valid
option at 'data'`) als **"Task exception was never retrieved"** - also
genau das Symptom, das der Lektion-35-Fix (blocking=True statt
blocking=False) beheben sollte. Ursache: Der Schema-Validierungsfehler
wird von `homeassistant/core.py` unverändert durchgereicht, ohne in eine
`HomeAssistantError`-Unterklasse gewrappt zu werden - er ist schlicht kein
`HomeAssistantError`. `except HomeAssistantError:` lief also seit Lektion
35 immer schon ins Leere für GENAU den Fehlerfall, den dieser Fix eigentlich
sollte abfangen können (Service-/Entity-Existenzfehler, die synchron VOR
der Schema-Validierung geprüft werden, fängt er weiterhin korrekt ab -
deshalb fiel das nicht früher auf). `blocking=True` war weiterhin richtig
und nötig (bringt den Fehler synchron in den `await`, verhindert den
unbeobachteten Task) - nur der Except-Typ war falsch. Fix: an allen drei
betroffenen Stellen (`_send_mobile_push()`, `_set_heating_temperature()`,
`_set_heating_preset_mode()` - alle drei mit `blocking=True` und jeweils
GENAU einem Service-Aufruf im try-Block) `except HomeAssistantError:` zu
`except Exception:` verbreitert. Bewusst nicht auf einen Import der
tatsächlichen Exception-Klasse (`probatio.error.MultipleInvalid`)
gesetzt - das wäre ein Zugriff auf eine interne Implementierungsdetail
von Home Assistants Service-Aufruf-Schicht, kein für Custom-Integrationen
vorgesehener, stabiler Import. Ein derart breiter Except-Typ ist hier
vertretbar, weil der try-Block ausschließlich den einen Service-Aufruf
enthält - er kann keine andere, eigene Fehlerursache verschleiern. Die
übrigen, mit `blocking=False` laufenden Service-Aufrufe (Luftentfeuchter/
Klimaanlage/Sommermodus-Schalter/Fenstersperre/TTS-Pause) sind von
diesem konkreten Fix bewusst unberührt geblieben - dort passiert eine
Schema-Validierung ohnehin in einem unbeobachteten Hintergrund-Task, egal
welcher Except-Typ verwendet wird (unveränderter, akzeptierter
Lektion-35-Rest-Risiko). Lektion: Ein Fix, der einen Fehler erfolgreich
"synchron macht" (hier: `blocking=True`), ist nur die halbe Miete, wenn
der dafür verwendete Except-Typ nie gegen die tatsächliche Exception-Klasse
verifiziert wurde - eine als erledigt dokumentierte Lektion kann ihr
eigentliches Ziel verfehlt haben, ohne dass Tests (hier: `py_compile`,
Import-Checks) das aufdecken können, weil der Code syntaktisch korrekt
bleibt und nur zur Laufzeit, mit dem echten Fehlerfall, sichtbar wird -
ein vom Nutzer bereitgestelltes Home-Assistant-Log war hier das einzige
Mittel, das zuverlässig aufzudecken.

**51. Lektion 42s Anwesenheits-Pausierung für die Heizung war als
gleichrangiger Pausier-Grund neben Fenster/Sommerbetrieb umgesetzt - der
Nutzer präzisierte nachträglich, dass sie ausschließlich den Comfort-Modus
verhindern, aber Standby/Nacht/Gebäudeschutz unangetastet lassen soll
(0.64.1).** Nutzer-Nachfrage "sicherheitshalber": "Das soll nur
verhindern, dass die Heizung nicht in den Komfortmodus schaltet. Alle
anderen Modi sowie Standby, Gebäudeschutz oder Eco-Nachtbetrieb sollen
natürlich weiterhin ganz normal ablaufen." Der bisherige Code
(`heating_target_mode`-Berechnung in `_evaluate()`) behandelte
`heating_presence_away` bislang exakt wie `heating_summer_mode_active` -
beide erzwangen sofort "standby", unabhängig davon, was Zeitplan oder
Schwellenwert-Logik eigentlich ergeben hätten. Das überschrieb z. B. einen
per Zeitplan aktiven Nacht-Modus fälschlich mit Standby, sobald zusätzlich
niemand zuhause war - genau das wollte der Nutzer nicht.

Fix: Die Anwesenheitsprüfung wandert hinter die eigentliche
Zielmodus-Ermittlung (Fenster/Sommerbetrieb/Zeitplan/Schwellenwert) und
degradiert das Ergebnis nur noch NACHTRÄGLICH von "comfort" auf "standby"
(`heating_presence_blocked_comfort = heating_presence_away and
heating_target_mode == "comfort"`) - jeder andere bereits ermittelte
Zielmodus bleibt unverändert. Fenster/Sommerbetrieb bleiben bewusst
unverändert als echte, dem eigentlichen Ziel übergeordnete Pausen (sie
erzwingen ihr Ergebnis unabhängig vom sonst gewollten Modus - anders als
Abwesenheit, die nur einen einzelnen, bereits eintretenden Fall
korrigiert). Der `_heating_reason`-Text wurde entsprechend nur noch für
den tatsächlich eingetretenen Fall (Comfort wurde verhindert) gesetzt,
nicht mehr für jede Abwesenheit unabhängig vom eigentlichen Zielmodus -
sonst hätte die Anzeige weiterhin "pausiert: niemand zuhause" suggeriert,
obwohl in Wahrheit z. B. ein Zeitfenster den Nacht-Modus unverändert
durchgesetzt hätte (dieselbe Art Fehler wie in Lektion 11/13: ein
Grund-Text darf keine Ursache behaupten, die den tatsächlichen Ausgang gar
nicht beeinflusst hat). README (Abschnitt "Sensoren & Geräte" sowie
"Pausen im Detail") entsprechend präzisiert: Abwesenheit dort explizit als
eigener, von den beiden echten Pausen (Fenster, Sommerbetrieb) getrennter
Absatz beschrieben, nicht mehr als dritte gleichrangige Pause. Lektion:
Bei einer als "Pausier-Grund" eingeführten Bedingung, die künftig für
mehrere strukturell ähnliche Fälle wiederverwendet wird (hier: Fenster/
Sommerbetrieb als Vorbild für die neue Anwesenheit), nicht automatisch
annehmen, dass "gleiche Code-Stelle" auch "gleiche Priorität/gleiche
Wirkung" bedeutet - eine spätere Nutzer-Präzisierung kann ergeben, dass
die neue Bedingung nur einen EINZELNEN, bereits woanders ermittelten
Fall korrigieren soll, nicht das gesamte Ergebnis unabhängig überschreiben
darf.

**52. Auf Nutzerwunsch: Die vier globalen Preset-Namen-Felder (Lektion 50)
waren reine Freitextfelder ohne jede Vorbelegung - anders als das
Raum-Formular (dort echte, vom Gerät gemeldete Presets als Dropdown)
fehlte den globalen Einstellungen jede Hilfestellung beim Ausfüllen
(0.64.1).** Nutzer-Feedback: "Die Preset-Namen in den globalen
Einstellungen sind gar nicht vorausgefüllt. Kann man da eventuell auch
eine Dropdown-Liste machen, wie bei dem Attribut für die Climate-Entität?"
- Verweis auf das bereits bestehende Muster bei `CONF_TEMP_ATTRIBUTE`
(fester Kandidaten-Katalog `COMMON_TEMP_ATTRIBUTES` als `SelectSelector`
mit `custom_value=True`, siehe Abschnitt "Erweitert"). Für die globalen
Preset-Felder gibt es - anders als im Raum-Formular - keine einzelne
Heizungs-Entität, deren `preset_modes` sich live auslesen ließen (jeder
Raum kann eine andere Entität haben, siehe `_heating_preset_selector()`s
ursprünglicher Kommentar dazu) - der bisherige reine `TextSelector()` war
daher eine bewusste, aber für den Nutzer unbequeme Entscheidung.

Fix: Neue Konstante `COMMON_HEATING_PRESET_MODES` in `const.py` - bewusst
NUR die acht offiziellen `PRESET_*`-Werte aus
`homeassistant.components.climate.const` (comfort/eco/home/sleep/away/
boost/activity/none), nicht als Import (keine Abhängigkeit von internem
HA-Modulnamen, siehe Lektion 40), sondern als reine String-Literale.
Explizit KEINE zusätzlichen, unverifizierten Vermutungen für
herstellerspezifische Namen (z. B. ein geratenes "building_protection")
ergänzt - genau die Art Fehler, die Lektion 48 bereits für
`COMMON_TEMP_ATTRIBUTES`s drittem Vorschlagswert (`target_temperature`)
kritisiert hatte. `_heating_preset_selector()` (bisher nur für das
Raum-Formular gedacht, `available_presets` kam dort immer von einer realen
Geräte-Abfrage) wird jetzt für BEIDE Formulare verwendet - die globale
Aufrufstelle übergibt `COMMON_HEATING_PRESET_MODES` statt der Live-Liste;
die Funktion selbst brauchte dafür keine Codeänderung, nur eine
präzisierte Docstring (zwei Aufrufer mit unterschiedlicher Herkunft der
Liste - einmal ein zuverlässiger Live-Wert vom Gerät, einmal nur ein
Hinweis ohne Garantie). Die bereits bestehende Schlüsselwort-Rate-Logik
(`_HEATING_PRESET_GUESS_KEYWORDS`) griff dadurch ohne weitere Änderung
automatisch auch global: "comfort" wird für das Comfort-Feld vorbelegt,
"eco" für das Nacht-Feld (da "eco" als Keyword für Nacht bereits seit
Lektion 50 hinterlegt ist) - für Standby und Gebäudeschutz bleibt es ohne
Vorschlag, da kein Kandidat aus der 8er-Liste zu deren Schlüsselwörtern
passt (ehrlich, statt einen falschen Vorschlag zu erzwingen). Wie beim
Raum-Formular bleibt das Feld über `custom_value=True` weiterhin frei
editierbar, falls die tatsächliche Entität einen anderen (insbesondere
herstellerspezifischen, z. B. KNX-eigenen) Namen meldet. Lektion: Ein
bereits etabliertes "Dropdown mit Vorschlägen, aber frei editierbar"-Muster
(hier: `COMMON_TEMP_ATTRIBUTES`) lässt sich oft direkt auf ein zweites,
strukturell ähnliches Feld übertragen, ohne dass eine neue Auswahl-Logik
gebaut werden müsste - wichtig ist dabei, wie Lektion 48 bereits zeigte,
den Kandidaten-Katalog auf tatsächlich verifizierte Werte zu beschränken,
statt die Vorschlagsliste durch unbelegte Vermutungen selbst unzuverlässig
zu machen.

**53. Überschreibbare Dropdowns für Zahlenfelder: erstmals für zwei
konkrete Felder umgesetzt, mit Rückfrage zum Umfang statt sofortiger
Ausweitung auf alle ~19 Schwellenwerte (0.65.0).** Nutzerwunsch (aus den
globalen Einstellungen heraus): "Kann man da nicht mehrere der
Eingabefenster umstellen auf überschreibbare Dropdown-Menüs?" - konkret
genannt: Erinnerungsintervall (Vorschläge 0/20/40/60 Minuten) und
Mindesteinspeiseleistung (500/1000/1500/2000 Watt), mit dem offenen
Zusatz "das wäre bei weiteren Feldern womöglich auch eine Option". Zwei
Rückfragen klärten den Umfang vor der Umsetzung (feste Arbeitsanweisung,
siehe oben): (1) Auch die entsprechenden RAUM-Override-Felder umstellen,
nicht nur die globalen - Nutzer wählte die empfohlene Variante
"Global + Raum-Override" für ein konsistentes Bedienbild. (2) Weitere
Felder sofort mit umsetzen oder erstmal bei den zwei genannten bleiben -
Nutzer wählte "weitere Felder, ich nenne sie dir" (noch offen, siehe
"Offene/mögliche nächste Schritte" unten).

Technisch besonders: Anders als bei `_heating_preset_selector()`/
`COMMON_TEMP_ATTRIBUTES` (beide reine Text-Werte) speichern
`CONF_REMINDER_INTERVAL`/`CONF_MIN_SURPLUS_POWER` echte Zahlen (int bzw.
float), die downstream in Vergleichen mit Sensor-Messwerten verwendet
werden. `selector.SelectSelector` liefert aber - auch mit
`custom_value=True` für einen frei eingegebenen numerischen Wert - IMMER
einen String zurück, nie eine Zahl (anders als `NumberSelector`, das
selbst schon `float` liefert). Ein naiver Umstieg hätte den gespeicherten
Wert stillschweigend von Zahl auf String verändert - unauffällig beim
Speichern selbst (kein Fehler), aber mit Absturzpotenzial beim nächsten
Vergleich mit einem echten Sensor-Wert (`str >= float` wirft
`TypeError`). Fix: `vol.All(selector.SelectSelector(...),
vol.Coerce(int|float))` als Schema-Wert - `vol.All` verkettet mehrere
Validatoren, der `SelectSelector` validiert/normalisiert zuerst, danach
wandelt `vol.Coerce()` den validierten String zurück in den tatsächlich
benötigten Zahlentyp. Lokal (ohne echte Home-Assistant-Instanz) mit einer
schlanken Nachbildung von `SelectSelector` gegen `voluptuous` verifiziert,
dass sowohl ein aus der Vorschlagsliste gewähltes ("20") als auch ein frei
eingegebener Wert ("45", oder mit Nachkommastelle für die
Leistungsschwelle) korrekt zum erwarteten Zahlentyp wird - dieses Muster
kombiniert also, anders als Lektion 52, ECHTE numerische Coercion mit dem
Dropdown-Muster, nicht nur reine String-Werte.

Beide bereits bestehenden Aufrufstellen je Feld (global über
`_threshold_selector()`, Raum-Override über `_override_selector()`)
teilen sich jetzt einen neuen, gemeinsamen Helper
(`_numeric_field_selector()`), der anhand einer neuen
`_THRESHOLD_DROPDOWN_OPTIONS`-Registry entscheidet, ob ein Feld ein
Dropdown (mit Coercion) oder weiterhin den bisherigen `NumberSelector`
bekommt - beide Aufrufer-Funktionen selbst (Marker-Erzeugung,
`suggested_value`- vs. `default=`-Logik) blieben unverändert, nur die
Selector-Erzeugung wurde ausgelagert. Dadurch wirkt sich eine künftige
Erweiterung der Registry automatisch auf beide Ebenen (global + Raum)
gleichzeitig aus, ohne eine der beiden Funktionen erneut anfassen zu
müssen. Bewusst NICHT für alle ~19 `_THRESHOLD_FIELDS`-Einträge auf einmal
umgesetzt, obwohl der Umbau technisch trivial skaliert hätte - die
Rückfrage ergab, dass der Nutzer die übrigen Felder selbst benennen
möchte (unterschiedliche Felder brauchen unterschiedliche, sinnvolle
Vorschlagswerte, die sich nicht pauschal aus min/max/step ableiten
lassen). Wie bei `_heating_preset_selector()` (Lektion 50) nicht gegen
eine echte Instanz verifizierbar, ob ein geleertes Dropdown-Feld beim
Absenden als leerer Wert oder wie ein `EntitySelector` als fehlender
Schlüssel übermittelt wird (siehe `ROOM_OPTIONAL_ENTITY_KEYS`,
Lektion 27) - folgt hier bewusst derselben, bereits bei den
Preset-Feldern getroffenen Annahme. Lektion: Ein bereits etabliertes
"Dropdown mit Vorschlägen, aber frei editierbar"-Muster lässt sich nicht
blind auf jedes Feld übertragen - bei Textfeldern (Lektion 50/52) liefert
der Selector bereits den richtigen Typ, bei Zahlenfeldern braucht es
zusätzlich eine explizite Rückwandlung (`vol.Coerce`), da `SelectSelector`
grundsätzlich nur Strings zurückgibt; dieser Unterschied fällt weder beim
Anzeigen des Formulars noch beim Speichern selbst auf, sondern erst bei
der nächsten Verwendung des gespeicherten Werts in einer Zahlen-Operation.

**54. Die beiden "Sommer-Fall"-Auslöser (`outdoor_warmer`/`outdoor_wetter`)
waren seit Lektion 13 bewusst als "nicht live nachrechenbar" eingestuft -
bei genauerem Hinsehen stimmte das nur noch für einen der beiden, und für
den anderen fehlte lediglich EIN Attribut (0.66.0).** Nutzer-Nachfrage zu
einem konkreten Fall (Zimmer Ida): Auslöser "Außen wärmer" mit Zeitstempel
09:12, obwohl die aktuell angezeigte Außentemperatur (18,3 °C) längst
wieder unter der Innentemperatur (21,4 °C) lag - ich erklärte das
zunächst korrekt als erwartetes, dokumentiertes Verhalten des historischen
`letzter_grund`-Rückfallwerts (Lektion 13). Die Nutzer-Reaktion darauf:
"Die Karte soll von dem farblichen Status her aber immer den aktuellen
Stand widerspiegeln" - eine grundsätzliche Anforderung, die über die
bloße Erklärung hinausging und mich veranlasste, die Lektion-13-Annahme
("nicht live nachrechenbar") noch einmal zu überprüfen, statt sie
unhinterfragt hinzunehmen.

Ergebnis der Prüfung: Für `outdoor_wetter` ("Außenluft inzwischen
feuchter") waren alle nötigen Werte (`absolute_luftfeuchtigkeit`,
`aussen_absolute_luftfeuchtigkeit`) bereits als Attribute vorhanden -
die Karte hatte sie schon immer nur für die reine Werte-Anzeige genutzt,
nie für die Live-Berechnung des Auslösers selbst. Reiner Karten-Fix, kein
Backend nötig. Für `outdoor_warmer` ("Außen wärmer") fehlte dagegen
tatsächlich nur EIN einzelnes Attribut, die Toleranz-Marge
(`CONF_TEMP_MARGIN`) - Innen-/Außentemperatur waren längst vorhanden.
Neues, schlankes Attribut `schwelle_temperatur_marge` (1:1 nach dem
Muster von `schwelle_frostschutz`/`schwelle_hitzeschutz` aus Lektion 13),
danach konnte die Karte `aussentemperatur >= innentemperatur + marge`
genauso selbst nachrechnen wie Frost-/Hitzeschutz. Nur die
Winter-Höchstdauer (`duration`) bleibt jetzt noch als historischer
Rückfallwert übrig - dafür fehlen weiterhin drei Attribute (Winter-
Schwelle, Höchstdauer, Prioritäts-Flag), auf Nutzerwunsch ausdrücklich
zurückgestellt ("reicht erstmal"), nicht in diesem Schritt mit erledigt.

Technisch: `close_fallback` in der Karte wechselte von "grund_code, falls
in [duration, outdoor_warmer, outdoor_wetter]" zu "outdoor_warmer_live,
sonst outdoor_wetter_live, sonst grund_code falls duration" - die beiden
neuen Live-Variablen ersetzen den historischen Rückfallwert für ihre
beiden Fälle komplett, nicht nur als zusätzliche Bedingung daneben.
Dadurch greift automatisch auch das bereits bestehende "Totzone
neutral"-Prinzip (Lektion 29): Trifft aktuell kein Live-Grund mehr zu,
wird die Karte 🟢 - unabhängig vom Fensterzustand -, genau das vom
Nutzer beobachtete Ida-Verhalten korrigierend. Bewusst KEIN Fallback auf
den historischen Wert, falls `schwelle_temperatur_marge` bei einer älteren
Integration-Version (Karte schon aktualisiert, Backend noch nicht) fehlt
- dieser Übergangsfall zeigt dann übergangsweise neutral statt eines
falschen Werts, analog zu `frost_live`/`heat_live`, die genauso nur bei
vorhandener Schwelle greifen. Lokal mit sechs Szenarien gegengetestet
(Jinja-Sandbox, `StrictUndefined`): aktuell wieder kühler/trockener außen
→ 🟢 neutral (Ida-Fall korrigiert), tatsächlich weiterhin wärmer/feuchter
außen bei offenem (Mismatch, 🔴) und geschlossenem (Match, 🟢 "endgültig
gelöst", Lektion 30) Fenster, sowie fehlendes `schwelle_temperatur_marge`-
Attribut (kein Crash, fällt auf neutral zurück). Lektion: Eine als
"strukturell identisch, beide nicht live nachrechenbar" zusammengefasste
Gruppe von zwei Fällen (Lektion 13) kann sich bei erneuter Prüfung als
uneinheitlich herausstellen - der eine brauchte in Wahrheit gar keine
neue Datenbasis (nur ungenutzte, längst vorhandene Attribute), der andere
nur ein einziges zusätzliches, schlankes Attribut nach bereits etabliertem
Muster. Eine pauschale frühere Einschätzung ("das ist halt einer von X
strukturell gleichen, aufwändigen Sonderfällen") verdient bei konkretem
Anlass eine erneute Einzelprüfung, statt automatisch für alle X Fälle
gleich viel Aufwand anzunehmen.

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
  aktualisiert wird. Das Posten des vollständigen YAML-Codes im Chat bei
  jeder Änderung ist eine feste Arbeitsanweisung - siehe ganz oben in
  dieser Datei ("Feste Arbeitsanweisungen").
- Überschreibbare Dropdowns für Zahlenfelder (siehe Lektion 53): bisher nur
  für Erinnerungsintervall und Mindesteinspeiseleistung umgesetzt (global +
  Raum-Override). Der Nutzer wollte weitere geeignete Felder selbst nennen
  (offen) - bei Bedarf `_THRESHOLD_DROPDOWN_OPTIONS` in `config_flow.py`
  um die genannten Felder samt sinnvoller Vorschlagswerte ergänzen, keine
  weiteren Codeänderungen nötig (`_numeric_field_selector()` greift dafür
  automatisch, sowohl global als auch beim Raum-Override).
- Winter-Höchstdauer (`duration`) ist seit Lektion 54 der letzte
  verbleibende Auslöser, den die Dashboard-Karte nur noch historisch aus
  `letzter_grund` anzeigt, nicht live nachrechnet - auf Nutzerwunsch
  ("reicht erstmal") bewusst zurückgestellt. Für eine Live-Berechnung
  fehlen der Karte noch drei Attribute (Winter-Schwelle, Höchstdauer,
  Prioritäts-Flag `CONF_HUMIDITY_PRIORITY_OVER_DURATION`) - `empfehlung_
  aktiv_seit` (bisherige Öffnungsdauer) ist dagegen bereits vorhanden.
