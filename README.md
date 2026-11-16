# Observatorio Fuerza Élite R3

Sitio privado del Observatorio. Se abre solo con contraseña.

- La página (`index.html`) no trae datos. Al poner la contraseña, descifra en el navegador
  la dirección del tablero y su llave (`config.enc.json`, cifrado con AES-256 y PBKDF2 de 600 000 vueltas).
- El tablero viaja cifrado dentro del sitio (`tablero.enc.json`, misma contraseña). Se arma en cada publicación
  a partir de `apps-script/Index.html`, así que **un cambio del tablero queda publicado al fusionar en `main`,
  sin pegar nada en Apps Script**.
- Con la llave, el sitio le pide a Apps Script solo los datos (`formato=json`), que salen en vivo de la Google Sheet.
  Sin la llave, Apps Script responde "Acceso restringido".
- Si Apps Script todavía tiene el `Code.gs` anterior (sin `formato=json`), el sitio pide la página completa,
  toma de ahí solo los datos y los muestra con el tablero del sitio. Funciona igual, solo descarga más.
- `config.enc.json` y `tablero.enc.json` los arma GitHub Actions en cada publicación; no están en el repositorio.
- `robots.txt` y la etiqueta `noindex` le piden a los buscadores no indexar el sitio.

## Secretos (Settings → Secrets and variables → Actions)

| Secreto | Qué es |
|---|---|
| `OBS_CLAVE` | La contraseña del sitio (mínimo 12 caracteres; mejor una frase de 4 palabras o más). |
| `OBS_URL` | La dirección `/exec` del Apps Script. |
| `OBS_LLAVE` | La llave que muestra `crearLlave()` en Apps Script. |

## Publicar

Settings → Pages → Source: **GitHub Actions**. Cada cambio en `main` (o "Run workflow" en Actions)
vuelve a publicar.

## Cambiar la contraseña

Editar el secreto `OBS_CLAVE` y correr de nuevo el workflow "Publicar sitio".

## Logos

Subir `assets/logo1.png` y `assets/logo2.png`; aparecen solos en la pantalla de entrada.
`assets/logo-msp.png` es el logo de la franja de arriba (recortado del banner `assets/banner.jpg`).
`assets/fondo.jpg` es la foto de fondo de la entrada (Basílica de los Ángeles).

## Homicidios y heridos (OIJ)

`datos/hechos.json` sale de Estadísticas Policiales del OIJ (datos abiertos): homicidios, lesiones y agresiones en Cartago, solo fecha, franja, cantón y tipo. Para actualizarlo hay dos caminos:

- **Automático:** en una rama nueva, subir el CSV o .xls a `datos/entrada/` (ver `datos/entrada/LEEME.md`). El flujo "Actualizar datos del OIJ" corre `scripts/oij.py`, borra el archivo subido y abre un pull request con `datos/hechos.json`.
- **A mano:** `python3 scripts/oij.py Estadisticas.csv`.

El sitio agrega los datos al tablero al abrirlo.

## Privacidad

Aquí no van datos, nombres, cédulas ni la contraseña. Solo el código de la página.

## Tablero (código fuente)

- `tablero/tablero_index.html` es el tablero. Sus datos de cortes y General no van aquí: Apps Script los lee en vivo de la Google Sheet.
- `apps-script/Index.html` es el tablero que se publica (se arma con `tablero/build_public.py` y `tablero/build_appscript.py`). Ya no hace falta pegarlo en Apps Script: el sitio lo publica cifrado.
- `apps-script/Code.gs` es lo único que vive en Apps Script. Solo se pega si cambia la forma de leer la hoja (poco frecuente). Tras pegarlo: Implementar → Gestionar implementaciones → Nueva versión (misma URL).
- Vista **Resumen y control**: texto del corte para WhatsApp, cortes sin datos de hoy, ayer y anteayer, y cuadre de la General contra `base_al_7_nov` más las hojas diarias desde el 8 nov. La base sale de `registro_general.json` de Cortes-Operativos-R3: `python3 tablero/actualizar_base.py registro_general.json`.
- Caché: Apps Script guarda los datos 15 minutos y un activador los precalienta cada 5 (`instalarPrecalentado()`, se corre una sola vez).

## Rotar la llave o la contraseña

- **Contraseña:** cambiar el secreto `OBS_CLAVE` y correr "Publicar sitio".
- **Llave de Apps Script:** correr `crearLlave()` en el editor, copiar la llave nueva al secreto `OBS_LLAVE` y correr "Publicar sitio". La llave anterior deja de servir al instante.
- **Dirección /exec:** si se crea una implementación nueva, actualizar `OBS_URL`.
