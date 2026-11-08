# Sensoren und Attribute

[← Zurück zur Übersicht](../README.md)

## Entitäten pro Raum

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

Ist für einen Raum die **Duscherkennung** aktiviert (siehe ["Duscherkennung" unter "Logik im Detail"](logik.md)), wird zusätzlich eine eigene Entität "**‹Raum›
Dusche aktiv**" angelegt - ein reiner, vom Haupt-Sensor abgeleiteter
Anzeige-Sensor ohne eigene Konfiguration, der **on** meldet, solange
gerade geduscht wird (identisch zum weiterhin vorhandenen
`duschen_erkannt`-Attribut des Haupt-Sensors, nur eben als eigenständige
Entität für Dashboards/Automationen) - Symbol `mdi:shower` bei **on**,
`mdi:shower-head` bei **off**.

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

## Raumstatus als Sensor (Ampel 🟢/🟠/🔴)

Zusätzlich zur Karte gibt es je Raum einen eigenen Sensor
`sensor.<raum>_raumstatus` mit der Ampel des Raums als Zustand:

| Zustand | Ampel | Bedeutung |
|---|---|---|
| `ok` | 🟢 | Nichts zu tun (oder ein bereits gelöster Fall) |
| `hinweis` | 🟠 | Aufmerksamkeit nötig, aber kein Fehler - z. B. Raum ohne Fenster, Fenster passt schon und die Werte normalisieren sich noch, ein Messwert fehlt, ein Luftentfeuchter/eine Klimaanlage läuft |
| `handlungsbedarf` | 🔴 | Das Fenster passt nicht zur Empfehlung |

Die Ampel wird einmal im Raum-Binärsensor berechnet (Attribut `raumstatus`);
die Dashboard-Karte und dieser Sensor zeigen nur das Ergebnis - die Farben der
Karte und des Sensors sind dadurch immer identisch.

- Das **Symbol** wechselt mit dem Zustand (Häkchen / Ausrufezeichen im Kreis /
  Warndreieck). Eine **Farbe** liefert der Sensor nicht - die bestimmt das
  Dashboard (siehe unten).
- Attribute: `raum`, `gruende` (Liste, was die Farbe bestimmt:
  `fenster_passt_nicht`, `wartet_auf_normalisierung`, `kein_fenster`,
  `keine_fensterinfo`, `messwert_fehlt`, `geraet_laeuft`), `ausloeser`
  (aktuell zutreffende Lüftungsgründe, z. B. `temp`, `humidity`, `co2`) und
  `lueften_empfohlen`.
- **Antippen:** Auf einem Dashboard öffnet ein Tipp auf die Entität die
  Standard-Detailansicht (Verlauf und Attribute). Soll ein Tipp stattdessen
  zu einer Raum-Seite navigieren, stellst du das in der jeweiligen Karte
  ein (`tap_action: navigate`).
- Der Sensor ist ein normaler Sensor mit festen Zuständen und lässt sich in
  Automationen nutzen, z. B. "Push, wenn ein Raum `handlungsbedarf` meldet".

Beispiel mit der Standard-Kachel (die Farbe ist dort fest, nicht pro Zustand):

```yaml
type: tile
entity: sensor.bad_raumstatus
state_content: state
tap_action:
  action: more-info
```

