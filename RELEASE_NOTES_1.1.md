# Freeda 1.1

Freeda 1.1 expands stereo image styling and adds more control over printed stereo cards. The main improvements over version 1.0:

- **Classic card shapes:** A classic arch and independently adjustable top and bottom image corner radii. Sliders control image radii, outer radius and arch height in Web and Print. PNG retains transparent outer corners; JPEG fills them with black in Web and white in Print.
- **Precise print layouts:** Templates for Holmes cards, 18 × 9 cm stereo cards and 13 × 6 cm Raumbild cards. Side margins, centre gap, top and bottom areas, row spacing and caption padding can be set in millimetres. Card geometry remains independent of dpi.
- **Logos instead of captions:** An image file can replace the text caption. Logos retain their proportions and can use an exact print height in mm. Imported logos and their presets remain portable when the program folder is moved.
- **Expanded colour palette:** 16 colour presets instead of ten, including additional combinations for classic and vintage stereo cards. Dark colours precede light colours; Night Gold remains the default and first preset.
- **Improved captions:** The default size increases from 3.5 to 4%. Revised spacing and adjustable Print padding create more balanced caption areas. The font picker previews the entered caption text.
- **Web sizing by long edge:** Pixel sizes now refer to the longest side of the finished graphic, including its frame and caption. The selected size therefore also has a clear meaning for portrait outputs.
- **Simpler cropping:** Single images export the displayed crop; reviewing it again during export is optional. Reset restores position and zoom while retaining the selected Web aspect ratio.
- **Revised folder processing:** One input folder can be processed together with its subfolders. The default destination is `output` in the program folder; a custom output folder remains available. Folder batches retain the source folder's name and relative tree, keeping equal filenames in different subfolders separate.
- **More reliable batch processing:** Discovery and export run in the background with progress, cancellation and an error summary. Manual crop dialogs pause the batch. Discovery excludes output folders and existing Freeda exports; crop records remain beside their respective originals. Incomplete exports never replace existing output images.
- **More consistent interface:** Colours and disabled controls follow the tool family. Rectangular preview areas preserve the available preview space.

Existing Freeda 1.0 presets remain usable.
