# Fehlersuche und Hinweise

[← Zurück zur Übersicht](../README.md)

## Fehlersuche / Diagnose

Drei Bordmittel helfen bei der Fehlersuche, ohne dass Werte oder
Log-Zeilen von Hand abgeschrieben werden müssen:

- **Diagnose herunterladen**: Bei jedem Eintrag (ein Raum oder
  "- Smart Climate Optionen -") lässt sich über das Drei-Punkte-Menü
  (⋮) → **Diagnose herunterladen** eine JSON-Datei erzeugen. Sie enthält
  die Konfiguration dieses Eintrags (personenbezogene Anwesenheits-/
  Notify-Ziel-Entitäten sind darin automatisch geschwärzt), bei einem
  Raum zusätzlich den aktuellen Entitäts-Zustand samt aller Attribute
  sowie eine Momentaufnahme (Zustand + Attribute) aller referenzierten
  Roh-Sensoren - Innentemperatur-Quelle, Luftfeuchtigkeit, CO2,
  Fensterkontakt sowie die globale Außentemperatur/-luftfeuchtigkeit. Bei
  den globalen Einstellungen zusätzlich für jedes App-Benachrichtigungsziel
  mit hinterlegter Anwesenheits-Entität eine Momentaufnahme von deren
  Zustand und Zeitpunkt der letzten Änderung (ohne die Entity-ID oder
  weitere Attribute) - nützlich, um zu erkennen, ob ein Push wegen
  "Person/Gerät nicht zuhause" übersprungen wurde (dieser Fall wird sonst
  nur mit Debug-Logging sichtbar).
  Damit lässt sich z. B. sofort erkennen, ob ein referenzierter Sensor
  gerade `unavailable`/`unknown` meldet. Diese Datei kann direkt
  hochgeladen/geteilt werden, z. B. um ein auffälliges Verhalten zu
  melden.
- **Debug-Protokollierung**: Über Einstellungen → Geräte & Dienste →
  beim jeweiligen Raum-Eintrag → Zahnrad-Symbol → **Debug-Protokollierung
  aktivieren** (oder global über `logger:` in der `configuration.yaml`
  für `custom_components.ha_smart_ventilation`) protokolliert die
  Integration bei jeder Neubewertung eine einzelne, strukturierte
  Log-Zeile mit allen Zwischenwerten der Entscheidungskette (Temperaturen,
  Luftfeuchtigkeit, CO2, alle Öffnen-/Schließen-/"noch benötigt"-Flags).
  Hilfreich vor allem bei Flacker-artigen Problemen (wiederholtes
  Öffnen/Schließen), bei denen ein einzelner Diagnose-Snapshot nicht
  ausreicht.
