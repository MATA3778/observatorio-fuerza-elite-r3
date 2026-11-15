import re
s=open('observatorio_publico.html').read()
s=re.sub(r'<script type="application/json" id="data-cortes">.*?</script>','<script type="application/json" id="data-cortes"><?!= cortes ?></script>',s,flags=re.S)
s=re.sub(r'<script type="application/json" id="data-general">.*?</script>','<script type="application/json" id="data-general"><?!= general ?></script>',s,flags=re.S)
s=re.sub(r'<script type="application/json" id="data-hechos">.*?</script>\n?','',s,flags=re.S)
s=s.replace('<title>Observatorio R3 Público</title>\n','').replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
s='<!DOCTYPE html>\n<html lang="es">\n<head>\n<base target="_top">\n<meta charset="utf-8">\n'+s.replace('<div id="dash-root">','</head>\n<body style="margin:0">\n<div id="dash-root">',1)+'</body>\n</html>\n'
for a,b in [('Lo que dice la hoja General de Cortes.xlsx','Lo que dice la hoja General'),
            ('Las hojas diarias de Cortes.xlsx desde el 22 de agosto','Las hojas diarias de la Google Sheet desde el 22 de agosto. Se leen cada vez que se abre la página')]:
  assert a in s; s=s.replace(a,b)
open('Index.html','w').write(s)
