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
3. Formular pro Raum ausfüllen:
   - **Raumname**
   - **Innentemperatur-Quelle**: eine `climate`-, `sensor`-, `number`- oder
     `input_number`-Entität
   - **Außentemperatur-Sensor** (Pflichtfeld – die Außentemperatur ist
     entscheidend dafür, ob Lüften überhaupt sinnvoll ist)
   - Optional: Luftfeuchtigkeits-Sensor, Fensterkontakt
   - Schwellenwerte zum Öffnen/Schließen
   - **Benachrichtigungsmethode(n)**: Sonos und/oder App – beides kann
     gleichzeitig aktiviert werden
   - Je nach Auswahl: Sonos-Lautsprecher + TTS-Entität und/oder eine
     `notify.*`-Entität (wird per Dropdown aus allen verfügbaren
     Notify-Entitäten ausgewählt)
4. **Nur wenn du eine climate-Entität gewählt hast**, folgt ein zweiter
   Schritt: Auswahl des Temperatur-Attributs. Vorausgewählt ist
   `current_temperature`; du kannst aus der Liste wählen oder einen
   eigenen Attributnamen eintippen. Bei sensor-, number- oder
   input_number-Entitäten entfällt dieser Schritt, da direkt der
   Entitätszustand als Temperatur verwendet wird.
5. Für weitere Räume den Vorgang wiederholen (Integration erneut
   hinzufügen)

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
