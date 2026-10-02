# Original adult portrait restored for RGB

On **2026-10-02**, the original adult portrait and its matching blink were restored to `anime-pixel` for an on-device comparison using lossless RGB. These are the initial images generated from text on 2026-10-01, before the hair, eye and skin simplifications. No new artwork was generated for this restoration.

The user confirmed that this restored original looked correct with RGB. It is now preserved as **`anime-pixel-detail`**; `anime-pixel` uses the new simple adult sprite in the chibi drawing style.

## Detail sources

- [Original open-eye image](artwork/anime-pixel-adult-open-source.png)
- [Original matching blink](artwork/anime-pixel-adult-blink-source.png)
- [Original generation brief](ANIME_PIXEL_ADULT_PROMPTS.md)

Run `python scripts/prepare_anime_artwork.py` to export the active pair. The detail asset prefix is `anime_pixel_detail_portrait` and its source prefix is `anime-pixel-adult`, with native eye regions `((25, 31, 47, 44), (52, 38, 69, 51))`. The export retains the current 78 × 78 RGB sampling method, with no global palette limit or dithering. Only the matching blink's eye sockets contribute to the closed-eye frame; the remaining pixels come from the open-eye image. Purple, red, blue and green remain available.

## Device comparison

The user reported that the preceding native 160 × 128 RGB dashboard, blink, WORKING animation and reset-credit screen displayed correctly. The user subsequently confirmed that the restored original artwork displayed correctly with RGB. Earlier cleanup, hair and close-up sources remain available for reference.

Stop the monitor and close the Divoom app and MiniToo audio connection, then run from the repository directory:

```sh
.venv/bin/python scripts/check_minitoo_rgb.py --address AA:BB:CC:DD:EE:FF --theme anime-pixel-detail --color green --output build/minitoo-original-rgb-check
```

This sends four screens with illustrative values (79% remaining and three resets), using RGB888/Zstandard. Start the live monitor afterwards with:

```sh
.venv/bin/codex-minitoo --address AA:BB:CC:DD:EE:FF --theme anime-pixel-detail --color green --encoding rgb
```
