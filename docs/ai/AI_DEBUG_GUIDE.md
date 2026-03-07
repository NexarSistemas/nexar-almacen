# AI Debug Guide

Proyecto: Sistema de Gestión de Almacén  
Tecnología: Python + Flask + SQLite  

Este documento ayuda a asistentes de IA a analizar y detectar errores en el sistema.

Antes de comenzar debugging revisar:

PROJECT_CONTEXT.md  
ARCHITECTURE.md  
DATA_MODEL.md  
FEATURE_MAP.md  

---

# Estrategia general de debugging

Cuando exista un problema:

1. identificar módulo afectado
2. identificar flujo de datos
3. revisar consultas SQL
4. revisar lógica en app.py
5. verificar integridad de datos

---

# Problemas comunes del sistema

## 1. Stock incorrecto

Síntomas:

- stock negativo
- stock no cambia después de una venta
- stock incorrecto después de una compra

Verificar:

- función de registro de venta
- función de actualización de stock
- tabla stock

Flujo correcto:

venta registrada  
→ detalle de venta guardado  
→ stock actualizado  

---

## 2. Venta registrada pero productos incorrectos

Síntomas:

- total incorrecto
- productos incorrectos en ticket

Verificar:

tabla ventas_detalle

Campos clave:

venta_id  
producto_id  
cantidad  
precio_unitario  

---

## 3. Caja no coincide con ventas

Síntomas:

- caja menor o mayor que ventas

Verificar:

tabla caja_historial

Regla del sistema:

cada venta debe registrar un ingreso en caja.

---

## 4. Problemas con base de datos

Errores comunes:

- tabla inexistente
- columna inexistente
- base de datos corrupta

Verificar:

- migraciones
- inicialización de base de datos
- rutas de conexión SQLite

Archivo responsable:

database.py

---

## 5. Problemas con importación de productos

Módulo:

OpenFoodFacts

Archivos:

openfoodfacts.py  
services/openfood_importer.py  

Errores posibles:

- API no responde
- código de barras inexistente
- datos incompletos

Solución:

validar respuesta antes de guardar en base de datos.

---

# Flujo de debugging recomendado

1. reproducir el error
2. identificar módulo
3. revisar logs
4. revisar consultas SQL
5. revisar flujo de funciones

---

# Verificación de integridad de datos

La IA debe verificar siempre:

- ventas sin detalle
- stock negativo
- productos sin categoría
- ventas sin cliente (si el sistema lo requiere)

---

# Consultas útiles para debugging

Productos sin stock:

SELECT * FROM productos
LEFT JOIN stock
ON productos.id = stock.producto_id
WHERE stock.stock_actual IS NULL;

---

Stock negativo:

SELECT *
FROM stock
WHERE stock_actual < 0;

---

Ventas sin detalle:

SELECT *
FROM ventas
WHERE id NOT IN (
SELECT venta_id FROM ventas_detalle
);

---

# Estrategia para corregir bugs

Cuando la IA proponga una solución debe:

1. explicar causa del problema
2. proponer solución
3. modificar solo funciones necesarias
4. evitar romper arquitectura existente

---

# Mejores prácticas de debugging

- revisar logs del servidor Flask
- revisar errores de SQLite
- revisar datos en base de datos
- probar cada módulo por separado

---

# Objetivo del debugging

Garantizar que el sistema mantenga:

- integridad de datos
- consistencia de stock
- consistencia de caja
- funcionamiento estable
