# Freeda 1.0

Freeda converts full side-by-side stereo images into Freeview graphics for web and print.

- Parallel viewing, cross-eyed viewing, both layouts and L–R–L.
- Exact web output width, default 2048 pixels; linked crop editing and custom per-eye aspect ratios.
- Print sizes, freely entered dpi (default 300), bleed margin (default 0 mm) with visible bleed preview, grey cutting guides.
- Proportional frames (default 4% of eye width, range 3–5%), colors, rounded corners and adjustable captions (default 3.5%). L–R–L captions shorten with an ellipsis when necessary.
- Rule-of-thirds grid in the crop dialog, for each eye; never exported.
- Fixed sidebar width with wrapped long filenames.
- Single-image and batch export with preview navigation, optional subfolders and protected output filenames.
- Portable presets and remembered DE/EN language in settings.json next to the program. Crop remembering is optional and uses freeda-crops.json in the image folders.

Download the archive for your operating system and extract it completely. Windows requires Freeda.exe and _internal together. Linux launches the Freeda executable. macOS provides separate Apple Silicon and Intel apps; move the package to a writable folder before use. Presets on macOS are saved beside Freeda.app. QUICKSTART.md contains the German quick-start guide.

Windows binaries are not Authenticode-signed. macOS apps use the build tool's ad-hoc signature and are not Apple-notarized. Linux is built on Ubuntu 22.04 (glibc 2.35 or newer). Automated tests and native build smoke checks run on each target; manual desktop testing beyond Windows remains to be done.

The proposed geometric-mean sizing is not part of 1.0: frame and caption percentages still refer to the eye width.