- **Push-Verlauf und Test-Push** (bei "Ich bekomme keine Push-
  Benachrichtigung"): Jede Lüftungsempfehlung-Entität hat das Attribut
  `push_verlauf` (Entwicklerwerkzeuge → Zustände, sowie in der
  Diagnose-Datei) mit den letzten zwölf Einträgen, neueste
  zuerst, jeweils mit Uhrzeit. Seit 0.93.1 steht dort auch **jede
  Sprachausgabe** mit Anlass und Text (z. B. `Sprachausgabe (Empfehlung
  Öffnen, Grund humidity): …`, `(Erinnerung)`, `(Licht an)`,
  `(Wassertank)`, `(Duschdauer)`, `(Fenster-Gerät-Konflikt)`) - so lässt sich
  nachvollziehen, warum eine Ansage kam. Push-Einträge: `gesendet an notify.…`, `FEHLER beim
  Senden an …` (mit der echten Fehlermeldung), `übersprungen …:
  Anwesenheits-Entität steht auf 'not_home'`, `nicht gesendet: App-Push
  ist wirksam deaktiviert`, `nicht gesendet: keine notify-Entität
  konfiguriert` sowie `keine Benachrichtigung: Fensterkontakt zeigt
  bereits den Zielzustand` bzw. `bewusst still` - also genau die Fälle,
  in denen früher stillschweigend nichts passiert ist. Dieselben
  Einträge stehen auch im normalen Log (Level `info`, bei Fehlern
  `warning`). Der Verlauf wird nicht über einen Neustart hinweg gespeichert.
  Mit der Aktion **Smart Climate: Test-Push senden**
  (`ha_smart_ventilation.send_test_push`, Ziel: die Lüftungsempfehlung
  des Raums) lässt sich außerdem jederzeit eine Test-Nachricht über
  exakt denselben Sendeweg an alle App-Push-Ziele des Raums schicken -
  auch wenn Push für den Raum deaktiviert oder die Person nicht zuhause
  ist. Der Verlauf nennt dann zusätzlich, ob eine **echte**
  Benachrichtigung jetzt gesendet würde; ein Sendefehler kommt als
  Fehlermeldung direkt zurück. Kommt der Test-Push an, eine echte
  Benachrichtigung aber nie, liegt es an einer der im Verlauf genannten
  Bedingungen (nicht am Zustellweg).

## Hinweise

- **Umstieg auf globale Benachrichtigungsziele**: Bestehende Räume, die
  bereits eigene Werte für App/Persistent gesetzt hatten, funktionieren
  unverändert weiter (ihre bisherigen Ja/Nein-Werte gelten jetzt einfach
  als expliziter Raum-Override). Neu ist nur, dass sich diese Felder jetzt
  auch komplett leer lassen lassen, um stattdessen die globale Einstellung
  zu übernehmen. Um einen bereits konfigurierten Raum auf "globale
  Einstellung nutzen" umzustellen, musst du das entsprechende Dropdown im
  Formular einmal manuell auf die leere Option zurücksetzen.
- **Automatische Migration noch älterer Räume**: Räume, die aus einer Zeit
  vor der obigen Umstellung stammen und seitdem nie neu gespeichert wurden,
  hatten intern noch eine ältere, längst nicht mehr ausgewertete
  `notify_method`-Liste anstelle von "Home Assistant Companion App"/
  "Persistente Benachrichtigung" - dadurch blieben sie trotz konfigurierter
  Benachrichtigungsziele dauerhaft stumm (weder Raum- noch globaler Wert
  vorhanden). Seit Version 0.33.2 migriert die Integration solche Räume beim
  nächsten Start automatisch einmalig auf die aktuellen Felder - kein
  manuelles Eingreifen nötig.
- **Wegfall des Sprachausgabe-Schalters**: Der frühere Ja/Nein/leer-Schalter
  "Sprachausgabe" (Raum und global) und die globale Lautsprecherliste
  wurden entfernt. Ein bereits konfigurierter Raum mit ausgewählten
  Lautsprechern ist davon nicht betroffen - Sprachausgabe war und bleibt
  aktiv, jetzt eben ausschließlich abgeleitet daraus, dass Lautsprecher
  ausgewählt sind. Hatte ein Raum dagegen Sprachausgabe nur über die
  globale Einstellung (leeres Dropdown) bezogen, ohne selbst Lautsprecher
  festzulegen, ist Sprachausgabe für ihn jetzt aus - dann müssen die
  gewünschten Lautsprecher einmalig direkt im Raum nachgetragen werden.
- Die Integration reagiert direkt auf Zustandsänderungen (kein Polling),
  daher sehr geringe Systemlast. Die angezeigten Attribute (aktuelle
  Temperatur/Luftfeuchtigkeit etc.) werden bei jeder Neubewertung aktuell
  gehalten - auch wenn sich der Empfehlungsstatus selbst dabei nicht
  ändert. **Ausnahme:** Die Außentemperatur kommt
  ausschließlich aus "- Smart Climate Optionen -" und wird beim Start jedes
  Raums direkt mitverfolgt – ändert sich aber die dort hinterlegte
  Sensor-**Auswahl** selbst (nicht nur ihr Messwert), wirkt sich das erst
  beim nächsten 5-Minuten-Tick des Raums aus. Dasselbe gilt für den
  Leistungssensor, falls dieser nur global (nicht zusätzlich im Raum)
  gesetzt ist.
- **Konservativ bei kurzzeitig nicht verfügbaren Außensensoren**: Sind
  Außentemperatur- und/oder Außen-Luftfeuchtigkeitssensor konfiguriert,
  aber gerade nicht verfügbar (z. B. während Home Assistant startet oder
  stoppt und andere Integrationen noch laden/entladen), werden die davon
  abhängigen Öffnen-Bedingungen und der Frostschutz **konservativ**
  behandelt (kein Öffnen, ggf. Frostschutz blockiert vorsorglich) - nicht
  permissiv, wie es bei komplett fehlender Konfiguration der Fall ist.
  Das verhindert Fehlalarme durch kurzzeitige Sensor-Ausfälle beim
  Neustart.
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
  gesetzt - die davor aktuelle Lautstärke jedes Lautsprechers wird dabei
  gemerkt und **nach der Ansage automatisch wieder gesetzt**. Da `tts.speak`
  kein plattformübergreifend zuverlässiges "Wiedergabe beendet"-Ereignis
  liefert, wird dafür die ungefähre Sprechdauer aus der Nachrichtenlänge
  geschätzt (rund 150 Wörter/Minute plus Pufferzeit) - bei sehr langen
  Ansagen oder einem ungewöhnlich langsamen TTS-Dienst kann die Lautstärke
  dadurch im Einzelfall etwas zu früh oder zu spät zurückgesetzt werden.
- **Pausieren vs. Überlagern**: Im Modus "Pausieren" wird die vorhandene
  Wiedergabe vor der Ansage pausiert, aber **nicht automatisch
  fortgesetzt** - ein zuverlässiges automatisches Fortsetzen ist
  plattformübergreifend (über alle `media_player`-Integrationen hinweg)
  nicht robust lösbar. "Überlagern" (Standard) spielt die Ansage einfach
  direkt über die laufende Wiedergabe.
- **Sprachausgabe-Nachtruhe**: Optionales Zeitfenster (global oder pro Raum,
  Standard aus, Standard-Zeiten 22:00–07:00), in dem ausschließlich die
  Sprachausgabe unterdrückt wird - App-Push und persistente Benachrichtigung
  werden davon nicht beeinflusst. Betrifft auch die Tank-voll-Benachrichtigung
  (siehe unten).
- **Titel der Benachrichtigungen** (seit 0.80.2): App-Push und persistente
  Web-Benachrichtigung tragen den Raumnamen zuerst im Titel, danach die
  eigentliche Überschrift - z. B. "Wohnzimmer – Lüften",
  "Wohnzimmer – Wassertank", "Wohnzimmer – Fenster schließen" (Test-Push:
  "Wohnzimmer – Smart Climate Test"). So ist der Raum auch in der
  Push-Vorschau sofort erkennbar. Die Titel sind fest, nur der Nachrichtentext
  ist anpassbar. Die Sprachausgabe hat keinen Titel.
- **Sendeweg der App-Benachrichtigungen:** Der Home-Assistant-Dienst
  `notify.send_message` akzeptiert nur `message` und `title` - kein
  `data`-Feld mit `tag`. Die Integration ermittelt deshalb zum gewählten
  Companion-App-Ziel den klassischen Dienst `notify.mobile_app_<gerät>`
  (aus dem Gerätenamen bzw. dem Namen der notify-Entität) und ruft, wenn er
  existiert, diesen mit `tag` auf - nur so funktionieren Ersetzen und
  Auflösen ("Clean Notification", siehe unten). Findet sich kein solcher
  Dienst, geht die Nachricht über `notify.send_message` **ohne** `tag` raus:
  sie kommt an, wird aber nicht ersetzt/aufgelöst (ein Auflösen wird dann
  gar nicht erst gesendet). Welcher Weg genutzt wurde, steht im Attribut
  `push_verlauf` (siehe "Fehlersuche / Diagnose"). Vor Version 0.79.1 wurde
  fälschlich immer `notify.send_message` mit `tag` aufgerufen - Home
  Assistant lehnte das mit `not a valid option at 'data'` ab, sodass gar
  kein Push ankam.
- **"Clean Notification"**: Erledigt sich eine Lüften-Empfehlung (Fenster
  wurde geöffnet/geschlossen und/oder die Werte haben sich normalisiert),
  wird eine zuvor gesendete Push-Benachrichtigung automatisch auf dem
  Gerät aufgelöst, und eine zuvor erstellte persistente Web-Benachrichtigung
  automatisch per `persistent_notification.dismiss` entfernt. Für Push
  technisch über einen festen, raumeindeutigen `tag` gelöst: eine neue
  Benachrichtigung ersetzt eine ältere auf demselben Gerät automatisch, und
  ein `clear_notification` löst sie ohne Ersatz auf. Das greift bei beiden
  Kanälen auch dann, wenn die Person das Fenster bereits selbst
  geöffnet/geschlossen hat, bevor sich die zugrunde liegenden Werte
  normalisiert haben - dafür ist kein vollständiger Zustandswechsel der
  Empfehlung nötig, es reicht, dass der konfigurierte Fensterkontakt den
  gewünschten Zustand erreicht. Das erfordert den Companion-App-Dienst
  `notify.mobile_app_<gerät>` (siehe "Sendeweg" oben) - deshalb ist die
  Auswahl beim App-Benachrichtigungsziel auf Companion-App-Entitäten
  eingeschränkt. Ein Sendefehler wird im `push_verlauf` und als Warnung
  mit der echten Fehlermeldung protokolliert, statt die Neubewertung
  fehlschlagen zu lassen.
- **Benachrichtigung bei vollem Wassertank**: Ist für einen Raum ein
  Tankstatus-Sensor konfiguriert UND die zugehörige Benachrichtigung
  aktiviert, löst ein Vollwerden des Tanks eine eigene Benachrichtigung über
  dieselben, für den Raum aktuell wirksamen Kanäle aus (eigener Text, eigener
  `tag`/eigene `notification_id`, unabhängig von der Lüftungsempfehlung) und
  löst sich nach demselben "Clean Notification"-Muster automatisch wieder
  auf, sobald der Tank wieder als "leer" gemeldet wird.
- **Fenster-Gerät-Konflikt melden** (Benachrichtigung): Ist für einen Raum die
  entsprechende Option aktiviert UND läuft dort ein konfigurierter
  Luftentfeuchter oder eine konfigurierte Klimaanlage bei offenem Fenster
  gegen ungünstigere Außenluft an, löst das eine eigene Benachrichtigung
  über dieselben, für den Raum aktuell wirksamen Kanäle aus (eigener Text
  mit `{raum}`/`{geraet}`-Platzhaltern, eigener `tag`/eigene
  `notification_id` je Gerät, unabhängig von der eigentlichen
  Lüftungsempfehlung - kann also auch dann auslösen, wenn diese gerade
  "aus"/neutral ist). Löst sich nach demselben "Clean Notification"-Muster
  automatisch wieder auf, sobald das Fenster geschlossen wird oder die
  Außenluft wieder hilft. Bewusst unabhängig von einem eventuellen
  Einspeiseleistungs-Überschuss - das Schließen hilft dem Gerät, sein Ziel
  tatsächlich zu erreichen, auch wenn der Betrieb gerade "kostenlos" ist.
- Diese Integration öffnet/schließt keine motorisierten Fenster automatisch –
  sie informiert nur. Falls du motorisierte Fenster hast, kannst du den
  `binary_sensor` als Trigger in einer eigenen Automation verwenden, um
  `cover.open_cover` / `cover.close_cover` aufzurufen.
