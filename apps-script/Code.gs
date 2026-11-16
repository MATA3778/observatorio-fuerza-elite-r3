/**
 * Observatorio Fuerza Élite R3 – página web que lee esta Google Sheet.
 * Solo lee cantidades de las hojas diarias (A4:G91) y de la General (A3:B90).
 * No escribe nada en la hoja.
 * Solo muestra datos con la llave de acceso (ver crearLlave); la usa el sitio con contraseña.
 */

var HORAS = ['13:00', '16:00', '18:00', '20:00', '22:00', '00:00'];
var MESES = { enero: 1, febrero: 2, marzo: 3, abril: 4, mayo: 5, junio: 6, julio: 7, agosto: 8,
  septiembre: 9, setiembre: 9, octubre: 10, noviembre: 11, diciembre: 12 };
var PRIMER_DIA = '2026-08-30'; // desde aquí las hojas tienen la estructura nueva (A4:G91)
// Nombres viejos de las hojas del 22 al 29 de agosto -> nombre de la General
var VIEJOS = {
  'aprehendidos por captura penal': 'Capturas Penales',
  'aprehendidos por conduccion temeraria': 'Aprehendidos Conducción Temeraria',
  'aprehendidos por migracion': 'Aprehensión Estatus Migratorio Irregular',
  'aprehendidos por migracion deportacion': 'Aprehensión Estatus Migratorio Irregular',
  'aprehendidos por migracion capturas internacionales': 'Captura Penal Internacional Migración',
  'aprehendidos por migracion citas': 'Citas Migración',
  'armas de fuego decomisadas': 'Decomiso Armas de Fuego',
  'decomiso armas menos letales': 'Decomiso Armas menos letal',
  'decomiso coaina gramos': 'Decomiso Cocaína Gramos',
  'decomiso coaina puntas': 'Decomiso Cocaína Puntas',
  'decomiso de municion': 'Decomiso de Municiones',
  'municion': 'Decomiso de Municiones',
  'municion 9mm': 'Decomiso de Municiones',
  'decomiso de placas': 'Placas decomisadas',
  'decomiso de placas transito': 'Placas decomisadas',
  'hallazgo arma de fuego': 'Hallazgo de arma de fuego',
  'informes contravencionales': 'Informes Policiales Contravencionales'
};

// Los datos se guardan en memoria (caché) para que la página cargue rápido.
// El activador "precalentar" los vuelve a preparar cada 5 minutos; duran CACHE_MIN minutos.
// Si alguien edita la hoja a mano, se borran y el próximo que abra ve lo nuevo.
var CACHE_MIN = 15;
var CACHE_PARTES = 20;           // máximo de pedazos de 90 000 caracteres
var CACHE_TAM = 90000;

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (!llaveValida_(p.llave)) {
    if (p.formato === 'html') return ContentService.createTextOutput('Acceso restringido');
    return HtmlService.createHtmlOutput('<div style="font-family:Arial,sans-serif;text-align:center;margin-top:80px">' +
      '<h2>Acceso restringido</h2><p>Este tablero solo se abre desde el sitio del Observatorio con contraseña.</p></div>')
      .setTitle('Acceso restringido');
  }
  var json = leerCache_();
  if (!json) {
    var datos = leerDatos_();
    json = JSON.stringify(datos);
    guardarCache_(json);
  }
  // formato=json: solo los datos. El sitio con contraseña ya trae el tablero (cifrado) y solo pide esto,
  // así el tablero se actualiza desde GitHub sin volver a pegar Index.html aquí.
  if (p.formato === 'json') return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
  var datos2 = JSON.parse(json);
  var t = HtmlService.createTemplateFromFile('Index');
  t.cortes = JSON.stringify(datos2.cortes).replace(/<\//g, '<\\/');
  t.general = JSON.stringify(datos2.general).replace(/<\//g, '<\\/');
  // formato=html: lo pide el sitio con contraseña (GitHub Pages) y lo muestra adentro.
  if (p.formato === 'html') return ContentService.createTextOutput(t.evaluate().getContent());
  return t.evaluate()
    .setTitle('Observatorio Fuerza Élite R3')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    // ALLOWALL: permite mostrar el tablero dentro de otra página (Google Sites).
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// Sin la llave correcta no se muestra nada. La llave se guarda en Propiedades del script (LLAVE),
// nunca en el código. Si no hay llave creada, el tablero queda cerrado.
function llaveValida_(llave) {
  var real = PropertiesService.getScriptProperties().getProperty('LLAVE');
  return !!real && typeof llave === 'string' && llave === real;
}

// Correr desde el editor: crea una llave nueva (la anterior deja de servir) y la muestra en el registro.
// Esa llave se copia en GitHub como el secreto OBS_LLAVE.
function crearLlave() {
  var llave = (Utilities.getUuid() + Utilities.getUuid()).replace(/-/g, '');
  PropertiesService.getScriptProperties().setProperty('LLAVE', llave);
  Logger.log('Llave nueva (cópiela en GitHub como OBS_LLAVE): ' + llave);
}

// Al editar la hoja a mano, se borra la caché para que el próximo que abra vea lo nuevo.
function onEdit() {
  borrarCache();
}

// Lo corre el activador cada 5 minutos: deja los datos listos para que nadie espere.
function precalentar() {
  guardarCache_(JSON.stringify(leerDatos_()));
}

// Correr UNA sola vez desde el editor: crea el activador de cada 5 minutos.
function instalarPrecalentado() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'precalentar') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('precalentar').timeBased().everyMinutes(5).create();
  precalentar();
}

