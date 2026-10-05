#!/usr/bin/env python3
"""Export generated anime artwork into stable native-size display frames."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs" / "artwork"
OUTPUT = ROOT / "src" / "divoom_minitoo_codex" / "assets"
SIZE = (78, 78)
RETRO_COLORS = 16
PIXEL_GRID_SAMPLES = 8
RGB_CELL_BUCKET = 16
RGB = tuple[int, int, int]
EyeRegions = tuple[tuple[int, int, int, int], ...]
# Eye sockets of this character only; cheeks and hair remain in the base frame.
EYE_REGIONS = ((9, 33, 27, 49), (38, 27, 63, 44))
# Include the sprite's eyelid creases so a blink does not duplicate them;
# keep both cheek patches outside these native eye regions.
CHIBI_EYE_REGIONS = ((20, 38, 42, 55), (54, 35, 71, 53))
# Preserve the detailed portrait's original eye positions independently.
DETAIL_EYE_REGIONS = ((25, 31, 47, 44), (52, 38, 69, 51))
# Previously created adult portrait/blink pair selected for the normal theme.
NORMAL_ADULT_EYE_REGIONS = ((25, 31, 47, 44), (52, 38, 69, 51))
# Chibi retains its slightly broader smile in the closed-eye frame.
CHIBI_MOUTH_REGIONS = ((41, 61, 56, 69),)


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
    """Build shared retro palettes without mixing warm/violet hues."""
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
        palette_size = RETRO_COLORS // 2
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
        palette.putpalette((entries * 256)[:768])
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


def dominant_native(
    image: Image.Image,
    detail_regions: EyeRegions = (),
    mouth_regions: EyeRegions = (),
) -> Image.Image:
    """Keep a cell's dominant source tone in RGB, without a global palette cap."""
    expected = (SIZE[0] * PIXEL_GRID_SAMPLES, SIZE[1] * PIXEL_GRID_SAMPLES)
    if image.size != expected:
        raise ValueError(f"Expected a {expected} sampled portrait, received {image.size}.")
    source_colors = image.getcolors(image.width * image.height)
    assert source_colors is not None
    tones = [tone for _, tone in source_colors]
    tone_samples = Image.new("RGB", (len(tones), 1))
    tone_samples.putdata(tones)
    hsv = tone_samples.convert("HSV").load()
    tone_keys: dict[RGB, tuple[int, ...]] = {}
    for index, tone in enumerate(tones):
        hue, saturation, _ = hsv[index, 0]
        tone_keys[tone] = (
            int(160 <= hue <= 245 and saturation >= 50),
            *(channel // RGB_CELL_BUCKET for channel in tone),
        )
    output = Image.new("RGB", SIZE)
    pixels = output.load()
    sample = PIXEL_GRID_SAMPLES
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            cell = image.crop((x * sample, y * sample, (x + 1) * sample, (y + 1) * sample))
            colors = cell.getcolors(sample * sample)
            assert colors is not None
            contours = []
            if any(left <= x < right and top <= y < bottom for left, top, right, bottom in detail_regions):
                contours = [(count, tone) for count, tone in colors if max(tone) < 96]
            elif any(left <= x < right and top <= y < bottom for left, top, right, bottom in mouth_regions):
                contours = [
                    (count, tone) for count, tone in colors
                    if tone[0] < 224 and tone[1] < 100 and tone[2] < 100
                ]
            # Thin eyelids and smile corners can cover less than half a cell.
            # Retain actual source contours once they cover a quarter, so a
            # curved smile does not lose its corners and become a flat line.
            if sum(count for count, _ in contours) >= sample * sample // 4:
                colors = contours
            # Group nearby source tones locally, without collapsing every
            # cell to a few fixed colors. The mean within the winning family
            # suppresses small source variations; competing edge colors are
            # excluded so hair/skin boundaries keep deliberate pixel steps.
            groups: dict[tuple[int, ...], list[int]] = {}
            for count, tone in colors:
                key = tone_keys[tone]
                totals = groups.setdefault(key, [0, 0, 0, 0])
                totals[0] += count
                for channel in range(3):
                    totals[channel + 1] += tone[channel] * count
            largest = max(total[0] for total in groups.values())
            winners = {key for key, total in groups.items() if total[0] == largest}
            center_pos = (sample // 2, sample // 2)
            center = cell.getpixel(center_pos)
            center_key = tone_keys[center]
            selected = center_key if center_key in winners else min(winners)
            totals = groups[selected]
            pixels[x, y] = tuple(round(value / totals[0]) for value in totals[1:])
    return output


def pixel_grid_frames(
    source_prefix: str,
    eye_regions: EyeRegions,
    blink_source_prefix: str | None = None,
    mouth_regions: EyeRegions = (),
) -> tuple[Image.Image, Image.Image]:
    """Reduce an oversized pixel illustration using one coherent output grid."""
    sample = PIXEL_GRID_SAMPLES
    sample_size = (SIZE[0] * sample, SIZE[1] * sample)
    sources = []
    for state in ("open", "blink"):
        prefix = blink_source_prefix if state == "blink" and blink_source_prefix else source_prefix
        with Image.open(SOURCES / f"{prefix}-{state}-source.png") as source:
            sources.append(source.convert("RGB").resize(sample_size, Image.Resampling.NEAREST))
    opened, generated_blink = sources
    blink = opened.copy()
    for box in (*eye_regions, *mouth_regions):
        sampled_box = tuple(value * sample for value in box)
        blink.paste(generated_blink.crop(sampled_box), sampled_box[:2])
    return (
        dominant_native(opened, mouth_regions=mouth_regions),
        dominant_native(blink, eye_regions, mouth_regions),
    )


def export_portrait(
    source_prefix: str,
    output_prefix: str,
    pixel_art: bool = False,
    eye_regions: EyeRegions | None = None,
    native_grid: bool = False,
    retro_palette: bool = False,
    blink_source_prefix: str | None = None,
    mouth_regions: EyeRegions = (),
) -> None:
    regions = eye_regions or (CHIBI_EYE_REGIONS if pixel_art else EYE_REGIONS)
    if native_grid:
        if not pixel_art:
            raise ValueError("The native pixel grid requires a pixel art portrait.")
        opened, blink = pixel_grid_frames(source_prefix, regions, blink_source_prefix, mouth_regions)
    else:
        opened = load_native(f"{source_prefix}-open-source.png", pixel_art)
        blink_prefix = blink_source_prefix or source_prefix
        generated_blink = load_native(f"{blink_prefix}-blink-source.png", pixel_art)
        blink = opened.copy()
        for box in (*regions, *mouth_regions):
            blink.paste(generated_blink.crop(box), box[:2])

    if pixel_art and (not native_grid or retro_palette):
        # A shared artistic palette gives chibi and the simple adult the same
        # retro color treatment. The detailed adult retains its RGB tones.
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
    export_portrait("anime-pixel-chibi-smile", "anime_pixel_chibi_portrait", pixel_art=True,
                    mouth_regions=CHIBI_MOUTH_REGIONS)
    export_portrait("anime-pixel-adult", "anime_pixel_detail_portrait", pixel_art=True,
                    eye_regions=DETAIL_EYE_REGIONS, native_grid=True)
    export_portrait("anime-pixel-adult-simple", "anime_pixel_portrait", pixel_art=True,
                    eye_regions=NORMAL_ADULT_EYE_REGIONS, native_grid=True)


if __name__ == "__main__":
    main()
