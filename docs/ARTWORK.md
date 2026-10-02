# Anime artwork provenance

The current anime portrait was created for this project on **2026-10-01** with the built-in OpenAI image generation tool.

The character design was generated from the written brief below with **no reference images**. Subsequent edits used only that newly generated character to refine the close-up, three-quarter pose, remove its hair accessory and create its blink. No previous theme portrait, uploaded reference, stock illustration, named anime character, artist, or franchise was supplied as an image input.

The final design uses a short violet bob and a gently turned face with a tight crop, without the initial design's collar or hair clip. The initial draft and final source frames are retained; intermediate edits are documented in the prompts below.

## Sources and runtime assets

| File | Purpose |
| --- | --- |
| [artwork/anime-portrait-design-source.png](artwork/anime-portrait-design-source.png) | Initial text-only character draft |
| [artwork/anime-portrait-open-source.png](artwork/anime-portrait-open-source.png) | Final three-quarter close-up without a hair accessory |
| [artwork/anime-portrait-blink-source.png](artwork/anime-portrait-blink-source.png) | Blink edit of the final close-up |
| [../src/divoom_minitoo_codex/assets/anime_portrait.png](../src/divoom_minitoo_codex/assets/anime_portrait.png) | Native 78 × 78 open-eye frame |
| [../src/divoom_minitoo_codex/assets/anime_portrait_blink.png](../src/divoom_minitoo_codex/assets/anime_portrait_blink.png) | Native 78 × 78 complete closed-eye frame |

Only the two native frames are included in the Python package or used to render the device display. The full-resolution sources are kept here for maintenance and provenance.

Regenerate the native frames from these sources, then refresh the README gallery:

```sh
.venv/bin/python scripts/prepare_anime_artwork.py
.venv/bin/python scripts/generate_theme_gallery.py
```

The native export uses Lanczos downsampling and full RGB PNGs without palette reduction. The blink export preserves the open-eye frame outside the two eye sockets, keeping the cheeks, eyebrows, skin and background identical. The display renderer continues to switch between complete portrait frames.

The four color options remain `purple`, `red`, `blue` and `green`; the renderer recolors the violet hair, irises and related shadows while retaining the warm skin and blush.

The separate pixel themes are `anime-pixel` (adult in the chibi drawing style), `anime-pixel-chibi`, and `anime-pixel-detail` (the original detailed adult). Their source images and prompts are documented in [Pixel artwork provenance](ANIME_PIXEL_ARTWORK.md).

## Generation prompts

### Initial character design

Image inputs: none.

```text
Use case: stylized-concept.
Asset type: one square anime mascot portrait for a tiny 78 by 78 pixel region in a 160 by 128 device dashboard.
Primary request: create a NEW original fictional young adult anime woman from this written description only. Do not use, imitate, transform, or draw from any earlier images in this conversation, any existing character, artist, franchise, or artwork. This is a fresh character design.
Scene/backdrop: perfectly flat dark aubergine background (#1b1126), no scenery.
Subject: friendly thoughtful young adult woman with a short softly rounded violet bob ending at her jaw, symmetrical center-parted curtain bangs that leave her eyebrows and eyes unobstructed, and one tiny ivory diamond-shaped hair clip at the right edge of the picture. Rounded warm peach face, visible small ears, smaller almond-shaped violet eyes with one simple bright highlight per iris, a tiny relaxed closed smile, subtle soft coral blush, a little neck and a simple ivory crew-neck collar visible at the bottom. Look directly at the viewer, head upright. Eyebrows clearly visible. No strands cross the eyes. This character should have a clearly new silhouette, face proportions, hairstyle and eye design.
Style/medium: polished clean anime cel illustration, bold simple readable silhouettes, smooth anti-aliased contours, flat clean cel shading with at most two shades per region. Deliberately simple enough to remain crisp after high-quality downsampling to 78 by 78. Do not make pixel art.
Composition/framing: a single head-and-neck close-up centered in a perfectly square canvas. Face and bob fill most of the square, crown and chin fully visible with a 4 percent margin. No surrounding border, no panels, no sprite sheet.
Color palette: natural warm peach skin and coral blush; purple hair and purple irises centered around RGB hue 215/255 (violet-magenta) so the software can recolor these regions to red, blue and green. Dark plum linework. Ivory collar and clip. Background nearly black.
Constraints: one open-eye portrait only; no text, color swatches, labels, watermark, logos, famous character cues, clothing logos, gradients, paper texture, dithering or noisy shading. Both eyes fully open and anatomically natural. Keep the drawing visually uncomplicated; hair ends at jaw level.
```

### Face-only framing

Image input: the newly generated initial design only.

