# PROJECT_CONTEXT.md

Proyecto: Sistema de Gestión de Almacén
Versión: leer archivo VERSION

Aplicación web local desarrollada en Python con Flask.

## Funciones principales

1. Gestión de productos
2. Control de stock mínimo y máximo
3. Punto de venta
4. Registro de compras
5. Control de caja diaria
6. Estadísticas de ventas
7. Cuentas corrientes de clientes y proveedores
8. Registro de gastos
9. Importación de productos
10. Backups del sistema

## Tecnologías

Python
Flask
SQLite
Jinja2
HTML

## Estructura

app.py
    servidor Flask y rutas

database.py
    acceso y operaciones en SQLite

generador_codigos.py
    generación automática de códigos

openfoodfacts.py
    integración con API de productos

services/
    servicios adicionales

templates/
    vistas HTML del sistema

## Tipo de aplicación

Aplicación web local (no SaaS)

Pensada para:

- pequeños comercios
- almacenes
- kioscos
- minimercados

## Reglas del sistema

- stock nunca debe ser negativo
- ventas deben descontar stock
- compras deben sumar stock
- el sistema registra caja diaria
