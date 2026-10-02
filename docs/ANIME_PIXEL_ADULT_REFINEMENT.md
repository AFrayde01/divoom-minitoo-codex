# Adult pixel portrait cleanup

The `anime-pixel` adult portrait was refined on **2026-10-01** with the **built-in OpenAI image generation tool**. The only image inputs were this project's own original adult artwork and the draft generated from it during this cleanup. No external image, named artist, character or franchise reference was used.

The character keeps her adult proportions, short violet bob, tilted three-quarter pose and existing dashboard crop. This pass simplifies the hair shapes, upper eyelids, iris detail, nose and mouth and removes some small color transitions in the skin. It retains the native 78 × 78 export and shared palette without dithering. The exporter takes only the matching blink's two eye-socket regions, preserving the cheeks, hair and other non-eye pixels across the animation. Red, blue, green and purple variants continue to use the same runtime color mapping.

The current runtime source pair is documented in the [original portrait restoration for RGB](ANIME_PIXEL_ADULT_ORIGINAL_RGB.md). The subsequent [close-up revision](ANIME_PIXEL_ADULT_CLOSEUP.md), following the [hair refinement](ANIME_PIXEL_ADULT_HAIR.md), records the RGB sampling method retained by that restoration. This page records the preceding general cleanup and the native export adjustment introduced with it.

## General cleanup source files

- [Open-eye source](artwork/anime-pixel-adult-solid-open-source.png)
- [Closed-eye source](artwork/anime-pixel-adult-solid-blink-source.png)
- [Native open-eye asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait.png)
- [Native closed-eye asset](../src/divoom_minitoo_codex/assets/anime_pixel_portrait_blink.png)

The general cleanup used source prefix `anime-pixel-adult-solid` and eye regions `((25, 31, 47, 44), (52, 38, 69, 51))`. The later hair refinement retained those regions. The subsequent close-up used different eye regions recorded in its own export notes; the restored original uses the general cleanup's region coordinates.

## Native export adjustment

On **2026-10-01**, the native export was adjusted while retaining the restored `anime-pixel-adult-solid` source pair. This is a deterministic exporter change; it does not regenerate the character or add another image generation prompt.

The previous export reduced the 1254 × 1254 source by taking one nearest-neighbor sample per output pixel, then used median-cut palettes. That can make thin contours uneven, and several of the palette entries were almost identical. At that stage, the adult export sampled 8 × 8 points for each of its 78 × 78 output cells. It quantized those samples with a shared palette that favors frequent original tones and omits near duplicates, then took each cell's dominant color. Equal-area ties prefer the center sample when it is one of the dominant colors. No dithering or blended edge colors are added in that final step.

At this stage, the open-eye export used 12 colors. Inspection of the rendered purple, red, blue and green variants found no pixel changes outside the fixed eye sockets during a blink. The dashboard remains 160 × 128 and the JPEG settings remain at quality 98 with no chroma subsampling. The user reported a modest improvement on the physical MiniToo after restarting the monitor, with artifacts still visible. Updated previews use illustrative account values. These observations do not establish that every artifact has been resolved.

## First cleanup brief

Input: [previous flat source](artwork/anime-pixel-adult-flat-open-source.png). This generated an intermediate review draft, which was used as the next edit's input rather than selected for runtime.

