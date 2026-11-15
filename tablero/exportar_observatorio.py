import openpyxl, json, re, sys, datetime, unicodedata
SP=sys.argv[1]
wb=openpyxl.load_workbook('Cortes.xlsx',data_only=True)
MES={'agosto':8,'septiembre':9,'octubre':10,'noviembre':11}
HORAS=['13:00','16:00','18:00','20:00','22:00','00:00']
def grupo(c):
  l=c.lower()
  if l in('personas investigadas','vehículos investigados','motos investigadas','camiones investigados','busetas investigadas','controles vehiculares'): return 'Acciones operativas'
  if 'marihuana' in l or 'crack' in l or 'cocaína' in l or 'éxtasis' in l or 'tusi' in l or 'wax' in l: return 'Psicotrópicos'
  if 'dinero' in l: return 'Dinero'
  if l.startswith('aprehen') or 'captura' in l and 'orden de captura' not in l or 'presentación' in l or 'citas migración' in l: return 'Aprehensiones'
  if 'arma' in l or 'munici' in l or 'cargadores' in l or 'chaleco' in l: return 'Armas'
  if 'boletas' in l or 'placas' in l or 'decomiso vehículos' in l or 'motos' in l or 'motocicletas' in l or 'informes policiales' in l: return 'Vehículos e infracciones'
  return 'Otros decomisos'
def tipo(c):
  l=c.lower()
  if l.startswith('decomiso'): return 'Decomiso'
  if l.startswith('hallazgo'): return 'Hallazgo'
  return ''
def unidad(c):
  l=c.lower()
  if 'gramos' in l: return 'g'
  if 'colones' in l: return '₡'
  if 'dólares' in l: return 'US$'
  return 'u'
gen=wb['General']; cats=[]
for r in range(3,91):
  c=(gen.cell(r,1).value or '').strip()
  if c: cats.append(dict(categoria=c,grupo=grupo(c),tipo=tipo(c),unidad=unidad(c),orden=r-2,total=gen.cell(r,2).value or 0))
info={c['categoria']:c for c in cats}
norm=lambda t:' '.join(unicodedata.normalize('NFKD',str(t)).encode('ascii','ignore').decode().lower().split())
POR_NORM={norm(c['categoria']):c['categoria'] for c in cats}
# Nombres viejos (22-29 ago) -> nombre de la General
VIEJOS={'aprehendidos por captura penal':'Capturas Penales','aprehendidos por conduccion temeraria':'Aprehendidos Conducción Temeraria',
  'aprehendidos por migracion':'Aprehensión Estatus Migratorio Irregular','aprehendidos por migracion deportacion':'Aprehensión Estatus Migratorio Irregular',
  'aprehendidos por migracion capturas internacionales':'Captura Penal Internacional Migración','aprehendidos por migracion citas':'Citas Migración',
  'armas de fuego decomisadas':'Decomiso Armas de Fuego','decomiso armas menos letales':'Decomiso Armas menos letal',
  'decomiso coaina gramos':'Decomiso Cocaína Gramos','decomiso coaina puntas':'Decomiso Cocaína Puntas','decomiso de municion':'Decomiso de Municiones',
  'municion':'Decomiso de Municiones','municion 9mm':'Decomiso de Municiones','decomiso de placas':'Placas decomisadas',
  'decomiso de placas transito':'Placas decomisadas','hallazgo arma de fuego':'Hallazgo de arma de fuego','informes contravencionales':'Informes Policiales Contravencionales'}
def num(v):
  if isinstance(v,(int,float)): return v
  if isinstance(v,str):
    t=v.replace(',','').strip()
    try: return float(t)
    except ValueError: return None
  return None
rows=[]
for dia in range(22,30):
  name=next((n for n in wb.sheetnames if re.fullmatch(r'\s*%d\s+agosto\s*'%dia,n)),None)
  if not name: continue
  ws=wb[name]; tot={}
  for r in range(1,ws.max_row+1):
    a=ws.cell(r,1).value
    if not a: continue
    c=POR_NORM.get(norm(a)) or VIEJOS.get(norm(a))
    if not c: continue
    vals=[num(ws.cell(r,k).value) for k in range(2,8)]
    vals=[v for v in vals if v is not None]
    if not vals: continue
    v=vals[0] if dia<=24 else vals[-1]   # 22-24: columna B es el total; 25-29: columnas acumuladas, la última es el total
    tot[c]=tot.get(c,0)+v
  # Corrección confirmada por Jean (8 nov 2026): el 26 ago la hoja dice 78.7 colones; eran ₡78 700.
  if dia==26 and tot.get('Decomiso de Dinero colones')==78.7: tot['Decomiso de Dinero colones']=78700
  for c,v in tot.items():
    if v:
      k=info[c]; rows.append(dict(fecha='2026-08-%02d'%dia,corte='Día completo',categoria=c,grupo=k['grupo'],tipo=k['tipo'],unidad=k['unidad'],valor=round(v,2)))
for name in wb.sheetnames:
  m=re.fullmatch(r'\s*(\d+)\s+(\w+)\s*',name)
  if not m or m.group(2) not in MES: continue
  d=datetime.date(2026,MES[m.group(2)],int(m.group(1)))
  if d<datetime.date(2026,8,30): continue
  ws=wb[name]
  for r in range(4,92):
    c=(ws.cell(r,1).value or '').strip()
    if not c: continue
    for i,h in enumerate(HORAS):
      v=ws.cell(r,2+i).value
      if isinstance(v,(int,float)) and v:
        k=info[c]; rows.append(dict(fecha=d.isoformat(),corte=h,categoria=c,grupo=k['grupo'],tipo=k['tipo'],unidad=k['unidad'],valor=round(v,2)))
rows.sort(key=lambda x:(x['fecha'],(HORAS+['Día completo']).index(x['corte']),info[x['categoria']]['orden']))
json.dump(rows,open(SP+'/cortes_por_hora.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump([{k:c[k] for k in('orden','categoria','grupo','tipo','unidad','total')} for c in cats],open(SP+'/general.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(rows),rows[-1]['fecha'])
from collections import Counter
