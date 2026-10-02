# Comparing JPEG with lossless RGB on MiniToo

The physical comparison on a tested MiniToo eliminated the checkerboard defect with RGB. The [native RGB guide and check](MINITOO_RGB.md) covers integration into the full dashboard and animations; native 160 × 128 was subsequently confirmed visually on the tested device.

This experimental comparison investigates alternating light/dark checkerboard patches seen on the physical display. It does not assess the normal LCD pixel grid or change the monitor's default encoder.

It uses a **128 × 128** diagnostic canvas with the same adult pixel portrait copied at its native **78 × 78** size, plus white `CHECK` lettering on a uniform green rectangle. Only the top `JPEG 98` / `RGB` label changes between sources. The strip below `CHECK` contains exactly one RGB color before encoding.

The two transfers use:

- **JPEG 98:** baseline JPEG, 4:4:4, through the `0x23` path with an 8 × 8 grid.
- **RGB:** original RGB888 bytes through the `0x25` Zstandard path. A raw Zstandard block preserves every source byte, with an explicit 128 KiB window. It requires no additional Python package. This diagnostic file is deliberately larger than a compressed photo.

The [MiniToo protocol capture and validation notes](https://github.com/alvinunreal/divoom-minitoo-osx/blob/main/PROTOCOL.md) document RGB888/Zstandard at 128 × 128. This comparison originally used that documented square size; a subsequent native 160 × 128 check was visually confirmed by the user on the tested MiniToo. The diagnostic JPEG also uses that square grid to keep the comparison geometry consistent. Both must be checked visually on your device; an ACK confirms transfer completion, not correct rendering. Device scaling or different decoder behavior can affect the result.

## Run the comparison

1. Stop the monitor with **Ctrl+C**, close the Divoom app and disconnect MiniToo's audio profile.
2. From the repository directory, run:

   ```sh
   .venv/bin/python scripts/compare_minitoo_codecs.py --address AA:BB:CC:DD:EE:FF --color green
   ```

   Replace the placeholder with your own device address. `MINITOO_ADDRESS` is also supported.

3. The command builds two separately named, authenticated diagnostic bridges using Xcode Command Line Tools. It sends **JPEG 98**, waits **30 seconds**, then sends **RGB** using a fresh connection. Check that each top label is visible.
4. Compare the checkerboard patches below `CHECK`, near the eyes and at the forehead. Record a blank/glitched image or a geometry change as an unsupported or inconclusive result, rather than a quality improvement.
5. Restart your normal monitor afterwards to restore usage and animation.

Use `--hold-seconds 60` for longer inspection, `--interactive` for manual advancement after each confirmed transfer, or `--only rgb` / `--only jpeg` to retry one stage. A failed transfer gets one reconnect attempt, then stops. **Ctrl+C** closes the bridge. The script does not read Codex usage or modify theme assets.

For offline preparation:

```sh
.venv/bin/python scripts/compare_minitoo_codecs.py --prepare-only --color green
```

Files are saved under the ignored `build/minitoo-codec-comparison/` directory:

- `original.png`: the common portrait and control bar before the top label.
- `jpeg-source.png`, `rgb-source.png`: the two labelled source frames.
- `jpeg-98.jpg`: the actual JPEG upload bytes.
- `rgb888.bin`, `rgb888.zst`: exact RGB bytes and the expected lossless Zstandard stream. The RGB diagnostic bridge wraps those pixels in the same raw-block format.
- `report.json`: source portrait hashes, dimensions, control-strip color, payload sizes and transfer progress/results.
- `bridge.log`: private diagnostic logs; review paths, addresses and received device control bytes before sharing.

`--output PATH` selects another directory. Repeated runs replace the comparison files. Diagnostic binaries live in `build/minitoo-codec-diagnostic/`; they reject normal monitor requests. The production bridge rejects diagnostic codec requests and uses its native 160 × 128 JPEG or RGB payload.

## Interpreting the result

If RGB visibly reduces the checkerboard while displaying the same portrait and control bar correctly, that implicates the JPEG processing route. It does not establish which step or decoder implementation causes the defect. If both formats show the same patches, JPEG encoding alone cannot explain them; display processing, scaling and color conversion need further investigation. A normal photographed LCD grid is not the artifact being compared.

The raw-block container follows the [official Zstandard format specification](https://github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md).
