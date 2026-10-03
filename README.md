# Codex usage on Divoom displays

[English](README.md) | [Español](README.es.md)

Show your Codex usage, refill times, activity, and available reset credits on a Divoom MiniToo or TimeBox Mini. The monitor reads the signed-in account through the local Codex App Server. MiniToo receives a 160 × 128 dashboard with the account email and plan in its footer; TimeBox Mini receives a compact screen for its 11 × 11 LED matrix.

This version runs on **macOS**. MiniToo includes six themes: **neon**, **pixel-art**, **anime**, **anime-pixel** (adult in the chibi drawing style), **anime-pixel-chibi**, and **anime-pixel-detail** (detailed adult). TimeBox Mini uses one compact layout designed for its 11 × 11 LED matrix, with optional accent colors. [See the theme gallery](#themes-and-colors).

## Requirements

- A Divoom MiniToo or TimeBox Mini paired with your Mac
- macOS with Bluetooth enabled
- Python 3.10 or later
- Xcode Command Line Tools (`swiftc`); install with `xcode-select --install` if needed
- [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) installed and signed in to a ChatGPT account with Codex usage limits

The monitor runs in Terminal and needs to stay open to keep the display updated. It does not install a background service.

## Install

Clone this repository in Terminal, then run:

```sh
git clone https://github.com/AFrayde01/divoom-minitoo-codex.git
cd divoom-minitoo-codex
./install
```

The installer creates a Python virtual environment and builds Bluetooth bridges for both Divoom models. Then it asks whether to install Codex activity hooks in all detected profiles or choose one. Use **↑ / ↓** and **Enter**, just like the `./start` menus. Discovery includes `CODEX_HOME` (or `~/.codex`) and each profile under `~/Library/Application Support/Parall/*/.codex`, including Codex and ChatGPT instances. All installed profiles use the same local activity state file, with each event attributed to its originating profile. Identical definitions are preserved on reinstall; changed definitions are backed up. Activity-state updates use the same lock as running hooks.

After installation, the terminal prints a `CODEX_HOME=... codex` command for each selected profile. Open each one, run `/hooks`, review and trust the Divoom hooks, then restart the matching Codex or Parall instance. Codex requires this review and does not allow the installer to trust hooks automatically. The installer backs up any existing `hooks.json` before updating it and preserves other hooks. See the [Codex hooks guide](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks).

If you use more than one local account and want WORK/IDLE to follow whichever account you select, install hooks in all profiles and review/trust them in each instance. The default `--activity-scope account` then attributes activity to the selected account. Use `--activity-scope all` only if you want activity combined across every installed profile.

The interactive installer recommends all detected profiles. To skip the menu and install in all of them, run `./install --all-profiles`; to install in one known profile, run `./install --codex-home "/path/to/profile/.codex"`. Without an interactive terminal, it installs in all detected profiles and prints the trust instructions.

If you add a Codex profile later, install its hooks with:

```sh
.venv/bin/python scripts/install_activity_hooks.py install \
  --codex-home "/path/to/profile/.codex"
```

To inspect or repair all detected profiles, including new Parall instances:

```sh
.venv/bin/python scripts/install_activity_hooks.py status --all-profiles
.venv/bin/python scripts/install_activity_hooks.py install --all-profiles
```

`status` checks the five Divoom lifecycle handlers, script paths, originating profile and shared state target. It returns a nonzero status when configuration needs attention; it does not confirm hook trust. Startup also reports missing or mismatched configurations. For each affected Parall instance, launch CLI with that instance's `CODEX_HOME`, review `/hooks`, then restart the instance. For example:

```sh
CODEX_HOME="$HOME/Library/Application Support/Parall/Codex (Personal)/.codex" codex
```

## Update an existing installation

Stop the monitor with `Ctrl+C`, update your repository checkout and run `./install` again. Rebuild **both bridges** to enable local authentication; an older binary is rejected with an upgrade message. Then restart the monitor. Existing hooks retain their configuration; review `/hooks` if Codex asks you to trust an updated hook.

For the profile activity update, run `./install` and choose all profiles or one profile when prompted. To repair hooks without rebuilding the bridges, run `.venv/bin/python scripts/install_activity_hooks.py setup` directly. Each hook command includes its originating `--codex-home`. Installation removes older activity records without a profile because they cannot be attributed reliably; new prompts create fresh records. A monitor using the selected-account scope ignores those old records even before installation.

The update also installs the lossless RGB compressor and rebuilds MiniToo's RGB-capable bridge. **Lossless RGB888/Zstandard is now the MiniToo default**, at the native 160 × 128 size. You do not need to pass `--encoding rgb`. Use `--encoding jpeg` to explicitly select JPEG. [RGB usage and native display check](docs/MINITOO_RGB.md).

## Find the Divoom Bluetooth address (optional)

`./start` automatically reads supported paired speakers from macOS Bluetooth, so you normally do not need an address. Pair the speaker in macOS Bluetooth settings first. Detection recognizes MiniToo and TimeBox Mini by their Bluetooth names; if you renamed yours or want to specify one manually, find its address as follows:

1. Turn on the Divoom device and pair it in **System Settings → Bluetooth**.
2. Open **System Information → Hardware → Bluetooth**, find the MiniToo or TimeBox Mini in the device list, and copy its **Address**. You can also inspect the list in Terminal:

   ```sh
   system_profiler SPBluetoothDataType
   ```

3. Use the Divoom device's Bluetooth address, in a format like `AA:BB:CC:DD:EE:FF`. This is not your Mac's Bluetooth address or an IP address.

If the MiniToo is connected as a Bluetooth audio device, disconnect that audio profile before starting the monitor. For TimeBox Mini, close the Divoom app if it already has an active connection.

## Start the monitor

Start the continuous monitor with:

```sh
./start
```

After the language choice, startup offers a Codex account selector when several account options are available, including Parall instances, with the account's email and plan when available. Then, if macOS has one supported Divoom paired, its address and model are selected automatically. If there are several, choose the speaker from the menu; currently connected speakers appear first, with MiniToo preferred when connection status is equal. Connected status does not guarantee that the image channel is free or that a disconnected paired speaker is powered on. The monitor then offers the theme and supported color, with your previous choices selected. The first MiniToo theme is **neon**. TimeBox Mini uses its compact layout and offers its accent colors.

To show only TimeBox Mini devices:

```sh
./start --device timebox-mini
```

Keep Terminal open while it runs; stop it with `Ctrl+C`. It reads usage at startup and every 60 seconds, checks activity every second, and reads usage again when a Codex turn ends. It sends an image when the display changes. The hook is silent in the Codex conversation; its status appears on the display.

### Startup choices and terminal output

- Use **↑ / ↓** to move through languages, accounts, speakers, themes and colors, then **Enter** to select. Numbers **1–9** jump to an option; **Esc / Q** or **Ctrl+C** cancel. Press Enter immediately to keep the highlighted choice. Terminals without key-mode support fall back to number/name input. Anime colors start with purple; TimeBox Mini starts with cyan. Neon and the robot pixel-art theme use fixed palettes.
- Explicit `--language`, `--codex-home`, `--theme` and `--color` values take priority and skip their respective questions. Continuous runs remember theme/color choices separately for each device, one shared language, and the last profile that successfully returned usage.
- Add `--no-prompt` to start directly with explicit options or your saved choices. `--once`, `--preview`, redirected input/output and `TERM=dumb` also skip the menu; once/preview runs leave saved choices unchanged.
- Without a menu, automatic detection must find exactly one matching speaker; otherwise specify `--device` or `--address`. An explicit address (or `MINITOO_ADDRESS`) bypasses detection; without a model, an explicit address uses MiniToo. Preview defaults to MiniToo without reading Bluetooth.
- Transfer updates **replace one status line** by default. It shows the latest send time, remaining quota, activity and displayed page. Long status text is clipped to fit the terminal; errors and the diagnostic log retain full details.
- Add `--sent detailed` for one complete line per successful send, including TimeBox Mini animation frames. Redirected output always uses plain lines.

For example:

```sh
./start --no-prompt
./start --sent detailed
```

Preferences are stored locally in `~/Library/Application Support/divoom-minitoo-codex/minitoo.json` or `timebox-mini.json`. These private files contain only the theme and color. The shared CLI/display language is stored in `language.json`, and the selected Codex profile directory in `account.json`, within the same folder. If they cannot be saved, the monitor continues and prints a notice.

`./start` uses the repository's virtual environment without requiring activation. After installation, `.venv/bin/divoom-codex start` and the existing `.venv/bin/codex-minitoo` entry point are also available. All support the same options. If no speaker is detected in an interactive terminal, the menu lets you retry after pairing or enter an address manually.

### Language

Run the CLI and all MiniToo themes in Spanish:

```sh
./start --language es
```

Use `--language en` for English, or `--lang` as an alias. `./start` offers a **Language / Idioma** selector before the account/speaker/theme/color menus and highlights the last selection. The initial language is English. `--no-prompt` restores the saved language; an explicit flag overrides it. Continuous runs save the language, while `--once`, `--preview` and `--help` do not change preferences.

The language applies to menus, help, monitor messages and every theme's usage/reset-credit screen. Spanish dates use **day/month** (with a two-digit year on reset-credit lists); hours stay in 24-hour format. The compact display uses **ACTIVO**, **REPOSO**, **RECARGA** and **REINICIOS**. TimeBox Mini keeps its language-independent numbers and bars. Command values such as `green` and `anime-pixel` stay the same; native Bluetooth/protocol diagnostics stay verbatim for troubleshooting.

## Themes and colors

These previews are generated by the same renderers used for each device. The percentages and reset counts are illustrative; `CODER@EXAMPLE.COM` is a fictional account email. The gallery below shows MiniToo; use `./start --device timebox-mini` for the compact TimeBox Mini layout.

| Neon (first-start default) | Pixel art |
| --- | --- |
| ![Neon usage theme](docs/images/neon.png) | ![Pixel art usage theme](docs/images/pixel-art.png) |
| `--theme neon` | `--theme pixel-art` |

The **anime** theme has four color variants. Purple is the default:

| Purple | Red |
| --- | --- |
| ![Anime purple usage theme](docs/images/anime-purple.png) | ![Anime red usage theme](docs/images/anime-red.png) |
| `--theme anime --color purple` | `--theme anime --color red` |

| Blue | Green |
| --- | --- |
| ![Anime blue usage theme](docs/images/anime-blue.png) | ![Anime green usage theme](docs/images/anime-green.png) |
| `--theme anime --color blue` | `--theme anime --color green` |

For example, start the green variant with:

```sh
./start \
  --theme anime --color green
```

`-color` also works as an alias for `--color`. On MiniToo, neon and pixel art have one palette each; if you pass a color with either theme, the monitor prints a notice and uses that theme's default colors. All anime portrait themes blink by cycling through complete display frames and animate their WORKING badge. Pixel art animates its robot and background; neon animates its working indicator.

The anime portrait was created for this project from a written character brief, with no external reference images. Its source files, generation prompts and native-frame export instructions are recorded in [Artwork provenance](docs/ARTWORK.md).

![Anime working indicator and blink animation](docs/images/anime-demo.gif)

### Anime pixel art

Select **anime-pixel** for an adult woman around 24, drawn in the same simple retro sprite style as the chibi: broad connected hair shapes, clean pixel contours, a compact nose and a short closed smile. Adult proportions and smaller almond eyes distinguish her from the chibi. The [adult sprite brief and sources](docs/ANIME_PIXEL_ADULT_RETRO.md) document this revision. Both use a shared artistic palette of up to 16 colors, not a hardware color limit. The native 78 × 78 portrait keeps the anime dashboard: remaining quota, refill countdowns, RESET dates, reset bank and animated activity, with bitmap text and square frames. Skin, cheeks and background remain identical during a blink. Purple, red, blue and green remain supported. The first-start theme is `neon`; later runs restore your saved choice.

![Anime pixel art working indicator and blink animation](docs/images/anime-pixel-demo.gif)

The same four colors are supported; purple is the default:

| Purple | Red |
| --- | --- |
| ![Anime pixel art in purple](docs/images/anime-pixel-purple.png) | ![Anime pixel art in red](docs/images/anime-pixel-red.png) |
| `--theme anime-pixel --color purple` | `--theme anime-pixel --color red` |

| Blue | Green |
| --- | --- |
| ![Anime pixel art in blue](docs/images/anime-pixel-blue.png) | ![Anime pixel art in green](docs/images/anime-pixel-green.png) |
| `--theme anime-pixel --color blue` | `--theme anime-pixel --color green` |

```sh
./start \
  --theme anime-pixel --color green
```

| Single quota window | Reset bank |
| --- | --- |
| ![Green anime pixel art with one vertical quota bar and blinking animation](docs/images/anime-pixel-green-pro-demo.gif) | ![Anime pixel art reset-credit screen](docs/images/anime-pixel-resets.png) |

The pixel characters began with independent text-only generations, followed by edits using only this project's own generated artwork. Open-eye and blink images are exported at 78 × 78 as RGB runtime assets. The simple adult and chibi use an artistic palette; the detailed adult preserves its full RGB tones. Sources, prompts and export details are recorded in [Pixel artwork provenance](docs/ANIME_PIXEL_ARTWORK.md).

### Anime pixel art detail

Select **anime-pixel-detail** to keep the original adult portrait with its richer hair, eyes and facial shading. This is the detailed version preserved after the successful RGB comparison. It keeps its full native RGB tones and the same dashboard, blink, WORKING animation, reset bank and four colors. [Sources and restoration notes](docs/ANIME_PIXEL_ADULT_ORIGINAL_RGB.md).

![Detail blink and working animation](docs/images/anime-pixel-detail-demo.gif)

| Purple | Red |
| --- | --- |
| ![Detail purple](docs/images/anime-pixel-detail-purple.png) | ![Detail red](docs/images/anime-pixel-detail-red.png) |
| `--theme anime-pixel-detail --color purple` | `--theme anime-pixel-detail --color red` |

| Blue | Green |
| --- | --- |
| ![Detail blue](docs/images/anime-pixel-detail-blue.png) | ![Detail green](docs/images/anime-pixel-detail-green.png) |
| `--theme anime-pixel-detail --color blue` | `--theme anime-pixel-detail --color green` |

| Single quota window | Reset bank |
| --- | --- |
| ![Detail single quota animation](docs/images/anime-pixel-detail-green-pro-demo.gif) | ![Detail reset bank](docs/images/anime-pixel-detail-resets.png) |

```sh
./start --address AA:BB:CC:DD:EE:FF --theme anime-pixel-detail --color green --encoding rgb
```

### Anime pixel art chibi

The previous pixel character is preserved as **anime-pixel-chibi**, with a compact face and large eyes. It shares the adult variant's layout, blink and `purple`, `red`, `blue` and `green` colors. Both simple pixel characters have a gentle smile with their eyes open and a broader smile during the closed-eye frame. [Smile sources and animation export](docs/ANIME_PIXEL_SMILES.md).

![Chibi blink and working animation](docs/images/anime-pixel-chibi-demo.gif)

| Purple | Red |
| --- | --- |
| ![Purple chibi](docs/images/anime-pixel-chibi-purple.png) | ![Red chibi](docs/images/anime-pixel-chibi-red.png) |
| `--theme anime-pixel-chibi --color purple` | `--theme anime-pixel-chibi --color red` |

| Blue | Green |
| --- | --- |
| ![Blue chibi](docs/images/anime-pixel-chibi-blue.png) | ![Green chibi](docs/images/anime-pixel-chibi-green.png) |
| `--theme anime-pixel-chibi --color blue` | `--theme anime-pixel-chibi --color green` |

### TimeBox Mini 11 × 11 display

When Codex is idle, TimeBox Mini alternates between thick quota bars and only the remaining percentage for the window with the nearest upcoming refill. When both windows are available, the shorter window appears above the longer one. If only a 7D window is available, it uses one centered vertical bar. While Codex is working, a full-matrix pulse animation fills the display; every ten seconds, it pauses for two seconds to show the remaining percentage.

The animated preview shows the working animation, the quota bars, the remaining percentage, and the reset count. The GIF compresses the wait. On the device, the working animation runs for eight seconds, then the percentage appears for two seconds. While idle, bars and percentage alternate every ten seconds. If credits are available, the reset count appears for eight seconds every five minutes and temporarily takes over the display.

![Animated TimeBox Mini preview with 5H and 7D bars, remaining percentage, and reset count](docs/images/timebox-mini-demo.gif)

When an account only has a 7D window, this preview shows the centered vertical bar and its other display states:

![Animated TimeBox Mini preview with only a 7D quota](docs/images/timebox-mini-7d-demo.gif)

The default accent is cyan. You can choose **purple**, **red**, **blue**, or **green** with `--color`. The reset-count screen uses the selected accent and shows only the count in larger digits.

For example, select green with:

```sh
./start \
  --device timebox-mini --color green
```

## Read the display

### MiniToo

- **5H** and **7D** identify the Codex usage windows returned for the account. Some plans return only one window.
- The large percentage and main bar show **usage remaining**, starting at 100% and shrinking as Codex is used.
- The slim vertical bar beside each window shows **time remaining until that window refills**. It shrinks toward the refill.
- **RESET** shows the expected local refill time for a short window or local date for a longer window.
- The footer shows the account email in **UPPERCASE** on the left and the **PLAN** on the right, in every MiniToo theme and on reset-credit screens. Long emails are shortened with `...` to keep the plan visible. If an email is unavailable, it is omitted.
- **WORK/WORKING** means an installed activity hook sees an active Codex turn within the selected activity scope. **IDLE** means no active turn. **SETUP** means matching activity hooks have not been detected. When only one usage window is available, the anime portrait themes use a taller vertical meter beside the portrait.

For example, the anime layout with a single Pro usage window looks like this:

![Anime theme with one vertical Pro usage window](docs/images/anime-single-window.png)

The email is read with `account/read` from the same local Codex App Server/profile as the quotas, at each usage refresh. No additional option is needed. If this optional lookup fails, usage and reset credits continue to display with the plan.

### TimeBox Mini

The quota-bar screen shows remaining quota. If there are two windows, the shorter window is the upper bar and the longer window is the lower bar. If only one window is available and it is 7D, one centered vertical bar is shown. The next screen shows only the remaining percentage (for example, **62%**) for the window with the nearest upcoming refill. During WORKING, the full matrix shows the pulsing animation for eight seconds, then the remaining percentage for two seconds, repeating until the turn ends.

### Reset-credit screen

If your account has available rate-limit reset credits, a separate screen appears **every five minutes for eight seconds**. MiniToo shows the available count and up to three expiry dates with days remaining. TimeBox Mini shows only the count in larger digits. If Codex returns only the count, MiniToo still shows it without dates. With zero available credits, this screen is skipped. MiniToo uses the selected theme; TimeBox Mini uses the selected accent.

MiniToo reset-screen examples:

| Neon | Pixel art | Anime |
| --- | --- | --- |
| ![Neon reset-credit screen](docs/images/neon-resets.png) | ![Pixel art reset-credit screen](docs/images/pixel-art-resets.png) | ![Anime reset-credit screen](docs/images/anime-resets.png) |

The usage windows and reset-credit details come from Codex App Server's [`account/rateLimits/read`](https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt) method. This project only displays reset credits; it does not redeem them.

You can also pass the address as an option:

```sh
./start --address "AA:BB:CC:DD:EE:FF"
```

## Use multiple Codex accounts

If you have separate Codex or Parall profiles signed in to different ChatGPT accounts, run `./start` and choose an account with **↑ / ↓** and **Enter**. Discovery includes the default Codex profile, `CODEX_HOME`, and existing `.codex` directories inside Parall instance folders under `~/Library/Application Support/Parall/`, including Codex and ChatGPT instances. These are local profiles; an instance can be listed even when its app is closed. Names identify the profile folders, while `account/read` confirms the signed-in account. The selector queries Codex App Server without reading or copying authentication files itself.

For example, the menu can show these fictional accounts:

```text
Codex · account
  1. Codex · default profile · PLAN PRO · MAIN@EXAMPLE.COM
› 2. Parall · Codex (Personal) · PLAN PLUS · PERSONAL@EXAMPLE.COM
```

Before showing the menu, startup reads account metadata and requests live usage from every detected ChatGPT profile. Only profiles that return usage windows successfully are offered. Checks run one at a time with bounded RPC timeouts to avoid simultaneous credential refreshes between cloned profiles. A timeout or failed check is not treated as a usable session; its reason is reported when no verified profile represents that account.

Profiles with the same email and plan share one menu option. A profile with verified usage takes priority over a saved directory or app name. Among verified profiles, the saved directory takes priority, or `CODEX_HOME` when no directory has been saved. Otherwise automatic selection prefers a Parall Codex instance, then the default CLI profile, then a custom profile, then other Parall instances. Use `--codex-home` to choose any particular directory directly.

The email and plan identify local account metadata; a successful usage request verifies access at the time of selection. Startup requests usage again before connecting Bluetooth because credentials can change while you choose a speaker or theme. If a verified profile then returns **401 Unauthorized**, recovery tries the other profiles grouped under that account after checking their email and plan again. The profile that returns usage successfully becomes the saved choice. Direct `--codex-home` and unattended starts use exactly their resolved directory and verify usage at connection time. If authentication is rejected without a successful fallback, the monitor prints the affected directory and a `CODEX_HOME=... codex login` command. It does not sign you in automatically.

Identity lookups do not request a forced token refresh; Codex manages authentication for the actual usage requests. Signed-out, API-key-only, Bedrock, rejected and unverified profiles are not selectable. If no profile returns live usage, startup stops with an explanation. If the email is unavailable but usage succeeds, the profile is offered without an email and stays separate because its identity cannot be compared.

The last profile is highlighted on subsequent interactive starts after it successfully returns usage. Only its directory is saved in `~/Library/Application Support/divoom-minitoo-codex/account.json`; emails, plans and credentials are not saved there. Interactive starts use the saved selection first, or `CODEX_HOME` when no profile has been saved. With menus skipped, the priority is `--codex-home`, `CODEX_HOME`, the saved profile, then the CLI default. Once/preview runs do not change this preference. If a saved directory was removed, interactive starts offer another choice; unattended runs report the missing profile.

The usage bars belong to the ChatGPT account signed in to the selected profile. To choose a directory directly and skip the account selector, use `--codex-home`:

```sh
./start \
  --codex-home "$HOME/Library/Application Support/Parall/ChatGPT (Personal)/.codex"
```

Substitute the profile directory you actually use. The monitor displays one account's usage at a time; restart it to select another profile. By default, activity follows the selected profile and the other local profiles grouped under the same email and plan during interactive discovery. A different account in another Parall instance or the native app does not activate this account's indicator. Direct and unattended starts follow only the resolved profile. Use `--activity-scope all` to combine every installed local profile instead. This does not detect work on another computer or ordinary ChatGPT conversations that do not execute these Codex hooks. API-key-only and Bedrock sessions do not provide the ChatGPT usage windows this display needs.

The monitor checks activity once per second. A missing `Stop` is recovered when the recorded Codex/app owner process has exited, or when the hook-provided local transcript contains a completion or interruption record for the same turn. These checks do not expire a running turn just because it has been quiet. Transcript recovery is best effort because Codex's transcript format is not a stable interface. If neither signal is available, the existing 24-hour orphan limit remains the fallback. `Stop` and `Interrupt` clear only their matching turn; a delayed event cannot clear a newer turn, and completion no longer creates an extra WORKING pulse.

## Options

Save a preview without connecting to a Divoom display or providing an address. A signed-in Codex profile is still required because the preview uses live usage data:

```sh
./start --theme anime --color blue --preview preview.png
```

To preview the compact TimeBox Mini layout in blue:

```sh
./start --device timebox-mini --color blue --preview timebox-mini-preview.png
```

Send one update and exit:

```sh
./start --once
```

Refresh usage every 90 seconds (the minimum is 10 seconds):

```sh
./start --interval 90
```

| Option | Purpose |
| --- | --- |
| `start` | Optional command; starts the monitor. The repository launcher is `./start`. |
| `--address ADDRESS` | Optional manual Bluetooth MAC address; also accepts `MINITOO_ADDRESS`. Omit for paired-speaker detection. |
| `--device DEVICE` | Filters automatic detection to `minitoo` or `timebox-mini`; an explicit address without this option uses MiniToo |
| `--theme neon`, `--theme pixel-art`, `--theme anime`, `--theme anime-pixel`, `--theme anime-pixel-chibi`, `--theme anime-pixel-detail` | MiniToo theme; explicit option overrides the saved choice. Initial choice: `neon`. TimeBox Mini always uses its compact layout. |
| `--color`, `-color` | Overrides the saved color. TimeBox Mini: `cyan` (initial), `purple`, `red`, `blue`, `green`; MiniToo portrait themes: `purple` (initial), `red`, `blue`, `green` |
| `--language en`, `--language es`, `--lang` | CLI and display language; overrides the saved choice. Initial choice: English |
| `--no-prompt` | Skip startup selection; use explicit language/theme/color or saved choices |
| `--sent compact`, `--sent detailed` | Compact single-row status (default) or a complete line for every sent update; redirected output uses plain lines |
| `--codex-home PATH` | Select a Codex profile directly; overrides the account selector and saved choice |
| `--activity-scope account\|all` | Follow the selected account's local profiles (default), or combine all installed local profiles |
| `--codex-bin PATH` | Codex CLI executable; also accepts `CODEX_BIN` |
| `--interval SECONDS` | Usage refresh interval; default: `60`, minimum: `10` |
| `--encoding rgb`, `--encoding jpeg` | MiniToo encoding; default: lossless RGB888/Zstandard. JPEG remains available explicitly. TimeBox Mini always uses RGB444. |
| `--preview FILE` | Write one PNG without Bluetooth |
| `--once` | Send one update, then exit |
| `--log-file FILE` | Diagnostic log; default: `~/Library/Logs/divoom-minitoo-codex/<device>-<port>.log`. Private (`0600`); rotates at 1 MiB with two backups. |

If `codex` is not on Terminal's `PATH`, set `CODEX_BIN` to the CLI executable:

```sh
CODEX_BIN="/path/to/codex" ./start
```

## Animation support

MiniToo themes send complete frames for their animations, using **lossless RGB888/Zstandard by default** or JPEG with `--encoding jpeg`. RGB compresses the full sequence together while preserving frame colors and timing. The [native RGB check](docs/MINITOO_RGB.md) can help diagnose display issues on your firmware. TimeBox Mini uses its own 11 × 11 RGB444 Bluetooth protocol and sends a new matrix image once per second while the full-screen WORKING animation runs. It does not upload a GIF. While idle, it alternates between quota bars and the remaining percentage for the nearest refill. The MiniToo uses Bluetooth RFCOMM channel 1, while TimeBox Mini uses channel 4. Their local bridges use ports `40584` and `40585`, respectively, so both model monitors can run at the same time. The TimeBox Mini image protocol follows [community documentation](https://github.com/MarcG046/timebox/blob/master/doc/protocol.md) rather than a public Divoom API.

## Troubleshooting

- **No speaker detected:** Turn it on, enable Bluetooth and pair it in macOS Bluetooth settings. Allow Terminal Bluetooth access if macOS asks. Detection recognizes the supported model names; renamed speakers can use the manual address option in the menu. Re-run `./install` if the detection helper is missing. Other Divoom models are not automatically selected.
- **Checkerboard or mottled fine details on MiniToo:** A physical [JPEG versus RGB comparison](docs/MINITOO_CODEC_COMPARISON.md) eliminated this defect with lossless RGB on a tested 128 × 128 image. Use the [native RGB check](docs/MINITOO_RGB.md) for the full dashboard and animations, then select `--encoding rgb` if they display correctly. The earlier [JPEG quality comparison](docs/JPEG_QUALITY_COMPARISON.md) remains available for diagnostics.
- **No usage bars:** Sign in to a ChatGPT account with Codex usage in the selected profile. If you use a separate profile, pass its path with `--codex-home`.
- **401 Unauthorized / authentication token could not be parsed:** The credential used for the account's usage request was rejected. Interactive startup omits accounts whose profiles fail the live usage check. Credentials can still expire or change after that check. Restart `./start` to verify the profiles again; startup can recover through a matching profile if authentication changes after selection. If they all fail, follow the sign-in command printed for the affected directory and restart the monitor. Each Parall profile has its own sign-in state; signing in to the default CLI profile may not repair the selected profile. See the [Codex App Server authentication documentation](https://learn.chatgpt.com/docs/app-server#auth-endpoints).
- **The bridge reports no data or an invalid response:** Run `./install` again to rebuild the bridges, confirm the selected Divoom is paired, and check its MAC address. For TimeBox Mini, close the Divoom app while connecting.
- **Connection lost, bridge stopped, or transfer not confirmed:** The monitor closes the failed bridge and retries once over a new Bluetooth session. If both attempts fail, continuous monitoring keeps running and retries the current screen after 5, 10, 20, 40, then at most 60 seconds between attempts. Failed transfers are not cached as completed. `--once` exits with an error if neither attempt succeeds. Errors include the connection stage, the bridge exit code when available, and recent bridge logs.
- **MiniToo stays on its loading screen:** The bridge handles chunk requests during both streaming and pull-mode transfers, validates packet checksums, and recognizes the [captured final completion response](https://github.com/alvinunreal/divoom-minitoo-osx/blob/main/PROTOCOL.md#final-ack) instead of treating any reply as confirmation. It requires an initial data request within 5 seconds: if MiniToo does not respond, it sends no image chunks and reconnects instead of uploading blindly. It waits up to 10 seconds for a requested block, uses a 40-second Bluetooth transaction deadline, and gives the local response up to 60 seconds. Missing confirmation triggers recovery on any screen. If the device is already stuck from a previous incomplete upload, stop the monitor, close the Divoom app and MiniToo Bluetooth audio connection, power-cycle the MiniToo, then restart the monitor. A missing acknowledgement means completion is unconfirmed; it does not by itself prove that the screen failed to update.
- **Diagnosing a recurring freeze:** Each monitor saves timestamped errors and bridge output, including incoming Bluetooth control bytes. The default MiniToo log is `~/Library/Logs/divoom-minitoo-codex/minitoo-40584.log`; TimeBox Mini uses `~/Library/Logs/divoom-minitoo-codex/timebox-mini-40585.log`. The full path is printed at startup. Override it with `--log-file /path/to/monitor.log`. When reporting a freeze, include the log section around that time: it can distinguish an unresponsive device from an unrecognized reply. Logs include connection addresses and displayed quota values, but do not contain prompts, access tokens, or image data.
- **Local bridge port is already in use:** Stop the other monitor for the same model. The monitor waits for its own bridge's readiness message; another process listening on the port is not considered a successful connection. MiniToo and TimeBox Mini can run together because their default ports are different (`40584` and `40585`).
- **The screen does not show WORK:** Run `.venv/bin/python scripts/install_activity_hooks.py status --all-profiles`. If configuration is missing, run the same command with `install` instead of `status`; it covers both Codex and ChatGPT instances in Parall. Keep the monitor running, review and trust the Divoom hooks with `/hooks` in the same profile that received the prompt, then restart that profile. A hook does not reply in the Codex conversation; it updates `~/.codex/divoom-minitoo-codex-activity.json` for the monitor.
- **WORK stays visible or comes from another account:** Restart with the default `--activity-scope account`, update the hooks with `install --all-profiles`, trust their new definitions and restart the affected Codex instances. Old records without an originating profile are discarded during installation. Process-exit and same-turn completion checks handle missed closure events when that evidence is available; the monitor does not count another account's activity in the default scope.
- **Bluetooth access is denied:** Allow Bluetooth access for the process that runs the bridge in macOS System Settings.
- **An hourglass appears during a MiniToo update:** The MiniToo can show its own transfer/loading screen when it receives changed frames. The monitor avoids sending identical frames, but a visible state change can still trigger that screen.

## Connection checks for development

Run the failure simulations with:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

These checks cover socket errors, process readiness and shutdown, incomplete responses, reconnect attempts, delayed retries of an unchanged screen, and persistent diagnostics. On macOS with Swift installed, they also compile the actual MiniToo transfer code against an in-memory RFCOMM channel to check fragmented packets, checksums, missing-block requests, final acknowledgements, disconnects, and a silent device that must never receive a blind animation upload. They do not open a Bluetooth connection; physical device behavior must be checked separately.

## Remove the hooks

Remove the Divoom activity hook from the CLI and detected Codex App profiles with:

```sh
.venv/bin/python scripts/install_activity_hooks.py uninstall --all-profiles
```

Other hooks in those profiles are preserved. This command does not remove the Python environment or Swift bridge.

## Privacy and gallery maintenance

The monitor does not read or store access tokens. The activity hooks store local profile paths, session and turn identifiers, timestamps, an owner process id when available and an optional local transcript path; they do not store prompts, responses, or tool output. For a missed closure hook, the monitor may read up to 256 KiB from the end of that transcript and retain only completion lifecycle identifiers and timestamps. Transcript contents are not logged, saved or uploaded. Usage data and the account email are read locally from Codex App Server and rendered into MiniToo display frames. The gallery generator uses only sample values and a fictional email; it does not query your account.

After changing a renderer, regenerate the README's sample images with:

```sh
.venv/bin/python scripts/generate_theme_gallery.py --language all
```


## License and contributions

This project uses the [MIT license](LICENSE): sharing, modification and reuse are permitted while retaining its notices. This includes project code, documentation and project-created artwork to the extent applicable rights exist. Trademarks and dependencies retain their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Current artwork and generation briefs are documented for [anime](docs/ARTWORK.md) and [adult/chibi pixel art](docs/ANIME_PIXEL_ARTWORK.md). Gallery images use sample data. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) to contribute or report a vulnerability.

Both bridges check a fresh per-process credential before accepting images. It is delivered through a private pipe, without storing it in process arguments, environment variables or logs. New and rotated logs have `0600` permissions; the dedicated default directory has `0700`. Older `build/` logs are also protected when starting with the default configuration. Review Bluetooth addresses and personal paths before sharing a log.

The terminal welcome screen shows the model, theme, color, refresh interval and log path. `NO_COLOR=1` disables colors; redirected output stays plain.


For the first publication with a clean history, see [PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md).
