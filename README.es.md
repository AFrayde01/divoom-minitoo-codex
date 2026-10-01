# Uso de Codex en pantallas Divoom

[English](README.md) | [Español](README.es.md)

Muestra el uso de Codex, los horarios de recarga, la actividad y los créditos de reset disponibles en una Divoom MiniToo o TimeBox Mini. El monitor consulta la cuenta iniciada mediante Codex App Server local. MiniToo recibe un panel de 160 × 128 píxeles; TimeBox Mini muestra una pantalla compacta para su matriz LED de 11 × 11.

Esta versión funciona en **macOS**. MiniToo incluye cinco temas: **neón**, **pixel art**, **anime**, **anime-pixel** (adulto) y **anime-pixel-chibi**. TimeBox Mini usa un diseño compacto para su matriz de 11 × 11, con varios colores de acento opcionales. [Ver los temas](#temas-y-colores).

## Requisitos

- Una Divoom MiniToo o TimeBox Mini enlazada con tu Mac
- macOS con Bluetooth activado
- Python 3.10 o posterior
- Xcode Command Line Tools (`swiftc`); si hace falta, instálalos con `xcode-select --install`
- [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) instalado e iniciado con una cuenta ChatGPT que tenga límites de uso de Codex

El monitor se ejecuta en Terminal, que debe permanecer abierta para mantener la pantalla actualizada. No instala un servicio en segundo plano.

## Instalación

Clona este repositorio desde Terminal y ejecuta:

```sh
git clone https://github.com/AFrayde01/divoom-minitoo-codex.git
cd divoom-minitoo-codex
./scripts/install.sh
```

El instalador crea un entorno virtual de Python, compila los puentes Bluetooth para ambos modelos Divoom e instala los hooks de actividad de Codex. Instala los hooks en `CODEX_HOME` (o `~/.codex`) y en cada perfil de Codex App que encuentre en `~/Library/Application Support/Parall/ChatGPT*/.codex`. Todos los perfiles comparten el mismo archivo local de actividad.

Codex requiere que revises y autorices los hooks que no administra antes de ejecutarlos. En cada perfil que uses, inicia una sesión de Codex CLI con su `CODEX_HOME`, ejecuta `/hooks`, revisa y autoriza los hooks de Divoom y luego reinicia ese perfil. Para un perfil separado, inicia CLI así: `CODEX_HOME="/ruta/al/perfil/.codex" codex`. Antes de modificar un `hooks.json` existente, el instalador guarda una copia y conserva los demás hooks. Consulta la [guía de hooks de Codex](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks).

Si después agregas otro perfil de Codex, instala sus hooks con:

```sh
.venv/bin/python scripts/install_activity_hooks.py install \
  --codex-home "/ruta/al/perfil/.codex"
```

## Actualizar una instalación existente

Detén el monitor con `Ctrl+C`, actualiza tu copia del repositorio y ejecuta `./scripts/install.sh` de nuevo. Hay que recompilar **ambos puentes** para usar la autenticación local; un binario antiguo se rechazará con un mensaje de actualización. Reinicia el monitor después. Los hooks existentes conservan su configuración; revisa `/hooks` si Codex solicita confiar en un hook actualizado.

## Cómo encontrar la dirección Bluetooth de Divoom

1. Enciende el dispositivo Divoom y enlázalo desde **Configuración del Sistema → Bluetooth**.
2. Abre **Información del Sistema → Hardware → Bluetooth**, busca MiniToo o TimeBox Mini en la lista y copia su **Address**. También puedes consultar la lista desde Terminal:

   ```sh
   system_profiler SPBluetoothDataType
   ```

3. Usa la dirección Bluetooth del dispositivo Divoom, con un formato como `AA:BB:CC:DD:EE:FF`. No es la dirección Bluetooth ni la dirección IP de tu Mac.

Si MiniToo está conectado como dispositivo de audio Bluetooth, desconecta ese perfil de audio antes de iniciar el monitor. Para TimeBox Mini, cierra la aplicación Divoom si mantiene una conexión activa.

## Iniciar el monitor

Inicia el monitor continuo con:

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo
```

Si omites `--device`, el monitor usa **MiniToo** con el tema **neón**. Para usar TimeBox Mini, agrega `--device timebox-mini`; usará su diseño compacto predeterminado:

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo --device timebox-mini
```

Deja Terminal abierta mientras se ejecuta; puedes detener el monitor con `Ctrl+C`. Lee el uso al iniciarse y cada 60 segundos, revisa la actividad cada segundo y vuelve a leer el uso cuando termina un turno de Codex. Envía una imagen cuando cambia la pantalla. Los hooks no responden en la conversación de Codex; su estado aparece en la pantalla Divoom.

## Temas y colores

Estas vistas previas se generan con los mismos renderizadores que usan ambos dispositivos. Los porcentajes y los conteos de resets son ejemplos. MiniToo es el dispositivo predeterminado; agrega `--device timebox-mini` para mostrar las animaciones de TimeBox Mini.

| Neón (predeterminado) | Pixel art |
| --- | --- |
| ![Tema de uso neón](docs/images/neon.png) | ![Tema de uso pixel art](docs/images/pixel-art.png) |
| `--theme neon` | `--theme pixel-art` |

El tema **anime** tiene cuatro variantes de color. El morado es el predeterminado:

| Morado | Rojo |
| --- | --- |
| ![Tema anime morado](docs/images/anime-purple.png) | ![Tema anime rojo](docs/images/anime-red.png) |
| `--theme anime --color purple` | `--theme anime --color red` |

| Azul | Verde |
| --- | --- |
| ![Tema anime azul](docs/images/anime-blue.png) | ![Tema anime verde](docs/images/anime-green.png) |
| `--theme anime --color blue` | `--theme anime --color green` |

Por ejemplo, inicia la variante verde así:

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo \
  --theme anime --color green
```

También puedes usar `-color` como alias de `--color`. En MiniToo, neón y pixel art tienen una sola paleta cada uno; si les asignas un color, el monitor avisa y usa los colores predeterminados del tema. Ambos temas anime parpadean alternando imágenes completas de la pantalla y animan el indicador WORKING. Pixel art anima el robot y el fondo; neón anima su indicador de actividad.

El retrato anime se creó para este proyecto a partir de una descripción escrita del personaje, sin imágenes externas de referencia. Sus archivos fuente, instrucciones de generación y exportación al tamaño de pantalla se documentan en [Procedencia de las ilustraciones](docs/ARTWORK.md).

![Animación del indicador de actividad y parpadeo anime](docs/images/anime-demo.gif)

### Anime pixel art

Selecciona **anime-pixel** para el nuevo personaje adulto, diseñado como una mujer de unos 24 años, con ojos más proporcionados y rostro menos redondo. Se creó de forma independiente a partir de texto, directamente para pixel art, y después se simplificó con mechones amplios, menos reflejos, iris sencillos y bloques de color conectados para la pantalla pequeña. Conserva la interfaz del anime: cuota restante, tiempo hasta el refill, fechas RESET, banco de resets y actividad, con texto de píxeles y marcos cuadrados. Sus imágenes de 78 × 78 usan 16 colores compartidos sin tramado. La piel, las mejillas y el fondo no cambian durante el parpadeo. El tema global predeterminado sigue siendo `neon`.

![Animación del indicador de actividad y parpadeo de anime pixel art](docs/images/anime-pixel-demo.gif)

Soporta los mismos cuatro colores; el morado es el predeterminado:

| Morado | Rojo |
| --- | --- |
| ![Anime pixel art morado](docs/images/anime-pixel-purple.png) | ![Anime pixel art rojo](docs/images/anime-pixel-red.png) |
| `--theme anime-pixel --color purple` | `--theme anime-pixel --color red` |

| Azul | Verde |
| --- | --- |
| ![Anime pixel art azul](docs/images/anime-pixel-blue.png) | ![Anime pixel art verde](docs/images/anime-pixel-green.png) |
| `--theme anime-pixel --color blue` | `--theme anime-pixel --color green` |

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo \
  --theme anime-pixel --color green
```

| Una sola ventana de cuota | Banco de resets |
| --- | --- |
| ![Anime pixel art verde con una barra vertical de cuota y parpadeo](docs/images/anime-pixel-green-pro-demo.gif) | ![Pantalla de créditos de reset de anime pixel art](docs/images/anime-pixel-resets.png) |

El personaje pixel art actual comenzó con una generación solo a partir de texto, seguida de ajustes sobre sus propias imágenes generadas. Las imágenes de ojos abiertos y cerrados se exportan a 78 × 78 con una paleta compartida y se guardan como archivos RGB para el dispositivo. Los archivos fuente, los prompts y la exportación se documentan en [Procedencia del pixel art](docs/ANIME_PIXEL_ARTWORK.md).

### Anime pixel art chibi

El personaje pixel anterior se conserva como **anime-pixel-chibi**, con rostro compacto y ojos grandes. Comparte la interfaz, el parpadeo y los colores `purple`, `red`, `blue` y `green` de la versión adulta.

![Parpadeo e indicador de actividad del tema chibi](docs/images/anime-pixel-chibi-demo.gif)

| Morado | Rojo |
| --- | --- |
| ![Chibi morado](docs/images/anime-pixel-chibi-purple.png) | ![Chibi rojo](docs/images/anime-pixel-chibi-red.png) |
| `--theme anime-pixel-chibi --color purple` | `--theme anime-pixel-chibi --color red` |

| Azul | Verde |
| --- | --- |
| ![Chibi azul](docs/images/anime-pixel-chibi-blue.png) | ![Chibi verde](docs/images/anime-pixel-chibi-green.png) |
| `--theme anime-pixel-chibi --color blue` | `--theme anime-pixel-chibi --color green` |

### Pantalla 11 × 11 de TimeBox Mini

Cuando Codex está inactivo, TimeBox Mini alterna entre barras de cuota gruesas y el porcentaje restante de la ventana cuyo siguiente refill ocurrirá primero. Si hay dos ventanas, la más corta aparece arriba. Si solo hay una ventana 7D, se muestra una barra vertical centrada. Mientras Codex trabaja, una animación de pulsos ocupa toda la matriz; cada diez segundos se detiene durante dos segundos para mostrar el porcentaje restante.

La vista previa animada muestra la animación de trabajo, las barras de cuota, el porcentaje restante y la cantidad de resets. El GIF comprime la espera. En el dispositivo, la animación de trabajo se muestra ocho segundos y el porcentaje aparece dos segundos. En estado inactivo, las barras y el porcentaje se alternan cada diez segundos. Si hay créditos disponibles, la cantidad de resets aparece ocho segundos cada cinco minutos y ocupa temporalmente la pantalla.

![Vista previa animada de TimeBox Mini con barras 5H y 7D, porcentaje restante y cantidad de resets](docs/images/timebox-mini-demo.gif)

Si la cuenta solo tiene una ventana 7D, esta vista previa muestra la barra vertical centrada y los demás estados de la pantalla:

![Vista previa animada de TimeBox Mini con una sola cuota 7D](docs/images/timebox-mini-7d-demo.gif)

El color de acento predeterminado es cian. Con `--color` puedes elegir **morado**, **rojo**, **azul** o **verde**. La pantalla de resets usa ese color y muestra la cantidad con números grandes.

Por ejemplo, selecciona el verde así:

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo \
  --device timebox-mini --color green
```

## Cómo leer la pantalla

### MiniToo

- **5H** y **7D** identifican las ventanas de uso que Codex devuelve para la cuenta. Algunos planes solo tienen una ventana.
- El porcentaje grande y la barra principal muestran el **uso restante**. Empiezan en 100 % y disminuyen a medida que usas Codex.
- La barra vertical delgada junto a cada ventana muestra **el tiempo que falta para el próximo refill**. Disminuye conforme se acerca.
- **RESET** muestra la hora local estimada de recarga para una ventana corta o la fecha local para una ventana más larga.
- **WORK/WORKING** indica que un hook instalado detectó un turno de Codex activo. **IDLE** indica que no hay turnos activos. **SETUP** significa que todavía no se detectaron hooks de actividad. Si solo hay una ventana de uso, ambos temas anime muestran un medidor vertical más alto junto al retrato.

Por ejemplo, así se ve el tema anime con una sola ventana de uso Pro:

![Tema anime con una sola ventana de uso Pro vertical](docs/images/anime-single-window.png)

### TimeBox Mini

La pantalla de barras muestra la cuota restante. Si hay dos ventanas, la más corta es la barra superior y la más larga es la inferior. Si solo hay una ventana 7D, aparece una sola barra vertical centrada. La siguiente pantalla muestra únicamente el porcentaje restante (por ejemplo, **62 %**) de la ventana cuyo refill está más próximo. Durante WORKING, la animación pulsante llena la matriz durante ocho segundos y después muestra el porcentaje restante durante dos segundos; el ciclo se repite hasta que termina el turno.

### Pantalla de créditos de reset

Si tu cuenta tiene créditos de reset de límites disponibles, aparece una pantalla aparte **cada cinco minutos durante ocho segundos**. MiniToo muestra la cantidad disponible y hasta tres fechas de expiración con los días restantes. TimeBox Mini muestra solo la cantidad con números más grandes. Si Codex solo devuelve la cantidad, MiniToo la muestra sin fechas. Si no hay créditos disponibles, se omite esta pantalla. MiniToo usa el tema seleccionado; TimeBox Mini usa el color de acento elegido.

Ejemplos de la pantalla de resets de MiniToo:

| Neón | Pixel art | Anime |
| --- | --- | --- |
| ![Pantalla de resets neón](docs/images/neon-resets.png) | ![Pantalla de resets pixel art](docs/images/pixel-art-resets.png) | ![Pantalla de resets anime](docs/images/anime-resets.png) |

Las ventanas de uso y los datos de resets se obtienen mediante el método [`account/rateLimits/read`](https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt) de Codex App Server. Este proyecto solo muestra los créditos de reset; no los canjea.

También puedes pasar la dirección como una opción:

```sh
.venv/bin/codex-minitoo --address "AA:BB:CC:DD:EE:FF"
```

## Elegir el perfil de cuenta de Codex

Las barras de uso corresponden a la cuenta ChatGPT iniciada en el perfil de Codex seleccionado. Si usas perfiles separados para una cuenta principal y otra Personal, selecciona uno con `--codex-home`:

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo \
  --codex-home "$HOME/Library/Application Support/Parall/ChatGPT (Personal)/.codex"
```

Sustituye la ruta por el directorio del perfil que uses. También puedes establecer `CODEX_HOME` en el entorno. Si no indicas ninguno, se usa el perfil predeterminado de CLI. El monitor muestra el uso de una cuenta a la vez; reinícialo después de cambiar el perfil seleccionado. La actividad aún puede reflejar turnos de cualquier perfil instalado y autorizado, porque todos sus hooks comparten el archivo local de actividad. Las sesiones que solo usan una clave API o Bedrock no proporcionan las ventanas de uso de ChatGPT que necesita esta pantalla.

## Opciones

Guarda una vista previa sin conectarte a un dispositivo Divoom ni indicar una dirección. Como usa datos de uso actuales, también necesitas un perfil de Codex con sesión iniciada:

```sh
.venv/bin/codex-minitoo --theme anime --color blue --preview preview.png
```

Para obtener una vista previa del diseño compacto de TimeBox Mini en azul:

```sh
.venv/bin/codex-minitoo --device timebox-mini --color blue --preview timebox-mini-preview.png
```

Envía una actualización y termina:

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo --once
```

Actualiza el uso cada 90 segundos (el mínimo es 10 segundos):

```sh
MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo --interval 90
```

| Opción | Propósito |
| --- | --- |
| `--address ADDRESS` | Dirección MAC Bluetooth de Divoom; también acepta `MINITOO_ADDRESS` |
| `--device DEVICE` | `minitoo` (predeterminado) o `timebox-mini` |
| `--theme neon`, `--theme pixel-art`, `--theme anime`, `--theme anime-pixel`, `--theme anime-pixel-chibi` | Tema MiniToo; el predeterminado es `neon`. TimeBox Mini siempre usa su diseño compacto. |
| `--color`, `-color` | Acento TimeBox Mini: `cyan` (predeterminado), `purple`, `red`, `blue` o `green`; paleta de los temas anime, anime-pixel y anime-pixel-chibi de MiniToo: `purple` (predeterminado), `red`, `blue` o `green` |
| `--codex-home PATH` | Perfil de Codex para consultar el uso; también acepta `CODEX_HOME` |
| `--codex-bin PATH` | Ejecutable de Codex CLI; también acepta `CODEX_BIN` |
| `--interval SECONDS` | Intervalo entre consultas de uso; predeterminado: `60`, mínimo: `10` |
| `--preview FILE` | Guarda un PNG sin usar Bluetooth |
| `--once` | Envía una actualización y termina |
| `--log-file FILE` | Archivo de diagnóstico; predeterminado: `~/Library/Logs/divoom-minitoo-codex/<device>-<port>.log`. Privado (`0600`); rota a 1 MiB y conserva dos respaldos. |

Si `codex` no está en el `PATH` de Terminal, establece `CODEX_BIN` con la ruta al ejecutable de CLI:

```sh
CODEX_BIN="/ruta/a/codex" MINITOO_ADDRESS="AA:BB:CC:DD:EE:FF" .venv/bin/codex-minitoo
```

## Soporte de animaciones

Los temas MiniToo envían imágenes JPEG completas para sus animaciones. TimeBox Mini usa su propio protocolo Bluetooth RGB444 para una matriz de 11 × 11 y envía una nueva imagen de la matriz cada segundo durante la animación WORKING de pantalla completa. No carga un GIF. Cuando está inactivo, alterna entre las barras de cuota y el porcentaje restante para la recarga más próxima. MiniToo usa el canal Bluetooth RFCOMM 1; TimeBox Mini usa el canal 4. Sus puentes locales usan los puertos `40584` y `40585`, respectivamente, así que ambos monitores pueden ejecutarse a la vez. El protocolo de imagen de TimeBox Mini sigue la [documentación de la comunidad](https://github.com/MarcG046/timebox/blob/master/doc/protocol.md), no una API pública de Divoom.

## Solución de problemas

- **No aparecen las barras de uso:** Inicia sesión en un perfil de ChatGPT con uso de Codex. Si utilizas otro perfil, pasa su ruta con `--codex-home`.
- **El puente no devuelve datos o la respuesta no es válida:** Ejecuta otra vez `./scripts/install.sh` para recompilar los puentes, confirma que el dispositivo esté enlazado y revisa su dirección MAC. Para TimeBox Mini, cierra la aplicación Divoom al conectar.
- **Se perdió la conexión, se detuvo el puente o no se confirmó una transferencia:** El monitor cierra el puente fallido e intenta una vez con una sesión Bluetooth nueva. Si ambos intentos fallan, el monitor continuo sigue ejecutándose e intenta de nuevo con pausas de 5, 10, 20, 40 y hasta 60 segundos. No marca como completada una transferencia fallida. `--once` termina con un error si los dos intentos fallan. Los mensajes muestran la etapa de conexión, el código de salida del puente cuando está disponible y sus logs recientes.
- **MiniToo se queda en la pantalla de carga:** El puente procesa pedidos de bloques durante la transferencia, valida las sumas de comprobación de los paquetes y reconoce la [confirmación final capturada](https://github.com/alvinunreal/divoom-minitoo-osx/blob/main/PROTOCOL.md#final-ack) en vez de tomar cualquier respuesta como confirmación. Exige que MiniToo solicite los datos en los primeros 5 segundos; si no responde, no envía imágenes y reconecta. Espera hasta 10 segundos por un bloque solicitado, limita la transferencia Bluetooth a 40 segundos y espera hasta 60 segundos la respuesta local. La recuperación ocurre en cualquier pantalla. Si el dispositivo ya quedó bloqueado por una transferencia anterior incompleta, detén el monitor, cierra la aplicación Divoom y la conexión de audio Bluetooth de MiniToo, apaga y enciende MiniToo, y reinicia el monitor. Si falta la confirmación, la transferencia no está confirmada; eso no demuestra por sí solo que no se haya actualizado la pantalla.
- **Diagnóstico de un bloqueo recurrente:** Cada monitor guarda logs con fecha y hora, errores y salida del puente, incluidos los bytes de control Bluetooth recibidos. El log predeterminado de MiniToo es `~/Library/Logs/divoom-minitoo-codex/minitoo-40584.log`; TimeBox Mini usa `~/Library/Logs/divoom-minitoo-codex/timebox-mini-40585.log`. La ruta completa se muestra al iniciar. Puedes elegir otra con `--log-file /ruta/al/monitor.log`. Al reportar un bloqueo, incluye la sección del log correspondiente: permite distinguir si el dispositivo no responde o si llegó una respuesta que el puente no reconoce. Los logs pueden incluir direcciones de conexión y porcentajes de uso mostrados; no contienen prompts, tokens de acceso ni imágenes.
- **El puerto local ya está en uso:** Detén el otro monitor del mismo modelo. El monitor espera el aviso de disponibilidad de su propio puente; otro proceso que escucha ese puerto no se considera una conexión correcta. MiniToo y TimeBox Mini pueden funcionar a la vez porque usan distintos puertos predeterminados (`40584` y `40585`).
- **La pantalla no muestra WORK:** Mantén el monitor en ejecución, revisa y autoriza los hooks de Divoom con `/hooks` en el mismo perfil que recibió el prompt y reinicia ese perfil. El hook no responde en la conversación de Codex; actualiza `~/.codex/divoom-minitoo-codex-activity.json` para que lo lea el monitor.
- **macOS deniega el acceso a Bluetooth:** Autoriza Bluetooth para el proceso que ejecuta el puente en Configuración del Sistema de macOS.
- **Aparece un reloj de arena durante una actualización MiniToo:** MiniToo puede mostrar su propia pantalla de transferencia/carga al recibir imágenes modificadas. El monitor evita enviar imágenes idénticas, pero un cambio visible puede activar esa pantalla.

## Comprobaciones de conexión para desarrollo

Ejecuta las simulaciones de fallos con:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Estas comprobaciones cubren errores de socket, disponibilidad y apagado de procesos, respuestas incompletas, intentos de reconexión, reintentos de la misma pantalla con pausa y logs persistentes. En macOS con Swift instalado, también compilan el código real de transferencia MiniToo y lo ejecutan con un canal RFCOMM en memoria para revisar paquetes fragmentados, sumas de comprobación, pedidos de bloques faltantes, acuses finales, desconexiones y el caso de un dispositivo silencioso que no debe recibir una animación enviada a ciegas. No abren conexiones Bluetooth; el comportamiento físico del dispositivo debe comprobarse aparte.

## Desinstalar los hooks

Elimina los hooks de actividad Divoom de CLI y de los perfiles de Codex App detectados con:

```sh
.venv/bin/python scripts/install_activity_hooks.py uninstall --all-profiles
```

Los demás hooks de esos perfiles se conservan. Este comando no elimina el entorno de Python ni el puente Swift.

## Privacidad y mantenimiento de la galería

El monitor no lee ni guarda tokens de acceso. Los hooks de actividad guardan identificadores de sesión y de turno con sus fechas y horas; no guardan prompts, respuestas ni resultados de herramientas. Los datos de uso se consultan localmente mediante Codex App Server y se representan en imágenes para la pantalla.

Después de cambiar un renderizador, regenera las imágenes de ejemplo del README con:

```sh
.venv/bin/python scripts/generate_theme_gallery.py
```


## Licencia y contribuciones

Este proyecto usa la [licencia MIT](LICENSE): permite compartir, modificar y reutilizar el proyecto conservando sus avisos. Incluye el código, la documentación y el arte creado para el proyecto en la medida en que existan derechos aplicables. Las marcas y dependencias mantienen sus propias condiciones; consulta [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

El arte actual y sus descripciones de generación están documentados en [anime](docs/ARTWORK.md) y [pixel adulto/chibi](docs/ANIME_PIXEL_ARTWORK.md). Las imágenes de la galería usan datos de ejemplo. Consulta [CONTRIBUTING.md](CONTRIBUTING.md) y [SECURITY.md](SECURITY.md) para contribuir o reportar una vulnerabilidad.

Los puentes comprueban una credencial nueva por proceso antes de aceptar imágenes. Se entrega por una tubería privada, sin guardarla en argumentos, variables de entorno ni logs. Los logs nuevos y rotados usan permisos `0600`; la carpeta predeterminada usa `0700`. Los logs anteriores del directorio `build/` también se protegen al iniciar con la configuración predeterminada. Revisa direcciones Bluetooth y rutas personales antes de adjuntar un log.

La terminal muestra al iniciar el modelo, tema, color, intervalo y ruta del log. `NO_COLOR=1` desactiva los colores; al redirigir la salida se conservan mensajes simples.


Para la primera publicación con historial limpio, consulta [PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md).
