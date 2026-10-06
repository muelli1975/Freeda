# Freeda 1.1

[English](README_EN.md)

Freeda ist ein lokales Desktop-Werkzeug zum Einrahmen und Exportieren von Full-SBS-Stereobildern als Freeview-Grafiken für Web und Druck. Parallelblick, Kreuzblick und kombinierte Ansichten nutzen dieselben Einstellungen für Rahmen, Untertitel und Ausschnitte.

Freeda arbeitet vollständig lokal: kein Konto, keine Cloud, kein Tracking und keine automatischen Downloads während der Nutzung.

![Freeda 1.1](docs/screenshots/Freeda.png)

## Portable Windows-Version

[Freeda 1.1 herunterladen](https://github.com/muelli1975/Freeda/releases/tag/v1.1)

1. `Freeda_1.1_Windows_x64.zip` vollständig in einen beschreibbaren Ordner entpacken.
2. `Freeda.exe` starten.
3. Den Programmordner zusammenhalten; `_internal`, `tools` und die anderen mitgelieferten Dateien gehören zur Anwendung.

Eine separate Python-Installation ist nicht nötig. Sprache und gespeicherte Presets liegen als `settings.json` neben `Freeda.exe`. Beim Update diese Datei und den eigenen Ordner `logos`, falls vorhanden, in den neuen Programmordner übernehmen. Die EXE ist nicht mit Authenticode signiert.

## macOS- und Linux-Builds

Auf derselben Downloadseite stehen Pakete für Linux x64, macOS Apple Silicon und macOS Intel bereit. Das vollständige Paket in einen beschreibbaren Ordner entpacken. Unter Linux `Freeda` in einer grafischen Desktop-Sitzung starten; benötigt wird glibc 2.35 oder neuer. Unter macOS `Freeda.app` aus dem zur Prozessorarchitektur passenden Paket starten. Die Einstellungen liegen neben dem App-Bundle. ExifTool liegt unter Linux im Ordner `tools` neben dem Programm und unter macOS in `Freeda.app/Contents/MacOS/tools`, wie bei StereoFine. Linux und macOS benötigen für die Metadatenübernahme einen funktionierenden Perl-Interpreter; das Windows-Paket enthält seine eigene Laufzeitumgebung.

Alle vier Varianten entstehen aus demselben markierten Quellstand. Automatische Tests und Startprüfungen der fertigen Programme laufen auf jeder Plattform; unter Windows und Linux kommen Exportprüfungen über die Oberfläche hinzu. Manuelle Desktop-Tests unter macOS und Linux stehen noch aus. Die macOS-Anwendungen sind ad hoc signiert und nicht von Apple notarisiert.

## Schnellstart

1. Ein Full-SBS-Bild, mehrere Dateien oder einen Bilderordner öffnen.
2. **Web** oder **Print** und die gewünschte Ansicht wählen.
3. Ausgabebreite beziehungsweise Druckformat, Rahmenfarben und Untertitel einstellen.
4. Mit **Ausschnitt anpassen** den Bildausschnitt positionieren. Bei Web lässt sich zusätzlich das Seitenverhältnis der Halbbilder wählen.
5. Die Vorschau prüfen. Mit Vorheriges/Nächstes weitere Bilder ansehen.
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

Bildfenster können rechteckig, rundum gerundet, nur oben gerundet oder mit einem klassischen flachen Bogen gestaltet werden. Der Bildradius erscheint nur bei gerundeten Bildkonturen und bezieht sich auf die Halbbildbreite; die Bogenhöhe wird separat in Prozent der Halbbildbreite eingestellt. Diese Konturen funktionieren bei Web, Print und in der Ausschnittvorschau. Der Außenradius im Abschnitt Bildkontur bezieht sich auf die Gesamtbreite und rundet die gesamte Grafik einschließlich eines vorhandenen Beschnittrands, unabhängig von der Bildkontur. PNG behält transparente Außenecken; JPEG füllt sie bei Web schwarz und bei Print weiß, wie bereits in der Vorschau zu sehen. Innere Bildecken zeigen die gewählte Rahmenfarbe.

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

Das Seitenverhältnis bleibt erhalten; die Breite ist auf 90 % eines Halbbilds begrenzt. Die Höhe startet mit 6 % der Halbbildbreite und ist von 1–20 % einstellbar. Print erlaubt zusätzlich eine positive Höhe in mm. Die eingestellte Höhe ist ein Maximum: Sehr breite Logos werden weiter verkleinert, damit sie hineinpassen. Automatische Abstände betragen 15 % der tatsächlichen Logohöhe oberhalb und 25 % unterhalb. Bei Print lassen sie sich über dieselben genauen Abstandsfelder in mm ersetzen.

Bei exakten Druckrändern muss das Logo in den unteren Bereich passen. Freeda meldet zu wenig Platz, statt die Bildfenster zu ändern. Proportionale Layouts erweitern ihren Beschriftungsbereich wie bei Untertiteln. Logos werden mit Lanczos skaliert; transparente Pixel lassen die Rahmenfarbe durchscheinen. Das Verhalten der Außenecken bei JPEG und PNG bleibt erhalten.

Freeda kopiert die gewählte Datei unverändert in `logos` neben `settings.json`. Presets speichern einen relativen Verweis und die Logogröße; dadurch bleiben sie beim Verschieben des gesamten Programmordners nutzbar. Beim Update sowohl `settings.json` als auch `logos` übernehmen. Fehlende oder unlesbare Logodateien erzeugen einen verständlichen Hinweis. Beim Ersetzen bleiben frühere Kopien für gespeicherte Presets erhalten. Beim Start bleibt Text voreingestellt; ein Logo-Preset wird erst beim Auswählen angewendet.

## Bildausschnitte

**Ausschnitt anpassen** verwendet denselben relativen Ausschnitt für beide Stereoansichten. **Zurücksetzen** stellt Zoom und Position wieder her. Ein zuschaltbares Drittelraster erscheint getrennt über den beiden Ansichten und wird nie exportiert. Beim Batch lässt sich jedes Bild einzeln prüfen oder derselbe relative Ausschnitt übernehmen.

Normalerweise bleiben Ausschnitte während der Sitzung im Arbeitsspeicher. **Bildausschnitte merken** lädt gespeicherte Ausschnitte und schreibt bestätigte Änderungen in `freeda-crops.json` im jeweiligen Bilderordner. Die Einträge verwenden Dateinamen und relative Koordinaten, getrennt für Web und Print. Den Bilderordner zusammen mit dieser Datei verschieben, um die Ausschnitte zu erhalten.

Die Checkbox ist beim Start ausgeschaltet. Ausschalten lässt gespeicherte Dateien bestehen. Zurücksetzen entfernt nur den Eintrag des jeweiligen Bilds und Modus. Die Originalbilder bleiben unverändert.

## Stapelverarbeitung und Navigation

Beim Öffnen eines Einzelbilds stehen auch die anderen unterstützten Bilder seines Ordners für die Vorschau zur Verfügung. Vorheriges/Nächstes und Bild↑/Bild↓ wechseln zwischen ihnen, ohne am Ende wieder vorne zu beginnen. Der Einzelbildexport verarbeitet weiterhin nur das angezeigte Bild.

Die Auswahl mehrerer Dateien oder eines Ordners erzeugt einen Batch. Die Navigation wechselt die Vorschau; der Batch exportiert die gesamte Auswahl. Unterordner werden nur bei eingeschalteter entsprechender Checkbox einbezogen.

## Ausgabe und Ordner

Standardmäßig ist „Unterordner im Input-Ordner verwenden“ aktiviert: Freeda schreibt nach `output/web` oder `output/print` im Input-Ordner. Ein eigener Ausgabeordner lässt sich auswählen und bleibt bei aktivierter Unterordner-Option sichtbar, erscheint aber grau. Das tatsächliche Ausgabeziel wird separat angezeigt. Input- und Outputdialoge merken sich während der Sitzung getrennte Startordner. Bei Ordner-Batches bleibt die relative Ordnerstruktur erhalten. Während des Exports sind die Einstellungen gesperrt.

Dateien heißen beispielsweise `bild_freeda_web.jpg` oder `bild_freeda_print.png`. Bestehende Ausgabebilder am selben Ziel werden beim Export überschrieben. Originaldateien bleiben unverändert. Freeda exportiert JPEG oder PNG und verarbeitet die Bilder in 8-Bit-RGB.

## Metadaten

Soweit möglich kopiert Freeda Metadaten der Quelle mit dem gebündelten ExifTool in die fertigen JPEG- und PNG-Dateien, entsprechend StereoFine und SplatTricia. Aufnahmedatum, Kamera, Belichtung, ursprüngliche Brennweite, Copyright und GPS-Angaben bleiben erhalten, soweit das Ausgabeformat sie unterstützt. Eingebettete Vorschauen, Vorschauminiaturen, Orientation und MPF/MPO-Containerdaten werden ausgeschlossen.

Die Bildabmessungen entsprechen dem neu berechneten Bild einschließlich eines etwaigen Beschnittrands. Auflösungswerte der Quelle werden ausgeschlossen; bei Print bleiben die eingestellten Export-dpi erhalten. Die Metadatenübernahme verändert keine Originaldateien und erzeugt keine `_original`-Sicherungskopien. Scheitert sie, bleibt das exportierte Bild gültig und Freeda zeigt einen nicht fatalen Hinweis in der gewählten Sprache.

ExifTool 13.59 liegt separat unter `tools`, zusammen mit seinen ursprünglichen Begleitdateien und Lizenzhinweisen. Es läuft nur beim Export, unter Windows ohne Konsolenfenster. Während der Programmnutzung werden keine Dateien heruntergeladen.

## Einstellungen und Sprache

Deutsch und Englisch stehen zur Verfügung. Sprache und benannte Presets werden lokal in `settings.json` neben dem Programm gespeichert; dadurch bleibt das gesamte Programm portabel. Presets enthalten Export- und Darstellungseinstellungen. Eingabebildpfade, Ausgabepfade, bildbezogene Untertiteltexte und individuelle Ausschnitte gehören nicht zu einem Preset.

Beim Start wird die zuletzt gewählte Sprache wiederhergestellt. Die übrigen Einstellungen verwenden die Standardwerte, bis ein Preset ausgewählt wird. Individuelle Ausschnittdateien liegen in den jeweiligen Bilderordnern, getrennt von den Programmeinstellungen.

## Quellcode und langfristige Nutzung

Das [GitHub-Repository](https://github.com/muelli1975/Freeda) enthält Quellcode und Build-Skripte. Für die Entwicklung werden Python 3.12 und die Abhängigkeiten aus `requirements-lock.txt` benötigt. `build_windows.ps1` bereitet die geprüfte ExifTool-Distribution vor und erstellt das Windows-Paket; für Linux und macOS zuerst `python scripts/prepare_exiftool.py` und anschließend `scripts/build_unix.py` auf dem jeweiligen System ausführen. Build-Downloads werden gegen die festgelegten Archivprüfsummen des Herausgebers geprüft. Der Release-Ablauf prüft die Programme vor der Veröffentlichung.

Freeda soll unabhängig von Konten und Onlinediensten nutzbar bleiben. Aktive Wartung, Support, Bearbeitung von Issues oder Prüfung von Pull Requests können nicht garantiert werden.

## Lizenz

Freeda steht unter der [MIT-Lizenz](LICENSE), Copyright Christoph Müller. Fremdkomponenten behalten ihre eigenen Lizenzen. Die Pakete enthalten [Hinweise zu Fremdkomponenten](THIRD_PARTY_NOTICES.md) und Lizenzkopien im Ordner `licenses`.
