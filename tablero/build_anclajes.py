"""Convierte las capas de Anclajes DR3 (shapefiles) al JSON que usa la vista "Anclajes y zonas" (constante ANC).
Uso: python3 build_anclajes.py <carpeta_shp> <cantones.geojson> <salida.json> [--set <capa SET DR3 sin .shp>] [--zip <capa ZIP UNIDA sin .shp> ...]
--set: delitos del seguimiento mensual (SET DR3). --zip: capas "ZIP UNIDA"/"ZIP UNIDO" de cada delegación (delitos que
sirvieron de base a las zonas); se juntan y se quitan los repetidos. Estas capas vienen en CRTM05 y se pasan a WGS84.
De los delitos no se copia el campo "Señas" (dirección del hecho, a veces la casa de la víctima).
Coordenadas en [latitud, longitud] (WGS84). Solo salen lugares y textos operativos; no se copian rutas del
servidor ni el nombre de quien registró cada factor. Las formas sin geometría se saltan."""
import json, sys, shapefile
from shapely.geometry import shape
sh, can, out = sys.argv[1:4]
OPC = {'--set': [], '--zip': []}; _k = None
for a in sys.argv[4:]:
    if a in OPC: _k = a
    else: OPC[_k].append(a)
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
# Delitos (SET DR3 y ZIP UNIDA): puntos en CRTM05 -> WGS84, sin "Señas".
import datetime
from pyproj import CRS, Transformer
ARREGLO = {'Vehï¿½culo': 'Vehículo', 'Edificaciï¿½n': 'Edificación', 'Paraï¿½so': 'Paraíso', 'Uniï¿½n': 'Unión', 'Jimï¿½nez': 'Jiménez',
           'Tarrazï¿½': 'Tarrazú', 'Leï¿½n': 'León', 'Cortï¿½s': 'Cortés', 'Comisiï¿½n': 'Comisión', 'Discusiï¿½n': 'Discusión'}
def arregla(t):
    for a, b in ARREGLO.items(): t = t.replace(a, b)
    return t.replace('ï¿½', '').replace('\ufffd', '')
def delitos(rutas):
    vistos, out_ = set(), []
    for ruta in rutas:
        r = shapefile.Reader(ruta, encoding='latin-1')
        tr = Transformer.from_crs(CRS.from_wkt(open(ruta + '.prj').read()), 'EPSG:4326', always_xy=True)
        nom = [f[0] for f in r.fields[1:]]
        campo = lambda d, pref: next((d[k] for k in nom if k.startswith(pref)), '')
        for s, rec in pares(r):
            d = dict(zip(nom, rec)); lon, lat = tr.transform(*s.points[0])
            fe = clean(campo(d, 'Fecha'))
            try: fe = datetime.datetime.strptime(fe, '%d/%m/%Y').strftime('%Y-%m-%d')
            except ValueError: pass
            ho = clean(campo(d, 'Hora'))[:5]
            fila = [round(lat, 5), round(lon, 5), arregla(clean(campo(d, 'Delito'))).capitalize(), arregla(clean(campo(d, 'Modalidad'))).capitalize(), fe, '' if ho.upper().startswith('DESCO') else ho,
                    clean(campo(d, 'Distrito')).title(), arregla(clean(campo(d, 'Delegaci'))), arregla(clean(campo(d, 'Lugar'))), clean(d.get('NOMBRE', '')), donde((lon, lat))]
            clave = (fila[0], fila[1], fila[4], fila[5], fila[2])
            if clave in vistos: continue
            vistos.add(clave); out_.append(fila)
    return sorted(out_, key=lambda f: f[4])
if OPC['--set']: res['set'] = delitos(OPC['--set'])
if OPC['--zip']: res['zip'] = delitos(OPC['--zip'])
json.dump(res, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v) for k, v in res.items()}, len(open(out).read()))
