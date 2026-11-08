"""Convierte el CSV de Estadísticas Policiales del OIJ en datos/hechos.json.

Uso: python3 scripts/oij.py Estadisticas.csv
Guarda solo homicidios, lesiones y agresiones: [fecha, franja, cantón, tipo]. Nada de datos de personas.
"""
import csv, html, json, sys

T = {'HOMICIDIO': 'Homicidio', 'LESIONES': 'Lesiones', 'AGRESION': 'Agresión'}
NOMBRES = {'La Union': 'La Unión', 'Paraiso': 'Paraíso', 'Jimenez': 'Jiménez'}
filas = list(csv.reader(open(sys.argv[1], encoding='utf-8', errors='replace')))[1:]
out = []
for r in filas:
    # Algunas filas traen comas dentro del subdelito: se lee desde la derecha.
    delito, sub = html.unescape(r[0]), html.unescape(','.join(r[1:-10]))
    if delito != 'DELITOS CONTRA LA VIDA' or sub not in T:
        continue
    h = r[-9].strip()
    franja = h[:5] + '-' + h[11:16] if len(h) >= 16 else h
    canton = r[-2].strip().title()
    out.append([r[-10], franja, NOMBRES.get(canton, canton), T[sub]])
out.sort()
json.dump(out, open('datos/hechos.json', 'w'), ensure_ascii=False)
print(len(out), 'hechos, del', out[0][0], 'al', out[-1][0])
