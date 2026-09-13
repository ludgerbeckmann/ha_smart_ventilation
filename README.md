# Smart Ventilation für Home Assistant

Eine Custom Integration, die pro Raum überwacht, ob gelüftet werden sollte –
basierend auf der Innentemperatur, der Luftfeuchtigkeit und der
Außentemperatur. Bei einem Zustandswechsel wird automatisch per
**Sprachausgabe** (z. B. Sonos, oder jede andere `media_player`-Entität) und/oder
**Home Assistant App-Push** benachrichtigt.

## Was die Integration macht

Für jeden konfigurierten Raum wird eine Entität
`binary_sensor.lueften_empfohlen_<raum>` angelegt:

- **on** = Lüften wird empfohlen (Fenster sollte offen sein)
- **off** = Lüften kann beendet werden

Bei jedem Wechsel wird automatisch eine Sprachansage und/oder Push-
Benachrichtigung ausgelöst – ganz ohne zusätzliche Automationen. Du kannst
den binary_sensor zusätzlich in Dashboards, eigenen Automationen oder
Skripten verwenden (z. B. um motorisierte Fenster automatisch zu öffnen).

## Installation

### Über HACS (empfohlen)

1. HACS → Menü (⋮) → *Benutzerdefinierte Repositories*
2. Repository-URL eintragen (nachdem du dieses Verzeichnis z. B. auf GitHub
   hochgeladen hast), Kategorie **Integration** wählen
3. "Smart Ventilation" installieren
4. Home Assistant neu starten

### Manuell

1. Ordner `custom_components/ha_smart_ventilation` in deinen
   Home-Assistant-Konfigurationsordner kopieren
   (`<config>/custom_components/ha_smart_ventilation`)
2. Home Assistant neu starten

## Einrichtung

### Raum hinzufügen

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach "Smart Ventilation" suchen – es öffnet sich direkt das
   Raum-Formular
3. **Hauptformular** ausfüllen:
   - **Raumname** (ganz oben)
   - **Benachrichtigungsmethoden**: Sprachausgabe und/oder Home Assistant
     Companion App – beides kann gleichzeitig aktiviert werden
   - **Abschnitt "Sensoren"**:
     - **Innentemperatur**: eine `climate`-, `sensor`-, `number`- oder
       `input_number`-Entität
     - **Temperatur-Attribut**: immer sichtbar, vorausgewählt ist
       `current_temperature` (Auswahl aus Liste oder eigener Text möglich).
       Wird nur ausgewertet, wenn die gewählte Entität tatsächlich eine
       `climate`-Entität ist – bei `sensor`/`number`/`input_number` wird der
       Wert ignoriert und stattdessen direkt der Entitätszustand verwendet.
     - Optional: Luftfeuchtigkeit, Fensterkontakt
   - **Abschnitt "Parameter"** (optional, standardmäßig eingeklappt –
     **überschreibt** für diesen Raum die allgemeinen Einstellungen; leer
     gelassen gilt der dort hinterlegte Wert):
     - Schwellenwerte zum Öffnen/Schließen sowie Toleranz-Marge,
       Frostschutz-Grenze, Winter-Schwelle, Winter-Höchstdauer und
       Erinnerungsintervall – Zahlenfelder mit Pfeil-hoch/-runter-Steuerung
   - **Abschnitt "Geräte" (optional, standardmäßig eingeklappt, am Ende des
     Formulars)**:
     - **Luftentfeuchter**: eine `switch`- oder `humidifier`-Entität
     - **Klimaanlage**: eine `climate`- oder `switch`-Entität
     - **Fenstersperre / Rollladen** (optional): eine `cover`- **oder**
       `switch`-Entität, die beim Einschalten der Klimaanlage herunter- und
       beim Ausschalten wieder hochfährt. Bei einer `switch`-Entität bedeutet
       "an" = herunterfahren + gesperrt, "aus" = hochfahren + entsperrt
     - **Mindest-Einspeiseleistung** / **Verzögerung bis Abschalten**:
       optionale Raum-Overrides der in "Smart Ventilation Options"
       hinterlegten Werte (der Leistungssensor selbst ist nur dort
       hinterlegbar, nicht mehr pro Raum)
