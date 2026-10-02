# Adult sprite in the chibi drawing style

Created on **2026-10-02** with the **built-in OpenAI image generation tool**. Every image input was this project's own generated artwork: the original adult portrait, the chibi portrait, and intermediate drafts derived from them. No external illustration, named artist, character or franchise reference was supplied.

## Themes and active sources

- **`anime-pixel`**: a woman around 24 with adult proportions, smaller almond eyes, a longer midface and a gentle closed smile, drawn with the chibi's connected hair clusters, stepped outlines and compact facial features. The smile grows during the closed-eye frame.
- **`anime-pixel-detail`**: preserves the preceding original adult portrait and matching blink with all sampled RGB tones. [Detail sources and notes](ANIME_PIXEL_ADULT_ORIGINAL_RGB.md).
- **`anime-pixel-chibi`**: retains the existing compact character with larger eyes, now with the same gentle-smile / broader-closed-eye-smile behavior.

The three share the same dashboard, five-frame blink/WORKING cadence, quota and refill bars, reset-credit screen, and `purple`, `red`, `blue` and `green` options.

Selected files:

- [Open-eye smile source](artwork/anime-pixel-adult-smile-open-source.png)
- [Matching closed-eye smile source](artwork/anime-pixel-adult-smile-blink-source.png)
- [Native open-eye asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait.png)
- [Native blink asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait_blink.png)

## Native export

Run `python scripts/prepare_anime_artwork.py`. The source prefix is `anime-pixel-adult-smile`. The eye regions are `((25, 36, 46, 48), (55, 39, 72, 53))` and the mouth region is `(40, 60, 56, 67)`. The [smile-generation prompts](ANIME_PIXEL_SMILES.md) record the current expression edits; the prompts below document the earlier drawing-style revision.

The simple adult uses the existing 78 × 78 cell sampling method followed by the same shared warm/violet artistic palette used by chibi, with at most 16 colors and no dithering. This palette is a drawing-style choice, not a limitation of MiniToo's TFT or RGB888 transmission. The detailed adult continues to use the original source pair and RGB sampling without this palette reduction.

Only the blink's fixed eye and mouth regions enter the final closed-eye frame. Every pixel outside those regions comes from the open-eye frame, preserving hair, cheeks and background. Recoloring changes violet tones while retaining warm skin and cheeks.

Use lossless RGB for the MiniToo comparison:

```sh
.venv/bin/codex-minitoo --address AA:BB:CC:DD:EE:FF --theme anime-pixel --color green --encoding rgb
```

Keep the detailed version with:

```sh
.venv/bin/codex-minitoo --address AA:BB:CC:DD:EE:FF --theme anime-pixel-detail --color green --encoding rgb
```

Both render at the native 160 × 128 dashboard size. The new simple artwork has been inspected locally; its physical device appearance has not yet been confirmed.

## Initial style-transfer draft

Inputs: original adult portrait (identity/pose) and the project's chibi (style). This draft was refined before selection.

```text
Use case: style-transfer.
Asset type: a complete OPEN-EYE adult pixel-art face portrait for a native 78 x 78 MiniToo dashboard.
Input images: Image 1 is this project's own ORIGINAL ADULT portrait, the edit target and identity/pose reference. Image 2 is this project's own CHIBI portrait, a STYLE reference only.
Primary request: redraw the adult woman from Image 1 using the same simple, charming hand-drawn retro-game sprite language as Image 2. The user wants the adult and chibi to feel like the same pixel-art family, while the adult keeps clearly adult proportions around age 24. Keep Image 1's gently tilted three-quarter face toward image-right, gaze at viewer, moderate almond eyes, longer midface, softly angular jaw and short violet bob. Do not copy the chibi's enormous round eyes or baby-round face.
Style reference transfer: broad connected purple/plum hair clusters, sparse broad lavender highlights, bold clean stepped outlines, simple compact violet irises with one square catchlight, small solid coral cheek patches, tiny warm nose and a small continuous closed smile. Draw a few coherent bob locks, not many strands. Use the chibi's readable moderate square pixel scale, crisp connected contours and warm friendly expression. Simplify the adult's detailed lips into a short connected smile like the chibi's. The result must feel deliberately DRAWN as a retro sprite, rather than a detailed illustration reduced in resolution.
Compose on one coherent 78 x 78 logical square pixel grid, enlarged to 1248 x 1248 if possible, exactly square. Moderate pixel size, enough eye definition. Rich violet base, plum shadow and broad lavender accent; warm peach face, restrained coral cheeks and ivory whites. Broad uniform cel-color planes with about 16-24 principal shades, no dither or fine texture. Color count is an artistic style, not a hardware constraint.
Framing: face close-up filling the square, crown and outer bob cropped naturally, chin at bottom, no visible neck, collar or shoulders. Preserve the adult three-quarter pose and expressive adult eyes. Dark aubergine only in corner gaps. Both eyes OPEN. No hair accessories.
Avoid gradients, speckles, tiny detached lash teeth, fine hair linework, mottled skin, isolated forehead dots, glossy lip details, mosaic filter, blur or antialiasing. One complete portrait only. No text, dashboard, swatches, panels, border, watermark, external characters or artist imitation.
```

