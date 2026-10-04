# Freeda 1.0 – Kurzstart

1. ZIP vollständig in einen frei beschreibbaren Ordner entpacken. `Freeda.exe` und `_internal` zusammen lassen.
2. `Freeda.exe` starten. Freeda beginnt mit der zuletzt gewählten Sprache, im Webmodus, mit 2048 Pixeln und den Standardwerten. Beim ersten Start ist Deutsch voreingestellt.
3. Ein Full-SBS-Bild (`L|R`), mehrere Dateien oder einen Bilderordner wählen. Unterordner sind optional.
4. Mit Vorheriges/Nächstes oder Bild↑/Bild↓ die Vorschau wechseln. Ein Einzelbildexport verarbeitet das angezeigte Bild; ein Batch die gesamte Auswahl.
5. Ansicht, Rahmen, Farben und Untertitel einstellen. L–R–L bietet links Parallelblick und rechts Kreuzblick. Lange Untertitel werden dort einzeilig begrenzt und nötigenfalls mit … gekürzt.
6. Für Web bei Bedarf das Seitenverhältnis eines Halbbilds wählen und „Ausschnitt anpassen …“ öffnen. Bei Print Druckformat, frei eingegebene dpi und Beschnittrand in mm einstellen. Beide Stereoansichten werden identisch zugeschnitten.
7. Export starten. Standardziel ist `output/web` beziehungsweise `output/print` bei der Eingabe. Alternativ einen eigenen Ausgabeordner wählen. Bestehende Ausgabedateien werden beim erneuten Export überschrieben. Originalbilder bleiben unverändert.

## Ausschnitte und Presets

Ausschnitte bleiben ohne Zusatzoption nur während der Sitzung erhalten. Mit „Bildausschnitte merken“ lädt Freeda gespeicherte Ausschnitte und schreibt bestätigte Änderungen in `freeda-crops.json` im jeweiligen Bilderordner. Die Checkbox ist beim Programmstart immer aus. Web- und Print-Ausschnitte werden getrennt gespeichert. Ausschalten löscht keine Datei; Zurücksetzen entfernt den jeweiligen Bild-/Moduseintrag. Den Bilderordner einschließlich dieser Datei gemeinsam verschieben.

Eigene Presets werden in `settings.json` neben der EXE gespeichert und ausschließlich beim Auswählen angewendet. Zum Update die Datei in den neuen Programmordner übernehmen. Originalbilder, bildbezogene Untertitel und individuelle Ausschnitte gehören nicht zu den Presets.

## Vorschau und Druck

Die Vorschau passt sich dem verfügbaren Platz an; ihre Anzeigeauflösung ist von den Export-dpi unabhängig. Bei Print startet der Beschnittrand mit 0 mm. „Beschnittrand in Vorschau zeigen“ ist eingeschaltet und zeigt einen eingegebenen zusätzlichen Rand sofort mit an. Schneidelinie und Schnittmarken sind mittelgrau.

Im Ausschnittdialog setzt „Zurücksetzen“ Zoom und Position auf den Ausgangsausschnitt zurück. In Serien lässt sich jedes Bild einzeln prüfen oder derselbe relative Ausschnitt übernehmen. Abbrechen beendet den Ablauf; bereits exportierte Dateien bleiben erhalten.

## Sprache

Deutsch und English stehen zur Verfügung. Die zuletzt gewählte Sprache wird in `settings.json` neben der EXE gespeichert und beim nächsten Start wieder verwendet.

Standard-Rahmenbreite: 4 % je Halbbild, einstellbar von 0 bis 5 %. Für die mobile Darstellung sind Parallelblick und Kreuzblick untereinander meist lesbarer als drei L–R–L-Ansichten nebeneinander.

Im Ausschnittdialog lässt sich das Drittelraster ein- und ausschalten. Es erscheint nur über den Bildflächen und wird nicht exportiert.

Bei Print wird das Druckformat vollständig ausgefüllt. Die Halbbildformate ergeben sich aus Druckformat, Ansicht, Rahmen und Beschriftung. Den Bildausschnitt im Ausschnittdialog wählen. Der Beschnittrand hat dieselbe Farbe wie der Rahmen. Freie Halbbildverhältnisse stehen weiterhin bei Web zur Verfügung.

„Untertitelschrift“ ändert nur die Untertitel. Die II/X-Symbole behalten unabhängig davon ihre Standardschrift. Die gewählte Untertitelschrift gehört zu den gespeicherten Presets.

Schlichte Stereokarte: Print → Parallelblick oder Kreuzblick → Rahmenbreite 0 % → Untertitel leer. „Blicksymbole anzeigen“ kann II/X auch bei vorhandenem Rahmen ausschalten. Bei 0 % werden sie automatisch weggelassen. Beide Einstellungen werden in Presets gespeichert; der Standard bleibt 4 % mit Blicksymbolen.
