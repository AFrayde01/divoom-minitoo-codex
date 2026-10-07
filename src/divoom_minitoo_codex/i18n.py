"""Shared English/Spanish wording for terminal UI and native display frames."""

from __future__ import annotations

import re

LANGUAGES = {"en": "English", "es": "Español"}

# Command values and protocol diagnostics remain stable across languages.
_SPANISH = {
    "Display Codex usage limits on a Divoom MiniToo or TimeBox Mini.": "Muestra los límites de uso de Codex en una Divoom MiniToo o TimeBox Mini.",
    "Start the monitor (default).": "Inicia el monitor (predeterminado).",
    "CLI and display language: en or es. Defaults to the saved choice, initially English.": "Idioma del CLI y la pantalla: en o es. Usa la elección guardada; inicialmente inglés.",
    "Optional Bluetooth MAC address (or MINITOO_ADDRESS); otherwise detect paired Divoom speakers.": "Dirección MAC Bluetooth opcional (o MINITOO_ADDRESS); si se omite, detecta bocinas Divoom emparejadas.",
    "Path to the Codex executable (or set CODEX_BIN).": "Ruta al ejecutable de Codex (o establece CODEX_BIN).",
    "Codex profile whose sign-in and usage limits should be queried.": "Perfil de Codex cuya cuenta y límites de uso se consultarán.",
    "Codex profile to monitor; overrides the account selector and saved choice.": "Perfil de Codex que se monitorizará; tiene prioridad sobre el selector y la preferencia guardada.",
    "Activity: selected account's local profiles (default), or all installed profiles.": "Actividad: perfiles locales de la cuenta seleccionada (predeterminado) o todos los perfiles instalados.",
    "Activity follows the selected account's local profiles.": "La actividad corresponde a los perfiles locales de la cuenta seleccionada.",
    "Activity follows all installed local profiles.": "La actividad combina todos los perfiles locales instalados.",
    "Codex · default profile": "Codex · perfil predeterminado",
    "Codex · current profile": "Codex · perfil actual",
    "Codex · account": "Codex · cuenta",
    "Finding Codex profiles and reading account details…": "Buscando perfiles de Codex y consultando sus cuentas…",
    "Finding Codex profiles and verifying usage access…": "Buscando perfiles de Codex y verificando el acceso a las cuotas…",
    "Checking usage access: {name}…": "Verificando el acceso a las cuotas: {name}…",
    "Authentication rejected (401); sign-in required": "Autenticación rechazada (401); es necesario iniciar sesión",
    "Omitted {name}: {reason}.": "Se omite {name}: {reason}.",
    "No Codex profile returned live usage. Sign in to Codex or retry after checking the connection.": "Ningún perfil de Codex devolvió cuotas actuales. Inicia sesión en Codex o vuelve a intentarlo después de revisar la conexión.",
    "Accounts with verified usage access: {count}.": "Cuentas con acceso a las cuotas verificado: {count}.",
    "The Codex profile's account changed while checking usage. Restart ./start.": "La cuenta del perfil de Codex cambió al comprobar las cuotas. Reinicia ./start.",
    "Account unavailable": "Cuenta no disponible",
    "Not signed in": "Sin sesión",
    "No ChatGPT usage limits": "Sin cuotas de ChatGPT",
    "Codex profile: {name}": "Perfil de Codex: {name}",
    "Could not read the saved Codex profile. {detail}": "No se pudo leer el perfil de Codex guardado. {detail}",
    "The saved Codex profile is no longer available. Choose another profile.": "El perfil de Codex guardado ya no está disponible. Elige otro perfil.",
    "No Codex profiles found. Sign in to Codex or provide --codex-home.": "No se encontraron perfiles de Codex. Inicia sesión en Codex o indica --codex-home.",
    "Codex profile directory not found: {path}. Run ./start interactively or provide --codex-home.": "No se encontró el directorio de Codex: {path}. Ejecuta ./start de forma interactiva o indica --codex-home.",
    "Could not save the Codex profile; this monitor will still run. {detail}": "No se pudo guardar el perfil de Codex; el monitor continuará. {detail}",
    "Trying another profile for the selected account: {name}.": "Probando otro perfil de la cuenta seleccionada: {name}.",
    "Skipping {name}: its account no longer matches the selected account.": "Se omite {name}: su cuenta ya no coincide con la seleccionada.",
    "Authentication rejected for {name}; trying a matching profile.": "Autenticación rechazada para {name}; se probará otro perfil de la misma cuenta.",
    "Could not use matching profile {name}. {detail}": "No se pudo usar el perfil de la misma cuenta {name}. {detail}",
    "Using matching Codex profile: {name}.": "Se usará otro perfil de Codex de la misma cuenta: {name}.",
    "The selected account is no longer available. Restart ./start to select it again.": "La cuenta seleccionada ya no está disponible. Reinicia ./start para seleccionarla otra vez.",
    "Codex rejected authentication for {name} (401). Sign in again to this profile, then restart the monitor.": "Codex rechazó la autenticación de {name} (401). Vuelve a iniciar sesión en este perfil y reinicia el monitor.",
    "Codex profile directory: {path}": "Directorio del perfil de Codex: {path}",
    "Sign-in command: {command}": "Comando para iniciar sesión: {command}",
    "Activity hooks are missing from this profile": "Faltan los hooks de actividad en este perfil",
    "Could not read this profile's activity hooks": "No se pudieron leer los hooks de actividad de este perfil",
    "Activity hook command is invalid": "El comando del hook de actividad no es válido",
    "Activity hook script is missing": "No se encontró el script del hook de actividad",
    "Activity hooks write to a different state file": "Los hooks de actividad escriben en otro archivo de estado",
    "Activity hooks need the profile tracking update": "Hay que actualizar los hooks para identificar su perfil",
    "Activity hooks identify a different profile": "Los hooks de actividad identifican otro perfil",
    "Some activity lifecycle hooks are missing": "Faltan algunos hooks del ciclo de actividad",
    "Activity hooks need attention in {name}: {reason}.": "Hay que revisar los hooks de actividad de {name}: {reason}.",
    "Hook installation command: {command}": "Comando para instalar los hooks: {command}",
    "Run scripts/install_activity_hooks.py install --all-profiles from the repository.": "Ejecuta scripts/install_activity_hooks.py install --all-profiles desde el repositorio.",
    "Review and trust the new hooks with /hooks in each affected profile, then restart that Parall instance.": "Revisa y autoriza los nuevos hooks con /hooks en cada perfil afectado y reinicia esa instancia de Parall.",
    "Restrict detection to minitoo or timebox-mini. An explicit address without a model uses MiniToo.": "Limita la detección a minitoo o timebox-mini. Una dirección explícita sin modelo usa MiniToo.",
    "Refresh interval in seconds (default: 60).": "Intervalo de actualización en segundos (predeterminado: 60).",
    "MiniToo image encoding: lossless rgb/Zstandard (default) or jpeg. TimeBox Mini always uses RGB444.": "Formato de MiniToo: rgb/Zstandard sin pérdida (predeterminado) o jpeg. TimeBox Mini siempre usa RGB444.",
    "MiniToo theme: {themes}. Defaults to the saved choice, initially neon. TimeBox Mini uses its compact layout.": "Tema de MiniToo: {themes}. Usa la elección guardada; inicialmente neon. TimeBox Mini usa su diseño compacto.",
    "Saved color or chosen palette. First use: cyan for TimeBox Mini, purple for MiniToo portraits.": "Color guardado o paleta elegida. Primer uso: cyan en TimeBox Mini, purple en los retratos de MiniToo.",
    "Refresh the display once and exit.": "Actualiza la pantalla una vez y termina.",
    "Keep Bluetooth updates running while any app uses the microphone.": "Mantén activos los envíos Bluetooth mientras cualquier aplicación use el micrófono.",
    "Save a preview image without using Bluetooth.": "Guarda una vista previa sin usar Bluetooth.",
    "Start without the selection menus, using explicit options or saved choices.": "Inicia sin los menús de selección, usando parámetros explícitos o preferencias guardadas.",
    "Transfer output: compact updates one terminal row (default); detailed prints every sent update.": "Salida de envíos: compact actualiza una sola línea (predeterminado); detailed imprime cada envío.",
    "Diagnostic log path (default: ~/Library/Logs/divoom-minitoo-codex/<device>-<port>.log; private, rotates at 1 MiB).": "Ruta del log de diagnóstico (predeterminado: ~/Library/Logs/divoom-minitoo-codex/<device>-<port>.log; privado, rota a 1 MiB).",
    "show this help message and exit": "muestra esta ayuda y termina",
    "Finding paired Divoom speakers…": "Buscando bocinas Divoom emparejadas…",
    "connected": "conectada", "paired, not connected": "emparejada, sin conexión",
    "Divoom · speaker": "Divoom · bocina", "Divoom · model": "Divoom · modelo",
    "Detected {name} ({state}).": "Detectada {name} ({state}).",
    "Several Divoom speakers are paired. Run ./start interactively to choose, or specify --device / --address.": "Hay varias bocinas Divoom emparejadas. Ejecuta ./start de forma interactiva para elegir, o indica --device / --address.",
    "No supported paired Divoom speaker found{model}. Turn it on, enable Bluetooth and pair it in macOS Bluetooth settings.": "No se encontró una bocina Divoom compatible emparejada{model}. Enciéndela, activa Bluetooth y empareja la bocina en los ajustes Bluetooth de macOS.",
    " for {device}": " para {device}",
    " You can also provide --address and --device.": " También puedes indicar --address y --device.",
    "Connection · next step": "Conexión · siguiente paso",
    "Refresh paired speakers": "Volver a buscar bocinas emparejadas",
    "Enter a Bluetooth address": "Escribir una dirección Bluetooth",
    "Bluetooth address": "Dirección Bluetooth",
    "Could not read saved display choices; using defaults. {detail}": "No se pudieron leer las preferencias; se usarán las predeterminadas. {detail}",
    "Could not read saved language. {detail}": "No se pudo leer el idioma guardado. {detail}",
    "Could not save language; this monitor will still run. {detail}": "No se pudo guardar el idioma; el monitor continuará. {detail}",
    "TimeBox Mini supports only its compact default theme; ignoring --theme {theme}.": "TimeBox Mini solo admite su tema compacto predeterminado; se omitirá --theme {theme}.",
    "MiniToo · theme": "MiniToo · tema", "{name} · color": "{name} · color",
    "the default {color} palette": "la paleta predeterminada {color}", "its default colors": "la paleta predeterminada",
    "The {theme} theme does not support --color {color}; using {fallback}.": "El tema {theme} no admite --color {color}; se usará {fallback}.",
    "The {theme} theme uses its own fixed palette.": "El tema {theme} usa su propia paleta fija.",
    "Could not save display choices; this monitor will still run. {detail}": "No se pudieron guardar las preferencias; el monitor continuará. {detail}",
    "Neon dashboard (current design)": "Panel neón",
    "Pixel art adventure": "Aventura pixel art",
    "Anime portrait with eyelid blink": "Retrato anime con parpadeo",
    "Adult pixel art anime portrait with eyelid blink": "Anime adulto pixel art con parpadeo",
    "Chibi pixel art anime portrait with eyelid blink": "Anime chibi pixel art con parpadeo",
    "Detailed adult pixel art portrait with eyelid blink": "Anime adulto detallado con parpadeo",
    "purple": "morado", "red": "rojo", "blue": "azul", "green": "verde", "cyan": "cian",
    "default": "predeterminado", "compact": "compacto", "detailed": "detallado",
    "The minimum refresh interval is 10 seconds.": "El intervalo mínimo de actualización es de 10 segundos.",
    "The local bridge port must be between 1 and 65535.": "El puerto del puente local debe estar entre 1 y 65535.",
    "Diagnostic log: {path}": "Log de diagnóstico: {path}",
    "Connecting to Codex and reading account usage…": "Conectando con Codex y consultando el uso de la cuenta…",
    "MiniToo encoding: lossless RGB888/Zstandard at 160x128.": "Formato de MiniToo: RGB888/Zstandard sin pérdida a 160x128.",
    "Monitoring {device} at {address}; reading Codex usage every {interval}s.": "Monitorizando {device} en {address}; consultando el uso de Codex cada {interval}s.",
    "Usage received. Connecting to the authenticated Bluetooth bridge…": "Uso recibido. Conectando con el puente Bluetooth autenticado…",
    "Usage received. Preparing the display monitor…": "Uso recibido. Preparando el monitor de pantalla…",
    "Automatic microphone pause is enabled; Bluetooth updates pause while any app uses the microphone.": "La pausa automática por micrófono está activa: los envíos Bluetooth se detienen mientras cualquier aplicación use el micrófono.",
    "Automatic microphone pause is unavailable: {detail} Continuing without automatic pause.": "La pausa automática por micrófono no está disponible: {detail} Se continuará sin pausa automática.",
    "Automatic microphone pause is disabled.": "La pausa automática por micrófono está desactivada.",
    "Updates paused: microphone input is active.": "Actualizaciones pausadas: hay una aplicación usando el micrófono.",
    "Updates paused: MiniToo is settling; reconnecting in {seconds}s.": "Actualizaciones pausadas: MiniToo se está estabilizando; se reconectará en {seconds}s.",
    "Updates resumed; refreshing the display.": "Actualizaciones reanudadas; se actualizará la pantalla.",
    "Updates paused: the Divoom is not responding; retrying in {seconds}s.": "Actualizaciones pausadas: la Divoom no responde; se reintentará en {seconds}s.",
    "Preview saved to {path}": "Vista previa guardada en {path}",
    "{detail} Retrying the current screen in {seconds}s.": "{detail} Se reintentará la pantalla actual en {seconds}s.",
    "working": "trabajando", "idle": "en reposo", "hooks not installed": "hooks no instalados",
    "Display updated": "Pantalla actualizada", "Display updated after reconnect": "Pantalla actualizada tras reconectar",
    "reset credits": "reinicios disponibles", "working animation": "animación de trabajo",
    "remaining percentage": "porcentaje restante", "usage": "uso",
    "{label} {percent}% left": "{label} {percent}% restante",
    "{usage} left": "{usage} restante", "usage unavailable": "uso no disponible",
    "{message}, reconnected": "{message}, reconectado",
    "{update}: {usage}; Codex {activity}; showing {view} ({transfer}).": "{update}: {usage}; Codex {activity}; mostrando {view} ({transfer}).",
    "sent": "enviado", "image sent": "imagen enviada", "sent; no final acknowledgement observed": "enviado; sin confirmación final",
    "no final acknowledgement": "sin confirmación final",
    "Selection input closed. Use --no-prompt to start with saved choices.": "Se cerró la entrada de selección. Usa --no-prompt para iniciar con las preferencias guardadas.",
    "Selection input closed.": "Se cerró la entrada de selección.", "Monitor stopped.": "Monitor detenido.",
    "  ↑ ↓ move · Enter select · 1–9 jump · Esc/Q cancel": "  ↑ ↓ mover · Enter elegir · 1–9 saltar · Esc/Q cancelar",
    "  Number or name [{selected}] (Enter keeps {default}): ": "  Número o nombre [{selected}] (Enter conserva {default}): ",
    "  Choose one of the listed numbers or names.": "  Elige uno de los números o nombres de la lista.",
    "     Your usage, a little closer.": "     Tu uso, un poco más cerca.",
    "  Device   {device}": "  Bocina   {device}", "  Theme    {theme}  ·  {color}": "  Tema     {theme}  ·  {color}",
    "  Format   {encoding}": "  Formato  {encoding}",
    "  Account  {profile}": "  Cuenta   {profile}",
    "  Refresh  {interval}s  ·  activity hooks checked each second": "  Consulta {interval}s  ·  actividad cada segundo",
    "  Output   {output}  ·  Ctrl+C to stop": "  Salida   {output}  ·  Ctrl+C para detener",
    "  Log: {path}\n": "  Log: {path}\n",
    "Use a Bluetooth MAC address such as AA:BB:CC:DD:EE:FF.": "Usa una dirección MAC Bluetooth como AA:BB:CC:DD:EE:FF.",
    "Automatic Bluetooth detection requires macOS.": "La detección automática Bluetooth requiere macOS.",
    "Bluetooth detection helper is missing. Run ./install once, or provide --address.": "Falta el detector Bluetooth. Ejecuta ./install una vez, o indica --address.",
    "Could not read paired Bluetooth devices: {detail}": "No se pudieron leer las bocinas Bluetooth emparejadas: {detail}",
    "Bluetooth detection failed. Check macOS Bluetooth permission and pairing.": "Falló la detección Bluetooth. Revisa el permiso Bluetooth de macOS y el emparejamiento.",
    "Bluetooth detection returned an invalid device inventory.": "La detección Bluetooth devolvió una lista de dispositivos no válida.",
}

