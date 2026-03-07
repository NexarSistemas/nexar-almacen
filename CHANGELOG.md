# Changelog — Sistema de Gestión para Almacenes

Todas las versiones publicadas de este proyecto están documentadas aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es).
Versionado semántico: `MAJOR.MINOR.PATCH` según política oficial del proyecto.

---
## 1.5.2 - 2026-03-07

### Mejoras
- Integración correcta de favicon mediante Flask (`/favicon.ico`)
- Iconos movidos a `static/icons/`
- Mejora en organización de archivos estáticos

## [1.5.1] — 2026-03-05 — Corrección

### Corregido
- Bug crítico: login_date se guardaba como fecha (`YYYY-MM-DD`) y sessions_invalidated_at como datetime completo (`YYYY-MM-DDTHH:MM:SS`). La comparación de strings hacía que el login quedara en loop infinito en el segundo arranque. Ahora ambos valores usan `datetime.now().isoformat()`.
- `iniciar.py` reescrito: import de `importlib.util` directo al inicio, `webview.start()` en el hilo principal (requerido por macOS/Windows), cierre limpio sin dependencias del entorno.

---

## [1.5.0] — 2026-03-02 — Nueva función

### Agregado
- Puerto aleatorio libre (rango 5100–5999) para evitar conflictos con otras aplicaciones Flask. Se guarda en `.port`.
- Ventana nativa independiente usando `pywebview` (se instala automáticamente en background). Si no está disponible, usa el navegador como fallback.
- Al cerrar el sistema (Ctrl+C, botón apagar, o cerrar ventana nativa) se invalidan todas las sesiones activas: el próximo inicio requiere nuevo login.
- Ruta `/apagar_rapido` para cerrar el sistema desde la pantalla de login sin estar autenticado.
- Sección de **Actualización del sistema** (`/actualizacion`): permite aplicar un ZIP con la nueva versión sin reinstalar. Nunca sobrescribe `almacen.db`.
- Botón "Apagar sistema" visible en la pantalla de login.
- Link "Actualización" en el menú lateral.

---

## [1.4.0] — 2026-02-27 — Nueva función

### Agregado
- Filtro de barcodes: solo se importan prefijos argentinos `779` y `780` desde OpenFoodFacts.
- Filtro anti-basura: descarta productos cuya descripción es el barcode mismo, contiene solo caracteres especiales (`---`, `???`) o tiene menos de 3 caracteres alfanuméricos reales.
- **Lista Negra de Barcodes** (`/blacklist`): pantalla para agregar, ver y eliminar barcodes bloqueados. Los barcodes bloqueados no se reimportan nunca.
- Botón "Bloquear y desactivar" en el catálogo de productos (ícono ☠): desactiva el producto y bloquea su barcode en un solo clic.
- Proveedor habitual en el modal de Stock: campo con `<datalist>` conectado a los proveedores cargados en el sistema.
- Alias `/punto_venta` → `/venta` (ambas rutas funcionan).
- Link "Lista Negra" en el menú lateral.

### Corregido
- Error 404 al acceder a `/punto_venta` (la ruta solo existía como `/venta`).

---

## [1.3.0] — 2026-02-27 — Nueva función

### Agregado
- Integración con API **OpenFoodFacts**: importación de productos reales argentinos con barcode, nombre, marca y categoría asignada automáticamente.
- Módulo `services/openfood_importer.py` standalone con funciones `import_products()` y `update_products()`.
- Comandos CLI: `flask import-products` y `flask update-products`.
- Pantalla **Importar Productos** (`/productos/importar`) con 3 opciones: dataset local, importación OFF, actualización.
- Búsqueda de producto por barcode en tiempo real desde la pantalla de importación.
- Sistema de **demo por tiempo**: 30 días desde la primera instalación (fecha fijada una sola vez, nunca se resetea).
- Changelog visible en la aplicación (`/changelog` y `/acerca`).

---

## [1.2.1] — 2026-02-24 — Corrección

### Corregido
- Sidebar con scroll cuando el menú supera la altura de la pantalla.
- `check_deps()` robusto con fallback para entornos sin `importlib.util`.
- Encoding UTF-8 en instaladores.

### Agregado
- Módulo de **respaldos automáticos** programables desde Configuración.
- Botón de **apagado del sistema** desde el menú (para cerrar el servidor Flask limpiamente).

---

## [1.2.0] — 2026-02-01 — Nueva función

### Agregado
- Dashboard con gráficos de ventas diarios/semanales/mensuales.
- Módulo de **Estadísticas** con análisis por temporada, medio de pago y tendencia.
- Módulo de **Análisis de rentabilidad**: top productos, margen por categoría, recomendaciones.
- Gestión de **Usuarios** con roles: `admin` y `usuario`. El admin puede crear, editar y desactivar usuarios.

---

## [1.1.0] — 2026-01-15 — Nueva función

### Agregado
- **Cuenta Corriente Clientes**: registro de movimientos, saldo, alertas de deuda.
- **Cuenta Corriente Proveedores**: facturas pendientes, pagos, alertas de vencimiento a 30 días.
- Integración automática: las ventas con medio "Cuenta Corriente" se registran en la CC del cliente seleccionado.

---

## [1.0.0] — 2026-01-01 — Lanzamiento inicial

### Incluido
- Módulos: Productos, Stock, Punto de Venta, Historial de Ventas, Compras, Caja, Gastos, Configuración.
- Base de datos SQLite sin servidor.
- Compatibilidad con lectores de barras USB (HID).
- Múltiples medios de pago: Efectivo, Débito, Crédito, Transferencia, QR/Billetera Virtual, Cuenta Corriente.
- Ticket de venta en pantalla.
- Alertas de stock: Sin Stock, Crítico, Bajo, Exceso.
- Instalación portable: solo requiere Python 3.8+ y `pip install flask openpyxl reportlab`.
