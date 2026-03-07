# CLAUDE.md

Proyecto: Sistema de Gestión de Almacén

Lenguaje principal: Python
Framework web: Flask
Base de datos: SQLite
Interfaz: HTML + Jinja2 templates

## Objetivo del sistema

Aplicación web local para gestión de un almacén o comercio pequeño.

Funciones principales:

- gestión de productos
- control de stock
- ventas (punto de venta)
- compras
- control de caja
- estadísticas
- cuentas corrientes
- gastos
- backup del sistema
- importación de productos

## Arquitectura

app.py
    aplicación principal Flask
    rutas del sistema

database.py
    acceso a base de datos SQLite
    funciones CRUD

iniciar.py
    script de inicio del sistema

generador_codigos.py
    generación de códigos de productos

openfoodfacts.py
    consulta API OpenFoodFacts

services/openfood_importer.py
    importación masiva de productos

templates/
    interfaz HTML del sistema

## Reglas para modificar el proyecto

- NO reescribir archivos completos si no es necesario
- modificar solo funciones afectadas
- mantener compatibilidad con SQLite
- mantener compatibilidad con Flask
- respetar estructura actual del proyecto

## Buenas prácticas

- código simple
- funciones pequeñas
- evitar dependencias externas innecesarias
- mantener nombres de variables existentes
