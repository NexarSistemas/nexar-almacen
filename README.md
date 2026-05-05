# 🛒 Nexar Almacen — v1.7.15

Sistema completo de gestión para almacenes desarrollado en Python + Flask + SQLite.
Funciona sin servidor, sin instalación compleja. Solo Python y un ZIP.

**Versión actual:** `1.7.15`
**Desarrollado por:** Nexar Sistemas · con Claude.ai · 2026

---

## 🚀 Cómo iniciar

### Requisitos
- Python 3.8 o superior
- Conexión a internet (solo la primera vez, para instalar dependencias)

### Pasos
1. Descomprimí el ZIP en cualquier carpeta
2. Abrí una terminal en la carpeta `almacen/`
3. Ejecutá: `python iniciar.py`
4. El sistema abre automáticamente en el navegador (o en ventana nativa si `pywebview` está disponible)

### Credenciales iniciales
| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | Administrador |
| `vendedor` | `vendedor123` | Vendedor |

---

## 💳 Planes de licencia

| Plan | Modalidad | Productos OFF | Clientes | Proveedores | Estadísticas | Actualizaciones |
|------|-----------|--------------|----------|-------------|--------------|-----------------|
| **BASICA** | Pago único / permanente | Máx 200 | Máx 100 | Máx 50 | Operación base | ❌ |
| **PRO** | Mensual | Ilimitado | Ilimitado | Ilimitado | Avanzadas | Según licencia |
| **FULL** | Mensual | Ilimitado | Ilimitado | Ilimitado | Completas | ✅ Incluidas |

