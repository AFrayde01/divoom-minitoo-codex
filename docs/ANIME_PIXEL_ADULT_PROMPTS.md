# Adult pixel-art generation brief

Created on 2026-10-01 using the built-in OpenAI image generation tool.

## Open eyes

Image inputs: none.

```text
Use case: stylized-concept.
Asset type: one square pixel-art face portrait for the 78 by 78 character region in a tiny Divoom MiniToo dashboard.
Primary request: create a NEW original fictional ADULT anime woman, about 24 years old, with clearly adult facial proportions. This is the default adult variant alongside a separate chibi portrait. Generate from this written brief only, without using any prior image, external illustration, named character, artist or franchise as a reference.
Subject: short violet bob with low side-swept bangs and broad clean hair shapes; a gently turned three-quarter face toward image-right, eyes looking toward the viewer. Almond-shaped modest-sized violet eyes with exactly one small highlight per iris, subtle expressive eyebrows, longer adult midface, softly angular jaw, a tiny unobtrusive nose and relaxed small connected closed smile. Gentle warm peach skin, small restrained flat blush patches. Visibly an adult woman over 18, preferably mid-20s; avoid babyish round face and enormous childlike eyes.
Style/medium: polished authentic retro game pixel art, deliberately drawn on a 78x78 logical pixel grid, purposefully stepped contours and medium-size coherent color clusters. Approximately 12-16 flat colors: 3-4 violet hair shades, dark plum outline, natural warm skin shades, coral blush and ivory eye whites. One simple shadow per region. The style comes from drawn pixel clusters, not mosaic filters. Clean readable features and broad hair masses; no fine hair strands, no scattered speckles, no gradients, no airbrushing, no antialiasing, no dithering or texture.
Composition/framing: one complete square extremely tight FACE-ONLY close-up. Face and hair occupy the canvas. Bangs/crown naturally cropped at top; bottom just at chin, with hair leaving side and bottom edges. NO neck, shoulders, collar or floating bust. Eyes around the middle of the square. A solid nearly black dark aubergine background (#1b1126) only in the corners. Both eyes fully open. Upright head with slight natural tilt.
Constraints: one portrait only; no accessories, hair clips, jewelry, logos, text, swatches, panels, UI, frame, border or watermark. Preserve moderate recognizable pixels and an uncluttered face for a tiny actual display. Hair and irises violet so software can recolor them to red, blue and green while keeping skin unchanged.
```

## Blink

Image input: `artwork/anime-pixel-adult-open-source.png` only.

```text
Edit this original pixel-art ADULT woman portrait to produce its matching eyes-closed blink frame. Preserve the exact composition, color palette, hair, bangs, ears, skin, cheeks, blush, nose, mouth, jaw, background and all pixels outside the two eye sockets. Change ONLY the eyes: replace each open eye with matching natural closed upper eyelid, following the existing tilted three-quarter perspective, with a single elegant dark curved pixel-cluster lash line at the lower eyelid position. Fill the original eye area with the neighboring skin color and gentle eyelid skin shadow; no eye whites or irises visible. Eyelids remain behind foreground hair; preserve hair overlaps exactly. No extra eyelash strokes, freckles, color changes, cheek changes or added details. Keep the same original adult woman, clearly around 24 years old, in the same retro pixel art style.
```

## Hair simplification

Image input: `artwork/anime-pixel-adult-open-source.png` only.

Output: `artwork/anime-pixel-adult-simple-open-source.png`.

```text
Use case: precise-object-edit.
Edit target: the attached project's original ADULT pixel-art woman portrait, designed as around 24 years old.
Primary request: simplify ONLY the HAIR for a tiny 78x78 pixel-art display. Keep the same short bob and side-swept bangs, but redraw the hair as 4 to 6 broad connected locks with THREE principal flat violet shades plus a dark plum silhouette outline. Use only 2 or 3 broad simple highlight patches. Remove all fine strand lines, thin streaks, tiny zigzags, isolated highlight pixels, repeated scalloped lines, texture and scattered fragments. The violet hair must read as clean calm masses at native 78x78 size, with intentional moderate-size pixel clusters.
Invariants: preserve the exact adult face, face proportions, forehead opening, placement and shape of the bangs over the face, eyebrows, open eyes, violet irises, eyelash shapes, nose, mouth, small smile, cheek colors, blush patches, ear, chin, face orientation, crop and dark corner background. No rejuvenation or chibi proportions. Match every feature's position; do not enlarge the eyes or move the hairline. Replace the interior hair detail rather than cropping or blurring the image.
Style: true retro game portrait drawn on a 78x78 logical grid, stepped pixel contours, flat color clusters, approximately 12-16 colors total. Hair boundaries remain deliberately pixel-art but orderly. No gradients, soft airbrushing, antialiasing, dithering or mosaic filter. Keep natural warm peach skin and blush and ivory eye whites completely unchanged. One full square open-eye portrait only, no UI, text, swatches, panels, accessories, watermark or border.
```

