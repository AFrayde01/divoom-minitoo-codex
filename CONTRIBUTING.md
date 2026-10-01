# Contributing

Use the [English README](README.md) or [Spanish README](README.es.md) to set up the project on macOS. Pull requests and bug reports are welcome.

For development without installing hooks into your Codex profiles:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Compile each bridge separately with `swiftc`, the `IOBluetooth` and `Network` frameworks, as shown in `scripts/install.sh`. Tests simulate Bluetooth; they do not connect to a physical Divoom. The loopback listener tests require permission to bind local ports.

Keep the English and Spanish READMEs in sync. After a renderer or artwork change, run:

```sh
.venv/bin/python scripts/prepare_anime_artwork.py
.venv/bin/python scripts/generate_theme_gallery.py
```

Preserve the native device sizes, remaining-quota semantics, reset metadata and palette support. Check both one-window and two-window layouts, idle/working states and reset-credit pages. New characters need independently created or appropriately licensed source artwork with documented provenance and matching blink frames.

Include the device model, macOS version, theme/color and sanitized error output in bug reports. Use placeholder Bluetooth addresses. Follow [SECURITY.md](SECURITY.md) for vulnerabilities. Avoid uploading account files, authentication tokens, private conversations or real account screenshots.

Contributions are offered under the project's [MIT license](LICENSE). Third-party contributions must carry the required permissions and notices.
