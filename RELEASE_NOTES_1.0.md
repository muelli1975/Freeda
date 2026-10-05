# Freeda 1.0

Freeda converts full side-by-side stereo images into Freeview graphics for web and print.

- Parallel viewing, cross-eyed viewing, both layouts and L–R–L.
- Exact web output width, default 2048 pixels; linked crop editing and custom per-eye aspect ratios.
- Print fills the selected paper format; image crops remain adjustable and bleed uses the frame colour.
- Print sizes, freely entered dpi (default 300), bleed margin (default 0 mm) with visible bleed preview, grey cutting guides.
- Proportional frames (default 4% of eye width, range 0–5%), colors, rounded corners and adjustable captions (default 3.5%). L–R–L captions shorten with an ellipsis when necessary.
- Caption font can be chosen independently of the standard II/X viewing symbols.
- Plain stereo cards with 0% frame; viewing symbols can be independently hidden. Defaults remain 4% with symbols enabled, and both settings are included in presets.
- ExifTool 13.59 bundled separately in tools, matching StereoFine/SplatTricia metadata handling. Capture metadata is copied where supported; previews, Orientation and MPF are excluded. Actual output dimensions and selected Print dpi are preserved. Failures produce a nonfatal warning while retaining the exported image.
- Rule-of-thirds grid in the crop dialog, for each eye; never exported.
- Fixed sidebar width with wrapped long filenames.
- Single-image and batch export with preview navigation, optional subfolders and stable output filenames that overwrite earlier exports.
- Portable presets and remembered DE/EN language in settings.json next to the program. Crop remembering is optional and uses freeda-crops.json in the image folders.

Download the archive for your operating system and extract it completely. Windows requires Freeda.exe and _internal together. Linux launches the Freeda executable. macOS provides separate Apple Silicon and Intel apps; move the package to a writable folder before use. Presets on macOS are saved beside Freeda.app. README_DE.md and README_EN.md provide matching German and English guides; QUICKSTART.md contains the German quick-start guide.

Windows binaries are not Authenticode-signed. macOS apps use the build tool's ad-hoc signature and are not Apple-notarized. Linux is built on Ubuntu 22.04 (glibc 2.35 or newer). Linux/macOS metadata transfer requires Perl; Windows includes the runtime. Automated tests and native build smoke checks run on each target; manual desktop testing beyond Windows remains to be done.
