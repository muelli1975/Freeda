# Freeda 1.1 – Kurzstart

1. ZIP vollständig in einen frei beschreibbaren Ordner entpacken. `Freeda.exe`, `_internal` und `tools` zusammen lassen.
2. `Freeda.exe` starten. Freeda beginnt mit der zuletzt gewählten Sprache, im Webmodus, mit 2048 Pixeln und den Standardwerten. Beim ersten Start ist Deutsch voreingestellt.
3. Ein Full-SBS-Bild (`L|R`), mehrere Dateien oder einen Bilderordner wählen. Unterordner sind optional.
4. Mit Vorheriges/Nächstes oder Bild↑/Bild↓ die Vorschau wechseln. Ein Einzelbildexport verarbeitet das angezeigte Bild; ein Batch die gesamte Auswahl.
5. Ansicht, Rahmen, Farben und Untertitel einstellen. L–R–L bietet links Parallelblick und rechts Kreuzblick. Lange Untertitel werden dort einzeilig begrenzt und nötigenfalls mit … gekürzt.
6. Für Web bei Bedarf das Seitenverhältnis eines Halbbilds wählen und „Ausschnitt anpassen …“ öffnen. Bei Print Druckformat, frei eingegebene dpi und Beschnittrand in mm einstellen. Beide Stereoansichten werden identisch zugeschnitten.
7. Export starten. Mit „Unterordner im Input-Ordner verwenden“ ist das Standardziel `output/web` beziehungsweise `output/print` im Input-Ordner. Alternativ einen eigenen Ausgabeordner wählen. Bestehende Ausgabedateien werden beim erneuten Export überschrieben. Originalbilder bleiben unverändert.

## Ausschnitte und Presets

Ausschnitte bleiben ohne Zusatzoption nur während der Sitzung erhalten. Mit „Bildausschnitte merken“ lädt Freeda gespeicherte Ausschnitte und schreibt bestätigte Änderungen in `freeda-crops.json` im jeweiligen Bilderordner. Die Checkbox ist beim Programmstart immer aus. Web- und Print-Ausschnitte werden getrennt gespeichert. Ausschalten löscht keine Datei; Zurücksetzen entfernt den jeweiligen Bild-/Moduseintrag. Den Bilderordner einschließlich dieser Datei gemeinsam verschieben.

Eigene Presets werden in `settings.json` neben der EXE gespeichert und ausschließlich beim Auswählen angewendet. Zum Update die Datei in den neuen Programmordner übernehmen. Originalbilder, bildbezogene Untertitel und individuelle Ausschnitte gehören nicht zu den Presets.

## Vorschau und Druck

Unter „Beschriftung“ lassen sich Text oder Logo wählen. „Logo wählen …“ kopiert eine Bilddatei unverändert in `logos` neben dem Programm. Ein transparentes PNG eignet sich besonders gut. Das Logo erscheint identisch unter jedem Halbbild. Die Höhe ist prozentual, bei Print zusätzlich in mm einstellbar; das Seitenverhältnis bleibt erhalten und die Breite wird auf 90 % des Halbbilds begrenzt. Bei exakten Rändern muss das Logo in den unteren Bereich passen. Logo und Größe gehören zu Presets; beim Update oder Verschieben auch den Ordner `logos` mitnehmen. Der Startstandard bleibt Text.

Bei Print liefern Holmes-Karte, Stereokarte 18 × 9 cm und Raumbildkarte 13 × 6 cm fertige, anpassbare Layouts. Sie verwenden Parallelblick ohne Blicksymbole und lassen Farben, Schrift und Untertiteltext unverändert. „Ränder und Bildfenster anpassen …“ klappt genaue Millimeterwerte auf. Der untere Bereich umfasst den Untertitel; bei Platzmangel erscheint ein Hinweis. Bildfenstermaße und Bildmittenabstand werden angezeigt. „Vorlage zurücksetzen“ stellt die gewählte Vorlage wieder her. Die Vorlagen sind Layoutvorschläge und müssen zum eigenen Betrachter und Stereobild passen.