function borrarCache() {
  var keys = ['obs_n'];
  for (var i = 0; i < CACHE_PARTES; i++) keys.push('obs_' + i);
  CacheService.getScriptCache().removeAll(keys);
}

function leerCache_() {
  try {
    var cache = CacheService.getScriptCache();
    var n = Number(cache.get('obs_n'));
    if (!n) return null;
    var keys = [];
    for (var i = 0; i < n; i++) keys.push('obs_' + i);
    var partes = cache.getAll(keys);
    var out = '';
    for (var j = 0; j < n; j++) {
      if (partes['obs_' + j] == null) return null;
      out += partes['obs_' + j];
    }
    return out;
  } catch (e) {
    return null;
  }
}

function guardarCache_(json) {
  try {
    var n = Math.ceil(json.length / CACHE_TAM);
    if (n > CACHE_PARTES) return;
    var obj = { obs_n: String(n) };
    for (var i = 0; i < n; i++) obj['obs_' + i] = json.substr(i * CACHE_TAM, CACHE_TAM);
    CacheService.getScriptCache().putAll(obj, CACHE_MIN * 60);
  } catch (e) {
    // Si la caché falla, la página igual funciona (solo carga más lento).
  }
}

function grupo_(c) {
  var l = c.toLowerCase();
  if (['personas investigadas', 'vehículos investigados', 'motos investigadas', 'camiones investigados',
       'busetas investigadas', 'controles vehiculares'].indexOf(l) >= 0) return 'Acciones operativas';
  if (/marihuana|crack|cocaína|éxtasis|tusi|wax/.test(l)) return 'Psicotrópicos';
  if (l.indexOf('dinero') >= 0) return 'Dinero';
  if (l.indexOf('aprehen') === 0 || (l.indexOf('captura') >= 0 && l.indexOf('orden de captura') < 0) ||
      l.indexOf('presentación') >= 0 || l.indexOf('citas migración') >= 0) return 'Aprehensiones';
  if (/arma|munici|cargadores|chaleco/.test(l)) return 'Armas';
  if (/boletas|placas|decomiso vehículos|motos|motocicletas|informes policiales/.test(l)) return 'Vehículos e infracciones';
  return 'Otros decomisos';
}
function tipo_(c) {
  var l = c.toLowerCase();
  if (l.indexOf('decomiso') === 0) return 'Decomiso';
  if (l.indexOf('hallazgo') === 0) return 'Hallazgo';
  return '';
}
function unidad_(c) {
  var l = c.toLowerCase();
  if (l.indexOf('gramos') >= 0) return 'g';
  if (l.indexOf('colones') >= 0) return '₡';
  if (l.indexOf('dólares') >= 0) return 'US$';
  return 'u';
}
function norm_(t) {
  return String(t).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^\x00-\x7f]/g, '').toLowerCase().split(/\s+/).filter(String).join(' ');
}
function num_(v) {
  if (typeof v === 'number') return v;
  if (typeof v === 'string' && v.trim()) { var n = Number(v.replace(/,/g, '').trim()); return isNaN(n) ? null : n; }
  return null;
}
function pad_(n) { return (n < 10 ? '0' : '') + n; }