```text
Use case: precise-object-edit.
Asset type: refined open-eye game sprite for this project's adult anime-pixel portrait, displayed at 78 x 78 native pixels.
Input image: ONLY edit this project's own original violet-haired adult woman's portrait. Preserve her recognizable identity, woman around 24 years old, short violet bob, slightly tilted three-quarter head, face silhouette, adult facial proportions, precise gaze and eye locations, eyebrows, warm peach skin, restrained closed smile, visible left ear, crop and dark background. Both eyes remain open.
Primary request: remove the grainy color clusters and lumpy detail by redrawing this existing portrait as polished hand-authored retro pixel art with genuinely uniform flat fills. Keep the same character and recognizable composition. Especially clean up the hair, upper eyelashes, irises, cheek/nose transitions and mouth.
STRICT PIXEL CRAFT: draw on ONE coherent 78 by 78 logical square-pixel grid, displayed enlarged. Clean deliberate staircase contours, individual native pixels all the same size, medium sized connected shapes. Absolutely no antialiasing or soft color transitions inside a region. Uniform color rectangles and solid connected silhouettes. Pixel art, not a smooth vector cartoon, not a blur, not a coarse mosaic effect.
Hair: retain the current bob and broad fringe shapes but consolidate all internal detail into about four broad connected locks. Use ONE uniform violet base, ONE connected shadow color and ONE sparse broad highlight color, plus the outline. Each highlight is a solid clean ribbon or simple broad cluster, never a streak of little shades. Remove the multiple little dark lines and little chipped notches at hair tips. The hair planes must look calm and completely flat, no gradient texture, no speckled islands.
Eyes: keep adult proportional eye shapes, use one thick continuous upper lid contour with no serrated lash teeth or stray crease strokes. Solid ivory whites, one flat violet iris base plus a simple connected darker upper half, compact dark pupil, one small square white catchlight per eye. No detailed rings, micro reflections or additional iris patches. Do not enlarge the eyes or turn her into a chibi.
Face: ONE completely uniform peach fill across forehead and cheeks; ONE broad connected warm shadow plane around the temple/neck; one flat warm cheek patch each with a clean intentional stepped edge. A compact continuous warm nose accent, no stray freckles or tiny fringe colors; a short connected closed smile in warm brown with no little lip highlight and no noisy lower lip patch. All planes are truly uniform solid color.
Palette: maximum 13 exact flat RGB colors including background. Suggested fixed palette: background #211728, outline/pupil #291A35, hair shadow #40274E, hair base #704385, hair highlight #9460A3, dark warm accent #C4795F, skin shadow #E9A175, skin base #F8C492, blush #EB8B77, eye white #FFF1D6, iris #643A78, iris highlight #9960B0, smile #8E493C. Never invent tiny intermediate edge shades.
Invariants: same adult woman, face angle, feature positions, square tight portrait composition and violet color family; no accessories, no change to age, no new details, no UI or lettering.
Avoid: gradients, grain, noise, tiny disconnected color specks, dithering, rough crunchy pixel edges, airbrushing, blurred contours, fine multicolored hair strands, realistic skin texture, glossy reflections, palette swatches, frames or watermark.
Return a single complete square open-eye portrait.
```

## Selected open-eye refinement

Input: the first cleanup's generated draft. Output: `anime-pixel-adult-solid-open-source.png`.

```text
Use case: precise-object-edit.
Redraw the supplied ORIGINAL character as a visibly cleaner, simpler retro game pixel sprite. This is an artwork simplification, not a new character. Keep the adult woman approximately age 24, her head tilt, three-quarter face direction, bob silhouette, eye positions and gentle expression. Both eyes open. Keep the tight square crop and violet theme.
The supplied source still has fine gradient/grain artifacts. REPLACE those tones completely with a tiny strict palette of uniform solid color fills. Treat every region like a bucket-filled polygon in a pixel editor. No region may contain a gradient or noise.
Draw on a coherent roughly 78 x 78 logical grid, enlarged with square clean uniform pixels. Deliberate regular one-pixel staircase boundaries. Medium pixel scale suited for a 78x78 screen; fine detail disappears, so simplify the shape itself.
Make these edits VERY visible:
1. Forehead, nose bridge, cheeks and chin form ONE large completely solid light-peach region. Only one broad flat connected warm shadow along the far-side face and neck. No mottled or orange patches across the face.
2. Hair uses ONLY THREE uniform violet colors: dark outline/shadow, mid-tone base, light highlight. Four broad simple locks, one broad clean highlight per side. Remove all thin internal strand lines, tiny jagged end chips and isolated highlight pixels. The base hue is solid everywhere, with zero texture.
3. Eye whites are one solid ivory. Irises use ONE uniform violet, dark pupils and one small square white catchlight. Remove iris rings, shiny gradients, scalloped purple reflections, and all tiny detail along the lower eyelids. Upper eyelids are simple continuous dark stepped contours. Eyebrows separate and simple, no crease near the upper outer corner.
4. Nose is a compact connected warm stepped mark without a thin long nose contour. Mouth is one clean short shallow stepped closed smile, no lower lip shading, no lip highlights.
5. One small FLAT blush patch on each cheek, restrained color, clean edges.
Maximum TEN solid colors for the whole image. Skin #F8C492; shadow #E9A175; blush #EB8B77; outline #291A35; violet hair base #704385; hair highlight #9460A3; hair shadow #40274E; ivory #FFF1D6; iris #643A78; warm nose/mouth #A46150. Background may share #291A35. These are solid fills, no in-between shades.
Keep mature proportional facial anatomy and eyes. Do not enlarge eyes or round the face into a chibi. NO blur, smooth vector curves, photorealism, antialiasing, dithering, gloss, gradients, grain, color banding, stray dots, palette chart, frame, text, watermark or accessories.
A single complete square open-eye portrait of this same original adult woman, with much simpler shapes and visibly uniform clean retro sprite fills.
```

