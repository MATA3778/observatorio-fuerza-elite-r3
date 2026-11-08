// Cifra la dirección del tablero y su llave con la contraseña del sitio.
// Lo corre GitHub Actions con los secretos OBS_CLAVE, OBS_URL y OBS_LLAVE.
// Salida: config.enc.json (solo datos cifrados; sin la contraseña no se puede leer).
import { webcrypto as crypto } from 'node:crypto';
import { writeFileSync } from 'node:fs';

const { OBS_CLAVE, OBS_URL, OBS_LLAVE } = process.env;
const salida = process.argv[2] || 'config.enc.json';
const faltan = ['OBS_CLAVE', 'OBS_URL', 'OBS_LLAVE'].filter((k) => !process.env[k]);
if (faltan.length) {
  console.error('Faltan los secretos: ' + faltan.join(', ') + ' (Settings → Secrets and variables → Actions)');
  process.exit(1);
}
if (OBS_CLAVE.length < 12) {
  console.error('La contraseña OBS_CLAVE debe tener al menos 12 caracteres.');
  process.exit(1);
}
if (!/^https:\/\/script\.google\.com\/macros\/s\/[^/]+\/exec$/.test(OBS_URL.trim())) {
  console.error('OBS_URL debe ser la dirección /exec de Apps Script (https://script.google.com/macros/s/…/exec).');
  process.exit(1);
}

const ITER = 600000;
const b64 = (u) => Buffer.from(u).toString('base64');
const sal = crypto.getRandomValues(new Uint8Array(16));
const iv = crypto.getRandomValues(new Uint8Array(12));
const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(OBS_CLAVE), 'PBKDF2', false, ['deriveKey']);
const llave = await crypto.subtle.deriveKey(
  { name: 'PBKDF2', salt: sal, iterations: ITER, hash: 'SHA-256' },
  base, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
const texto = JSON.stringify({ url: OBS_URL.trim(), llave: OBS_LLAVE.trim() });
const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, llave, new TextEncoder().encode(texto));
writeFileSync(salida, JSON.stringify({ v: 1, it: ITER, sal: b64(sal), iv: b64(iv), ct: b64(new Uint8Array(ct)) }));
console.log('Listo: ' + salida);
