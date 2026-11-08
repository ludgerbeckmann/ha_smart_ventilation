# Einrichtung und Einstellungen

[← Zurück zur Übersicht](../README.md)

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
       **Höchstlaufzeit**-Felder (siehe ["Geräte-Steuerung"](geraete-und-heizung.md)): gelten
       nur für Luftentfeuchter/Klimaanlage, nicht für die Heizung (der
       Leistungssensor selbst ist nur in "- Smart Climate Optionen -"
       hinterlegbar, nicht pro Raum). Die Abschaltung wegen zu geringer
       Einspeisung richtet sich seit 0.91.0 nach dem tatsächlichen Gerätezustand:
       Sie gilt auch für ein von Hand oder von einer anderen Automation
       eingeschaltetes Gerät
     - **Duscherkennung** (Checkbox, Standard: aus; nur hier im Raum
       einstellbar, keine globale Einstellung) – siehe ["Duscherkennung"](logik.md)
       unter ["Logik im Detail"](logik.md). Die zugehörige **Anstiegs-Schwelle** und
       die **Duschdauer-Ansage** (ab wie vielen Minuten Sprachansage; nur
       Sprachausgabe) stehen direkt darunter. Optional steht dort ein
       **Duschtemperatur-Sensor** (seit 0.96.0), siehe ["Duscherkennung"](logik.md)
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
       ["Geräte-Steuerung"](geraete-und-heizung.md) weiter unten. Wird ignoriert, falls oben
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
       werden müsste. Details siehe ["Geräte-Steuerung"](geraete-und-heizung.md) weiter unten
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
       das jeweils aktive Profil (Comfort, Standby oder Nacht; je Profil nur
       eine **Startzeit**, getrennt nach Werktag und Wochenende, also sechs
       Zeitfelder) den jeweiligen Sollwert unabhängig von der Innentemperatur.
       Ein Profil gilt, bis ein anderes startet; ein leeres Feld heißt, dass
       dieses Profil nicht genutzt wird. Deaktiviert (Standard) gilt
       weiterhin die reine Schwellenwert-Logik des Abschnitts "Heizung".
       Details siehe ["Geräte-Steuerung"](geraete-und-heizung.md) weiter unten
     - **Dynamischer Auslöser** (nur pro Raum, ein Auslöser): eine Licht-,
       Schalter-, Binärsensor-, input_boolean-, Person- oder Geräte-Tracker-
       Entität, dazu **Profil bei Auslöser** (Standard Comfort),
       **Einschalt-Verzögerung** (Standard 5 min) und **Nachlaufzeit**
       (Standard 15 min). Siehe ["Geräte-Steuerung"](geraete-und-heizung.md) weiter unten
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
       App-Push und persistente Benachrichtigung laufen unverändert weiter.
       **Wiederholung beim Einschalten (seit 0.93.0):** Geht das Licht von
       **aus** auf **an** (ein Wechsel aus „nicht verfügbar" zählt nicht), werden
       offene Dinge per Sprachausgabe erneut angesagt, höchstens alle
       5 Minuten: erst „Wassertank voll" (sofern die Tank-Benachrichtigung
       aktiv ist und der Tank noch voll ist), dann die noch offene
       Lüftungsempfehlung - beides als eine Ansage. Öffnen-Empfehlung: solange das
       Fenster laut Kontakt noch nicht offen ist (ohne Kontakt zählt die
       Empfehlung selbst). Schließen-Empfehlung: nur mit Fensterkontakt, wenn das
       Fenster noch offen ist und schon vor dem Wechsel der Empfehlung geöffnet
       wurde; bewusst still bleibende Gründe (CO2, fehlender Frost-Sensor) werden
       nicht wiederholt. Nachtruhe unterdrückt auch diese Ansagen; die
       Erinnerung (Intervall) und die einmalige Duschdauer-Ansage bleiben
       unverändert
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
  drinnen – siehe eigener Abschnitt ["Absolute vs. relative
  Luftfeuchtigkeit"](logik.md) unten. Ohne diesen Sensor bleibt es beim bisherigen
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
  nötig, siehe ["Geräte-Steuerung"](geraete-und-heizung.md) unten). Steuert damit automatisch den
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
  Klimaanlage/Heizung, siehe ["Geräte-Steuerung"](geraete-und-heizung.md) unten). **An** = Sommerbetrieb
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
  Standard Nein) sowie sechs Startzeiten (Comfort/Standby/Nacht, je
  getrennt für Werktag und Wochenende) als raumweiter Standard - pro Raum
  überschreibbar wie jeder andere Parameter. Neue Installationen starten mit
  Comfort 06:00/08:00 und Nacht 22:00/23:00 (Werktag/Wochenende), Standby
  ist leer (nicht genutzt)

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

**Sprachausgabe ohne Werte (ab 0.95.0):** Die Durchsagen über die
media_player-Lautsprecher verwenden **nicht** diese einstellbaren Texte,
sondern allgemeine, fest eingebaute Sätze ohne Messwerte und Schwellen - z. B.
"Bitte das Fenster im Büro öffnen, weil die Luftfeuchtigkeit zu hoch ist."
oder "Bitte das Fenster im Büro wegen Frostgefahr wieder schließen." Das gilt
für alle Anlässe (Öffnen wegen Temperatur/Luftfeuchtigkeit/CO2, die acht
Schließen-Gründe, Erinnerung) und auch für die wiederholte Ansage beim
Einschalten des Lichts. App-Push und die dauerhafte Benachrichtigung
behalten die einstellbaren Texte mit `{wert}`/`{schwelle}`. Unverändert für
alle Kanäle gleich bleiben die Texte für Wassertank, Fenster-Gerät-Konflikt
und Duschdauer (diese nennt weiterhin die Minuten). Die allgemeinen
Sprachtexte sind nicht einstellbar; eigene Anpassungen der Texte oben wirken
daher nur noch auf Push und persistente Benachrichtigung. Der vollständige
gesprochene Text steht im Attribut `push_verlauf`.

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
