# AI Developer Guide

Proyecto: Sistema de Gestión de Almacén  
Tecnología: Python + Flask + SQLite  

Este documento guía a asistentes de IA (Claude, ChatGPT, Gemini, Copilot)
para trabajar correctamente con el código del proyecto.

Antes de generar código nuevo, revisar:

PROJECT_CONTEXT.md  
ARCHITECTURE.md  
DATA_MODEL.md  
DEV_RULES.md  

---

# Principios del desarrollo

La aplicación es un sistema de gestión para pequeños comercios.

Debe priorizar:

- simplicidad
- estabilidad
- facilidad de mantenimiento
- bajo consumo de recursos

No introducir complejidad innecesaria.

---

# Arquitectura general

Flujo principal:

Usuario → HTML Template → Flask Route → Lógica → database.py → SQLite

Las responsabilidades se dividen así:

app.py  
    rutas Flask y lógica de negocio

database.py  
    acceso a base de datos

templates/  
    interfaz visual

services/  
    integraciones externas

---

# Cómo agregar nuevas funcionalidades

Cuando se agregue una funcionalidad nueva seguir este flujo.

## 1. definir objetivo

Ejemplo:

Agregar módulo de estadísticas de ventas.

---

## 2. verificar base de datos

Consultar:

DATA_MODEL.md

Si es necesario agregar una tabla, hacerlo en database.py.

---

## 3. crear funciones en database.py

Ejemplo:

obtener_ventas_por_fecha()  
obtener_top_productos()

La lógica de consultas debe ir aquí.

---

## 4. crear lógica en app.py

Agregar rutas Flask.

Ejemplo:

/estadisticas  
/ventas/reporte

Las rutas deben:

- llamar funciones de database.py
- procesar resultados
- enviar datos al template

---

## 5. crear template HTML

Ubicación:

templates/

Ejemplo:

estadisticas.html

Responsabilidades:

- mostrar datos
- no ejecutar lógica compleja

---

# Ejemplo de implementación

Caso: agregar reporte de productos más vendidos.

Pasos:

1. función en database.py

obtener_productos_mas_vendidos()

2. ruta en app.py

/estadisticas/productos

3. template

templates/productos_mas_vendidos.html

---

# Manejo de stock

Las reglas del sistema son:

- ventas descuentan stock
- compras aumentan stock
- el stock no puede ser negativo

Cuando se registra una venta:

1. guardar venta
2. guardar detalle
3. descontar stock

---

# Manejo de ventas

Proceso:

1. seleccionar productos
2. calcular total
3. registrar venta
4. registrar detalle de venta
5. actualizar stock
6. registrar movimiento de caja

---

# Manejo de compras

Proceso:

1. registrar proveedor
2. registrar compra
3. registrar detalle
4. actualizar stock

---

# Manejo de caja

Los movimientos de caja deben registrar:

fecha  
tipo (ingreso / egreso)  
monto  
descripcion

---

# Buenas prácticas para IA

Cuando modifiques el código:

1. no reescribir archivos completos
2. modificar solo funciones necesarias
3. respetar estructura del proyecto
4. evitar dependencias externas innecesarias
5. mantener compatibilidad con Python estándar

---

# Cuando analizar un archivo

Responder:

- qué hace el archivo
- cómo interactúa con otros módulos
- si existe código duplicado
- posibles mejoras

---

# Cuando agregar código

El código generado debe:

- seguir estilo existente
- mantener compatibilidad con Flask
- evitar lógica en templates
- centralizar consultas SQL

---

# Errores comunes a evitar

No hacer:

- SQL dentro de templates
- lógica compleja en HTML
- duplicar consultas SQL
- romper estructura de rutas

---

# Mejoras futuras posibles

El sistema puede evolucionar hacia:

- API REST
- multiusuario avanzado
- permisos por rol
- múltiples sucursales
- sincronización en red
- versión cloud

Las implementaciones futuras deben respetar la arquitectura base.

---

# Objetivo final

Mantener un sistema de gestión de almacén:

- estable
- simple
- rápido
- fácil de mantener