- Al vencer un plan mensual, la instalación conserva la base activa si ya tenía BASICA habilitada
- Contacto para licencias: [WhatsApp +549 264 585-8874](https://wa.me/5492645858874)

---

## 📋 Módulos incluidos

| Módulo | Descripción |
|--------|-------------|
| 🏠 **Dashboard** | KPIs en tiempo real, alertas, gráfico de ventas |
| 📦 **Productos** | Catálogo con margen, IVA, código interno y barras |
| 📊 **Stock** | Niveles con alertas: Sin stock / Crítico / Bajo / Exceso |
| 🛒 **Punto de Venta** | Ticket, búsqueda por código o barras, múltiples medios de pago |
| 📝 **Historial Ventas** | Filtros por fecha, cliente, medio de pago |
| 🛍️ **Compras** | Ingreso de mercadería con actualización automática de stock |
| 💰 **Caja** | Apertura/cierre diario, gastos del día, historial |
| 💸 **Gastos** | Registro y clasificación |
| 👥 **CC Clientes** | Cuenta corriente con movimientos y alertas de deuda |
| 🏭 **CC Proveedores** | Facturas pendientes, pagos, alertas de vencimiento |
| 📈 **Estadísticas** | Ventas mensuales, semanales, medios de pago, temporadas *(Pro)* |
| 🔍 **Análisis** | Rentabilidad, top productos, recomendaciones estacionales *(Pro)* |
| ☁️ **Importar Productos** | Importación desde OpenFoodFacts (Argentina) o dataset local |
| 🚫 **Lista Negra** | Barcodes bloqueados para no reimportar |
| 🔄 **Actualización** | Aplicar nueva versión sin reinstalar *(Pro)* |
| ⚙️ **Configuración** | Datos del negocio, categorías, márgenes, respaldos |
| 👤 **Usuarios** | Roles admin/vendedor, alta y baja de usuarios |
| 📜 **Changelog** | Historial de versiones dentro de la aplicación |

---

## 💳 Medios de pago soportados
- Efectivo
- Débito / Crédito
- Transferencia
- QR / Billetera Virtual (Mercado Pago, etc.)
- Cuenta Corriente (se registra automáticamente en la CC del cliente)

## 🔫 Lector de código de barras
Compatible con lectores USB (HID). Sin configuración: el código se ingresa directamente en el campo activo del Punto de Venta o en el formulario de productos.

## 💾 Base de datos
- **SQLite** — el archivo `almacen.db` se crea automáticamente en el primer inicio
- No requiere servidor de base de datos
- Las actualizaciones **nunca sobrescriben** `almacen.db`
- Hacer backup periódico del archivo `almacen.db`

---

## 🔄 Cómo actualizar sin reinstalar *(Plan Pro)*

1. Obtené el ZIP de la nueva versión
2. En la aplicación: **Menú → Actualización**
3. Subí el ZIP → el sistema extrae solo `.py` y `.html`
4. Reiniciá con `python iniciar.py`

La base de datos, tus ventas, productos y configuración **nunca se tocan**.

---

## 📁 Estructura del proyecto

```
almacen/
├── iniciar.py              ← Launcher principal
├── app.py                  ← Rutas Flask
├── database.py             ← Lógica de datos y migraciones
├── productos_seed.py       ← Dataset local de 361 productos argentinos
├── openfoodfacts.py        ← Módulo API OpenFoodFacts (legacy)
├── license_verifier.py     ← Verificación de licencia online
├── VERSION                 ← Versión actual (fuente de verdad)
├── CHANGELOG.md            ← Historial de versiones
├── README.md               ← Este archivo
├── almacen.db              ← Base de datos (NO incluir en backups del código)
├── services/
│   └── openfood_importer.py ← Importador OFF con filtros y blacklist
└── templates/              ← Vistas HTML (Jinja2)
```

---

## 📦 Versiones

Ver historial completo en [CHANGELOG.md](CHANGELOG.md) o en la app: **Menú → Acerca de**.

| Versión | Fecha | Tipo | Descripción |
|---------|-------|------|-------------|
| **1.7.15** | 2026-05-05 | Mejora | Alineación comercial de planes BASICA / PRO / FULL, ocultando DEMO como plan visible y limpiando textos antiguos de licencia |
| **1.7.14** | 2026-05-05 | Mejora | El plan Demo ahora habilita los módulos principales para probar Nexar Almacén sin incluir módulos premium |
| **1.7.13** | 2026-05-01 | Mejora | La ventana nativa inicia maximizada de forma explícita |
| **1.7.12** | 2026-05-01 | Mejora | Búsqueda e importación individual desde OpenFoodFacts Argentina por código de barras o nombre |
| **1.7.11** | 2026-04-25 | Mejora | Tickets con diseño detallado, IVA opcional, vendedor real y recibido/vuelto para pagos en efectivo |
| **1.7.10** | 2026-04-25 | Seguridad / Mejora | Borrado seguro de ventas y cálculo claro de margen bruto, ganancia bruta, markup y precio sugerido en productos |
| **1.7.9** | 2026-04-23 | Corrección | Normalización de URLs Supabase en licencias |
| **1.7.8** | 2026-04-23 | Seguridad | Política uniforme de usuarios y contraseñas |
| **1.7.1** | 2026-03-29 | Seguridad | Llave pública desde env var, builds mejorados |
| **1.7.2** | 2026-04-08 | Mejoras | Aplicación del estándar NEXAR_SECRET_KEY_STANDARD para el manejo de `SECRET_KEY`. |
| **1.7.3** | 2026-04-08 | Corrección | Corrección de la carga de `SECRET_KEY` en el build y del hash de contraseñas de usuarios predeterminados. |
| **1.7.0** | 2026-03-28 | Mejoras | Pipeline CI/CD inteligente y corrección de enlaces |
| **1.6.0** | 2026-03-19 | Nueva función | Sistema de tiers: Plan Básico y Plan Pro, anti-reinstall |
| 1.5.5 | 2026-03-18 | Corrección | Fix ticket abría navegador externo pidiendo login |
| 1.5.4 | 2026-03-15 | Seguridad | Sistema de licencias RSA con soporte MONO y MULTI |
| 1.5.3 | 2026-03-07 | Corrección | Fix loop de login al apagar desde la app |
| 1.5.2 | 2026-03-07 | Mejoras | Integración, Organización y Mejora del manejo de favicon en Flask |
| 1.5.1 | 2026-03-05 | Corrección | Fix login loop al reiniciar |
| 1.5.0 | 2026-03-02 | Nueva función | Puerto aleatorio, ventana nativa, actualizaciones |
| 1.4.0 | 2026-02-27 | Nueva función | Filtros OFF, lista negra, proveedor en stock |
| 1.3.0 | 2026-02-27 | Nueva función | OpenFoodFacts, demo por tiempo |
| 1.2.1 | 2026-02-24 | Corrección | Respaldos, apagado, estabilidad |
| 1.2.0 | 2026-02-01 | Nueva función | Estadísticas, análisis, usuarios |
| 1.1.0 | 2026-01-15 | Nueva función | Cuentas corrientes |
| 1.0.0 | 2026-01-01 | Lanzamiento | Primera versión |

---

Desarrollado con Python 3 · Flask · SQLite · Bootstrap 5 · Chart.js
