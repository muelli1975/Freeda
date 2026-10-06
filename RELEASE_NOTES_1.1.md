# Freeda 1.1

Freeda frames full side-by-side stereo images for Freeview viewing and printing. Version 1.1 adds editable card layouts, graphic logos and more control over image windows and captions.

- Four image shapes: rectangular, all corners rounded, top corners rounded and a classic arch with adjustable height. Identical antialiased contours in Web, Print and crop previews.
- Holmes (177.8 × 88.9 mm), 18 × 9 cm and Raumbild (13 × 6 cm) card templates, with explicit margins and image-window dimensions. Templates retain colours, caption text and fonts. These are editable layout suggestions for checking against your viewer and images.
- A collapsible precise Print section for outer margins, centre gap, top margin, bottom area and, for two rows, row spacing. Physical dimensions and crop aspect remain stable when changing dpi.
- The bottom area includes captions. Exact layouts report insufficient space instead of silently shrinking image windows. Window dimensions and image-centre distance are shown; edited templates are marked and can be reset.
- Caption default increased to 4%, with more compact font-based padding. Optional point sizes and millimetre text padding in Print.
- Choose Text or Logo under Caption. Logos are centred and repeated identically below every stereo view, including L–R–L and both rows of the combined layout. Switching retains the current text and logo selection during the session.
- Transparent PNG and other supported raster images are imported without changing the original file. Lanczos scaling preserves aspect ratio; width is capped at 90% of a view. Maximum height starts at 6% and is adjustable from 1–20%, with optional millimetre heights in Print. Exact layouts report when the logo exceeds the bottom area; automatic logo padding can be overridden in mm.
- Logo copies live in the portable `logos` folder beside `settings.json`; presets store relative references. Text remains the startup default. Missing files produce a clear message; German and English controls, crop previews and batch export use the same behaviour.
- Six additional light colour presets: Cream, Parchment, Honey card, Sage paper, Blue grey and Dusty rose. All ten original combinations remain. Dark presets precede light ones; Night gold stays first and the default.
- Outer rounding also works in Print. PNG preserves transparent outer corners; JPEG fills them with black in Web and white in Print. The preview matches the chosen format. Inner corners and bleed retain the frame colour.
- New controls are available in German and English and are included in portable presets; existing 1.0 presets remain usable. Language is remembered; other startup defaults remain Web, 2048 pixels, Night gold, 4% frame, 300 dpi and 0 mm bleed.

Extract the complete package for your operating system. On Windows, keep `Freeda.exe`, `_internal` and `tools` together. Copy your existing `settings.json` and the `logos` folder, if present, beside the new program to retain language, named presets and logos. Individual crop records remain in their image folders. Existing output images are overwritten; input images and original logo files remain unchanged.

Print at **100% / actual size** to preserve card dimensions. ExifTool 13.59 remains bundled in `tools`. Linux/macOS metadata transfer requires Perl; Windows includes its runtime. Windows binaries are not Authenticode-signed. macOS apps are ad-hoc signed and not Apple-notarized. Linux requires glibc 2.35 or newer. Automated tests and packaged startup checks run on every target, with GUI export checks on Windows and Linux; manual desktop testing beyond Windows remains pending.
