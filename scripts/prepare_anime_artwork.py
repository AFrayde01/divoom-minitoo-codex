#!/usr/bin/env python3
"""Export generated anime artwork into stable native-size display frames."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs" / "artwork"
OUTPUT = ROOT / "src" / "divoom_minitoo_codex" / "assets"
SIZE = (78, 78)
PIXEL_COLORS = 16
# Eye sockets of this character only; cheeks and hair remain in the base frame.
EYE_REGIONS = ((9, 33, 27, 49), (38, 27, 63, 44))
# Include the sprite's eyelid creases so a blink does not duplicate them;
# keep both cheek patches outside these native eye regions.
CHIBI_EYE_REGIONS = ((20, 38, 42, 55), (54, 35, 71, 53))


def violet_mask(image: Image.Image) -> Image.Image:
    """Keep the recolorable violet tones separate from skin and eye whites."""
    mask = Image.new("L", image.size)
    hsv = image.convert("HSV").load()
    mask.putdata([
        255 if 160 <= hsv[x, y][0] <= 245 and hsv[x, y][1] >= 50 else 0
        for y in range(image.height)
        for x in range(image.width)
    ])
    return mask


def pixel_palettes(pair: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Build shared warm and violet palettes without mixing their hues."""
    mask = violet_mask(pair)
    groups: tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]] = ([], [])
    pixels, selected = pair.load(), mask.load()
    for y in range(pair.height):
        for x in range(pair.width):
            groups[bool(selected[x, y])].append(pixels[x, y])
    palettes = []
    for group_index, colors in enumerate(groups):
        samples = Image.new("RGB", (len(colors), 1))
        samples.putdata(colors)
        palette_size = PIXEL_COLORS // 2
        anchors: list[int] = []
        if group_index == 0:
            # A tiny mouth and eye whites can disappear when skin dominates
            # median-cut sampling. Reserve both ends of the warm color range.
            def luminance(color: tuple[int, int, int]) -> float:
                return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]

            anchors = list(min(colors, key=luminance)) + list(max(colors, key=luminance))
        reduced_size = palette_size - len(anchors) // 3
        reduced = samples.quantize(colors=reduced_size, method=Image.Quantize.MEDIANCUT)
        entries = anchors + reduced.getpalette()[:reduced_size * 3]
        palette = Image.new("P", (1, 1))
        palette.putpalette(entries * (256 // palette_size))
        palettes.append(palette)
    return palettes[0], palettes[1]


def quantize_pixel_frame(image: Image.Image, palettes: tuple[Image.Image, Image.Image]) -> Image.Image:
    warm, violet = (
        image.quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")
        for palette in palettes
    )
    return Image.composite(violet, warm, violet_mask(image))


def load_native(filename: str, pixel_art: bool = False) -> Image.Image:
    with Image.open(SOURCES / filename) as source:
        # Preserve fine contours at the full portrait size. The retro style
        # comes from the artwork rather than reducing and enlarging its pixels.
        resampling = Image.Resampling.NEAREST if pixel_art else Image.Resampling.LANCZOS
        return source.convert("RGB").resize(SIZE, resampling)


def export_portrait(source_prefix: str, output_prefix: str, pixel_art: bool = False, eye_regions=None) -> None:
    opened = load_native(f"{source_prefix}-open-source.png", pixel_art)
    generated_blink = load_native(f"{source_prefix}-blink-source.png", pixel_art)
    blink = opened.copy()
    for box in eye_regions or (CHIBI_EYE_REGIONS if pixel_art else EYE_REGIONS):
        blink.paste(generated_blink.crop(box), box[:2])

    if pixel_art:
        # A shared palette keeps stepped shading and identical cheek colors
        # across the blink while retaining all 78x78 portrait pixels.
        pair = Image.new("RGB", (SIZE[0] * 2, SIZE[1]))
        pair.paste(opened, (0, 0))
        pair.paste(blink, (SIZE[0], 0))
        palettes = pixel_palettes(pair)
        opened = quantize_pixel_frame(opened, palettes)
        blink = quantize_pixel_frame(blink, palettes)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    opened.save(OUTPUT / f"{output_prefix}.png", optimize=True)
    blink.save(OUTPUT / f"{output_prefix}_blink.png", optimize=True)
    print(f"Wrote two {SIZE[0]}x{SIZE[1]} {output_prefix} frames to {OUTPUT}")


def main() -> None:
    export_portrait("anime-portrait", "anime_portrait")
    export_portrait("anime-pixel-mature", "anime_pixel_chibi_portrait", pixel_art=True)
    export_portrait("anime-pixel-adult-flat", "anime_pixel_portrait", pixel_art=True,
                    eye_regions=((25, 31, 47, 44), (52, 38, 69, 51)))


if __name__ == "__main__":
    main()
