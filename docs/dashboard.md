# Dashboard-Karte und Bubble-Card-Modul

[← Zurück zur Übersicht](../README.md)

## Dashboard-Karte (Statusübersicht aller Räume)

Die Integration bringt eine eigene Lovelace-Karte mit (`smart-climate-card`,
Einrichtung siehe "Einrichtung und Bedienung der Karte" weiter unten). Sie
zeigt automatisch alle Räume mit Status, aktuellen Werten, Schwellenwerten
und letzter Änderung. Die folgenden Abschnitte beschreiben, was die Karte
anzeigt und wie sie die Farben bestimmt.

**Hervorhebung des ausschlaggebenden Werts** (fette, farbige Schrift):
Hervorgehoben wird jeweils die Zelle mit der Maßeinheit zusammen (z. B. `34.2 °C`,
nicht nur `34.2`) - bei jedem aktiven Auslöser grundsätzlich **rot**,
mit Ausnahmen für Schließen-Gründe: Ein Schließen-Auslöser bedeutet per
Definition, dass der jeweilige Wert seine Schließen-Schwelle bereits
erreicht hat - das zugrunde liegende Problem (zu warm/zu feucht/zu viel
CO2) ist damit bereits gelöst, im Unterschied zu einem Öffnen-Auslöser,
bei dem der Wert noch außerhalb der Norm liegt und auf Normalisierung
"wartet". Deshalb: **grün**, wenn "CO2" der aktuelle Schließen-Auslöser
ist - ein niedriger CO2-Wert ist kein Sicherheitsrisiko (anders als
Frost-/Hitzeschutz), das Schließen dient nur der Ordnung, nicht der
Sicherheit (siehe ["Logik im Detail"](logik.md) unten), es besteht also kein
Handlungsbedarf, unabhängig vom tatsächlichen Fensterzustand; **grün**
auch, wenn Temperatur, Luftfeuchtigkeit oder "Außen wärmer"/
"Außen feuchter" der aktuelle Schließen-Auslöser ist UND das Fenster
bereits geschlossen ist (die Person hat also bereits reagiert) - anders
als bei CO2 kann Weiterlüften hier aber tatsächlich schaden (zu kalt/zu
feucht werden, oder bei "Außen wärmer"/"Außen feuchter" die Lage sogar
verschlimmern), daher gilt Grün hier NUR bei bereits passendem Fenster,
nicht unabhängig vom Fensterzustand wie bei CO2. Bleibt das Fenster bei
diesen vier Gründen dagegen noch offen (Fenster-Mismatch), zeigt die
Karte weiterhin normal **rot** - ein Handeln ist dann sehr wohl nötig;
**orange**, wenn das Fenster bereits genau so steht, wie es die aktuelle
Empfehlung vorsieht (die Person hat also bereits reagiert), die
zugrunde liegenden Werte sich aber noch nicht normalisiert haben - das
betrifft ausschließlich Öffnen-Auslöser (Temperatur/Luftfeuchtigkeit/
CO2 noch über ihrer Öffnen-Schwelle): hier ist ebenfalls kein weiteres
Handeln nötig, die Werte liegen aber (anders als beim Totzone-Fall)
tatsächlich noch außerhalb der Norm, daher nicht grün, sondern nur
orange. Bei Räumen ohne Fenster ("Dieser Raum hat kein Fenster"
aktiviert) gilt ebenfalls **orange**, unabhängig vom Auslöser, da sich
der Wert dort gar nicht durch Lüften beeinflussen lässt (höchstens
Luftentfeuchter/Klimaanlage reagieren automatisch). Rot bleibt damit auf
den Fall beschränkt, in dem tatsächlich noch etwas zu tun ist: das
Fenster steht (noch) nicht so, wie die Empfehlung es vorsieht. Da zu
jedem Zeitpunkt ohnehin immer nur **ein** Auslöser als "der" Grund gilt
(siehe Prioritätsreihenfolge unten - Frostschutz vor Hitzeschutz vor
Luftfeuchtigkeit vor CO2 vor Temperatur), stellt sich die Frage "mehrere
Auslöser gleichzeitig" für die Farbe nicht: Rot ist der Normalfall bei
einem echten Fenster-Mismatch, die Grün-Ausnahmen greifen nur, wenn
dieser eine, gewinnende Auslöser tatsächlich ein Schließen-Grund ist -
überwiegt stattdessen ein Öffnen-Grund, wird dieser zum gewinnenden
Auslöser, und der Raum zeigt ganz normal Rot bzw. Orange dafür, nicht
Grün.

Auslöser und Hervorhebung werden dabei **live** berechnet, nicht aus dem
historischen `letzter_grund`-Attribut: Die Integration selbst wertet bei
jedem Lesen der Attribute (nicht nur bei einem echten Zustandswechsel)
aus, welche der drei Öffnen-Größen (Innentemperatur, Luftfeuchtigkeit,
CO2) aktuell ihre Öffnen-Schwelle erreichen (`offene_gruende`, ggf. auch
mehrere gleichzeitig, siehe unten), sowie - für die Schließen-Seite -
einen einzelnen, live berechneten Grund (`schliessgrund_live`): zuerst
Frost- und Hitzeschutz (aktuelle Außentemperatur gegen die konfigurierte
Grenze), dann Luftfeuchtigkeit, CO2, Temperatur gegen ihre jeweilige
Schließen-Schwelle, dann der Sommer-Fall ("Außen wärmer", aktuelle
Außentemperatur gegen die Öffnen-Schwelle selbst - die obere
Normalbereich-Grenze) und "Außenluft inzwischen feuchter"
(`outdoor_wetter`, absolute Außenluftfeuchtigkeit gegen die auf dieselbe
Weise umgerechnete Feuchtigkeits-Öffnen-Schwelle) - beide Male schließt
Lüften also erst, wenn die Außenluft selbst außerhalb des Normalbereichs
liegt, nicht schon, wenn sie nur wärmer/feuchter als die aktuelle (noch
im Normalbereich liegende) Innenluft ist. Die Dashboard-Karte liest diese
beiden Attribute nur noch aus, statt die Vergleiche selbst aus
Rohwerten/Schwellen nachzubauen.
Das funktioniert unabhängig davon, ob die Empfehlung schon einmal einen
echten Zustandswechsel hatte, und beschreibt immer den **aktuellen**
Zustand, nicht nur die Historie - wurde z. B. wegen eines längst
vorbeigezogenen Kälte-Einbruchs geschlossen und ist die Außentemperatur
inzwischen wieder deutlich über der Frostschutz-Grenze, oder wegen eines
inzwischen längst wieder abgekühlten "Außen wärmer"-Falls, zeigt der
Auslöser das nicht mehr an.
`letzter_grund` dient nur noch als **Rückfallwert** für den einen
verbleibenden Fall, der sich nicht live nachrechnen lässt: die
Winter-Höchstdauer (`duration` - dafür fehlen als Attribute noch die
Winter-Schwelle, die Höchstdauer selbst und das Prioritäts-Flag).
Trifft weder ein Live-Check noch dieser Rückfallwert zu ("Totzone": z. B.
eine Innentemperatur, die zwischen Schließen-ab- und Öffnen-ab-Schwelle
liegt, ohne dass eine andere Größe oder Frost-/Hitzeschutz aktuell
zieht), zeigt die Karte konsequent überall neutral "–" statt einer
veralteten Empfehlung: Auslöser, Empfehlung **und** Uhrzeit werden dann
alle "–", das Icon am Raumnamen wird 🟢 (aktuell liegt kein Grund zum
Eingreifen vor, unabhängig vom Fensterzustand). Der zugrunde liegende
`binary_sensor` behält seinen letzten
Zustand technisch unverändert bei (er ändert sich erst bei einem echten
neuen Auslöser) - die Karte soll aber nicht länger eine aktive
Empfehlung suggerieren, für die es aktuell keinen nachvollziehbaren
Grund gibt. Innen-/Außenwerte bleiben in diesem Fall unhervorgehoben, da
es keinen ausschlaggebenden Grund gibt.

