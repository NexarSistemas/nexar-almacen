# Security Policy

## 📌 Versiones soportadas

Este proyecto se encuentra en desarrollo activo.

| Versión | Soporte |
|--------|--------|
| 1.7.x  | ✅ Soporte activo |
| < 1.7.0 | ❌ No soportado |

---

## 🚨 Reporte de vulnerabilidades

Si encontrás una vulnerabilidad, por favor **NO abrir un issue público**.

Contactar por:

- 📧 Email: nexarsistemas@outlook.com.ar  
- 📱 WhatsApp: +54 9 264 585-8874  

### 📋 Información necesaria

- Descripción del problema  
- Pasos para reproducirlo  
- Impacto potencial  
- Evidencia (capturas, logs, etc.)  

---

## ⏱️ Tiempos de respuesta

- Confirmación: dentro de 48 horas  
- Evaluación: 3 a 5 días  
- Resolución: según criticidad  

---

## 🔒 Alcance del sistema

Nexar Almacen es un sistema de gestión local que incluye:

- Punto de Venta (POS)  
- Gestión de stock e inventario  
- Caja y gastos  
- Cuentas corrientes  
- Sistema de usuarios (admin / vendedor)  
- Sistema de licencias y validación  

---

## 🔍 Áreas críticas

### 🔐 Autenticación
- Login de usuarios  
- Roles (admin / vendedor)  
- Manejo de sesiones  

⚠️ IMPORTANTE:  
Las credenciales por defecto deben cambiarse en el primer uso.

---

### 🔑 Configuración sensible
- `SECRET_KEY` (obligatoria desde v1.7.2)  
- Variables de entorno (`.env`)  
- `PUBLIC_KEY` para validación RSA  

---

### 🧾 Sistema de licencias
- Validación de licencias  
- Manipulación de tokens  
- Anti-reinstall (`telemetry.bin`)  
- Hardware ID  

---

### 💾 Base de datos
- Archivo `almacen.db`  
- Integridad de ventas, stock y caja  
- Acceso directo no autorizado  

---

### 📦 Backups
- Archivos de respaldo  
- Exportaciones de datos  

---

## ⚠️ Buenas prácticas implementadas

A partir de versiones recientes:

- `SECRET_KEY` obligatoria por variable de entorno  
- Eliminación de claves hardcodeadas  
- Uso de hashing seguro (`werkzeug.security`)  
- Soporte para claves públicas desde entorno (`PUBLIC_KEY`)  
- Validación de inputs del usuario  
- Manejo robusto en procesos de build  

---

## 🚫 Vulnerabilidades conocidas / prácticas inseguras

Se consideran fallos críticos:

- Uso de credenciales por defecto en producción  
- Hardcodear `SECRET_KEY`  
- Subir `.env` al repositorio  
- Manipular licencias o bypass del sistema  
- Modificar manualmente `almacen.db`  
- Acceso sin autenticación a endpoints  
- Exposición de backups o archivos internos  

---

## 🧪 Entornos

El sistema está diseñado para:

- Ejecución local (Flask + navegador o pywebview)  
- Distribución mediante ZIP o ejecutables  

⚠️ No está diseñado como servicio web expuesto a internet sin protección adicional.

---

## 📦 Dependencias

Se utilizan herramientas automáticas:

- Dependabot alerts  
- Dependabot security updates  

Se recomienda mantener las dependencias actualizadas.

---

## 🆕 Cambios relevantes de seguridad

### v1.7.3
- Corrección en carga de `SECRET_KEY` en build  
- Corrección de hashing de usuarios  

### v1.7.2
- Implementación obligatoria de `SECRET_KEY` por entorno  
- Eliminación de valores hardcodeados  

### v1.7.1
- Uso de `PUBLIC_KEY` desde variables de entorno  
- Eliminación de archivos sensibles del repositorio  

### v1.5.4
- Migración a sistema de licencias RSA 2048  

---

## 🙏 Reconocimiento

Se agradece a quienes reporten vulnerabilidades de forma responsable.

---

## 📢 Nota final

Este sistema maneja datos comerciales críticos (ventas, caja, clientes).  
La seguridad depende tanto del software como de su correcta configuración y uso por parte del usuario.