# Short, uppercase labels preserve the native dashboard layout and bitmap font.
_DISPLAY_ES = {
    "USAGE": "USO", "LEFT": "LIBRE", "RESET": "RECARGA",
    "WORKING": "ACTIVO", "WORK": "ACTIVO", "IDLE": "REPOSO", "SETUP": "CONFIG",
    "THINKING": "PENSANDO", "ON STANDBY": "EN ESPERA", "INSTALL HOOKS": "ACTIVA HOOKS",
    "NO USAGE DATA": "SIN DATOS DE USO", "NO USAGE": "SIN DATOS", "DATA": "DE USO",
    "CODEX USAGE": "USO CODEX", "CODEX LIVE": "CODEX VIVO", "USAGE ARCADE": "USO ARCADE",
    "RESET CREDITS": "REINICIOS", "RESET VAULT": "REINICIOS", "RESET BANK": "REINICIOS",
    "AVAILABLE": "DISPONIBLES", "RESETS": "REINICIOS", "DATE / DAYS": "FECHA / DIAS",
    "DATE / DAYS LEFT": "FECHA / DIAS REST.", "EXPIRY / DAYS LEFT": "VENCE / DIAS REST.",
    "DATE N/A": "SIN FECHA", "NO EXPIRY": "NO VENCE", "EXPIRY DATE N/A": "SIN FECHA",
    "+{count} MORE": "+{count} MAS", "AVAILABLE {count}": "DISPONIBLES {count}",
}


