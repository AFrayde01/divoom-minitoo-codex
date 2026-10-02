# Comparing JPEG quality on MiniToo

If all three qualities show the same checkerboard defect, the [JPEG versus lossless RGB comparison](MINITOO_CODEC_COMPARISON.md) changes the encoding route instead of repeating this quality test.

Use this comparison when fine edges look mottled or show a checkerboard pattern on the physical screen. It displays **the same static portrait and dashboard** at quality **95, 97 and 98**, with 4:4:4 chroma sampling in all three files. Only a small footer label changes to identify which version is actually visible. It is a diagnostic comparison, not an automatic quality adjustment.

The script uses the renderer and assets from its own checkout. It does not connect to Codex or read account usage. Its default adult `anime-pixel` dashboard uses illustrative values: **79% remaining, a single 7D window, and IDLE**. The footer says `JPEG 95`, `JPEG 97` or `JPEG 98`. Its label clears rows 112–122, including the whole original caption, and uses the footer's background color. These are separate JPEG blocks below the portrait; the face, hair and other comparison pixels stay unchanged.

## Compare on the device

1. Stop the MiniToo monitor with **Ctrl+C**.
2. Close the Divoom app and disconnect MiniToo's Bluetooth audio profile. Leave the paired MiniToo powered on.
3. From the repository directory, run:

   ```sh
   .venv/bin/python scripts/compare_minitoo_jpeg.py --address AA:BB:CC:DD:EE:FF --color green
   ```

   Replace the placeholder with your own MiniToo address. `MINITOO_ADDRESS` is also supported. Portrait colors are `green` (default), `purple`, `red` and `blue`.

4. Sending starts automatically. The script opens a fresh Bluetooth session for quality 95, sends it and waits for confirmation. Check that the screen footer actually says **JPEG 95**.
5. Inspect the eyes, forehead, hair edges, text and flat background. It keeps each acknowledged image for **20 seconds** before connecting again for the next quality. Check the footer changes to **JPEG 97**, then **JPEG 98**. Use `--hold-seconds 30` for more inspection time, or `--interactive` to advance by entering an optional observation and pressing **Enter** after each upload.
6. The script leaves the last static image on the screen. Restart your normal monitor to restore live usage and animation.

Each quality uses one complete frame from the same original RGB drawing, with its identifying footer label. All portrait pixels are identical before JPEG encoding; the report stores their hash. There is no blinking, WORKING animation, periodic refresh, resize, dithering or chained JPEG recompression. Each quality starts with a fresh session of the existing authenticated bridge and requires the final acknowledgement. The Terminal prints the returned chunk count; confirm the matching footer label visually, since an acknowledgement alone cannot establish which image is visible. A failure gets one bounded reconnect attempt; if it remains unconfirmed, the comparison stops and closes the bridge. **Ctrl+C** also closes it.

## Send one quality directly

To isolate a quality that did not visibly update, send it by itself without waiting for input:

```sh
.venv/bin/python scripts/compare_minitoo_jpeg.py --address AA:BB:CC:DD:EE:FF --quality 97
```

Check for **JPEG 97** on the screen. If it stays on another label despite a confirmation, preserve `report.json` and `bridge.log` before running another comparison.

## Prepare files without Bluetooth

```sh
.venv/bin/python scripts/compare_minitoo_jpeg.py --prepare-only --color green
```

To compare an existing native-sized PNG instead:

```sh
.venv/bin/python scripts/compare_minitoo_jpeg.py --address AA:BB:CC:DD:EE:FF --image /path/to/original.png
```

The custom image must be exactly **160 × 128**. The script rejects other dimensions rather than resize them. Run the sending command in a macOS Terminal with Bluetooth access; environments that block local listener ports cannot run the bridge. Only the optional `--interactive` mode requires an interactive input stream.

## Files and observations

The default output directory is `build/jpeg-quality-comparison/` inside the checkout, regardless of the current Terminal directory. It contains:

- `original.png`: the common RGB source before JPEG encoding.
- `quality-95-source.png`, `quality-97-source.png`, `quality-98-source.png`: original RGB frames with their footer labels.
- `quality-95.jpg`, `quality-97.jpg`, `quality-98.jpg`: the actual bytes used for the uploads.
- `report.json`: original and portrait pixel hashes, dimensions, file sizes, numerical differences from each labelled PNG, current transfer state, returned chunk counts, acknowledgement state, errors and any observations entered in interactive mode.
- `bridge.log`: private (`0600`) diagnostic output from the Bluetooth bridge, including received control bytes and chunk transfers. It rotates at 1 MiB. Review personal paths or addresses before sharing this log.

`--output PATH` selects another directory. A repeat run replaces this comparison's files. The default directory is ignored by Git. The report does not include the Bluetooth address or live account values; your typed observations are stored locally.

Numerical differences are measured using the desktop JPEG decoder. They **do not establish which version will look best on MiniToo**. The useful result is your observation on the physical display. For background on the behavior of fast JPEG decoding at very high quality, see [libjpeg's decoder documentation](https://github.com/libjpeg-turbo/libjpeg-turbo/blob/main/doc/usage.txt); this does not establish which decoder MiniToo uses.
