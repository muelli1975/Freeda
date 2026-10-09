# Freeda 1.0

Freeda wandelt Full-SBS-Stereobilder in Freeview-Grafiken für Bildschirm und Druck um.

- Parallelblick, Kreuzblick, beide Ansichten gemeinsam und L–R–L.
- Exakte Ausgabebreite für Bildschirmgrafiken, standardmäßig 2048 Pixel; gekoppelte Ausschnittbearbeitung und frei wählbare Seitenverhältnisse je Halbbild.
- Druckausgabe im gewählten Papierformat mit einstellbaren Bildausschnitten und Beschnittzugabe in der Rahmenfarbe.
- Druckformate, frei eingegebene Auflösung in dpi (Standard 300), Beschnittzugabe (Standard 0 mm) mit sichtbarer Vorschau und grauen Schnittlinien.
- Proportionale Rahmen (Standard 4 % der Halbbildbreite, Bereich 0–5 %), Farben, abgerundete Ecken und einstellbare Untertitel (Standard 3,5 %). Bei L–R–L werden zu lange Untertitel mit Auslassungspunkten gekürzt.
- Die Schrift für Untertitel lässt sich unabhängig von den Blicksymbolen II/X wählen.
- Schlichte Stereokarten mit 0 % Rahmen; Blicksymbole können unabhängig davon ausgeblendet werden. Standard sind 4 % Rahmen und sichtbare Symbole; beide Einstellungen werden in Presets gespeichert.
- Übernahme der Aufnahmemetadaten mit dem mitgelieferten ExifTool 13.59, entsprechend StereoFine und SplatTricia. Eingebettete Vorschauen, Orientation und MPF werden ausgeschlossen; tatsächliche Ausgabeabmessungen und gewählte Druckauflösung bleiben erhalten. Bei einem Metadatenfehler bleibt das exportierte Bild erhalten und es erscheint ein Hinweis.
- Drittelraster für jedes Halbbild im Ausschnittdialog; das Raster wird nicht exportiert.
- Seitenleiste mit fester Breite und umbrochenen langen Dateinamen.
- Einheitliche Beschriftungen und Ausgabebedienung der Stereo-Tools: Der eigene Ausgabeordner bleibt auch inaktiv sichtbar, Eingabe- und Ausgabedialog merken sich während der Sitzung getrennte Orte, und während des Exports sind die Einstellungen gesperrt.
- Einzelbild- und Stapelausgabe mit Bildnavigation, optionalen Unterordnern und gleichbleibenden Ausgabedateinamen. Frühere Ausgaben mit demselben Namen werden ersetzt.
- Portable Presets und gespeicherte deutsche/englische Spracheinstellung in `settings.json` neben dem Programm. Ausschnitte können optional in `freeda-crops.json` in den Bildordnern gespeichert werden.

Das Archiv für dein Betriebssystem herunterladen und vollständig entpacken. Unter Windows müssen `Freeda.exe` und `_internal` zusammenbleiben. Unter Linux startet die ausführbare Datei `Freeda`. Für macOS gibt es getrennte Anwendungen für Apple Silicon und Intel; das Paket vor der Verwendung in einen beschreibbaren Ordner verschieben. Presets werden unter macOS neben `Freeda.app` gespeichert. `README_DE.md` und `README_EN.md` enthalten deutsche und englische Anleitungen; `QUICKSTART.md` enthält den deutschen Schnellstart.

Die Windows-Anwendung ist nicht mit Authenticode signiert. Die macOS-Anwendungen besitzen eine Ad-hoc-Signatur des Build-Werkzeugs und sind nicht von Apple notarisiert. Die Linux-Version wurde unter Ubuntu 22.04 erstellt und benötigt glibc 2.35 oder neuer. Für die Metadatenübernahme unter Linux und macOS ist Perl erforderlich; unter Windows ist die Laufzeitumgebung enthalten.
