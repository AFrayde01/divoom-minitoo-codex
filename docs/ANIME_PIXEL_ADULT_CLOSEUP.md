# Adult pixel portrait close-up and RGB export

The adult `anime-pixel` portrait was reframed on **2026-10-02** using the **built-in OpenAI image generation tool**. Inputs were only this project's own generated portrait and the matching blink draft. No external illustration, named artist, character or franchise reference was used.

**Historical revision:** the runtime now uses the [restored original portrait](ANIME_PIXEL_ADULT_ORIGINAL_RGB.md). The sources, eye regions and measurements below describe this preceding close-up.

## Close-up sources and shared runtime asset paths

- [Close-up open-eye source](artwork/anime-pixel-adult-closeup-open-source.png)
- [Matching closed-eye source](artwork/anime-pixel-adult-closeup-blink-source.png)
- [Native open-eye asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait.png)
- [Native blink asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait_blink.png)

The edit brings the face closer by cropping the crown and outer bob, while preserving the adult proportions, tilted three-quarter pose and expression. It gives the eyes and facial features more space within the same 78 × 78 portrait area. Previous hair sources remain available for comparison.

## RGB export

Run `python scripts/prepare_anime_artwork.py`. At this revision, the adult's source prefix was `anime-pixel-adult-closeup`, with native eye regions `((22, 27, 45, 41), (54, 36, 75, 49))`.

The previous adult exporter deliberately reduced the portrait to at most 16 colors. That was an artistic/software choice, **not a demonstrated hardware limit**. The current adult exporter keeps RGB tones without an indexed palette or global color-count limit. The chibi retains its existing 16-color retro treatment.

For each native pixel, the exporter samples an 8 × 8 cell. Nearby samples are grouped locally in 16-wide RGB channel buckets, keeping violet tones separate from warm tones. The output takes the weighted mean of the most frequent group; equal-area ties prefer the center sample's group. These buckets identify the dominant local tone, rather than force pixels to a fixed palette: different cells can retain different RGB values. Competing edge colors are excluded, so the final grid keeps its deliberate steps without dithering or blending hair and skin together. Within the closed-eye sockets, dark source strokes covering at least one quarter of a cell are retained to keep thin eyelids connected.

The blink source contributes only within the eye regions. All remaining pixels come from the open-eye source. Purple, red, blue and green recoloring continues to preserve warm skin and cheek colors.

Local render inspection found 746 distinct colors in the purple open-eye portrait, and 694–699 in the recolored portraits. Pixels outside the eye regions remain identical across a blink for all four variants. These counts describe the runtime PNG artwork, not the TFT's hardware color depth. The actual JPEG encoder remains at quality 98 with 4:4:4 sampling. The five illustrative display frames totaled about 109–112 KB; physical device appearance and transfer duration have not been checked for this revision.

## Open-eye reframing prompt

Input: `anime-pixel-adult-hair-open-source.png`.

```text
Use case: precise-object-edit.
Asset type: revised close-up OPEN-EYE pixel-art portrait for this project's MiniToo anime-pixel adult theme, rendered in a native 78 x 78 square.
Input: the supplied project's own generated adult woman portrait is the EDIT TARGET. No external art reference.
Primary request: make the portrait a visibly tighter FACE CLOSE-UP with confident readable pixel-art shapes. The existing view includes too much whole bob/neck so its face feels distant and low-resolution. Enlarge/reframe the SAME adult face by about 20-25 percent, preserving the slight three-quarter head tilt and expression. The facial features should be substantially larger on the tiny display.
Composition: tightly crop the top/crown and outer bob naturally at the image edges. Chin reaches the bottom edge; NO visible neck or shoulders. Both eyes, nose, closed smile, forehead opening and cheek patches remain comfortably visible. The exposed ear may be partly cropped. The face dominates the square, not a small face centered inside a full hair silhouette. Preserve perspective, don't rotate to a frontal view.
Style: drawn as clear retro game pixel art on ONE coherent 78 x 78 logical grid displayed enlarged. Intentional regular stair-step contours; compact connected color clusters, medium square pixels, consistent native one-pixel contours and clearly legible eye whites, pupils and catchlights. More readable pixel craft rather than simply blurring or coarsening the image. Avoid fine zigzag noise, isolated stray pixels and too many narrow parallel hair lines. Bob made of a few natural broad connected locks, simple wide highlight clusters and clean tips.
Color: retain violet hair and eyes, warm peach skin, muted coral cheeks, dark plum shadows and background. Retain nuanced well-chosen RGB colors and richer warm/violet shades where they help form. Do NOT force a 12- or 16-color palette. No dithering, grain, mottled texture or scattered noisy shades; every color cluster should feel deliberately placed.
Invariants: SAME woman around age 24, same adult facial proportions, head tilt, gaze and gentle expression, same bob identity. The framing enlarges the entire face proportionally; do not enlarge the eyes relative to the face, make a chibi, redesign her identity, add details or change the smile into an open mouth.
One complete square OPEN-EYE portrait only. No text, UI, frames, swatches, hair clip, accessories, logo or watermark.
```