## Selected matching blink

Input: `anime-pixel-adult-solid-open-source.png` only. Output: `anime-pixel-adult-solid-blink-source.png`.

```text
Use case: precise-object-edit.
Asset type: the matching fully closed-eye blink frame for the supplied refined adult anime-pixel sprite.
Edit target: ONLY this project's supplied original violet-haired adult woman portrait.
Change ONLY the two existing eye openings. Fully close both eyes. Replace all eye whites, iris, pupil and white highlights with the EXACT adjacent solid warm peach skin color. For each eye draw ONE continuous simple dark-plum stepped eyelid arc, near the lower-middle of the original eye opening, respecting the tilted three-quarter head angle. Restrained thickness, no lash teeth, upper crease, lower-lid specks or duplicate lines. Both eyelids remain naturally behind the existing foreground hair.
STRICTLY preserve all the rest of this complete portrait: adult woman around age 24, head tilt and three-quarter pose, short violet bob silhouette, the same broad locks and flat highlight planes, existing eyebrows, exact face silhouette, peach skin, small flat blush patches, nose, connected closed smile, ear, jaw, neck/crop and dark background. Do not alter hair, cheeks, blush color or skin shading. Eye sockets keep the same size and position.
Use the same coherent native 78 x 78 square-pixel grid, medium connected pixel clusters, restrained flat palette and clean regular staircase contours. Every fill region must remain completely solid and uniform. No blur, gradient, antialiasing, grain, dithering, little disconnected pixels, glossy lighting or extra detail. No text, frames, swatches, watermark or accessories.
Return one complete square portrait, exactly the matching closed-eye state of the original, with all visible change confined to the original eye openings.
```


## Reverted eye and forehead experiment

After the general cleanup, a further edit used only this project's `anime-pixel-adult-solid-open-source.png` to simplify the eye openings and remove narrow warm shading around the forehead and eyes. Its sources, `anime-pixel-adult-face-open-source.png` and `anime-pixel-adult-face-blink-source.png`, are retained as a reverted experiment. The user reported that artifacts between the forehead and eyelashes still appeared on the device, and requested the previous artwork. The runtime therefore uses the `anime-pixel-adult-solid` pair again, with JPEG quality 98. This feedback does not establish the cause of the physical display artifacts.

During the reverted experiment, the adult theme's JPEG quality was raised from 98 to 99 with chroma subsampling disabled. An illustrative green Pro animation using the general cleanup's frames grew from 104,140 to 120,871 bytes. In selected eye and forehead areas, mean absolute RGB channel differences from the uncompressed renderer decreased from 1.31/1.44 to 0.83/0.85 levels on the 0–255 scale. These measurements concern the local JPEG encoder, not the physical display or Bluetooth duration; live values and the final artwork affect payload size. Quality 99 was reverted together with the artwork.

### Open-eye edit

