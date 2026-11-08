# Observatorio Fuerza Élite R3

Sitio privado del Observatorio. Se abre solo con contraseña.

- La página (`index.html`) no trae datos. Al poner la contraseña, descifra en el navegador
  la dirección del tablero y su llave (`config.enc.json`, cifrado con AES-256 y PBKDF2 de 600 000 vueltas).
- Con esa llave pide el tablero a Apps Script, que lee la Google Sheet en vivo.
  Sin la llave, Apps Script responde "Acceso restringido".
- `config.enc.json` lo arma GitHub Actions en cada publicación; no está en el repositorio.
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

## Privacidad

Aquí no van datos, nombres, cédulas ni la contraseña. Solo el código de la página.
