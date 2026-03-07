# AI Tasks

Proyecto: Sistema de Gestión de Almacén

Este archivo contiene tareas de desarrollo que pueden ser realizadas por asistentes de IA.

Antes de trabajar en una tarea revisar:

PROJECT_CONTEXT.md  
ARCHITECTURE.md  
DATA_MODEL.md  
DEV_RULES.md  
AI_DEVELOPER_GUIDE.md  

Cada tarea debe completarse respetando la arquitectura del sistema.

---

# Estado de tareas

Estados posibles:

TODO
IN_PROGRESS
DONE

---

# Tarea 001 — Mejora del control de stock

Estado: TODO

Objetivo:

Agregar historial de movimientos de stock.

Descripción:

Actualmente el sistema solo guarda el stock actual.  
Se necesita registrar cada cambio para poder auditar movimientos.

Cambios necesarios:

1. Crear tabla `movimientos_stock`.

Campos:

id  
producto_id  
tipo_movimiento  
cantidad  
fecha  
referencia  

Tipos de movimiento:

venta  
compra  
ajuste  

Archivos a modificar:

database.py  
app.py  

Resultado esperado:

Cada cambio de stock debe generar un registro en esta tabla.

---

# Tarea 002 — Productos más vendidos

Estado: TODO

Objetivo:

Crear reporte de productos más vendidos.

Cambios necesarios:

1. Crear consulta SQL para sumar ventas por producto.
2. Crear ruta Flask `/estadisticas/productos`.
3. Crear template `productos_mas_vendidos.html`.

Archivos a modificar:

database.py  
app.py  
templates/

Resultado esperado:

Lista ordenada de productos con mayor cantidad vendida.

---

# Tarea 003 — Alerta de stock mínimo

Estado: TODO

Objetivo:

Mostrar alerta cuando un producto llegue al stock mínimo.

Cambios necesarios:

1. consulta para detectar stock bajo
2. mostrar alerta en dashboard

Archivos a modificar:

database.py  
app.py  
templates/dashboard.html

Resultado esperado:

El dashboard muestra productos con stock bajo.

---

# Tarea 004 — Exportar ventas a Excel

Estado: TODO

Objetivo:

Permitir exportar ventas a archivo Excel.

Cambios necesarios:

1. generar archivo XLSX
2. descargar desde navegador

Archivos a modificar:

app.py

Librerías posibles:

pandas  
openpyxl

Resultado esperado:

El usuario puede descargar reporte de ventas.

---

# Tarea 005 — Mejora del buscador de productos

Estado: TODO

Objetivo:

Mejorar búsqueda de productos.

Funciones:

buscar por:

- nombre
- código de barras
- marca

Archivos a modificar:

database.py  
app.py  
templates/productos.html

Resultado esperado:

Búsqueda más rápida y flexible.

---

# Tarea 006 — Dashboard mejorado

Estado: TODO

Objetivo:

Mejorar panel principal del sistema.

Agregar:

- ventas del día
- ingresos del día
- productos con stock bajo
- top productos vendidos

Archivos a modificar:

app.py  
templates/dashboard.html

---

# Reglas para IA

Cuando una IA trabaje en una tarea debe:

1. leer contexto del proyecto
2. explicar la solución
3. generar código
4. indicar archivos modificados
5. no romper arquitectura existente

---

# Flujo recomendado para IA

1. seleccionar tarea
2. analizar archivos relacionados
3. proponer solución
4. generar código
5. explicar cambios
