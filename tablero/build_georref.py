"""Agrega a la constante ANC de apps-script/Index.html las capas "her" (heridos georreferenciados) y "dclp" (delitos contra la propiedad).
Uso: python3 build_georref.py <heridos.xlsx> <dclp.xls> <cantones.geojson> <apps-script/Index.html>
Se usan las coordenadas depuradas (si no sirven, las originales). NO se copian direcciones ni señas (pueden identificar a víctimas).
Cada fila: [lat, lon, cantón, delegación, cuántos registros caen en ese mismo punto]. Requiere pandas, xlrd, shapely."""
import sys, json, re, pandas as pd
from shapely.geometry import shape, Point
hx, dx, can, html = sys.argv[1:5]
POL = {}
CAN = {'Tarrazú': 'Tarrazú', 'Dota': 'Dota', 'León Cortés Castro': 'León Cortés', 'Cartago': 'Cartago', 'Paraíso': 'Paraíso', 'La Unión': 'La Unión',
       'Jiménez': 'Jiménez', 'Turrialba': 'Turrialba', 'Alvarado': 'Alvarado', 'Oreamuno': 'Oreamuno', 'El Guarco': 'El Guarco'}
for f in json.load(open(can))['features']:
    n = CAN.get(f['properties']['NAME'])
    if n: POL[n] = shape(f['geometry'])
DELEG = {'D37': 'Cartago', 'D38': 'Paraíso', 'D39': 'La Unión', 'D40': 'Jiménez', 'D41': 'Turrialba', 'D42': 'Alvarado', 'D43': 'Oreamuno', 'D44': 'El Guarco', 'D45': 'Tarrazú', 'D46': 'Dota', 'D48': 'Cartago'}
num = lambda v: pd.to_numeric(str(v).replace(',', '').strip(), errors='coerce')
ok = lambda lo, la: pd.notna(lo) and pd.notna(la) and -86 < lo < -82 and 8 < la < 11.5
def punto(lo1, la1, lo2, la2):
    for lo, la in ((num(lo2), num(la2)), (num(lo1), num(la1))):
        if ok(lo, la): return lo, la
def donde(p, pref):
    for n, g in POL.items():
        if g.contains(Point(p)): return n
    return pref
def arma(filas):
    cuenta, ord_ = {}, []
    for lo, la, pref, deleg in filas:
        c = donde((lo, la), pref); k = (round(la, 5), round(lo, 5), c, deleg)
        if k not in cuenta: cuenta[k] = 0; ord_.append(k)
        cuenta[k] += 1
    return [[*k[:4], cuenta[k]] for k in ord_], len(filas)
# Heridos: hojas D37.., columnas A cantón, E-F coordenadas originales (D,E), depuradas (H,I).
H, perdidos_h = [], 0
for n, x in pd.read_excel(hx, sheet_name=None, header=None).items():
    for _, r in x.iloc[1:].iterrows():
        p = punto(r[3], r[4], r[7], r[8])
        if not p: perdidos_h += 1; continue
        H.append((*p, '', DELEG.get(n[:3], '')))
her, nh = arma(H)
# DCLP: A delegación, E-F originales, I-J depuradas.
d = pd.read_excel(dx, header=0); D, perdidos_d = [], 0
for _, r in d.iterrows():
    p = punto(r.iloc[4], r.iloc[5], r.iloc[8], r.iloc[9])
    if not p: perdidos_d += 1; continue
    D.append((*p, '', DELEG.get(str(r.iloc[0])[:3], '')))
dclp, nd = arma(D)
s = open(html, encoding='utf-8').read()
m = re.search(r'^(  const ANC = )(\{.*\});$', s, re.M)
A = json.loads(m.group(2)); A['her'] = her; A['dclp'] = dclp; A['n'] = {'her': nh, 'dclp': nd, 'her_sin': perdidos_h, 'dclp_sin': perdidos_d}
s = s[:m.start(2)] + json.dumps(A, ensure_ascii=False, separators=(',', ':')) + s[m.end(2):]
open(html, 'w', encoding='utf-8').write(s)
print(A['n'], len(her), len(dclp))
