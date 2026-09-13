# Smart Ventilation für Home Assistant

Eine Custom Integration, die pro Raum überwacht, ob gelüftet werden sollte –
basierend auf der Innentemperatur, der Luftfeuchtigkeit und der
Außentemperatur. Bei einem Zustandswechsel wird automatisch per
**Sonos-Sprachausgabe** und/oder **Home Assistant App-Push** benachrichtigt.

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

Die Integration bringt ihr eigenes Icon mit
(`custom_components/ha_smart_ventilation/brand/icon.png` +
`icon@2x.png`, `logo.png`, `logo@2x.png`). Seit Home Assistant 2026.3
werden solche mitgelieferten Brand-Icons automatisch in den
Integrationen sowie in HACS angezeigt – eine separate Pull Request an
das `home-assistant/brands`-Repository ist für Custom Integrations
nicht mehr nötig.

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
   - **Raumname**
   - **Innentemperatur-Quelle**: eine `climate`-, `sensor`-, `number`- oder
     `input_number`-Entität
   - **Temperatur-Attribut**: immer sichtbar, vorausgewählt ist
     `current_temperature` (Auswahl aus Liste oder eigener Text möglich).
     Wird nur ausgewertet, wenn die gewählte Entität tatsächlich eine
     `climate`-Entität ist – bei `sensor`/`number`/`input_number` wird der
     Wert ignoriert und stattdessen direkt der Entitätszustand verwendet.
   - **Außentemperatur-Sensor** (Pflichtfeld – die Außentemperatur ist
     entscheidend dafür, ob Lüften überhaupt sinnvoll ist)
   - Optional: Luftfeuchtigkeits-Sensor, Fensterkontakt
   - Schwellenwerte zum Öffnen/Schließen
   - **Benachrichtigungsmethode(n)**: Sonos und/oder App – beides kann
     gleichzeitig aktiviert werden
4. **Folgeschritte** (erscheinen automatisch nur, wenn passend ausgewählt):
   - Bei "Sonos": eigener Schritt für Sonos-Lautsprecher + TTS-Entität
   - Bei "App": eigener Schritt für die `notify.*`-Entität (Dropdown mit
     allen verfügbaren Notify-Entitäten)
5. Für weitere Räume den Vorgang wiederholen (Integration erneut
   hinzufügen)

> Hinweis: Home-Assistant-Formulare können Felder nicht dynamisch während
> der Eingabe ein-/ausblenden. Deshalb ist die Reihenfolge so gelöst, dass
> die passenden Zusatzfelder direkt im nächsten Schritt nach der
> Methodenauswahl erscheinen – aber jeweils nur, wenn die zugehörige
> Methode wirklich ausgewählt wurde.

## Logik im Detail

- **Öffnen** wird empfohlen, wenn:
  - Innentemperatur ≥ "Schwelle zum Öffnen" **und** draußen kühler als
    drinnen (oder Außenwert gerade nicht verfügbar), **oder**
  - Luftfeuchtigkeit ≥ "Schwelle zum Öffnen"
- **Schließen** wird empfohlen, wenn:
  - Innentemperatur ≤ "Schwelle zum Schließen", **oder**
  - Luftfeuchtigkeit ≤ "Schwelle zum Schließen"

## Hinweise

- Die Integration reagiert direkt auf Zustandsänderungen (kein Polling),
  daher sehr geringe Systemlast.
- Für Sonos wird der Standard-Service `tts.speak` verwendet – stelle sicher,
  dass eine TTS-Integration (z. B. Google Translate, Piper) eingerichtet ist.
- Für App-Benachrichtigungen wird `notify.send_message` auf die gewählte
  notify-Entität aufgerufen (benötigt Home Assistant 2024.9 oder neuer).
- Diese Integration öffnet/schließt keine motorisierten Fenster automatisch –
  sie informiert nur. Falls du motorisierte Fenster hast, kannst du den
  `binary_sensor` als Trigger in einer eigenen Automation verwenden, um
  `cover.open_cover` / `cover.close_cover` aufzurufen.
