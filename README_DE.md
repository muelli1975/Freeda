# Freeda 1.2

[English](README_EN.md)

Freeda ist ein lokales Desktop-Werkzeug zum Einrahmen und Exportieren von Full-SBS-Stereobildern als Freeview-Grafiken für Web und Druck. Parallelblick, Kreuzblick und kombinierte Ansichten nutzen dieselben Einstellungen für Rahmen, Untertitel und Ausschnitte.

Freeda arbeitet vollständig lokal: kein Konto, keine Cloud, kein Tracking und keine automatischen Downloads während der Nutzung.

![Freeda 1.2](docs/screenshots/Freeda.png)

## Portable Windows-Version

[Freeda 1.2 herunterladen](https://github.com/muelli1975/Freeda/releases/tag/v1.2)

1. `Freeda_1.2_Windows_x64.zip` vollständig in einen beschreibbaren Ordner entpacken.
2. `Freeda.exe` starten.
3. Den Programmordner zusammenhalten; `_internal`, `tools` und die anderen mitgelieferten Dateien gehören zur Anwendung.

Eine separate Python-Installation ist nicht nötig. Sprache und gespeicherte Presets liegen als `settings.json` neben `Freeda.exe`. Beim Update diese Datei und den eigenen Ordner `logos`, falls vorhanden, in den neuen Programmordner übernehmen. Die EXE ist nicht mit Authenticode signiert.

## macOS- und Linux-Builds

Auf derselben Downloadseite stehen Pakete für Linux x64, macOS Apple Silicon und macOS Intel bereit. Das vollständige Paket in einen beschreibbaren Ordner entpacken. Unter Linux `Freeda` in einer grafischen Desktop-Sitzung starten; benötigt wird glibc 2.35 oder neuer. Unter macOS `Freeda.app` aus dem zur Prozessorarchitektur passenden Paket starten. Die Einstellungen liegen neben dem App-Bundle. ExifTool liegt unter Linux im Ordner `tools` neben dem Programm und unter macOS in `Freeda.app/Contents/MacOS/tools`. Linux und macOS benötigen für die Metadatenübernahme einen funktionierenden Perl-Interpreter; das Windows-Paket enthält seine eigene Laufzeitumgebung.

Alle vier Varianten entstehen aus demselben markierten Quellstand. Automatische Tests und Startprüfungen der fertigen Programme laufen auf jeder Plattform; unter Windows und Linux kommen Exportprüfungen über die Oberfläche hinzu. Manuelle Desktop-Tests unter macOS und Linux stehen noch aus. Die macOS-Anwendungen sind ad hoc signiert und nicht von Apple notarisiert.

## Schnellstart

1. Ein Full-SBS-Bild, mehrere Dateien oder einen Bilderordner öffnen.
2. **Web** oder **Print** und die gewünschte Ansicht wählen.
3. Lange Seite in Pixeln beziehungsweise Druckformat, Rahmenfarben und Untertitel einstellen.
4. Mit **Ausschnitt anpassen** den Bildausschnitt positionieren. Bei Web lässt sich zusätzlich das Seitenverhältnis der Halbbilder wählen.
5. Die Vorschau prüfen. Mit Vorheriges/Nächstes weitere Bilder ansehen. Der Vorschaubereich hat rechteckige Ecken und nutzt die verfügbare Fläche bei Web und Print.
6. Export starten. Der Einzelbildexport verarbeitet das angezeigte Bild, der Batch die gesamte Auswahl.

Beim ersten Start ist Deutsch eingestellt. Über die Sprachauswahl lässt sich auf Englisch umschalten; Freeda merkt sich die zuletzt gewählte Sprache. Die übrigen Einstellungen starten mit den Standardwerten: Web, 2048 Pixel, 4 % Rahmenbreite, 4 % Untertitelgröße, 300 dpi und 0 mm Beschnittrand mit eingeschalteter Beschnittrandvorschau. Presets werden erst beim ausdrücklichen Auswählen angewendet.

## Unterstützte Eingaben

Freeda öffnet JPEG-, PNG-, TIFF-, BMP- und WebP-Bilder mit zwei gleich großen Ansichten nebeneinander: linkes Auge links, rechtes Auge rechts (`L|R`). Erwartet werden Full-SBS-Bilder, keine horizontal gestauchten Half-SBS-Bilder. Freeda erzeugt keine Stereotiefe und richtet die beiden Ansichten nicht zueinander aus.

## Ansichten

- **Parallelblick:** `L|R`.
- **Kreuzblick:** `R|L`.
- **Parallelblick + Kreuzblick:** beide Bildpaare in zwei Zeilen.
- **L–R–L:** drei Ansichten in einer Zeile; das linke Paar ermöglicht Parallelblick, das rechte Kreuzblick.

Die II/X-Symbole belegen einen Streifen in Rahmenbreite. Bei L–R–L stehen sie über den Zwischenräumen. Untertitel erscheinen unter den Bildern; ihr Bereich darf unabhängig vom Symbolstreifen anwachsen. Lange L–R–L-Untertitel werden bei Bedarf bis auf 75 % der gewählten Größe verkleinert und anschließend mit Auslassungspunkten gekürzt. Bei proportionalen Rahmen hat der unterste Untertitelbereich eine Rahmenbreite weniger Abstand.

## Web und Druck

**Ausschnitt zurücksetzen** setzt Position und Zoom des angezeigten Bildes zurück; das gewählte Seitenverhältnis und die Ausschnitte anderer Bilder bleiben erhalten.

Webgrößen bestimmen die **lange Seite in Pixeln** der fertigen Grafik einschließlich Rahmen und Untertitel beziehungsweise Logo. Bei 2048 ist eine querformatige Ausgabe 2048 Pixel breit, eine hochformatige 2048 Pixel hoch. Zur Auswahl stehen Presets, eine frei eingegebene Größe und Original für die vorhandene Bildauflösung. Das Seitenverhältnis der Halbbilder kann unverändert bleiben oder über ein Preset beziehungsweise ein eigenes Verhältnis angepasst werden.

Print bietet vorgegebene und eigene Druckformate, frei eingegebene positive ganzzahlige dpi und einen frei einstellbaren **Beschnittrand in mm** mit Nachkommastellen. Der Beschnittrand startet bei 0 mm; seine Vorschau ist eingeschaltet, damit ein hinzugefügter Rand sofort sichtbar wird. Das Druckformat wird vollständig ausgefüllt; das Seitenverhältnis der Halbbilder ergibt sich aus Papierformat, Ansicht, Rahmen und Untertiteln. Einzelbilder exportieren den in der Vorschau gezeigten Ausschnitt direkt. **Bildausschnitt beim Export prüfen** öffnet auf Wunsch den Ausschnittdialog; die manuelle Ausschnittwahl im Batch bleibt verfügbar. Der Beschnittrand hat dieselbe Farbe wie der Rahmen. Optionale Schneidelinien und Schnittmarken sind grau. Die Vorschau passt sich dem verfügbaren Platz an; ihre Anzeigeskalierung ist unabhängig von den Export-dpi.

Die Rahmenbreite ist von 0 bis 5 % einstellbar, mit 4 % als Standard. Untertitelschrift und Untertitelgröße lassen sich anpassen; die Standardgröße beträgt 4 %. Die Schriftwahl zeigt den eingegebenen Untertitel als Muster; lange Mustertexte werden mit Auslassungspunkten gekürzt, ohne den eigentlichen Untertitel zu verändern. Die Schriftwahl betrifft ausschließlich Untertitel; die II/X-Symbole behalten ihre Standardschrift. Beide Prozentwerte beziehen sich auf die Breite eines Halbbilds und werden in Web und Print gleich berechnet. Die Textabstände orientieren sich an der Schriftgröße: etwa 0,4-mal oberhalb und 0,6-mal unterhalb, mit zusätzlichem Zeilenabstand nur zwischen den Zeilen.

**Bildkontur** bietet zwei Optionen: **Rechteck / gerundete Ecken** und **Klassischer Bogen**. Bei Rechteck / gerundete Ecken bestimmen **Radius oben** und **Radius unten** unabhängig die beiden oberen beziehungsweise unteren Bildecken. 0 lässt die jeweiligen Ecken rechteckig; gleiche Werte runden alle Ecken gleich. Beide Radien beziehen sich auf die Halbbildbreite. Beim klassischen Bogen erscheint stattdessen die Bogenhöhe, ebenfalls in Prozent der Halbbildbreite. Ausgeblendete Radiuswerte bleiben beim Wechsel erhalten, beeinflussen den Bogen aber nicht. Alle Konturen funktionieren in Web, Print und Ausschnittvorschau. Vorhandene Presets werden mit ihrem bisherigen Aussehen übernommen. Die Konturwerte werden wie Rahmen- und Untertitelgröße über Schieberegler eingestellt; der aktuelle Wert steht in der Beschriftung. Die üblichen Bereiche sind 0–25 % für Bildradien, 0–5 % für Radius außen und 0–50 % für Bogenhöhe, in Schritten von 0,5 %, 0,1 % beziehungsweise 0,5 %. Die Bereiche berücksichtigen die aktuelle Geometrie und erweitern sich für größere gespeicherte Werte, soweit geometrisch möglich. Beim Abgleichen der Regler werden gespeicherte Werte nicht verändert.

**Radius außen** steht bei beiden Optionen zur Verfügung, bezieht sich auf die Gesamtbreite und rundet die fertige Grafik einschließlich eines vorhandenen Beschnittrands. Bildradien und äußerer Radius sind unabhängig; zu große Radien werden auf die geometrisch mögliche Größe begrenzt. PNG behält transparente Außenecken; JPEG füllt sie bei Web schwarz und bei Print weiß, wie bereits in der Vorschau zu sehen. Innere Bildecken zeigen die gewählte Rahmenfarbe.

Die 16 Farbpresets stehen zuerst dunkel, dann hell; **Nachtgold** bleibt auf dem ersten Platz und Standard. Die bisherigen zehn Kombinationen bleiben erhalten. Creme, Pergament, Honigkarton, Salbeipapier, Blaugrau und Altrosa ergänzen helle Kartenhintergründe mit dunkler Schrift. Eigene Farben sind weiterhin möglich.

## Kartenvorlagen und genaue Druckränder

Eine **Kartenvorlage** liefert ein fertiges Layout; **Freies Layout** behält die proportionalen Rahmen. Vorlagen ändern Druckformat, Ränder, Bildkontur und Ansicht. Farben, Untertitelschrift und Untertiteltext bleiben erhalten.

| Vorlage | Fertige Karte | Bildfenster | Mittelsteg |
| --- | --- | --- | --- |
| Holmes-Karte | 177,8 × 88,9 mm (7 × 3½ Zoll) | 76,2 × 76,2 mm | 1,6 mm |
| Stereokarte 18 × 9 cm | 180 × 90 mm | 76,2 × 76,2 mm | 2,6 mm |
| Raumbildkarte 13 × 6 cm | 130 × 60 mm | 59 × 52 mm | 2 mm |

Das sind anpassbare Layoutvorschläge, keine universellen Normen für historische Betrachter. Holmes und 18 × 9 cm beginnen mit Bogen, Raumbild rechteckig. Alle verwenden Parallelblick ohne II/X. Die Eignung für den eigenen Betrachter und die Bildinhalte prüfen: Der Abstand der Bildmitten allein bestimmt nicht den Sehkomfort.

**Ränder und Bildfenster anpassen** öffnet die genauen Einstellungen. **Exakte Ränder in mm** erlaubt unabhängige Werte für Außenrand links/rechts, oberen Rand, Mittelsteg und unteren Bereich. Bei zwei Bildzeilen erscheint zusätzlich deren Abstand. Der untere Bereich umfasst den Untertitel und gilt je Bildzeile. Er wächst nicht automatisch mit dem Text: Freeda meldet zu wenig Platz, statt die Bildfenster zu verkleinern. Angezeigte Bildfenstermaße und Bildmittenabstand werden sofort aktualisiert. Geänderte Vorlagen erscheinen als angepasst; **Vorlage zurücksetzen** stellt ihr Layout wieder her.

Bei Print lässt sich die Schriftgröße auch frei in Punkt eingeben. Optionale Textabstände oben und unten werden in mm eingestellt; leere Felder verwenden die automatischen Abstände nach Schriftgröße. Exakte Ränder ersetzen den Prozentregler für den Rahmen, Punktgrößen den Prozentregler für Untertitel. Die Einstellungen gehören zu den portablen Presets. Vorhandene Presets aus 1.0 bleiben verwendbar.

Kartenmaße, Ränder und Ausschnittverhältnis werden vor der Pixelumrechnung in Millimetern berechnet. Ein anderer dpi-Wert verändert dadurch die Auflösung, nicht die Kartengeometrie. Der Beschnittrand wird außen in Rahmenfarbe ergänzt. Exportierte Karten mit **100 % / tatsächlicher Größe** drucken, ohne automatische Seitenanpassung.

Für schlichte Stereokarten bei Print Parallelblick oder Kreuzblick, 0 % Rahmenbreite und einen leeren Untertitel wählen. Die Halbbilder liegen dann ohne Außenrahmen und Zwischensteg direkt nebeneinander und füllen das Druckformat aus. **Blicksymbole anzeigen** schaltet II/X unabhängig vom Rahmen ein oder aus; bei 0 % entfallen sie automatisch. Standardmäßig bleibt die Option eingeschaltet. Rahmenbreite und Symbolwahl gehören zu den Presets.

## Logos statt Untertiteltext

Unter **Beschriftung** zwischen **Text** und **Logo** wählen. **Logo wählen** importiert eine Bilddatei; transparente PNG-Dateien eignen sich besonders gut. Logos erscheinen zentriert und identisch unter jedem Halbbild, auch bei allen drei L–R–L-Ansichten und beiden Zeilen der kombinierten Ansicht. Beim Umschalten bleiben Text und Logoauswahl während der Sitzung erhalten. Solange noch kein Logo gewählt ist, bleibt die Vorschau ohne Beschriftung sichtbar und fordert zur Auswahl auf; der Export ist bis dahin deaktiviert.

Das Seitenverhältnis bleibt erhalten; die Breite ist auf 90 % eines Halbbilds begrenzt. Die Höhe startet mit 8 % der Halbbildbreite und ist von 1–20 % einstellbar. Print erlaubt zusätzlich eine positive Höhe in mm. Die eingestellte Höhe ist ein Maximum: Sehr breite Logos werden weiter verkleinert, damit sie hineinpassen. Automatische Abstände betragen 15 % der tatsächlichen Logohöhe oberhalb und 25 % unterhalb. Bei Print lassen sie sich über dieselben genauen Abstandsfelder in mm ersetzen.

Bei exakten Druckrändern muss das Logo in den unteren Bereich passen. Freeda meldet zu wenig Platz, statt die Bildfenster zu ändern. Proportionale Layouts erweitern ihren Beschriftungsbereich wie bei Untertiteln. Logos werden mit Lanczos skaliert; transparente Pixel lassen die Rahmenfarbe durchscheinen. Das Verhalten der Außenecken bei JPEG und PNG bleibt erhalten.

Freeda kopiert die gewählte Datei unverändert in `logos` neben `settings.json`. Presets speichern einen relativen Verweis und die Logogröße; dadurch bleiben sie beim Verschieben des gesamten Programmordners nutzbar. Beim Update sowohl `settings.json` als auch `logos` übernehmen. Fehlende oder unlesbare Logodateien erzeugen einen verständlichen Hinweis. Beim Ersetzen bleiben frühere Kopien für gespeicherte Presets erhalten. Beim Start bleibt Text voreingestellt; ein Logo-Preset wird erst beim Auswählen angewendet.

## Bildausschnitte

**Ausschnitt anpassen** verwendet denselben relativen Ausschnitt für beide Stereoansichten. **Zurücksetzen** stellt Zoom und Position wieder her. Ein zuschaltbares Drittelraster erscheint getrennt über den beiden Ansichten und wird nie exportiert. Beim Batch lässt sich jedes Bild einzeln prüfen oder derselbe relative Ausschnitt übernehmen.

Normalerweise bleiben Ausschnitte während der Sitzung im Arbeitsspeicher. **Bildausschnitte merken** lädt gespeicherte Ausschnitte und schreibt bestätigte Änderungen in `freeda-crops.json` im jeweiligen Bilderordner. Die Einträge verwenden Dateinamen und relative Koordinaten, getrennt für Web und Print. Den Bilderordner zusammen mit dieser Datei verschieben, um die Ausschnitte zu erhalten.

Die Checkbox ist beim Start ausgeschaltet. Ausschalten lässt gespeicherte Dateien bestehen. Zurücksetzen entfernt nur den Eintrag des jeweiligen Bilds und Modus. Die Originalbilder bleiben unverändert.

## Stapelverarbeitung und Navigation

Beim Öffnen eines Einzelbilds stehen auch die anderen unterstützten Bilder seines Ordners für die Vorschau zur Verfügung. Vorheriges/Nächstes und Bild↑/Bild↓ wechseln zwischen ihnen, ohne am Ende wieder vorne zu beginnen. Der Einzelbildexport verarbeitet weiterhin nur das angezeigte Bild.

Die Auswahl mehrerer Dateien oder eines Ordners erzeugt einen Batch. Die Navigation wechselt die Vorschau; der Batch exportiert die gesamte Auswahl. **Unterordner mitverarbeiten** schließt die Unterordner eines gewählten Eingabeordners ein. Ohne die Option werden nur dessen direkt enthaltene Bilder verarbeitet.

## Ausgabe und Ordner

Standardmäßig ist `output` im **Programmordner** als Ausgabeordner gewählt. Ein Ordner-Batch übernimmt darunter den Namen des Eingabeordners und dessen relative Unterordnerstruktur: `Urlaub/Tag1/bild.jpg` wird zu `<Programmordner>/output/Urlaub/Tag1/bild_freeda_web.jpg`; bei Print entsprechend zu `bild_freeda_print.jpg`. Einzeln gewählte Dateien landen direkt im Ausgabeordner.

**Unterordner im Programmordner verwenden** ist beim Start aktiviert. Beschriftung und Pfad unter **Eigener Ausgabeordner** sind dann ausgegraut. **Auswählen** bleibt bedienbar: Ein eigenes gemeinsames Ziel wählen, wodurch der Haken automatisch entfernt wird; die Struktur darunter bleibt erhalten. Erneutes Aktivieren stellt `output` im Programmordner wieder her und behält den eigenen Ordner für später. Das tatsächliche Ziel wird separat angezeigt. Input- und Outputdialoge merken sich getrennte Startordner während der Sitzung.

**Unterordner mitverarbeiten** ist beim Start ausgeschaltet. Einschalten liest den gewählten Eingabeordner rekursiv neu ein; ein Wechsel des Ausgabeziels aktualisiert ebenfalls die Liste. Das gewählte Ausgabeziel innerhalb der Eingabe sowie Ordner namens `output`, `tmp` und `_temp` werden vor dem Durchsuchen ausgeschlossen. Bereits erzeugte Freeda-Dateien werden bei der Ordnersuche übersprungen. Ausschnittdateien sind keine Bilddateien; verknüpfte Unterordner werden nicht verfolgt. Bewusst über **Dateien …** gewählte Ausgaben lassen sich weiterhin öffnen. Die Eingabeliste steht vor dem Export fest.

Dateien heißen beispielsweise `bild_freeda_web.jpg` oder `bild_freeda_print.png`. Gleichnamige Bilder in verschiedenen Unterordnern behalten getrennte Ziele. Wenn unterschiedliche Quelldateiendungen im selben Ordner denselben Ausgabenamen ergäben, erhält das weitere Ziel eine Nummer. Vorhandene Ausgaben beeinflussen diese Zuordnung nicht: Bestehende Bilder am gleichen Ziel werden beim erneuten Export überschrieben. Originaldateien bleiben unverändert. Freeda exportiert JPEG oder **PNG (mit Transparenz)** und verarbeitet die Bilder in 8-Bit-RGB. PNG erhält transparente Außenecken; ausgesparte Ecken der Bildfenster zeigen weiterhin die Rahmenfarbe.

Einlesen und Export laufen im Hintergrund. Vorschau und Fortschritt zeigen relative Quellpfade, damit gleichnamige Bilder unterscheidbar bleiben. **Abbrechen** stoppt das Einlesen oder den Export. Der Ausschnittdialog pausiert den Export bis zu Übernehmen, Überspringen oder Export abbrechen. Bei aktivierter Merkoption werden gespeicherte Ausschnitte aus dem konkreten Quellordner übernommen; **Bildausschnitt beim Export prüfen** fordert ihre erneute Prüfung an. Bestätigte Änderungen bleiben auch nach einem späteren Exportabbruch gespeichert.

Fertige Ausgaben bleiben bei Abbruch erhalten. Das laufende Bild wird zunächst temporär gespeichert und erst nach vollständiger Speicherung und Metadatenübernahme an sein Ziel übernommen. Ein Abbruch verwirft die temporäre Datei und erhält eine frühere Ausgabe. Innerhalb eines Bildschritts wird der Abbruch an der nächsten sicheren Grenze ausgeführt; Einstellungen bleiben bis zum Ende gesperrt. Dateifehler stoppen nicht den ganzen Batch. Der Abschluss zeigt exportierte und übersprungene Bilder sowie die Fehlerzahl; die Zusammenfassung nennt betroffene Quellen. Ausschnitt- und Metadatenwarnungen werden ebenfalls angezeigt.

## Metadaten

Soweit möglich kopiert Freeda Metadaten der Quelle mit dem gebündelten ExifTool in die fertigen JPEG- und PNG-Dateien. Aufnahmedatum, Kamera, Belichtung, ursprüngliche Brennweite, Copyright und GPS-Angaben bleiben erhalten, soweit das Ausgabeformat sie unterstützt. Eingebettete Vorschauen, Vorschauminiaturen, Orientation und MPF/MPO-Containerdaten werden ausgeschlossen.

Die Bildabmessungen entsprechen dem neu berechneten Bild einschließlich eines etwaigen Beschnittrands. Auflösungswerte der Quelle werden ausgeschlossen; bei Print bleiben die eingestellten Export-dpi erhalten. Die Metadatenübernahme verändert keine Originaldateien und erzeugt keine `_original`-Sicherungskopien. Scheitert sie, bleibt das exportierte Bild gültig und Freeda zeigt einen nicht fatalen Hinweis in der gewählten Sprache.

ExifTool 13.59 liegt separat unter `tools`, zusammen mit seinen ursprünglichen Begleitdateien und Lizenzhinweisen. Es läuft nur beim Export, unter Windows ohne Konsolenfenster. Während der Programmnutzung werden keine Dateien heruntergeladen.

## Einstellungen und Sprache

Deutsch und Englisch stehen zur Verfügung. Sprache und benannte Presets werden lokal in `settings.json` neben dem Programm gespeichert; dadurch bleibt das gesamte Programm portabel. Presets enthalten Export- und Darstellungseinstellungen. Eingabebildpfade, Ausgabepfade, bildbezogene Untertiteltexte und individuelle Ausschnitte gehören nicht zu einem Preset.

Beim Start wird die zuletzt gewählte Sprache wiederhergestellt. Die übrigen Einstellungen verwenden die Standardwerte, bis ein Preset ausgewählt wird. Individuelle Ausschnittdateien liegen in den jeweiligen Bilderordnern, getrennt von den Programmeinstellungen.

## Quellcode und langfristige Nutzung

Das [GitHub-Repository](https://github.com/muelli1975/Freeda) enthält Quellcode und Build-Skripte. Für die Entwicklung werden Python 3.12 und die Abhängigkeiten aus `requirements-lock.txt` benötigt. `build_windows.ps1` bereitet die geprüfte ExifTool-Distribution vor und erstellt das Windows-Paket; für Linux und macOS zuerst `python scripts/prepare_exiftool.py` und anschließend `scripts/build_unix.py` auf dem jeweiligen System ausführen. Build-Downloads werden gegen die festgelegten Archivprüfsummen des Herausgebers geprüft. Der Release-Ablauf prüft die Programme vor der Veröffentlichung.

Freeda soll unabhängig von Konten und Onlinediensten nutzbar bleiben. Aktive Wartung, Support, Bearbeitung von Issues oder Prüfung von Pull Requests können nicht garantiert werden.


## Bildnavigation und Ausschnittkontrolle

**Links/Rechts** und **Bild auf/Bild ab** wechseln das Bild. Im Ausschnittdialog zeigen **Parallelblick (P)**, **Kreuzblick (X)** und **Anaglyph (A)** denselben Ausschnitt, ohne die Exportansicht zu verändern. Die Anaglyphenkontrolle verwendet Dubois LCD mit linearer sRGB-Verarbeitung und Rotpotenz 0,75. Vorschauen werden im Hintergrund berechnet. EXIF-Orientation wird für Vorschau und Export genau einmal angewendet.

Ausgabeziel und eigene Ordner bleiben getrennt sichtbar. Ergebnisse tragen `_freeda_web` bzw. `_freeda_print`; zusätzliche web-/print-Ordner werden nicht angelegt. Ordnerexport erhält Quellordnernamen und Unterordnerstruktur. Gespeicherte Ausschnitte liegen als `freeda-crops.json` im jeweiligen konkreten Quellordner. Das Release enthält den passenden Quellstand unter `source`.

## Lizenz

Freeda steht unter der [MIT-Lizenz](LICENSE), Copyright Christoph Müller. Fremdkomponenten behalten ihre eigenen Lizenzen. Die Pakete enthalten [Hinweise zu Fremdkomponenten](THIRD_PARTY_NOTICES.md) und Lizenzkopien im Ordner `licenses`.
