# Arquitectura del Sistema

Proyecto: Sistema de Gestión de Almacén  
Tecnología principal: Python + Flask  
Base de datos: SQLite  
Interfaz: HTML + Jinja2 templates  

## Tipo de aplicación

Aplicación web local diseñada para ejecutarse en una computadora del comercio.

No depende de servicios externos salvo APIs opcionales (OpenFoodFacts).

---

# Componentes del sistema

## 1. Aplicación principal

Archivo:

app.py

Responsabilidades:

- inicializar servidor Flask
- registrar rutas
- manejar lógica de negocio
- coordinar interacción con base de datos
- renderizar templates HTML

---

## 2. Capa de base de datos

Archivo:

database.py

Responsabilidades:

- conexión SQLite
- operaciones CRUD
- consultas de productos
- consultas de ventas
- consultas estadísticas

Debe mantenerse separada de la lógica de interfaz.

---

## 3. Servicios externos

Directorio:

services/

Contiene integraciones externas.

Ejemplo:

openfood_importer.py

Función:

- importar productos desde OpenFoodFacts

---

## 4. Generación de datos auxiliares

Archivos:

generador_codigos.py  
productos_seed.py  

Responsabilidades:

- generación automática de códigos
- carga inicial de productos

---

## 5. Integración de productos externos

Archivo:

openfoodfacts.py

Función:

- consultar información de productos desde API pública

---

## 6. Interfaz de usuario

Directorio:

templates/

Tecnología:

HTML + Jinja2

Ejemplos de vistas:

- dashboard
- productos
- ventas
- stock
- estadísticas
- caja

---

# Flujo típico del sistema

Usuario → Interfaz HTML → Flask (app.py) → database.py → SQLite

Respuesta:

SQLite → database.py → Flask → Template → Usuario

---

# Reglas de arquitectura

1. Separar lógica de negocio y acceso a datos.
2. No mezclar consultas SQL dentro de templates.
3. Mantener funciones pequeñas y específicas.
4. Evitar dependencias externas innecesarias.
5. Mantener compatibilidad con Python estándar.

---

# Escalabilidad futura

Posibles mejoras:

- migración a PostgreSQL
- API REST
- interfaz SPA
- sistema multiusuario
- sistema de permisos
