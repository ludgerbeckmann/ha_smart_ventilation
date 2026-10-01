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

- **on** = Lüften wird empfohlen (Fenster sollte offen sein) - Symbol
  `mdi:window-open-variant`
- **off** = Lüften kann beendet werden - Symbol `mdi:window-closed-variant`

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
Entität für Dashboards/Automationen) - Symbol `mdi:shower` bei **on**,
`mdi:shower-head` bei **off**.

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
3. **Hauptformular** ausfüllen (sechs Abschnitte in dieser Reihenfolge,
   alle standardmäßig eingeklappt):
   - **Raumname** (ganz oben, ggf. bereits durch den HA-Bereich
     vorbelegt – lässt sich hier weiterhin frei ändern)
   - **Abschnitt "Sensoren"** (Innen-Messwerte dieses Raums):
     - **Innentemperatur**: eine `climate`-, `sensor`-, `number`- oder
       `input_number`-Entität (das zugehörige "Temperatur-Attribut" steht
       direkt darunter)
     - **Temperatur-Attribut**: vorausgewählt ist `current_temperature`
       (Auswahl aus Liste oder eigener Text möglich). Wird nur ausgewertet,
       wenn die oben gewählte
       Innentemperatur-Entität tatsächlich eine `climate`-Entität ist – bei
       `sensor`/`number`/`input_number` wird der Wert ignoriert und
       stattdessen direkt der Entitätszustand verwendet
     - Optional: Innen-Luftfeuchtigkeit
     - Optional: CO2 (`sensor`-Entität mit ppm-Wert) – ohne Außenluft-
       Vergleich der Luftqualität, da Außenluft praktisch immer weit unter
       jeder sinnvollen Innenschwelle liegt (nur bei Außentemperatur über der
       Temperatur-Obergrenze öffnet CO2 erst ab dem 1,5-Fachen der Schwelle)
   - **Abschnitt "Fenster & Lüften"** (Fenster, Rollladen, Normalbereich-Grenzen,
     Schutzfunktionen; die Felder mit Zahlenwerten **überschreiben** für diesen
     Raum die allgemeinen Einstellungen - leer gelassen gilt der dort
     hinterlegte Wert, als Orientierung zeigt der Hinweistext darunter den
     aktuell wirksamen globalen Wert an, z. B. "Aktuell global: 23.0 °C"):
     - **Fensterkontakt** (optional; unterdrückt Benachrichtigungen, sobald
       das Fenster laut Sensor bereits im empfohlenen Zustand ist - siehe
       eigener Abschnitt unten; nur relevant, wenn "Dieser Raum hat kein
       Fenster" deaktiviert ist)
     - **Dieser Raum hat kein Fenster** (Checkbox, Standard: aus): bei "an"
       werden nie Öffnen-/Schließen-Benachrichtigungen erzeugt – nützlich
       z. B. für fensterlose Flure/Kellerräume, bei denen nur Luftentfeuchter,
       Klimaanlage oder Heizung anhand der Sensorwerte gesteuert werden sollen
       (siehe unten). Die Geräte-Steuerung läuft davon unabhängig weiter,
       unabhängig vom Fenster-Status. Bei "an" ist auch keine
       Benachrichtigungsmethode mehr zwingend erforderlich
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
     - Schwellenwerte zum Öffnen/Schließen für Temperatur, Luftfeuchtigkeit
       und CO2 sowie Frostschutz-Grenze, Hitzeschutz-Grenze, Winter-Schwelle
       und Winter-Höchstdauer – Zahlenfelder mit Pfeil-hoch/-runter-Steuerung
     - **Toleranz-Marge** (wirkt außer bei der Lüftungs-Logik auch als
       Hysterese der Heizungssteuerung und des Sommermodus), **Debounce-Zeit
       Frostschutz** und **Luftfeuchtigkeit/CO2 haben Vorrang** (im Raum:
       Ja/Nein/leer; Verhalten bei Erreichen der Winter-Höchstdauer)
   - **Abschnitt "Luftentfeuchter, Klima & Dusche"** (automatisch gesteuerte Geräte,
     Leistungs-/Laufzeit-Begrenzung und Duscherkennung; die Werte sind
     ebenfalls Raum-Overrides mit "Aktuell global: ..."-Hinweistext):
     - **Luftentfeuchter**: eine `switch`- oder `humidifier`-Entität
     - **Tankstatus-Sensor (Luftentfeuchter)** (optional): eine
       `binary_sensor`-Entität, die "an" meldet, sobald der Tank voll ist
       bzw. ein Fehler vorliegt - rein informativ, wird auf der
       Dashboard-Karte als eigenes Status-Icon (🔴 voll/Fehler, 🟢 ok) neben
       dem Luftentfeuchter-Status angezeigt; hat für sich allein keine
       Auswirkung auf die Lüftungs- oder Geräte-Steuerung selbst
     - **Benachrichtigung bei vollem Tank** (Standard aus): aktiviert eine
       echte Benachrichtigung, sobald der oben gewählte Tankstatus-Sensor
       "voll" meldet - nutzt dieselben, für den Raum aktuell wirksamen
       Kanäle wie die Lüftungsempfehlung (Sprachausgabe/App-Push/persistente
       Benachrichtigung), mit eigenem Text (siehe "Smart Climate Optionen",
       Abschnitt "Benachrichtigungstexte"). Löst sich automatisch wieder auf,
       sobald der Tank wieder als "leer" gemeldet wird. Nur wirksam, wenn
       oben auch tatsächlich ein Tankstatus-Sensor ausgewählt ist
     - **Klimaanlage**: eine `climate`- oder `switch`-Entität (die
       zugehörige Mindest-Einspeiseleistung/Abschaltverzögerung
       steht weiter unten in diesem Abschnitt)
     - **Fenster-Gerät-Konflikt melden** (Standard aus): EIN
       gemeinsamer Schalter für Luftentfeuchter UND Klimaanlage. Aktiviert
       eine echte Benachrichtigung, solange eines der beiden konfigurierten
       Geräte bei offenem Fenster gegen ungünstigere Außenluft ankämpft
       (Luftentfeuchter: Außenluft nicht trockener als drinnen;
       Klimaanlage: Außenluft nicht kühler als drinnen) - bewusst
       **unabhängig** von einem eventuellen Einspeiseleistungs-Überschuss,
       da das Schließen dem Gerät hilft, sein Ziel tatsächlich zu
       erreichen, auch wenn der Betrieb gerade "kostenlos" ist. Nutzt
       dieselben Kanäle wie die Lüftungsempfehlung, mit eigenem Text
       (siehe "Smart Climate Optionen", Abschnitt "Benachrichtigungstexte") und
       löst sich automatisch wieder auf, sobald das Fenster geschlossen
       wird oder die Außenluft wieder hilft. Läuft komplett unabhängig von
       der eigentlichen Öffnen/Schließen-Empfehlung - kann also auch dann
       auslösen, wenn diese gerade "aus"/neutral ist
     - **Mindest-Einspeiseleistung** / **Extreme Luftfeuchtigkeit** /
       **Abschaltverzögerung** sowie die drei
       **Höchstlaufzeit**-Felder (siehe "Geräte-Steuerung"): gelten
       nur für Luftentfeuchter/Klimaanlage, nicht für die Heizung (der
       Leistungssensor selbst ist nur in "- Smart Climate Optionen -"
       hinterlegbar, nicht pro Raum). Die Abschaltung wegen zu geringer
       Einspeisung richtet sich seit 0.91.0 nach dem tatsächlichen Gerätezustand:
       Sie gilt auch für ein von Hand oder von einer anderen Automation
       eingeschaltetes Gerät
     - **Duscherkennung** (Checkbox, Standard: aus; nur hier im Raum
       einstellbar, keine globale Einstellung) – siehe "Duscherkennung"
       unter "Logik im Detail". Die zugehörige **Anstiegs-Schwelle** und
       die **Duschdauer-Ansage** (ab wie vielen Minuten Sprachansage; nur
       Sprachausgabe) stehen direkt darunter
   - **Abschnitt "Heizung"** (Heizungs-Gerät, Presets, Anwesenheit und Sollwerte;
     Sollwerte sind Raum-Overrides mit "Aktuell global: ..."-Hinweistext):
     - **Temperaturquelle auch fürs Heizen** (Checkbox, Standard:
       aus): verwendet automatisch die im Abschnitt "Sensoren" gewählte Innentemperatur-Quelle
       als Heizungs-Gerät, statt sie zusätzlich im Feld "Heizung" separat
       auszuwählen - erspart die doppelte Auswahl derselben Entität für
       Räume, in denen dieselbe `climate`-Entität sowohl die Temperatur
       liefert als auch heizen soll. Nur wirksam, wenn die Temperaturquelle
       tatsächlich eine `climate`-Entität ist (bei `sensor`/`number`/
       `input_number` wie "keine Heizung konfiguriert" behandelt, kein
       Formularfehler). Bei aktiviertem Schalter wird das Feld "Heizung"
       direkt darunter ignoriert (Home-Assistant-Formulare können Felder
       nicht abhängig von einer Checkbox ausblenden, siehe "Home Assistant
       Companion App" im Abschnitt "Benachrichtigungen"
       weiter unten)
     - **Heizung** (optional): eine `climate`-Entität - anders als
       Luftentfeuchter/Klimaanlage kein einfaches Ein/Aus, sondern ein
       Umschalten zwischen einem Comfort-, einem Standby- und einem
       Nacht-Sollwert (siehe "Heizungs-Schwelle"/"Comfort-Sollwert"/
       "Standby-Sollwert"/"Nacht-Sollwert" weiter unten in diesem Abschnitt sowie
       "Heizungs-Zeitplan aktivieren" im Abschnitt "Heizungs-Zeitplan") - wie für
       Heizungen typisch. Details siehe
       "Geräte-Steuerung" weiter unten. Wird ignoriert, falls oben
       "Temperaturquelle auch fürs Heizen" aktiviert ist
     - **Presets steuern/anzeigen** (Ja/Nein/leer, Standard auch global: Ja)
       + vier Preset-Namen-Felder (Komfort/Standby/Eco (Nacht)/Gebäudeschutz):
       Manche climate-Integrationen (z. B. KNX) bilden diese Zustände nativ
       als `preset_mode` ab statt nur als Zahlen-Sollwert. Aktiviert (und nur
       wenn die gewählte Heizungs-Entität preset_mode tatsächlich
       unterstützt), wird darüber gesteuert **und** angezeigt statt über den
       Zahlen-Sollwert - die vier Namensfelder bieten dafür ein Dropdown mit
       den von der Entität tatsächlich gemeldeten Presets (frei editierbar,
       automatisch vorbelegt, falls ein passender Name erkannt wird). Leer
       gelassen (einzeln pro Zustand möglich) greift für genau diesen
       Zustand weiterhin der entsprechende Zahlen-Sollwert - Gebäudeschutz
       nutzt dafür ersatzweise den Standby-Sollwert, da es dafür keinen
       eigenen gibt. Gebäudeschutz wird ausschließlich gesetzt, solange das
       Fenster bestätigt offen ist (ersetzt dafür Standby); bei Abwesenheit
       oder aktivem Sommerbetrieb bleibt es bei Standby. Ohne
       Preset-Unterstützung der Entität bleibt es automatisch bei der
       reinen Sollwert-Steuerung, ganz ohne dass hier etwas eingestellt
       werden müsste. Details siehe "Geräte-Steuerung" weiter unten
     - **Anwesenheit für Heizung (Personen)** (optional): eine oder mehrere
       `person`- oder `device_tracker`-Entitäten (Mehrfachauswahl) - ist
       mindestens eine hinterlegt und melden ALLE davon bestätigt "nicht
       zuhause", verhindert das ausschließlich den Wechsel in den
       **Comfort**-Modus (Herabstufung auf Standby) - ein anderweitig
       ermittelter Standby-/Nacht-/Gebäudeschutz-Modus läuft unverändert
       normal weiter, es handelt sich also NICHT um eine eigene Pause.
       Meldet mindestens eine "zuhause", oder ist der Zustand einer von
       ihnen unbekannt/nicht verfügbar, heizt der Raum normal weiter
       (permissiv - ein einzelner GPS-Aussetzer soll die Heizung nicht
       fälschlich aus dem Comfort-Modus nehmen). Ohne hinterlegte Entität
       keine Auswirkung. Unabhängig von den im Abschnitt
       "Benachrichtigungen" konfigurierten Anwesenheits-Entitäten der App-Benachrichtigungsziele - dort geht es
       um "wen benachrichtigen", hier um "wann Comfort erlaubt ist"
     - **Heizungs-Schwelle (Innentemperatur)**, **Heizung Comfort-Sollwert**,
       **Heizung Standby-Sollwert** und **Heizung Nacht-Sollwert** (nur
       relevant, wenn oben eine Heizung hinterlegt oder die
       Temperaturquelle dafür wiederverwendet wird) - jeweils Dropdown mit gängigen Vorschlagswerten,
       weiterhin frei editierbar
   - **Abschnitt "Heizungs-Zeitplan"** (Raum-Override, leer = globaler Wert):
     - **Heizungs-Zeitplan aktivieren** (Ja/Nein/leer) - aktiviert, erzwingt
       ein Comfort- bzw. Nacht-Zeitfenster (je acht Zeitfelder: Start/Ende,
       getrennt nach Werktag und Wochenende) den jeweiligen Sollwert
       unabhängig von der Innentemperatur; außerhalb aller Zeitfenster gilt
       Standby. Deaktiviert (Standard) gilt weiterhin die reine
       Schwellenwert-Logik des Abschnitts "Heizung". Details siehe "Geräte-Steuerung" weiter
       unten
   - **Abschnitt "Benachrichtigungen"** (Sprachausgabe, App-Push, persistente
     Benachrichtigung und Erinnerung; die Anwesenheits-Entitäten für die
     Heizung stehen dagegen im Abschnitt "Heizung"):
     - **Lautsprecher** (`media_player`-Entitäten, z. B. Sonos, Mehrfachauswahl):
       Sprachausgabe ist automatisch aktiv, sobald hier mindestens ein
       Lautsprecher ausgewählt ist – kein eigener Ja/Nein-Schalter mehr,
       auch keine globale Einstellung dafür. Die TTS-Entität selbst kommt
       ausschließlich aus "Smart Climate Optionen" und ist hier nicht
       auswählbar
     - **Licht für Sprachausgabe** (optional, `light`-Entität): leer =
       Sprachausgabe funktioniert unabhängig vom Licht (wie bisher). Ist
       hier ein Licht hinterlegt, wird die Ansage nur unterdrückt, wenn
       dieses Licht aktuell **bestätigt aus** ist - ein unbekannter/nicht
       verfügbarer Zustand (z. B. kurz nach einem Neustart) unterdrückt die
       Ansage **nicht** (bewusst permissiv, reiner Komfort-Fall ohne
       Sicherheitsrelevanz). Betrifft ausschließlich die Sprachausgabe,
       App-Push und persistente Benachrichtigung laufen unverändert weiter
     - **Wiedergabelautstärke für Sprachausgabe** (optional): überschreibt
       für diesen Raum die in "Smart Climate Optionen" hinterlegte
       Lautstärke - leer gelassen gilt der dort hinterlegte Wert (Hinweistext
       zeigt den aktuell wirksamen globalen Wert an, z. B. "Aktuell global: 40 %")
     - **Sprachausgabe-Nachtruhe** (Ja/Nein/leer, Standard aus) sowie
       **Nachtruhe-Start**/**Nachtruhe-Ende** (optional, überschreiben die
       globalen Zeiten aus "Smart Climate Optionen", Standard 22:00–07:00):
       Ist die Nachtruhe aktiviert, wird die Sprachausgabe innerhalb dieses
       Zeitfensters unterdrückt - **ausschließlich** die Sprachausgabe, App-
       Push und persistente Benachrichtigung laufen unverändert weiter. Das
       Zeitfenster gilt für alle Wochentage gleich und unterstützt einen
       Mitternachts-Wraparound (Start > Ende, z. B. 22:00–07:00)
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
     - **Persistente Benachrichtigung** (Weboberfläche) (Ja/Nein/leer) –
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
setzt sie sämtliche Schwellenwerte, Sollwerte, Zeitfenster und Laufzeiten,
das Erinnerungsintervall und sämtliche Benachrichtigungstexte auf die
einprogrammierten Standardwerte zurück - unabhängig davon, was gerade in diesen Feldern eingetragen ist.
Ausgewählte Entitäten (Sensoren, TTS,
Leistungssensor, App-Benachrichtigungsziele), der Sprachausgabe-Modus und die
Benachrichtigungsmethoden bleiben davon unberührt. Einzelne Felder lassen
sich weiterhin wie gewohnt zurücksetzen, indem man nur sie leert und
speichert (siehe unten) - die Checkbox ist für den Fall gedacht, dass
gleich mehrere oder alle Werte auf einmal zurückgesetzt werden sollen.
Danach folgen sieben Abschnitte in derselben Gliederung wie im Raum-Formular
(alle standardmäßig eingeklappt; "Benachrichtigungstexte" gibt es nur hier):

**Abschnitt "Sensoren"** (Außen-Messwerte):
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

**Abschnitt "Fenster & Lüften"**:
- Der komplette Normalbereich-/Schwellenwerte-Satz (dieselben Felder wie im
  Raum-Abschnitt "Fenster & Lüften", inklusive CO2-Schwellen, Frost-/
  Hitzeschutz, Winter-Schwelle/-Höchstdauer) als raumweiter Standard
- **Toleranz-Marge**, **Debounce-Zeit Frostschutz** und **Luftfeuchtigkeit/CO2
  haben Vorrang** (fester Ja/Nein-Wert, Standard Ja): ebenfalls raumweiter
  Standard, pro Raum überschreibbar. Die Toleranz-Marge wirkt außer bei der
  Lüftungs-Logik auch als Hysterese der Heizungssteuerung und des Sommermodus

**Abschnitt "Luftentfeuchter, Klima & Dusche"**:
- **Leistungssensor**: wird für **alle** Räume verwendet – ist nicht im
  Raum-Formular auswählbar
- **Mindest-Einspeiseleistung** + **Extreme Luftfeuchtigkeit** +
  **Abschaltverzögerung**, die drei
  **Höchstlaufzeit**-Felder sowie **Anstiegs-Schwelle Duscherkennung** und
  **Duschdauer-Ansage**: Standardwerte für alle Räume, die keine eigenen
  Werte festlegen (pro Raum überschreibbar; die Aktivierung der
  Duscherkennung selbst sowie Luftentfeuchter/Klimaanlage/Tankstatus sind
  reine Raumeinstellungen)

**Abschnitt "Heizung"**:
- **Heizungs-Schwelle (Innentemperatur)**, **Heizung Comfort-Sollwert**,
  **Heizung Standby-Sollwert** und **Heizung Nacht-Sollwert** - Dropdown
  mit gängigen Vorschlagswerten, weiterhin frei editierbar; als raumweiter
  Standard, pro Raum überschreibbar (die Heizungs-Entität selbst ist wie
  Luftentfeuchter/Klimaanlage reine Raumeinstellung)
- **Presets steuern/anzeigen** (Standard Ja) + vier Preset-Namen-Felder
  (Komfort/Standby/Eco (Nacht)/Gebäudeschutz) als raumweiter Standard -
  hier Dropdown mit den acht offiziellen Home-Assistant-Standardwerten als
  Vorschlag (kein konkretes Gerät zum Auslesen auf globaler Ebene, daher
  nur ein Hinweis statt eines Live-Werts), weiterhin frei editierbar; pro
  Raum überschreibbar und dort mit Dropdown-Vorschlag der tatsächlich von
  der jeweiligen Entität gemeldeten Presets (siehe Abschnitt "Heizung"
  im Raum-Formular)
- **Sommermodus-Vorhersagequelle** (optional, nur global): eine `sensor`-
  oder `weather`-Entität mit einer Temperatur-Vorhersage - z. B. ein eigener
  Template-Sensor, der die Tagesvorhersage als Attribut bereitstellt (kein
  direkter `weather.get_forecasts`-Service-Aufruf durch diese Integration
  nötig, siehe "Geräte-Steuerung" unten). Steuert damit automatisch den
  unten hinterlegten Sommer-/Winterbetrieb-Schalter. Ohne diese Entität
  bleibt der Schalter rein manuell bedienbar (das zugehörige
  Vorhersage-Attribut steht direkt darunter)
- **Vorhersage-Attribut** (optional): Name eines Attributs der oben
  hinterlegten Sommermodus-Vorhersagequelle, aus dem der Vorhersagewert
  gelesen wird - Dropdown mit den offiziell dokumentierten Standard-
  Attributen einer `weather`-Entität (`temperature`, `templow`,
  `dew_point`, `humidity`, `pressure`, `wind_speed`, `wind_bearing`,
  `wind_gust_speed`, `visibility`, `uv_index`, `cloud_coverage`, `ozone`),
  weiterhin frei editierbar für einen abweichenden, z. B. selbst gewählten
  Attributnamen eines eigenen Template-Sensors. Leer = state der Entität
  direkt als Zahl lesen (z. B. bei einem Template-Sensor, dessen state
  selbst schon der Vorhersagewert ist)
- **Sommer-/Winterbetrieb-Schalter** (optional, nur global): eine bereits
  **vorhandene** `switch`-Entität - wird **nicht** von dieser Integration
  angelegt, sondern nur aktiv gesteuert (analog zu Luftentfeuchter/
  Klimaanlage/Heizung, siehe "Geräte-Steuerung" unten). **An** = Sommerbetrieb
  (Heizung aller Räume pausiert), **Aus** = Winterbetrieb (Heizung läuft
  normal). Ohne konfigurierte Entität hat der Sommer-/Winterbetrieb keine
  Wirkung, selbst wenn eine Vorhersagequelle hinterlegt ist
- **Sommermodus-Schwelle (Vorhersage)** - ab dieser Vorhersage-Temperatur
  (+/- Toleranz-Marge) wird der oben hinterlegte Sommer-/Winterbetrieb-
  Schalter automatisch eingeschaltet (Sommerbetrieb), darunter automatisch
  wieder ausgeschaltet (Winterbetrieb). Nur global verfügbar, **kein**
  Raum-Override - andernfalls könnten unterschiedliche Räume
  unterschiedliche Entscheidungen für denselben gemeinsamen Schalter
  treffen. Nur wirksam, wenn oben sowohl eine Vorhersagequelle als auch der
  zu steuernde Schalter konfiguriert sind

**Abschnitt "Heizungs-Zeitplan"**:
- **Heizungs-Zeitplan aktivieren** (global immer ein fester Ja/Nein-Wert,
  Standard Nein) sowie acht Zeitfelder (Comfort-/Nacht-Start/-Ende, je
  getrennt für Werktag und Wochenende) als raumweiter Standard - pro Raum
  überschreibbar wie jeder andere Parameter

**Abschnitt "Benachrichtigungen"**:
- **TTS-Entität**: wird verwendet, wenn ein Raum keine eigene TTS-Entität
  für die Sprachausgabe festlegt
- **Wiedergabelautstärke für Sprachausgabe**: Lautstärke (0–100 %), auf die
  die Lautsprecher **vor** der Ansage gesetzt werden - Dropdown mit
  gängigen Vorschlagswerten, weiterhin frei editierbar; pro Raum im
  Abschnitt "Benachrichtigungen" überschreibbar
- **Vorhandene Wiedergabe beim Ansagen**: "Überlagern" (Standard) spielt die
  Ansage direkt über eine laufende Wiedergabe; "Pausieren" pausiert sie vorher
- **Sprachausgabe-Nachtruhe** + Start/Ende, **Home Assistant Companion App**,
  **App-Benachrichtigungsziele**, **Persistente Benachrichtigung**:
  globaler Standard, pro Raum überschreibbar
- **Erinnerungsintervall** als raumweiter Standard - pro Raum im Abschnitt
  "Benachrichtigungen" überschreibbar (siehe oben)

Sprachausgabe hat hier keine eigene Aktivierung – Lautsprecherauswahl und
Aktivierung erfolgen ausschließlich pro Raum.

**Abschnitt "Benachrichtigungstexte"** (nur global):
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
> Abschnitt "Benachrichtigungen" ist deshalb immer sichtbar,
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

Jede der drei Größen (Temperatur, Luftfeuchtigkeit, CO2) hat ein Paar
Schwellenwerte, die zusammen einen **Normalbereich** aufspannen: unterhalb
der Untergrenze (Formularfelder "Untergrenze Temperatur/Luftfeuchtigkeit/CO2
(schließen)") wird geschlossen, oberhalb der Obergrenze (Formularfelder
"Obergrenze ... (öffnen)") wird geöffnet, dazwischen bleibt der zuletzt gesetzte Zustand
unverändert (Hysterese/Totzone, siehe unten). Genau diese
Normalbereich-Grenzen entscheiden bei Temperatur und Luftfeuchtigkeit auch
mit darüber, wann die Außenluft selbst als "nicht mehr hilfreich" gilt
(Sommer-Fall/"Außen feuchter", siehe unten).

**Öffnen** wird empfohlen, wenn (und weder Frost- noch Hitzeschutz greift):
- Innentemperatur ≥ "Schwelle zum Öffnen" **und** draußen mindestens um die
  Toleranz-Marge kühler ist als drinnen, **oder**
- Luftfeuchtigkeit ≥ "Schwelle zum Öffnen" **und** (kein Außen-
  Luftfeuchtigkeitssensor hinterlegt **oder** es draußen **absolut**
  betrachtet trockener ist als drinnen – siehe "Absolute vs. relative
  Luftfeuchtigkeit" unten), **oder**
- CO2 ≥ "CO2-Schwelle zum Öffnen" – **ohne** Außenluft-Vergleich der
  Luftqualität selbst, da Außenluft praktisch immer bei ~420 ppm liegt.
  Ist die Außentemperatur allerdings höher als die Temperatur-Obergrenze
  ("Schwelle zum Öffnen"), würde Lüften den Raum aufheizen: dann öffnet CO2
  nur noch, wenn der Wert die CO2-Schwelle um mehr als das **1,5-Fache**
  überschreitet (bei 1000 ppm also über 1500 ppm; Faktor fest, keine
  Einstellung). Ohne verfügbaren Außentemperaturwert entfällt diese
  Einschränkung - die Luftqualität soll nicht von einem Sensorausfall
  abhängen

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
- **Sommer-Fall**: die Außentemperatur selbst hat inzwischen die "Normalbereich"-
  Obergrenze (Temperatur-Schwelle zum Öffnen) erreicht/überschritten – die
  Außenluft ist damit nicht mehr nur wärmer als die aktuelle Innenluft,
  sondern liegt selbst außerhalb des Normalbereichs, sodass Lüften die
  Situation nicht mehr verbessern würde – *außer* es wird gerade noch aus
  Feuchtigkeits- oder CO2-Gründen gelüftet, **oder**
- **Außenluft inzwischen feuchter**: das Pendant zum Sommer-Fall für
  Luftfeuchtigkeit – die Öffnen-Empfehlung wegen Luftfeuchtigkeit prüft
  einmalig beim Öffnen, ob die Außenluft absolut trockener ist als die
  Innenluft (siehe oben); danach gilt, identisch zum Sommer-Fall, dieselbe
  "Normalbereich"-Logik: Erst wenn die absolute Außenluftfeuchtigkeit die
  in absolute Luftfeuchtigkeit umgerechnete "Normalbereich"-Obergrenze
  (Feuchtigkeits-Schwelle zum Öffnen) selbst erreicht/überschreitet, würde
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
"Luftfeuchtigkeit/CO2 haben Vorrang" (gegenüber der Winter-Höchstdauer) legt fest, wie
dieser Konflikt aufgelöst wird:
- **An (Standard)**: Luftfeuchtigkeit/CO2 gewinnen – die Winter-Höchstdauer
  wird bei noch bestehendem Feuchtigkeits- oder CO2-Lüftungsbedarf
  ignoriert, das Fenster bleibt offen (Gesundheit/Schimmelvermeidung vor
  Wärmeverlust-Begrenzung)
- **Aus**: die Winter-Höchstdauer wird strikt durchgesetzt, auch bei noch
  hoher Luftfeuchtigkeit oder hohem CO2-Wert (Wärmeverlust-Begrenzung vor
  Schimmelvermeidung/Gesundheit)

In den globalen Einstellungen ("Smart Climate Optionen") als fester
Ja/Nein-Schalter, im Raum-Abschnitt "Fenster & Lüften" als Ja/Nein/Leer-Auswahl
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
"Luftentfeuchter, Klima & Dusche" aktivierbar - keine globale Einstellung), gedacht für Bäder mit
Dusche/Badewanne, bei denen die Luftfeuchtigkeit durch das Duschen sehr
schnell ansteigt. Ist "Duscherkennung" für einen Raum aktiviert, wird
laufend der Anstieg der bereits konfigurierten Luftfeuchtigkeit über die
letzten 10 Minuten beobachtet - kein zusätzlicher Sensor nötig. Steigt die
Luftfeuchtigkeit schneller als die "Anstiegs-Schwelle" (Standard 1,5
%-Punkte/Minute, im Abschnitt "Luftentfeuchter, Klima & Dusche" einstellbar), wird angenommen,
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

**Duschdauer-Ansage** (seit 0.89.0): Optional (Standard 0 = aus) kann eine
Sprachansage ausgelöst werden, sobald die erkannte Dusche länger als die
eingestellte Zeit ununterbrochen läuft. Einstellung "Duschdauer-Ansage ab
(Minuten)" im Abschnitt "Luftentfeuchter, Klima & Dusche" (global und als
Raum-Override); Dropdown mit 0 (aus)/8/10/12/15/20 Minuten,
frei editierbar. Typische Duschen dauern etwa 5-10 Minuten - die gemessene
Dauer ist die Zeit mit erhöhter Luftfeuchtigkeit, also etwas länger als das
reine Duschen; einen Anhaltspunkt für den eigenen Wert liefert die Spalte
"Laufzeit" der Dusche-Zeile in der Dashboard-Karte (letzter Lauf). Die Ansage
läuft nur über die Sprachausgabe (media_player-Lautsprecher des Raums, TTS-Entität
nötig), gilt nur für Räume mit aktivierter Duscherkennung, kommt einmal pro
Dusche und beachtet Sprachausgabe-Nachtruhe und Licht-aus-Regel wie die
Wassertank-Ansage (eine dadurch unterdrückte Ansage wird nicht später in
derselben Dusche nachgeholt). Der Text ist global einstellbar
(`msg_shower_long`, Platzhalter `{raum}`, `{wert}` = bisherige Dauer in Minuten,
`{schwelle}`), Standard: "Die Dusche im {raum} läuft schon seit {wert} Minuten."

Direkt nach einem Start oder Neuladen der Integration (bzw. nach einem
Sensorausfall) ist der Feuchteverlauf noch leer - deshalb wird die Erkennung
erst bewertet, wenn mindestens 3 Minuten Verlauf vorliegen. Sonst könnte ein
normaler Ausschlag des Sensors (z. B. bei offenem Fenster) in den ersten
Minuten als Duschen gelten. Im laufenden Betrieb verzögert das nichts.
Zusätzlich muss die Luftfeuchtigkeit im Beobachtungsfenster insgesamt um
mindestens 8 %-Punkte steigen (liegt über dem normalen Rauschen eines
Hygrometers, eine echte Dusche steigt um deutlich mehr) - unabhängig davon,
wie hoch die Rate kurzzeitig wirkt.
**Diagnose:** Bei jedem Anschlagen und Ende der Erkennung führt der
Haupt-Sensor ein Kurzprotokoll im Attribut `dusche_verlauf` (letzte 6
Einträge, neueste zuerst): Zeitpunkt, Feuchte, berechneter Anstieg samt
Beobachtungsdauer, Fensterzustand, Minuten seit Start und die letzten
Messwerte. Es steht auch in der heruntergeladenen Diagnose-Datei und hilft,
einen Fehlalarm nachzuvollziehen (nicht über Neustarts hinweg gespeichert).

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

Ist im Abschnitt "Fenster & Lüften" ein Fensterkontakt hinterlegt, wird sein
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

Die Schwellenwerte zum Öffnen/Schließen selbst (im Abschnitt "Fenster & Lüften")
bleiben bewusst in % RH - das ist der Wert, der spürbar ist und der
Schimmelrisiko-Bewertungen zugrunde liegt. Nur der reine Außen-/
Innenvergleich ("würde Lüften die Feuchtigkeit tatsächlich senken?")
nutzt die berechnete absolute Feuchte.

## Absolute Luftfeuchtigkeit und Taupunkt als Sensoren

Die Integration legt die absolute Luftfeuchtigkeit (g/m³, Magnus-Formel wie in
der Lüftungslogik) und den Taupunkt (°C, ebenfalls Magnus-Formel) zusätzlich
als eigene `sensor`-Entitäten an:

- `sensor.<raum>_absolute_luftfeuchtigkeit` - je Raum mit konfiguriertem
  Feuchtigkeitssensor (Temperatur und Feuchte des Raums).
- `sensor.aussen_absolute_luftfeuchtigkeit` - einmal, aus den in den globalen
  Einstellungen gewählten Außensensoren.
- `sensor.<raum>_taupunkt` und `sensor.aussen_taupunkt` - dieselben
  Quellen, Ergebnis in °C (Temperatur, bei 0 % Luftfeuchtigkeit "nicht
  verfügbar"). Der Taupunkt ist die Temperatur, auf die Luft abkühlen muss,
  damit Feuchtigkeit kondensiert - kältere Oberflächen (Fenster, Außenwand-
  ecken) beschlagen bzw. schimmeln. Ist der Außentaupunkt niedriger als der
  Innentaupunkt, ist die Außenluft absolut trockener (Lüften entfeuchtet).

Alle sind normale Sensoren (Verlauf, Diagramme, Automationen) und liefern
"nicht verfügbar", solange ein Eingangswert fehlt. Der Raum-Sensor reagiert auf
Änderungen der Quell-Sensoren, der Außen-Sensor zusätzlich alle 5 Minuten. Die
JS-Karte zeigt den Taupunkt als eigene Zeile (Raum- und Außen-Tabelle) und öffnet die Sensoren per Klick auf "Abs. Luftfeuchtigkeit" bzw. "Taupunkt". Nach dem Update ist
ein Neustart von Home Assistant nötig (neue Plattform).

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
  Ein/Aus, sondern ein Umschalten zwischen festen Sollwerten (Comfort/
  Standby/Nacht, über `climate.set_temperature`) - wie für Heizungen
  typisch. Zwei echte Pausen (Fenster offen, Sommerbetrieb aktiv - beide
  siehe unten) haben dabei immer höchste Priorität und schalten sofort auf
  **Gebäudeschutz** bzw. **Standby** (siehe unten), unabhängig von allem
  anderen weiter unten. Abwesenheit (siehe unten) ist dagegen **keine**
  eigene Pause, sondern verhindert ausschließlich den Wechsel in **Comfort**
  - ein bereits anderweitig ermittelter Standby-/Nacht-/Gebäudeschutz-Modus
  bleibt davon unberührt.

  **Presets statt Sollwert** (optional, Option "Presets steuern/anzeigen",
  Standard auch global Ja): Manche climate-Integrationen (z. B. KNX) bilden
  Comfort/Standby/Nacht/Gebäudeschutz nativ als `preset_mode`
  (`climate.set_preset_mode`) ab statt nur als Zahlen-Sollwert - portabler
  wäre eigentlich der reine Zahlen-Sollwert (Preset-Namen sind zwischen
  Herstellern nicht standardisiert), aber wo eine Entität das native
  Preset-Konzept anbietet, ist die direkte Steuerung darüber die
  naheliegendere Wahl. Aktiv nur, wenn die gewählte Heizungs-Entität
  `preset_mode` tatsächlich unterstützt (automatisch geprüft, keine
  Einstellung nötig) UND für den jeweiligen Zustand ein Preset-Name
  hinterlegt ist (vier Felder im Raum-Formular, Dropdown mit den von der
  Entität tatsächlich gemeldeten Presets) - fehlt der Name für einen
  einzelnen Zustand, greift für genau diesen weiterhin der entsprechende
  Zahlen-Sollwert. **Gebäudeschutz** ersetzt dabei Standby ausschließlich
  beim Pausier-Grund "Fenster offen" (nicht bei Abwesenheit/Sommerbetrieb) -
  es gibt dafür keinen eigenen Zahlen-Sollwert, ohne hinterlegten
  Preset-Namen wird ersatzweise der Standby-Sollwert verwendet. Bei aktiver
  Preset-Steuerung liest auch die Anzeige (`heizung_modus`,
  Dashboard-Karte) direkt den live vom Gerät gemeldeten `preset_mode`
  zurück, statt den Sollwert näherungsweise zu erraten.

  Ist **"Heizungs-Zeitplan aktivieren"** (Abschnitt "Heizungs-Zeitplan")
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

  **Pausen im Detail** (schalten sofort auf Gebäudeschutz/Standby,
  unabhängig vom eigentlich gewollten Zielmodus):
  - Solange der Fensterkontakt-Sensor das Fenster als **bestätigt offen**
    meldet - gegen ein offenes Fenster zu heizen verschwendet nur Energie.
  - Solange der globale **Sommer-/Winterbetrieb-Schalter** (siehe unten)
    **an** ist (Sommerbetrieb) - pausiert dann die Heizung **aller** Räume.

  **Abwesenheit - keine Pause, sondern ein reines Comfort-Verbot:** Sobald
  im Abschnitt "Heizung" mindestens eine
  Anwesenheits-Entität für die Heizung hinterlegt ist UND ALLE davon
  bestätigt "nicht zuhause" melden, wird ein ansonsten ermittelter
  Comfort-Zielmodus auf Standby herabgestuft - ein bereits anderweitig
  ermittelter Standby-, Nacht- oder Gebäudeschutz-Zielmodus läuft dagegen
  unverändert normal weiter, genau wie ohne Abwesenheit. Meldet mindestens
  eine Entität "zuhause", oder ist der Zustand einer von ihnen gerade
  unbekannt/nicht verfügbar, greift diese Herabstufung gar nicht (permissiv,
  ein einzelner GPS-Aussetzer soll die Heizung nicht fälschlich aus dem
  Comfort-Modus nehmen). Ohne konfigurierte Entität entfällt diese
  Bedingung komplett.
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
- **Live-Anzeige der Geräte (seit 0.92.2)**: Die Integration verfolgt die
  Geräte-Entitäten (Luftentfeuchter, Klimaanlage, Heizung, Tankstatus-Sensor)
  und schreibt bei jeder Zustandsänderung sofort den Sensorzustand neu. Die
  Dashboard-Karte zeigt ein ein- oder ausgeschaltetes Gerät (auch von Hand oder
  durch eine andere Automation geschaltet) deshalb ohne Verzögerung. Die
  Lüftungslogik wird dadurch nicht neu bewertet.
- **Extreme Luftfeuchtigkeit (seit 0.92.0, nur Luftentfeuchter)**: Liegt die
  Luftfeuchtigkeit mindestens bei der Schwelle "Extreme Luftfeuchtigkeit"
  (Standard 80 %, 0 = aus; global, pro Raum überschreibbar), läuft der
  Luftentfeuchter auch bei zu geringer Einspeiseleistung: Die
  Mindest-Einspeiseleistung gilt dann nicht, und die Abschaltverzögerung
  schaltet ihn nicht ab. Unverändert wirksam bleiben die Pause bei offenem
  Fenster (feuchtere Außenluft), der Tankstatus, die Obergrenze des
  Normalbereichs (ohne Überschreitung wird nicht eingeschaltet), die
  Ruhezeit nach der Höchstlaufzeit und die Höchstlaufzeit "bei geringer
  Einspeiseleistung" (sie richtet sich weiter nach der tatsächlichen
  Einspeisung). Der Grund in der Gerätetabelle lautet dann "extreme
  Luftfeuchtigkeit (läuft trotz geringer Einspeiseleistung)". Ohne
  Leistungssensor ändert die Schwelle nichts.
- **Rollladen-Kopplung**: Ist bei der Klimaanlage eine Fenstersperre/Rollladen
  hinterlegt, wird diese automatisch aktiviert, sobald die Klimaanlage
  einschaltet, und wieder deaktiviert, sobald sie ausschaltet. Unterstützt
  sowohl `cover`-Entitäten (auf/zu) als auch `switch`-Entitäten (an =
  herunterfahren + gesperrt, aus = hochfahren + entsperrt).
- **Höchstlaufzeit** (Abschnitt "Luftentfeuchter, Klima & Dusche", global + Raum-Override):
  Läuft Luftentfeuchter oder Klimaanlage ununterbrochen länger als diese
  Zeit, werden sie zwangsweise abgeschaltet - unabhängig davon, ob die
  eigentliche Zielbedingung (Feuchtigkeit/Temperatur) noch erfüllt ist.
  Verfolgt wird dafür die tatsächlich am Gerät live abgefragte Laufzeit,
  nicht nur der zuletzt von dieser Integration gesendete Befehl. Es gibt
  **zwei Werte**, je nach aktueller Einspeiseleistung (Grenze ist die
  **Mindesteinspeiseleistung** aus dem Leistungssensor oben):
  - **Höchstlaufzeit bei geringer Einspeisung** (Standard 0 =
    deaktiviert): gilt, solange die Leistung unter der
    Mindesteinspeiseleistung liegt - und immer dann, wenn kein
    Leistungssensor konfiguriert ist.
  - **Höchstlaufzeit bei hoher Einspeisung** (Standard 0 =
    unbegrenzt, wie bisher): gilt, solange die Leistung mindestens der
    Mindesteinspeiseleistung entspricht (nur mit konfiguriertem
    Leistungssensor). Damit lässt sich z. B. bei viel PV-Überschuss eine
    längere Laufzeit erlauben als bei knappem Überschuss.

  Nach einem Zwangs-Abschalten (in beiden Fällen) gilt zusätzlich eine
  gemeinsame, konfigurierbare **Ruhezeit** (Standard 30 Minuten), bevor das
  Gerät wieder einschalten darf - ohne sie würde es bei weiterhin hoher
  Feuchtigkeit/Temperatur sofort wieder anspringen und die Begrenzung wäre
  wirkungslos. Während der Ruhezeit zeigt die Geräte-Tabelle als Grund
  "Ruhezeit nach Höchstlaufzeit, bis HH:MM" an.

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
| `luftfeuchtigkeit`, `schwelle_feuchtigkeit_oeffnen` / `_schliessen` | nur vorhanden, falls ein Luftfeuchtigkeits-Sensor hinterlegt ist |
| `co2`, `schwelle_co2_oeffnen` / `_schliessen` | nur vorhanden, falls ein CO2-Sensor hinterlegt ist |
| `offene_gruende` | Liste der aktuell live zutreffenden Öffnen-Gründe (`temp`/`humidity`/`co2`, auch mehrere gleichzeitig möglich) - "liegt der Messwert gerade außerhalb des Normalbereichs" **und** die Außenluft-Prüfung des jeweiligen Grunds (Temperatur: Außen kühler, Luftfeuchtigkeit: Außen absolut trockener, CO2: nicht bei zu warmer Außenluft, außer deutlich erhöht), damit die Karte keinen Auslöser zeigt, der die Empfehlung gar nicht auslöst. Unabhängig vom tatsächlichen `should_open` (das zusätzlich Frost-/Hitzeschutz/Hysterese/Duscherkennung berücksichtigt). Dient der Dashboard-Karte für den Fenster-Mismatch-Abgleich, ohne die Vergleichslogik selbst nachbauen zu müssen |
| `schliessgrund_live` | wie `offene_gruende`, aber für die Schließen-Seite (dort kann strukturell nur ein Grund gewinnen): `temp`/`humidity`/`co2`/`frost`/`heat`/`outdoor_warmer`/`outdoor_wetter`/`duration`, leerer String falls keiner zutrifft. Berücksichtigt bereits "Schließempfehlung deaktivieren" (reine Komfort-Gründe entfallen dann, Frost-/Hitzeschutz bleiben unberührt) |
| `aussen_luftfeuchtigkeit` | nur vorhanden, falls global gesetzt |
| `taupunkt` / `aussen_taupunkt` | Taupunkt in °C (Magnus-Formel), nur wenn Temperatur und Feuchte vorliegen und die Feuchte > 0 % ist - nur für die Anzeige in der JS-Karte |
| `absolute_luftfeuchtigkeit` / `aussen_absolute_luftfeuchtigkeit` | berechnete absolute Luftfeuchtigkeit (g/m³, siehe "Absolute vs. relative Luftfeuchtigkeit") - nur vorhanden, wenn die jeweils nötigen Temperatur-/Feuchtigkeitswerte verfügbar sind. Genau diese Werte entscheiden, ob Lüften bei hoher Innen-Luftfeuchtigkeit tatsächlich empfohlen wird |
| `empfehlung_aktiv_seit` | Zeitpunkt, seit dem "Lüften empfohlen" aktiv ist |
| `fenster_seit` | Zeitpunkt, seit dem der Fensterkontakt im aktuellen Zustand (auf/zu) steht - aus der Verlaufsdatenbank gelesen, übersteht Neustarts (siehe Dashboard-Karte, "Fenster-Zeitpunkt über Neustarts"). Nur gesetzt, wenn bekannt |
| `letzter_wechsel` | Zeitpunkt des letzten ECHTEN Empfehlungswechsels (nur bei tatsächlichem Zustandswechsel neu gesetzt, über Neustarts hinweg korrekt erhalten) - anders als `last_changed` der Entität selbst, das Home Assistant bei jedem Neustart auf den Neustart-Zeitpunkt zurücksetzt. Von der Dashboard-Karte für die "Uhrzeit"-Spalte der Empfehlung verwendet, statt sich auf das irreführende `last_changed` zu verlassen |
| `letzter_grund` | Grund der letzten Empfehlungsänderung (`temp`, `humidity`, `co2`, `frost`, `heat`, `duration`, `outdoor_warmer`, `outdoor_wetter`) - fehlt ein Außentemperatur-Wert (Sensor gerade `unavailable`/`unknown`), schließt der Frostschutz zwar vorsorglich, ohne dabei `letzter_grund` zu setzen (siehe "Logik im Detail") |
| `letzte_benachrichtigung` | Zeitpunkt der letzten tatsächlich verschickten Benachrichtigung |
| `luftentfeuchter_an`, `klimaanlage_an` | nur vorhanden, falls die jeweiligen Geräte konfiguriert sind UND ihre Entität aktuell im Zustandsautomaten existiert (nicht z. B. wegen deaktiviertem Integrationseintrag komplett entfernt) - live vom tatsächlichen Gerätezustand gelesen (auch wenn das Gerät manuell oder von einer anderen Automation ein-/ausgeschaltet wurde, nicht nur wenn diese Integration es selbst geschaltet hat). Ist die Entität komplett verschwunden, wird das Gerät auch nicht mehr gesteuert - anders als eine bloß vorübergehende "nicht verfügbar"-Meldung (Gerät kurz offline), die weiterhin wie "aus" behandelt wird |
| `luftentfeuchter_grund`, `klimaanlage_grund` | nur vorhanden, falls das jeweilige Gerät konfiguriert und seine Entität vorhanden ist - kurzer, rein informativer Text, warum das Gerät aktuell an/aus ist bzw. pausiert (z. B. "Luftfeuchtigkeit über Schwelle", "pausiert: Fenster offen, Außenluft nicht trockener"); live bei jeder Neubewertung berechnet, hat selbst keine Steuerungswirkung |
| `luftentfeuchter_tank_fehler` | nur vorhanden, falls ein Tankstatus-Sensor für den Luftentfeuchter hinterlegt ist; `true`, solange dieser "an" meldet (Tank voll/Fehler) |
| `luftentfeuchter_seit`, `klimaanlage_seit`, `dusche_seit` | nur vorhanden, solange das jeweilige Gerät gerade läuft bzw. die Duscherkennung gerade anschlägt - Zeitpunkt, seit dem das ununterbrochen der Fall ist (Dashboard-Karte, Spalte "Laufzeit"). Live anhand des tatsächlichen Gerätezustands gepflegt (wie `luftentfeuchter_an`/`klimaanlage_an`), übersteht daher auch ein manuelles Ein-/Ausschalten außerhalb dieser Integration korrekt |
| `dusche_letzter_start` | Startzeitpunkt der zuletzt erkannten Dusche (ISO-Zeitstempel) - bleibt nach dem Ende stehen (anders als `dusche_seit`) und übersteht einen Neustart; Dashboard-Karte, Zeile "Dusche" der Gerätetabelle |
| `luftentfeuchter_letzte_laufzeit`, `klimaanlage_letzte_laufzeit`, `dusche_letzte_laufzeit` | Dauer (Minuten) des letzten ABGESCHLOSSENEN Laufs - nur vorhanden, sobald mindestens einmal ein Lauf beendet wurde, bleibt danach bis zum nächsten abgeschlossenen Lauf unverändert stehen. Die Dashboard-Karte zeigt in der Spalte "Laufzeit" diesen Wert, solange das Gerät gerade aus ist (bzw. die Duscherkennung nicht anschlägt) - andernfalls weiterhin die laufende Zeit aus `..._seit` |
| `heizung_an` | nur vorhanden, falls eine Heizung konfiguriert ist UND ihre Entität aktuell im Zustandsautomaten existiert. Anders als `luftentfeuchter_an`/`klimaanlage_an` kein reines Ein/Aus, sondern `true` genau bei Comfort - erkennt daher auch, wenn der Sollwert/Preset manuell oder von einer anderen Automation geändert wurde |
| `heizung_modus` | wie `heizung_an`, aber alle vier Stufen: `"comfort"`/`"standby"`/`"night"`/`"building_protection"` (bzw. `null`, falls sich der aktuelle Zustand nicht ablesen/zuordnen lässt). Bei aktiver Preset-Steuerung direkt aus dem live gemeldeten `preset_mode` zurückgemappt, sonst aus der Näherung zum aktuellen Zahlen-Sollwert (kennt dabei kein `"building_protection"`, da es dafür keinen eigenen Sollwert gibt) |
| `heizung_zieltemperatur` | aktuell am Heizungs-Gerät eingestellter Sollwert (live gelesen, unabhängig von Preset- oder Sollwert-Steuerung), `null` falls (noch) nicht ablesbar |
| `heizung_grund` | wie `luftentfeuchter_grund`/`klimaanlage_grund`, nur für die Heizung (z. B. "Innentemperatur unter Schwelle, Comfort", "Zeitfenster: Nacht", "pausiert: Fenster offen", "pausiert: Sommerbetrieb aktiv") |
| `heizung_seit` | wie `luftentfeuchter_seit`/`klimaanlage_seit` - Zeitpunkt, seit dem `heizung_an` ununterbrochen `true` ist |
| `heizung_letzte_laufzeit` | wie `luftentfeuchter_letzte_laufzeit`/`klimaanlage_letzte_laufzeit`, nur für die Heizung |
| `sommermodus_an` | nur vorhanden, falls in "- Smart Climate Optionen -" ein Sommer-/Winterbetrieb-Schalter hinterlegt ist UND diese Entität aktuell im Zustandsautomaten existiert - `true`/`false`, live vom Schalter gelesen. Identisch für jeden Raum, da es sich um eine hausweite, nicht raumspezifische Einstellung handelt |
| `hat_fenster` | nur vorhanden (mit Wert `false`), falls "Dieser Raum hat kein Fenster" aktiviert ist |
| `sprachausgabe_aktiv`, `sprachausgabe_lautsprecher` | nur vorhanden, wenn der Raum mindestens einen Lautsprecher ausgewählt hat |
| `app_aktiv`, `app_ziele` | nur vorhanden, wenn App-Benachrichtigung effektiv aktiv ist |
| `persistent_aktiv` | nur vorhanden, wenn persistente Web-Benachrichtigung effektiv aktiv ist |
| `duschen_erkannt` | nur vorhanden, wenn Duscherkennung effektiv aktiv ist; `true`, solange die Luftfeuchtigkeit schneller als die Anstiegs-Schwelle steigt (siehe "Duscherkennung" unter "Logik im Detail") |
| `entitaeten` | Entity-IDs der angezeigten Werte/Geräte (`innentemperatur`, `luftfeuchtigkeit`, `co2`, `aussentemperatur`, `aussen_luftfeuchtigkeit`, `fenster`, `luftentfeuchter`, `luftentfeuchter_tank`, `klimaanlage`, `heizung`, `sommermodus`, `dusche`, `absolute_luftfeuchtigkeit`, `aussen_absolute_luftfeuchtigkeit`, `taupunkt`, `aussen_taupunkt`) - nur die konfigurierten bzw. vorhandenen. Die JS-Karte öffnet damit per Klick die Detailansicht (more-info) |
| `integration_version` | aktuell installierte Version der Integration (aus `manifest.json`) - identisch für jeden Raum, dient nur der Dashboard-Karte zur Anzeige der Versionsnummer |

Der Standard-Entitätszustand selbst (`last_changed`) zeigt außerdem, seit
wann der aktuelle Öffnen/Schließen-Status gilt.

### Dashboard-Karte (Statusübersicht aller Räume)

Die Integration bringt eine eigene Lovelace-Karte mit (`smart-climate-card`,
Einrichtung siehe "Einrichtung und Bedienung der Karte" weiter unten). Sie
zeigt automatisch alle Räume mit Status, aktuellen Werten, Schwellenwerten
und letzter Änderung. Die folgenden Abschnitte beschreiben, was die Karte
anzeigt und wie sie die Farben bestimmt.

**Hervorhebung des ausschlaggebenden Werts** (fette, farbige Schrift):
Hervorgehoben wird jeweils die Zelle mit der Maßeinheit zusammen (z. B. `34.2 °C`,
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

Auslöser und Hervorhebung werden dabei **live** berechnet, nicht aus dem
historischen `letzter_grund`-Attribut: Die Integration selbst wertet bei
jedem Lesen der Attribute (nicht nur bei einem echten Zustandswechsel)
aus, welche der drei Öffnen-Größen (Innentemperatur, Luftfeuchtigkeit,
CO2) aktuell ihre Öffnen-Schwelle erreichen (`offene_gruende`, ggf. auch
mehrere gleichzeitig, siehe unten), sowie - für die Schließen-Seite -
einen einzelnen, live berechneten Grund (`schliessgrund_live`): zuerst
Frost- und Hitzeschutz (aktuelle Außentemperatur gegen die konfigurierte
Grenze), dann Luftfeuchtigkeit, CO2, Temperatur gegen ihre jeweilige
Schließen-Schwelle, dann der Sommer-Fall ("Außen wärmer", aktuelle
Außentemperatur gegen die Öffnen-Schwelle selbst - die obere
Normalbereich-Grenze) und "Außenluft inzwischen feuchter"
(`outdoor_wetter`, absolute Außenluftfeuchtigkeit gegen die auf dieselbe
Weise umgerechnete Feuchtigkeits-Öffnen-Schwelle) - beide Male schließt
Lüften also erst, wenn die Außenluft selbst außerhalb des Normalbereichs
liegt, nicht schon, wenn sie nur wärmer/feuchter als die aktuelle (noch
im Normalbereich liegende) Innenluft ist. Die Dashboard-Karte liest diese
beiden Attribute nur noch aus, statt die Vergleiche selbst aus
Rohwerten/Schwellen nachzubauen.
Das funktioniert unabhängig davon, ob die Empfehlung schon einmal einen
echten Zustandswechsel hatte, und beschreibt immer den **aktuellen**
Zustand, nicht nur die Historie - wurde z. B. wegen eines längst
vorbeigezogenen Kälte-Einbruchs geschlossen und ist die Außentemperatur
inzwischen wieder deutlich über der Frostschutz-Grenze, oder wegen eines
inzwischen längst wieder abgekühlten "Außen wärmer"-Falls, zeigt der
Auslöser das nicht mehr an.
`letzter_grund` dient nur noch als **Rückfallwert** für den einen
verbleibenden Fall, der sich nicht live nachrechnen lässt: die
Winter-Höchstdauer (`duration` - dafür fehlen als Attribute noch die
Winter-Schwelle, die Höchstdauer selbst und das Prioritäts-Flag).
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

**Reihenfolge:** Zu Beginn der Karte (einmalig, vor der Raumliste) eine
**Übersichts-Tabelle** (🟢/🟠/🔴 als Spaltenköpfe, darunter zentriert die
Anzahl der Räume mit dem jeweiligen Icon-Status - Zählung identisch zum
Icon am jeweiligen Raumnamen weiter unten - gefolgt von - falls vorhanden -
einer Spalte "Integration" mit der aktuell installierten Versionsnummer
(`integration_version`, vom ersten Raum, für den das Attribut vorhanden ist)).
Die Raumliste selbst ist nach demselben Icon-Status
wie am Raumnamen sortiert (identisch zur Zählung in der Übersichts-
Tabelle): zuerst alle 🔴-Räume (echter Fenster-Mismatch, größter
Handlungsbedarf), danach alle 🟠-Räume (Fenster steht schon korrekt, aber
Werte noch außerhalb der Norm, oder Raum ohne Fenster), zuletzt alle
🟢-Räume (bereits gelöster Schließen-Grund oder gar kein Auslöser) -
innerhalb jeder der drei
Gruppen jeweils alphabetisch. Räume mit dem größten Handlungsbedarf
stehen so immer ganz oben, unabhängig vom Raumnamen. Pro Raum dann: Raumname →
**Empfehlungs-Tabelle** (Spalten: leer | Status |
Uhrzeit, darunter die beiden Zeilen "Fenster" und "Empfehlung" - nur für Räume mit Fenster; die erste
zeigt ausschließlich den Fensterzustand mit dem Zeitpunkt seiner letzten
tatsächlichen Änderung (Attribut `fenster_seit`, siehe unten; "–" ohne
konfigurierten Fensterkontakt), die zweite ausschließlich
die Empfehlung mit dem Zeitpunkt des letzten ECHTEN Empfehlungswechsels
(`letzter_wechsel`-Attribut, siehe "Attribute für eine Statusübersicht" -
bewusst nicht `last_changed` der Sensor-Entität selbst, das Home Assistant
bei jedem Neustart auf den Neustart-Zeitpunkt zurücksetzt) -
dadurch auf einen Blick erkennbar, ob die Fensteraktion vor oder nach dem
Empfehlungswechsel lag, z. B. um zu prüfen, ob eine fehlende
Benachrichtigung dadurch erklärbar ist (Fenster stand zum Zeitpunkt des
Wechsels bereits passend, siehe "Logik im Detail"). Beide Zeitstempel
zeigen nur die Uhrzeit ohne Datum, falls sie auf den heutigen Tag fallen.
**Fenster-Zeitpunkt über Neustarts (seit 0.90.1):** Das `last_changed` des
Fensterkontakt-Sensors springt bei jedem Neustart (Zustand "Nicht
verfügbar" und danach wieder "Geöffnet") auf den Neustart-Zeitpunkt. Deshalb
liest die Integration beim Start einmal je Raum die Zustandshistorie des
Fensterkontakts aus der Verlaufsdatenbank (Recorder, letzte 30 Tage) und
bestimmt daraus, seit wann das Fenster im aktuellen Zustand steht: Phasen
mit "Nicht verfügbar"/"Unbekannt" werden übersprungen (auf → nicht
verfügbar → auf bleibt der ursprüngliche Öffnungszeitpunkt). Spätere echte
Wechsel im Betrieb übernimmt die Integration direkt. Das Ergebnis steht im
Attribut `fenster_seit` (nur gesetzt, wenn bekannt). Ist die Zeit nicht
ermittelbar (Recorder nicht geladen, Fensterkontakt vom Recorder
ausgeschlossen, in 30 Tagen kein Wechsel), fehlt das Attribut, und die
Karte fällt auf das alte Verhalten zurück: Fällt bei mindestens drei Räumen
zeitgleich (auf die Minute gerundet) derselbe Fenster-Zeitstempel auf - ein
Anzeichen für einen gemeinsamen Neustart-Reset - wird "–" statt dieses
irreführenden Zeitstempels angezeigt. Ein Wechsel, der passiert, während Home
Assistant aus ist, bleibt unbekannt (angezeigt wird dann der Zeitpunkt nach
dem Start). Eine eigene
Auslöser-Spalte gibt es nicht mehr: Der Auslöser ergibt sich aus der
Werte-Tabelle darunter - bei Temperatur, Luftfeuchtigkeit und CO2 sind dort
**Bezeichnung und Wert** des auslösenden Eintrags gleich eingefärbt (siehe
"Hervorhebung des ausschlaggebenden Werts" oben; auch ein fehlender Messwert
färbt Bezeichnung und "–" orange). **Ausführliche Begründung (seit 0.92.1):** Unter
der Zeile "Empfehlung" steht, über die ganze Tabellenbreite, eine eigene Zeile mit
einem ausgeschriebenen Satz je aktuellem Grund (z. B. "Außen feuchter: Die Außenluft ist
absolut feuchter (14.4 g/m³ gegen 12.8 g/m³ innen), Lüften würde die Feuchtigkeit
erhöhen."). Sie erscheint nur, wenn aktuell ein Grund vorliegt; mehrere gleichzeitige
Öffnen-Gründe stehen untereinander. Die Texte nennen Messwerte und Grenzen, soweit die
Karte sie als Attribut kennt (bei Frost-/Hitzeschutz und Winter-Höchstdauer ohne Zahl).
Räume ohne Fenster haben diese Tabelle nicht und damit auch keine Begründungs-Zeile. Der
Auslöser wird live aus den aktuellen Werten/Schwellen berechnet. Solange dabei ein Auslöser vorliegt,
zeigt die Empfehlung "Öffnen"/"Schließen" entsprechend dem aktuellen Zustand;
liegt aktuell **kein** Auslöser vor ("Totzone", siehe
oben), zeigt die Zeile "Empfehlung" in Status und Uhrzeit "–" statt einer sonst
nicht mehr begründbaren Empfehlung. Das Icon am Raumnamen richtet sich danach, ob aktuell ein
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
`dusche_seit` berechnet), sonst "–"; die Spalte "Status/Grund" zeigt bei Luftentfeuchter/
Klimaanlage/Heizung eine rein informative, live bei jeder Neubewertung
berechnete Kurzbeschreibung, warum das Gerät gerade an/aus (bzw. bei der
Heizung: Comfort/Standby/Nacht bzw. "Zeitfenster: …" bei aktiviertem
Heizungs-Zeitplan) ist bzw. pausiert (u. a. auch "Sommerbetrieb aktiv" - der Vorsatz
"pausiert: " des Attributs wird in der Karte weggelassen, das Status-Icon zeigt
es bereits), ohne selbst Einfluss auf die Steuerung zu haben - siehe
`binary_sensor.py`; bei der Heizung ergänzt um die aktuelle Sollstellung in
Klammern (z. B. "Innentemperatur unter Schwelle, Comfort (Sollstellung: 21.0 °C)" oder
"Zeitfenster: Nacht (Sollstellung: 16.0 °C)"); bei Dusche entsprechend, ob und warum die
Duscherkennung aktuell anschlägt; seit 0.92.3 steht jeder Text in Klammern - Sollstellung,
"(Einspeiseleistung zu gering)", "(kein Comfort)", "(Start 07:42)" - in einer eigenen Zeile
unter dem Grund) → **Benachrichtigungen**
(ein-/ausklappbare Tabelle, standardmäßig eingeklappt, jetzt als letzter
Abschnitt pro Raum; zwei Spalten "Benachrichtigung | Ziele" (mehrere Ziele stehen jeweils in einer eigenen Zeile, ohne Komma, und sind einzeln antippbar), das Status-Icon
🟢/⚫ steht links vor dem Namen der Methode (Sprachausgabe, Push-Benachrichtigung, Persistente Benachrichtigung); bei schmaler Karte bricht der Methodenname an den Leerzeichen um, damit die Ziele-Spalte Platz behält).

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
des jeweiligen Werts).

### Einrichtung und Bedienung der Karte

Die Karte (`smart-climate-card.js`) ist eine eigenständige, in reinem
JavaScript geschriebene Lovelace-Custom-Card und lässt sich mit normalem CSS
gestalten. Sie liest alle Werte aus den Sensor-Attributen der Räume (siehe
"Attribute für eine Statusübersicht").

**Einrichtung:** Die Karte wird von der Integration selbst automatisch als
Lovelace-Ressource bereitgestellt - es ist **keine** eigene
`resources:`-Eintragung im Dashboard nötig. Nach der Installation/einem
Update einfach eine neue Karte anlegen und als Typ
`Custom: Smart Climate Karte` wählen (oder im YAML-Modus
`type: custom:smart-climate-card` eintragen) - ohne weitere Konfiguration
findet die Karte automatisch alle Räume über das `raum`-Attribut. Optional lässt sich ein Kartentitel vergeben
(`title:` im YAML-Modus, oder über das Textfeld im Karten-Editor - dafür
bringt die Karte einen eigenen, schlanken visuellen Editor mit) - leer
gelassen erscheint kein Titel, wie bisher.

Die Karte hat keine eigene Versionsanzeige - sie wird automatisch als
Lovelace-Ressource von der Integration selbst bereitgestellt und ist dadurch
immer auf demselben Stand wie die installierte Integration (die Übersicht
zeigt die Version der Integration).

**Lange Texte:** Sehr lange Texte in den Tabellen (Auslöser, Grund der
Geräte, Ziele der Benachrichtigungen) werden nach vier Zeilen automatisch
mit „…“ gekürzt - die Wörter selbst bleiben unverändert. Ein Tippen auf
den Text klappt ihn vollständig auf (nochmal tippen: wieder zu), am
Desktop zeigt zusätzlich ein Tooltip den ganzen Text. Der aufgeklappte
Zustand bleibt beim automatischen Aktualisieren der Karte erhalten.

**Absolute Luftfeuchtigkeit:** Ist „Luftfeuchtigkeit“ der Öffnen-Grund, wird
in der JS-Karte zusätzlich die Zeile „Abs. Luftfeuchtigkeit“ (innen und
außen) genauso hervorgehoben wie der Auslöser - der Vergleich der absoluten
Werte (Außenluft trockener) ist es, der das Öffnen freigibt. Fehlt ein
Wert, bleibt die Zeile unauffällig.

**Detailansicht per Klick:** In der JS-Karte lassen sich die **Bezeichnungen**
der Sensoren und Geräte antippen bzw. anklicken (wie sonst in Home Assistant
üblich) - es öffnet sich die Standard-Detailansicht (more-info, mit
Verlauf/Logbuch) der jeweiligen Entität: "Temperatur", "Luftfeuchtigkeit" und
"CO2" in den Messwert-Tabellen (Raum und Außen), die Kopfzellen "Fenster"
(Fensterkontakt) und "Empfehlung" (Empfehlungs-Sensor), die Gerätenamen
(Luftentfeuchter, Wassertank, Heizung, Dusche), der Wert unter "Modus" in der
Statuszeile (globaler Sommer-/Winterschalter) sowie die Ziele der
Benachrichtigungen. Die Werte selbst (z. B. "22,3 °C", "geöffnet") sind nicht
klickbar; klickbare Elemente zeigen nur den Mauszeiger, keine Unterstreichung.
Auch "Abs. Luftfeuchtigkeit" und "Taupunkt" sind klickbar (eigene Sensoren, siehe "Absolute Luftfeuchtigkeit als Sensor").
Die Entity-IDs liefert das Attribut `entitaeten` (nur die tatsächlich
konfigurierten).

**Außenwerte oben:** Da die Außenwerte für alle Räume gleich sind, zeigt die
JS-Karte sie einmal ganz oben unter der Statuszeile als vier Kacheln
(Titel "Außen-Messwerte": Temperatur, Luftfeuchtigkeit, absolute Luftfeuchtigkeit, Taupunkt;
Bezeichnung klein oben, Wert darunter; die Bezeichnungen sind antippbar und öffnen die
Detailansicht des jeweiligen Sensors). Die Kacheln stehen immer zu zweit nebeneinander (2 × 2); ab einer Kartenbreite
von etwa 620 px (bezogen auf die Karte selbst, nicht auf den Bildschirm) stehen
alle vier in einer Zeile. Ein Außensensor, der konfiguriert ist, aber gerade
keinen Wert liefert, zeigt ein oranges "–" (die Räume bleiben davon
unberührt). Die Messwert-Tabellen der einzelnen Räume haben dadurch
keine Spalte "Außen" mehr (Kopfzeile nur noch "Messwert" über Bezeichnung und Wert sowie "Normalbereich"; die Überschrift "Innen" entfällt, da klar ist, dass es der Innenwert ist) - die
Hervorhebung der Außenzelle bei "Außen wärmer/feuchter", Frost und Hitze
entfällt dort, der Auslöser steht weiter in der Empfehlungs-Zeile.

**Schriftgröße:** Die Tabellen und die Bezeichnungen der Außen-Kacheln verwenden die
normale Kartenschriftgröße (`1 em`, wie die Standardkarten von Home Assistant);
nur der Raumname und die Statuszeile sind etwas größer. Der farbige Streifen
links am Raum liegt hinter dem abgerundeten Rahmen und endet dadurch in den
runden Ecken.

**Fehlende Messwerte:** Liefert einer der konfigurierten Sensoren eines Raums
(Innentemperatur, Luftfeuchtigkeit, CO2) gerade keinen Wert (`nicht verfügbar`/
`unbekannt`), zeigt die Karte den Raum 🟠 (Rahmen orange, in der Übersicht bei
Orange mitgezählt, standardmäßig aufgeklappt) und den fehlenden Wert als oranges
"–". Ein 🔴-Raum (Fenster passt nicht zur Empfehlung) bleibt rot; das Orange
hebt nur einen sonst grünen Raum an. Nach einem Neustart von Home Assistant
kann ein Raum kurz orange erscheinen, solange seine Sensoren noch laden.

**Laufende Geräte (seit 0.91.0):** Läuft in einem Raum ein Luftentfeuchter oder eine
Klimaanlage (`luftentfeuchter_an`/`klimaanlage_an`, live vom Gerät gelesen), zeigt die
Karte den Raum ebenfalls 🟠 - ein 🔴-Raum bleibt rot, nur ein sonst grüner Raum wird
angehoben. Die Heizung zählt nicht dazu. In der Zeile "Dusche" der Gerätetabelle steht
in "Status/Grund" die letzte Startzeit ("Letzter Start 07:42", an einem anderen Tag mit
Datum; während der Dusche "Luftfeuchtigkeit steigt schnell (Start 07:42)").

**Statuszeilen für laufende Geräte (seit 0.92.4):** Solange ein Luftentfeuchter oder eine
Klimaanlage läuft, steht in der ersten Tabelle des Raums (unter "Fenster" und
"Empfehlung") eine Zeile "Luftentfeuchter" bzw. "Klimaanlage" mit Status "Aktiv" und der
Startzeit (heute nur Uhrzeit, sonst mit Datum; ohne bekannten Start "–"). Die bisherige
Zeile verschwindet, sobald das Gerät aus ist. Räume ohne Fenster haben die Tabelle nur
dann, wenn ein Gerät läuft (nur mit der Geräte-Zeile). Die Begründungs-Zeile bleibt
direkt unter "Empfehlung"; die Bezeichnung öffnet wie sonst die Detailansicht.

**Karten-Editor:** Neben dem Titel gibt es die Option "Räume mit Handlungsbedarf
(🟠/🔴) aufgeklappt anzeigen" (YAML: `expand_attention_rooms`, Standard `true`).
Ist sie aus (`expand_attention_rooms: false`), starten alle Räume eingeklappt;
grüne Räume sind ohnehin eingeklappt. Ein von Hand geänderter Zustand bleibt
erhalten, solange sich der Status des Raums nicht ändert; wird die Option
umgeschaltet, gilt sie sofort für alle Räume.

**Einschränkung:** Ohne eine echte Home-Assistant-Instanz zum Testen des
tatsächlichen Lovelace-Rendering ließ sich diese Karte nur über eine
simulierte DOM-Umgebung (jsdom) mit Beispieldaten gegen die dokumentierten
Szenarien (mehrere gleichzeitige Öffnen-Gründe, aufgelöster Schließen-Grund
bei fensterlosen Räumen, Frostschutz-Mismatch, Totzone-Neutralfall,
Laufzeit-Formatierung) verifizieren - echtes Home-Assistant-Frontend-
Verhalten (Rendering-Details, Registrierung als Lovelace-Ressource) bleibt
bis zu einer Rückmeldung aus der echten Oberfläche ungewiss.

## Fehlersuche / Diagnose

Drei Bordmittel helfen bei der Fehlersuche, ohne dass Werte oder
Log-Zeilen von Hand abgeschrieben werden müssen:

- **Diagnose herunterladen**: Bei jedem Eintrag (ein Raum oder
  "- Smart Climate Optionen -") lässt sich über das Drei-Punkte-Menü
  (⋮) → **Diagnose herunterladen** eine JSON-Datei erzeugen. Sie enthält
  die Konfiguration dieses Eintrags (personenbezogene Anwesenheits-/
  Notify-Ziel-Entitäten sind darin automatisch geschwärzt), bei einem
  Raum zusätzlich den aktuellen Entitäts-Zustand samt aller Attribute
  sowie eine Momentaufnahme (Zustand + Attribute) aller referenzierten
  Roh-Sensoren - Innentemperatur-Quelle, Luftfeuchtigkeit, CO2,
  Fensterkontakt sowie die globale Außentemperatur/-luftfeuchtigkeit. Bei
  den globalen Einstellungen zusätzlich für jedes App-Benachrichtigungsziel
  mit hinterlegter Anwesenheits-Entität eine Momentaufnahme von deren
  Zustand und Zeitpunkt der letzten Änderung (ohne die Entity-ID oder
  weitere Attribute) - nützlich, um zu erkennen, ob ein Push wegen
  "Person/Gerät nicht zuhause" übersprungen wurde (dieser Fall wird sonst
  nur mit Debug-Logging sichtbar).
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
- **Push-Verlauf und Test-Push** (bei "Ich bekomme keine Push-
  Benachrichtigung"): Jede Lüftungsempfehlung-Entität hat das Attribut
  `push_verlauf` (Entwicklerwerkzeuge → Zustände, sowie in der
  Diagnose-Datei) mit den letzten acht Push-Entscheidungen, neueste
  zuerst, jeweils mit Uhrzeit: `gesendet an notify.…`, `FEHLER beim
  Senden an …` (mit der echten Fehlermeldung), `übersprungen …:
  Anwesenheits-Entität steht auf 'not_home'`, `nicht gesendet: App-Push
  ist wirksam deaktiviert`, `nicht gesendet: keine notify-Entität
  konfiguriert` sowie `keine Benachrichtigung: Fensterkontakt zeigt
  bereits den Zielzustand` bzw. `bewusst still` - also genau die Fälle,
  in denen früher stillschweigend nichts passiert ist. Dieselben
  Einträge stehen auch im normalen Log (Level `info`, bei Fehlern
  `warning`). Der Verlauf wird nicht über einen Neustart hinweg gespeichert.
  Mit der Aktion **Smart Climate: Test-Push senden**
  (`ha_smart_ventilation.send_test_push`, Ziel: die Lüftungsempfehlung
  des Raums) lässt sich außerdem jederzeit eine Test-Nachricht über
  exakt denselben Sendeweg an alle App-Push-Ziele des Raums schicken -
  auch wenn Push für den Raum deaktiviert oder die Person nicht zuhause
  ist. Der Verlauf nennt dann zusätzlich, ob eine **echte**
  Benachrichtigung jetzt gesendet würde; ein Sendefehler kommt als
  Fehlermeldung direkt zurück. Kommt der Test-Push an, eine echte
  Benachrichtigung aber nie, liegt es an einer der im Verlauf genannten
  Bedingungen (nicht am Zustellweg).

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
- **Sprachausgabe-Nachtruhe**: Optionales Zeitfenster (global oder pro Raum,
  Standard aus, Standard-Zeiten 22:00–07:00), in dem ausschließlich die
  Sprachausgabe unterdrückt wird - App-Push und persistente Benachrichtigung
  werden davon nicht beeinflusst. Betrifft auch die Tank-voll-Benachrichtigung
  (siehe unten).
- **Titel der Benachrichtigungen** (seit 0.80.2): App-Push und persistente
  Web-Benachrichtigung tragen den Raumnamen zuerst im Titel, danach die
  eigentliche Überschrift - z. B. "Wohnzimmer – Lüften",
  "Wohnzimmer – Wassertank", "Wohnzimmer – Fenster schließen" (Test-Push:
  "Wohnzimmer – Smart Climate Test"). So ist der Raum auch in der
  Push-Vorschau sofort erkennbar. Die Titel sind fest, nur der Nachrichtentext
  ist anpassbar. Die Sprachausgabe hat keinen Titel.
- **Sendeweg der App-Benachrichtigungen:** Der Home-Assistant-Dienst
  `notify.send_message` akzeptiert nur `message` und `title` - kein
  `data`-Feld mit `tag`. Die Integration ermittelt deshalb zum gewählten
  Companion-App-Ziel den klassischen Dienst `notify.mobile_app_<gerät>`
  (aus dem Gerätenamen bzw. dem Namen der notify-Entität) und ruft, wenn er
  existiert, diesen mit `tag` auf - nur so funktionieren Ersetzen und
  Auflösen ("Clean Notification", siehe unten). Findet sich kein solcher
  Dienst, geht die Nachricht über `notify.send_message` **ohne** `tag` raus:
  sie kommt an, wird aber nicht ersetzt/aufgelöst (ein Auflösen wird dann
  gar nicht erst gesendet). Welcher Weg genutzt wurde, steht im Attribut
  `push_verlauf` (siehe "Fehlersuche / Diagnose"). Vor Version 0.79.1 wurde
  fälschlich immer `notify.send_message` mit `tag` aufgerufen - Home
  Assistant lehnte das mit `not a valid option at 'data'` ab, sodass gar
  kein Push ankam.
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
  gewünschten Zustand erreicht. Das erfordert den Companion-App-Dienst
  `notify.mobile_app_<gerät>` (siehe "Sendeweg" oben) - deshalb ist die
  Auswahl beim App-Benachrichtigungsziel auf Companion-App-Entitäten
  eingeschränkt. Ein Sendefehler wird im `push_verlauf` und als Warnung
  mit der echten Fehlermeldung protokolliert, statt die Neubewertung
  fehlschlagen zu lassen.
- **Benachrichtigung bei vollem Wassertank**: Ist für einen Raum ein
  Tankstatus-Sensor konfiguriert UND die zugehörige Benachrichtigung
  aktiviert, löst ein Vollwerden des Tanks eine eigene Benachrichtigung über
  dieselben, für den Raum aktuell wirksamen Kanäle aus (eigener Text, eigener
  `tag`/eigene `notification_id`, unabhängig von der Lüftungsempfehlung) und
  löst sich nach demselben "Clean Notification"-Muster automatisch wieder
  auf, sobald der Tank wieder als "leer" gemeldet wird.
- **Fenster-Gerät-Konflikt melden** (Benachrichtigung): Ist für einen Raum die
  entsprechende Option aktiviert UND läuft dort ein konfigurierter
  Luftentfeuchter oder eine konfigurierte Klimaanlage bei offenem Fenster
  gegen ungünstigere Außenluft an, löst das eine eigene Benachrichtigung
  über dieselben, für den Raum aktuell wirksamen Kanäle aus (eigener Text
  mit `{raum}`/`{geraet}`-Platzhaltern, eigener `tag`/eigene
  `notification_id` je Gerät, unabhängig von der eigentlichen
  Lüftungsempfehlung - kann also auch dann auslösen, wenn diese gerade
  "aus"/neutral ist). Löst sich nach demselben "Clean Notification"-Muster
  automatisch wieder auf, sobald das Fenster geschlossen wird oder die
  Außenluft wieder hilft. Bewusst unabhängig von einem eventuellen
  Einspeiseleistungs-Überschuss - das Schließen hilft dem Gerät, sein Ziel
  tatsächlich zu erreichen, auch wenn der Betrieb gerade "kostenlos" ist.
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