Alternativ „Freies Layout“ für proportionale Rahmen verwenden. Exakte mm-Ränder und Prozentrahmen sind alternative Einstellungen. Untertitel starten mit 4 %; bei Print sind auch frei eingegebene Punktgrößen und Textabstände in mm möglich. Leere Textabstandsfelder verwenden automatische Abstände. Karten mit 100 % / tatsächlicher Größe drucken, ohne automatische Seitenanpassung.

„Bildkontur“ bietet Rechteck, gerundete Ecken, nur oben gerundete Ecken und einen klassischen Bogen mit eigener Höheneinstellung. Der Außenradius rundet die fertige Grafik. JPEG füllt transparente Außenecken bei Web schwarz und bei Print weiß; PNG erhält die Transparenz. Die ausgesparten Ecken der Bildfenster bleiben in Rahmenfarbe. Die 16 Farbpresets stehen dunkel vor hell, Nachtgold bleibt Standard.

Die Vorschau passt sich dem verfügbaren Platz an; ihre Anzeigeauflösung ist von den Export-dpi unabhängig. Bei Print startet der Beschnittrand mit 0 mm. „Beschnittrand in Vorschau zeigen“ ist eingeschaltet und zeigt einen eingegebenen zusätzlichen Rand sofort mit an. Schneidelinie und Schnittmarken sind mittelgrau.

Im Ausschnittdialog setzt „Zurücksetzen“ Zoom und Position auf den Ausgangsausschnitt zurück. In Serien lässt sich jedes Bild einzeln prüfen oder derselbe relative Ausschnitt übernehmen. Abbrechen beendet den Ablauf; bereits exportierte Dateien bleiben erhalten.

## Sprache

Deutsch und English stehen zur Verfügung. Die zuletzt gewählte Sprache wird in `settings.json` neben der EXE gespeichert und beim nächsten Start wieder verwendet.

Standard-Rahmenbreite: 4 % je Halbbild, einstellbar von 0 bis 5 %. Für die mobile Darstellung sind Parallelblick und Kreuzblick untereinander meist lesbarer als drei L–R–L-Ansichten nebeneinander.

Im Ausschnittdialog lässt sich das Drittelraster ein- und ausschalten. Es erscheint nur über den Bildflächen und wird nicht exportiert.

Bei Print wird das Druckformat vollständig ausgefüllt. Die Halbbildformate ergeben sich aus Druckformat, Ansicht, Rahmen und Beschriftung. Den Bildausschnitt im Ausschnittdialog wählen. Der Beschnittrand hat dieselbe Farbe wie der Rahmen. Freie Halbbildverhältnisse stehen weiterhin bei Web zur Verfügung.

„Untertitelschrift“ ändert nur die Untertitel. Die II/X-Symbole behalten unabhängig davon ihre Standardschrift. Die gewählte Untertitelschrift gehört zu den gespeicherten Presets.

Schlichte Stereokarte: Print → Parallelblick oder Kreuzblick → Rahmenbreite 0 % → Untertitel leer. „Blicksymbole anzeigen“ kann II/X auch bei vorhandenem Rahmen ausschalten. Bei 0 % werden sie automatisch weggelassen. Beide Einstellungen werden in Presets gespeichert; der Standard bleibt 4 % mit Blicksymbolen.

## Metadaten

ExifTool übernimmt geeignete Metadaten automatisch beim Export. Vorschaubilder, Orientation und MPF/MPO-Daten werden nicht übernommen; neue Bildabmessungen und gewählte Druck-dpi bleiben erhalten. Originale werden nicht verändert. Bei einem Metadatenfehler bleibt das fertige Bild erhalten und Freeda zeigt einen Hinweis. Den Ordner `tools` mit seinen Begleitdateien zusammenhalten. Unter Linux und macOS wird Perl benötigt, unter Windows ist die Laufzeitumgebung enthalten.
