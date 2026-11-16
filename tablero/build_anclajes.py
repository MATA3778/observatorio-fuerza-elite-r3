"""Convierte las capas de Anclajes DR3 (shapefiles) al JSON que usa la vista "Anclajes y zonas" (constante ANC).
Uso: python3 build_anclajes.py <carpeta_shp> <cantones.geojson> <salida.json>
Coordenadas en [latitud, longitud] (WGS84). Solo salen lugares y textos operativos; no se copian rutas del
servidor ni el nombre de quien registró cada factor. Las formas sin geometría se saltan."""
import json, sys, shapefile
from shapely.geometry import shape
sh, can, out = sys.argv[1:4]
R = lambda n: shapefile.Reader(f'{sh}/{n} DR3', encoding='latin-1')
CAN = {'Tarrazú': 'Tarrazú', 'Dota': 'Dota', 'León Cortés Castro': 'León Cortés', 'Cartago': 'Cartago', 'Paraíso': 'Paraíso', 'La Unión': 'La Unión',
       'Jiménez': 'Jiménez', 'Turrialba': 'Turrialba', 'Alvarado': 'Alvarado', 'Oreamuno': 'Oreamuno', 'El Guarco': 'El Guarco'}
ll = lambda q: [round(q[1], 5), round(q[0], 5)]
def partes(s, tol):
    g = shape(s.__geo_interface__).simplify(tol, preserve_topology=True)
    ps = list(g.geoms) if g.geom_type.startswith('Multi') else [g]
    return [[ll(q) for q in (p.exterior.coords if p.geom_type == 'Polygon' else p.coords)] for p in ps]
clean = lambda v: ' '.join(str(v or '').split())
pares = lambda r: [(s, rec) for s, rec in zip(r.shapes(), r.records()) if s.shapeType and s.points]
from shapely.geometry import Point
res = {'cantones': {}}; POL = {}
for f in json.load(open(can))['features']:
    n = CAN.get(f['properties']['NAME'])
    if n: g = shape(f['geometry']); POL[n] = g; b = g.bounds; res['cantones'][n] = [round(b[1], 4), round(b[0], 4), round(b[3], 4), round(b[2], 4)]
# Cantón donde cae cada punto (para acercar el mapa al elegir un cantón).
donde = lambda q: next((n for n, g in POL.items() if g.contains(Point(q))), '')
res['anclajes'] = [[*ll(s.points[0]), clean(rec['Nombre']), donde(s.points[0])] for s, rec in pares(R('Anclajes'))]
res['circuitos'] = [[partes(s, 0.00003), clean(rec['Nombre'])] for s, rec in pares(R('Circuitos'))]
res['cascos'] = [[partes(s, 0.00002), clean(rec['NOMBRE']), rec['FREQ']] for s, rec in pares(R('Cascos'))]
res['elipses'] = [[partes(s, 0.00002), clean(rec['ID_']), rec['FREQ']] for s, rec in pares(R('Elipses'))]
F = []
for s, rec in pares(R('Factores de riesgo')):
    d = rec.as_dict(); nom = clean(d['Nombre'])
    F.append([*ll(s.points[0]), clean(d['Descripcio']) or nom, clean(d['Hipotesis']), clean(d['AccionSuge']), clean(d['Canton']).title(), clean(d['Distrito']).title(), clean(d['Delito ASO']), clean(d['Categoria'] or d['TipoFactor']), donde(s.points[0])])
res['factores'] = F
json.dump(res, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v) for k, v in res.items()}, len(open(out).read()))