```text
Use case: precise-object-edit.
Input image: the newly generated original anime portrait is the sole edit target; no other images are references.
Primary request: preserve this exact newly designed character but change the composition to an extremely tight square FACE-ONLY close-up. Zoom into the existing face without changing its face or its features. The visible image must consist of her forehead/bangs, eyes, cheeks, mouth, jaw and framing bob hair. Her face fills almost the entire square. The top of the head and crown of the hair are naturally cropped at the top edge. The very bottom of her chin is just cropped by the bottom edge. There is absolutely NO neck, NO collar, NO shoulders and NO floating bust visible anywhere. Hair runs out of the sides and bottom of the canvas to make this a natural tight facial crop.
Composition: front-facing upright head, both eyes horizontally level, face centered horizontally, eye centers around 45 to 50 percent down the square. The face must be large and readable inside a 78 by 78 dashboard card. At most narrow dark aubergine background slivers between the hair and the square edges. Retain the short purple bob, central curtain bangs, one ivory diamond hair clip where it falls in the cropped framing, violet almond eyes, warm peach skin, coral blush and small calm smile of the target. Preserve identity, palette, clean anime rendering and eye design.
Constraints: both eyes open; create a true close-up crop with no anatomy invented at the lower edge. No neck, no collar, no text, no swatches, no watermark, no borders, no panels or icons. Do not use any earlier or external character design; only reframe the new input portrait.
```

### Three-quarter pose

Image input: the newly generated close-up only.

```text
Use case: precise-object-edit.
Input image: this newly generated original anime face is the SOLE target. No other images are references. Preserve her new character identity, violet short bob with center-part curtain bangs, ivory diamond hair clip, violet almond-shaped eyes, warm peach skin, subtle coral blush and small calm smile.
Primary request: change the head orientation from straight-on to a subtle natural three-quarter angle TURNED TOWARD THE LEFT SIDE OF THE PICTURE by about 15 to 20 degrees. Her eyes still look toward the viewer. The eye on the LEFT of the picture is slightly farther away and thus narrower; the eye on the RIGHT is nearer and slightly larger. The nose and mouth naturally follow the gently turned facial plane, with the nose a little left of the midpoint between the eyes and more of the right cheek visible. Add only a very slight natural head tilt, so the right eye sits a little higher than the left. Use convincing anime facial perspective, not a skewed flat frontal face. This must clearly look gently turned, not front-facing and not a side profile.
Framing: retain an extremely tight square FACE-ONLY close-up. Forehead/bangs are cropped at the top. Face fills the square; the lowest part of the chin is just cropped at the bottom edge. Hair flows out of the side and bottom edges. Show NO neck, collar, shoulders or floating bust. Eye centers around 45 to 50 percent down the square. Keep the face large and readable for a 78 by 78 display region.
Style and invariants: retain the new input character's polished clean anime cel illustration, flat two-tone shadows, smooth anti-aliased lines, violet palette, warm skin, short bob and ivory clip. Both eyes open. Do not copy or reference any other character, earlier illustration, external image, artist or franchise. No text, color swatches, logos, watermark, border or panels.
```

### Remove the hair accessory

Image input: the new three-quarter portrait only.

```text
Use case: precise-object-edit.
Input image: the new original three-quarter close-up anime portrait is the sole target.
Primary request: REMOVE ONLY the ivory diamond-shaped hair clip in the upper-right part of the image. Restore continuous violet hair beneath that accessory, following the adjacent smooth cel-shaded hair section and its natural strands. There should be no clip, pin, badge, ornament, symbol or accessory left in the hair.
Strict invariants: every other area of the image is unchanged. Preserve the exact three-quarter head orientation toward the left of the image, slight tilt, tight face-only crop, square canvas, face scale and position, short violet bob, central curtain bangs, eyes fully open, iris shapes, eyebrows, nose, lips, small smile, skin color, both cheeks and coral blush, ears, existing shadows, background and linework. Do not straighten the head, introduce new neck or shoulders, zoom or redraw any facial detail. Edit only the small former clip region in the upper-right hair. No text, watermark or border.
```

### Final blink edit

Image input: `artwork/anime-portrait-open-source.png` only.

```text
Use case: precise-object-edit.
Input image: the one newly generated original three-quarter anime face is the SOLE edit target. No other image is a reference.
Primary request: change ONLY the two eye openings to a relaxed natural blink. Both upper eyelids descend fully over the irises. Thin dark plum eyelid contours and simple outer lashes close each eye near the lower part of its original opening, following the perspective and head tilt. The eye on the left of the image is farther away and smaller; the eye on the right is nearer and larger. Both are fully closed. Use a calm natural blink rather than smiling upward crescents. Fill former whites and irises with matching skin only inside their original eye sockets.
Strict invariants: the three-quarter head orientation, slight tilt, face-only close framing, canvas dimensions, head scale and position, nose, lips, smile, eyebrows, cheeks, coral blush color and intensity, skin tone, ears, hair strands, central part, short bob, absence of hair accessories and all background pixels remain exactly unchanged. The hair stays in front of the eyelids and is not repainted. Keep the face at the identical angle; do not straighten the head or face. Do not change either cheek or any other facial region. Do not add any neck, collar or shoulders. Only the two eyelids may change.
No other art, earlier portraits or external character references; no text, logos, watermark, color swatches, panels or borders.
Keep the hair free of clips, pins, badges, jewels or decorations; no hair accessory may be added.
```
