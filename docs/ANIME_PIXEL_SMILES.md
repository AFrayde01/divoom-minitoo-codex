# Pixel portrait smiles

Created on **2026-10-02** with the **built-in OpenAI image generation tool**. All image inputs are this project's own generated portraits and drafts. No external illustration, named character, artist or franchise reference was supplied.

## Expression and native frames

The adult-smile edit described here is a previous experiment; the normal `anime-pixel` theme now uses the existing `anime-pixel-adult-simple` pair and simply blinks, leaving its mouth unchanged. `anime-pixel-chibi` still has a gentle closed-mouth smile with a broader smile when its eyes close. `anime-pixel-detail` preserves the original detailed portrait.

The native exporter saves complete **78 × 78 RGB PNG** frames. The active adult sprite changes only the eye sockets, using the previously created defined-lash blink. The chibi blink retains its eye and mouth regions while all hair, skin, cheeks and background stay fixed. The adult keeps full RGB tones; chibi uses its artistic palette of at most 16 colors with no dithering. This is a style choice, not a TFT or RGB888 transmission limit. Color changes still affect only violet hues and leave warm skin and cheek tones intact.

| Theme | Source prefix | Native eye regions | Native mouth region |
| --- | --- | --- | --- |
| `anime-pixel` (restored) | `anime-pixel-adult-simple` | `(25, 31, 47, 44)`, `(52, 38, 69, 51)` | unchanged |
| `anime-pixel-chibi` | `anime-pixel-chibi-smile` | `(20, 38, 42, 55)`, `(54, 35, 71, 53)` | `(41, 61, 56, 69)` |

Coordinates are left, top, right, bottom, with exclusive right and bottom edges. The adult-smile coordinates below are retained as generation-history details, but that source is no longer active. The renderer switches complete frames; it does not draw eyelids or mouths over the displayed face at runtime. The existing five-frame cadence keeps eyes open for four frames and closed for one, at 600 ms per frame.

Export artwork with `python scripts/prepare_anime_artwork.py`, then refresh README previews with `PYTHONPATH=src python scripts/generate_theme_gallery.py`. For MiniToo, use `--encoding rgb` to avoid the previously observed JPEG display artifacts.

[Adult drawing style and earlier drafts](ANIME_PIXEL_ADULT_RETRO.md) · [All pixel artwork provenance](ANIME_PIXEL_ARTWORK.md)

## Generation prompts

### Adult open-eye smile

Input: [artwork/anime-pixel-adult-retro-expression-open-source.png](artwork/anime-pixel-adult-retro-expression-open-source.png). Output: [artwork/anime-pixel-adult-smile-open-source.png](artwork/anime-pixel-adult-smile-open-source.png).

```text
Use case: precise-object-edit.
Change ONLY the mouth of the supplied project's own pixel portrait. Both eyes stay OPEN.
The user wants the resting expression to be friendly, never serious. Draw a clear gentle CLOSED SMILE: a small connected warm reddish-brown shallow stepped curve, about 6-7 logical pixels wide, roughly one pixel thick, with BOTH corners lifted about one pixel above the center. Preserve enough curvature that it remains a recognizable smile when reduced to 78 x 78. No straight neutral line, frown, thick filled lipstick shape, open mouth, teeth or detached corner dots.
Keep ALL other features unchanged: exact open eyes and their positions/highlights, brows and eyelid details, all violet/lavender hair blocks and foreground bangs, forehead, nose, both coral cheek patches and their colors, skin shading, ear, jaw, head angle, framing and background. Keep the current character identity and proportions.
Same crisp coherent 78 x 78 retro logical pixel grid enlarged, connected simple clusters, moderate pixel scale. No antialiasing, blur, dither, new details, accessories, text, palette, watermark or UI. One complete square OPEN-EYE portrait.
This is the ADULT woman around 24: preserve adult face proportions, almond eyes and the newly discreet tiny nose. Do not make her chibi.
```

### Chibi open-eye smile

Input: [artwork/anime-pixel-mature-open-source.png](artwork/anime-pixel-mature-open-source.png). Output: [artwork/anime-pixel-chibi-smile-open-source.png](artwork/anime-pixel-chibi-smile-open-source.png).