function leerDatos_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var general = [];
  var orden = {};
  var gen = ss.getSheetByName('General');
  if (gen) {
    gen.getRange('A3:B90').getValues().forEach(function (r, i) {
      var c = String(r[0] || '').trim();
      if (!c) return;
      orden[c] = i;
      general.push({ orden: i + 1, categoria: c, grupo: grupo_(c), tipo: tipo_(c), unidad: unidad_(c), total: Number(r[1]) || 0 });
    });
  }
  var cortes = [];
  var porNorm = {};
  general.forEach(function (g) { porNorm[norm_(g.categoria)] = g.categoria; });
  // Hojas del 22 al 29 de agosto: se leen como están (no se modifican).
  // 22-24: la columna B es el total del día; 25-29: columnas acumuladas, la última con dato es el total.
  ss.getSheets().forEach(function (sh) {
    var m = sh.getName().trim().match(/^(\d{1,2})\s+agosto$/i);
    if (!m) return;
    var dia = Number(m[1]);
    if (dia < 22 || dia > 29) return;
    var vals = sh.getRange(1, 1, sh.getLastRow(), 7).getValues();
    var tot = {};
    vals.forEach(function (r) {
      if (!r[0]) return;
      var c = porNorm[norm_(r[0])] || VIEJOS[norm_(r[0])];
      if (!c) return;
      var nums = r.slice(1, 7).map(num_).filter(function (v) { return v !== null; });
      if (!nums.length) return;
      tot[c] = (tot[c] || 0) + (dia <= 24 ? nums[0] : nums[nums.length - 1]);
    });
    Object.keys(tot).forEach(function (c) {
      if (!tot[c]) return;
      cortes.push({ fecha: '2026-08-' + pad_(dia), corte: 'Día completo', categoria: c, grupo: grupo_(c), tipo: tipo_(c),
        unidad: unidad_(c), valor: Math.round(tot[c] * 100) / 100, _o: orden[c] === undefined ? 999 : orden[c] });
    });
  });
  ss.getSheets().forEach(function (sh) {
    var m = sh.getName().trim().match(/^(\d{1,2})\s+([a-záéíóú]+)$/i);
    if (!m) return;
    var mes = MESES[m[2].toLowerCase()];
    if (!mes) return;
    var anio = mes >= 8 ? 2026 : 2027;
    var fecha = anio + '-' + pad_(mes) + '-' + pad_(Number(m[1]));
    if (fecha < PRIMER_DIA) return;
    sh.getRange('A4:G91').getValues().forEach(function (r) {
      var c = String(r[0] || '').trim();
      if (!c) return;
      for (var i = 0; i < 6; i++) {
        var v = r[i + 1];
        if (typeof v === 'number' && v) {
          cortes.push({ fecha: fecha, corte: HORAS[i], categoria: c, grupo: grupo_(c), tipo: tipo_(c),
            unidad: unidad_(c), valor: Math.round(v * 100) / 100, _o: orden[c] === undefined ? 999 : orden[c] });
        }
      }
    });
  });
  cortes.sort(function (a, b) {
    return a.fecha < b.fecha ? -1 : a.fecha > b.fecha ? 1 :
      HORAS.concat(['Día completo']).indexOf(a.corte) - HORAS.concat(['Día completo']).indexOf(b.corte) || a._o - b._o;
  });
  cortes.forEach(function (r) { delete r._o; });
  return { cortes: cortes, general: general };
}
