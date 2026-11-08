"""Convierte el CSV de Estadísticas Policiales del OIJ en datos/hechos.json.

Uso: python3 scripts/oij.py Estadisticas.csv [OtroArchivo.csv ...]
Cada archivo reemplaza en datos/hechos.json los cantones que trae (así se puede cargar Cartago y, por
separado, Tarrazú, Dota y León Cortés, que el OIJ cuenta en San José) y vuelve a correr sin duplicar.
Guarda solo homicidios, lesiones y agresiones: [fecha, franja, cantón, tipo]. Nada de datos de personas.
"""
import csv, html, json, sys

T = {'HOMICIDIO': 'Homicidio', 'LESIONES': 'Lesiones', 'AGRESION': 'Agresión'}
NOMBRES = {'La Union': 'La Unión', 'Paraiso': 'Paraíso', 'Jimenez': 'Jiménez', 'Tarrazu': 'Tarrazú', 'Leon Cortes': 'León Cortés'}
import os
RUTA = 'datos/hechos.json'
out = json.load(open(RUTA)) if os.path.exists(RUTA) else []
for archivo in sys.argv[1:]:
    nuevos = []
    for r in list(csv.reader(open(archivo, encoding='utf-8', errors='replace')))[1:]:
        # Algunas filas traen comas dentro del subdelito: se lee desde la derecha.
        delito, sub = html.unescape(r[0]), html.unescape(','.join(r[1:-10]))
        if delito != 'DELITOS CONTRA LA VIDA' or sub not in T:
            continue
        h = r[-9].strip()
        franja = h[:5] + '-' + h[11:16] if len(h) >= 16 else h
        canton = r[-2].strip().title()
        nuevos.append([r[-10], franja, NOMBRES.get(canton, canton), T[sub]])
    cantones = {n[2] for n in nuevos}
    out = [o for o in out if o[2] not in cantones] + nuevos
    print(archivo, ':', len(nuevos), 'hechos de', ', '.join(sorted(cantones)))
out.sort()
json.dump(out, open(RUTA, 'w'), ensure_ascii=False)
print(len(out), 'hechos, del', out[0][0], 'al', out[-1][0])
