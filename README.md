# 🛒 Sistema de Gestión — Almacén

Sistema completo de gestión para almacenes desarrollado en Python + Flask + SQLite.

## 🚀 Cómo iniciar

### Requisitos
- Python 3.8 o superior
- Flask (`pip install flask`)

### Pasos
1. Descomprimí la carpeta `almacen`
2. Abrí una terminal en esa carpeta
3. Ejecutá: `python iniciar.py`
4. Se abre automáticamente en tu navegador: **http://127.0.0.1:5000**

---

## 📋 Módulos incluidos

| Módulo | Descripción |
|--------|-------------|
| 🏠 **Dashboard** | KPIs en tiempo real, alertas, gráfico de ventas |
| 📦 **Productos** | Catálogo completo con margen, IVA, código interno/barras |
| 📊 **Stock** | Control de niveles con alertas (Sin stock / Crítico / Bajo / Exceso) |
| 🛒 **Punto de Venta** | Ticket en pantalla, búsqueda por código o barras, múltiples pagos |
| 📝 **Historial Ventas** | Filtros por fecha, cliente, medio de pago |
| 🛍️ **Compras** | Ingreso de mercadería con actualización automática de stock |
| 💰 **Caja** | Apertura/cierre diario, gastos del día, historial 30 días |
| 💸 **Gastos** | Registro y clasificación (necesario / prescindible) |
| 👥 **CC Clientes** | Cuenta corriente con movimientos y vencimientos |
| 🏭 **CC Proveedores** | Facturas pendientes, pagos, alertas de vencimiento |
| 📈 **Estadísticas** | Gráficos ventas mensuales, semanales, medios de pago, temporadas |
| 🔍 **Análisis** | Rentabilidad, top productos, recomendaciones estacionales |
| ⚙️ **Configuración** | Datos del negocio, categorías, márgenes |

---

## 💳 Medios de pago soportados
- Efectivo
- Débito
- Crédito
- Transferencia
- QR / Billetera Virtual (Mercado Pago, etc.)
- Cuenta Corriente (registra automáticamente en CC del cliente)

## 🔫 Lector de código de barras
El sistema es **100% compatible** con lectores de barras USB (HID).  
No requiere configuración: al escanear, el código se ingresa directamente en el campo activo del Punto de Venta o en el formulario de productos.

## 💾 Base de datos
- Se usa **SQLite** — el archivo `almacen.db` se crea automáticamente
- No requiere servidor de base de datos
- Hacé backup periódico del archivo `almacen.db`

## 📊 Datos de ejemplo incluidos
- 25 productos (lácteos, bebidas, limpieza, infusiones, fiambres, etc.)
- ~700 ventas de los últimos 90 días
- 4 clientes de ejemplo
- 5 proveedores de ejemplo
- Facturas y gastos de demostración

---

## 🛠️ Primeros pasos reales

1. Entrá a **Configuración** y completá los datos de tu almacén (nombre, CUIT, dirección)
2. En **Productos**, eliminá los de ejemplo y cargá los tuyos
3. En **Stock**, ajustá los niveles actuales, mínimo y máximo de cada producto
4. Empezá a registrar ventas en **Punto de Venta**
5. Registrá compras en **Compras** para mantener el stock al día

---
Desarrollado con Python 3 · Flask · SQLite · Bootstrap 5 · Chart.js
# SisAlmacen
