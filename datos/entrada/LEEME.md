Sube aquí (desde GitHub: Add file → Upload files, en una rama nueva) el CSV o .xls de Estadísticas Policiales del OIJ.
El flujo "Actualizar datos del OIJ" lo convierte y abre un pull request con `datos/hechos.json` actualizado.
Estos archivos no se guardan: el flujo los borra en el mismo pull request. El reporte solo trae fecha, franja, cantón, tipo, distrito y modalidad.
