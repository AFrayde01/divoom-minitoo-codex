# Adult pixel portrait hair refinement

The `anime-pixel` portrait's hair was refined on **2026-10-01** with the **built-in OpenAI image generation tool**. Every image input was this project's own generated adult portrait or a draft derived from it. No external illustration, named character, franchise or artist was used.

The current runtime artwork is documented in the [original portrait restoration for RGB](ANIME_PIXEL_ADULT_ORIGINAL_RGB.md). The subsequent [close-up and RGB revision](ANIME_PIXEL_ADULT_CLOSEUP.md) records a previous design and the RGB sampling method retained by the restoration. This page records the preceding hair design and its export at that time.

## Selected sources

- [Open-eye portrait](artwork/anime-pixel-adult-hair-open-source.png)
- [Matching blink](artwork/anime-pixel-adult-hair-blink-source.png)
- [Native open-eye asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait.png)
- [Native closed-eye asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait_blink.png)

The edit consolidates the bob into connected masses, removes many thin stripes and loose lower tips, and keeps the adult character's tilted pose and facial proportions. The restored `anime-pixel-adult-solid` sources remain in the repository as the previous version.

## Native export

At this stage, the adult used source prefix `anime-pixel-adult-hair`, the existing eye regions `((25, 31, 47, 44), (52, 38, 69, 51))`, and the [native grid exporter](ANIME_PIXEL_ADULT_REFINEMENT.md#native-export-adjustment). That exporter sampled an 8 × 8 grid per output cell and used a shared palette of up to 16 distinct warm/violet colors, and selected the dominant color without dithering. For the closed-eye frame only, a dark source stroke covering at least one quarter of a cell is retained inside the eye sockets; a pure majority rule otherwise breaks a thin eyelid into isolated dots. This exception does not alter open-eye highlights or regions outside the eye sockets.

The complete dashboard remains 160 × 128, with a 78 × 78 portrait. Purple, red, blue and green remain supported. The JPEG encoder remains at quality 98 and 4:4:4 sampling. Local frame inspection establishes image dimensions and blink stability, but does not establish that every artifact reported on the physical device has disappeared.

## Open-eye hair edit

Input: `anime-pixel-adult-solid-open-source.png`.

```text
Use case: precise-object-edit.
Asset type: revised open-eye source for the existing adult anime-pixel MiniToo portrait, exported at exactly 78 x 78 native pixels.
Edit target: ONLY this project's supplied original violet-haired adult woman's portrait. The image is the character to edit, not a style reference.
Primary request: visibly improve the HAIR DESIGN for this tiny retro pixel-art portrait. The current lower hair has too many thin parallel strands, dangling chipped tips and narrow dark channels. Replace these with a coherent, attractive chin-length bob made of a few large readable connected locks.
Hair construction: retain the overall bob length, violet family, broad side-swept fringe, crown volume and the same exposed ear. Keep the central forehead opening and hair overlap positions along the forehead and temples. Draw approximately FOUR broad main hair masses: one sweeping fringe, two cheek-framing side locks and one back mass. The lower ends should form a small number of intentional softly tapered stepped tips, not a forest of little spikes or ribbons. Remove the many skinny vertical strands and fine stripe highlights. Use exactly THREE flat violet hair tones: deep plum shadow/outline, a rich mid-violet base, and one restrained lighter violet highlight. Highlights are two or three solid connected curved bands inside the hair volume, never tiny streaks, dots, gradient texture or scratchy patches. Hair must feel naturally shaped and consistent with the head tilt.
Native pixel craft: ONE coherent 78 x 78 logical square-pixel grid, displayed enlarged, ideally 1248 x 1248 with each logical pixel 16 x 16. Hard clean deliberate staircase contours, medium-sized connected clusters, minimum native one-pixel stroke thickness. Solid bucket-filled colors throughout. The style remains pixel art, not a smooth illustration with a pixel filter. Avoid changing the face into coarser mosaic blocks.
LOCK THE FACE: keep this same adult woman around age 24, exact slightly tilted three-quarter pose, tight square composition, adult facial proportions, face silhouette, eyebrow and eye positions and sizes, open eyes and gaze, nose, little closed smile, both cheeks and warm skin, exposed ear, jaw and neck crop. Preserve the source's recognizable expression. Do not enlarge eyes, make a chibi, change the angle or add accessories.
Everything should be sharp, with a restrained flat palette and no grain, shading noise, soft gradients, gloss, checkerboard texture, antialiasing, stray pixels or tiny loose hair strands. Preserve the same dark background. No text, palette swatches, frames, UI, logos or watermark.
Return one complete square OPEN-EYE portrait of the same adult woman, with the improved simple natural bob.
```

## Matching blink draft

Input: the selected new open-eye portrait. This generated an intermediate blink with eyelids that were too thick; it was used only as the next edit's input. The intermediate draft is retained locally under the ignored build directory.

```text
Use case: precise-object-edit.
Asset type: matching closed-eye blink source for the supplied adult anime-pixel woman with the newly improved violet bob.
Edit target: this project's own supplied original OPEN-EYE portrait only.
Primary request: change ONLY the two existing eye openings to naturally CLOSED eyes. Replace eye whites, irises, pupils and catchlights with the adjacent warm-peach skin fill. Each eye becomes one restrained continuous dark-plum stepped eyelid arc following the existing head tilt and three-quarter perspective. Position the arcs inside the current eye sockets; one clean native-pixel stroke, no extra crease, double lash line or separated marks. Eyelids must remain behind the existing hair.
Preserve the ENTIRE remainder of this portrait EXACTLY: the new broad connected violet bob masses, side-swept fringe, highlight blocks, shadow shapes and intentional tapered ends; adult woman around 24; head angle, crop, background, ear, face silhouette, eyebrows, warm skin, cheek patches and their colors, nose, tiny mouth, jaw and neck. Do not redraw, restyle or recolor these regions. No face or hair movement, no blush change.
Same coherent 78 x 78 logical square-pixel grid displayed enlarged, crisp medium-sized connected clusters, solid color fills with no dithering or antialiasing. No gradient, grain, texture, speckles, smoothing, accessories, text, UI, frame, palette swatches or watermark.
Return one complete square portrait exactly matching the supplied open-eye state, with both eyes fully closed.
```

## Selected thin-eyelid blink

Input: the project's intermediate matching closed-eye draft.

```text
Use case: precise-object-edit.
Edit target: ONLY the supplied original adult pixel-art woman's CLOSED-EYE blink portrait.
Change ONLY the two dark closed eyelid strokes. The current eyelids look like thick filled dark wedges. Replace each with a THIN natural continuous stepped line, exactly ONE logical native pixel thick, about 16 image pixels thick on this enlarged canvas. No region of the line should become a broad filled triangle or eye-shaped black blob. Remove the two little upright lash teeth near the left eye. No extra crease or shadow. One restrained shallow continuous dark-plum eyelid arc per eye, each following the existing head tilt, positioned across the lower-middle of the existing eye socket. Both eyes stay fully closed and the surrounding socket stays the same warm-peach skin tone. The two arcs should be recognizably much thinner than in the supplied image.
The intended output is a coherent 78 x 78 logical pixel sprite, enlarged. Keep the same pixel grid and clean staircase boundaries. Eyelid stroke thickness: approximately 1/78 of image width; not two or three logical pixels thick.
Preserve EVERY OTHER FEATURE EXACTLY: all redesigned violet hair masses, bangs and highlight ribbons, their silhouette and colors, face pose and adult proportions, skin, eyebrow shapes, both blush patches, nose, mouth, ear, jaw, neck crop and background. No movement, redrawing, recoloring or new detail outside the closed eye sockets. No gradients, antialiasing, grain, dithering, blur, text, accessories, swatches or watermark.
Return one complete square matching closed-eye portrait with ONLY thinner, cleaner eyelids.
```