```text
Use case: precise-object-edit.
Change ONLY the mouth of the supplied project's own pixel portrait. Both eyes stay OPEN.
The user wants the resting expression to be friendly, never serious. Draw a clear gentle CLOSED SMILE: a small connected warm reddish-brown shallow stepped curve, about 6-7 logical pixels wide, roughly one pixel thick, with BOTH corners lifted about one pixel above the center. Preserve enough curvature that it remains a recognizable smile when reduced to 78 x 78. No straight neutral line, frown, thick filled lipstick shape, open mouth, teeth or detached corner dots.
Keep ALL other features unchanged: exact open eyes and their positions/highlights, brows and eyelid details, all violet/lavender hair blocks and foreground bangs, forehead, nose, both coral cheek patches and their colors, skin shading, ear, jaw, head angle, framing and background. Keep the current character identity and proportions.
Same crisp coherent 78 x 78 retro logical pixel grid enlarged, connected simple clusters, moderate pixel scale. No antialiasing, blur, dither, new details, accessories, text, palette, watermark or UI. One complete square OPEN-EYE portrait.
This is the existing CHIBI character: preserve the compact face and current expressive eyes, not the adult variant.
```

### Adult closed-eye smile

Input: [artwork/anime-pixel-adult-smile-open-source.png](artwork/anime-pixel-adult-smile-open-source.png). Output: [artwork/anime-pixel-adult-smile-blink-source.png](artwork/anime-pixel-adult-smile-blink-source.png).

```text
Use case: precise-object-edit, full-frame pixel-animation edit.
Produce the CLOSED-EYE cheerful frame for this project's own supplied OPEN-EYE pixel portrait.
Close BOTH eyes naturally, replacing the irises and eye whites with unchanged warm skin and one thin connected dark-plum curved eyelid for each. The eyelids should make the face look happily relaxed, with gentle lifted ends, no stacked duplicate eyelid/crease marks. Preserve eyebrows and all foreground hair: eyelids must remain behind the bangs.
Also change the mouth to a slightly WIDER and more curved CLOSED SMILE than the supplied open-eye smile: around 9 logical pixels wide, one pixel thick with 2 pixels of depth and both corners lifted above the center. A warm reddish-brown connected shallow stepped smile, cheerful yet subtle and clear when sampled to 78 x 78. No detached dots, teeth, open mouth, thick lips or lipstick.
Only the eye sockets and mouth may change. Preserve the EXACT framing, head tilt and position, identity, nose, hair shape and all violet/lavender color blocks, forehead, ear, jaw, skin shading, both coral blush patches and their exact colors, dark background. No zoom or scaling or shifting the face. Every region outside the eyes and mouth should be identical to the reference.
Preserve the crisp consistent 78 x 78 logical retro pixel grid enlarged. Simple connected pixel clusters, same moderate pixel size, no extra fine detail, antialiasing, dither, blur, gradients, texture, accessories, text, palette, logo, watermark or UI. Return one complete square portrait with closed eyes and the slightly broader smile.
This is the adult variant: keep her adult proportions, around age 24, and the supplied small discreet nose. Do not make her chibi.
```

### Chibi closed-eye smile

Input: [artwork/anime-pixel-chibi-smile-open-source.png](artwork/anime-pixel-chibi-smile-open-source.png). Output: [artwork/anime-pixel-chibi-smile-blink-source.png](artwork/anime-pixel-chibi-smile-blink-source.png).

```text
Use case: precise-object-edit, full-frame pixel-animation edit.
Produce the CLOSED-EYE cheerful frame for this project's own supplied OPEN-EYE pixel portrait.
Close BOTH eyes naturally, replacing the irises and eye whites with unchanged warm skin and one thin connected dark-plum curved eyelid for each. The eyelids should make the face look happily relaxed, with gentle lifted ends, no stacked duplicate eyelid/crease marks. Preserve eyebrows and all foreground hair: eyelids must remain behind the bangs.
Also change the mouth to a slightly WIDER and more curved CLOSED SMILE than the supplied open-eye smile: around 9 logical pixels wide, one pixel thick with 2 pixels of depth and both corners lifted above the center. A warm reddish-brown connected shallow stepped smile, cheerful yet subtle and clear when sampled to 78 x 78. No detached dots, teeth, open mouth, thick lips or lipstick.
Only the eye sockets and mouth may change. Preserve the EXACT framing, head tilt and position, identity, nose, hair shape and all violet/lavender color blocks, forehead, ear, jaw, skin shading, both coral blush patches and their exact colors, dark background. No zoom or scaling or shifting the face. Every region outside the eyes and mouth should be identical to the reference.
Preserve the crisp consistent 78 x 78 logical retro pixel grid enlarged. Simple connected pixel clusters, same moderate pixel size, no extra fine detail, antialiasing, dither, blur, gradients, texture, accessories, text, palette, logo, watermark or UI. Return one complete square portrait with closed eyes and the slightly broader smile.
This is the chibi variant: preserve the compact face, existing head and facial proportions. Do not make her adult.
```