## Matching blink for hair draft

Image input: `artwork/anime-pixel-adult-simple-open-source.png` only.

Output: `artwork/anime-pixel-adult-simple-blink-source.png`.

```text
Use case: precise-object-edit.
Edit target: this project's original adult pixel-art woman with newly simplified violet hair.
Make its matching fully closed-eye blink frame, changing ONLY the two original eye sockets. Replace whites and irises with matching warm peach skin and draw one restrained dark plum stepped eyelid contour at the lower portion of each eye opening, following the exact head tilt and three-quarter perspective. Preserve the existing eyebrows and natural occlusion of the foreground bangs. No extra crease lines or speckled eyelash details.
Strict invariants: identical broad simplified hair locks, interior hair blocks and three violet shades, highlights, outlines, hairline, ear, face proportions, forehead, cheeks, blush intensity and color, nose, mouth and smile, jaw, chin, crop, background and all pixels outside the eyes. Do not add hair detail or reintroduce the earlier fine strands. Preserve the same adult woman around 24 years old. Keep moderate-size connected pixel clusters on the same 78x78 logical grid, flat solid colors, no antialiasing, gradients, blur, dithering, text, accessories, panels, frames or watermark. One square fully closed-eye portrait.
```

## Clean eye refinement

Image input: `artwork/anime-pixel-adult-simple-open-source.png` only.

Output: `artwork/anime-pixel-adult-clean-open-source.png`.

```text
Use case: precise-object-edit.
Edit target: this project's original ADULT retro pixel-art woman with simplified violet bob hair.
Change ONLY the two open EYES and their immediate eyelid details so they read cleanly at 78x78 native pixels.
Keep the exact existing almond eye shapes, sizes, positions, tilt, viewing direction and adult proportions. Simplify each iris into TWO flat violet color clusters with one compact dark pupil and ONE tiny single square ivory highlight. Simplify each upper eyelash outline into a continuous clean dark plum stepped contour, with only one very short outer lash. Lower lids remain minimal. Remove tiny iris flecks, repeated rings, tiny lash teeth, soft shadow fringes and the extra warm thin crease stroke directly above each upper eyelid. Eye whites remain flat ivory. Avoid dark jagged noise around the eyes. Keep all eye changes within the original eye socket regions, with no enlargement and no eye repositioning.
Pixel style: intentional moderate-size connected retro-game pixel clusters on a 78x78 logical grid; 12-16 solid colors; crisp clean staircase edges rather than fine scattered pixels. Do not add blur, antialiasing, airbrushing, gradients, dithering or a coarse mosaic filter.
STRICTLY preserve everything else: the recently simplified broad hair locks and sparse highlights, face silhouette and proportions, eyebrows, bangs over the eyes, forehead, skin, cheeks, blush, ear, nose, lips and small closed smile, chin, head tilt, three-quarter perspective, square crop and background. Same woman designed as around 24 years old, visibly adult, not chibi. Both eyes fully open. No text, accessories, frames, panels or watermark.
```

## Clean matching blink

Image input: `artwork/anime-pixel-adult-clean-open-source.png` only.

Output: `artwork/anime-pixel-adult-clean-blink-source.png`.

