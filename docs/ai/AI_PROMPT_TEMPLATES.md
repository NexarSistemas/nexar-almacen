# AI Prompt Templates

Proyecto: Sistema de Gestión de Almacén  
Tecnología: Python + Flask + SQLite  

Este archivo contiene plantillas de prompts para trabajar con el proyecto usando asistentes de IA.

Antes de usar cualquier prompt, proporcionar también el contexto del proyecto:

PROJECT_CONTEXT.md  
ARCHITECTURE.md  
DATA_MODEL.md  
FEATURE_MAP.md  
DEV_RULES.md  

---

# Prompt: analizar archivo

Analiza el siguiente archivo del proyecto.

Contexto del proyecto:
(ver PROJECT_CONTEXT.md)

Archivo a analizar:

[PEGAR CÓDIGO]

Explica:

1. qué hace el archivo
2. cómo interactúa con otros módulos
3. posibles problemas
4. posibles mejoras

---

# Prompt: encontrar bugs

Analiza el siguiente código del sistema.

Contexto del proyecto:
(ver PROJECT_CONTEXT.md)

Archivo:

[PEGAR CÓDIGO]

Objetivo:

1. detectar posibles bugs
2. explicar causa
3. proponer solución
4. indicar exactamente qué líneas modificar

No reescribir todo el archivo.

---

# Prompt: agregar nueva funcionalidad

Contexto del proyecto:

(ver PROJECT_CONTEXT.md)

Objetivo:

Agregar la siguiente funcionalidad al sistema:

[DESCRIBIR FUNCIONALIDAD]

Restricciones:

- mantener arquitectura actual
- modificar solo funciones necesarias
- mantener compatibilidad con Flask y SQLite

Indicar:

1. archivos a modificar
2. código a agregar
3. explicación del cambio

---

# Prompt: mejorar código existente

Analiza el siguiente código.

Objetivo:

Mejorar calidad del código sin cambiar comportamiento.

Código:

[PEGAR CÓDIGO]

Evaluar:

- claridad
- duplicación
- eficiencia
- posibles errores

Proponer refactorización.

---

# Prompt: crear consulta SQL

Contexto del sistema:

(ver DATA_MODEL.md)

Objetivo:

Crear consulta SQL que haga lo siguiente:

[DESCRIBIR CONSULTA]

Explicar:

1. consulta SQL
2. cómo integrarla en database.py

---

# Prompt: crear reporte

Contexto del proyecto:

(ver PROJECT_CONTEXT.md)

Crear reporte para:

[DESCRIBIR REPORTE]

Ejemplos:

- ventas por día
- productos más vendidos
- ganancias mensuales

Indicar:

1. consulta SQL
2. función en database.py
3. ruta Flask
4. template HTML

---

# Prompt: implementar tarea

Contexto del proyecto:

(ver PROJECT_CONTEXT.md)

Archivo AI_TASKS.md contiene tareas de desarrollo.

Implementar la tarea:

[TAREA]

Seguir estos pasos:

1. explicar solución
2. generar código
3. indicar archivos modificados

---

# Prompt: revisar arquitectura

Analiza la arquitectura del proyecto.

Usar:

ARCHITECTURE.md  
FEATURE_MAP.md  

Evaluar:

- organización del código
- separación de responsabilidades
- posibles mejoras

---

# Prompt: preparar nueva versión

Usando ROADMAP.md, planificar la siguiente versión del sistema.

Indicar:

1. funcionalidades a implementar
2. cambios necesarios en base de datos
3. módulos a modificar
4. plan de desarrollo por etapas

---

# Buenas prácticas al usar IA

Siempre proporcionar:

- contexto del proyecto
- archivo específico a modificar
- objetivo claro

Evitar:

- pedir cambios vagos
- enviar todo el proyecto innecesariamente
- reescribir archivos completos
