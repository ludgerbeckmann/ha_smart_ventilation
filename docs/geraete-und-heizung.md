# Geräte-Steuerung und Heizung

[← Zurück zur Übersicht](../README.md)

## Geräte-Steuerung (Luftentfeuchter/Klimaanlage/Heizung/Sommer-/Winterbetrieb)

Optional kann pro Raum ein Luftentfeuchter, eine Klimaanlage und/oder eine
Heizung hinterlegt werden, die automatisch gesteuert werden:

- **Luftentfeuchter**: an bei Luftfeuchtigkeit ≥ "Schwelle zum Öffnen", aus
  bei ≤ "Schwelle zum Schließen" - grundsätzlich unabhängig vom
  Fenster-Status. Eine Ausnahme: Meldet der Fensterkontakt-Sensor das
  Fenster als **offen**, pausiert der Luftentfeuchter, sofern die Außenluft
  dabei nicht absolut trockener ist als die Innenluft (derselbe Vergleich
  wie bei der Öffnen-Empfehlung wegen Luftfeuchtigkeit, siehe ["Absolute vs.
  relative Luftfeuchtigkeit"](logik.md) unten) - sonst würde er nur gegen ständig
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

  Ist der Zeitplan **aktiviert**, erzwingt stattdessen das aktuell aktive
  **Profil** den Sollwert **unabhängig von der Innentemperatur**: Comfort
  setzt den **Comfort-Sollwert**, Standby den **Standby-Sollwert**, Nacht den
  **Nacht-Sollwert**. Jedes Profil hat nur eine **Startzeit** (je einmal für
  Werktage und einmal fürs Wochenende, da sich z. B. der Aufstehzeitpunkt am
  Wochenende typischerweise verschiebt); das Ende ergibt sich dadurch, dass
  ein anderes Profil startet. Es gilt das Profil mit der zuletzt erreichten
  Startzeit, vor der ersten Startzeit des Tages das zuletzt gestartete Profil
  vom Vortag (in der Nacht auf Samstag also noch das der Freitag-Zeiten). Ein
  leeres Feld heißt: Dieses Profil wird nicht genutzt; ist gar keine
  Startzeit gesetzt, ändert der Zeitplan nichts. Beim Update bleiben die
  bisherigen Comfort-/Nacht-Startzeiten erhalten, die früheren Endzeiten
  werden nicht mehr gelesen (hatte jemand eine Lücke zwischen zwei Fenstern,
  die bisher Standby war, gilt dort jetzt das vorherige Profil weiter - dafür
  eine Standby-Startzeit setzen). Die "Heizungs-Schwelle" selbst bleibt bei
  aktiviertem Zeitplan ohne Wirkung.

  **Manuelle Übersteuerung:** Ändert jemand den Preset bzw. Sollwert von Hand
  (oder eine andere Automation tut es), behält die Integration diesen Wert, bis
  die Regeln einen anderen Modus verlangen (z. B. das nächste Zeitplan-Profil
  startet), längstens 24 Stunden. Ein Handeingriff wird nur erkannt, wenn das
  Gerät den zuletzt von der Integration gesendeten Wert vorher bestätigt hatte
  - ein nie angekommener Funkbefehl wird weiter wiederholt. Fenster offen und
  Sommerbetrieb beenden die Übersteuerung sofort. Anwesenheit (kein Comfort)
  hebt eine bewusste manuelle Wahl nicht auf. Die Erkennung erfolgt bei der
  nächsten Neubewertung (spätestens nach 5 Minuten). Das Attribut
  `heizung_uebersteuert` zeigt den Zustand, `heizung_grund` den Text
  "manuell geändert (bleibt bis zum nächsten Moduswechsel)".

  **Dynamischer Auslöser:** Ist für den Raum eine Auslöser-Entität gewählt (z. B.
  das Licht im Homeoffice-Büro oder die Person im Schlafzimmer), gilt das
  gewählte Profil, solange sie "an" bzw. "zuhause" ist - und **ersetzt** dabei
  Zeitplan bzw. Schwellenwert-Logik. Er greift erst, wenn er die
  Einschalt-Verzögerung lang ununterbrochen aktiv war, und wirkt nach seinem
  Ende noch für die Nachlaufzeit (gegen Flackern). Unbekannt/nicht verfügbar
  zählt als nicht aktiv. Rangfolge: Fenster offen/Sommerbetrieb, dann manuelle
  Übersteuerung, dann Auslöser, dann Zeitplan/Schwelle; "niemand zuhause" macht
  weiterhin aus Comfort ein Standby. Nach einem Neustart beginnt die
  Einschalt-Verzögerung neu. `heizung_grund` zeigt "Auslöser aktiv: Comfort".

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

  **Ferien-/Werktagssensor - ebenfalls nur ein Comfort-Verbot:** In den
  globalen Einstellungen (Abschnitt "Heizung") kann ein
  **Ferien-/Werktagssensor** (`binary_sensor`, `input_boolean` oder
  `schedule`) hinterlegt werden. **"Comfort erlaubt, wenn Sensor"** (An/Aus)
  legt fest, bei welchem Zustand Comfort normal genutzt wird: **An** für
  einen Ferien-Sensor (Ferien = an: Comfort normal, Ferien = aus: nur
  Standby), **Aus** für einen Werktag-Sensor (Werktag = an: kein Comfort,
  Werktag = aus: Comfort normal). **"Sensor für alle Räume nutzen"**
  (global, Standard Nein) und die Raum-Option **"Ferien-/Werktagssensor
  nutzen"** (Ja/Nein/leer = global) bestimmen, welche Räume den Sensor
  beachten - nur dort wird ein ermittelter Comfort-Zielmodus auf Standby
  herabgestuft, wenn der Sensor Comfort sperrt; Nacht, Standby und
  Gebäudeschutz laufen unverändert (auch eine per Hand gesetzte Comfort-
  Wahl bleibt bestehen, wie bei der Anwesenheit). Das gilt auch für
  Auslöser und Zeitplan. Ist der Sensor unbekannt/nicht verfügbar, heizt der
  Raum normal weiter. `heizung_grund` zeigt "Ferien-/Werktagssensor (kein
  Comfort)", das Attribut `heizung_comfort_gesperrt` den aktuellen Stand
  (nur gesetzt, wenn der Raum den Sensor berücksichtigt). Die Auswertung
  läuft bei jeder Neubewertung (spätestens im 5-Minuten-Takt).

- **Raumtypen (ab 1.14.0):** Im Abschnitt "Heizung" eines Raums wählen Sie
  einen **Raumtyp** (Wohnzimmer, Schlafzimmer, Kinderzimmer, Büro, Küche, Bad).
  Der Typ belegt **Comfort-/Standby-/Nacht-Temperatur** und die **sechs
  Startzeiten** des Heizungs-Zeitplans (Werktag/Wochenende) mit
  Richtwerten vor. Rangfolge: **Raum-Override, dann Raumtyp, dann globale
  Einstellung, dann Standard** - ein im Raum selbst eingetragener Wert schlägt
  den Raumtyp, der Raumtyp schlägt die globalen Werte. Nichts wird beim
  Speichern eingefroren: ändern Sie den Typ oder seine Werte, wirkt das auf
  alle Räume mit diesem Typ. Mit Raumtyp gelten für die Startzeiten
  ausschließlich die des Typs; ein Profil, das der Typ nicht nennt, wird nicht
  genutzt (kein Durchfall auf die globalen Startzeiten). Ohne Raumtyp ändert
  sich nichts. Der Raumtyp wirkt nur auf Heizungs-Temperaturen und
  Zeitplan-Startzeiten (nicht auf Schwelle, Lüftungswerte oder die
  Nutzungserkennung).

  | Raumtyp | Comfort / Standby / Nacht | Startzeiten Werktag / Wochenende |
  |---|---|---|
  | Wohnzimmer | 21 / 18 / 17 °C | Comfort 06:30 / 08:00, Nacht 23:00 / 23:30 |
  | Schlafzimmer | 19 / 17 / 16 °C | Comfort 06:00 / 08:00, Nacht 21:30 / 22:30 |
  | Kinderzimmer | 21 / 18 / 18 °C | Comfort 06:30 / 08:00, Nacht 20:30 / 21:00 |
  | Büro | 21 / 17 / 16 °C | Comfort 07:30 / -, Standby 18:00 / 00:00 |
  | Küche | 20 / 17 / 16 °C | Comfort 06:30 / 08:00, Standby 21:30 / 22:30 |
  | Bad | 23 / 18 / 17 °C | Comfort 06:00 / 08:00, Standby 08:00 / 10:00, Nacht 22:00 / 23:00 |

  **Werte anpassen:** In "Smart Climate Optionen" im Abschnitt **"Raumtypen"**
  den Raumtyp unter "Raumtyp bearbeiten" wählen und speichern - danach öffnet
  sich ein Formular mit den Werten dieses Typs (vorbelegt mit dem aktuell
  wirksamen Wert). Gespeichert werden nur Abweichungen vom Standard des Typs;
  ein leeres Zeitfeld heißt "Profil nicht genutzt"; die Checkbox "Auf
  Standard des Typs zurücksetzen" verwirft die Anpassungen dieses Typs. Für
  weitere Typen die Einstellungen erneut öffnen. Spätere Änderungen der
  Richtwerte in einem Update lassen Ihre gespeicherten Anpassungen unberührt.

- **Nutzungserkennung (lernende Heizzeiten, ab 1.13.0):** Im Abschnitt
  "Heizungs-Zeitplan" eines Raums wählen Sie unter **"Nutzungs-Signale"** ein
  oder mehrere Lichter (später auch Präsenzsensoren). Die Integration lernt
  daraus, in welchen Stunden der Raum an **Werktagen** und am **Wochenende**
  genutzt wird. Als genutzt zählt eine Stunde, wenn mindestens ein Signal an
  war und - falls unter "Heizung" Personen für die Anwesenheit hinterlegt
  sind - mindestens eine Person nicht bestätigt abwesend war. Ferientage
  (Ferien-/Werktagssensor sperrt Comfort) zählen wie Wochenende. Beim Start
  werden bis zu 28 Tage aus dem Verlauf (Recorder) nachgeladen, danach wird
  laufend ergänzt; die Daten liegen lokal im Speicher von Home Assistant
  (`.storage`), nicht in Attributen. Es ist einfache Statistik, kein
  Machine Learning: nachvollziehbar und ohne Trainingsphase.
  - **Vorschlagsmodus (Standard):** Es wird nur gelernt und angezeigt - im
    Raum-Dialog und in der Geräte-Tabelle steht z. B. "Gelernte Nutzung:
    Werktag 7–8 und 15–22 Uhr (nur Anzeige)". Die Heizung ändert sich nicht.
  - **"Gelernte Zeiten verwenden" = Ja** (global Standard Nein, pro Raum
    überschreibbar): In typischerweise genutzten Stunden gilt Comfort, sonst
    Standby. Das ersetzt den Zeitplan, sobald genug gelernt wurde
    (**Mindest-Lernzeit**, Standard 14 Tage, und mindestens 2 Vergleichstage
    der jeweiligen Stunde); bis dahin gilt weiter Zeitplan bzw.
    Schwellenwert-Logik. Eine Stunde gilt als genutzt, wenn der Raum an
    mindestens **40 %** (**Nutzungs-Schwelle**) der Vergleichstage genutzt
    wurde.
  - **Rangfolge:** Fenster offen, Sommerbetrieb, manuelle Übersteuerung und
    der dynamische Auslöser haben Vorrang; ein aktives **Nacht-Profil des
    Zeitplans** bleibt bestehen; Anwesenheit und Ferien-/Werktagssensor
    stufen Comfort wie gewohnt auf Standby herab. Frost-/Gebäudeschutz bleibt
    unberührt. `heizung_grund` zeigt z. B. "Gelernt: genutzt (7 von 10
    Werktagen)".
  - Attribute: `nutzung_lerntage`, `nutzung_aktiv`,
    `nutzung_gelernt_werktag`, `nutzung_gelernt_wochenende` (nur mit
    konfigurierter Heizung und Nutzungs-Signalen). Der Dienst
    `ha_smart_ventilation.reset_usage_learning` (Ziel: die
    Lüftungsempfehlung des Raums) verwirft das Gelernte.

