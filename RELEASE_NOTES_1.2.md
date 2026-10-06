# Freeda 1.2

Freeda 1.2 adds an optional graphic logo in place of caption text, retaining the card templates, shapes, colours and precise Print controls introduced in 1.1.

- Choose Text or Logo under Caption. Logos are centred and repeated identically below every stereo view, including L–R–L and both rows of the combined layout.
- Transparent PNG and other supported raster images are imported without changing the original file. Lanczos scaling preserves aspect ratio; width is capped at 90% of a view. Height starts at 6% and is adjustable from 1–20%, with optional millimetre heights in Print.
- With exact Print margins, the logo must fit the bottom area. Insufficient space produces a message rather than shrinking the image windows. Automatic logo padding can be overridden in mm.
- Logo copies live in the portable `logos` folder beside `settings.json`; presets store relative references. Copy both when moving or updating the application. Existing presets from 1.0 and 1.1 remain usable, and Text remains the startup default.
- German and English logo controls, preview, crop grids, batch export and missing-file messages use the same behaviour.

Download and extract the complete package for your platform. Keep the application, its support folders and `tools` together. Existing output images are overwritten; source images and imported logo originals remain unchanged. PNG retains transparent outer corners; JPEG fills them black for Web and white for Print.

Print cards at **100% / actual size**. Windows binaries are not Authenticode-signed. macOS apps are ad-hoc signed and not Apple-notarized. Linux requires glibc 2.35 or newer. ExifTool 13.59 remains bundled in `tools`; Linux/macOS require Perl for metadata transfer. Automated tests and native startup checks run on all four platforms, with GUI export checks on Windows and Linux; manual desktop testing beyond Windows remains pending.
