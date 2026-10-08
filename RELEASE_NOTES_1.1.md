# Freeda 1.1

## Deutsch

- Ein Eingabeordner mit optionaler rekursiver Verarbeitung über **Unterordner mitverarbeiten**. Gleichnamige Bilder in verschiedenen Unterordnern behalten getrennte Ziele.
- Standardziel ist **output im Programmordner**. Ordner-Batches übernehmen den Namen des Eingabeordners und seine Unterordnerstruktur. Ein eigenes Ziel und die ausdrücklich einschaltbare Ausgabe im Input-Ordner bleiben möglich.
- Die Suche schließt das Ausgabeziel und vorhandene Freeda-Ausgaben aus. Die Eingabeliste steht vor dem Export fest; erneute Durchläufe überschreiben ihre bisherigen Ausgaben, ohne Originale zu verändern.
- Einlesen, Web und Print bleiben bedienbar und abbrechbar. Ausschnittdialoge pausieren den Export. Fertige Dateien bleiben erhalten; unvollständige Exporte ersetzen keine vorhandenen Ausgaben. Dateifehler werden gesammelt gemeldet, die übrigen Bilder weiterverarbeitet.
- Ausschnitte bleiben optional in **freeda-crops.json im konkreten Quellordner**, getrennt für Web und Print. Rekursive Verarbeitung lädt und speichert sie im jeweiligen Bilderordner.
- Die weiteren 1.1-Funktionen bleiben erhalten: lange Seite bei Web, Kartenvorlagen und genaue mm-Ränder, unabhängige Eckenradien und klassischer Bogen, 16 Farbpresets, Untertitel oder portable Logos und Lanczos-Skalierung.

## English

- One input folder with optional recursive processing through **Include subfolders**. Equal filenames in different subfolders retain separate destinations.
- **output in the program folder** is the default. Folder batches preserve the input folder's name and relative tree. A custom destination and an explicitly enabled output subfolder inside the input folder remain available.
- Discovery excludes the output destination and existing Freeda exports. The input list is frozen before export; reruns overwrite previous outputs without modifying originals.
- Discovery, Web and Print remain responsive and cancellable. Crop dialogs pause export. Completed files remain; incomplete exports never replace previous output files. Errors are collected while healthy images continue.
- Optional crop records remain in **freeda-crops.json in each original's source folder**, separately for Web and Print. Recursive processing loads and saves them in their respective folders.
- Existing 1.1 features remain: Web long-edge sizing, card templates and precise mm margins, independent corner radii and classic arches, 16 colour presets, captions or portable logos, and Lanczos scaling.

Extract the complete package into a writable folder. Keep `Freeda.exe`, `_internal` and `tools` together on Windows. To retain portable settings, copy `settings.json` and `logos` from the previous program folder. Crop records stay with their source images. Print cards at **100% / actual size**. ExifTool 13.59 remains bundled in `tools`.

The updated folder workflow is included in the Windows x64, Linux x64, macOS Apple Silicon and macOS Intel packages. Windows binaries are not Authenticode-signed. macOS apps are ad-hoc signed and not Apple-notarized. Linux requires glibc 2.35 or newer; Linux/macOS metadata transfer requires Perl.
