# Security policy

## Reporting a vulnerability

Use **Security → Report a vulnerability** on this repository if private vulnerability reporting is enabled. If that option is unavailable, open an issue asking the maintainer for a private contact channel, without including an exploit, credentials or personal diagnostics. No response-time guarantee is offered.

Review logs before sharing them: they can contain Bluetooth addresses, local paths, session identifiers and account quota values. Never attach Codex authentication files or a copy of a Codex profile. Ordinary device connection problems can be reported as issues with sanitized diagnostics.

## System and scope

This is a user-launched macOS utility. Python reads account limits from a local Codex App Server and sends rendered frames to a bundled Swift Bluetooth bridge. The bridge listens on IPv4 loopback only. Activity hooks update a shared local status file. There is no hosted backend or intentionally public network listener.

Security-sensitive paths include `src/divoom_minitoo_codex/bridge.py`, `diagnostics.py`, `appserver.py`, `activity.py`, both bridges in `Sources/`, and the hook installer and writer in `scripts/`.

## Trust boundaries and required properties

- Unrelated local processes and malformed local socket input must not cause Bluetooth display writes. A per-process credential must be checked before image parsing or transfer work is queued.
- The credential is generated afresh for each bridge process and passed through its inherited standard-input pipe. It must not be written to arguments, environment variables, files or diagnostics. Older bridges without authenticated readiness must be rejected.
- Local requests must have bounded size, receive time and concurrent connection count. Bluetooth transfers must remain serialized and have bounded recovery behavior.
- Active and rotated diagnostic files must be regular files owned by the current user, with permissions `0600`. The application's dedicated default log directory must use `0700`. Log handling must reject final symlinks and shared hardlinks; custom existing parent directories must retain their permissions.
- Account access tokens, prompts, responses and tool output must not be collected by the monitor or hooks. The monitor may display usage values and reset-credit metadata returned by Codex.
- Hook installation must preserve unrelated hooks and provide backups. Shared activity state must contain only the metadata necessary to track activity.

## Assessment context and limitations

Assess severity using the actual exposure and impact: the bridge is local and controls a paired display. Loopback binding alone is not client authentication. Rendering bugs and Bluetooth reliability problems are reportable as ordinary bugs; do not use that distinction to suppress a reachable security defect.

The macOS user account, administrator privileges, the selected Codex executable and installed dependencies are part of the runtime environment. The per-process credential is not intended to isolate a monitor from a process that can inspect or control that same user's memory. No blanket finding exclusions or accepted security exceptions are declared here.

Tests use simulated Bluetooth channels. A restricted execution environment may block the real loopback test; such a skip must be disclosed and checked in an unrestricted macOS run. Physical device behavior requires a separate device check.

Security fixes target the current source on the default branch. Older revisions are not promised backports.
