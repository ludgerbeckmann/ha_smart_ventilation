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
   Raum-Formular (ein einziger Schritt, keine Folgeseiten mehr)
3. **Hauptformular** ausfüllen:
   - **Raumname** (ganz oben)
   - **Abschnitt "Benachrichtigungsmethoden"**:
     - **Sprachausgabe** (Checkbox) – direkt darunter: **Lautsprecher**
       (`media_player`-Entitäten, z. B. Sonos, Mehrfachauswahl). Die
       TTS-Entität selbst kommt ausschließlich aus "Smart Ventilation
       Options" und ist hier nicht mehr auswählbar
     - **Home Assistant Companion App** (Checkbox) – direkt
       darunter: eine Liste von **Benachrichtigungszielen**. Pro Eintrag: eine
       `notify.*`-Entität (Pflicht, falls die Checkbox aktiv ist) und
       optional eine **Anwesenheits-Entität** (`person` oder
       `device_tracker`, individuell pro Ziel) – ist sie gesetzt, erhält
       genau dieses Ziel die Push-Nachricht nur, wenn die Person/das Gerät
       zuhause ist. Über "Hinzufügen" lassen sich beliebig viele Ziele
       ergänzen
     - **Persistente Benachrichtigung (Weboberfläche)** (Checkbox) – keine
       weiteren Felder nötig. Erstellt eine dauerhafte Benachrichtigung im
       Home-Assistant-Benachrichtigungsbereich (Glocken-Symbol), solange die
       Empfehlung aktiv ist, und löst sich automatisch wieder auf, sobald
       sie sich erledigt hat
     - Mindestens eine der drei Checkboxen muss aktiviert (und, falls nötig,
       vollständig ausgefüllt) sein
   - **Abschnitt "Sensoren"**:
     - **Innentemperatur**: eine `climate`-, `sensor`-, `number`- oder
       `input_number`-Entität
     - **Temperatur-Attribut**: immer sichtbar, vorausgewählt ist
       `current_temperature` (Auswahl aus Liste oder eigener Text möglich).
       Wird nur ausgewertet, wenn die gewählte Entität tatsächlich eine
       `climate`-Entität ist – bei `sensor`/`number`/`input_number` wird der
       Wert ignoriert und stattdessen direkt der Entitätszustand verwendet.
     - Optional: Luftfeuchtigkeit
     - **Dieser Raum hat kein Fenster** (Checkbox, Standard: aus): bei "an"
       werden nie Öffnen-/Schließen-Benachrichtigungen erzeugt – nützlich
       z. B. für fensterlose Flure/Kellerräume, bei denen nur Luftentfeuchter
       oder Klimaanlage anhand der Sensorwerte gesteuert werden sollen (siehe
       Abschnitt "Geräte" weiter unten). Die Geräte-Steuerung läuft davon
       unabhängig weiter, unabhängig vom Fenster-Status. Bei "an" ist auch
       keine Benachrichtigungsmethode mehr zwingend erforderlich
     - **Fensterkontakt** (optional; unterdrückt Benachrichtigungen, sobald
       das Fenster laut Sensor bereits im empfohlenen Zustand ist - siehe
       eigener Abschnitt unten; nur relevant, wenn "Dieser Raum hat kein
       Fenster" deaktiviert ist)
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
       optionale Raum-Overrides der in "- Smart Ventilation Optionen -"
       hinterlegten Werte (der Leistungssensor selbst ist nur dort
       hinterlegbar, nicht mehr pro Raum)
4. Für weitere Räume den Vorgang wiederholen (Integration erneut
   hinzufügen)

### Allgemeine Einstellungen ("- Smart Ventilation Optionen -")

Direkt beim ersten Start der Integration wird **automatisch**, ganz ohne
Zutun, ein zusätzlicher Eintrag namens **"- Smart Ventilation Optionen -"**
angelegt – er taucht unter **Einstellungen → Geräte & Dienste** neben
deinen Räumen auf. Dieser Eintrag erzeugt keine eigene Entität und keinen
eigenen Sensor; er dient ausschließlich als raumübergreifender Standard.

**Bearbeiten:** Beim Eintrag "- Smart Ventilation Optionen -" auf
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

Alle Zahlenfelder sind immer mit einem sinnvollen Standardwert vorausgefüllt
– wird ein Feld komplett geleert, greift beim Speichern automatisch wieder
dieser Standardwert.

> Home Assistant erlaubt es grundsätzlich, jeden Integrations-Eintrag über
> die Oberfläche zu löschen – das lässt sich nicht unterbinden. Löschst du
> "- Smart Ventilation Optionen -" trotzdem, wird er **automatisch sofort wieder
> neu angelegt** (mit den Standardwerten) – er soll ja immer vorhanden
> sein. Willst du ihn stattdessen dauerhaft loswerden, müsstest du die
> gesamte Integration deinstallieren oder den Eintrag manuell deaktivieren
> statt zu löschen.

**Zur Sortierung in der Integrationsliste:** Es gibt keinen zuverlässigen
Trick, um "- Smart Ventilation Optionen -" in der Liste an eine bestimmte
Stelle zu bringen. Ein früherer Versuch mit einer führenden Ziffer im
Namen hat sich als wirkungslos erwiesen – die Reihenfolge mehrerer
Einträge einer Integration richtet sich in Home Assistant offenbar nicht
zuverlässig nach dem Namen (mehrfach von Nutzern als "wirkt zufällig"
gemeldet), sondern vermutlich eher nach der Reihenfolge, in der die
Einträge angelegt wurden. Da "- Smart Ventilation Optionen -" meist erst nach
bereits bestehenden Räumen automatisch erzeugt wird, taucht er entsprechend
oft weiter unten auf. Eine nachträgliche Änderung ist darüber nicht
zuverlässig erreichbar.

## Bestehenden Eintrag bearbeiten

Ein bereits eingerichteter Raum – oder "- Smart Ventilation Optionen -" – lässt
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
> der Eingabe ein-/ausblenden. Die Felder für Sprachausgabe bzw. App im
> Abschnitt "Benachrichtigungsmethoden" sind deshalb immer sichtbar, werden
> aber nur ausgewertet, wenn die jeweilige Checkbox aktiviert ist.
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
- Innentemperatur ≤ "Schwelle zum Schließen" – *außer* es wird gerade noch
  aus Feuchtigkeitsgründen gelüftet (siehe "Vorrang der Luftfeuchtigkeit"
  unten), **oder**
- Luftfeuchtigkeit ≤ "Schwelle zum Schließen", **oder**
- **Sommer-Fall**: draußen ist mittlerweile mindestens um die Toleranz-Marge
  wärmer als drinnen – *außer* es wird gerade noch aus Feuchtigkeitsgründen
  gelüftet, **oder**
- **Winter-Höchstdauer**: es herrschen "Winter"-Bedingungen (Außentemperatur
  unter der Winter-Schwelle) **und** die Empfehlung ist bereits länger als die
  eingestellte Höchstdauer aktiv – *außer* die Einstellung "Luftfeuchtigkeit
  hat Vorrang vor Winter-Höchstdauer" ist aktiv (Standard) **und** es wird
  gerade noch aus Feuchtigkeitsgründen gelüftet, **oder**
- **Frostschutz**: die Außentemperatur ist auf/unter die Frostschutz-Grenze
  gefallen (greift sofort, unabhängig von allen anderen Bedingungen,
  **auch** falls noch aus Feuchtigkeitsgründen gelüftet wird - Frostschutz
  hat immer Vorrang)

**Vorrang der Luftfeuchtigkeit:** Reine Temperatur- und Winter-Höchstdauer-
Gründe schließen das Fenster nicht, solange die Luftfeuchtigkeit noch über
der "Schwelle zum Öffnen" liegt (und Lüften laut Außen-Luftfeuchtigkeits-
Vergleich noch helfen würde) - sonst würde direkt im Anschluss wieder eine
Öffnen-Empfehlung wegen der Feuchtigkeit folgen. Einzige Ausnahme:
Frostschutz hat immer Vorrang vor der Luftfeuchtigkeit.

**Konfigurierbare Priorität bei Winter-Höchstdauer:** Der neue Parameter
"Luftfeuchtigkeit hat Vorrang vor Winter-Höchstdauer" legt fest, wie
dieser Konflikt aufgelöst wird:
- **An (Standard)**: Luftfeuchtigkeit gewinnt – die Winter-Höchstdauer wird
  bei noch bestehendem Feuchtigkeits-Lüftungsbedarf ignoriert, das Fenster
  bleibt offen (Schimmelvermeidung vor Wärmeverlust-Begrenzung)
- **Aus**: die Winter-Höchstdauer wird strikt durchgesetzt, auch bei noch
  hoher Luftfeuchtigkeit (Wärmeverlust-Begrenzung vor Schimmelvermeidung)

In den globalen Einstellungen ("Smart Ventilation Optionen") als fester
Ja/Nein-Schalter, im Raum-Parameter-Abschnitt als Ja/Nein/Leer-Auswahl
(leer = globalen Wert verwenden). Frostschutz hat davon unabhängig immer
Vorrang, unabhängig von dieser Einstellung.

Die reine Temperatur-Schließbedingung berücksichtigt einen noch
bestehenden Feuchtigkeits-Lüftungsbedarf dagegen immer (nicht
konfigurierbar) - ein Schließen nur wegen erreichter Zieltemperatur,
gefolgt von einem sofortigen erneuten Öffnen wegen der Luftfeuchtigkeit,
ergäbe so gut wie nie Sinn.

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

## Fensterkontakt und Benachrichtigungen

Ist im Abschnitt "Sensoren" ein Fensterkontakt hinterlegt, wird sein
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

## Attribute für eine Statusübersicht

Jede `binary_sensor.lueften_empfohlen_<raum>`-Entität liefert zusätzlich zum
reinen Ein/Aus-Zustand folgende Attribute (sichtbar unter Entwicklerwerkzeuge
→ Zustände, oder nutzbar in eigenen Dashboards/Templates):

| Attribut | Bedeutung |
|---|---|
| `raum` | Raumname |
| `innentemperatur` | aktueller Messwert |
| `aussentemperatur` | aktueller Messwert (aus "Smart Ventilation Optionen") |
| `schwelle_temperatur_oeffnen` / `_schliessen` | aktuell wirksame Schwellenwerte (inkl. Raum-Override/globaler Fallback) |
| `luftfeuchtigkeit`, `schwelle_feuchtigkeit_oeffnen` / `_schliessen` | nur vorhanden, falls ein Luftfeuchtigkeits-Sensor hinterlegt ist |
| `aussen_luftfeuchtigkeit` | nur vorhanden, falls global gesetzt |
| `empfehlung_aktiv_seit` | Zeitpunkt, seit dem "Lüften empfohlen" aktiv ist |
| `letzter_grund` | Grund der letzten Empfehlungsänderung (`temp`, `humidity`, `frost`, `duration`, `outdoor_warmer`) |
| `letzte_benachrichtigung` | Zeitpunkt der letzten tatsächlich verschickten Benachrichtigung |
| `luftentfeuchter_an`, `klimaanlage_an` | nur vorhanden, falls die jeweiligen Geräte konfiguriert sind |
| `hat_fenster` | nur vorhanden (mit Wert `false`), falls "Dieser Raum hat kein Fenster" aktiviert ist |

Der Standard-Entitätszustand selbst (`last_changed`) zeigt außerdem, seit
wann der aktuelle Öffnen/Schließen-Status gilt.

### Beispiel-Dashboard-Karte (Statusübersicht aller Räume)

Eine **Markdown-Karte** mit folgendem Inhalt zeigt automatisch alle Räume
mit Status, aktuellen Werten, Schwellenwerten und letzter Änderung – ganz
ohne zusätzliche Custom Cards:

```yaml
type: markdown
title: Lüftungsübersicht
content: >
  {% set grund_text = {'temp': 'Temperatur', 'humidity': 'Luftfeuchtigkeit',
     'frost': 'Frostschutz', 'duration': 'Winter-Höchstdauer',
     'outdoor_warmer': 'Außen wärmer'} %}
  {% for s in states.binary_sensor
     | selectattr('attributes.raum', 'defined')
     | sort(attribute='attributes.raum') %}
  {% set humidity_line = ('\n| 💧 Feuchte | ' ~ (s.attributes.luftfeuchtigkeit | round(0) | string if s.attributes.luftfeuchtigkeit is not none else '–') ~ ' % | ' ~ (s.attributes.schwelle_feuchtigkeit_oeffnen | string) ~ ' % | ' ~ (s.attributes.schwelle_feuchtigkeit_schliessen | string) ~ ' % |') if s.attributes.luftfeuchtigkeit is defined else '' %}
  {% set dehum_text = ('💨 Luftentfeuchter ' ~ ('🟢 an' if s.attributes.luftentfeuchter_an else '⚪ aus')) if s.attributes.luftentfeuchter_an is defined else '' %}
  {% set ac_text = ('❄️ Klimaanlage ' ~ ('🟢 an' if s.attributes.klimaanlage_an else '⚪ aus')) if s.attributes.klimaanlage_an is defined else '' %}
  {% set sep = ' · ' if (dehum_text and ac_text) else '' %}
  {% set devices_text = dehum_text ~ sep ~ ac_text %}
  {% set devices_line = ('\n\nGeräte: ' ~ devices_text) if devices_text else '' %}
  {% set grund = grund_text.get(s.attributes.letzter_grund, s.attributes.letzter_grund) if s.attributes.letzter_grund is defined else '' %}
  {% set entry = '### ' ~ ('🟢 Öffnen' if s.state == 'on' else '⚪ Zu') ~ ' — ' ~ s.attributes.raum ~ '\n\n| | Wert | Öffnen ab | Schließen ab |\n|---|---|---|---|\n| 🌡️ Temperatur | ' ~ (s.attributes.innentemperatur | round(1) | string if s.attributes.innentemperatur is not none else '–') ~ ' °C | ' ~ (s.attributes.schwelle_temperatur_oeffnen | string) ~ ' °C | ' ~ (s.attributes.schwelle_temperatur_schliessen | string) ~ ' °C |' ~ humidity_line ~ devices_line ~ '\n\nZuletzt geändert: ' ~ relative_time(s.last_changed) ~ (' (' ~ grund ~ ')' if grund else '') %}
  {{ ('\n\n<hr>\n\n' if not loop.first else '') ~ entry }}
  {% endfor %}
```

Einfügen über **Dashboard bearbeiten → Karte hinzufügen → Markdown** (im
YAML-Modus den obigen Inhalt einfügen). Die Karte findet Räume automatisch
über das `raum`-Attribut - neue Räume erscheinen ohne weitere Anpassung.
Die "Geräte"-Zeile erscheint nur bei Räumen, bei denen tatsächlich ein
Luftentfeuchter und/oder eine Klimaanlage konfiguriert ist. Sowohl die
Zeilenumbrüche als auch die Raum-Trennung (`<hr>` statt `---`) sind
bewusst **als Teil des Textinhalts** in die `~`-Verkettung eingebettet,
nicht als Leerzeilen im Vorlagentext - damit ist die Karte unabhängig
davon, wie Home Assistants Jinja-Umgebung Vorlagen-Whitespace behandelt.

## Hinweise

- Die Integration reagiert direkt auf Zustandsänderungen (kein Polling),
  daher sehr geringe Systemlast. Die angezeigten Attribute (aktuelle
  Temperatur/Luftfeuchtigkeit etc.) werden bei jeder Neubewertung aktuell
  gehalten - auch wenn sich der Empfehlungsstatus selbst dabei nicht
  ändert. **Ausnahme:** Die Außentemperatur kommt
  ausschließlich aus "- Smart Ventilation Optionen -" und wird beim Start jedes
  Raums direkt mitverfolgt – ändert sich aber die dort hinterlegte
  Sensor-**Auswahl** selbst (nicht nur ihr Messwert), wirkt sich das erst
  beim nächsten 5-Minuten-Tick des Raums aus. Dasselbe gilt für den
  Leistungssensor, falls dieser nur global (nicht zusätzlich im Raum)
  gesetzt ist.
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