4. **Folgeschritte** (erscheinen automatisch nur, wenn passend ausgewählt):
   - Bei "Sprachausgabe": eigener Schritt für **einen oder mehrere** Lautsprecher
     (`media_player`-Entitäten, z. B. Sonos) + optional eine **eigene**
     TTS-Entität für diesen Raum (leer = TTS-Entität aus "Smart Ventilation
     Options")
   - Bei "Home Assistant Companion App": eigener Schritt mit einer Liste von
     **Notify-Zielen**. Pro Eintrag: eine `notify.*`-Entität (Pflicht) und
     optional eine **Anwesenheits-Entität** (`person` oder `device_tracker`,
     individuell pro Ziel). Ist bei einem Eintrag eine Anwesenheits-Entität
     gesetzt, erhält genau dieses Ziel die Push-Nachricht nur, wenn die
     Person/das Gerät zuhause ist - andere Ziele ohne Anwesenheits-Entität
     erhalten sie weiterhin immer. So lässt sich z. B. konfigurieren: "an
     Person A nur, wenn sie zuhause ist" und gleichzeitig "an Person B immer".
     Über "Hinzufügen" lassen sich beliebig viele Ziele ergänzen.
5. Für weitere Räume den Vorgang wiederholen (Integration erneut
   hinzufügen)

### Allgemeine Einstellungen ("Smart Ventilation Options")

Direkt beim ersten Start der Integration wird **automatisch**, ganz ohne
Zutun, ein zusätzlicher Eintrag namens **"Smart Ventilation Options"**
angelegt – er taucht unter **Einstellungen → Geräte & Dienste** neben
deinen Räumen auf. Dieser Eintrag erzeugt keine eigene Entität und keinen
eigenen Sensor; er dient ausschließlich als raumübergreifender Standard.

**Bearbeiten:** Beim Eintrag "Smart Ventilation Options" auf
**Konfigurieren** (Zahnrad-Symbol) klicken. Zwei Abschnitte:

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
  die Lautsprecher **vor** der Ansage gesetzt werden
- **Vorhandene Wiedergabe beim Ansagen**: "Überlagern" (Standard) spielt die
  Ansage direkt über eine laufende Wiedergabe; "Pausieren" pausiert sie vorher
- **Leistungssensor**: wird für **alle** Räume verwendet – ist nicht mehr
  im Raum-Formular auswählbar
- **Mindest-Einspeiseleistung** + **Verzögerung bis Abschalten**:
  Standardwerte für alle Räume, die keine eigenen Werte festlegen (die
  Werte selbst bleiben pro Raum überschreibbar, siehe Geräte-Abschnitt
  im Raum-Formular)

**Abschnitt "Parameter"**:
- Der komplette Schwellenwerte-/Lüftungs-Parameter-Satz (dieselben Felder
  wie im Raum-Parameter-Abschnitt) als raumweiter Standard

Der **Name dieses Eintrags lässt sich hier bewusst nicht ändern** – dafür
gibt es keinen praktischen Bedarf. Alle Zahlenfelder sind immer mit einem
sinnvollen Standardwert vorausgefüllt – wird ein Feld komplett geleert,
greift beim Speichern automatisch wieder dieser Standardwert.

> Home Assistant erlaubt es grundsätzlich, jeden Integrations-Eintrag über
> die Oberfläche zu löschen – das lässt sich nicht unterbinden. Löschst du
> "Smart Ventilation Options" trotzdem, wird er **automatisch sofort wieder
> neu angelegt** (mit den Standardwerten) – er soll ja immer vorhanden
> sein. Willst du ihn stattdessen dauerhaft loswerden, müsstest du die
> gesamte Integration deinstallieren oder den Eintrag manuell deaktivieren
> statt zu löschen.

**Zur Sortierung in der Integrationsliste:** Es gibt keinen zuverlässigen
Trick, um "Smart Ventilation Options" in der Liste an eine bestimmte
Stelle zu bringen. Ein früherer Versuch mit einer führenden Ziffer im
Namen hat sich als wirkungslos erwiesen – die Reihenfolge mehrerer
Einträge einer Integration richtet sich in Home Assistant offenbar nicht
zuverlässig nach dem Namen (mehrfach von Nutzern als "wirkt zufällig"
gemeldet), sondern vermutlich eher nach der Reihenfolge, in der die
Einträge angelegt wurden. Da "Smart Ventilation Options" meist erst nach
bereits bestehenden Räumen automatisch erzeugt wird, taucht er entsprechend
oft weiter unten auf. Eine nachträgliche Änderung ist darüber nicht
zuverlässig erreichbar.

## Bestehenden Eintrag bearbeiten

Ein bereits eingerichteter Raum – oder "Smart Ventilation Options" – lässt
sich jederzeit nachträglich anpassen, ohne ihn zu löschen und neu anzulegen:

1. **Einstellungen → Geräte & Dienste → Smart Ventilation** (bzw. der von
   dir vergebene Name)
2. Beim gewünschten Eintrag auf **Konfigurieren** klicken
3. Es öffnet sich das passende Formular, mit den aktuell gespeicherten
   Werten vorausgefüllt
4. Nach dem Speichern wird der Eintrag automatisch mit den neuen
   Einstellungen neu geladen – ein manueller Neustart von Home Assistant
   ist dafür nicht nötig

> Hinweis: Home-Assistant-Formulare können Felder nicht dynamisch während
> der Eingabe ein-/ausblenden. Deshalb ist die Reihenfolge so gelöst, dass
> die passenden Zusatzfelder direkt im nächsten Schritt nach der
> Methodenauswahl erscheinen – aber jeweils nur, wenn die zugehörige
> Methode wirklich ausgewählt wurde.
>
> Änderungen an den globalen Einstellungen wirken sich auf alle Räume ohne
> eigenen Override aus - allerdings nicht sofort, sondern spätestens beim
> nächsten 5-Minuten-Tick jedes Raums (kein sofortiger Reload aller
> Raum-Entitäten).

## Logik im Detail

**Öffnen** wird empfohlen, wenn (und Frostschutz nicht greift):
- Innentemperatur ≥ "Schwelle zum Öffnen" **und** draußen mindestens um die
  Toleranz-Marge kühler ist als drinnen, **oder**
- Luftfeuchtigkeit ≥ "Schwelle zum Öffnen" **und** (kein Außen-
  Luftfeuchtigkeitssensor hinterlegt **oder** es draußen **absolut**
  betrachtet trockener ist als drinnen – siehe "Absolute vs. relative
  Luftfeuchtigkeit" unten)

**Schließen** wird empfohlen, wenn:
- Innentemperatur ≤ "Schwelle zum Schließen", **oder**
- Luftfeuchtigkeit ≤ "Schwelle zum Schließen", **oder**
- **Sommer-Fall**: draußen ist mittlerweile mindestens um die Toleranz-Marge
  wärmer als drinnen – *außer* es wird gerade noch aus Feuchtigkeitsgründen
  gelüftet, **oder**
- **Winter-Höchstdauer**: es herrschen "Winter"-Bedingungen (Außentemperatur
  unter der Winter-Schwelle) **und** die Empfehlung ist bereits länger als die
  eingestellte Höchstdauer aktiv, **oder**
- **Frostschutz**: die Außentemperatur ist auf/unter die Frostschutz-Grenze
  gefallen (greift sofort, unabhängig von allen anderen Bedingungen)

**Zusätzlich:**
- **Frostschutz** verhindert außerdem grundsätzlich das Öffnen, solange die
  Außentemperatur auf/unter der Frostschutz-Grenze liegt
- **Erinnerung**: ist ein Erinnerungsintervall > 0 eingestellt, wird die
  Benachrichtigung wiederholt, solange die Empfehlung aktiv bleibt (z. B.
  falls das Fenster trotzdem nicht geöffnet wurde)
- Die **Toleranz-Marge** verhindert, dass die Empfehlung bei Außen-/
  Innentemperaturen nahe beieinander ständig zwischen "öffnen" und
  "schließen" hin- und herspringt

**Nicht berücksichtigt** (bewusst, aktuell außerhalb des Funktionsumfangs):
Regen und Windgeschwindigkeit.

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

## Geräte-Steuerung (Luftentfeuchter/Klimaanlage)

Optional kann pro Raum ein Luftentfeuchter und/oder eine Klimaanlage
hinterlegt werden, die automatisch gestartet und gestoppt werden:

- **Luftentfeuchter**: an bei Luftfeuchtigkeit ≥ "Schwelle zum Öffnen", aus
  bei ≤ "Schwelle zum Schließen" - unabhängig vom Fenster-Status.
- **Klimaanlage**: an, wenn Innentemperatur ≥ "Schwelle zum Öffnen" **und**
  Lüften nicht helfen würde (draußen nicht ausreichend kühler). Aus, sobald
  die Innentemperatur die "Schwelle zum Schließen" erreicht **oder** Lüften
  wieder ausreicht. Ergänzt damit gezielt die Fensterlogik, statt sie zu
  duplizieren: Wenn Lüften reicht, läuft keine Klimaanlage.
- **Leistungssensor (optional)**: Ist eine "Mindest-Einspeiseleistung"
  konfiguriert, wird ein Gerät nur eingeschaltet, wenn der Sensor mindestens
  diesen Wert meldet (z. B. um nur bei PV-Überschuss zu starten). Ohne
  Leistungssensor entfällt diese Bedingung komplett.
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

## Hinweise

- Die Integration reagiert direkt auf Zustandsänderungen (kein Polling),
  daher sehr geringe Systemlast. **Ausnahme:** Die Außentemperatur kommt
  ausschließlich aus "Smart Ventilation Options" und wird beim Start jedes
  Raums direkt mitverfolgt – ändert sich aber die dort hinterlegte
  Sensor-**Auswahl** selbst (nicht nur ihr Messwert), wirkt sich das erst
  beim nächsten 5-Minuten-Tick des Raums aus. Dasselbe gilt für den
  Leistungssensor, falls dieser nur global (nicht zusätzlich im Raum)
  gesetzt ist.
- Für die Sprachausgabe wird der Standard-Service `tts.speak` verwendet – das
  funktioniert mit jeder `media_player`-Entität, nicht nur mit Sonos. Stelle
  sicher, dass eine TTS-Integration (z. B. Google Translate, Piper)
  eingerichtet ist.
- **Lautstärke der Ansage**: `tts.speak` selbst unterstützt keine
  Lautstärkeangabe. Die in den globalen Einstellungen konfigurierte
  Lautstärke wird deshalb vorher separat per `media_player.volume_set`
  gesetzt und **danach nicht automatisch zurückgesetzt** - die Lautsprecher
  bleiben auf dieser Lautstärke stehen.
- **Pausieren vs. Überlagern**: Im Modus "Pausieren" wird die vorhandene
  Wiedergabe vor der Ansage pausiert, aber **nicht automatisch
  fortgesetzt** - ein zuverlässiges automatisches Fortsetzen ist
  plattformübergreifend (über alle `media_player`-Integrationen hinweg)
  nicht robust lösbar. "Überlagern" (Standard) spielt die Ansage einfach
  direkt über die laufende Wiedergabe.
- Für App-Benachrichtigungen wird `notify.send_message` auf die gewählte
  notify-Entität aufgerufen (benötigt Home Assistant 2024.9 oder neuer).
- Diese Integration öffnet/schließt keine motorisierten Fenster automatisch –
  sie informiert nur. Falls du motorisierte Fenster hast, kannst du den
  `binary_sensor` als Trigger in einer eigenen Automation verwenden, um
  `cover.open_cover` / `cover.close_cover` aufzurufen.
