# Smart Climate für Home Assistant

[![Validate](https://github.com/ludgerbeckmann/ha_smart_ventilation/actions/workflows/validate.yml/badge.svg)](https://github.com/ludgerbeckmann/ha_smart_ventilation/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/ludgerbeckmann/ha_smart_ventilation.svg)](https://github.com/ludgerbeckmann/ha_smart_ventilation/releases/)
[![GitHub license](https://img.shields.io/github/license/ludgerbeckmann/ha_smart_ventilation.svg)](https://github.com/ludgerbeckmann/ha_smart_ventilation/blob/main/LICENSE)

Eine Custom Integration, die pro Raum überwacht, ob gelüftet werden sollte –
basierend auf der Innentemperatur, der Luftfeuchtigkeit und der
Außentemperatur. Bei einem Zustandswechsel wird automatisch per
**Sprachausgabe** (z. B. Sonos, oder jede andere `media_player`-Entität) und/oder
**Home Assistant App-Push** benachrichtigt.

## Was die Integration macht

Für jeden konfigurierten Raum wird eine Entität mit dem Namen "**‹Raum›
Lüftungsempfehlung**" angelegt (bei bereits bestehenden Räumen bleibt die
Entity-ID `binary_sensor.lueften_empfohlen_<raum>` unverändert - nur der
angezeigte Name ändert sich; neu angelegte Räume erhalten eine daraus
abgeleitete Entity-ID):

- **on** = Lüften wird empfohlen (Fenster sollte offen sein)
- **off** = Lüften kann beendet werden

Bei jedem Wechsel wird automatisch eine Sprachansage und/oder Push-
Benachrichtigung ausgelöst – ganz ohne zusätzliche Automationen. Du kannst
den binary_sensor zusätzlich in Dashboards, eigenen Automationen oder
Skripten verwenden (z. B. um motorisierte Fenster automatisch zu öffnen).

Ist für einen Raum die **Duscherkennung** aktiviert (siehe "Duscherkennung"
unter "Logik im Detail"), wird zusätzlich eine eigene Entität "**‹Raum›
Dusche aktiv**" angelegt - ein reiner, vom Haupt-Sensor abgeleiteter
Anzeige-Sensor ohne eigene Konfiguration, der **on** meldet, solange
gerade geduscht wird (identisch zum weiterhin vorhandenen
`duschen_erkannt`-Attribut des Haupt-Sensors, nur eben als eigenständige
Entität für Dashboards/Automationen).

## Installation

### Über HACS (empfohlen)

1. HACS → Menü (⋮) → *Benutzerdefinierte Repositories*
2. Repository-URL eintragen (nachdem du dieses Verzeichnis z. B. auf GitHub
   hochgeladen hast), Kategorie **Integration** wählen
3. "Smart Climate" installieren
4. Home Assistant neu starten

### Manuell

1. Ordner `custom_components/ha_smart_ventilation` in deinen
   Home-Assistant-Konfigurationsordner kopieren
   (`<config>/custom_components/ha_smart_ventilation`)
2. Home Assistant neu starten

## Einrichtung

### Raum hinzufügen

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach "Smart Climate" suchen – es öffnet sich zunächst ein kurzer
   erster Schritt zur (optionalen) Auswahl eines **HA-Bereichs**: Wird
   hier ein Bereich gewählt, wird im folgenden Hauptformular der Raumname
   automatisch mit der Bezeichnung dieses Bereichs vorbelegt, und alle
   Sensor-/Geräte-Auswahllisten (Temperatur, Luftfeuchtigkeit, CO2,
   Fensterkontakt, Lautsprecher, Luftentfeuchter, Klimaanlage,
   Fenstersperre/Rollladen) zeigen nur noch die diesem Bereich
   zugeordneten Entitäten an - die **Anwesenheits-Entität** bei den
   App-Benachrichtigungszielen ist bewusst ausgenommen, da eine Person bzw.
   deren Gerät (`person`/`device_tracker`) keinem Raum zugeordnet ist.
   Enthält der gewählte Bereich für eine bestimmte Domain keine passende
   Entität, bleibt die betreffende
   Liste unverändert unbeschränkt (kein Sensor "verschwindet" dadurch).
   Bleibt dieser Schritt leer, funktioniert alles wie bisher – Raumname
   frei eintippen, alle Entitäten wählbar
3. **Hauptformular** ausfüllen (alle Abschnitte sind standardmäßig
   eingeklappt):
   - **Raumname** (ganz oben, ggf. bereits durch den HA-Bereich
     vorbelegt – lässt sich hier weiterhin frei ändern)
   - **Abschnitt "Sensoren & Geräte"** (Mess-Entitäten UND optional
     automatisch gesteuerte Geräte in einem gemeinsamen Abschnitt - beide
     Themen überschneiden sich: eine `climate`-Entität kann sowohl
     Temperatur-Quelle als auch Heizung sein, siehe unten):
     - **Innentemperatur**: eine `climate`-, `sensor`-, `number`- oder
       `input_number`-Entität
     - **Temperatur-Attribut**: immer sichtbar, vorausgewählt ist
       `current_temperature` (Auswahl aus Liste oder eigener Text möglich).
       Wird nur ausgewertet, wenn die gewählte Entität tatsächlich eine
       `climate`-Entität ist – bei `sensor`/`number`/`input_number` wird der
       Wert ignoriert und stattdessen direkt der Entitätszustand verwendet.
     - **Temperaturquelle auch fürs Heizen verwenden** (Checkbox, Standard:
       aus): verwendet automatisch die oben gewählte Innentemperatur-Quelle
       als Heizungs-Gerät, statt sie zusätzlich im Feld "Heizung" separat
       auszuwählen - erspart die doppelte Auswahl derselben Entität für
       Räume, in denen dieselbe `climate`-Entität sowohl die Temperatur
       liefert als auch heizen soll. Nur wirksam, wenn die Temperaturquelle
       tatsächlich eine `climate`-Entität ist (bei `sensor`/`number`/
       `input_number` wie "keine Heizung konfiguriert" behandelt, kein
       Formularfehler). Bei aktiviertem Schalter wird das Feld "Heizung"
       direkt darunter ignoriert (Home-Assistant-Formulare können Felder
       nicht abhängig von einer Checkbox ausblenden, siehe "Home Assistant
       Companion App" im Abschnitt "Benachrichtigungen & Anwesenheit"
       weiter unten)
     - **Heizung** (optional): eine `climate`-Entität - anders als
       Luftentfeuchter/Klimaanlage kein einfaches Ein/Aus, sondern ein
       Umschalten zwischen einem Comfort-, einem Standby- und einem
       Nacht-Sollwert (siehe "Heizungs-Schwelle"/"Comfort-Sollwert"/
       "Standby-Sollwert"/"Nacht-Sollwert"/"Heizungs-Zeitplan aktivieren" im
       Abschnitt "Parameter") - wie für Heizungen typisch. Details siehe
       "Geräte-Steuerung" weiter unten. Wird ignoriert, falls oben
       "Temperaturquelle auch fürs Heizen verwenden" aktiviert ist
     - Optional: Innen-Luftfeuchtigkeit
     - **Duscherkennung** (Checkbox, Standard: aus; nur hier im Raum
       einstellbar, keine globale Einstellung) – siehe "Duscherkennung"
       unter "Logik im Detail". Die zugehörige Anstiegs-Schwelle findet
       sich weiter unten im Abschnitt "Parameter"
     - Optional: CO2 (`sensor`-Entität mit ppm-Wert) – ohne Außenluft-
       Vergleich, da Außenluft praktisch immer weit unter jeder sinnvollen
       Innenschwelle liegt
     - **Dieser Raum hat kein Fenster** (Checkbox, Standard: aus): bei "an"
       werden nie Öffnen-/Schließen-Benachrichtigungen erzeugt – nützlich
       z. B. für fensterlose Flure/Kellerräume, bei denen nur Luftentfeuchter,
       Klimaanlage oder Heizung anhand der Sensorwerte gesteuert werden sollen
       (siehe unten). Die Geräte-Steuerung läuft davon unabhängig weiter,
       unabhängig vom Fenster-Status. Bei "an" ist auch keine
       Benachrichtigungsmethode mehr zwingend erforderlich
     - **Fensterkontakt** (optional; unterdrückt Benachrichtigungen, sobald
       das Fenster laut Sensor bereits im empfohlenen Zustand ist - siehe
       eigener Abschnitt unten; nur relevant, wenn "Dieser Raum hat kein
       Fenster" deaktiviert ist)
     - **Fenstersperre / Rollladen** (optional): eine `cover`- **oder**
       `switch`-Entität, die beim Einschalten der Klimaanlage herunter- und
       beim Ausschalten wieder hochfährt. Bei einer `switch`-Entität bedeutet
       "an" = herunterfahren + gesperrt, "aus" = hochfahren + entsperrt
     - **Schließempfehlung deaktivieren** (Checkbox, Standard: aus): bei
       "an" wird für diesen Raum nie mehr "bitte schließen" empfohlen -
       Temperatur, Luftfeuchtigkeit, CO2, Winter-Höchstdauer und der
       Sommer-Fall bleiben ohne Wirkung aufs Schließen. Sinnvoll für Räume,
       in denen eine Schließen-Empfehlung nicht sinnvoll umsetzbar ist,
       z. B. weil der Fensterkontakt den tatsächlichen Zustand nicht
       zuverlässig widerspiegelt (etwa eine Schiebetür) oder weil eine
       Klimaanlage die Kühlung ohnehin unabhängig vom Fenster übernimmt.
       Frost-/Hitzeschutz sind davon **unberührt** und schließen weiterhin
       sofort (Sicherheits-, keine Komfort-Bedingung) - Öffnen-Empfehlungen
       ebenfalls unberührt
     - **Luftentfeuchter**: eine `switch`- oder `humidifier`-Entität
     - **Tankstatus-Sensor (Luftentfeuchter)** (optional): eine
       `binary_sensor`-Entität, die "an" meldet, sobald der Tank voll ist
       bzw. ein Fehler vorliegt - rein informativ, wird auf der
       Dashboard-Karte als eigenes Status-Icon (🔴 voll/Fehler, 🟢 ok) neben
       dem Luftentfeuchter-Status angezeigt; hat keine Auswirkung auf die
       Lüftungs- oder Geräte-Steuerung selbst
     - **Klimaanlage**: eine `climate`- oder `switch`-Entität
     - **Mindest-Einspeiseleistung** / **Verzögerung bis Abschalten**:
       optionale Raum-Overrides der in "- Smart Climate Optionen -"
       hinterlegten Werte (der Leistungssensor selbst ist nur dort
       hinterlegbar, nicht mehr pro Raum) - auch hier zeigt der
       Hinweistext den aktuell wirksamen globalen Wert an. Gilt nur für
       Luftentfeuchter/Klimaanlage, nicht für die Heizung
   - **Abschnitt "Benachrichtigungen & Anwesenheit"** (früher
     "Benachrichtigungsmethoden" - umbenannt, da hier jetzt auch die
     Anwesenheits-Entitäten für die Heizungs-Pausierung stehen):
     - **Lautsprecher** (`media_player`-Entitäten, z. B. Sonos, Mehrfachauswahl):
       Sprachausgabe ist automatisch aktiv, sobald hier mindestens ein
       Lautsprecher ausgewählt ist – kein eigener Ja/Nein-Schalter mehr,
       auch keine globale Einstellung dafür. Die TTS-Entität selbst kommt
       ausschließlich aus "Smart Climate Optionen" und ist hier nicht
       auswählbar
     - **Wiedergabelautstärke für Sprachausgabe** (optional): überschreibt
       für diesen Raum die in "Smart Climate Optionen" hinterlegte
       Lautstärke - leer gelassen gilt der dort hinterlegte Wert (Hinweistext
       zeigt den aktuell wirksamen globalen Wert an, z. B. "Aktuell global: 40 %")
     - **Home Assistant Companion App** (Ja/Nein/leer) – direkt darunter:
       eine Liste von **App-Benachrichtigungszielen** (leer = globale Ziele
       verwenden). Pro Eintrag: eine `notify.*`-Entität (Pflicht, die
       Auswahl ist auf Entitäten der Home Assistant Companion App
       eingeschränkt - andere notify-Entitäten unterstützen das für das
       "Clean Notification"-Muster benötigte `data`-Feld mit `tag` häufig
       nicht) und optional eine **Anwesenheits-Entität** (`person` oder
       `device_tracker`, individuell pro Ziel) – ist sie gesetzt, erhält
       genau dieses Ziel die Push-Nachricht nur, wenn die Person/das Gerät
       zuhause ist. Über "Hinzufügen" lassen sich beliebig viele Ziele
       ergänzen
     - **Persistente Benachrichtigung (Weboberfläche)** (Ja/Nein/leer) –
       keine weiteren Felder nötig. Erstellt eine dauerhafte Benachrichtigung
       im Home-Assistant-Benachrichtigungsbereich (Glocken-Symbol), solange
       die Empfehlung aktiv ist, und löst sich automatisch wieder auf,
       sobald sie sich erledigt hat
     - Es gibt keine Pflicht mehr, hier etwas auszufüllen - lässt du alles
       leer, gilt komplett die globale Einstellung. Fehlt am Ende sowohl
       raum- als auch global eine gültige Ziel-Entität für eine aktivierte
       Methode, erscheint nur ein Log-Hinweis, das Formular blockiert nicht
     - Bei "Home Assistant Companion App", den App-Benachrichtigungszielen
       und "Persistente Benachrichtigung" zeigt der Hinweistext jetzt
       ebenfalls den aktuell wirksamen globalen Wert an (z. B.
       "Aktuell global: Ja" bzw. die Liste der globalen Ziel-Entitäten)
     - **Erinnerungsintervall** (optional): überschreibt für diesen Raum das
       in "- Smart Climate Optionen -" hinterlegte Intervall - leer gelassen
       gilt der dort hinterlegte Wert (Hinweistext zeigt den aktuell
       wirksamen globalen Wert an). 0 = keine wiederkehrende Erinnerung,
       falls die Empfehlung ignoriert wird
     - **Anwesenheit für Heizung (Personen)** (optional): eine oder mehrere
       `person`- oder `device_tracker`-Entitäten (Mehrfachauswahl) - ist
       mindestens eine hinterlegt, pausiert die Heizung (Standby), solange
       ALLE davon bestätigt "nicht zuhause" melden. Meldet mindestens eine
       "zuhause", oder ist der Zustand einer von ihnen unbekannt/nicht
       verfügbar, heizt der Raum normal weiter (permissiv - ein einzelner
       GPS-Aussetzer soll die Heizung nicht fälschlich abschalten). Ohne
       hinterlegte Entität keine Auswirkung. Unabhängig von den oben
       konfigurierten Anwesenheits-Entitäten der App-Benachrichtigungsziele
       - dort geht es um "wen benachrichtigen", hier um "wann heizen"
   - **Abschnitt "Parameter"** (optional, standardmäßig eingeklappt –
     **überschreibt** für diesen Raum die allgemeinen Einstellungen; leer
     gelassen gilt der dort hinterlegte Wert - als Orientierung zeigt der
     Hinweistext unter jedem dieser Felder zusätzlich den aktuell
     wirksamen globalen Wert an, z. B. "Aktuell global: 23.0 °C"):
     - Schwellenwerte zum Öffnen/Schließen für Temperatur, Luftfeuchtigkeit
       und CO2 sowie Toleranz-Marge, Frostschutz-Grenze, Debounce-Zeit
       Frostschutz, Hitzeschutz-Grenze, Winter-Schwelle und
       Winter-Höchstdauer – Zahlenfelder mit Pfeil-hoch/-runter-Steuerung
       (das Erinnerungsintervall steht jetzt im Abschnitt "Benachrichtigungen
       & Anwesenheit", siehe oben)
     - Anstiegs-Schwelle für die Duscherkennung (nur relevant, wenn diese im
       Abschnitt "Sensoren & Geräte" aktiviert ist)
     - **Heizungs-Schwelle (Innentemperatur)**, **Heizung Comfort-Sollwert**,
       **Heizung Standby-Sollwert** und **Heizung Nacht-Sollwert** (nur
       relevant, wenn im Abschnitt "Sensoren & Geräte" eine Heizung
       hinterlegt oder die Temperaturquelle dafür wiederverwendet wird) -
       siehe dort
     - **Heizungs-Zeitplan aktivieren** (Ja/Nein/leer) - aktiviert, erzwingt
       ein Comfort- bzw. Nacht-Zeitfenster (je acht Zeitfelder: Start/Ende,
       getrennt nach Werktag und Wochenende) den jeweiligen Sollwert
       unabhängig von der Innentemperatur; außerhalb aller Zeitfenster gilt
       Standby. Deaktiviert (Standard) gilt weiterhin die reine
       Schwellenwert-Logik oben. Details siehe "Geräte-Steuerung" weiter
       unten
4. Für weitere Räume den Vorgang wiederholen (Integration erneut
   hinzufügen)

### Allgemeine Einstellungen ("- Smart Climate Optionen -")

Direkt beim ersten Start der Integration wird **automatisch**, ganz ohne
Zutun, ein zusätzlicher Eintrag namens **"- Smart Climate Optionen -"**
angelegt – er taucht unter **Einstellungen → Geräte & Dienste** neben
deinen Räumen auf. Dieser Eintrag erzeugt keine eigene Entität und keinen
eigenen Sensor; er dient ausschließlich als raumübergreifender Standard.

**Bearbeiten:** Beim Eintrag "- Smart Climate Optionen -" auf
**Konfigurieren** (Zahnrad-Symbol) klicken. Ganz oben im Formular steht die
Checkbox **"Auf Standardwerte zurücksetzen"**: aktiviert und gespeichert,
setzt sie sämtliche Schwellenwerte im Abschnitt "Parameter", das
Erinnerungsintervall und sämtliche Benachrichtigungstexte im Abschnitt
"Benachrichtigungen" auf die einprogrammierten Standardwerte zurück -
unabhängig davon, was gerade in diesen Feldern eingetragen ist. Ausgewählte
Entitäten (Sensoren, TTS,
Leistungssensor, App-Benachrichtigungsziele), der Sprachausgabe-Modus und die
Benachrichtigungsmethoden bleiben davon unberührt. Einzelne Felder lassen
sich weiterhin wie gewohnt zurücksetzen, indem man nur sie leert und
speichert (siehe unten) - die Checkbox ist für den Fall gedacht, dass
gleich mehrere oder alle Werte auf einmal zurückgesetzt werden sollen.
Danach folgen drei Abschnitte (aktuell **testweise** alle standardmäßig
eingeklappt - vorher waren "Sensoren" und "Parameter" ausgeklappt):

**Abschnitt "Sensoren"**:
- **Außentemperatur**: wird für **alle** Räume verwendet – kann seit
  dieser Version nicht mehr pro Raum überschrieben werden (dafür gibt es
  im Raum-Formular kein Feld mehr)
- **Außen-Luftfeuchtigkeit** (optional, ebenfalls nur global): ist sie
  gesetzt, wird Lüften bei hoher Innen-Luftfeuchtigkeit nur noch empfohlen,
  wenn es draußen auch **absolut** (nicht nur relativ) trockener ist als
  drinnen – siehe eigener Abschnitt "Absolute vs. relative
  Luftfeuchtigkeit" unten. Ohne diesen Sensor bleibt es beim bisherigen
  Verhalten (Lüften bei hoher Innen-Luftfeuchtigkeit, unabhängig von der
  Außenluft)
- **TTS-Entität**: wird verwendet, wenn ein Raum keine eigene TTS-Entität
  für die Sprachausgabe festlegt
- **Wiedergabelautstärke für Sprachausgabe**: Lautstärke (0–100 %), auf die
  die Lautsprecher **vor** der Ansage gesetzt werden - pro Raum im
  Abschnitt "Benachrichtigungen & Anwesenheit" überschreibbar
- **Vorhandene Wiedergabe beim Ansagen**: "Überlagern" (Standard) spielt die
  Ansage direkt über eine laufende Wiedergabe; "Pausieren" pausiert sie vorher
- **Leistungssensor**: wird für **alle** Räume verwendet – ist nicht mehr
  im Raum-Formular auswählbar
- **Mindest-Einspeiseleistung** + **Verzögerung bis Abschalten**:
  Standardwerte für alle Räume, die keine eigenen Werte festlegen (die
  Werte selbst bleiben pro Raum überschreibbar, siehe Abschnitt
  "Sensoren & Geräte" im Raum-Formular)
- **Home Assistant Companion App** + **App-Benachrichtigungsziele**: globaler
  Standard, pro Raum überschreibbar
- **Persistente Benachrichtigung (Weboberfläche)**: ebenso globaler
  Standard, pro Raum überschreibbar
- **Sommermodus-Vorhersagequelle** (optional, nur global): eine `sensor`-
  oder `weather`-Entität mit einer Temperatur-Vorhersage - z. B. ein eigener
  Template-Sensor, der die Tagesvorhersage als Attribut bereitstellt (kein
  direkter `weather.get_forecasts`-Service-Aufruf durch diese Integration
  nötig, siehe "Geräte-Steuerung" unten). Steuert damit automatisch den
  unten hinterlegten Sommer-/Winterbetrieb-Schalter. Ohne diese Entität
  bleibt der Schalter rein manuell bedienbar
- **Vorhersage-Attribut** (optional): Name eines Attributs der obigen
  Entität, aus dem der Vorhersagewert gelesen wird (z. B. `temperature`).
  Leer = state der Entität direkt als Zahl lesen (z. B. bei einem
  Template-Sensor, dessen state selbst schon der Vorhersagewert ist)
- **Sommer-/Winterbetrieb-Schalter** (optional, nur global): eine bereits
  **vorhandene** `switch`-Entität - wird **nicht** von dieser Integration
  angelegt, sondern nur aktiv gesteuert (analog zu Luftentfeuchter/
  Klimaanlage/Heizung, siehe "Geräte-Steuerung" unten). **An** = Sommerbetrieb
  (Heizung aller Räume pausiert), **Aus** = Winterbetrieb (Heizung läuft
  normal). Ohne konfigurierte Entität hat der Sommer-/Winterbetrieb keine
  Wirkung, selbst wenn eine Vorhersagequelle hinterlegt ist

Sprachausgabe hat hier keine Einstellung mehr – Lautsprecherauswahl und
Aktivierung erfolgen ausschließlich pro Raum (Abschnitt
"Benachrichtigungen & Anwesenheit" im Raum-Formular).

**Abschnitt "Parameter"**:
- Der komplette Schwellenwerte-/Lüftungs-Parameter-Satz (dieselben Felder
  wie im Raum-Parameter-Abschnitt) als raumweiter Standard, inklusive
  CO2-Schwellen zum Öffnen/Schließen, der Anstiegs-Schwelle für die
  Duscherkennung (die Aktivierung selbst ist reine Raumeinstellung, siehe
  oben) sowie der Heizungs-Schwelle und dem Comfort-/Standby-/Nacht-Sollwert
  (die Heizungs-Entität selbst ist wie Luftentfeuchter/Klimaanlage reine
  Raumeinstellung, siehe Abschnitt "Sensoren & Geräte" im Raum-Formular)
- **Heizungs-Zeitplan aktivieren** (global immer ein fester Ja/Nein-Wert,
  Standard Nein) sowie acht Zeitfelder (Comfort-/Nacht-Start/-Ende, je
  getrennt für Werktag und Wochenende) als raumweiter Standard - pro Raum
  überschreibbar wie jeder andere Parameter
- **Sommermodus-Schwelle (Vorhersage)** - ab dieser Vorhersage-Temperatur
  (+/- Toleranz-Marge) wird der oben hinterlegte Sommer-/Winterbetrieb-
  Schalter automatisch eingeschaltet (Sommerbetrieb), darunter automatisch
  wieder ausgeschaltet (Winterbetrieb). Nur global verfügbar, **kein**
  Raum-Override - andernfalls könnten unterschiedliche Räume
  unterschiedliche Entscheidungen für denselben gemeinsamen Schalter
  treffen. Nur wirksam, wenn oben sowohl eine Vorhersagequelle als auch der
  zu steuernde Schalter konfiguriert sind

**Abschnitt "Benachrichtigungen"** (früher "Benachrichtigungstexte" -
umbenannt, da hier jetzt auch das Erinnerungsintervall steht, direkt neben
dem zugehörigen Erinnerungstext; standardmäßig eingeklappt):
- **Erinnerungsintervall** als raumweiter Standard - pro Raum im Abschnitt
  "Benachrichtigungen & Anwesenheit" überschreibbar (siehe oben)

Außerdem ist hier der Wortlaut jeder einzelnen Benachrichtigung frei
anpassbar - je ein Textfeld für:
- Öffnen wegen Temperatur / wegen Luftfeuchtigkeit / wegen CO2
- Schließen wegen Temperatur (allgemein) / Luftfeuchtigkeit / CO2 /
  Frostschutz / Hitzeschutz / Winter-Höchstdauer / weil draußen wärmer
  geworden ist / weil draußen feuchter geworden ist
- Erinnerung (falls die Empfehlung ignoriert wird)

Drei Platzhalter stehen zur Verfügung und werden automatisch ersetzt:
- `{raum}` – der jeweilige Raumname
- `{wert}` – der aktuelle Mess-/Ist-Wert, der die Empfehlung ausgelöst hat,
  bereits inklusive Einheit (z. B. `60 %`, `1234 ppm`, `34.2 °C`, `45 min`)
- `{schwelle}` – der zugehörige Schwellenwert, ebenso inklusive Einheit
  (z. B. `59 %`)

Welcher Mess- und Schwellenwert genau hinter `{wert}`/`{schwelle}` steckt,
hängt vom jeweiligen Textfeld ab – bei "Öffnen wegen Luftfeuchtigkeit"
z. B. aktuelle Luftfeuchtigkeit vs. Feuchtigkeits-Schwelle zum Öffnen, bei
"Schließen wegen Frostschutz" aktuelle Außentemperatur vs.
Frostschutz-Grenze, bei "Schließen wegen Winter-Höchstdauer" bisherige
Öffnungsdauer vs. Höchstdauer, bei der Erinnerung der Wert/die
Öffnen-Schwelle des ursprünglichen Lüftungsgrundes. Damit lässt sich z. B.
formulieren: "Die Luftfeuchtigkeit liegt mit {wert} über dem Schwellenwert
von {schwelle}." Keiner der drei Platzhalter muss verwendet werden – wer
lieber bei kurzen, generischen Texten bleibt, lässt `{wert}`/`{schwelle}`
einfach weg.

Ein Feld komplett zu leeren setzt es beim Speichern automatisch wieder auf
den mitgelieferten Standardtext zurück. Enthält ein selbst angepasster
Text einen ungültigen Platzhalter (z. B. Tippfehler wie `{room}` statt
`{raum}`), wird die Nachricht trotzdem unverändert verschickt (ein
entsprechender Hinweis erscheint dann im Log) - eine Benachrichtigung geht
dadurch nie komplett verloren.

Alle Zahlenfelder sind immer mit einem sinnvollen Standardwert vorausgefüllt
– wird ein Feld komplett geleert, greift beim Speichern automatisch wieder
dieser Standardwert.

> Home Assistant erlaubt es grundsätzlich, jeden Integrations-Eintrag über
> die Oberfläche zu löschen – das lässt sich nicht unterbinden. Löschst du
> "- Smart Climate Optionen -" trotzdem, wird er **automatisch sofort wieder
> neu angelegt** (mit den Standardwerten) – er soll ja immer vorhanden
> sein. Willst du ihn stattdessen dauerhaft loswerden, müsstest du die
> gesamte Integration deinstallieren oder den Eintrag manuell deaktivieren
> statt zu löschen.

**Zur Sortierung in der Integrationsliste:** Es gibt keinen zuverlässigen
Trick, um "- Smart Climate Optionen -" in der Liste an eine bestimmte
Stelle zu bringen. Ein früherer Versuch mit einer führenden Ziffer im
Namen hat sich als wirkungslos erwiesen – die Reihenfolge mehrerer
Einträge einer Integration richtet sich in Home Assistant offenbar nicht
zuverlässig nach dem Namen (mehrfach von Nutzern als "wirkt zufällig"
gemeldet), sondern vermutlich eher nach der Reihenfolge, in der die
Einträge angelegt wurden. Da "- Smart Climate Optionen -" meist erst nach
bereits bestehenden Räumen automatisch erzeugt wird, taucht er entsprechend
oft weiter unten auf. Eine nachträgliche Änderung ist darüber nicht
zuverlässig erreichbar.

## Bestehenden Eintrag bearbeiten

Ein bereits eingerichteter Raum – oder "- Smart Climate Optionen -" – lässt
sich jederzeit nachträglich anpassen, ohne ihn zu löschen und neu anzulegen:

1. **Einstellungen → Geräte & Dienste → Smart Climate** (bzw. der von
   dir vergebene Name)
2. Beim gewünschten Eintrag auf **Konfigurieren** klicken
3. Es öffnet sich das passende Formular, mit den aktuell gespeicherten
   Werten vorausgefüllt
4. Nach dem Speichern wird der Eintrag automatisch mit den neuen
   Einstellungen neu geladen – ein manueller Neustart von Home Assistant
   ist dafür nicht nötig

> Hinweis: Home-Assistant-Formulare können Felder nicht dynamisch während
> der Eingabe ein-/ausblenden. Das Ziel-Feld für die App-Benachrichtigung im
> Abschnitt "Benachrichtigungen & Anwesenheit" ist deshalb immer sichtbar,
> wird aber nur ausgewertet, wenn die Checkbox aktiviert ist.
>
> Änderungen an den globalen Einstellungen wirken sich auf alle Räume ohne
> eigenen Override aus - allerdings nicht sofort, sondern spätestens beim
> nächsten 5-Minuten-Tick jedes Raums (kein sofortiger Reload aller
> Raum-Entitäten).
>
> Beim Bearbeiten eines Raums steht - anders als beim Neuanlegen - kein
> eigener erster Schritt für den HA-Bereich zur Verfügung; das Feld
> "HA-Bereich" findet sich hier direkt ganz oben im selben Formular, neben
> dem Raumnamen. Änderst du den Bereich hier und speicherst, werden beim
> ersten Speichern zunächst nur die darunter angezeigten Sensor-/
> Geräte-Auswahllisten auf den neuen Bereich aktualisiert (das Formular
> bleibt offen, bereits gemachte Eingaben bleiben erhalten) - erst ein
> zweites Speichern übernimmt die Änderungen tatsächlich.

## HA-Bereich nachträglich zuordnen oder ändern

Ein Raum, der schon vor diesem Feature angelegt wurde (oder bei dem der
erste Schritt leer gelassen wurde), hat keinen HA-Bereich hinterlegt - die
Sensor-Auswahllisten zeigen dann weiterhin, wie gewohnt, alle Entitäten.
Das lässt sich jederzeit nachträglich ändern: Eintrag über "Konfigurieren"
öffnen, oben das Feld "HA-Bereich" setzen und speichern - die Auswahllisten
darunter werden daraufhin sofort entsprechend eingeschränkt angezeigt
(Formular bleibt offen), ein zweites Speichern übernimmt die Änderung.
Umgekehrt lässt sich ein einmal gesetzter Bereich genauso wieder leeren, um
zur unbeschränkten Auswahl zurückzukehren.

## Logik im Detail

**Öffnen** wird empfohlen, wenn (und weder Frost- noch Hitzeschutz greift):
- Innentemperatur ≥ "Schwelle zum Öffnen" **und** draußen mindestens um die
  Toleranz-Marge kühler ist als drinnen, **oder**
- Luftfeuchtigkeit ≥ "Schwelle zum Öffnen" **und** (kein Außen-
  Luftfeuchtigkeitssensor hinterlegt **oder** es draußen **absolut**
  betrachtet trockener ist als drinnen – siehe "Absolute vs. relative
  Luftfeuchtigkeit" unten), **oder**
- CO2 ≥ "CO2-Schwelle zum Öffnen" – **ohne** Außenluft-Vergleich, da
  Außenluft praktisch immer bei ~420 ppm liegt und Lüften bei hohem CO2
  immer hilft

**Schließen** wird empfohlen, wenn:
- Innentemperatur ≤ "Schwelle zum Schließen" – *außer* es wird gerade noch
  aus Feuchtigkeits- oder CO2-Gründen gelüftet (siehe "Vorrang zwischen
  Temperatur/Luftfeuchtigkeit/CO2" unten), **oder**
- Luftfeuchtigkeit ≤ "Schwelle zum Schließen" – *außer* es wird gerade noch
  aus Temperatur- oder CO2-Gründen gelüftet, **oder**
- CO2 ≤ "CO2-Schwelle zum Schließen" – *außer* es wird gerade noch aus
  Temperatur- oder Feuchtigkeits-Gründen gelüftet. Anders als bei
  Frostschutz/Hitzeschutz gibt es für CO2 keinen "zu niedrig ist
  gefährlich"-Fall - ein niedriger CO2-Wert ist unproblematisch, das
  Schließen dient hier nur der Ordnung, nicht der Sicherheit. Der
  Auslöser-Eintrag in der Empfehlungs-Tabelle erscheint trotzdem ganz
  normal (der Grund ist ja real), nur die Benachrichtigung entfällt -
  kein zwingender Handlungsbedarf, **oder**
- **Sommer-Fall**: draußen ist mittlerweile mindestens um die Toleranz-Marge
  wärmer als drinnen – *außer* es wird gerade noch aus Feuchtigkeits- oder
  CO2-Gründen gelüftet, **oder**
- **Außenluft inzwischen feuchter**: das Pendant zum Sommer-Fall für
  Luftfeuchtigkeit – die Öffnen-Empfehlung wegen Luftfeuchtigkeit prüft
  einmalig beim Öffnen, ob die Außenluft absolut trockener ist als die
  Innenluft (siehe oben); ändert sich das *danach* (Außenluft wird absolut
  feuchter als die Innenluft, z. B. weil es zu regnen beginnt), würde
  Lüften die Situation nur noch verschlimmern. Schließt daher genauso
  nach, *außer* es wird gerade noch aus Temperatur- oder CO2-Gründen
  gelüftet. Nur bei vollständig vorliegenden Innen-/Außenwerten aktiv -
  ein nur fehlender Messwert schließt hier bewusst **nicht**
  vorsorglich (reiner Komfort-, kein Sicherheitsfall wie beim
  Frostschutz), **oder**
- **Winter-Höchstdauer**: es herrschen "Winter"-Bedingungen (Außentemperatur
  unter der Winter-Schwelle) **und** die Empfehlung ist bereits länger als die
  eingestellte Höchstdauer aktiv – *außer* die Einstellung "Luftfeuchtigkeit/
  CO2 haben Vorrang vor Winter-Höchstdauer" ist aktiv (Standard) **und** es
  wird gerade noch aus Feuchtigkeits- oder CO2-Gründen gelüftet, **oder**
- **Frostschutz**: die Außentemperatur ist auf/unter die Frostschutz-Grenze
  gefallen **oder** der Außentemperatur-Sensor ist zwar konfiguriert, meldet
  aber gerade `unavailable`/`unknown` (z. B. während Home Assistant
  startet/stoppt - beide Fälle werden gleich behandelt). Das reine
  **Blockieren des Öffnens** greift dabei immer sofort (unabhängig von
  allen anderen Bedingungen, **auch** falls noch aus Feuchtigkeits- oder
  CO2-Gründen gelüftet wird - Frostschutz hat immer Vorrang) - konservativ
  zu bleiben ist risikofrei. Das tatsächliche **Schließen eines bereits
  offenen Zustands** greift dagegen erst, sobald einer dieser beiden Fälle
  ununterbrochen für mindestens die eingestellte "Debounce-Zeit
  Frostschutz" (Standard 10 Minuten, 0 = ohne Verzögerung) anhält - das
  verhindert ein sofortiges, ungewolltes Schließen sowohl durch einen
  einzelnen unplausiblen Ausreißer-Messwert als auch durch eine kurze
  Sensor-Nichtverfügbarkeit beim Neustart. Das durch einen tatsächlich
  niedrigen Messwert ausgelöste Schließen erhält einen Auslöser-Eintrag
  samt Benachrichtigung; das durch einen fehlenden Sensor ausgelöste
  Schließen bleibt bewusst **stumm**: kein Auslöser-Eintrag in der
  Empfehlungs-Tabelle, keine Benachrichtigung, da es sich meist nur um
  einen vorübergehenden Zustand beim Neustart handelt, **oder**
- **Hitzeschutz**: die Außentemperatur ist auf/über die Hitzeschutz-Grenze
  gestiegen (Pendant zum Frostschutz, greift genauso sofort und unabhängig
  von allen anderen Bedingungen - Lüften würde absehbar nur noch Hitze
  hereinlassen, egal ob eigentlich wegen Temperatur, Luftfeuchtigkeit oder
  CO2 gelüftet werden sollte)

Ist im Raum-Formular "Schließempfehlung deaktivieren" aktiviert, entfallen
alle sechs oben genannten **Komfort**-Schließgründe (Temperatur,
Luftfeuchtigkeit, CO2, Winter-Höchstdauer, Sommer-Fall, Außenluft
inzwischen feuchter) komplett - einmal
geöffnet, bleibt die Empfehlung "Öffnen" bestehen, bis Frost- oder
Hitzeschutz greift. Frost-/Hitzeschutz selbst sind von dieser Einstellung
**nicht** betroffen und schließen weiterhin wie gewohnt sofort - das sind
Sicherheits-, keine Komfort-Bedingungen.

**Vorrang zwischen Temperatur/Luftfeuchtigkeit/CO2:** Die drei Größen
schützen sich gegenseitig davor, allein wegen einer der beiden anderen
geschlossen zu werden - das gilt symmetrisch in alle Richtungen: Temperatur
schließt nicht, solange noch Luftfeuchtigkeits- oder CO2-Bedarf besteht,
Luftfeuchtigkeit schließt nicht, solange noch Temperatur- oder CO2-Bedarf
besteht, und CO2 schließt nicht, solange noch Temperatur- oder
Luftfeuchtigkeits-Bedarf besteht. Auch Sommer-Fall und Winter-Höchstdauer
respektieren das (siehe oben). Ist das Fenster bereits wegen einer Größe
offen, gilt deren Schutzwirkung so lange, bis **diese** Größe auf ihre
eigene **Schließen**-Schwelle gefallen ist - nicht schon, sobald sie unter
ihre (höhere) Öffnen-Schwelle fällt. Sonst würde die Empfehlung bei Werten
zwischen den beiden Schwellen ständig hin- und herflackern (z. B. "wegen
Temperatur schließen" und "wegen Luftfeuchtigkeit/CO2 wieder öffnen"),
obwohl sich der eigentliche Lüftungsbedarf die ganze Zeit über nicht
geändert hat. Einzige Ausnahme: Frost- und Hitzeschutz haben immer Vorrang.

**Konfigurierbare Priorität bei Winter-Höchstdauer:** Der Parameter
"Luftfeuchtigkeit/CO2 haben Vorrang vor Winter-Höchstdauer" legt fest, wie
dieser Konflikt aufgelöst wird:
- **An (Standard)**: Luftfeuchtigkeit/CO2 gewinnen – die Winter-Höchstdauer
  wird bei noch bestehendem Feuchtigkeits- oder CO2-Lüftungsbedarf
  ignoriert, das Fenster bleibt offen (Gesundheit/Schimmelvermeidung vor
  Wärmeverlust-Begrenzung)
- **Aus**: die Winter-Höchstdauer wird strikt durchgesetzt, auch bei noch
  hoher Luftfeuchtigkeit oder hohem CO2-Wert (Wärmeverlust-Begrenzung vor
  Schimmelvermeidung/Gesundheit)

In den globalen Einstellungen ("Smart Climate Optionen") als fester
Ja/Nein-Schalter, im Raum-Parameter-Abschnitt als Ja/Nein/Leer-Auswahl
(leer = globalen Wert verwenden; der Hinweistext zeigt dabei auch hier den
aktuell wirksamen globalen Wert an, z. B. "Aktuell global: Ja"). Frost- und
Hitzeschutz haben davon unabhängig immer Vorrang, unabhängig von dieser
Einstellung.

Die reine Temperatur-Schließbedingung berücksichtigt einen noch
bestehenden Feuchtigkeits- oder CO2-Lüftungsbedarf dagegen immer (nicht
konfigurierbar) - ein Schließen nur wegen erreichter Zieltemperatur,
gefolgt von einem sofortigen erneuten Öffnen deswegen, ergäbe so gut wie
nie Sinn.

**Duscherkennung:** Optional (Standard aus, nur im Raum-Formular unter
"Sensoren & Geräte" aktivierbar - keine globale Einstellung), gedacht für Bäder mit
Dusche/Badewanne, bei denen die Luftfeuchtigkeit durch das Duschen sehr
schnell ansteigt. Ist "Duscherkennung" für einen Raum aktiviert, wird
laufend der Anstieg der bereits konfigurierten Luftfeuchtigkeit über die
letzten 10 Minuten beobachtet - kein zusätzlicher Sensor nötig. Steigt die
Luftfeuchtigkeit schneller als die "Anstiegs-Schwelle" (Standard 1,5
%-Punkte/Minute, im Abschnitt "Parameter" einstellbar), wird angenommen,
dass gerade geduscht wird: die Öffnen-Empfehlung wegen Luftfeuchtigkeit
bleibt währenddessen zurückgehalten, da Lüften mitten im Duschvorgang
nichts bringt (es entsteht weiter Dampf). Sobald der Anstieg wieder unter
die Schwelle fällt (Duschen vorbei, Luftfeuchtigkeit stabilisiert sich oder
sinkt bereits wieder), greift die normale Feuchtigkeits-Logik und die
Öffnen-Empfehlung erfolgt wie gewohnt. Der aktuelle Erkennungsstatus steht
als Attribut `duschen_erkannt` des Haupt-Sensors zur Verfügung, sowie -
sobald die Funktion für den Raum aktiviert ist - zusätzlich als eigene
Entität "‹Raum› Dusche aktiv" (siehe "Was die Integration macht" oben).
Rein temperatur- oder anders begründete Öffnen-Empfehlungen (siehe oben)
sind von der Duscherkennung nicht betroffen.

**Zusätzlich:**
- **Frostschutz** verhindert außerdem grundsätzlich das Öffnen, solange die
  Außentemperatur auf/unter der Frostschutz-Grenze liegt
- **Hitzeschutz** verhindert ebenso grundsätzlich das Öffnen, solange die
  Außentemperatur auf/über der Hitzeschutz-Grenze liegt (Standard 30 °C) -
  anders als beim Frostschutz wird ein fehlender/nicht verfügbarer
  Außentemperatur-Wert dabei NICHT vorsorglich als "zu heiß" gewertet
  (das übernimmt in diesem Fall bereits der Frostschutz als konservativer
  Fallback)
- **Erinnerung**: ist ein Erinnerungsintervall > 0 eingestellt, wird die
  Benachrichtigung wiederholt, solange die Empfehlung aktiv bleibt (z. B.
  falls das Fenster trotzdem nicht geöffnet wurde)
- Die **Toleranz-Marge** verhindert, dass die Empfehlung bei Außen-/
  Innentemperaturen nahe beieinander ständig zwischen "öffnen" und
  "schließen" hin- und herspringt

**Nicht berücksichtigt** (bewusst, aktuell außerhalb des Funktionsumfangs):
Regen und Windgeschwindigkeit.

## Fensterkontakt und Benachrichtigungen

Ist im Abschnitt "Sensoren & Geräte" ein Fensterkontakt hinterlegt, wird sein
Zustand vor jeder Benachrichtigung geprüft:

- **Öffnen-Empfehlung**: Wird nur verschickt, wenn der Fensterkontakt
  aktuell "zu" meldet. Zeigt er bereits "offen" (Zustand `on`), wird keine
  Benachrichtigung gesendet - das Fenster ist ja schon offen.
- **Schließen-Empfehlung**: Umgekehrt - wird nur verschickt, wenn der
  Fensterkontakt aktuell "offen" meldet.
- **Erinnerung**: Wird ebenfalls unterdrückt, sobald der Fensterkontakt den
  empfohlenen Zustand bereits erreicht hat.

Erwartete Konvention des Sensors: `on` = Fenster offen, `off` = Fenster zu
(Standard bei `binary_sensor`-Entitäten mit `device_class` `window`,
`door` oder `opening`). Ohne hinterlegten Fensterkontakt - oder bei
unbekanntem/nicht verfügbarem Sensorzustand - wird sicherheitshalber
weiterhin immer benachrichtigt, wie bisher.

## Absolute vs. relative Luftfeuchtigkeit

Der Außen-/Innenvergleich für die Feuchtigkeits-Öffnen-Bedingung nutzt
bewusst **nicht** die relative Luftfeuchtigkeit (% RH), sondern rechnet
daraus die **absolute** Luftfeuchtigkeit (g Wasser pro m³ Luft, über die
Magnus-Formel aus Temperatur + relativer Feuchte) und vergleicht diese.

**Warum das wichtig ist:** Relative Luftfeuchtigkeit ist stark
temperaturabhängig - dieselbe Menge Wasser in der Luft ergibt bei kalter
Luft eine hohe %-Zahl und bei warmer Luft eine niedrige, weil warme Luft
viel mehr Feuchtigkeit aufnehmen kann. Praktisch relevantester Fall:

- **Winter**: Draußen zeigt der Sensor oft 85–95 % RH bei wenigen Grad
  Celsius an. Ein reiner %-Vergleich würde das als "draußen feuchter"
  werten und vom Lüften abraten - dabei ist kalte Luft absolut gesehen
  meist sehr trocken. Sobald sie hereinströmt und sich erwärmt, sinkt ihre
  RH oft auf 20–30 %. Winterliches Stoßlüften ist deshalb in der Praxis
  eine der wirksamsten Entfeuchtungsmethoden - mit einem reinen
  RH%-Vergleich hätte die Integration genau davon abgeraten.
- **Sommer**: Umgekehrt kann draußen bei Hitze ein niedrigerer RH%-Wert
  gemessen werden als drinnen, obwohl die Luft absolut mehr Wasser enthält.
  Ein reiner %-Vergleich hätte hier fälschlich zum Lüften geraten.

Die Schwellenwerte zum Öffnen/Schließen selbst (im Parameter-Abschnitt)
bleiben bewusst in % RH - das ist der Wert, der spürbar ist und der
Schimmelrisiko-Bewertungen zugrunde liegt. Nur der reine Außen-/
Innenvergleich ("würde Lüften die Feuchtigkeit tatsächlich senken?")
nutzt die berechnete absolute Feuchte.

## Geräte-Steuerung (Luftentfeuchter/Klimaanlage/Heizung/Sommer-/Winterbetrieb)

Optional kann pro Raum ein Luftentfeuchter, eine Klimaanlage und/oder eine
Heizung hinterlegt werden, die automatisch gesteuert werden:

- **Luftentfeuchter**: an bei Luftfeuchtigkeit ≥ "Schwelle zum Öffnen", aus
  bei ≤ "Schwelle zum Schließen" - grundsätzlich unabhängig vom
  Fenster-Status. Eine Ausnahme: Meldet der Fensterkontakt-Sensor das
  Fenster als **offen**, pausiert der Luftentfeuchter, sofern die Außenluft
  dabei nicht absolut trockener ist als die Innenluft (derselbe Vergleich
  wie bei der Öffnen-Empfehlung wegen Luftfeuchtigkeit, siehe "Absolute vs.
  relative Luftfeuchtigkeit" unten) - sonst würde er nur gegen ständig
  nachströmende feuchte Luft anarbeiten und dabei Energie verschwenden. Ist
  die Außenluft dagegen absolut trockener, läuft er bei offenem Fenster
  unverändert weiter, da das Lüften die Entfeuchtung zusätzlich
  unterstützt. Ohne konfigurierten Fensterkontakt-Sensor oder ohne
  Außen-Luftfeuchtigkeitssensor entfällt diese Ausnahme komplett (wie
  bisher rein nach den Innen-Schwellen). Ist ein Leistungssensor
  konfiguriert (siehe unten) UND meldet dieser gerade genug
  Einspeiseleistung, entfällt die Pausierung ebenfalls - überschüssige,
  sonst ungenutzte Leistung zu verbrauchen ist kein Verlust, selbst wenn
  der Luftentfeuchter dabei nur gegen nachströmende feuchte Luft ankämpft.
- **Klimaanlage**: an, wenn Innentemperatur ≥ "Schwelle zum Öffnen" **und**
  Lüften nicht helfen würde (draußen nicht ausreichend kühler). Aus, sobald
  die Innentemperatur die "Schwelle zum Schließen" erreicht **oder** Lüften
  wieder ausreicht. Ergänzt damit gezielt die Fensterlogik, statt sie zu
  duplizieren: Wenn Lüften reicht, läuft keine Klimaanlage.
- **Heizung**: anders als Luftentfeuchter/Klimaanlage kein einfaches
  Ein/Aus, sondern ein Umschalten zwischen drei festen Sollwerten (Comfort/
  Standby/Nacht, über `climate.set_temperature`) - wie für Heizungen
  typisch. Pausen (Fenster offen, niemand zuhause, Sommerbetrieb aktiv - alle
  drei siehe unten) haben dabei immer höchste Priorität und schalten sofort
  auf **Standby**, unabhängig von allem anderen unten.

  Ist **"Heizungs-Zeitplan aktivieren"** (Abschnitt "Parameter")
  **deaktiviert** (Standard), gilt außerhalb dieser Pausen weiterhin die
  ursprüngliche reine Schwellenwert-Logik: Fällt die Innentemperatur unter
  die "Heizungs-Schwelle", wird der **Comfort-Sollwert** gesetzt; erreicht
  sie die Schwelle plus Toleranz-Marge wieder (Hysterese, verhindert
  Flackern nahe der Schwelle), wird auf den **Standby-Sollwert**
  zurückgeschaltet. Dazwischen bleibt der zuletzt gesetzte Sollwert
  unverändert. Ist gerade kein Innentemperatur-Messwert verfügbar, wird
  bewusst **nichts** geändert (kein sicherheits-, nur komfortrelevanter
  Fall).

  Ist der Zeitplan **aktiviert**, erzwingt stattdessen ein Zeitfenster den
  Sollwert **unabhängig von der Innentemperatur**: Innerhalb des
  Comfort-Zeitfensters (Start/Ende) gilt der **Comfort-Sollwert**, innerhalb
  des Nacht-Zeitfensters der **Nacht-Sollwert**, außerhalb beider Fenster
  der **Standby-Sollwert**. Beide Zeitfenster sind je einmal für Werktage
  und einmal fürs Wochenende konfigurierbar (acht Zeitfelder insgesamt), da
  sich z. B. der Aufstehzeitpunkt am Wochenende typischerweise verschiebt.
  Überlappen sich beide Fenster versehentlich, hat das Nacht-Fenster
  Vorrang. Die "Heizungs-Schwelle" selbst bleibt bei aktiviertem Zeitplan
  ohne Wirkung.

  Die Heizung setzt voraus, dass die gewählte `climate`-Entität bereits im
  gewünschten Heiz-Betriebsmodus steht (z. B. "Heizen"/"Auto") - diese
  Integration ändert nur den Sollwert, nicht den Betriebsmodus selbst.
  Unberührt vom Leistungssensor unten - die Heizung startet unabhängig von
  einer eventuell konfigurierten Mindest-Einspeiseleistung. Ist die als
  Innentemperatur-Quelle gewählte Entität selbst bereits eine `climate`-
  Entität, kann sie über die Checkbox "Temperaturquelle auch fürs Heizen
  verwenden" direkt als Heizungs-Gerät wiederverwendet werden, statt sie
  zusätzlich im Feld "Heizung" ein zweites Mal auszuwählen.

  **Pausen im Detail:**
  - Solange der Fensterkontakt-Sensor das Fenster als **bestätigt offen**
    meldet - gegen ein offenes Fenster zu heizen verschwendet nur Energie.
  - Sobald im Abschnitt "Benachrichtigungen & Anwesenheit" mindestens eine
    Anwesenheits-Entität für die Heizung hinterlegt ist UND ALLE davon
    bestätigt "nicht zuhause" melden - meldet mindestens eine "zuhause",
    oder ist der Zustand einer von ihnen gerade unbekannt/nicht verfügbar,
    heizt der Raum normal weiter (permissiv, ein einzelner GPS-Aussetzer
    soll die Heizung nicht fälschlich abschalten). Ohne konfigurierte
    Entität entfällt diese Bedingung komplett.
  - Solange der globale **Sommer-/Winterbetrieb-Schalter** (siehe unten)
    **an** ist (Sommerbetrieb) - pausiert dann die Heizung **aller** Räume.
- **Sommer-/Winterbetrieb**: **kein** eigenes, von dieser Integration
  angelegtes Gerät, sondern eine bereits **vorhandene** `switch`-Entität,
  die in "- Smart Climate Optionen -" hinterlegt und von dieser Integration
  **aktiv gesteuert** wird - genau wie Luftentfeuchter/Klimaanlage/Heizung
  jeweils eine bereits vorhandene Entität steuern, statt eine eigene
  anzulegen. **An** = Sommerbetrieb, pausiert die Heizung **aller** Räume
  (siehe oben). **Aus** = Winterbetrieb, Heizung läuft normal. Nur global
  verfügbar (kein Raum-Override), da mehrere Räume mit unterschiedlichen
  Schwellen sonst gegensätzlich auf denselben gemeinsamen Schalter schreiben
  könnten.

  Wird **automatisch** ein-/ausgeschaltet, sobald in "- Smart Climate
  Optionen -" sowohl eine **Sommermodus-Vorhersagequelle** als auch der zu
  steuernde Schalter hinterlegt sind: Erreicht die Vorhersage-Temperatur die
  "Sommermodus-Schwelle" plus Toleranz-Marge, wird der Schalter
  eingeschaltet; fällt sie unter die Schwelle minus Toleranz-Marge, wieder
  ausgeschaltet - dazwischen sowie ohne verfügbare Vorhersage bleibt der
  aktuelle (automatisch ODER manuell gesetzte) Live-Zustand des Schalters
  unverändert. Ein manueller Schaltvorgang wird dadurch nicht sofort wieder
  überschrieben, sondern bleibt bestehen, bis die Vorhersage die jeweilige
  Grenze eindeutig über-/unterschreitet - der Schalter bleibt also jederzeit
  auch manuell bedienbar. Ohne konfigurierte Vorhersagequelle **oder** ohne
  konfigurierten Schalter unterbleibt jede automatische Schaltung. Da jeder
  Raum unabhängig voneinander dieselbe Entscheidung anhand derselben
  globalen Vorhersage-/Schwellenwerte trifft und ggf. denselben Schalter
  ansteuert, sind redundante, aber harmlose Schreibversuche mehrerer Räume
  im selben Bewertungslauf möglich - nur der erste tatsächlich abweichende
  Schreibversuch ändert etwas, alle weiteren sehen bereits den neuen
  Live-Zustand und tun nichts.

  Diese Integration ruft dafür **keinen eigenen `weather.get_forecasts`-
  Service** auf (das wäre der erste nicht-simple State-Read dieser
  Integration gewesen) - stattdessen wird eine vom Nutzer selbst gepflegte
  Entität gelesen, z. B. ein Template-Sensor, der die Tagesvorhersage per
  eigener `time_pattern`-Automation regelmäßig aus `weather.get_forecasts`
  in ein Attribut schreibt (siehe Home-Assistant-Dokumentation zu
  `weather`-Vorhersage-Entitäten für ein Beispiel-Template).
- **Leistungssensor (optional)**: Ist eine "Mindest-Einspeiseleistung"
  konfiguriert, wird ein Gerät (Luftentfeuchter/Klimaanlage, nicht die
  Heizung, nicht der Sommer-/Winterbetrieb-Schalter) nur eingeschaltet, wenn
  der Sensor mindestens diesen Wert meldet (z. B. um nur bei PV-Überschuss
  zu starten). Ohne Leistungssensor entfällt diese Bedingung komplett.
- **Verzögertes Abschalten bei Einspeisung**: Ist die Einspeiseleistung
  ununterbrochen seit mindestens der eingestellten "Verzögerung bis
  Abschalten" zu niedrig, wird ein bereits laufendes Gerät deswegen
  abgeschaltet. Kurze Schwankungen (z. B. eine vorbeiziehende Wolke) führen
  also nicht sofort zum Abschalten - erst wenn der Zustand dauerhaft anhält.
  Unabhängig davon wird ein Gerät natürlich sofort abgeschaltet, sobald die
  eigentliche Zielbedingung (Temperatur/Feuchtigkeit) erreicht ist.
- Wird die Mindest-Einspeiseleistung beim gewünschten Einschalten nicht
  erreicht, wird die Prüfung spätestens alle 5 Minuten automatisch wiederholt.
- **Rollladen-Kopplung**: Ist bei der Klimaanlage eine Fenstersperre/Rollladen
  hinterlegt, wird diese automatisch aktiviert, sobald die Klimaanlage
  einschaltet, und wieder deaktiviert, sobald sie ausschaltet. Unterstützt
  sowohl `cover`-Entitäten (auf/zu) als auch `switch`-Entitäten (an =
  herunterfahren + gesperrt, aus = hochfahren + entsperrt).

## Attribute für eine Statusübersicht

Jede `binary_sensor.lueften_empfohlen_<raum>`-Entität liefert zusätzlich zum
reinen Ein/Aus-Zustand folgende Attribute (sichtbar unter Entwicklerwerkzeuge
→ Zustände, oder nutzbar in eigenen Dashboards/Templates):

| Attribut | Bedeutung |
|---|---|
| `raum` | Raumname |
| `innentemperatur` | aktueller Messwert |
| `aussentemperatur` | aktueller Messwert (aus "Smart Climate Optionen") |
| `schwelle_temperatur_oeffnen` / `_schliessen` | aktuell wirksame Schwellenwerte (inkl. Raum-Override/globaler Fallback) |
| `schwelle_frostschutz` / `schwelle_hitzeschutz` | aktuell wirksame Frostschutz-/Hitzeschutz-Grenze - nur vorhanden, falls ein Außentemperatur-Sensor hinterlegt ist. Dient hauptsächlich der Dashboard-Karte, um Frost-/Hitzeschutz live gegen die aktuelle Außentemperatur zu prüfen, statt sich auf den historischen `letzter_grund` verlassen zu müssen |
| `luftfeuchtigkeit`, `schwelle_feuchtigkeit_oeffnen` / `_schliessen` | nur vorhanden, falls ein Luftfeuchtigkeits-Sensor hinterlegt ist |
| `co2`, `schwelle_co2_oeffnen` / `_schliessen` | nur vorhanden, falls ein CO2-Sensor hinterlegt ist |
| `aussen_luftfeuchtigkeit` | nur vorhanden, falls global gesetzt |
| `absolute_luftfeuchtigkeit` / `aussen_absolute_luftfeuchtigkeit` | berechnete absolute Luftfeuchtigkeit (g/m³, siehe "Absolute vs. relative Luftfeuchtigkeit") - nur vorhanden, wenn die jeweils nötigen Temperatur-/Feuchtigkeitswerte verfügbar sind. Genau diese Werte entscheiden, ob Lüften bei hoher Innen-Luftfeuchtigkeit tatsächlich empfohlen wird |
| `empfehlung_aktiv_seit` | Zeitpunkt, seit dem "Lüften empfohlen" aktiv ist |
| `letzter_grund` | Grund der letzten Empfehlungsänderung (`temp`, `humidity`, `co2`, `frost`, `heat`, `duration`, `outdoor_warmer`, `outdoor_wetter`) - fehlt ein Außentemperatur-Wert (Sensor gerade `unavailable`/`unknown`), schließt der Frostschutz zwar vorsorglich, ohne dabei `letzter_grund` zu setzen (siehe "Logik im Detail") |
| `letzte_benachrichtigung` | Zeitpunkt der letzten tatsächlich verschickten Benachrichtigung |
| `luftentfeuchter_an`, `klimaanlage_an` | nur vorhanden, falls die jeweiligen Geräte konfiguriert sind UND ihre Entität aktuell im Zustandsautomaten existiert (nicht z. B. wegen deaktiviertem Integrationseintrag komplett entfernt) - live vom tatsächlichen Gerätezustand gelesen (auch wenn das Gerät manuell oder von einer anderen Automation ein-/ausgeschaltet wurde, nicht nur wenn diese Integration es selbst geschaltet hat). Ist die Entität komplett verschwunden, wird das Gerät auch nicht mehr gesteuert - anders als eine bloß vorübergehende "nicht verfügbar"-Meldung (Gerät kurz offline), die weiterhin wie "aus" behandelt wird |
| `luftentfeuchter_grund`, `klimaanlage_grund` | nur vorhanden, falls das jeweilige Gerät konfiguriert und seine Entität vorhanden ist - kurzer, rein informativer Text, warum das Gerät aktuell an/aus ist bzw. pausiert (z. B. "Luftfeuchtigkeit über Schwelle", "pausiert: Fenster offen, Außenluft nicht trockener"); live bei jeder Neubewertung berechnet, hat selbst keine Steuerungswirkung |
| `luftentfeuchter_tank_fehler` | nur vorhanden, falls ein Tankstatus-Sensor für den Luftentfeuchter hinterlegt ist; `true`, solange dieser "an" meldet (Tank voll/Fehler) |
| `luftentfeuchter_seit`, `klimaanlage_seit`, `dusche_seit` | nur vorhanden, solange das jeweilige Gerät gerade läuft bzw. die Duscherkennung gerade anschlägt - Zeitpunkt, seit dem das ununterbrochen der Fall ist (Dashboard-Karte, Spalte "Laufzeit"). Live anhand des tatsächlichen Gerätezustands gepflegt (wie `luftentfeuchter_an`/`klimaanlage_an`), übersteht daher auch ein manuelles Ein-/Ausschalten außerhalb dieser Integration korrekt |
| `heizung_an` | nur vorhanden, falls eine Heizung konfiguriert ist UND ihre Entität aktuell im Zustandsautomaten existiert. Anders als `luftentfeuchter_an`/`klimaanlage_an` kein reines Ein/Aus, sondern `true`, sofern der aktuell am Gerät eingestellte Sollwert (live gelesen) näher am Comfort- als an Standby/Nacht liegt - erkennt daher auch, wenn der Sollwert manuell oder von einer anderen Automation geändert wurde |
| `heizung_modus` | wie `heizung_an`, aber alle drei Stufen: `"comfort"`/`"standby"`/`"night"` (bzw. `null`, falls der Sollwert noch nicht ablesbar ist) |
| `heizung_zieltemperatur` | aktuell am Heizungs-Gerät eingestellter Sollwert (live gelesen), `null` falls (noch) nicht ablesbar |
| `heizung_grund` | wie `luftentfeuchter_grund`/`klimaanlage_grund`, nur für die Heizung (z. B. "Innentemperatur unter Schwelle, Comfort", "Zeitfenster: Nacht", "pausiert: Fenster offen", "pausiert: Sommerbetrieb aktiv") |
| `heizung_seit` | wie `luftentfeuchter_seit`/`klimaanlage_seit` - Zeitpunkt, seit dem `heizung_an` ununterbrochen `true` ist |
| `schwelle_heizung` | aktuell wirksame Heizungs-Schwelle (inkl. Raum-Override/globaler Fallback) - nur vorhanden, falls eine Heizung konfiguriert ist. Ohne Wirkung, solange der Heizungs-Zeitplan aktiviert ist |
| `sommermodus_an` | nur vorhanden, falls in "- Smart Climate Optionen -" ein Sommer-/Winterbetrieb-Schalter hinterlegt ist UND diese Entität aktuell im Zustandsautomaten existiert - `true`/`false`, live vom Schalter gelesen. Identisch für jeden Raum, da es sich um eine hausweite, nicht raumspezifische Einstellung handelt |
| `hat_fenster` | nur vorhanden (mit Wert `false`), falls "Dieser Raum hat kein Fenster" aktiviert ist |
| `schliessempfehlung_deaktiviert` | nur vorhanden (mit Wert `true`), falls "Schließempfehlung deaktivieren" für diesen Raum aktiviert ist. Dient der Dashboard-Karte, damit sie die reinen Komfort-Schließgründe (Temperatur/Feuchtigkeit/CO2/Winter-Höchstdauer) live genauso unterdrückt wie die Integration selbst - Frost-/Hitzeschutz bleiben davon unberührt |
| `fensterkontakt_entity` | Entity-ID des Fensterkontakt-Sensors, nur vorhanden falls im Raum hinterlegt (nützlich für Dashboards, um den tatsächlichen Fensterzustand per `states(...)` nachzuschlagen) |
| `sprachausgabe_aktiv`, `sprachausgabe_lautsprecher` | nur vorhanden, wenn der Raum mindestens einen Lautsprecher ausgewählt hat |
| `app_aktiv`, `app_ziele` | nur vorhanden, wenn App-Benachrichtigung effektiv aktiv ist |
| `persistent_aktiv` | nur vorhanden, wenn persistente Web-Benachrichtigung effektiv aktiv ist |
| `duschen_erkannt` | nur vorhanden, wenn Duscherkennung effektiv aktiv ist; `true`, solange die Luftfeuchtigkeit schneller als die Anstiegs-Schwelle steigt (siehe "Duscherkennung" unter "Logik im Detail") |
| `integration_version` | aktuell installierte Version der Integration (aus `manifest.json`) - identisch für jeden Raum, dient nur der Dashboard-Karte zur Anzeige der Versionsnummer |

Der Standard-Entitätszustand selbst (`last_changed`) zeigt außerdem, seit
wann der aktuelle Öffnen/Schließen-Status gilt.

### Beispiel-Dashboard-Karte (Statusübersicht aller Räume)

Eine **Markdown-Karte** mit folgendem Inhalt zeigt automatisch alle Räume
mit Status, aktuellen Werten, Schwellenwerten und letzter Änderung – ganz
ohne zusätzliche Custom Cards.

**Aktuelle Karten-Version: 22** – anders als der Integrations-Code wird
diese Karte nicht automatisch aktualisiert, sondern muss nach jeder
inhaltlichen Änderung manuell neu in dein Dashboard eingefügt werden. Die
Zahl in der `card_version`-Zeile ganz am Anfang der Vorlage unten zeigt
dir in der Übersichts-Tabelle deines Dashboards ("Karte"-Spalte), welchen
Stand deine eingefügte Karte gerade hat – stimmt sie nicht mit der hier
im README dokumentierten aktuellen Version überein, ist deine Karte
veraltet und du solltest den Block unten erneut komplett einfügen.

```yaml
type: markdown
title: Lüftungsübersicht
content: >
  {% set card_version = 22 %}
  {% set grund_text = {'temp': 'Temperatur', 'humidity': 'Luftfeuchtigkeit', 'co2': 'CO2', 'frost': 'Frostschutz', 'heat': 'Hitzeschutz', 'duration': 'Winter-Höchstdauer', 'outdoor_warmer': 'Außen wärmer', 'outdoor_wetter': 'Außen feuchter'} %}
  {% set sep_line = '━━━━━━━━━━━━━━━━━━━━' %}
  {% set ns = namespace(green=0, orange=0, red=0, entries=[], rooms='', version=none, summer_mode=none) %}
  {% for s in states.binary_sensor | selectattr('attributes.raum', 'defined') | sort(attribute='attributes.raum') %}
  {% set a = s.attributes %}
  {% set no_window = a.hat_fenster is defined and a.hat_fenster == false %}
  {% set no_close_rec = a.schliessempfehlung_deaktiviert is defined and a.schliessempfehlung_deaktiviert %}
  {% set grund_code = a.letzter_grund if a.letzter_grund is defined else '' %}
  {% set temp_needs_open = a.innentemperatur is not none and a.innentemperatur >= a.schwelle_temperatur_oeffnen %}
  {% set temp_needs_close = a.innentemperatur is not none and a.innentemperatur <= a.schwelle_temperatur_schliessen %}
  {% set hum_needs_open = a.luftfeuchtigkeit is defined and a.luftfeuchtigkeit is not none and a.luftfeuchtigkeit >= a.schwelle_feuchtigkeit_oeffnen %}
  {% set hum_needs_close = a.luftfeuchtigkeit is defined and a.luftfeuchtigkeit is not none and a.luftfeuchtigkeit <= a.schwelle_feuchtigkeit_schliessen %}
  {% set co2_needs_open = a.co2 is defined and a.co2 is not none and a.co2 >= a.schwelle_co2_oeffnen %}
  {% set co2_needs_close = a.co2 is defined and a.co2 is not none and a.co2 <= a.schwelle_co2_schliessen %}
  {% set frost_live = a.aussentemperatur is defined and a.aussentemperatur is not none and a.schwelle_frostschutz is defined and a.aussentemperatur <= a.schwelle_frostschutz %}
  {% set heat_live = a.aussentemperatur is defined and a.aussentemperatur is not none and a.schwelle_hitzeschutz is defined and a.aussentemperatur >= a.schwelle_hitzeschutz %}
  {% set close_fallback = grund_code if grund_code in ['duration', 'outdoor_warmer', 'outdoor_wetter'] else '' %}
  {% set live_grund_open = 'temp' if temp_needs_open else ('humidity' if hum_needs_open else ('co2' if co2_needs_open else '')) %}
  {% set comfort_close = 'humidity' if hum_needs_close else ('co2' if co2_needs_close else ('temp' if temp_needs_close else close_fallback)) %}
  {% set live_grund_close = 'frost' if frost_live else ('heat' if heat_live else ('' if no_close_rec else comfort_close)) %}
  {% set highlight_code = live_grund_open if s.state == 'on' else live_grund_close %}
  {% set has_live_reason = highlight_code != '' %}
  {% set window_entity = a.fensterkontakt_entity if a.fensterkontakt_entity is defined else '' %}
  {% set window_state_text = '–' %}
  {% set window_changed_time = '–' %}
  {% set co2_close_exception = s.state == 'off' and highlight_code == 'co2' %}
  {% set comfort_close_resolved_exception = s.state == 'off' and highlight_code in ['humidity', 'temp', 'outdoor_warmer', 'outdoor_wetter'] %}
  {% set no_window_resolved = no_window and comfort_close_resolved_exception %}
  {% set match_icon = '🟢 ' if (not has_live_reason or co2_close_exception or no_window_resolved) else ('🟠 ' if no_window else '🔴 ') %}
  {% set highlight_ok = false %}
  {% if window_entity %}
  {% set w = states(window_entity) %}
  {% set window_state_text = 'geöffnet' if w == 'on' else ('geschlossen' if w == 'off' else 'unbekannt') %}
  {% if w in ['on', 'off'] %}
  {% set window_changed_time = as_local(states[window_entity].last_changed).strftime('%d.%m. %H:%M') %}
  {% endif %}
  {% if not no_window and has_live_reason and not co2_close_exception and w in ['on', 'off'] %}
  {% set is_match = (s.state == 'on') == (w == 'on') %}
  {% set match_icon = ('🟢 ' if comfort_close_resolved_exception else '🟠 ') if is_match else '🔴 ' %}
  {% set highlight_ok = is_match %}
  {% endif %}
  {% endif %}
  {% if ns.version is none and a.integration_version is defined %}
  {% set ns.version = a.integration_version %}
  {% endif %}
  {% if ns.summer_mode is none and a.sommermodus_an is defined %}
  {% set ns.summer_mode = a.sommermodus_an %}
  {% endif %}
  {% if match_icon == '🟢 ' %}
  {% set ns.green = ns.green + 1 %}
  {% elif match_icon == '🟠 ' %}
  {% set ns.orange = ns.orange + 1 %}
  {% elif match_icon == '🔴 ' %}
  {% set ns.red = ns.red + 1 %}
  {% endif %}
  {% set highlight_open = '<font color="green"><strong>' if (co2_close_exception or (comfort_close_resolved_exception and highlight_ok) or no_window_resolved) else ('<font color="orange"><strong>' if (no_window or highlight_ok) else '<font color="red"><strong>') %}
  {% set status_icon = ('Öffnen' if s.state == 'on' else 'Schließen') if has_live_reason else '–' %}
  {% set changed_time = (as_local(s.last_changed).strftime('%d.%m. %H:%M')) if has_live_reason else '–' %}
  {% set temp_val = (a.innentemperatur | round(1) | string ~ ' °C') if a.innentemperatur is not none else '–' %}
  {% set temp_val = (highlight_open ~ temp_val ~ '</strong></font>') if highlight_code == 'temp' else temp_val %}
  {% set outdoor_temp_val = (a.aussentemperatur | round(1) | string ~ ' °C') if (a.aussentemperatur is defined and a.aussentemperatur is not none) else '–' %}
  {% set outdoor_temp_val = (highlight_open ~ outdoor_temp_val ~ '</strong></font>') if highlight_code in ['frost', 'heat', 'outdoor_warmer'] else outdoor_temp_val %}
  {% set outdoor_hum_val = (a.aussen_luftfeuchtigkeit | round(0) | string) if (a.aussen_luftfeuchtigkeit is defined and a.aussen_luftfeuchtigkeit is not none) else '–' %}
  {% set hum_row = '' %}
  {% if a.luftfeuchtigkeit is defined %}
  {% set hum_val = (a.luftfeuchtigkeit | round(0) | string ~ ' %') if a.luftfeuchtigkeit is not none else '–' %}
  {% set hum_val = (highlight_open ~ hum_val ~ '</strong></font>') if highlight_code == 'humidity' else hum_val %}
  {% set hum_row = '\n| Luftfeuchtigkeit | ' ~ hum_val ~ ' | ' ~ outdoor_hum_val ~ ' % | > ' ~ (a.schwelle_feuchtigkeit_oeffnen | round(0) | int | string) ~ ' % | < ' ~ (a.schwelle_feuchtigkeit_schliessen | round(0) | int | string) ~ ' % |' %}
  {% endif %}
  {% set co2_row = '' %}
  {% if a.co2 is defined %}
  {% set co2_val = (a.co2 | round(0) | string ~ ' ppm') if a.co2 is not none else '–' %}
  {% set co2_val = (highlight_open ~ co2_val ~ '</strong></font>') if highlight_code == 'co2' else co2_val %}
  {% set co2_row = '\n| CO2 | ' ~ co2_val ~ ' | – | > ' ~ (a.schwelle_co2_oeffnen | round(0) | int | string) ~ ' ppm | < ' ~ (a.schwelle_co2_schliessen | round(0) | int | string) ~ ' ppm |' %}
  {% endif %}
  {% set abs_row = '' %}
  {% if a.luftfeuchtigkeit is defined %}
  {% set abs_in = (a.absolute_luftfeuchtigkeit | string ~ ' g/m³') if (a.absolute_luftfeuchtigkeit is defined and a.absolute_luftfeuchtigkeit is not none) else '–' %}
  {% set abs_out = (a.aussen_absolute_luftfeuchtigkeit | string ~ ' g/m³') if (a.aussen_absolute_luftfeuchtigkeit is defined and a.aussen_absolute_luftfeuchtigkeit is not none) else '–' %}
  {% set abs_out = (highlight_open ~ abs_out ~ '</strong></font>') if highlight_code == 'outdoor_wetter' else abs_out %}
  {% set abs_row = '\n| Abs. Luftfeuchtigkeit | ' ~ abs_in ~ ' | ' ~ abs_out ~ ' | – | – |' %}
  {% endif %}
  {% set device_rows = '' %}
  {% if a.luftentfeuchter_an is defined %}
  {% set dehum_name = ('🔴' if a.luftentfeuchter_an else '⚫') ~ '&nbsp;Luftentfeuchter' %}
  {% set dehum_name = (dehum_name ~ '<br>' ~ (('🔴' if a.luftentfeuchter_tank_fehler else '🟢') ~ '&nbsp;Wassertank')) if a.luftentfeuchter_tank_fehler is defined else dehum_name %}
  {% set dehum_laufzeit = '–' %}
  {% if a.luftentfeuchter_an and a.luftentfeuchter_seit is defined %}
  {% set dehum_minutes = ((now() - as_datetime(a.luftentfeuchter_seit)).total_seconds() / 60) | int %}
  {% set dehum_laufzeit = (dehum_minutes ~ ' Min') if dehum_minutes < 60 else ((dehum_minutes // 60) ~ 'h ' ~ (dehum_minutes % 60) ~ ' Min') %}
  {% endif %}
  {% set dehum_grund = a.luftentfeuchter_grund if a.luftentfeuchter_grund is defined else '–' %}
  {% set device_rows = device_rows ~ '\n| ' ~ dehum_name ~ ' | ' ~ dehum_laufzeit ~ ' | ' ~ dehum_grund ~ ' |' %}
  {% endif %}
  {% if a.klimaanlage_an is defined %}
  {% set ac_name = ('🔴' if a.klimaanlage_an else '⚫') ~ '&nbsp;Klimaanlage' %}
  {% set ac_laufzeit = '–' %}
  {% if a.klimaanlage_an and a.klimaanlage_seit is defined %}
  {% set ac_minutes = ((now() - as_datetime(a.klimaanlage_seit)).total_seconds() / 60) | int %}
  {% set ac_laufzeit = (ac_minutes ~ ' Min') if ac_minutes < 60 else ((ac_minutes // 60) ~ 'h ' ~ (ac_minutes % 60) ~ ' Min') %}
  {% endif %}
  {% set ac_grund = a.klimaanlage_grund if a.klimaanlage_grund is defined else '–' %}
  {% set device_rows = device_rows ~ '\n| ' ~ ac_name ~ ' | ' ~ ac_laufzeit ~ ' | ' ~ ac_grund ~ ' |' %}
  {% endif %}
  {% if a.heizung_an is defined %}
  {% set heiz_name = ('🔴' if a.heizung_an else '⚫') ~ '&nbsp;Heizung' %}
  {% set heiz_laufzeit = '–' %}
  {% if a.heizung_an and a.heizung_seit is defined %}
  {% set heiz_minutes = ((now() - as_datetime(a.heizung_seit)).total_seconds() / 60) | int %}
  {% set heiz_laufzeit = (heiz_minutes ~ ' Min') if heiz_minutes < 60 else ((heiz_minutes // 60) ~ 'h ' ~ (heiz_minutes % 60) ~ ' Min') %}
  {% endif %}
  {% set heiz_grund = a.heizung_grund if a.heizung_grund is defined else '–' %}
  {% set heiz_grund = (heiz_grund ~ ' (' ~ (a.heizung_zieltemperatur | round(1) | string) ~ ' °C)') if (a.heizung_zieltemperatur is defined and a.heizung_zieltemperatur is not none) else heiz_grund %}
  {% set device_rows = device_rows ~ '\n| ' ~ heiz_name ~ ' | ' ~ heiz_laufzeit ~ ' | ' ~ heiz_grund ~ ' |' %}
  {% endif %}
  {% if a.duschen_erkannt is defined %}
  {% set dusche_name = ('🟢' if a.duschen_erkannt else '⚫') ~ '&nbsp;Dusche' %}
  {% set dusche_laufzeit = '–' %}
  {% if a.duschen_erkannt and a.dusche_seit is defined %}
  {% set dusche_minutes = ((now() - as_datetime(a.dusche_seit)).total_seconds() / 60) | int %}
  {% set dusche_laufzeit = (dusche_minutes ~ ' Min') if dusche_minutes < 60 else ((dusche_minutes // 60) ~ 'h ' ~ (dusche_minutes % 60) ~ ' Min') %}
  {% endif %}
  {% set dusche_grund = 'Luftfeuchtigkeit steigt schnell' if a.duschen_erkannt else '–' %}
  {% set device_rows = device_rows ~ '\n| ' ~ dusche_name ~ ' | ' ~ dusche_laufzeit ~ ' | ' ~ dusche_grund ~ ' |' %}
  {% endif %}
  {% set device_table = ('| Gerät | Laufzeit | Grund |\n|---|:---:|---|' ~ device_rows) if device_rows else '' %}
  {% set grund_label = grund_text.get(highlight_code, highlight_code) if highlight_code else '–' %}
  {% set header = '### ' ~ match_icon ~ a.raum %}
  {% set empfehlung_text = (highlight_open ~ status_icon ~ '</strong></font>') if has_live_reason else status_icon %}
  {% set uhrzeit_val = changed_time %}
  {% set empf_table = '' %}
  {% if not no_window %}
  {% set empf_table = '| Fenster | Empfehlung | Auslöser | Uhrzeit |\n|---|---|---|---|\n| ' ~ window_state_text ~ ' | – | – | ' ~ window_changed_time ~ ' |\n| – | ' ~ empfehlung_text ~ ' | ' ~ grund_label ~ ' | ' ~ uhrzeit_val ~ ' |' %}
  {% endif %}
  {% set values_table = '| Messwert | Innen | Außen | Öffnen | Schließen |\n|---|---|---|---|---|\n| Temperatur | ' ~ temp_val ~ ' | ' ~ outdoor_temp_val ~ ' | > ' ~ (a.schwelle_temperatur_oeffnen | string) ~ ' °C | < ' ~ (a.schwelle_temperatur_schliessen | string) ~ ' °C |' ~ hum_row ~ abs_row ~ co2_row %}
  {% set n1 = 'Sprachausgabe' %}
  {% set n1_status = '🟢' if a.sprachausgabe_aktiv is defined else '⚫' %}
  {% set n1_ziel = (a.sprachausgabe_lautsprecher | join(', ')) if a.sprachausgabe_lautsprecher is defined else '–' %}
  {% set n2 = 'App-Benachrichtigung' %}
  {% set n2_status = '🟢' if a.app_aktiv is defined else '⚫' %}
  {% set n2_ziel = (a.app_ziele | join(', ')) if a.app_ziele is defined else '–' %}
  {% set n3 = 'Persistente Benachrichtigung' %}
  {% set n3_status = '🟢' if a.persistent_aktiv is defined else '⚫' %}
  {% set n3_ziel = '–' %}
  {% set notify_table = '<details>\n<summary><strong>Benachrichtigungen</strong></summary>\n\n| Benachrichtigung | Status | Ziel(e) |\n|---|:---:|---|\n| ' ~ n1 ~ ' | ' ~ n1_status ~ ' | ' ~ n1_ziel ~ ' |\n| ' ~ n2 ~ ' | ' ~ n2_status ~ ' | ' ~ n2_ziel ~ ' |\n| ' ~ n3 ~ ' | ' ~ n3_status ~ ' | ' ~ n3_ziel ~ ' |\n\n</details>' %}
  {% set spacer = '\n\n<small><small><small>&nbsp;</small></small></small>\n\n' %}
  {% set body = empf_table %}
  {% set body = (body ~ spacer ~ values_table) if body else values_table %}
  {% set body = (body ~ spacer ~ device_table) if device_table else body %}
  {% set body = body ~ spacer ~ notify_table %}
  {% set color_rank = '0' if match_icon == '🔴 ' else ('1' if match_icon == '🟠 ' else '2') %}
  {% set sort_key = color_rank ~ a.raum %}
  {% set ns.entries = ns.entries + [{'key': sort_key, 'block': header ~ '\n\n' ~ body}] %}
  {% endfor %}
  {% for entry in ns.entries | sort(attribute='key') %}
  {% set sep_before = '\n\n' ~ sep_line ~ '\n\n' if not loop.first else '' %}
  {% set ns.rooms = ns.rooms ~ sep_before ~ entry.block %}
  {% endfor %}
  {% set summer_header = ' Sommer/Winter |' if ns.summer_mode is not none else '' %}
  {% set summer_sep = ':---:|' if ns.summer_mode is not none else '' %}
  {% set summer_cell = (' ☀️ Sommer |' if ns.summer_mode else ' ❄️ Winter |') if ns.summer_mode is not none else '' %}
  {% set version_header = (' Integration |' if ns.version is not none else '') ~ ' Karte |' %}
  {% set version_sep = (':---:|' if ns.version is not none else '') ~ ':---:|' %}
  {% set version_cell = (' ' ~ ns.version ~ ' |' if ns.version is not none else '') ~ ' ' ~ card_version ~ ' |' %}
  {% set overview = '| 🟢 | 🟠 | 🔴 |' ~ summer_header ~ version_header ~ '\n|:---:|:---:|:---:|' ~ summer_sep ~ version_sep ~ '\n| ' ~ ns.green ~ ' | ' ~ ns.orange ~ ' | ' ~ ns.red ~ ' |' ~ summer_cell ~ version_cell %}
  {{ overview ~ '\n\n' ~ sep_line ~ '\n\n' ~ ns.rooms }}
```

Einfügen über **Dashboard bearbeiten → Karte hinzufügen → Markdown** (im
YAML-Modus den obigen Inhalt einfügen). Die Karte findet Räume automatisch
über das `raum`-Attribut - neue Räume erscheinen ohne weitere Anpassung.

**Wichtige technische Erkenntnis:** Home Assistants Markdown-Karte
filtert offenbar das `style`-Attribut aus eingebettetem HTML heraus (ein
üblicher Sicherheitsmechanismus - Skripte oder aufwändiges CSS über
eingebettetes HTML einzuschleusen soll verhindert werden). Deshalb wurden
`<div style="height: ...">` und `<hr style="...">` unwirksam. Diese
Version verzichtet komplett auf `style`-Attribute:

- **Abstand zwischen Tabellen**: `<small><small><small>&nbsp;</small></small></small>` -
  ein eigenständiger Absatz, durch dreifaches `<small>` möglichst kompakt
  gehalten, ohne jedes Style-Attribut
- **Trennlinie zwischen Räumen**: schlichtes `<hr>` (Standard-Tag ohne
  Style-Attribut) - ein Versuch, die Linie über Text-Zeichen dicker/dunkler
  zu gestalten, führte je nach Bildschirmbreite zu Zeilenumbrüchen; das
  Standard-`<hr>` ist dafür zuverlässig über die volle Kartenbreite
- **Hervorhebung des ausschlaggebenden Werts**: `<font color="red"><strong>`
  bzw. `<font color="green"><strong>` statt `<span style="...">` - das
  `style`-Attribut wird gefiltert (siehe oben), das ältere, rein
  präsentative `color`-Attribut auf `<font>` sowie das attributlose
  `<strong>` aber nicht. Zuvor kam `<mark>` (gelber Hintergrund) zum
  Einsatz; auf Nutzerwunsch durch fette, farbige Schrift ersetzt, da die
  gelbe Markierung als zu unauffällig wahrgenommen wurde. Hervorgehoben
  wird jeweils die Zelle mit der Maßeinheit zusammen (z. B. `34.2 °C`,
  nicht nur `34.2`) - bei jedem aktiven Auslöser grundsätzlich **rot**,
  mit Ausnahmen für Schließen-Gründe: Ein Schließen-Auslöser bedeutet per
  Definition, dass der jeweilige Wert seine Schließen-Schwelle bereits
  erreicht hat - das zugrunde liegende Problem (zu warm/zu feucht/zu viel
  CO2) ist damit bereits gelöst, im Unterschied zu einem Öffnen-Auslöser,
  bei dem der Wert noch außerhalb der Norm liegt und auf Normalisierung
  "wartet". Deshalb: **grün**, wenn "CO2" der aktuelle Schließen-Auslöser
  ist - ein niedriger CO2-Wert ist kein Sicherheitsrisiko (anders als
  Frost-/Hitzeschutz), das Schließen dient nur der Ordnung, nicht der
  Sicherheit (siehe "Logik im Detail" unten), es besteht also kein
  Handlungsbedarf, unabhängig vom tatsächlichen Fensterzustand; **grün**
  auch, wenn Temperatur, Luftfeuchtigkeit oder "Außen wärmer"/
  "Außen feuchter" der aktuelle Schließen-Auslöser ist UND das Fenster
  bereits geschlossen ist (die Person hat also bereits reagiert) - anders
  als bei CO2 kann Weiterlüften hier aber tatsächlich schaden (zu kalt/zu
  feucht werden, oder bei "Außen wärmer"/"Außen feuchter" die Lage sogar
  verschlimmern), daher gilt Grün hier NUR bei bereits passendem Fenster,
  nicht unabhängig vom Fensterzustand wie bei CO2. Bleibt das Fenster bei
  diesen vier Gründen dagegen noch offen (Fenster-Mismatch), zeigt die
  Karte weiterhin normal **rot** - ein Handeln ist dann sehr wohl nötig;
  **orange**, wenn das Fenster bereits genau so steht, wie es die aktuelle
  Empfehlung vorsieht (die Person hat also bereits reagiert), die
  zugrunde liegenden Werte sich aber noch nicht normalisiert haben - das
  betrifft ausschließlich Öffnen-Auslöser (Temperatur/Luftfeuchtigkeit/
  CO2 noch über ihrer Öffnen-Schwelle): hier ist ebenfalls kein weiteres
  Handeln nötig, die Werte liegen aber (anders als beim Totzone-Fall)
  tatsächlich noch außerhalb der Norm, daher nicht grün, sondern nur
  orange. Bei Räumen ohne Fenster ("Dieser Raum hat kein Fenster"
  aktiviert) gilt ebenfalls **orange**, unabhängig vom Auslöser, da sich
  der Wert dort gar nicht durch Lüften beeinflussen lässt (höchstens
  Luftentfeuchter/Klimaanlage reagieren automatisch). Rot bleibt damit auf
  den Fall beschränkt, in dem tatsächlich noch etwas zu tun ist: das
  Fenster steht (noch) nicht so, wie die Empfehlung es vorsieht. Da zu
  jedem Zeitpunkt ohnehin immer nur **ein** Auslöser als "der" Grund gilt
  (siehe Prioritätsreihenfolge unten - Frostschutz vor Hitzeschutz vor
  Luftfeuchtigkeit vor CO2 vor Temperatur), stellt sich die Frage "mehrere
  Auslöser gleichzeitig" für die Farbe nicht: Rot ist der Normalfall bei
  einem echten Fenster-Mismatch, die Grün-Ausnahmen greifen nur, wenn
  dieser eine, gewinnende Auslöser tatsächlich ein Schließen-Grund ist -
  überwiegt stattdessen ein Öffnen-Grund, wird dieser zum gewinnenden
  Auslöser, und der Raum zeigt ganz normal Rot bzw. Orange dafür, nicht
  Grün.

  Auslöser und Hervorhebung werden dabei **live** aus den aktuell
  angezeigten Werten und Schwellen berechnet, nicht aus dem historischen
  `letzter_grund`-Attribut: Bei "Öffnen" wird geprüft, welche der drei
  Größen (Innentemperatur, Luftfeuchtigkeit, CO2, in dieser Reihenfolge)
  aktuell ihre Öffnen-Schwelle erreicht; bei "Schließen" wird zusätzlich
  zuerst Frost- und Hitzeschutz live geprüft (aktuelle Außentemperatur
  gegen `schwelle_frostschutz`/`schwelle_hitzeschutz`), dann symmetrisch
  Luftfeuchtigkeit, CO2, Temperatur gegen ihre Schließen-Schwelle -
  identisch zur tatsächlichen Prioritätsreihenfolge in `binary_sensor.py`
  (Frostschutz hat immer Vorrang). Das funktioniert unabhängig davon, ob
  die Empfehlung schon einmal einen echten Zustandswechsel hatte, und
  beschreibt immer den **aktuellen** Zustand, nicht nur die Historie -
  wurde z. B. wegen eines längst vorbeigezogenen Kälte-Einbruchs
  geschlossen und ist die Außentemperatur inzwischen wieder deutlich über
  der Frostschutz-Grenze, zeigt der Auslöser das nicht mehr an.
  `letzter_grund` dient nur noch als **Rückfallwert** für die drei Fälle,
  die sich nicht live aus den angezeigten Werten nachrechnen lassen:
  Sommer-Fall, "Außenluft inzwischen feuchter" und Winter-Höchstdauer
  (`outdoor_warmer`/`outdoor_wetter`/`duration` - fehlende Toleranz-Marge
  bzw. bisherige Öffnungsdauer im Vergleich zur Karte).
  Trifft weder ein Live-Check noch dieser Rückfallwert zu ("Totzone": z. B.
  eine Innentemperatur, die zwischen Schließen-ab- und Öffnen-ab-Schwelle
  liegt, ohne dass eine andere Größe oder Frost-/Hitzeschutz aktuell
  zieht), zeigt die Karte konsequent überall neutral "–" statt einer
  veralteten Empfehlung: Auslöser, Empfehlung **und** Uhrzeit werden dann
  alle "–", das Icon am Raumnamen wird 🟢 (aktuell liegt kein Grund zum
  Eingreifen vor, unabhängig vom Fensterzustand). Der zugrunde liegende
  `binary_sensor` behält seinen letzten
  Zustand technisch unverändert bei (er ändert sich erst bei einem echten
  neuen Auslöser) - die Karte soll aber nicht länger eine aktive
  Empfehlung suggerieren, für die es aktuell keinen nachvollziehbaren
  Grund gibt. Innen-/Außenwerte bleiben in diesem Fall unhervorgehoben, da
  es keinen ausschlaggebenden Grund gibt.

Falls einzelne dieser drei Elemente bei dir immer noch nicht wie erwartet
aussehen, sag bitte genau, **welches** der drei betroffen ist - das hilft,
die Ursache weiter einzugrenzen (z. B. ob wirklich nur `style`-Attribute
gefiltert werden oder noch mehr).

**Reihenfolge:** Zu Beginn der Karte (einmalig, vor der Raumliste) eine
**Übersichts-Tabelle** (🟢/🟠/🔴 als Spaltenköpfe, darunter zentriert die
Anzahl der Räume mit dem jeweiligen Icon-Status - Zählung identisch zum
Icon am jeweiligen Raumnamen weiter unten - gefolgt von - falls vorhanden -
einer Spalte "Integration" mit der aktuell installierten Versionsnummer **der
Integration**, liest `integration_version` vom ersten Raum, für den das
Attribut vorhanden ist, und zuletzt einer Spalte "Karte" mit der
Versionsnummer **dieser Karten-Vorlage selbst** (`card_version`, eine
reine Konstante ganz am Anfang der Vorlage, siehe unten); nebeneinander
platzierte, aber getrennte Tabellen sind in Home Assistants Markdown-
Karte ohne das gefilterte `style`-Attribut nicht zuverlässig umsetzbar,
siehe "Hervorhebung des ausschlaggebenden Werts" oben - daher eine
gemeinsame Tabelle). Die Raumliste selbst ist nach demselben Icon-Status
wie am Raumnamen sortiert (identisch zur Zählung in der Übersichts-
Tabelle): zuerst alle 🔴-Räume (echter Fenster-Mismatch, größter
Handlungsbedarf), danach alle 🟠-Räume (Fenster steht schon korrekt, aber
Werte noch außerhalb der Norm, oder Raum ohne Fenster), zuletzt alle
🟢-Räume (bereits gelöster Schließen-Grund oder gar kein Auslöser) -
innerhalb jeder der drei
Gruppen jeweils alphabetisch. Räume mit dem größten Handlungsbedarf
stehen so immer ganz oben, unabhängig vom Raumnamen. Pro Raum dann: Raumname →
**Empfehlungs-Tabelle** (Fenster/Empfehlung/
Auslöser/Uhrzeit - nur für Räume mit Fenster, zwei Zeilen: die erste
zeigt ausschließlich den Fensterzustand mit dem Zeitpunkt seiner letzten
tatsächlichen Änderung (`last_changed` des Fensterkontakt-Sensors selbst,
"–" ohne konfigurierten Fensterkontakt), die zweite ausschließlich
Empfehlung/Auslöser mit dem Zeitpunkt der letzten Empfehlungsänderung -
dadurch auf einen Blick erkennbar, ob die Fensteraktion vor oder nach dem
Empfehlungswechsel lag, z. B. um zu prüfen, ob eine fehlende
Benachrichtigung dadurch erklärbar ist (Fenster stand zum Zeitpunkt des
Wechsels bereits passend, siehe "Logik im Detail"). Auslöser wird live aus
den aktuellen Werten/Schwellen berechnet (siehe "Hervorhebung des
ausschlaggebenden Werts" oben). Solange dabei ein Auslöser vorliegt, zeigt
Empfehlung "Öffnen"/"Schließen" entsprechend dem aktuellen Zustand und
Uhrzeit (zweite Zeile) den Zeitpunkt der letzten tatsächlichen
Zustandsänderung; liegt aktuell **kein** Auslöser vor ("Totzone", siehe
oben), zeigen Empfehlung
und Uhrzeit ebenfalls "–" statt einer sonst nicht mehr begründbaren
Empfehlung. Das Icon am Raumnamen richtet sich danach, ob aktuell ein
Auslöser vorliegt und, falls ja, ob das Fenster bereits entsprechend
steht (🔴 bei echtem Fenster-Mismatch, 🟠 wenn das Fenster schon korrekt
steht, aber die Werte noch außerhalb der Norm liegen, 🟢 bei einem
bereits gelösten Schließen-Grund oder ganz ohne Auslöser - siehe
"Hervorhebung des ausschlaggebenden Werts" oben) →
**Werte-Tabelle** (mit Spaltenüberschrift "Messwert", inkl.
CO2-Zeile falls ein CO2-Sensor hinterlegt ist) → **Geräte-Tabelle**
(Gerät/Laufzeit/Grund - Zeilen für Luftentfeuchter, Klimaanlage, Heizung
und Dusche, jeweils nur falls konfiguriert bzw. für den Raum aktiviert; das
Status-Icon steht direkt vor dem Gerätenamen in der ersten Spalte; ist
ein Tankstatus-Sensor für den Luftentfeuchter hinterlegt, zeigt dessen
Zeile in der "Gerät"-Spalte per Zeilenumbruch (`<br>`) zusätzlich
"Wassertank" mit eigenem Icon (🔴 voll/Fehler, 🟢 ok) direkt unter dem
Gerätenamen; "Laufzeit" zeigt, seit wann das jeweilige Gerät ununter-
brochen läuft bzw. die Duscherkennung anschlägt (`Xh YMin`/`XMin`,
live aus `luftentfeuchter_seit`/`klimaanlage_seit`/`heizung_seit`/
`dusche_seit` berechnet), sonst "–"; "Grund" zeigt bei Luftentfeuchter/
Klimaanlage/Heizung eine rein informative, live bei jeder Neubewertung
berechnete Kurzbeschreibung, warum das Gerät gerade an/aus (bzw. bei der
Heizung: Comfort/Standby/Nacht bzw. "Zeitfenster: …" bei aktiviertem
Heizungs-Zeitplan) ist bzw. pausiert (u. a. auch "pausiert: Sommerbetrieb
aktiv"), ohne selbst Einfluss auf die Steuerung zu haben - siehe
`binary_sensor.py`; bei der Heizung ergänzt um den aktuellen Sollwert in
Klammern (z. B. "Innentemperatur unter Schwelle, Comfort (21.0 °C)" oder
"Zeitfenster: Nacht (16.0 °C)"); bei Dusche entsprechend, ob und warum die
Duscherkennung aktuell anschlägt) → **Benachrichtigungen**
(ein-/ausklappbare Tabelle, standardmäßig eingeklappt, jetzt als letzter
Abschnitt pro Raum).

Icons dienen ausschließlich zur **Status-Signalisierung**: 🟢/🟠/🔴 am
Raumnamen zeigen, ob aktuell eine Empfehlung mit Handlungsbedarf vorliegt
- und, falls ja, ob dafür noch tatsächlich etwas zu tun ist. 🔴 nur, wenn
das Fenster (noch) nicht so steht, wie es die aktuelle Empfehlung
vorsieht - hier kann direkt eingegriffen werden. Steht das Fenster
bereits korrekt, unterscheidet sich die Farbe danach, ob der Auslöser ein
Öffnen- oder ein Schließen-Grund ist: Bei einem **Öffnen**-Grund (die
Person hat also schon reagiert, die zugrunde liegenden Werte haben sich
nur noch nicht normalisiert) zeigt das Icon 🟠 - kein Handlungsbedarf
mehr, aber auch noch nicht "alles gut". Bei einem **Schließen**-Grund
zeigt das Icon dagegen 🟢: Ein Schließen-Auslöser bedeutet per Definition,
dass der jeweilige Wert seine Schließen-Schwelle bereits erreicht hat -
das Problem ist also bereits gelöst, nicht nur "wartend". Für CO2 gilt
das sogar unabhängig vom Fensterzustand (ein niedriger CO2-Wert ist kein
Sicherheitsrisiko, sondern zeigt nur "Luftqualität wieder gut genug" -
Weiterlüften schadet nie); für Temperatur, Luftfeuchtigkeit sowie
"Außen wärmer"/"Außen feuchter" gilt 🟢 dagegen nur, wenn das Fenster
tatsächlich schon passt - bliebe es trotz erreichter Schließen-Schwelle
offen, könnte Weiterlüften hier tatsächlich schaden, daher bleibt es in
diesem Fall bei 🔴. 🟢 gilt außerdem, wenn aktuell gar kein Auslöser
vorliegt ("Totzone", siehe oben) - hier gibt es nichts, das ein
Eingreifen nahelegt, und auch keine außerhalb der Norm liegenden Werte.
Da zu jedem Zeitpunkt ohnehin immer nur ein Auslöser als "der" Grund gilt
(Prioritätsreihenfolge unten), zeigt der Raum bei einem gleichzeitig
aktiven, aber nicht gewinnenden Schließen-Grund ganz normal 🔴/🟠 mit dem
tatsächlich gewinnenden Grund als Auslöser, nicht 🟢.
Bei Räumen ohne Fenster ("Dieser Raum hat kein Fenster" aktiviert) gibt
es ohnehin keinen Fenster-Zustand, über den sich lüften ließe, daher
richtet sich das Icon dort danach, ob aktuell ein Auslöser vorliegt: 🟢,
solange alle Werte im jeweils passenden Bereich liegen. Liegt ein
Öffnen-Auslöser vor, zeigt das Icon 🟠 (identisch zur orangen
Hervorhebung des betroffenen Werts, siehe oben - Handlungsbedarf
besteht, aber nicht über das Fenster, sondern höchstens über
Luftentfeuchter/Klimaanlage). Liegt dagegen ein Schließen-Auslöser vor
(Temperatur, Luftfeuchtigkeit, "Außen wärmer"/"Außen feuchter"), gilt
dieselbe "bereits gelöst, nicht nur wartend"-Logik wie bei Räumen mit
Fenster (siehe oben) - das Icon zeigt 🟢, auch ohne Fenster zum
Abgleichen, unabhängig davon, ob für den Raum zusätzlich ein
Luftentfeuchter/eine Klimaanlage konfiguriert ist. Da zu jedem Zeitpunkt nur ein Auslöser als
"der" Grund gilt (siehe Prioritätsreihenfolge unten), gibt es nie einen
Konflikt zwischen 🟠 und 🔴 für ein und denselben Raum. Bei den
Benachrichtigungsmethoden steht 🟢 für an, ⚫ für aus. Beim Geräte-Status
(Luftentfeuchter/Klimaanlage) gilt dagegen 🔴 für an (läuft gerade), ⚫ für
aus - hier soll ein laufendes Gerät auffallen, nicht als "alles gut"
grün erscheinen. Der Luftentfeuchter-Status ergänzt zusätzlich ein
eigenes Status-Icon in Klammern für den optionalen Tankstatus-Sensor: 🔴,
solange dieser "an" meldet (Tank voll/Fehler), sonst 🟢 - unabhängig vom
🔴/⚫-Icon des Luftentfeuchters selbst. Die Empfehlungs-Tabelle selbst
kommt bewusst ohne Icons aus (nur Text: "Öffnen"/"Schließen" für die
Empfehlung bzw. "geöffnet"/"geschlossen" für den tatsächlichen
Fensterzustand - klein geschrieben, da kein eigenständiger Satzanfang,
und als Partizip sprachlich zu "das Fenster ist geöffnet/geschlossen"
passend). Der Empfehlungstext ("Öffnen"/"Schließen") wird
zusätzlich fett und in derselben Farbe wie der ausschlaggebende Wert
dargestellt, solange dafür ein Auslöser vorliegt - **rot**, wenn das
Fenster noch nicht so steht wie die Empfehlung es vorsieht (echter
Handlungsbedarf); **orange**, wenn das Fenster bereits korrekt steht,
aber die Werte noch außerhalb der Norm liegen, oder der Raum kein
Fenster hat; **grün**, wenn der Auslöser CO2 (Schließen) ist (kein
Handlungsbedarf, siehe "Hervorhebung des ausschlaggebenden Werts" oben);
liegt kein Auslöser
vor ("Totzone"), bleibt der Text schlicht "–" ohne Hervorhebung. Die
Hervorhebung der Innen-/Außenwerte in der Werte-Tabelle folgt derselben
grün/orange/rot-Logik (siehe "Hervorhebung des ausschlaggebenden Werts"
oben).
Die Schwellenwerte
sind mit `>`/`<` versehen (öffnen **oberhalb**, schließen **unterhalb**
des jeweiligen Werts). Die Vorlage ist bewusst in viele kurze, einfache
Einzelschritte zerlegt - das macht sie robuster gegenüber Kopier-/
Einfügeproblemen. Diese Version wurde sowohl gegen eine echte
YAML-Faltung (`content: >`) als auch gegen Home Assistants sandboxed
Jinja-Umgebung getestet.

## Fehlersuche / Diagnose

Zwei Bordmittel helfen bei der Fehlersuche, ohne dass Werte oder
Log-Zeilen von Hand abgeschrieben werden müssen:

- **Diagnose herunterladen**: Bei jedem Eintrag (ein Raum oder
  "- Smart Climate Optionen -") lässt sich über das Drei-Punkte-Menü
  (⋮) → **Diagnose herunterladen** eine JSON-Datei erzeugen. Sie enthält
  die Konfiguration dieses Eintrags (personenbezogene Anwesenheits-/
  Notify-Ziel-Entitäten sind darin automatisch geschwärzt), bei einem
  Raum zusätzlich den aktuellen Entitäts-Zustand samt aller Attribute
  sowie eine Momentaufnahme (Zustand + Attribute) aller referenzierten
  Roh-Sensoren - Innentemperatur-Quelle, Luftfeuchtigkeit, CO2,
  Fensterkontakt sowie die globale Außentemperatur/-luftfeuchtigkeit.
  Damit lässt sich z. B. sofort erkennen, ob ein referenzierter Sensor
  gerade `unavailable`/`unknown` meldet. Diese Datei kann direkt
  hochgeladen/geteilt werden, z. B. um ein auffälliges Verhalten zu
  melden.
- **Debug-Protokollierung**: Über Einstellungen → Geräte & Dienste →
  beim jeweiligen Raum-Eintrag → Zahnrad-Symbol → **Debug-Protokollierung
  aktivieren** (oder global über `logger:` in der `configuration.yaml`
  für `custom_components.ha_smart_ventilation`) protokolliert die
  Integration bei jeder Neubewertung eine einzelne, strukturierte
  Log-Zeile mit allen Zwischenwerten der Entscheidungskette (Temperaturen,
  Luftfeuchtigkeit, CO2, alle Öffnen-/Schließen-/"noch benötigt"-Flags).
  Hilfreich vor allem bei Flacker-artigen Problemen (wiederholtes
  Öffnen/Schließen), bei denen ein einzelner Diagnose-Snapshot nicht
  ausreicht.

## Hinweise

- **Umstieg auf globale Benachrichtigungsziele**: Bestehende Räume, die
  bereits eigene Werte für App/Persistent gesetzt hatten, funktionieren
  unverändert weiter (ihre bisherigen Ja/Nein-Werte gelten jetzt einfach
  als expliziter Raum-Override). Neu ist nur, dass sich diese Felder jetzt
  auch komplett leer lassen lassen, um stattdessen die globale Einstellung
  zu übernehmen. Um einen bereits konfigurierten Raum auf "globale
  Einstellung nutzen" umzustellen, musst du das entsprechende Dropdown im
  Formular einmal manuell auf die leere Option zurücksetzen.
- **Automatische Migration noch älterer Räume**: Räume, die aus einer Zeit
  vor der obigen Umstellung stammen und seitdem nie neu gespeichert wurden,
  hatten intern noch eine ältere, längst nicht mehr ausgewertete
  `notify_method`-Liste anstelle von "Home Assistant Companion App"/
  "Persistente Benachrichtigung" - dadurch blieben sie trotz konfigurierter
  Benachrichtigungsziele dauerhaft stumm (weder Raum- noch globaler Wert
  vorhanden). Seit Version 0.33.2 migriert die Integration solche Räume beim
  nächsten Start automatisch einmalig auf die aktuellen Felder - kein
  manuelles Eingreifen nötig.
- **Wegfall des Sprachausgabe-Schalters**: Der frühere Ja/Nein/leer-Schalter
  "Sprachausgabe" (Raum und global) und die globale Lautsprecherliste
  wurden entfernt. Ein bereits konfigurierter Raum mit ausgewählten
  Lautsprechern ist davon nicht betroffen - Sprachausgabe war und bleibt
  aktiv, jetzt eben ausschließlich abgeleitet daraus, dass Lautsprecher
  ausgewählt sind. Hatte ein Raum dagegen Sprachausgabe nur über die
  globale Einstellung (leeres Dropdown) bezogen, ohne selbst Lautsprecher
  festzulegen, ist Sprachausgabe für ihn jetzt aus - dann müssen die
  gewünschten Lautsprecher einmalig direkt im Raum nachgetragen werden.
- Die Integration reagiert direkt auf Zustandsänderungen (kein Polling),
  daher sehr geringe Systemlast. Die angezeigten Attribute (aktuelle
  Temperatur/Luftfeuchtigkeit etc.) werden bei jeder Neubewertung aktuell
  gehalten - auch wenn sich der Empfehlungsstatus selbst dabei nicht
  ändert. **Ausnahme:** Die Außentemperatur kommt
  ausschließlich aus "- Smart Climate Optionen -" und wird beim Start jedes
  Raums direkt mitverfolgt – ändert sich aber die dort hinterlegte
  Sensor-**Auswahl** selbst (nicht nur ihr Messwert), wirkt sich das erst
  beim nächsten 5-Minuten-Tick des Raums aus. Dasselbe gilt für den
  Leistungssensor, falls dieser nur global (nicht zusätzlich im Raum)
  gesetzt ist.
- **Konservativ bei kurzzeitig nicht verfügbaren Außensensoren**: Sind
  Außentemperatur- und/oder Außen-Luftfeuchtigkeitssensor konfiguriert,
  aber gerade nicht verfügbar (z. B. während Home Assistant startet oder
  stoppt und andere Integrationen noch laden/entladen), werden die davon
  abhängigen Öffnen-Bedingungen und der Frostschutz **konservativ**
  behandelt (kein Öffnen, ggf. Frostschutz blockiert vorsorglich) - nicht
  permissiv, wie es bei komplett fehlender Konfiguration der Fall ist.
  Das verhindert Fehlalarme durch kurzzeitige Sensor-Ausfälle beim
  Neustart.
- **Neustart-sicher**: Der Empfehlungsstatus ("Lüften empfohlen: ja/nein")
  wird über Neustarts von Home Assistant hinweg wiederhergestellt
  (`RestoreEntity`). Ohne diesen Mechanismus würde jede Entität nach einem
  Neustart immer bei "nein" beginnen und bei aktuell noch zutreffenden
  Bedingungen einen scheinbaren Zustandswechsel erkennen - mit einer
  überflüssigen erneuten Benachrichtigung, obwohl sich nichts geändert hat.
  Hat sich während der Ausfallzeit tatsächlich etwas geändert (z. B. wurde
  das Fenster manuell geöffnet), wird das weiterhin korrekt erkannt und
  gemeldet.
- Für die Sprachausgabe wird der Standard-Service `tts.speak` verwendet – das
  funktioniert mit jeder `media_player`-Entität, nicht nur mit Sonos. Stelle
  sicher, dass eine TTS-Integration (z. B. Google Translate, Piper)
  eingerichtet ist.
- **Lautstärke der Ansage**: `tts.speak` selbst unterstützt keine
  Lautstärkeangabe. Die in den globalen Einstellungen konfigurierte
  Lautstärke wird deshalb vorher separat per `media_player.volume_set`
  gesetzt - die davor aktuelle Lautstärke jedes Lautsprechers wird dabei
  gemerkt und **nach der Ansage automatisch wieder gesetzt**. Da `tts.speak`
  kein plattformübergreifend zuverlässiges "Wiedergabe beendet"-Ereignis
  liefert, wird dafür die ungefähre Sprechdauer aus der Nachrichtenlänge
  geschätzt (rund 150 Wörter/Minute plus Pufferzeit) - bei sehr langen
  Ansagen oder einem ungewöhnlich langsamen TTS-Dienst kann die Lautstärke
  dadurch im Einzelfall etwas zu früh oder zu spät zurückgesetzt werden.
- **Pausieren vs. Überlagern**: Im Modus "Pausieren" wird die vorhandene
  Wiedergabe vor der Ansage pausiert, aber **nicht automatisch
  fortgesetzt** - ein zuverlässiges automatisches Fortsetzen ist
  plattformübergreifend (über alle `media_player`-Integrationen hinweg)
  nicht robust lösbar. "Überlagern" (Standard) spielt die Ansage einfach
  direkt über die laufende Wiedergabe.
- Für App-Benachrichtigungen wird `notify.send_message` auf die gewählte
  notify-Entität aufgerufen (benötigt Home Assistant 2024.9 oder neuer).
- **"Clean Notification"**: Erledigt sich eine Lüften-Empfehlung (Fenster
  wurde geöffnet/geschlossen und/oder die Werte haben sich normalisiert),
  wird eine zuvor gesendete Push-Benachrichtigung automatisch auf dem
  Gerät aufgelöst, und eine zuvor erstellte persistente Web-Benachrichtigung
  automatisch per `persistent_notification.dismiss` entfernt. Für Push
  technisch über einen festen, raumeindeutigen `tag` gelöst: eine neue
  Benachrichtigung ersetzt eine ältere auf demselben Gerät automatisch, und
  ein `clear_notification` löst sie ohne Ersatz auf. Das greift bei beiden
  Kanälen auch dann, wenn die Person das Fenster bereits selbst
  geöffnet/geschlossen hat, bevor sich die zugrunde liegenden Werte
  normalisiert haben - dafür ist kein vollständiger Zustandswechsel der
  Empfehlung nötig, es reicht, dass der konfigurierte Fensterkontakt den
  gewünschten Zustand erreicht. Das erfordert eine notify-Entität, die ein
  `data`-Feld mit `tag` unterstützt - deshalb ist die Auswahl beim
  App-Benachrichtigungsziel auf Companion-App-Entitäten eingeschränkt
  (siehe oben). Wird trotzdem eine andere notify-Entität konfiguriert
  (z. B. nachträglich über die Home-Assistant-eigene YAML-Konfiguration)
  und lehnt diese `data` per Schema ab, wird nur eine Warnung geloggt
  ("Konnte Push-Benachrichtigung an ... nicht senden"), statt die
  Neubewertung fehlschlagen zu lassen.
- Diese Integration öffnet/schließt keine motorisierten Fenster automatisch –
  sie informiert nur. Falls du motorisierte Fenster hast, kannst du den
  `binary_sensor` als Trigger in einer eigenen Automation verwenden, um
  `cover.open_cover` / `cover.close_cover` aufzurufen.

## Releases automatisch erstellen (nur für Entwicklung/Maintenance)

Zwei GitHub-Actions-Dateien im `.github`-Ordner automatisieren das
Release-Management dieses Repositories:

- **`.github/release.yml`**: Kategorisiert die Release Notes anhand von
  PR-Labels (🚀 Neue Funktionen, 🐛 Fehlerbehebungen, 📚 Dokumentation,
  🧹 Sonstiges).
- **`.github/workflows/auto-release.yml`**: Erstellt bei jeder Änderung an
  der Versionsnummer in `custom_components/ha_smart_ventilation/manifest.json`
  auf dem `main`-Branch automatisch einen passenden Git-Tag (`vX.Y.Z`) und
  ein GitHub-Release mit automatisch generierten Notes - nutzt dabei die
  Kategorisierung aus `release.yml`. Existiert der Tag bereits, passiert
  nichts (kein doppeltes Release).

Der Ablauf bei einer neuen Version ist damit: Code ändern → Version in
`manifest.json` hochzählen → auf `main` pushen. Tag und Release entstehen
automatisch, ohne manuellen Schritt auf GitHub.

**Pre-Releases (Beta-Versionen):** Enthält die Versionsnummer einen
Bindestrich nach dem semver-Schema (z. B. `0.33.0-beta.1`), markiert der
Workflow das erzeugte GitHub-Release automatisch als **Pre-Release** und
setzt es nicht als "Latest Release". HACS zeigt Pre-Releases nur Nutzern
an, die für diese Integration in HACS unter "Beta-Versionen anzeigen"
zugestimmt haben - alle anderen bleiben unverändert auf der letzten
regulären (nicht-Pre-Release-)Version. Sobald eine Beta-Version bestätigt
ist, wird sie durch eine reguläre Versionsnummer ohne Bindestrich (z. B.
`0.33.0`) abgelöst, die dann ganz normal für alle sichtbar wird.
