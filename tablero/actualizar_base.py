"""Refresca la línea BASE (solo cantidades) del tablero con registro_general.json de Cortes-Operativos-R3.
Uso: python3 actualizar_base.py ruta/a/registro_general.json   (reescribe tablero_index.html)"""
import json, re, sys
base = json.load(open(sys.argv[1]))['base_al_7_nov']
linea = 'const BASE = ' + json.dumps(base, ensure_ascii=False) + '; // marca-base'
p = 'tablero_index.html'
s = open(p).read()
s, n = re.subn(r"const BASE = .*?; // marca-base", lambda m: linea, s, count=1, flags=re.S)
assert n == 1, 'no se encontró la marca-base'
open(p, 'w').write(s)
print('BASE actualizada:', len(base), 'categorías')