def tr(text: str, language: str = "en", **values: object) -> str:
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    template = _SPANISH.get(text, text) if language == "es" else text
    return template.format(**values) if values else template


def display_text(text: str, language: str = "en", **values: object) -> str:
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    template = _DISPLAY_ES.get(text, text) if language == "es" else text
    return template.format(**values) if values else template


# Translate the monitor's actionable errors; preserve native logs, OS errors,
# protocol names and received bytes verbatim for troubleshooting.
_ERROR_FRAGMENTS = {
    "Bluetooth bridge not found at {path}. Run ./install first.": "No se encontró el puente Bluetooth en {path}. Ejecuta ./install primero.",
    "Could not start the {device} bridge: ": "No se pudo iniciar el puente de {device}: ",
    "{device} bridge stopped while connecting. Check the Bluetooth address, pairing, and macOS Bluetooth permission.": "El puente de {device} se detuvo al conectar. Revisa la dirección Bluetooth, el emparejamiento y el permiso Bluetooth de macOS.",
    "{device} bridge stopped while connecting.": "Se detuvo el puente de {device} al conectar.",
    " Stop the monitor with Ctrl+C, then restart it with ./start. If the same channel error returns, close the Divoom app and any other Divoom monitor, turn the TimeBox Mini off for 10 seconds, turn it back on, then restart ./start.": " Detén el monitor con Ctrl+C y vuelve a iniciarlo con ./start. Si continúa el mismo error del canal, cierra la app Divoom y cualquier otro monitor Divoom, apaga TimeBox Mini durante 10 segundos, vuelve a encenderlo y reinicia ./start.",
    " A software Bluetooth link reset was attempted. If MiniToo stays on Loading or the channel error repeats, stop the monitor with Ctrl+C, turn MiniToo off for 10 seconds, turn it back on, then run ./start.": " Se intentó restablecer el enlace Bluetooth por software. Si MiniToo sigue en Loading o se repite el error del canal, detén el monitor con Ctrl+C, apaga MiniToo durante 10 segundos, vuelve a encenderlo y ejecuta ./start.",
    "The {device} bridge is outdated and does not authenticate local requests. Rebuild it with ./install, then restart the monitor.": "El puente de {device} está desactualizado y no autentica solicitudes locales. Recompílalo con ./install y reinicia el monitor.",
    "{device} bridge did not start listening on localhost:{port} within 15 seconds.": "El puente de {device} no empezó a escuchar en localhost:{port} en 15 segundos.",
    " Rebuild the authenticated bridges with ./install if upgrading.": " Si estás actualizando, recompila los puentes autenticados con ./install.",
    "The display bridge supports between 1 and 8 image frames.": "El puente admite entre 1 y 8 cuadros de imagen.",
    "Animation speed must be between 0 and 65535 ms.": "La duración de los cuadros debe estar entre 0 y 65535 ms.",
    "Image request exceeds the bridge's 512 KiB limit.": "La imagen supera el límite de 512 KiB del puente.",
    "The local bridge has no authentication credential. Restart the monitor.": "El puente local no tiene credencial de autenticación. Reinicia el monitor.",
    "The MiniToo bridge does not support RGB888/Zstandard. Rebuild it with ./install before sending RGB.": "El puente MiniToo no admite RGB888/Zstandard. Recompílalo con ./install antes de enviar RGB.",
    "The bridge response exceeded 64 KiB.": "La respuesta del puente superó los 64 KiB.",
    "{device} connection failed while ": "Falló la conexión de {device} al ",
    "connecting to the local bridge": "conectar con el puente local",
    "sending the image request": "enviar la imagen",
    "waiting for the Bluetooth transfer response": "esperar la respuesta del envío Bluetooth",
    "{device} bridge returned an invalid response type.": "El puente de {device} devolvió un tipo de respuesta no válido.",
    "{device} bridge returned an invalid response.": "El puente de {device} devolvió una respuesta no válida.",
    " The bridge sent no data.": " El puente no envió datos.",
    "{device} did not accept the image.": "{device} no aceptó la imagen.",
    "{device} transfer was not confirmed: ": "El envío a {device} no fue confirmado: ",
    "{device} transfer failed after one reconnect.": "Falló el envío a {device} tras un intento de reconexión.",
    " Initial attempt: ": " Intento inicial: ", " Reconnect attempt: ": " Intento de reconexión: ",
    "Could not start Codex App Server using {executable}. Install the Codex CLI or set CODEX_BIN to its path.": "No se pudo iniciar Codex App Server con {executable}. Instala Codex CLI o establece CODEX_BIN con su ruta.",
    "Codex returned an unexpected rate-limit response.": "Codex devolvió una respuesta de límites inesperada.",
    "Codex App Server did not return usage windows. Confirm you are signed in with a ChatGPT account that includes Codex.": "Codex App Server no devolvió cuotas de uso. Confirma que iniciaste sesión con una cuenta ChatGPT que incluye Codex.",
    "Codex App Server returned an invalid initialize response.": "Codex App Server devolvió una respuesta de inicio no válida.",
    "Codex App Server returned an invalid usage response.": "Codex App Server devolvió una respuesta de uso no válida.",
    "Codex App Server returned an invalid account response.": "Codex App Server devolvió una respuesta de cuenta no válida.",
    "Codex App Server sent a response without a result.": "Codex App Server envió una respuesta sin resultado.",
    "Timed out waiting for Codex App Server method {method}.": "Se agotó el tiempo de espera del método {method} de Codex App Server.",
    "Codex App Server is not running. Run this from a normal macOS session where Codex can access its local state.": "Codex App Server no está en ejecución. Inicia el monitor desde una sesión normal de macOS con acceso al estado local de Codex.",
    "Could not send a request to Codex App Server.": "No se pudo enviar una solicitud a Codex App Server.",
    "Codex App Server stdout closed unexpectedly.": "La salida de Codex App Server se cerró inesperadamente.",
    "Codex App Server exited before replying": "Codex App Server terminó antes de responder",
}


def translate_error(message: str, language: str) -> str:
    if language != "es":
        return message
    # Split off diagnostics before translating so Bluetooth logs stay exact.
    fragments = re.split(r"( Details: .*?(?= Reconnect attempt: |$))", message)
    for index in range(0, len(fragments), 2):
        part = fragments[index]
        for source, target in _ERROR_FRAGMENTS.items():
            names = re.findall(r"\{(\w+)\}", source)
            pattern = re.escape(source)
            for name in names:
                capture = r"MiniToo|TimeBox Mini" if name == "device" else r".+?"
                pattern = pattern.replace(re.escape("{" + name + "}"), f"(?P<{name}>{capture})")
            part = re.sub(pattern, lambda match, target=target: target.format(**match.groupdict()), part)
        part = tr(part, language)
        part = part.replace("sent; no final acknowledgement observed", tr("sent; no final acknowledgement observed", language))
        fragments[index] = part
    for index in range(1, len(fragments), 2):
        fragments[index] = fragments[index].replace(" Details: ", " Detalles técnicos: ", 1)
    return "".join(fragments)
