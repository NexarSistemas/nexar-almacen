# Reglas de Desarrollo

Estas reglas están diseñadas para que herramientas de IA
(Claude, ChatGPT, Gemini, Copilot) trabajen correctamente con el proyecto.

---

# Principios generales

1. No reescribir archivos completos innecesariamente.
2. Modificar solo las funciones afectadas.
3. Mantener nombres de variables existentes.
4. Mantener estructura del proyecto.

---

# Estilo de código

Lenguaje: Python

Reglas:

- funciones cortas
- nombres descriptivos
- evitar duplicación de código
- comentarios cuando la lógica no sea obvia

---

# Base de datos

Motor:

SQLite

Reglas:

- centralizar consultas en database.py
- evitar SQL en múltiples archivos
- validar datos antes de guardar

---

# Lógica de negocio

Debe mantenerse en:

app.py  
o en módulos específicos.

Nunca en templates.

---

# Templates

Directorio:

templates/

Reglas:

- lógica mínima
- solo renderización
- evitar cálculos complejos

---

# Integraciones externas

Las APIs deben implementarse en:

services/

Nunca mezclar llamadas externas dentro de rutas Flask directamente.

---

# Seguridad

Siempre validar:

- inputs de usuario
- datos de formularios
- consultas a base de datos

---

# Compatibilidad

El sistema debe funcionar con:

Python 3.x  
Flask  
SQLite

Sin requerir infraestructura compleja.

---

# Cambios grandes

Si se realizan cambios importantes:

- documentar en CHANGELOG.md
- actualizar ARCHITECTURE.md
