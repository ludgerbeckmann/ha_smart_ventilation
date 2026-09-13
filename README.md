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

## Icon

Die Integration bringt ihr eigenes Icon mit – an zwei Stellen, für zwei
unterschiedliche Zwecke:

- `custom_components/ha_smart_ventilation/brand/` – wird seit Home Assistant
  2026.3 automatisch für die normale Home-Assistant-Oberfläche genutzt
  (Einstellungen → Geräte & Dienste, Entitäten, etc.). Eine separate Pull
  Request an das `home-assistant/brands`-Repository ist dafür nicht mehr
  nötig.
- `brand/` im Repository-Wurzelverzeichnis – wird zusätzlich von **HACS
  selbst** erwartet (für den HACS-Store und den Download-Dialog), laut
  [HACS-Dokumentation](https://www.hacs.xyz/docs/publish/integration/).

Beide Ordner enthalten dieselben Dateien (`icon.png`, `icon@2x.png`,
`logo.png`, `logo@2x.png`).

> Hinweis: Auch mit beiden Ordnern korrekt vorhanden kann es aktuell
> vorkommen, dass HACS im Store/Download-Dialog trotzdem "icon not
> available" anzeigt – das liegt an einem bekannten, noch offenen Fehler in
> der HACS-Oberfläche (siehe
> [hacs/integration#5171](https://github.com/hacs/integration/issues/5171)
> und [#5223](https://github.com/hacs/integration/issues/5223)), bei dem
> HACS weiterhin eine veraltete CDN-Adresse statt der lokalen Icons abfragt.
> In der normalen Home-Assistant-Oberfläche wird das Icon davon nicht
> beeinträchtigt.

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

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach "Smart Ventilation" suchen
3. **Hauptformular** pro Raum ausfüllen:
   - **Benachrichtigungsmethoden** (ganz oben, eigenständig): Sprachausgabe
     und/oder Home Assistant Companion App – beides kann gleichzeitig
     aktiviert werden
   - **Raumname**
   - **Abschnitt "Sensoren"**:
     - **Innentemperatur**: eine `climate`-, `sensor`-, `number`- oder
       `input_number`-Entität
     - **Temperatur-Attribut**: immer sichtbar, vorausgewählt ist
       `current_temperature` (Auswahl aus Liste oder eigener Text möglich).
       Wird nur ausgewertet, wenn die gewählte Entität tatsächlich eine
       `climate`-Entität ist – bei `sensor`/`number`/`input_number` wird der
       Wert ignoriert und stattdessen direkt der Entitätszustand verwendet.
     - **Außentemperatur** (Pflichtfeld – entscheidend dafür, ob Lüften
       überhaupt sinnvoll ist)
     - Optional: Luftfeuchtigkeit, Fensterkontakt
   - **Abschnitt "Geräte" (optional, eingeklappt)**:
     - **Luftentfeuchter**: eine `switch`- oder `humidifier`-Entität
     - **Klimaanlage**: eine `climate`- oder `switch`-Entität
     - **Fenstersperre / Rollladen** (optional): eine `cover`- **oder**
       `switch`-Entität, die beim Einschalten der Klimaanlage herunter- und
       beim Ausschalten wieder hochfährt. Bei einer `switch`-Entität bedeutet
       "an" = herunterfahren + gesperrt, "aus" = hochfahren + entsperrt
     - **Leistungssensor** (optional): z. B. aktuelle Einspeiseleistung
     - **Mindest-Einspeiseleistung**: nur relevant, wenn ein Leistungssensor
       gewählt ist – blockiert das Einschalten, bis genug Überschuss da ist
     - **Verzögerung bis Abschalten**: nur relevant, wenn ein Leistungssensor
       gewählt ist – ein bereits laufendes Gerät wird erst nach dieser Zeit
       dauerhaft zu geringer Einspeisung abgeschaltet
   - **Abschnitt "Parameter"**:
     - Schwellenwerte zum Öffnen/Schließen – Zahlenfelder mit
       Pfeil-hoch/-runter-Steuerung, vorausgefüllt mit einem sinnvollen
       Standardwert. Wird ein Feld komplett geleert, greift beim Speichern
       automatisch wieder der Standardwert (24 °C / 21 °C bzw. 60 % / 50 %)
4. **Folgeschritte** (erscheinen automatisch nur, wenn passend ausgewählt):
   - Bei "Sprachausgabe": eigener Schritt für **einen oder mehrere** Lautsprecher
     (`media_player`-Entitäten, z. B. Sonos) + eine TTS-Entität (gilt für alle
     gewählten Lautsprecher)
   - Bei "Home Assistant Companion App": eigener Schritt für **eine oder
     mehrere** `notify.*`-Entitäten (Dropdown mit Mehrfachauswahl, z. B. um
     mehrere Familienmitglieder oder Geräte gleichzeitig zu benachrichtigen)
5. Für weitere Räume den Vorgang wiederholen (Integration erneut
   hinzufügen)

## Bestehenden Raum bearbeiten

Ein bereits eingerichteter Raum lässt sich jederzeit nachträglich anpassen,
ohne ihn zu löschen und neu anzulegen:

1. **Einstellungen → Geräte & Dienste → Smart Ventilation**
2. Beim gewünschten Raum-Eintrag auf **Konfigurieren** klicken
3. Es öffnet sich derselbe mehrstufige Ablauf wie beim Einrichten, diesmal
   mit den aktuell gespeicherten Werten vorausgefüllt
4. Nach dem Speichern wird der Raum automatisch mit den neuen Einstellungen
   neu geladen – ein manueller Neustart von Home Assistant ist dafür nicht
   nötig

> Hinweis: Home-Assistant-Formulare können Felder nicht dynamisch während
> der Eingabe ein-/ausblenden. Deshalb ist die Reihenfolge so gelöst, dass
> die passenden Zusatzfelder direkt im nächsten Schritt nach der
> Methodenauswahl erscheinen – aber jeweils nur, wenn die zugehörige
> Methode wirklich ausgewählt wurde.

## Logik im Detail

**Öffnen** wird empfohlen, wenn (und Frostschutz nicht greift):
- Innentemperatur ≥ "Schwelle zum Öffnen" **und** draußen mindestens um die
  Toleranz-Marge kühler ist als drinnen, **oder**
- Luftfeuchtigkeit ≥ "Schwelle zum Öffnen"

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
  daher sehr geringe Systemlast.
- Für die Sprachausgabe wird der Standard-Service `tts.speak` verwendet – das
  funktioniert mit jeder `media_player`-Entität, nicht nur mit Sonos. Stelle
  sicher, dass eine TTS-Integration (z. B. Google Translate, Piper)
  eingerichtet ist.
- Für App-Benachrichtigungen wird `notify.send_message` auf die gewählte
  notify-Entität aufgerufen (benötigt Home Assistant 2024.9 oder neuer).
- Diese Integration öffnet/schließt keine motorisierten Fenster automatisch –
  sie informiert nur. Falls du motorisierte Fenster hast, kannst du den
  `binary_sensor` als Trigger in einer eigenen Automation verwenden, um
  `cover.open_cover` / `cover.close_cover` aufzurufen.
