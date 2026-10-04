# Freeda

Freeda creates free-view stereoscopic layouts from Full Side-by-Side images for web and print.

> Development status: early 1.0 development.

## Current development build

The first working foundation already includes:

- Full-SBS input (left/right)
- single files, multiple files and recursive folder batches
- parallel view, cross view, or both
- exact web row widths: Original, 1280, 1600, 1920, 2048, 3840, custom
- proportional frame width, defined relative to one half image
- matching outer frame, centre divider and horizontal divider
- default frame color `#111111`
- `II` / `X` and captions in light gold `#c6a95e`
- stereo-safe duplicated captions
- selectable Windows font for captions
- optional inner and outer corner rounding
- PNG with transparency
- JPEG quality 90 with 4:4:4 chroma (no subsampling)
- live preview
- batch export
- shared Stereo-Tools completion sound

## Print design

The print path is being built around physical size, DPI and bleed. Presets include
DIN A6, common German photo-lab sizes (9 × 13, 10 × 15, 11 × 17, 13 × 18,
15 × 20 and 20 × 30 cm), historical stereo-card sizes (7 × 3½ in, 18 × 9 cm,
13 × 6 cm) and a custom size, at 300 or 600 dpi.

Manual print cropping is explicitly batch-aware:

- **Manual crop per image**: the batch pauses on every image until the crop is
  accepted, skipped or the batch is cancelled.
- **Reuse crop**: one relative crop can be reused for a similarly composed
  series.

The crop is always applied identically to both stereo half images.

## Development

Runtime dependencies are pinned in `requirements-lock.txt`. A Windows
PyInstaller build is defined by `Freeda.spec` and `build_windows.ps1`.

Automated tests run on Windows/Python 3.12 through GitHub Actions.

The application follows the shared StereoFine / SplatTricia dark-and-gold
design standard documented in `DESIGN_STANDARD_STEREOTOOLS.txt`.

## License

MIT License — Christoph Müller.