## Selected simple adult

Inputs: the project's chibi (style) and the preceding generated adult draft (edit target).

```text
Use case: style-transfer.
Image 1 is the project's CHIBI portrait, the main STYLE reference. Image 2 is the new ADULT portrait draft, the edit target.
Redraw Image 2 in the actual simple sprite drawing style of Image 1. The first adult draft still has detailed lips, a long nose contour and many hair streaks. Replace those design choices with the chibi's restrained connected shapes. This is an adult counterpart in the SAME retro sprite art family.
Keep the adult woman around 24: tilted three-quarter head, moderate almond eyes, longer midface and softly angular jaw. Keep violet short bob, peach face, coral cheeks and dark plum outlines. Preserve her pose, not the chibi's young facial proportions.
Specific style changes:
MOUTH: remove ALL lips, pink lip patches and lower lip shading. Use only a short connected dark warm-red shallow closed smile, like the chibi reference, about five logical pixels wide.
NOSE: remove the bridge contour, big nostril hook and white highlight. Just a compact two-pixel warm nose mark like the chibi.
HAIR: four broad connected bob masses, three principal violet tones plus outline. Two or three broad simple lavender highlight shapes. No thin parallel strand lines, zigzag streak highlights or small islands.
EYES: readable adult almond eyes, solid ivory whites, compact violet iris with only two tones and one tiny square catchlight per eye. Clean bold upper lash silhouette, no extra crease strokes.
FACE: warm peach base and one restrained warm edge shadow, small solid coral cheek patches. Calm uniform fields, same flat game-sprite style as the chibi.
Compose as a single complete OPEN-EYE face sprite on a coherent 78 x 78 logical grid, enlarged 16 times to a square 1248 x 1248 image if possible. Crisp deliberate regular moderate square pixel steps; not a blur, mosaic or smooth illustration. Tightly fill the frame with face and bob, chin at the lower edge, no neck or shoulders. Dark aubergine only in corners.
Use about 16 well-chosen principal flat colors. No gradients, antialiasing, dither, noise, fine texture, accessories, text, UI, palette, frames, watermark or external character references. Both eyes OPEN.
```

## Matching blink draft

Input: the selected simple adult open-eye image only.

```text
Use case: precise-object-edit.
Asset type: matching complete CLOSED-EYE blink frame for the supplied project's own new adult retro pixel-art portrait.
Edit target: ONLY the supplied image. Close BOTH eyes naturally in their current positions. Replace all eye whites, iris, pupils and highlights inside the two original openings with the exact neighboring warm peach skin. Draw one restrained thin dark-plum connected stepped closed eyelid per eye near the lower half of the original opening. Follow the slight three-quarter head angle, no smiling crescent exaggeration. Remove the small warm upper-eyelid crease strokes inside the eye sockets so the blink has only one lid line each. Keep the eyebrows above intact.
Strictly preserve every other part: same adult woman around 24, almond-eye socket proportions, face orientation and crop, violet bob and ALL broad violet/lavender clusters and outlines, foreground bangs occluding the eyelids, forehead, eyebrows, tiny warm nose, short connected dark warm-red smile, cheeks and their exact coral patches, peach skin, jaw, ear, dark corner background and pixel scale. Change only the eye sockets. Absolutely no cheek-color changes, floating lines over hair, extra eyelashes or face movement.
Same simple charming retro sprite family as the chibi, coherent 78 x 78 logical grid shown enlarged in one square, moderate connected square pixel clusters, clean stepped contours and broad solid colors. No added detail, gradients, dither, antialiasing, texture, speckles, text, UI, border, swatches, accessories or watermark. One complete square portrait, both eyes CLOSED.
```

## Selected thinner eyelids

Input: the preceding generated closed-eye draft only.

```text
Use case: precise-object-edit.
Edit target: this project's supplied CLOSED-EYE adult retro sprite.
Change ONLY the two closed eyelid sockets. REMOVE the two small floating warm-brown crease marks just above the closed lids, replacing them with the immediately surrounding peach color. Preserve the violet eyebrows higher up.
Make each existing dark closed eyelid about HALF its current thickness, a single connected dark-plum line about ONE native 78x78 pixel thick, or 16 source pixels in this enlarged image. Relaxed short gently stepped contours, same position and eye angle, no separate lashes or double outlines. These are a natural blink, not thick black smiling bars.
Preserve everything else exactly: same face, pose and crop, forehead, bangs and all hair colors and shapes, eyebrows, both coral cheeks, warm skin shading, tiny nose and connected warm-red smile, ear and chin, dark corner background and logical pixel size. No changes outside the two eye sockets. Eyelids remain under foreground hair.
Keep simple coherent crisp 78x78 retro pixel art displayed enlarged. No gradients, dither, blur, antialiasing, scattered pixels, new details, accessories, labels, borders or UI. Return one complete square CLOSED-EYE portrait.
```