**Reihenfolge:** Zu Beginn der Karte (einmalig, vor der Raumliste) eine
**Übersichts-Tabelle** (🟢/🟠/🔴 als Spaltenköpfe, darunter zentriert die
Anzahl der Räume mit dem jeweiligen Icon-Status - Zählung identisch zum
Icon am jeweiligen Raumnamen weiter unten - gefolgt von - falls vorhanden -
einer Spalte "Integration" mit der aktuell installierten Versionsnummer
(`integration_version`, vom ersten Raum, für den das Attribut vorhanden ist)).
Die Raumliste selbst ist nach demselben Icon-Status
wie am Raumnamen sortiert (identisch zur Zählung in der Übersichts-
Tabelle): zuerst alle 🔴-Räume (echter Fenster-Mismatch, größter
Handlungsbedarf), danach alle 🟠-Räume (Fenster steht schon korrekt, aber
Werte noch außerhalb der Norm, oder Raum ohne Fenster), zuletzt alle
🟢-Räume (bereits gelöster Schließen-Grund oder gar kein Auslöser) -
innerhalb jeder der drei
Gruppen jeweils alphabetisch. Räume mit dem größten Handlungsbedarf
stehen so immer ganz oben, unabhängig vom Raumnamen. Pro Raum dann: Raumname →
**Empfehlungs-Tabelle** (Spalten: leer | Status |
Uhrzeit, darunter die beiden Zeilen "Fenster" und "Empfehlung" - nur für Räume mit Fenster; die erste
zeigt ausschließlich den Fensterzustand mit dem Zeitpunkt seiner letzten
tatsächlichen Änderung (Attribut `fenster_seit`, siehe unten; "–" ohne
konfigurierten Fensterkontakt), die zweite ausschließlich
die Empfehlung mit dem Zeitpunkt des letzten ECHTEN Empfehlungswechsels
(`letzter_wechsel`-Attribut, siehe ["Attribute für eine Statusübersicht"](sensoren.md) -
bewusst nicht `last_changed` der Sensor-Entität selbst, das Home Assistant
bei jedem Neustart auf den Neustart-Zeitpunkt zurücksetzt) -
dadurch auf einen Blick erkennbar, ob die Fensteraktion vor oder nach dem
Empfehlungswechsel lag, z. B. um zu prüfen, ob eine fehlende
Benachrichtigung dadurch erklärbar ist (Fenster stand zum Zeitpunkt des
Wechsels bereits passend, siehe ["Logik im Detail"](logik.md)). Beide Zeitstempel
zeigen nur die Uhrzeit ohne Datum, falls sie auf den heutigen Tag fallen.
**Fenster-Zeitpunkt über Neustarts (seit 0.90.1):** Das `last_changed` des
Fensterkontakt-Sensors springt bei jedem Neustart (Zustand "Nicht
verfügbar" und danach wieder "Geöffnet") auf den Neustart-Zeitpunkt. Deshalb
liest die Integration beim Start einmal je Raum die Zustandshistorie des
Fensterkontakts aus der Verlaufsdatenbank (Recorder, letzte 30 Tage) und
bestimmt daraus, seit wann das Fenster im aktuellen Zustand steht: Phasen
mit "Nicht verfügbar"/"Unbekannt" werden übersprungen (auf → nicht
verfügbar → auf bleibt der ursprüngliche Öffnungszeitpunkt). Spätere echte
Wechsel im Betrieb übernimmt die Integration direkt. Das Ergebnis steht im
Attribut `fenster_seit` (nur gesetzt, wenn bekannt). Ist die Zeit nicht
ermittelbar (Recorder nicht geladen, Fensterkontakt vom Recorder
ausgeschlossen, in 30 Tagen kein Wechsel), fehlt das Attribut, und die
Karte fällt auf das alte Verhalten zurück: Fällt bei mindestens drei Räumen
zeitgleich (auf die Minute gerundet) derselbe Fenster-Zeitstempel auf - ein
Anzeichen für einen gemeinsamen Neustart-Reset - wird "–" statt dieses
irreführenden Zeitstempels angezeigt. Ein Wechsel, der passiert, während Home
Assistant aus ist, bleibt unbekannt (angezeigt wird dann der Zeitpunkt nach
dem Start). Eine eigene
Auslöser-Spalte gibt es nicht mehr: Der Auslöser ergibt sich aus der
Werte-Tabelle darunter - bei Temperatur, Luftfeuchtigkeit und CO2 sind dort
**Bezeichnung und Wert** des auslösenden Eintrags gleich eingefärbt (siehe
"Hervorhebung des ausschlaggebenden Werts" oben; auch ein fehlender Messwert
färbt Bezeichnung und "–" orange). **Ausführliche Begründung (seit 0.92.1):** Unter
der Zeile "Empfehlung" steht, über die ganze Tabellenbreite, eine eigene Zeile mit
einem ausgeschriebenen Satz je aktuellem Grund (z. B. "Außen feuchter: Die Außenluft ist
absolut feuchter (14.4 g/m³ gegen 12.8 g/m³ innen), Lüften würde die Feuchtigkeit
erhöhen."). Sie erscheint nur, wenn aktuell ein Grund vorliegt; mehrere gleichzeitige
Öffnen-Gründe stehen untereinander. Die Texte nennen Messwerte und Grenzen, soweit die
Karte sie als Attribut kennt (bei Frost-/Hitzeschutz und Winter-Höchstdauer ohne Zahl).
Räume ohne Fenster haben diese Tabelle nicht und damit auch keine Begründungs-Zeile. Der
Auslöser wird live aus den aktuellen Werten/Schwellen berechnet. Solange dabei ein Auslöser vorliegt,
zeigt die Empfehlung "Öffnen"/"Schließen" entsprechend dem aktuellen Zustand;
liegt aktuell **kein** Auslöser vor ("Totzone", siehe
oben), zeigt die Zeile "Empfehlung" in Status und Uhrzeit "–" statt einer sonst
nicht mehr begründbaren Empfehlung. Das Icon am Raumnamen (die Ampel selbst wird im Backend berechnet und kommt als Attribut `raumstatus`, siehe ["Raumstatus als Sensor"](sensoren.md)) richtet sich danach, ob aktuell ein
Auslöser vorliegt und, falls ja, ob das Fenster bereits entsprechend
steht (🔴 bei echtem Fenster-Mismatch, 🟠 wenn das Fenster schon korrekt
steht, aber die Werte noch außerhalb der Norm liegen, 🟢 bei einem
bereits gelösten Schließen-Grund oder ganz ohne Auslöser - siehe
"Hervorhebung des ausschlaggebenden Werts" oben) →
**Werte-Tabelle** (mit Spaltenüberschrift "Messwert", inkl.
CO2-Zeile falls ein CO2-Sensor hinterlegt ist) → **Geräte-Tabelle**
(Gerät/Laufzeit/Grund - Zeilen für Luftentfeuchter, Klimaanlage, Heizung
und Dusche, jeweils nur falls konfiguriert bzw. für den Raum aktiviert; das
Status-Icon steht direkt vor dem Gerätenamen in der ersten Spalte; ist
ein Tankstatus-Sensor für den Luftentfeuchter hinterlegt, zeigt dessen
Zeile in der "Gerät"-Spalte per Zeilenumbruch (`<br>`) zusätzlich
"Wassertank" mit eigenem Icon (🔴 voll/Fehler, 🟢 ok) direkt unter dem
Gerätenamen; "Laufzeit" zeigt, seit wann das jeweilige Gerät ununter-
brochen läuft bzw. die Duscherkennung anschlägt (`Xh YMin`/`XMin`,
live aus `luftentfeuchter_seit`/`klimaanlage_seit`/`heizung_seit`/
`dusche_seit` berechnet), sonst "–"; die Spalte "Status/Grund" zeigt bei Luftentfeuchter/
Klimaanlage/Heizung eine rein informative, live bei jeder Neubewertung
berechnete Kurzbeschreibung, warum das Gerät gerade an/aus (bzw. bei der
Heizung: Comfort/Standby/Nacht bzw. "Zeitplan: …" bei aktiviertem
Heizungs-Zeitplan) ist bzw. pausiert (u. a. auch "Sommerbetrieb aktiv" - der Vorsatz
"pausiert: " des Attributs wird in der Karte weggelassen, das Status-Icon zeigt
es bereits), ohne selbst Einfluss auf die Steuerung zu haben - siehe
`binary_sensor.py`; bei der Heizung ergänzt um die aktuelle Sollstellung in
Klammern (z. B. "Innentemperatur unter Schwelle, Comfort (Sollstellung: 21.0 °C)" oder
"Zeitplan: Nacht (Sollstellung: 16.0 °C)"); bei Dusche entsprechend, ob und warum die
Duscherkennung aktuell anschlägt; seit 0.92.3 steht jeder Text in Klammern - Sollstellung,
"(Einspeiseleistung zu gering)", "(kein Comfort)", "(Start 07:42)" - in einer eigenen Zeile
unter dem Grund) → **Benachrichtigungen**
(ein-/ausklappbare Tabelle, standardmäßig eingeklappt, jetzt als letzter
Abschnitt pro Raum; zwei Spalten "Benachrichtigung | Ziele" (mehrere Ziele stehen jeweils in einer eigenen Zeile, ohne Komma, und sind einzeln antippbar), das Status-Icon
🟢/⚫ steht links vor dem Namen der Methode (Sprachausgabe, Push-Benachrichtigung, Persistente Benachrichtigung); bei schmaler Karte bricht der Methodenname an den Leerzeichen um, damit die Ziele-Spalte Platz behält).

Icons dienen ausschließlich zur **Status-Signalisierung**: 🟢/🟠/🔴 am
Raumnamen zeigen, ob aktuell eine Empfehlung mit Handlungsbedarf vorliegt
- und, falls ja, ob dafür noch tatsächlich etwas zu tun ist. 🔴 nur, wenn
das Fenster (noch) nicht so steht, wie es die aktuelle Empfehlung
vorsieht - hier kann direkt eingegriffen werden. Steht das Fenster
bereits korrekt, unterscheidet sich die Farbe danach, ob der Auslöser ein
Öffnen- oder ein Schließen-Grund ist: Bei einem **Öffnen**-Grund (die
Person hat also schon reagiert, die zugrunde liegenden Werte haben sich
nur noch nicht normalisiert) zeigt das Icon 🟠 - kein Handlungsbedarf
mehr, aber auch noch nicht "alles gut". Bei einem **Schließen**-Grund
zeigt das Icon dagegen 🟢: Ein Schließen-Auslöser bedeutet per Definition,
dass der jeweilige Wert seine Schließen-Schwelle bereits erreicht hat -
das Problem ist also bereits gelöst, nicht nur "wartend". Für CO2 gilt
das sogar unabhängig vom Fensterzustand (ein niedriger CO2-Wert ist kein
Sicherheitsrisiko, sondern zeigt nur "Luftqualität wieder gut genug" -
Weiterlüften schadet nie); für Temperatur, Luftfeuchtigkeit sowie
"Außen wärmer"/"Außen feuchter" gilt 🟢 dagegen nur, wenn das Fenster
tatsächlich schon passt - bliebe es trotz erreichter Schließen-Schwelle
offen, könnte Weiterlüften hier tatsächlich schaden, daher bleibt es in
diesem Fall bei 🔴. 🟢 gilt außerdem, wenn aktuell gar kein Auslöser
vorliegt ("Totzone", siehe oben) - hier gibt es nichts, das ein
Eingreifen nahelegt, und auch keine außerhalb der Norm liegenden Werte.
Da zu jedem Zeitpunkt ohnehin immer nur ein Auslöser als "der" Grund gilt
(Prioritätsreihenfolge unten), zeigt der Raum bei einem gleichzeitig
aktiven, aber nicht gewinnenden Schließen-Grund ganz normal 🔴/🟠 mit dem
tatsächlich gewinnenden Grund als Auslöser, nicht 🟢.
Bei Räumen ohne Fenster ("Dieser Raum hat kein Fenster" aktiviert) gibt
es ohnehin keinen Fenster-Zustand, über den sich lüften ließe, daher
richtet sich das Icon dort danach, ob aktuell ein Auslöser vorliegt: 🟢,
solange alle Werte im jeweils passenden Bereich liegen. Liegt ein
Öffnen-Auslöser vor, zeigt das Icon 🟠 (identisch zur orangen
Hervorhebung des betroffenen Werts, siehe oben - Handlungsbedarf
besteht, aber nicht über das Fenster, sondern höchstens über
Luftentfeuchter/Klimaanlage). Liegt dagegen ein Schließen-Auslöser vor
(Temperatur, Luftfeuchtigkeit, "Außen wärmer"/"Außen feuchter"), gilt
dieselbe "bereits gelöst, nicht nur wartend"-Logik wie bei Räumen mit
Fenster (siehe oben) - das Icon zeigt 🟢, auch ohne Fenster zum
Abgleichen, unabhängig davon, ob für den Raum zusätzlich ein
Luftentfeuchter/eine Klimaanlage konfiguriert ist. Da zu jedem Zeitpunkt nur ein Auslöser als
"der" Grund gilt (siehe Prioritätsreihenfolge unten), gibt es nie einen
Konflikt zwischen 🟠 und 🔴 für ein und denselben Raum. Bei den
Benachrichtigungsmethoden steht 🟢 für an, ⚫ für aus. Beim Geräte-Status
(Luftentfeuchter/Klimaanlage) gilt dagegen 🔴 für an (läuft gerade), ⚫ für
aus - hier soll ein laufendes Gerät auffallen, nicht als "alles gut"
grün erscheinen. Der Luftentfeuchter-Status ergänzt zusätzlich ein
eigenes Status-Icon in Klammern für den optionalen Tankstatus-Sensor: 🔴,
solange dieser "an" meldet (Tank voll/Fehler), sonst 🟢 - unabhängig vom
🔴/⚫-Icon des Luftentfeuchters selbst. Die Empfehlungs-Tabelle selbst
kommt bewusst ohne Icons aus (nur Text: "Öffnen"/"Schließen" für die
Empfehlung bzw. "geöffnet"/"geschlossen" für den tatsächlichen
Fensterzustand - klein geschrieben, da kein eigenständiger Satzanfang,
und als Partizip sprachlich zu "das Fenster ist geöffnet/geschlossen"
passend). Der Empfehlungstext ("Öffnen"/"Schließen") wird
zusätzlich fett und in derselben Farbe wie der ausschlaggebende Wert
dargestellt, solange dafür ein Auslöser vorliegt - **rot**, wenn das
Fenster noch nicht so steht wie die Empfehlung es vorsieht (echter
Handlungsbedarf); **orange**, wenn das Fenster bereits korrekt steht,
aber die Werte noch außerhalb der Norm liegen, oder der Raum kein
Fenster hat; **grün**, wenn der Auslöser CO2 (Schließen) ist (kein
Handlungsbedarf, siehe "Hervorhebung des ausschlaggebenden Werts" oben);
liegt kein Auslöser
vor ("Totzone"), bleibt der Text schlicht "–" ohne Hervorhebung. Die
Hervorhebung der Innen-/Außenwerte in der Werte-Tabelle folgt derselben
grün/orange/rot-Logik (siehe "Hervorhebung des ausschlaggebenden Werts"
oben).
Die Schwellenwerte
sind mit `>`/`<` versehen (öffnen **oberhalb**, schließen **unterhalb**
des jeweiligen Werts).

## Einrichtung und Bedienung der Karte

Die Karte (`smart-climate-card.js`) ist eine eigenständige, in reinem
JavaScript geschriebene Lovelace-Custom-Card und lässt sich mit normalem CSS
gestalten. Sie liest alle Werte aus den Sensor-Attributen der Räume (siehe
["Attribute für eine Statusübersicht"](sensoren.md)).

**Einrichtung:** Die Karte wird von der Integration selbst automatisch als
Lovelace-Ressource bereitgestellt - es ist **keine** eigene
`resources:`-Eintragung im Dashboard nötig. Nach der Installation/einem
Update einfach eine neue Karte anlegen und als Typ
`Custom: Smart Climate Karte` wählen (oder im YAML-Modus
`type: custom:smart-climate-card` eintragen) - ohne weitere Konfiguration
findet die Karte automatisch alle Räume über das `raum`-Attribut. Optional lässt sich ein Kartentitel vergeben
(`title:` im YAML-Modus, oder über das Textfeld im Karten-Editor - dafür
bringt die Karte einen eigenen, schlanken visuellen Editor mit) - leer
gelassen erscheint kein Titel, wie bisher.

Die Karte hat keine eigene Versionsanzeige - sie wird automatisch als
Lovelace-Ressource von der Integration selbst bereitgestellt und ist dadurch
immer auf demselben Stand wie die installierte Integration (die Übersicht
zeigt die Version der Integration).

**Automatischer Ressourcen-Eintrag (ab 0.94.1):** Die Integration lädt die
Karte weiterhin über Home Assistants Zusatzmodul-Mechanismus, trägt sie nach
dem Start aber zusätzlich als Lovelace-Ressource ein (Typ „JavaScript-Modul“,
URL `/ha_smart_ventilation/smart-climate-card.js?v=<Version>`) - so, wie es
auch HACS für Karten tut. Hintergrund: Karten, die nur als Zusatzmodul geladen
wurden, meldeten gelegentlich „Custom element doesn't exist:
smart-climate-card“, bis die App hart beendet wurde. Der Eintrag erscheint unter
*Einstellungen → Dashboards → ⋮ → Ressourcen* und wird bei jedem Update auf die
neue Version angepasst. Nur im Storage-Modus (Standard) möglich; bei
Dashboards im YAML-Modus bleibt es beim bisherigen Zusatzmodul. Einen von Hand
angelegten Eintrag für denselben Pfad ohne `?v=` lässt die Integration
unangetastet. Nach dem Update Home Assistant neu starten und die Companion-App
vollständig beenden und neu öffnen.

**Eintrag von Hand entfernen:** Die Integration entfernt den Eintrag **nie
selbst** - weder beim Löschen einer Karte (die Ressource gilt für alle
Dashboards, nicht für eine einzelne Karte) noch beim Deinstallieren (z. B. über
HACS; darauf kann die Integration nicht reagieren). Zum Entfernen:
*Einstellungen → Dashboards → ⋮ (oben rechts) → Ressourcen* (die Option
erscheint nur mit aktiviertem „Erweiterten Modus“ im Profil, sofern die
Home-Assistant-Version ihn noch kennt), den Eintrag
`/ha_smart_ventilation/smart-climate-card.js?v=…` öffnen und löschen. Solange
die Integration installiert ist, wird er beim nächsten Start wieder angelegt.
Wird nur die Karte nicht mehr gebraucht, genügt es, sie aus den Dashboards zu
entfernen; ein verwaister Eintrag ist harmlos (lädt nur eine Datei, die dann
fehlt, und zeigt ggf. einen Ladefehler in der Browser-Konsole). Schlägt der
automatische Eintrag fehl, steht eine Warnung im Log; dann die Ressource von
Hand mit obigen Werten anlegen.

**Lange Texte:** Sehr lange Texte in den Tabellen (Auslöser, Grund der
Geräte, Ziele der Benachrichtigungen) werden nach vier Zeilen automatisch
mit „…“ gekürzt - die Wörter selbst bleiben unverändert. Ein Tippen auf
den Text klappt ihn vollständig auf (nochmal tippen: wieder zu), am
Desktop zeigt zusätzlich ein Tooltip den ganzen Text. Der aufgeklappte
Zustand bleibt beim automatischen Aktualisieren der Karte erhalten.

**Absolute Luftfeuchtigkeit:** Ist „Luftfeuchtigkeit“ der Öffnen-Grund, wird
in der JS-Karte zusätzlich die Zeile „Abs. Luftfeuchtigkeit“ (innen und
außen) genauso hervorgehoben wie der Auslöser - der Vergleich der absoluten
Werte (Außenluft trockener) ist es, der das Öffnen freigibt. Fehlt ein
Wert, bleibt die Zeile unauffällig.

**Detailansicht per Klick:** In der JS-Karte lassen sich die **Bezeichnungen**
der Sensoren und Geräte antippen bzw. anklicken (wie sonst in Home Assistant
üblich) - es öffnet sich die Standard-Detailansicht (more-info, mit
Verlauf/Logbuch) der jeweiligen Entität: "Temperatur", "Luftfeuchtigkeit" und
"CO2" in den Messwert-Tabellen (Raum und Außen), die Kopfzellen "Fenster"
(Fensterkontakt) und "Empfehlung" (Empfehlungs-Sensor), die Gerätenamen
(Luftentfeuchter, Wassertank, Heizung, Dusche), der Wert unter "Modus" in der
Statuszeile (globaler Sommer-/Winterschalter) sowie die Ziele der
Benachrichtigungen. Die Werte selbst (z. B. "22,3 °C", "geöffnet") sind nicht
klickbar; klickbare Elemente zeigen nur den Mauszeiger, keine Unterstreichung.
Auch "Abs. Luftfeuchtigkeit" und "Taupunkt" sind klickbar (eigene Sensoren, siehe ["Absolute Luftfeuchtigkeit als Sensor"](sensoren.md)).
Die Entity-IDs liefert das Attribut `entitaeten` (nur die tatsächlich
konfigurierten).

**Außenwerte oben:** Da die Außenwerte für alle Räume gleich sind, zeigt die
JS-Karte sie einmal ganz oben unter der Statuszeile als vier Kacheln
(Titel "Außen-Messwerte": Temperatur, Luftfeuchtigkeit, absolute Luftfeuchtigkeit, Taupunkt;
Bezeichnung klein oben, Wert darunter; die Bezeichnungen sind antippbar und öffnen die
Detailansicht des jeweiligen Sensors). Die Kacheln stehen immer zu zweit nebeneinander (2 × 2); ab einer Kartenbreite
von etwa 620 px (bezogen auf die Karte selbst, nicht auf den Bildschirm) stehen
alle vier in einer Zeile. Ein Außensensor, der konfiguriert ist, aber gerade
keinen Wert liefert, zeigt ein oranges "–" (die Räume bleiben davon
unberührt). Die Messwert-Tabellen der einzelnen Räume haben dadurch
keine Spalte "Außen" mehr (Kopfzeile nur noch "Messwert" über Bezeichnung und Wert sowie "Normalbereich"; die Überschrift "Innen" entfällt, da klar ist, dass es der Innenwert ist) - die
Hervorhebung der Außenzelle bei "Außen wärmer/feuchter", Frost und Hitze
entfällt dort, der Auslöser steht weiter in der Empfehlungs-Zeile.

**Schriftgröße:** Die Tabellen und die Bezeichnungen der Außen-Kacheln verwenden die
normale Kartenschriftgröße (`1 em`, wie die Standardkarten von Home Assistant);
nur der Raumname und die Statuszeile sind etwas größer. Der farbige Streifen
links am Raum liegt hinter dem abgerundeten Rahmen und endet dadurch in den
runden Ecken.

**Fehlende Messwerte:** Liefert einer der konfigurierten Sensoren eines Raums
(Innentemperatur, Luftfeuchtigkeit, CO2) gerade keinen Wert (`nicht verfügbar`/
`unbekannt`), zeigt die Karte den Raum 🟠 (Rahmen orange, in der Übersicht bei
Orange mitgezählt, standardmäßig aufgeklappt) und den fehlenden Wert als oranges
"–". Ein 🔴-Raum (Fenster passt nicht zur Empfehlung) bleibt rot; das Orange
hebt nur einen sonst grünen Raum an. Nach einem Neustart von Home Assistant
kann ein Raum kurz orange erscheinen, solange seine Sensoren noch laden.

**Laufende Geräte (seit 0.91.0):** Läuft in einem Raum ein Luftentfeuchter oder eine
Klimaanlage (`luftentfeuchter_an`/`klimaanlage_an`, live vom Gerät gelesen), zeigt die
Karte den Raum ebenfalls 🟠 - ein 🔴-Raum bleibt rot, nur ein sonst grüner Raum wird
angehoben. Die Heizung zählt nicht dazu. In der Zeile "Dusche" der Gerätetabelle steht
in "Status/Grund" die letzte Startzeit ("Letzter Start 07:42", an einem anderen Tag mit
Datum; während der Dusche "Luftfeuchtigkeit steigt schnell (Start 07:42)").

**Statuszeilen für laufende Geräte (seit 0.92.4):** Solange ein Luftentfeuchter oder eine
Klimaanlage läuft, steht in der ersten Tabelle des Raums (unter "Fenster" und
"Empfehlung") eine Zeile "Luftentfeuchter" bzw. "Klimaanlage" mit Status "Aktiv" und der
Startzeit (heute nur Uhrzeit, sonst mit Datum; ohne bekannten Start "–"). Die bisherige
Zeile verschwindet, sobald das Gerät aus ist. Räume ohne Fenster haben die Tabelle nur
dann, wenn ein Gerät läuft (nur mit der Geräte-Zeile). Die Begründungs-Zeile bleibt
direkt unter "Empfehlung"; die Bezeichnung öffnet wie sonst die Detailansicht.

**Karten-Editor:** Neben dem Titel gibt es die Option "Räume mit Handlungsbedarf
(🟠/🔴) aufgeklappt anzeigen" (YAML: `expand_attention_rooms`, Standard `true`).
Ist sie aus (`expand_attention_rooms: false`), starten alle Räume eingeklappt;
grüne Räume sind ohnehin eingeklappt. Ein von Hand geänderter Zustand bleibt
erhalten, solange sich der Status des Raums nicht ändert; wird die Option
umgeschaltet, gilt sie sofort für alle Räume.

**Raum-Dialog (Tippen auf einen Raumnamen):** Die Karte zeigt auf Wunsch die Details
**eines** Raums in einem Dialog, ausgelöst über die Standard-Tipp-Aktion `fire-dom-event`
(z. B. an einer Mushroom-/Bubble-Karte, die den Raumnamen zeigt):

```yaml
tap_action:
  action: fire-dom-event
  smart_climate_room: badezimmer   # Raumname, Slug oder Entity-ID des Binärsensors
```

Der Dialog erscheint wie ein Bottom-Sheet am unteren Bildschirmrand (auf jeder Breite unten anliegend, am Tablet/PC bis 600 px breit und horizontal zentriert),
mit der Dashboard-Hintergrundfarbe und unscharf abgedunkeltem Hintergrund. Die Seite dahinter
scrollt nicht mit. Schließen: Kreuz, Tippen neben den Dialog, Esc oder nach unten wegwischen
(am Griff oben oder im Inhalt, wenn er ganz oben steht).

Der Dialog zeigt den Raum in einer kompakten Ansicht im Home-Assistant-Stil (ohne Übersicht
und Außen-Messwerte): Titel mit Status-Chip (OK/Hinweis/Handlungsbedarf), dann die Abschnitte
**Lüften** (Fenster, Empfehlung mit Begründung), **Messwerte** (Temperatur, Luftfeuchtigkeit,
CO2 mit Balken für den Normalbereich, darunter abs. Luftfeuchtigkeit und Taupunkt), **Geräte**
(Luftentfeuchter, Klimaanlage, Heizung, Dusche, jeweils mit Zustand, Grund und Laufzeit - ein
voller Wassertank steht beim Luftentfeuchter) und **Benachrichtigungen** (aufklappbar). Die
Symbole sind MDI-Symbole, die Farben kommen aus dem Theme (`--success-color`, `--warning-color`,
`--error-color`, `--info-color`). Die normale Raumansicht der Karte bleibt unverändert (Tabellen).
Der Dialog ist nicht einklappbar; ein langer Inhalt scrollt im Dialog, das Kreuz bleibt stehen. Er schließt per Kreuz, Tippen neben den Dialog oder Esc, und
übernimmt Zustandsänderungen, solange er offen ist. Anders als ein Pop-up je Raum wird
der Inhalt erst beim Tippen erzeugt und beim Schließen entfernt - es läuft nichts im
Hintergrund mit (wichtig auf schwachen Tablets). Dafür muss die Karte als
Lovelace-Ressource geladen sein (macht die Integration selbst); eine Karte auf dem
Dashboard braucht es nicht. Ein unbekannter Raum zeigt "Raum nicht gefunden". Ob die
Bubble Card `fire-dom-event` an Home Assistant durchreicht, ist nicht geprüft.
Tippt man im Dialog auf eine Bezeichnung (z. B. "Temperatur"), öffnet sich die Detailansicht
der Entität, und der Raum-Dialog schließt sich dabei. Funktioniert die Tipp-Aktion nicht, im
Browser (F12, Konsole) `window.__smartClimateRoomDialog` prüfen (`true` = Karte ab 0.98.0 geladen)
und mit `window.dispatchEvent(new CustomEvent('ll-custom', {detail: {smart_climate_room: 'badezimmer'}}))`
testen.
Intern setzt der Dialog die Karten-Option `compact_room: true` (nur der Raum in der kompakten
Ansicht).

**Raum-Dialog statt Standard-more-info (ab 1.12.0):** Die Karte fängt außerdem das
Standard-Ereignis `hass-more-info` ab: Öffnet etwas (z. B. eine Bubble-Kachel mit
`tap_action: more-info`) die Detailansicht eines **Raum-Sensors dieser Integration**, erscheint
statt des Standard-Fensters der Raum-Dialog. Für die Kachel genügt:

```yaml
button_action:
  tap_action:
    action: more-info
    entity: binary_sensor.badezimmer_lueftungsempfehlung   # Raum-Sensor der Integration
```

Die Kachel behält ihre Hauptentität (`climate.<raum>`). Das gilt überall, wo der Raum-Sensor
angetippt wird (Suche, andere Karten, Logbuch), nicht für andere Entitäten. Das Standard-Fenster
(Verlauf, Rohattribute) bleibt über den runden **↗-Knopf** neben dem Schließen-Kreuz erreichbar.
Hat der Raum eine Heizung, steht im Abschnitt **Raumklima** (unter Temperatur, Luftfeuchtigkeit,
Abs. Luftfeuchtigkeit und Taupunkt) eine eigene **Thermostat-Bedienung**:
Zustand ("Leerlauf"/"Heizt"; die Ist-Temperatur steht in der Zeile "Temperatur"), der Sollwert groß mit -/+ (im Schritt der
Entität, begrenzt auf deren Min/Max; gesendet wird 0,7 s nach dem letzten Tippen), Chips für den
Betriebsmodus und die Voreinstellung (aus den von der Entität gemeldeten `hvac_modes`/
`preset_modes`; Dienste `climate.set_temperature`/`set_hvac_mode`/`set_preset_mode`). Home
Assistants eigene Thermostat-Karte ließ sich im Dialog nicht verlässlich einbetten (blieb leer),
einen runden Drehregler gibt es daher nicht; das Standard-Fenster der Heizung bleibt über die
Bezeichnung "Heizung" erreichbar. Die Heizungszeile zeigt darunter Modus, Grund und **seit wann** der gewollte Modus
gilt ("Soll Standby seit 22:14 (vor 3h 20 Min)"), ggf. "Comfort verhindert: niemand zuhause"
und "Manuell übersteuert seit ..."; Antippen klappt den ganzen Text auf. Dieselben Zeilen
stehen in der Spalte "Status/Grund" der Geräte-Tabelle der normalen Karte. Eine Änderung am
Thermostat im Dialog zählt für die Integration als manueller Eingriff (siehe "Manuelle
Übersteuerung").

**Kopfzeile und Reihenfolge (ab 1.14.3):** Der Raumname mit dem Statuschip (OK/Hinweis/Handlungsbedarf)
steht in der Kopfzeile neben den beiden runden Knöpfen. Danach folgen die Abschnitte **Raumklima**
(Messwerte plus Heizungssteuerung, statt "Messwerte"), **Lüften**, **Geräte** und **Benachrichtigungen**.
Räume ohne Heizung zeigen im Raumklima keinen Steuerblock.

**Layout und Farben des Dialogs (ab 1.14.1):** Das Blatt wird oben durch die Statusleiste des
Geräts begrenzt (Safe-Area), das Schließen-Kreuz ist ein runder 44-px-Knopf, der Knopf für die Standardansicht (↗) ein ebenso runder Knopf daneben, und bis zu vier Voreinstellungen stehen in einer Zeile (mehr brechen
um). Die Messwerte im Dialog sind nach dem Normalbereich eingefärbt (Wert, Balkenmarke, Symbol):

| Messwert | unter dem Bereich | im Bereich | über dem Bereich |
|---|---|---|---|
| Temperatur | blau | grün | rot |
| Luftfeuchtigkeit | orange (zu trocken) | grün | blau (zu feucht) |
| CO2 | grün | grün | rot |

Taupunkt und absolute Luftfeuchtigkeit bleiben neutral, ein fehlender Wert bleibt ein oranges "–".
Die normale Karte ist unverändert. Eine Überschriftskarte kann statt `fire-dom-event` einfach
`tap_action: {action: more-info, entity: binary_sensor.<raum>_lueftungsempfehlung}` nutzen.

**Einschränkung:** Ohne eine echte Home-Assistant-Instanz zum Testen des
tatsächlichen Lovelace-Rendering ließ sich diese Karte nur über eine
simulierte DOM-Umgebung (jsdom) mit Beispieldaten gegen die dokumentierten
Szenarien (mehrere gleichzeitige Öffnen-Gründe, aufgelöster Schließen-Grund
bei fensterlosen Räumen, Frostschutz-Mismatch, Totzone-Neutralfall,
Laufzeit-Formatierung) verifizieren - echtes Home-Assistant-Frontend-
Verhalten (Rendering-Details, Registrierung als Lovelace-Ressource) bleibt
bis zu einer Rückmeldung aus der echten Oberfläche ungewiss.

## Bubble-Card-Modul "climate_status" und Dashboard-Darstellung

Für Dashboards mit der [Bubble Card](https://github.com/Clooos/Bubble-Card)
liefert die Integration das Modul **`climate_status`** mit (Preset- und
Ventilbalken, Rollladenbalken, farbiger Hintergrund nach Raumstatus,
Wechselanzeige der Zusatzwerte). Es wird für `climate`-Entitäten verwendet.

**Wo das Modul liegt:** Ist [Bubble Card Tools](https://github.com/Clooos/Bubble-Card-Tools)
installiert (Ordner `/config/bubble_card/modules`), schreibt die Integration
beim Start die Datei `climate_status.yaml` dorthin - aber nur, wenn sie noch
fehlt oder eine ältere Version enthält. Die vorherige Fassung wird einmalig als
`/config/bubble_card/climate_status_v<alt>.yaml.bak` gesichert. Die Meldung
"Bubble-Card-Modul climate_status angelegt/aktualisiert" steht im Log. Danach
Browser bzw. App neu laden. Das Modul ist dann im Bubble-Card-Editor unter
"Module" mit der Version `v4.2` zu sehen. Eigene Änderungen am Modulcode gehen
bei einem Update verloren, deshalb stehen alle Einstellungen in der Integration.
Gibt es den Ordner nicht (oder liest Bubble Card die Datei nicht ein), kann der
Modultext aus dem Integrationsordner (`bubble/climate_status.yaml`) über "Import
from YAML" im Bubble-Card-Editor eingefügt werden.

**Einstellungen:** In den allgemeinen Einstellungen ("- Smart Climate Optionen -"
→ Konfigurieren) gibt es den Abschnitt **"Dashboard-Darstellung"**:
- **Farbiger Hintergrund** (an/aus), **Heizungsbalken** und **Rollladenbalken**
  (an/aus) jeweils mit **Seite** (links/rechts; liegen beide auf derselben Seite,
  steht der Rollladenbalken neben dem Heizungsbalken).
- **Heizungsbalken/Rollladenbalken: Ecken einbeziehen** (jeweils an/aus, Standard
  **aus**) mit **Eckenradius der Balken** (px, Standard 14): Aus füllt der Balken anteilig
  über die gesamte Kachelhöhe, wodurch kleine Werte komplett in der Rundung
  verschwinden. An: Beim Heizungsbalken ist die untere Rundung dunkel, sobald das Ventil
  offen ist (heizt das Gerät, zählt das auch bei `command_value` 0), der Ventilwert füllt
  dann die gerade Kante von unten, bei 100 % geht der Balken bis ganz oben durch. Der
  Rollladenbalken arbeitet gespiegelt von oben: sobald der Rollladen nicht ganz offen ist, ist die
  obere Rundung dunkel, bei ganz geschlossen geht der Balken bis ganz unten. Passt die Rundung
  optisch nicht, den Eckenradius an den Radius deiner Kacheln anpassen.
- **Wechselwert 1/2:** welche Zusatzwerte im Wechsel mit der Temperatur laufen
  (absolute oder relative Luftfeuchtigkeit, CO2, Taupunkt oder aus). Die Reihenfolge ergibt
  sich aus 1 und 2.
- **Anzeigedauer Temperatur** (Standard 8 s) und **Anzeigedauer Wechselwerte** (Standard 2 s je Wert;
  ein Durchlauf dauert Temperatur + Anzeige je Wechselwert), **Balkenbreite**, **Rahmenbreite**, **Zeilenhöhe** des
  Namens, **Schriftgröße** der Wechselwerte.
- **Farben** sind nicht einstellbar: Das Modul nutzt feste Theme-Variablen von
  Home Assistant und folgt damit deinem Theme (auch Hell/Dunkel). Komfort =
  `--state-climate-heat-color`, Eco = `--state-climate-auto-color`,
  Gebäudeschutz/kalt = `--state-climate-cool-color`, Standby/warm/Hinweis =
  `--warning-color`, Sommerbetrieb = `--disabled-color`, heiß/Handlungsbedarf =
  `--error-color`, Rollladen = `--state-cover-open-color`. Ist eine Variable im
  Theme nicht gesetzt, gilt die bisherige Farbe als Rückfall. Der Hintergrund
  bei Hinweis/Handlungsbedarf ist die jeweilige Farbe mit 20 % bzw. 25 %
  Deckkraft.

Die Werte stehen als fertige CSS-Werte in den Attributen des Sensors
**"Smart Climate Darstellung"** (`sensor.smart_climate_darstellung`, Kategorie
Diagnose, Zustand = Modulversion). Das Modul liest sie live aus den Zuständen,
Änderungen wirken also sofort ohne Neuschreiben der Datei. Fehlt der Sensor oder
ein Wert, gelten die Standards im Modul. Der Schalter für den Sommerbetrieb
kommt aus der globalen Einstellung ("Sommer-/Winterbetrieb-Schalter").

**Fenster-Button bei Hinweis/Handlungsbedarf:** Das Modul findet den Fenster-Sub-Button der
Karte automatisch: Es sucht in den Sub-Buttons (`main`, dann `bottom`) den, dessen `entity` der
Fensterkontakt des Raums ist (`entitaeten.fenster`). Fläche und Symbol bleiben unverändert (die Farbe
kommt vom Fensterzustand, z. B. aus deinem Modul `subbutton_typfarben`: blau = offen). Der Raumstatus
wird nur als Signal am Rand bzw. im Inneren gezeichnet (ändert die Größe nicht): bei `hinweis` in der
Warnfarbe (`--warning-color`), bei `handlungsbedarf` rot (`#E53935`); sonst gibt es kein Signal. Die
Darstellung wählst du in den allgemeinen Einstellungen im Abschnitt "Dashboard-Darstellung" unter
**Fenster-Signal**: Aus, A Ring innen, B Ring außen, C Ring außen mit Lücke, D Leuchten außen, E Ring
innen + Leuchten, F Ring innen mit dunklem Abstand, G weicher Innenschein, H stärkerer Innenschein,
I Verlauf Rand zur Mitte, **J dünner Ring + Innenschein (Standard)**, K Verlauf von oben, L Balken links, M Balken rechts, N Balken links und rechts, O obere Hälfte, P untere Hälfte, Q linke Hälfte, R rechte Hälfte, S Balken oben, T Balken unten, U Ecke oben rechts, V Balken an allen vier Seiten (wie die Balken für Heizung und Rollladen, nur Status ohne Füllhöhe). Die
**Ring-/Balkenbreite** (1-12 px, Standard 2) gilt für die Varianten mit Ring oder Balken (A, B, C, E, F, J, L, M, N, S, T, V). Die Einstellungen stehen in zwei Abschnitten: **Dashboard: Bubble-Card** (Kachel) und **Dashboard: Fenster-Button** (Signal); Vorschau der Varianten: `custom_components/ha_smart_ventilation/www/fenster-signal.png` (im Einstellungsdialog selbst lassen sich keine Bilder anzeigen); schematische Kachel: `www/bubble-card-vorschau.png` (kein Screenshot). Die Verläufe I/K
setzen ein Hintergrundbild auf den Button; außen liegende Varianten (B, C, D, E) können vom Container
abgeschnitten werden. Die
Reihenfolge der Buttons ist egal. Steht der Fensterkontakt nicht in den Sub-Buttons (oder hat der Raum
keinen), passiert nichts - außer `climate_status: { window_button: N }` ist gesetzt, dann gilt dieser Platz
(1-basiert). Die Regel ist spezifischer als die des Moduls `subbutton_typfarben`. Eine rote Fläche über
`subbutton_colors` (`condition` auf den Raumstatus) ist nicht mehr nötig. Das Symbol (Fenster offen/zu) kommt vom Fensterkontakt. Damit der Button auch bei
geschlossenem Fenster und Empfehlung "Öffnen" erscheint, braucht seine
`visibility` eine Oder-Bedingung, z. B.:

```yaml
visibility:
  - condition: or
    conditions:
      - condition: state
        entity: binary_sensor.badezimmer_fenster_status_1
        state: 'on'
      - condition: state
        entity: sensor.badezimmer_raumstatus
        state: handlungsbedarf
```

**Voraussetzungen im Modul:** Der Raum-Binärsensor heißt
`binary_sensor.luften_empfohlen_<raum>` und der Raumstatus
`sensor.<raum>_raumstatus` (Standardnamen der Integration). Der Rollladen wird
als `cover.<raum>_rollladen` abgeleitet (Ausnahme im Modul: `climate.buro` →
`cover.rollo_buro`) oder über `climate_status: { cover_entity: ... }` an der
Karte gesetzt.