## Matching blink draft prompt

Input: the selected close-up open-eye source. The resulting draft had thick eyelids, so it was used only as the next edit's input and retained locally in the ignored build directory.

```text
Use case: precise-object-edit.
Asset type: matching CLOSED-EYE blink frame for the supplied project's own close-up adult pixel-art woman.
Primary request: change ONLY the two visible eye openings into a gentle natural blink in this exact close-up portrait. Replace the open whites/irises/pupils/catchlights with adjacent warm peach skin. Each eye closes into ONE THIN continuous dark-plum pixel eyelid arc, roughly ONE logical pixel thick on the 78 x 78 native grid (about 16 source image pixels). No broad dark wedge, double crease, teeth-shaped lash spikes or eye-shaped solid blob. Follow the existing tilted three-quarter perspective. Keep arcs wholly inside the original eye openings and behind the same hair.
LOCK ALL ELSE EXACTLY: the new close-up composition, same woman around age 24, whole face proportion and tilted pose, all hair shapes and violet tones, eyebrows, forehead opening, skin colors, cheeks/blush, ear, nose, closed smile, chin crop and background. No facial movement or recoloring outside the eyes.
Craft: same coherent 78 x 78 logical pixel grid displayed enlarged; clean connected medium-size clusters and deliberate steps, nuanced warm/violet RGB tones. No arbitrary 16-color reduction, dithering, grain, mottled texture, isolated noisy pixels, blur, accessories, text, UI, frames, swatches or watermark.
One complete square portrait matching the supplied open frame with both eyes naturally closed.
```

## Selected thin-eyelid prompt

Input: the matching blink draft. The exporter uses only this selected output's eye regions.

```text
Use case: precise-object-edit.
Edit target: the supplied project's own CLOSED-EYE adult pixel-art close-up.
Change ONLY the dark closed eyelid shapes. They are still much too thick and look like filled wedges. REPLACE each with ONE THIN uninterrupted stepped dark-plum arc, exactly ONE logical pixel thick on a 78 x 78 logical grid, about 16 source image pixels thick. Clearly less than HALF the existing stroke thickness. A thin clean line rather than a filled black eye silhouette. Remove the upright lash teeth on the left eye. Remove the extra peach crease lines above the closed eyes, replace them with adjacent skin color. No separate crease, wedge, dark shadow or doubled stroke. Keep both eyes fully CLOSED, the same position, tilted perspective and appropriate arc.
Preserve ALL OTHER PIXELS/FEATURES: close-up face framing, the same adult 24-year-old face, pose and proportions, entire hair silhouette and highlights, eyebrows, forehead, nose, tiny closed smile, both cheek patches, skin colors, ear, chin crop and background. No redraw, recolor, movement or added details outside the two eyelid regions. Same nuanced RGB tones and deliberate 78 x 78 logical pixel-art clusters, no palette cap, dithering, noise, grain, blur, text, accessories, UI, frames or watermark.
Return one matching complete CLOSED-EYE portrait with only thinner eyelids and removal of their extra creases.
```

