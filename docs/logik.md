# Logik im Detail

[← Zurück zur Übersicht](../README.md)

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

**Eigener Temperatursensor für die Duscherkennung (seit 0.96.0):** Im
Raum-Formular lässt sich optional ein **Duschtemperatur-Sensor** wählen (z. B.
direkt in der Dusche oder am Feuchtesensor), falls er empfindlicher reagiert
als die Raum-Temperatur. Er ersetzt NUR für die Duscherkennung (Temperatur-
Anstieg und Ende, siehe unten) die Raum-Temperatur; Lüften, Frostschutz und
Heizung nutzen weiter die Temperaturquelle aus dem Abschnitt "Sensoren". Ohne
Auswahl ändert sich nichts. Fällt der gewählte Sensor aus, greifen die
Temperatur-Kriterien nicht (kein Rückfall auf die Raum-Temperatur, damit sich
zwei Quellen mit unterschiedlicher Empfindlichkeit nicht im Verlauf mischen);
Feuchte-Kriterien und der Fenster-Rückfall wirken weiter. Die Schwellen (0,3 °C
Anstieg bzw. Absinken) wurden nicht angepasst - ob sie für den empfindlicheren
Sensor passen, zeigt der Betrieb (Attribut `dusche_verlauf` nennt den
verwendeten Sensor).

**Schnelleres Ende der Dusche (seit 0.93.2):** Das 10-Minuten-Fenster allein
erkennt das Ende erst viele Minuten nach dem Ausschalten (der Anstieg steckt
noch im Fenster). Deshalb gilt eine laufende Dusche zusätzlich als beendet,
(a) wenn die Luftfeuchtigkeit seit 3 Minuten keinen neuen Höchstwert mehr
erreicht hat oder 2 Punkte unter ihren Höchstwert gefallen ist - **nicht**,
solange der Feuchtesensor gesättigt ist (Höchstwert ab 97 %, typisch
99 %: dort sind Plateau und Absinken nicht erkennbar) - oder (b) wenn die
Raumtemperatur, die während der Dusche um mindestens 0,3 °C gestiegen ist,
0,3 °C unter ihren Höchstwert fällt (hilft bei gesättigtem Feuchtesensor, ein
Temperatursensor mit grober Auflösung oder ohne erkennbaren Anstieg wird
dafür nicht genutzt). Ohne eines dieser Signale gilt weiterhin das alte
Verhalten. Während einer laufenden Dusche wird jede Minute neu bewertet
(sonst nur bei Sensoränderung bzw. alle 5 Minuten). Nach einem Ende wird
der Verlauf verworfen; eine neue Dusche braucht wieder einen echten Anstieg.
Das Protokoll `dusche_verlauf` nennt beim Ende den Grund (z. B. "Temperatur
22.2 °C fiel unter den Höchstwert 22.5 °C" oder "Anstieg unter der
Schwelle").

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
