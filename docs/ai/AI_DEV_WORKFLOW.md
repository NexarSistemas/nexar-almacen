# AI Development Workflow

Proyecto: Sistema de Gestión de Almacén  
Tecnología: Python + Flask + SQLite  

Este documento describe el flujo recomendado para desarrollar el proyecto utilizando asistentes de inteligencia artificial.

Objetivo:

Permitir que la IA funcione como un asistente de desarrollo confiable sin romper la arquitectura del sistema.

---

# Contexto necesario para trabajar

Antes de pedirle algo a una IA, proporcionar siempre:

PROJECT_CONTEXT.md  
ARCHITECTURE.md  
DATA_MODEL.md  
FEATURE_MAP.md  
DEV_RULES.md  

Esto permite que la IA entienda correctamente el sistema.

---

# Flujo de trabajo recomendado

El desarrollo asistido por IA debe seguir estas etapas.

---

# Etapa 1 — Definir el objetivo

Antes de generar código, definir claramente el objetivo.

Ejemplo:

Agregar reporte de productos más vendidos.

La IA debe responder:

- qué archivos modificar
- qué funciones crear
- qué consultas SQL usar

---

# Etapa 2 — Analizar el sistema

La IA debe revisar:

- arquitectura del sistema
- modelo de datos
- módulos existentes

Archivos clave:

ARCHITECTURE.md  
DATA_MODEL.md  
FEATURE_MAP.md  

---

# Etapa 3 — Plan de implementación

La IA debe proponer un plan antes de escribir código.

Ejemplo de plan:

1. crear consulta SQL
2. crear función en database.py
3. crear ruta Flask
4. crear template HTML

Solo después generar código.

---

# Etapa 4 — Generación de código

La IA debe:

- modificar solo funciones necesarias
- mantener estructura actual
- evitar duplicación de lógica
- centralizar consultas SQL en database.py

---

# Etapa 5 — Verificación

Después de generar código, revisar:

- integridad del stock
- integridad de ventas
- integridad de caja
- errores de base de datos

Usar AI_DEBUG_GUIDE.md.

---

# Etapa 6 — Pruebas manuales

Probar:

- creación de productos
- registro de ventas
- registro de compras
- actualización de stock
- reportes

---

# Etapa 7 — Documentación

Si se agrega una funcionalidad nueva:

Actualizar:

FEATURE_MAP.md  
DATA_MODEL.md  
ROADMAP.md  

---

# Flujo para resolver bugs

Cuando exista un bug:

1. reproducir el error
2. identificar módulo
3. revisar consultas SQL
4. revisar lógica en app.py
5. proponer solución mínima

Nunca reescribir archivos completos.

---

# Flujo para agregar funcionalidades

1. definir funcionalidad
2. verificar modelo de datos
3. crear consultas SQL
4. implementar rutas Flask
5. crear templates
6. probar funcionalidad

---

# Uso de AI_TASKS.md

Las tareas del proyecto se registran en:

AI_TASKS.md

El flujo recomendado es:

1. seleccionar tarea
2. analizar archivos relacionados
3. proponer solución
4. generar código
5. verificar funcionamiento

---

# Buenas prácticas para trabajar con IA

Siempre:

- proporcionar contexto
- trabajar archivo por archivo
- pedir cambios específicos

Evitar:

- enviar todo el proyecto innecesariamente
- pedir reescritura completa
- hacer cambios sin analizar arquitectura

---

# Objetivo del workflow

Este flujo permite que asistentes de IA funcionen como un segundo desarrollador que:

- analiza el sistema
- propone soluciones
- genera código compatible
- mantiene estabilidad del proyecto