```text
Use case: precise-object-edit.
Edit target: this project's original adult pixel-art woman with the simplified broad violet hair and clean open eyes.
Create the matching FULLY CLOSED-EYE blink frame by changing ONLY the two original eye sockets. Replace every iris, pupil, highlight and eye white with the surrounding warm peach skin. Draw ONE simple continuous dark plum closed eyelid contour for each eye, following the same head tilt and three-quarter perspective, at the lower portion of the original eye opening. Use a restrained shallow stepped curve of even thickness, no individual lash teeth, no extra crease lines above or below, no freckles or stray pixels. Preserve the existing eyebrows and the exact occlusion of the eyelids behind the foreground bangs.
Strict invariants: keep the same woman around 24 years old, visibly adult, exact face proportions, eye positions, ear, forehead, nose, mouth, smile, jaw, chin, crop and background. All broad simplified hair locks, hairline, sparse highlight patches, flat violet shades and dark outlines must remain IDENTICAL. All cheek patches, blush intensity and skin outside the original eye sockets must remain IDENTICAL. Do not reintroduce the old fine hair or iris detail, add shading, or change the palette. Keep moderate connected retro pixel clusters on the same 78x78 logical grid, solid colors and clean intentional stair steps. No antialiasing, blur, gradients, dithering, noise, accessories, text, panels, frame, border or watermark. One complete square fully closed-eye portrait only.
```

## Artifact cleanup

Image input: `artwork/anime-pixel-adult-clean-open-source.png` only.

Output: `artwork/anime-pixel-adult-flat-open-source.png`.

```text
Use case: precise-object-edit.
Asset type: final clean open-eye portrait for the native 78x78 adult anime-pixel MiniToo theme.
Edit target: this project's own original violet-haired adult woman portrait is the only input. Preserve her identity, adult age around 24, short bob, broad locks, exact crop, tilted three-quarter pose, face proportions, gaze, eyes' shape and positions, eyebrows, restrained smile, cheeks' positions and overall violet/peach palette.
Primary request: remove fine visual artifacts and small-scale noise by refining the existing portrait as a genuinely clean flat-color retro game sprite. Simplify color boundaries into connected deliberate pixel clusters. Every interior region must be a uniform solid fill; remove the soft gradients currently visible inside skin and violet hair. Use one base warm peach skin plus one broad connected warm shadow, one small uniform coral cheek patch per cheek, solid ivory eye whites, two flat violet iris tones, compact dark pupils, one small square eye highlight each, clean continuous upper lash contours without detached lash teeth. Remove the fine upper-eyelid crease strokes and tiny lower-lid flecks. Keep the nose and mouth readable but simple: one small warm nose cluster, one short connected smile with no lip highlight specks. Hair: keep the currently broad shapes and sparse broad highlights, three solid violet shades plus dark plum outline; remove tiny notches, texture, extra highlight lines and thin color fringes.
Pixel craft: coherent 78x78 logical pixel grid, crisp medium-size connected clusters, clean stepped boundaries and broad flat fills. Each visible square pixel belongs to a deliberate contour or color block. Approximately 12-16 solid colors total. No gradients, airbrushing, antialiasing, dithering, halftone, grain, isolated speckles, extra colors at boundaries, smooth vector outline, blur or coarser mosaic. Avoid increasing fine detail.
Constraints: adult woman visibly over 18, not chibi; same feature positions and head silhouette, no frontal pose, no enlarged eyes, no accessories, no text, UI, border, palette swatches or watermark. One full square portrait with both eyes fully open. Changes should be refinement of the existing drawing, not a different character.
```

## Matching blink after artifact cleanup

Image input: `artwork/anime-pixel-adult-flat-open-source.png` only.

Output: `artwork/anime-pixel-adult-flat-blink-source.png`.

```text
Use case: precise-object-edit.
Asset type: matching fully closed-eye blink frame of this project's adult flat-color pixel portrait.
Edit target: the attached refined original adult woman portrait is the ONLY input.
Primary request: change only the two original eye socket regions to close both eyes. Remove all iris, pupil, highlight and white pixels, filling them with the adjacent warm peach skin. Each eye must have ONE continuous dark plum eyelid line, an even simple shallow stepped curve following the exact existing tilted three-quarter perspective. No separate lash teeth or upper crease strokes, no scattered marks, added shading or extra pixels. Eyelids remain naturally underneath the foreground bangs.
Strict invariants: same woman around 24 years old, face proportions and feature positions, gaze orientation implied by head pose, square crop, broad simplified violet hair locks and sparse highlights, palette, warm skin and broad shadows, flat coral cheeks, eyebrow shapes, nose, connected smile, jaw, ear, chin and dark background. Keep all pixels outside the two eye sockets identical; particularly no cheek or hair changes during the blink. Use the same clean 78x78 logical pixel clusters and restrained 12-16-color flat palette. Avoid gradients, blur, antialiasing, dithering, grain, speckles, texture, extra details, UI, frames, text, accessories or watermark. One complete square face-only closed-eye portrait.
```