- **Heizungsart und Vorheizen (ab 1.15.0):** Im Abschnitt "Heizung" eines
  Raums (nur pro Raum) wählen Sie die **Heizungsart**: **Heizkörper** oder
  **Fußbodenheizung** (eine Fußbodenheizung ist deutlich träger). Mit
  Heizungsart beginnt **Comfort** - im Zeitplan wie in der gelernten Nutzung -
  um die **Vorheizzeit früher** als die Startzeit. Vorgezogen wird nur
  Comfort; Standby, Nacht und Gebäudeschutz beginnen nicht früher. Fenster
  offen, Sommerbetrieb, manuelle Übersteuerung, Anwesenheit und
  Ferien-/Werktagssensor haben weiter Vorrang, der dynamische Auslöser
  (Licht/Person) wird nicht vorgeheizt. Ohne Heizungsart ändert sich nichts.
  - **Feste Vorheizzeit:** Vorbelegung **20 Min. (Heizkörper)** bzw.
    **120 Min. (Fußbodenheizung)**; im Feld "Vorheizzeit" überschreibbar
    (leer oder 0 = Vorbelegung).
  - **Automatisch lernen (Standard an):** Die Integration misst jeden
    Aufheizlauf auf Comfort (mindestens 30 Min. und 0,5 K Anstieg, Ende bei
    Erreichen des Sollwerts; Läufe mit offenem Fenster oder manueller
    Änderung zählen nicht). Aus dem **Median der letzten 10 Läufe** (ab 2
    Läufen) ergibt sich die Aufheizrate in K/h. Die Vorheizzeit ist dann
    `(Comfort-Sollwert − Ist-Temperatur) ÷ Rate × 1,1`, höchstens 6 Stunden,
    und wird bei jeder Neubewertung neu gerechnet (ist der Raum schon warm,
    entfällt sie). Bis genug Läufe vorliegen, gilt die feste Vorheizzeit. Die
    Außentemperatur fließt nicht ein. Der Dienst `reset_usage_learning`
    verwirft auch die Aufheizrate.
  - `heizung_grund` zeigt "Zeitplan: Vorheizen (Comfort beginnt in X Min.)"
    bzw. "Gelernt: Vorheizen (...)". Attribute: `heizung_vorheizzeit` (Minuten,
    nur mit Heizungsart) und `heizung_aufheizrate` (K/h, sobald gelernt).
  - **Tipp Fußbodenheizung:** Standby-/Nacht-Sollwert nur wenig unter Comfort
    legen - eine tiefe Absenkung lohnt wegen der Trägheit kaum und kostet
    beim Wiederaufheizen viel. Das wird nicht erzwungen.
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
