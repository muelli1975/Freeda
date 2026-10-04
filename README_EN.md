# Freeda 1.0

Freeda turns full side-by-side stereo images (L|R) into Freeview graphics for web and print.

[Download Freeda 1.0](https://github.com/muelli1975/Freeda/releases/tag/v1.0)

Extract the complete package. Windows: keep `Freeda.exe` and `_internal` together. Linux: run the `Freeda` executable in a graphical desktop session (glibc 2.35 or newer). macOS: choose Apple Silicon or Intel and move the complete package to a writable folder before launching `Freeda.app`.

The first launch uses German. Select English via Language; the last language is remembered. Each launch otherwise starts in Web mode, at 2048 pixels, with a 4% frame, 3.5% caption size, 300 dpi, zero bleed and enabled bleed preview. Saved presets are only applied when explicitly selected.

## Images and export

Load one full-SBS image, several files or a folder. Subfolders are optional. Previous/Next and Page Up/Page Down change the preview. Single-image export processes the displayed image; batch export processes the entire selection. Output goes into `output/web` or `output/print` beside the inputs, or to a custom folder. Existing output files receive distinct filenames.

Choose parallel viewing, cross-eyed viewing, both in two rows, or L–R–L in one row. Web widths describe the complete finished graphic. Custom per-eye aspect ratios and linked crop editing apply the same crop to both views. In batches, inspect every image or reuse the relative crop.

Print supports preset/custom dimensions, freely entered positive integer dpi and decimal bleed margins. The preview includes any entered bleed. Grey cutting guides are optional. Preview display resolution is separate from export dpi.

Captions and fonts are adjustable. L–R–L repeats the same caption in all three views, reduces its size to at least 75% when necessary, then truncates with an ellipsis. The final caption area has one frame width less padding. Frame and caption percentages refer to eye width in 1.0.

The crop dialog includes a toggleable rule-of-thirds grid for each view. It is preview-only. Reset restores zoom and position.

## Portable settings

Presets and language are stored in `settings.json` beside the executable, or beside `Freeda.app` on macOS. Copy this file to a new program folder during updates.

Crops normally stay in memory for the session. Enable Remember image crops to load/save `freeda-crops.json` in each image folder. It stores relative crops by filename, separately for Web and Print. Moving the image folder with its sidecar preserves them. The checkbox is off at startup. Disabling it leaves the file intact; resetting a crop removes only that image/mode entry. Original images remain unchanged.

## Release verification

Native Windows, Linux and macOS builds run automated tests and a packaged startup check. GUI export checks run on Windows and Linux. Manual desktop testing beyond Windows is still pending. Windows is not Authenticode-signed; macOS apps are ad-hoc signed, not Apple-notarized.

Freeda is licensed under MIT; third-party notices and license copies are included.
