# Smart Lüftungsassistent für Home Assistant

Eine Custom Integration, die pro Raum überwacht, ob gelüftet werden sollte –
basierend auf der Innentemperatur (Attribut einer `climate`-Entität) und/oder
der Luftfeuchtigkeit. Bei einem Zustandswechsel wird automatisch per
**Sonos-Sprachausgabe** oder **Home Assistant App-Push** benachrichtigt.

## Was die Integration macht

Für jeden konfigurierten Raum wird eine Entität
`binary_sensor.lueften_empfohlen_<raum>` angelegt:

- **on** = Lüften wird empfohlen (Fenster sollte offen sein)
- **off** = Lüften kann beendet werden

Bei jedem Wechsel wird automatisch eine Sprachansage oder Push-Benachrichtigung
ausgelöst – ganz ohne zusätzliche Automationen. Du kannst den binary_sensor
zusätzlich in Dashboards, eigenen Automationen oder Skripten verwenden (z. B.
um motorisierte Fenster automatisch zu öffnen).

## Installation

### Über HACS (empfohlen)

1. HACS → Menü (⋮) → *Benutzerdefinierte Repositories*
2. Repository-URL eintragen (nachdem du dieses Verzeichnis z. B. auf GitHub
   hochgeladen hast), Kategorie **Integration** wählen
3. "Smart Lüftungsassistent" installieren
4. Home Assistant neu starten

### Manuell

1. Ordner `custom_components/smart_ventilation` in deinen
   Home-Assistant-Konfigurationsordner kopieren
   (`<config>/custom_components/smart_ventilation`)
2. Home Assistant neu starten

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach "Smart Lüftungsassistent" suchen
3. Formular pro Raum ausfüllen:
   - **Raumname**
   - **climate-Entität** (z. B. dein Heizkörperthermostat)
   - **Temperatur-Attribut** (Standard: `current_temperature` – im
     Entwicklerwerkzeuge-Bereich prüfen, falls dein Gerät ein anderes nutzt)
   - Optional: Luftfeuchtigkeits-Sensor, Außentemperatur-Sensor,
     Fensterkontakt
   - Schwellenwerte zum Öffnen/Schließen
   - Benachrichtigungsmethode: **Sonos** (+ Lautsprecher & TTS-Entität) oder
     **App** (+ Notify-Service-Name, z. B. `mobile_app_pixel7` – findest du
     unter *Entwicklerwerkzeuge → Aktionen* mit "notify.")
4. Für weitere Räume den Vorgang wiederholen (Integration erneut hinzufügen)

## Logik im Detail

- **Öffnen** wird empfohlen, wenn:
  - Innentemperatur ≥ "Schwelle zum Öffnen" **und** (keine Außentemperatur
    bekannt **oder** draußen kühler als drinnen), **oder**
  - Luftfeuchtigkeit ≥ "Schwelle zum Öffnen"
- **Schließen** wird empfohlen, wenn:
  - Innentemperatur ≤ "Schwelle zum Schließen", **oder**
  - Luftfeuchtigkeit ≤ "Schwelle zum Schließen"

## Hinweise

- Die Integration reagiert direkt auf Zustandsänderungen (kein Polling),
  daher sehr geringe Systemlast.
- Für Sonos wird der Standard-Service `tts.speak` verwendet – stelle sicher,
  dass eine TTS-Integration (z. B. Google Translate, Piper) eingerichtet ist.
- Diese Integration öffnet/schließt keine motorisierten Fenster automatisch –
  sie informiert nur. Falls du motorisierte Fenster hast, kannst du den
  `binary_sensor` als Trigger in einer eigenen Automation verwenden, um
  `cover.open_cover` / `cover.close_cover` aufzurufen.