Soll die Kachel je Zustand eine andere Farbe haben, braucht es eine
Zusatzkarte, die Vorlagen kann (z. B. Mushroom-Template-Karte oder `card-mod`);
die Farbvorlagen hängen von der jeweiligen Karte ab und sind hier nicht
mitgeliefert. Nach dem Update ist ein Neustart von Home Assistant nötig (neue
Entität).

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
| `raumstatus` | Ampel des Raums: `ok` (🟢), `hinweis` (🟠) oder `handlungsbedarf` (🔴) - einmal hier berechnet, von der Dashboard-Karte und dem Sensor `sensor.<raum>_raumstatus` nur angezeigt (siehe "Raumstatus als Sensor") |
| `raumstatus_gruende` | Liste der Gründe, die die Ampel bestimmen (`fenster_passt_nicht`, `wartet_auf_normalisierung`, `kein_fenster`, `keine_fensterinfo`, `messwert_fehlt`, `geraet_laeuft`) |
| `taupunkt` / `aussen_taupunkt` | Taupunkt in °C (Magnus-Formel), nur wenn Temperatur und Feuchte vorliegen und die Feuchte > 0 % ist - nur für die Anzeige in der JS-Karte |
| `absolute_luftfeuchtigkeit` / `aussen_absolute_luftfeuchtigkeit` | berechnete absolute Luftfeuchtigkeit (g/m³, siehe ["Absolute vs. relative Luftfeuchtigkeit"](logik.md)) - nur vorhanden, wenn die jeweils nötigen Temperatur-/Feuchtigkeitswerte verfügbar sind. Genau diese Werte entscheiden, ob Lüften bei hoher Innen-Luftfeuchtigkeit tatsächlich empfohlen wird |
| `empfehlung_aktiv_seit` | Zeitpunkt, seit dem "Lüften empfohlen" aktiv ist |
| `fenster_seit` | Zeitpunkt, seit dem der Fensterkontakt im aktuellen Zustand (auf/zu) steht - aus der Verlaufsdatenbank gelesen, übersteht Neustarts (siehe Dashboard-Karte, "Fenster-Zeitpunkt über Neustarts"). Nur gesetzt, wenn bekannt |
| `letzter_wechsel` | Zeitpunkt des letzten ECHTEN Empfehlungswechsels (nur bei tatsächlichem Zustandswechsel neu gesetzt, über Neustarts hinweg korrekt erhalten) - anders als `last_changed` der Entität selbst, das Home Assistant bei jedem Neustart auf den Neustart-Zeitpunkt zurücksetzt. Von der Dashboard-Karte für die "Uhrzeit"-Spalte der Empfehlung verwendet, statt sich auf das irreführende `last_changed` zu verlassen |
| `letzter_grund` | Grund der letzten Empfehlungsänderung (`temp`, `humidity`, `co2`, `frost`, `heat`, `duration`, `outdoor_warmer`, `outdoor_wetter`) - fehlt ein Außentemperatur-Wert (Sensor gerade `unavailable`/`unknown`), schließt der Frostschutz zwar vorsorglich, ohne dabei `letzter_grund` zu setzen (siehe ["Logik im Detail"](logik.md)) |
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
| `heizung_grund` | wie `luftentfeuchter_grund`/`klimaanlage_grund`, nur für die Heizung (z. B. "Innentemperatur unter Schwelle, Comfort", "Zeitplan: Nacht", "pausiert: Fenster offen", "pausiert: Sommerbetrieb aktiv") |
| `heizung_soll_modus` | der von der Integration gewollte Modus (`"comfort"`/`"standby"`/`"night"`/`"building_protection"`) - im Unterschied zu `heizung_modus`, das den Gerätezustand live liest. Bleibt bei einer manuellen Übersteuerung auf dem zuletzt gewollten Wert |
| `heizung_modus_seit` | Zeitpunkt, seit dem `heizung_soll_modus` gilt (Wechsel des gewollten Modus, per Neubewertung erkannt, also auf wenige Minuten genau; über Neustarts erhalten). Nach dem Update gilt zunächst der Zeitpunkt der ersten Auswertung |
| `heizung_verhindert` | nur vorhanden, wenn ein sonst gewollter Comfort herabgestuft wurde: `"anwesenheit"` oder `"ferien"` (Ferien-/Werktagssensor) |
| `nutzung_lerntage` / `nutzung_aktiv` / `nutzung_gelernt_werktag` / `nutzung_gelernt_wochenende` | Nutzungserkennung (nur mit Heizung und Nutzungs-Signalen): beobachtete Tage, ob das Gelernte die Heizung steuert, und die gelernten Nutzungszeiten (z. B. `7–8 und 15–22 Uhr`) |
| `heizung_seit` | wie `luftentfeuchter_seit`/`klimaanlage_seit` - Zeitpunkt, seit dem `heizung_an` ununterbrochen `true` ist |
| `heizung_uebersteuert` | nur vorhanden (`true`), solange ein manueller Eingriff in Preset/Sollwert gilt (siehe "Manuelle Übersteuerung"); `heizung_uebersteuerung_seit` (Zeitpunkt) und `heizung_uebersteuerung_basis` (Regel-Zielmodus zum Zeitpunkt des Eingriffs) dienen der Wiederherstellung nach einem Neustart |
| `heizung_letzte_laufzeit` | wie `luftentfeuchter_letzte_laufzeit`/`klimaanlage_letzte_laufzeit`, nur für die Heizung |
| `sommermodus_an` | nur vorhanden, falls in "- Smart Climate Optionen -" ein Sommer-/Winterbetrieb-Schalter hinterlegt ist UND diese Entität aktuell im Zustandsautomaten existiert - `true`/`false`, live vom Schalter gelesen. Identisch für jeden Raum, da es sich um eine hausweite, nicht raumspezifische Einstellung handelt |
| `hat_fenster` | nur vorhanden (mit Wert `false`), falls "Dieser Raum hat kein Fenster" aktiviert ist |
| `sprachausgabe_aktiv`, `sprachausgabe_lautsprecher` | nur vorhanden, wenn der Raum mindestens einen Lautsprecher ausgewählt hat |
| `app_aktiv`, `app_ziele` | nur vorhanden, wenn App-Benachrichtigung effektiv aktiv ist |
| `persistent_aktiv` | nur vorhanden, wenn persistente Web-Benachrichtigung effektiv aktiv ist |
| `duschen_erkannt` | nur vorhanden, wenn Duscherkennung effektiv aktiv ist; `true`, solange die Luftfeuchtigkeit schneller als die Anstiegs-Schwelle steigt (siehe ["Duscherkennung"](logik.md) unter ["Logik im Detail"](logik.md)) |
| `entitaeten` | Entity-IDs der angezeigten Werte/Geräte (`innentemperatur`, `luftfeuchtigkeit`, `co2`, `aussentemperatur`, `aussen_luftfeuchtigkeit`, `fenster`, `luftentfeuchter`, `luftentfeuchter_tank`, `klimaanlage`, `heizung`, `sommermodus`, `dusche`, `absolute_luftfeuchtigkeit`, `aussen_absolute_luftfeuchtigkeit`, `taupunkt`, `aussen_taupunkt`) - nur die konfigurierten bzw. vorhandenen. Die JS-Karte öffnet damit per Klick die Detailansicht (more-info) |
| `integration_version` | aktuell installierte Version der Integration (aus `manifest.json`) - identisch für jeden Raum, dient nur der Dashboard-Karte zur Anzeige der Versionsnummer |

Der Standard-Entitätszustand selbst (`last_changed`) zeigt außerdem, seit
wann der aktuelle Öffnen/Schließen-Status gilt.
