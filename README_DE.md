# Freeda 1.0

[English](README_EN.md)

Freeda ist ein lokales Desktop-Werkzeug zum Einrahmen und Exportieren von Full-SBS-Stereobildern als Freeview-Grafiken für Web und Druck. Parallelblick, Kreuzblick und kombinierte Ansichten nutzen dieselben Einstellungen für Rahmen, Untertitel und Ausschnitte.

Freeda arbeitet vollständig lokal: kein Konto, keine Cloud, kein Tracking und keine automatischen Downloads während der Nutzung.

![Freeda 1.0](docs/screenshots/Freeda.png)

## Portable Windows-Version

[Freeda 1.0 herunterladen](https://github.com/muelli1975/Freeda/releases/tag/v1.0)

1. `Freeda_1.0_Windows_x64.zip` vollständig in einen beschreibbaren Ordner entpacken.
2. `Freeda.exe` starten.
3. Den Programmordner zusammenhalten; `_internal` und die anderen mitgelieferten Dateien gehören zur Anwendung.

Eine separate Python-Installation ist nicht nötig. Sprache und gespeicherte Presets liegen als `settings.json` neben `Freeda.exe`. Beim Update diese Datei in den neuen Programmordner übernehmen. Die EXE ist nicht mit Authenticode signiert.

## macOS- und Linux-Builds

Auf derselben Downloadseite stehen Pakete für Linux x64, macOS Apple Silicon und macOS Intel bereit. Das vollständige Paket in einen beschreibbaren Ordner entpacken. Unter Linux `Freeda` in einer grafischen Desktop-Sitzung starten; benötigt wird glibc 2.35 oder neuer. Unter macOS `Freeda.app` aus dem zur Prozessorarchitektur passenden Paket starten. Die Einstellungen liegen neben dem App-Bundle.

Alle vier Varianten entstehen aus demselben markierten Quellstand. Automatische Tests und Startprüfungen der fertigen Programme laufen auf jeder Plattform; unter Windows und Linux kommen Exportprüfungen über die Oberfläche hinzu. Manuelle Desktop-Tests unter macOS und Linux stehen noch aus. Die macOS-Anwendungen sind ad hoc signiert und nicht von Apple notarisiert.

## Schnellstart

1. Ein Full-SBS-Bild, mehrere Dateien oder einen Bilderordner öffnen.
2. **Web** oder **Print** und die gewünschte Ansicht wählen.
3. Ausgabebreite beziehungsweise Druckformat, Rahmenfarben und Untertitel einstellen.
4. Mit **Ausschnitt anpassen** den Bildausschnitt positionieren. Bei Web lässt sich zusätzlich das Seitenverhältnis der Halbbilder wählen.
5. Die Vorschau prüfen. Mit Vorheriges/Nächstes weitere Bilder ansehen.
6. Export starten. Der Einzelbildexport verarbeitet das angezeigte Bild, der Batch die gesamte Auswahl.

Beim ersten Start ist Deutsch eingestellt. Über die Sprachauswahl lässt sich auf Englisch umschalten; Freeda merkt sich die zuletzt gewählte Sprache. Die übrigen Einstellungen starten mit den Standardwerten: Web, 2048 Pixel, 4 % Rahmenbreite, 3,5 % Untertitelgröße, 300 dpi und 0 mm Beschnittrand mit eingeschalteter Beschnittrandvorschau. Presets werden erst beim ausdrücklichen Auswählen angewendet.

## Unterstützte Eingaben

Freeda öffnet JPEG-, PNG-, TIFF-, BMP- und WebP-Bilder mit zwei gleich großen Ansichten nebeneinander: linkes Auge links, rechtes Auge rechts (`L|R`). Erwartet werden Full-SBS-Bilder, keine horizontal gestauchten Half-SBS-Bilder. Freeda erzeugt keine Stereotiefe und richtet die beiden Ansichten nicht zueinander aus.

## Ansichten

- **Parallelblick:** `L|R`.
- **Kreuzblick:** `R|L`.
- **Parallelblick + Kreuzblick:** beide Bildpaare in zwei Zeilen.
- **L–R–L:** drei Ansichten in einer Zeile; das linke Paar ermöglicht Parallelblick, das rechte Kreuzblick.

Die II/X-Symbole belegen einen Streifen in Rahmenbreite. Bei L–R–L stehen sie über den Zwischenräumen. Untertitel erscheinen unter den Bildern; ihr Bereich darf unabhängig vom Symbolstreifen anwachsen. Lange L–R–L-Untertitel werden bei Bedarf bis auf 75 % der gewählten Größe verkleinert und anschließend mit Auslassungspunkten gekürzt. Der unterste Untertitelbereich hat eine Rahmenbreite weniger Abstand.

## Web und Druck

Webbreiten beziehen sich auf die gesamte fertige Grafik einschließlich Rahmen. Zur Auswahl stehen Presets, eine frei eingegebene Breite und die Originalbreite. Das Seitenverhältnis der Halbbilder kann unverändert bleiben oder über ein Preset beziehungsweise ein eigenes Verhältnis angepasst werden.

Print bietet vorgegebene und eigene Druckformate, frei eingegebene positive ganzzahlige dpi und einen frei einstellbaren **Beschnittrand in mm** mit Nachkommastellen. Der Beschnittrand startet bei 0 mm; seine Vorschau ist eingeschaltet, damit ein hinzugefügter Rand sofort sichtbar wird. Das Druckformat wird vollständig ausgefüllt; das Seitenverhältnis der Halbbilder ergibt sich aus Papierformat, Ansicht, Rahmen und Untertiteln. Der Ausschnittdialog legt den passenden Bildausschnitt fest. Der Beschnittrand hat dieselbe Farbe wie der Rahmen. Optionale Schneidelinien und Schnittmarken sind grau. Die Vorschau passt sich dem verfügbaren Platz an; ihre Anzeigeskalierung ist unabhängig von den Export-dpi.

Die Rahmenbreite ist von 3 bis 5 % einstellbar, mit 4 % als Standard. Untertitelschrift und Untertitelgröße lassen sich anpassen; die Standardgröße beträgt 3,5 %. Die Schriftwahl betrifft ausschließlich Untertitel; die II/X-Symbole behalten ihre Standardschrift. Beide Prozentwerte beziehen sich auf die Breite eines Halbbilds und werden in Web und Print gleich berechnet.

## Bildausschnitte

**Ausschnitt anpassen** verwendet denselben relativen Ausschnitt für beide Stereoansichten. **Zurücksetzen** stellt Zoom und Position wieder her. Ein zuschaltbares Drittelraster erscheint getrennt über den beiden Ansichten und wird nie exportiert. Beim Batch lässt sich jedes Bild einzeln prüfen oder derselbe relative Ausschnitt übernehmen.

Normalerweise bleiben Ausschnitte während der Sitzung im Arbeitsspeicher. **Bildausschnitte merken** lädt gespeicherte Ausschnitte und schreibt bestätigte Änderungen in `freeda-crops.json` im jeweiligen Bilderordner. Die Einträge verwenden Dateinamen und relative Koordinaten, getrennt für Web und Print. Den Bilderordner zusammen mit dieser Datei verschieben, um die Ausschnitte zu erhalten.

Die Checkbox ist beim Start ausgeschaltet. Ausschalten lässt gespeicherte Dateien bestehen. Zurücksetzen entfernt nur den Eintrag des jeweiligen Bilds und Modus. Die Originalbilder bleiben unverändert.

## Stapelverarbeitung und Navigation

Beim Öffnen eines Einzelbilds stehen auch die anderen unterstützten Bilder seines Ordners für die Vorschau zur Verfügung. Vorheriges/Nächstes und Bild↑/Bild↓ wechseln zwischen ihnen, ohne am Ende wieder vorne zu beginnen. Der Einzelbildexport verarbeitet weiterhin nur das angezeigte Bild.

Die Auswahl mehrerer Dateien oder eines Ordners erzeugt einen Batch. Die Navigation wechselt die Vorschau; der Batch exportiert die gesamte Auswahl. Unterordner werden nur bei eingeschalteter entsprechender Checkbox einbezogen.

## Ausgabe und Ordner

Standardmäßig schreibt Freeda nach `output/web` oder `output/print` bei der Eingabe. Ein eigener Ausgabeordner lässt sich auswählen. Bei Ordner-Batches bleibt die relative Ordnerstruktur erhalten.

Dateien heißen beispielsweise `bild_freeda_web.jpg` oder `bild_freeda_print.png`. Bestehende Ausgabebilder am selben Ziel werden beim Export überschrieben. Originaldateien bleiben unverändert. Freeda exportiert JPEG oder PNG und verarbeitet die Bilder in 8-Bit-RGB.

## Einstellungen und Sprache

Deutsch und Englisch stehen zur Verfügung. Sprache und benannte Presets werden lokal in `settings.json` neben dem Programm gespeichert; dadurch bleibt das gesamte Programm portabel. Presets enthalten Export- und Darstellungseinstellungen. Bildpfade, Ausgabepfade, bildbezogene Untertiteltexte und individuelle Ausschnitte gehören nicht zu einem Preset.

Beim Start wird die zuletzt gewählte Sprache wiederhergestellt. Die übrigen Einstellungen verwenden die Standardwerte, bis ein Preset ausgewählt wird. Individuelle Ausschnittdateien liegen in den jeweiligen Bilderordnern, getrennt von den Programmeinstellungen.

## Quellcode und langfristige Nutzung

Das [GitHub-Repository](https://github.com/muelli1975/Freeda) enthält Quellcode und Build-Skripte. Für die Entwicklung werden Python 3.12 und die Abhängigkeiten aus `requirements-lock.txt` benötigt. `build_windows.ps1` erstellt das Windows-Paket; `scripts/build_unix.py` erstellt Linux- und macOS-Pakete auf den jeweiligen Systemen. Der Release-Ablauf prüft die Programme vor der Veröffentlichung.

Freeda soll unabhängig von Konten und Onlinediensten nutzbar bleiben. Aktive Wartung, Support, Bearbeitung von Issues oder Prüfung von Pull Requests können nicht garantiert werden.

## Lizenz

Freeda steht unter der [MIT-Lizenz](LICENSE), Copyright Christoph Müller. Fremdkomponenten behalten ihre eigenen Lizenzen. Die Pakete enthalten [Hinweise zu Fremdkomponenten](THIRD_PARTY_NOTICES.md) und Lizenzkopien im Ordner `licenses`.
