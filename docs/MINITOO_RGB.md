# Lossless RGB on MiniToo

A physical comparison of the same 128 × 128 portrait and flat green text bar found that the checkerboard defect remained with JPEG 95/97/98 and disappeared with RGB888. This identifies the JPEG processing route as the source of the observed difference; it does not determine the precise decoder implementation or internal step responsible.

The monitor now supports **RGB888 with lossless Zstandard compression** for every MiniToo theme, animation and reset-credit screen. It keeps the complete **160 × 128** dashboard, all source colors and original animation frames/timing. It does not resize, dither or reduce a palette during transmission.

**Native 160 × 128 RGB was visually confirmed on the tested MiniToo on 2026-10-02:** the user reported that the complete dashboard, blink, WORKING animation and reset-credit screen displayed correctly. **RGB is now the CLI default**; no encoding option is required. This confirms the tested device, not every firmware. The user also confirmed the restored original adult portrait over RGB.

## Check the full dashboard

Stop the monitor, close the Divoom app and disconnect MiniToo's audio profile. From the repository directory:

```sh
.venv/bin/python scripts/check_minitoo_rgb.py --address AA:BB:CC:DD:EE:FF --theme anime-pixel --color green
```

The script builds the current RGB-capable bridge and sends these native-size stages, with 20 seconds between them:

1. Static usage dashboard.
2. Idle animation, including the portrait blink.
3. WORKING animation.
4. Reset-credit screen.

The displayed **79% remaining and 3 resets are illustrative**; the script does not read your Codex account. Check the full layout, text edges, portrait colors, blinking and working indicator. Report a blank, clipped or distorted image as well as any checkerboard defect. A transfer ACK alone does not establish correct display. Restart the regular monitor afterwards for live account values.

Use `--only static`, `--only idle-animation`, `--only working-animation` or `--only reset-credits` to repeat one stage. Other MiniToo themes are accepted with `--theme`. `--prepare-only` generates files without Bluetooth.

The ignored `build/minitoo-native-rgb-check/` directory contains exact `.payload` uploads, compressed `.zst` streams, original PNG frames, a report with byte counts and source hashes, and private rotating bridge diagnostics. Review paths and device control data before sharing logs.

## Use RGB in the monitor

Update the installation with `./scripts/install.sh` to install the `zstandard` Python dependency and rebuild the authenticated bridge, then start:

```sh
.venv/bin/codex-minitoo --address AA:BB:CC:DD:EE:FF --theme anime-pixel --color green
```

`--encoding jpeg` explicitly selects the existing JPEG route; `--encoding rgb` explicitly selects the default lossless route. This setting applies to MiniToo; TimeBox Mini continues to use its own RGB444 protocol. Existing installations with a `zstd` executable on `PATH` can use that lossless compressor until their Python dependency is updated. There is no automatic fallback from RGB to JPEG. Without theme/color options, interactive startup offers a menu with the last choices preselected; `--no-prompt` starts directly with saved choices.

The Python client checks that the bridge advertises RGB support before submitting RGB data, so an old JPEG-only binary receives no RGB image request. RGB transfers retain the existing authenticated loopback connection, bounded reconnect, initial device-request requirement and final-ACK handling.

## Compression and transfer size

The encoder concatenates the original frames into one RGB888 stream, then compresses it using Zstandard level 10 with a window of at most **128 KiB**, content-size metadata and no dictionary. Compressing the complete sequence allows repeated portrait and dashboard pixels to share storage. The [documented Android RGB route](https://github.com/alvinunreal/divoom-minitoo-osx/blob/main/PROTOCOL.md) uses the same window constraint.

In the prepared adult green dashboard, five idle frames took approximately **15 KiB** in RGB/Zstandard versus **104 KiB** as JPEG. These are file-size measurements for illustrative values, not a measured Bluetooth time or a guarantee for every image. Compression preserves the original bytes; it does not reduce visual quality.

The bridge validates the RGB container, native dimensions, frame count, speed, compressed length, declared decompressed size, window limit and Zstandard block boundaries before starting a Bluetooth image transfer. It accepts at most eight native frames, with bounded local request/payload sizes.
