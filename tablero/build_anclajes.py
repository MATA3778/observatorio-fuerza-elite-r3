"""Convierte las capas de Anclajes DR3 (shapefiles) al JSON que usa la vista "Anclajes y zonas".
Uso: python3 build_anclajes.py <carpeta_shp> <cantones.geojson> <salida.json>
Solo salen lugares y textos operativos; no se copian rutas del servidor ni el nombre de quien registró."""
import json, sys, math, shapefile
from shapely.geometry import shape
sh, can, out = sys.argv[1:4]
R = lambda n: shapefile.Reader(f'{sh}/{n} DR3', encoding='latin-1')
cg = json.load(open(can))['features']
xs, ys = [], []
for f in cg:
    s = shape(f['geometry']); b = s.bounds; xs += [b[0], b[2]]; ys += [b[1], b[3]]
CAN = {'Tarrazú','Dota','León Cortés Castro','Cartago','Paraíso','La Unión','Jiménez','Turrialba','Alvarado','Oreamuno','El Guarco'}
cs = [f for f in cg if f['properties']['NAME'] in CAN]
xs, ys = [], []
for f in cs:
    b = shape(f['geometry']).bounds; xs += [b[0], b[2]]; ys += [b[1], b[3]]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); cx = math.cos(math.radians((y0+y1)/2))
W = 560; k = W/((x1-x0)*cx); H = (y1-y0)*k
P = lambda x, y: ((x-x0)*cx*k, (y1-y)*k)
fmt = lambda pts: 'L'.join('%.1f,%.1f' % P(*q) for q in pts)
def path(g, tol, close):
    g = g.simplify(tol, preserve_topology=True)
    parts = list(g.geoms) if g.geom_type.startswith('Multi') else [g]
    d = ''
    for p in parts:
        rings = [p.exterior] if p.geom_type == 'Polygon' else [p]
        for r in rings:
            if len(r.coords) > 1: d += 'M' + fmt(r.coords) + ('Z' if close else '')
    return d
def clean(v): return ' '.join(str(v or '').split())
res = {'w': W, 'h': round(H, 1)}
# Los cantones de fondo ya están en el tablero (MAPA.c), con esta misma proyección.
r = R('Anclajes'); res['anclajes'] = [[*map(lambda v: round(v, 1), P(*s.points[0])), clean(rec['Nombre'])] for s, rec in zip(r.shapes(), r.records()) if s.shapeType and s.points]
r = R('Circuitos'); res['circuitos'] = [[path(shape(s.__geo_interface__), 0.0001, False), clean(rec['Nombre'])] for s, rec in zip(r.shapes(), r.records()) if s.shapeType]
r = R('Cascos'); res['cascos'] = [[path(shape(s.__geo_interface__), 0.0001, True), clean(rec['NOMBRE']), rec['FREQ']] for s, rec in zip(r.shapes(), r.records()) if s.shapeType]
r = R('Elipses'); res['elipses'] = [[path(shape(s.__geo_interface__), 0.0001, True), clean(rec['ID_']), rec['FREQ']] for s, rec in zip(r.shapes(), r.records()) if s.shapeType]
r = R('Factores de riesgo'); F = []
for s, rec in zip(r.shapes(), r.records()):
    d = rec.as_dict()
    if not s.shapeType or not s.points: continue
    nom = clean(d['Nombre']); desc = clean(d['Descripcio']) or nom
    F.append([*map(lambda v: round(v, 1), P(*s.points[0])), desc, clean(d['Hipotesis']), clean(d['AccionSuge']), clean(d['Canton']).title(), clean(d['Distrito']).title(), clean(d['Delito ASO']), clean(d['Categoria'] or d['TipoFactor'])])
res['factores'] = F
json.dump(res, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v) for k, v in res.items() if isinstance(v, (list, dict))}, len(open(out).read()))
