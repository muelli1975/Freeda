# Freeda 1.0

Freeda erstellt aus Full-Side-by-Side-Stereobildern (SBS) Freeview-Darstellungen für Web und Druck. Die Anleitung für die portable Windows-Ausgabe steht in [QUICKSTART.md](QUICKSTART.md).

## Builds und Downloads

Die finalen Pakete stehen unter [GitHub Releases](https://github.com/muelli1975/Freeda/releases/tag/v1.0): Windows x64, Linux x64 sowie macOS Apple Silicon und Intel. `build_windows.ps1` erstellt eine isolierte Buildumgebung, prüft die automatischen Tests und erzeugt `release/Freeda_1.0_Windows_x64.zip` samt SHA-256-Prüfsumme. Die nativen Linux-/macOS-Pakete baut `scripts/build_unix.py` auf dem jeweiligen System. Für den separaten Windows-Oberflächentest: `.venv-build/Scripts/python.exe tests/gui_feedback_smoke.py`.

## Funktionen

- einzelne Full-SBS-Bilder, mehrere Dateien oder ganze Ordner laden
- Ordner im Batch verarbeiten, Unterordner optional einbeziehen
- Parallelblick, Kreuzblick, beide Ansichten gemeinsam oder L–R–L ausgeben
- Web-Ausgabe in Originalgröße, 1280, 1600, 1920, 2048, 3840 Pixel oder frei wählbarer Breite
- proportionaler Außenrahmen sowie gleich breite Mittel- und Querstege
- optionale Rundung der äußeren und inneren Ecken
- optionale Untertitel unter beiden Halbbildern
- frei wählbare Schriftart für Untertitel
- Farbvorgaben für Rahmen und Beschriftung sowie benutzerdefinierte Farben
- Live-Vorschau
- PNG-Ausgabe mit Transparenz
- JPEG-Ausgabe mit Qualität 90 und 4:4:4 ohne Chroma-Subsampling

## Druck

Der Druckmodus unterstützt feste Ausgabeformate, frei eingegebene positive ganzzahlige dpi (Standard 300), einen frei einstellbaren Beschnittrand in mm und einen gekoppelten Bildausschnitt für beide Stereo-Halbbilder.

Enthaltene Formatvorgaben:

- Foto 9 × 13 cm
- Foto 10 × 15 cm
- Foto 11 × 17 cm
- Foto 13 × 18 cm
- Foto 15 × 20 cm
- Foto 20 × 30 cm
- DIN A6
- klassische Stereokarte 7 × 3½ Zoll
- Stereokarte 18 × 9 cm
- Raumbildkarte 13 × 6 cm
- benutzerdefiniertes Format

Bei Druck-Batches kann derselbe Ausschnitt für eine Serie übernommen oder für jedes Bild einzeln gesetzt werden. Im manuellen Modus pausiert der Batch bei jedem Bild, bis der Ausschnitt übernommen oder das Bild übersprungen wird.

Optional können Schneidelinien beziehungsweise Schnittmarken mit ausgegeben werden.

## Lizenz

MIT License — Christoph Müller.

## Startwerte, Bildausschnitt und Navigation

Freeda startet mit der zuletzt gewählten Sprache, im Webmodus mit 2048 Pixeln und Standardwerten. Ohne gespeicherte Sprachwahl ist Deutsch voreingestellt. Eigene Presets werden ausschließlich auf Wunsch angewendet und bleiben portabel in `settings.json` neben der EXE. Die Sprachwahl wird ebenfalls portabel in `settings.json` gespeichert.

Web unterstützt Original, 1:1, 4:3, 3:2, 16:9, Hochformate und freie positive Seitenverhältnisse (Breite:Höhe oder Dezimalzahl). Die Breite bezeichnet weiterhin die komplette Ausgabe. Beide Stereoansichten erhalten denselben Ausschnitt. „Ausschnitt anpassen …“ funktioniert bei Web und Print; manuelle Ausschnitte gehören zum Bild und werden nicht in Presets gespeichert. Für Serien lässt sich jedes Bild einzeln prüfen oder der erste Ausschnitt relativ auf weitere Bilder übernehmen. Ein gewähltes Seitenverhältnis wird auch bei unterschiedlichen Eingabeformaten eingehalten. Mit Original und deaktivierter Exportprüfung läuft der Webexport ohne Dialog.

Vorheriges/Nächstes und Bild↑/Bild↓ blättern in der Vorschau. Einzelbildexport verarbeitet nur das angezeigte Bild; Batch exportiert die komplette Auswahl. Vorschauposition und Verarbeitungsfortschritt werden getrennt angezeigt. Ein einzeln gewähltes Bild kann durch seine Nachbarbilder im gleichen Ordner navigiert werden. Eine Ordnerauswahl ist stets ein Batch, auch mit nur einem Bild.

Lange Untertitel umbrechen innerhalb jedes Halbbilds. Bei L–R–L wird derselbe Untertitel unter allen drei Ansichten in einer Zeile wiederholt, damit beide Blickmethoden übereinstimmende Beschriftungen sehen. Lange Texte werden zunächst auf mindestens 75 % der gewählten Schriftgröße verkleinert und anschließend nötigenfalls mit … gekürzt. II/X bleiben als Blickhinweise erhalten. Web wächst dafür in der Höhe; Print behält das Druckformat und verkleinert entsprechend den Bildbereich. Schneidelinie und Schnittmarken sind unabhängig vom Rahmen mittelgrau (#808080).

Angepasste Ausschnitte bleiben standardmäßig nur pro Bild und getrennt für Web/Print im Arbeitsspeicher. „Bildausschnitte merken“ ist beim Start aus. Aktiviert die Checkbox, um vorhandene Ausschnitte zu laden und bestätigte Änderungen automatisch in `freeda-crops.json` im jeweiligen Bilderordner zu speichern. Die Datei verwendet Dateinamen und relative Ausschnittkoordinaten; beim Verschieben des ganzen Bilderordners kommen die Ausschnitte mit. Auch das Seitenverhältnis wird als Zusatzinformation gespeichert. Presets enthalten keine individuellen Bildausschnitte. Ausschalten belässt aktuelle Ausschnitte im Arbeitsspeicher und die Datei auf der Festplatte. Zurücksetzen entfernt nur den Ausschnitt des aktuellen Bilds im aktuellen Modus aus der Datei. Originalbilder werden nicht geändert.

Standard-Rahmenbreite: 4 % je Halbbild, einstellbar von 3 bis 5 %. Für die mobile Darstellung sind Parallelblick und Kreuzblick untereinander meist lesbarer als drei L–R–L-Ansichten nebeneinander.

Der Beschnittrand startet mit 0 mm. „Beschnittrand in Vorschau zeigen“ ist standardmäßig eingeschaltet, damit jeder eingegebene Rand sofort sichtbar wird.

## Plattformen

Linux x64 wird auf Ubuntu 22.04 gebaut und benötigt glibc 2.35 oder neuer sowie eine grafische Desktop-Sitzung. macOS wird getrennt für Apple Silicon und Intel gebaut. Einstellungen liegen auf macOS neben `Freeda.app`; auf Windows/Linux neben dem ausführbaren Programm. Den vollständigen Programmordner an einen beschreibbaren Ort verschieben. Die Programme sind nicht mit einem Entwicklerzertifikat signiert beziehungsweise Apple-notarisiert.

Der GitHub-Releaseablauf prüft und veröffentlicht zunächst Windows. Linux und macOS werden anschließend nativ gebaut, geprüft und dem gleichen Release hinzugefügt. Automatisierte GUI-Exportprüfungen laufen auf Windows und Linux; macOS erhält Unit-Tests und einen Starttest des fertigen App-Binaries. Ein manueller Desktop-Test auf Linux/macOS ist noch nicht erfolgt.

Die Prozentwerte beziehen sich in 1.0 weiter auf die Halbbildbreite. Die vorgeschlagene gemeinsame Bezugsgröße aus Breite und Höhe bleibt eine spätere Änderung.
