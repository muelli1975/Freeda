# Portable ExifTool

Freeda bundles the official ExifTool 13.59 distribution separately from its MIT-licensed code, matching StereoFine's current build version. Windows uses `tools/exiftool.exe` and `tools/exiftool_files`; Linux uses `tools/exiftool` and `tools/lib`. On macOS these files are inside `Freeda.app/Contents/MacOS/tools`, as in StereoFine.

Run `python scripts/prepare_exiftool.py` on the build host to obtain the platform-appropriate archive. Its SHA-256 is pinned to the publisher's `checksums-13.59.txt`. Original support files, documentation and licence material are retained. Binary/support files are not committed to the application repository.

ExifTool is copyright Phil Harvey and may be distributed under the same terms as Perl (Artistic License or GNU GPL). The Windows distribution also contains its own Perl runtime and launcher notices. See the original distribution material and <https://exiftool.org/>. Linux and macOS require a Perl interpreter, as with StereoFine.
