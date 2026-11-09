"""Convierte reportes de Estadísticas Policiales del OIJ en datos/hechos.json.

Uso: python3 scripts/oij.py archivo1 [archivo2 ...]   (en ese orden)
Acepta el CSV o el .xls del sitio (que en realidad es una tabla HTML).
Cada fila queda como [fecha, franja, cantón, tipo, distrito, modalidad]. Nada de datos de personas.
Cada archivo reemplaza, para los cantones y tipos que trae, lo que había antes; así se puede volver a correr
sin duplicar, y un reporte más completo (por ejemplo con distrito) reemplaza a uno anterior.
"""
import csv, html, json, os, re, sys, unicodedata

RUTA = 'datos/hechos.json'
VIDA = {'HOMICIDIO': 'Homicidio', 'LESIONES': 'Lesiones', 'AGRESION': 'Agresión'}
DELITO = {'HOMICIDIO': 'Homicidio', 'HURTO': 'Hurto', 'ROBO': 'Robo', 'ASALTO': 'Asalto',
          'ROBO DE VEHICULO': 'Robo de vehículo', 'TACHA DE VEHICULO': 'Tacha de vehículo'}
ACENTOS = {'La Union': 'La Unión', 'Paraiso': 'Paraíso', 'Jimenez': 'Jiménez', 'Tarrazu': 'Tarrazú', 'Leon Cortes': 'León Cortés',
           'San Nicolas': 'San Nicolás', 'Concepcion': 'Concepción', 'Tres Rios': 'Tres Ríos', 'San Rafael': 'San Rafael',
           'Orosi': 'Orosi', 'Cachi': 'Cachí', 'Llanos De Santa Lucia': 'Llanos de Santa Lucía', 'Santa Rosa': 'Santa Rosa',
           'Pejibaye': 'Pejibaye', 'Juan Vinas': 'Juan Viñas', 'Tuis': 'Tuis', 'Tayutic': 'Tayutic', 'Santa Cruz': 'Santa Cruz',
           'Oriental': 'Oriental', 'Occidental': 'Occidental', 'Carmen': 'Carmen', 'Aguacaliente': 'Aguacaliente (San Francisco)',
           'San Francisco': 'San Francisco', 'Guadalupe': 'Guadalupe', 'Corralillo': 'Corralillo', 'Tierra Blanca': 'Tierra Blanca',
           'Dulce Nombre': 'Dulce Nombre', 'Llano Grande': 'Llano Grande', 'Quebradilla': 'Quebradilla', 'El Tejar': 'El Tejar',
           'San Isidro': 'San Isidro', 'Tobosi': 'Tobosí', 'Patio De Agua': 'Patio de Agua', 'San Juan': 'San Juan', 'San Diego': 'San Diego',
           'San Ramon': 'San Ramón', 'Rio Azul': 'Río Azul', 'Santiago': 'Santiago', 'Birrisito': 'Birrisito', 'Cervantes': 'Cervantes',
           'Capellades': 'Capellades', 'Pacayas': 'Pacayas', 'Cot': 'Cot', 'Potrero Cerrado': 'Potrero Cerrado', 'San Pablo': 'San Pablo', 'San Andres': 'San Andrés', 'El Chirripo': 'El Chirripó',
           'San Marcos': 'San Marcos', 'San Lorenzo': 'San Lorenzo', 'Santa Maria': 'Santa María', 'San Pedro': 'San Pedro',
           'San Antonio': 'San Antonio', 'San Carlos': 'San Carlos', 'Copey': 'Copey', 'Jardin': 'Jardín', 'Santa Maria De Dota': 'Santa María',
           'Turrialba': 'Turrialba', 'La Suiza': 'La Suiza', 'Peralta': 'Peralta', 'Santa Teresita': 'Santa Teresita', 'La Isabel': 'La Isabel',
           'Chirripo': 'Chirripó', 'Santa Cruz De Turrialba': 'Santa Cruz', 'Cirri Sur': 'Cirrí Sur', 'La Virgen': 'La Virgen', 'Santa Rosa De Oreamuno': 'Santa Rosa'}
CANTON = {k: v for k, v in ACENTOS.items() if k in ('La Union', 'Paraiso', 'Jimenez', 'Tarrazu', 'Leon Cortes')}


def lee(archivo):
    """Devuelve (encabezado, filas) de un CSV o de un .xls que es una tabla HTML."""
    if archivo.lower().endswith(('.xls', '.html', '.htm')):
        t = open(archivo, encoding='utf-8', errors='replace').read()
        filas = [[html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, flags=re.S)]
                 for r in re.findall(r'<tr>(.*?)</tr>', t, flags=re.S)]
        return filas[0], filas[1:]
    filas = list(csv.reader(open(archivo, encoding='utf-8', errors='replace')))
    return filas[0], filas[1:]


def franja(h):
    h = h.strip()
    return h[:5] + '-' + h[11:16] if len(h) >= 16 else h


def tit(s):
    return ACENTOS.get(s.strip().title(), s.strip().title())


def filas_de(archivo):
    h, filas = lee(archivo)
    xls = 'Distrito' in h and archivo.lower().endswith(('.xls', '.html', '.htm'))
    out = []
    for r in filas:
        if xls:  # tabla con 12 columnas: Delito, SubDelito, Fecha, Hora, ..., Provincia, Canton, Distrito
            delito, sub, fecha, hora, canton, distrito = r[0], r[1], r[2], r[3], r[10], r[11]
            if delito == 'DELITOS CONTRA LA VIDA':
                tipo = VIDA.get(sub); sub = ''
            else:
                tipo = DELITO.get(delito)
        else:    # CSV: columnas corridas, se lee desde la derecha
            delito, sub = html.unescape(r[0]), html.unescape(','.join(r[1:-10]))
            fecha, hora, canton, distrito = r[-10], r[-9], r[-2], ''
            tipo = VIDA.get(sub) if delito == 'DELITOS CONTRA LA VIDA' else None
            sub = ''
        if not tipo:
            continue
        c = canton.strip().title()
        out.append([fecha, franja(hora), CANTON.get(c, ACENTOS.get(c, c)), tipo, tit(distrito) if distrito else '', tit(sub) if sub else ''])
    return out


if __name__ == '__main__':
    out = json.load(open(RUTA)) if os.path.exists(RUTA) and '--nuevo' not in sys.argv else []
    for archivo in [a for a in sys.argv[1:] if not a.startswith('--')]:
        nuevos = filas_de(archivo)
        pares = {(n[2], n[3]) for n in nuevos}
        out = [o for o in out if (o[2], o[3]) not in pares] + nuevos
        print(os.path.basename(archivo), ':', len(nuevos), 'hechos,', len({n[2] for n in nuevos}), 'cantones')
    out.sort()
    json.dump(out, open(RUTA, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(len(out), 'hechos, del', out[0][0], 'al', out[-1][0])