Input: `artwork/anime-pixel-adult-solid-open-source.png`. Output: `artwork/anime-pixel-adult-face-open-source.png`. Built-in image generation tool.

```text
Use case: precise-object-edit.
Asset type: targeted clarity cleanup of the supplied project's original adult anime-pixel woman portrait for a 78x78 native display.
Edit target: this exact original violet-haired woman. Only modify the FOREHEAD SKIN and the TWO OPEN EYE REGIONS; keep the existing adult woman around age 24, her eyes' size and positions, head tilt, three-quarter pose, bob silhouette, violet hair planes, face proportions, cheek patches, nose, mouth, ear, neck, square crop and dark background unchanged.
FOREHEAD: the exposed skin triangle between the fringe and eyebrows must be ONE absolutely uniform SOLID peach fill, the same peach as the main cheek skin. Remove every subtle gradient, mottled color, little orange border fringe, stray mark or tiny secondary skin patch in this forehead area. Preserve the exact hair silhouette and both existing eyebrows. The skin simply meets the crisp hair boundary; no extra outline following the hairline and no extra thin shadow band.
EYES: preserve their adult proportional outlines and exact perspective, but simplify all interior details into clean contiguous native pixel clusters. Each eye: one continuous smooth staircase upper lash contour in dark plum, one simple flat ivory eye-white area, one solid violet iris disk, one compact dark pupil, and exactly ONE small square ivory catchlight. Keep iris and pupil separate and readable. Remove the multiple purple shades, scalloped iris reflections, tiny disconnected white or violet flecks, broken lower lash teeth, warm eyelid crease strokes, fine corner lines and noisy multicolored edge fringes. Allow broad flat warm skin to touch the lid directly, with no noisy fine skin shading around eyes. Iris color and eye whites must each be uniform solid fills.
Pixel craft: coherent 78x78 logical square-pixel grid enlarged, precise regular staircase edges and compact connected shapes, solid bucket-filled color areas, no more fine detail. All facial features remain adult size and location; no bigger eyes or chibi proportions. Keep the same violet/warm-peach palette and clean retro pixel-art aesthetic.
Absolutely no gradients, blur, antialiasing, dithering, grain, texture, speckles, glossy multicolor eye reflections, soft lighting, new hair strands, new expressions, accessories, text, border, palette swatches or watermark.
Return one full square matching OPEN-EYE portrait of this exact original adult woman, with cleaner more uniform forehead and readable simple eyes.
```

### Matching blink edit

Input: `artwork/anime-pixel-adult-face-open-source.png` only. Output: `artwork/anime-pixel-adult-face-blink-source.png`. Built-in image generation tool.

```text
Use case: precise-object-edit.
Asset type: matching complete closed-eye blink state of the supplied original adult anime-pixel portrait after the eye/forehead cleanup.
Edit target: ONLY this project's supplied violet-haired adult woman's face.
Change ONLY the two existing open eye areas: close both eyes fully, removing all iris, pupil, eye white and catchlight pixels. Fill each original eye opening with the EXACT neighboring uniform solid peach skin, and draw one continuous simple dark-plum stepped eyelid curve, restrained and naturally following the tilted three-quarter perspective. No lash teeth, separate creases, corner specks, iris traces or new shading. Preserve the foreground bangs' natural occlusion over the eyelids.
All the rest of the image MUST stay identical: the clean exposed forehead and skin between eyebrows, eyebrows, the warm peach base of the face, both cheek blush patches, same colors and broad violet hair locks/highlight planes, adult proportions and age around 24, three-quarter head tilt, ear, nose, closed smile, jaw, neck/crop and dark background.
Same coherent enlarged 78x78 logical square-pixel grid and restrained solid-color retro palette. Every eye-area fill is completely uniform; avoid little intermediate shades around eyelids.
No gradients, noise, grain, dithering, antialiasing, blur, rough edge fringes, glossy lighting, accessories, UI, text, border, swatches or watermark.
Return one full square closed-eye portrait matching this exact source, with changes confined to the two eye openings.
```
