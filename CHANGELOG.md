# Changelog — Nexar Almacen

Todas las versiones publicadas de este proyecto están documentadas aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es).
Versionado semántico: `MAJOR.MINOR.PATCH` según política oficial del proyecto.

---

## [1.7.7] - 2026-04-22 - Icono en menu de aplicaciones

### Corregido
- El paquete Linux vuelve a usar `Icon=nexar-almacen` en la entrada de aplicaciones e instala el PNG tambien en el tema `hicolor`, evitando que GNOME muestre la rueda generica en el menu.
- Se conserva el alias `nexar_almacen` para que el dock y caches previos sigan resolviendo el icono.

---

## [1.7.6] - 2026-04-22 - Icono y nombre en Ubuntu Dock

### Cambiado
- El paquete Linux ahora instala y ejecuta el binario PyInstaller `NexarAlmacen`, igual que Nexar Tienda, en lugar de lanzar `python3 iniciar.py`.
- El build Linux compila `dist/NexarAlmacen` antes de generar el `.deb` y empaqueta las dependencias Qt/PySide6 necesarias para la ventana nativa.

### Corregido
- La entrada de escritorio de Ubuntu ahora usa `Name=Nexar Almacen`, `Icon=nexar_almacen` y `StartupWMClass=NexarAlmacen` para que el dock muestre el icono y nombre correctos.

---

## [1.7.5] - 2026-04-21 - Ventana completa y cierre seguro

### Cambiado
- Nexar Almacen ahora abre maximizado en ventana nativa, con la misma presentacion inicial que Nexar Tienda.

### Corregido
- Al cerrar la ventana nativa con la X, el sistema bloquea el cierre si hay una sesion activa y muestra un aviso para cerrar sesion primero.
- El cierre de sesion y el apagado limpian el estado desktop para evitar avisos incorrectos despues de salir.

---

## [1.7.4] - 2026-04-21 - Licencias, usuarios y actualizaciones

### Agregado
- Integracion del flujo de licencias online con solicitud, activacion por clave, cache local y planes `BASICA` / `MENSUAL_FULL`.
- Creacion obligatoria del primer usuario administrador y configuracion de recuperacion de contrasena.
- Formulario de soporte online desde Ayuda con envio a Supabase.
- Pantalla de actualizacion online con descarga de instaladores desde GitHub Releases, respaldo previo, instalacion y estado de reinicio.

### Cambiado
- El plan anterior `PRO` se normaliza como `MENSUAL_FULL`, igual que en Nexar Tienda.
- El build de Windows y Linux empaqueta `.env`, `nexar_licencias`, servicios de licencia y dependencias desde `requirements.txt`.
- El identificador de equipo ahora diferencia producto para permitir varias apps Nexar en la misma maquina.

---

## [1.7.3] — 2026-04-08 — Corrección de arranque y usuarios

### Corregido
- **Carga de SECRET_KEY**: Se corrigió el flujo en GitHub Actions para generar un archivo `.env` físico durante el proceso de build, asegurando que el ejecutable empaquetado pueda cargar la clave y no lance un `RuntimeError`.
- **Usuarios predeterminados**: Se corrigió el seeding de la base de datos para que los usuarios `admin` y `vendedor` usen el hash de `werkzeug.security`, permitiendo el inicio de sesión en instalaciones limpias.
- **Launcher**: Se añadió `python-dotenv` a la verificación de dependencias en `iniciar.py`.

---

## [1.7.3] — 2026-04-08 — Corrección de arranque y usuarios

### Corregido
- **Carga de SECRET_KEY**: Se corrigió el flujo en GitHub Actions para generar un archivo `.env` físico durante el proceso de build, asegurando que el ejecutable empaquetado pueda cargar la clave y no lance un `RuntimeError`.
- **Usuarios predeterminados**: Se corrigió el seeding de la base de datos para que los usuarios `admin` y `vendedor` usen el hash de `werkzeug.security`, permitiendo el inicio de sesión en instalaciones limpias.
- **Launcher**: Se añadió `python-dotenv` a la verificación de dependencias en `iniciar.py`.

---

## [1.7.2] — 2026-04-08 — Mejoras de seguridad

### Mejorado
- **Aplicación del estándar NEXAR_SECRET_KEY_STANDARD**: Se ha refactorizado el manejo de `SECRET_KEY` en `app.py` para cumplir con el estándar, asegurando que siempre se cargue desde variables de entorno, eliminando valores hardcodeados y generando un `RuntimeError` si no está definida. Esto mejora la seguridad y consistencia en la gestión de claves secretas.

### Corregido
- **Errores de build**: Scripts de build ahora manejan la ausencia de `keys/` sin fallar.
- **Compatibilidad**: La app funciona en runtime con `PUBLIC_KEY` o archivo fallback.

---

## [1.7.1] — 2026-03-29 — Mejora de seguridad y build

### Agregado
- **Llave pública desde variable de entorno**: La clave pública RSA ahora se carga desde `PUBLIC_KEY` (GitHub Actions secrets), eliminando archivos sensibles del repositorio.
- **Fallback robusto**: Si no hay `PUBLIC_KEY`, busca `keys/public_key.asc` en el directorio de la app (para builds .deb y .exe).
- **Builds mejorados**: 
  - Linux (.deb): Crea `keys/public_key.asc` desde `PUBLIC_KEY` si no existe la carpeta `keys`.
  - Windows (Inno Setup): Incluye `keys/public_key.asc` generado desde `PUBLIC_KEY` en CI.
  - PyInstaller: Bundle opcional de `keys` o archivo temporal desde env var.

---

## [1.7.0] — 2026-03-28 — Mejoras y correcciones

### Agregado
- **Pipeline de CI/CD inteligente**: automatización de releases basada en CHANGELOG, firma GPG de binarios, y creación automática de tags y releases en GitHub Actions.

### Corregido
- Enlaces a proveedores en stock.html corregidos para apuntar a /cc_proveedores.

---

## [1.6.0] — 2026-03-19 — Nueva función

### Agregado
- **Sistema de tiers de licencia**: Plan Básico (pago único U$D 30) y Plan Pro (mensual U$D 6).
- **Límites por tier en Plan Básico**: máx 200 productos desde OpenFoodFacts, 100 clientes, 50 proveedores. Sin categorías personalizadas ni actualizaciones.
- **Plan Pro**: ilimitado en todos los recursos + estadísticas históricas + análisis de rentabilidad + actualizaciones incluidas + soporte prioritario.
- **Al cancelar Pro**: el sistema baja automáticamente a Básico sin perder datos cargados.
- **Estadísticas y análisis bloqueados** en Plan Básico con llamador visual a Pro.
- **Anti-reinstall**: archivo `telemetry.bin` en AppData/AppData local que preserva la fecha de inicio de demo aunque se borre la base de datos. El contenido está codificado y vinculado al machine_id.
- **Pantalla de licencia renovada**: muestra tier activo, barras de uso actual (productos OFF, clientes, proveedores) y comparativa clara entre planes.
- **Generador de licencias actualizado**: nuevos tipos `PRO_MONO` y `PRO_MULTI_3` con campos `tier` y `expires_at` en el payload RSA firmado.

---

## [1.5.5] — 2026-03-18 — Corrección

### Corregido
- Bug: el botón "Ver Ticket" en Punto de Venta y el link de ticket en Historial de Ventas tenían `target="_blank"`, lo que hacía que se abrieran en el navegador externo del sistema. Al hacerlo, el navegador no tenía la sesión activa de la app y pedía login. Ahora ambos abren el ticket dentro de la misma ventana de la aplicación.

---

## [1.5.4] — 2026-03-15
### Mejora de seguridad
- **Sistema de licencias RSA**: reemplaza validación HMAC por firma digital RSA de 2048 bits
- **Token Base64**: el cliente pega el token en la pantalla de licencia (sin archivos adjuntos)
- **Soporte MONO y MULTI**: licencias para 1, 3 o 10 PCs con hardware IDs firmados
- **Proceso de transferencia**: cambio de PC sin perder la licencia adquirida
- **Retrocompatibilidad**: la demo de 30 días funciona igual que antes

---

## [1.5.3] — 2026-03-07 — Corrección

### Corregido
- Bug crítico: rutas `/apagar` y `/apagar_rapido` usaban `date.today().isoformat()` (formato `YYYY-MM-DD`) para escribir `sessions_invalidated_at`, mientras que el check de login comparaba contra `datetime.now().isoformat()` (formato `YYYY-MM-DDTHH:MM:SS`). La comparación de strings fallaba siempre, causando loop de login al reiniciar después de apagar desde la app. Mismo bug que se corrigió en 1.5.1 pero quedó sin aplicar en las rutas de apagado.
- Fallback de versión en `app.py` e `iniciar.py` actualizado a `1.5.3`.
- Comentario de encabezado en `iniciar.py` actualizado a v1.5.3.
- `_seed_changelog` en `database.py` incluye ahora entradas de versiones 1.5.2 y 1.5.3.

---

## [1.5.2] — 2026-03-07 — Mejoras

### Mejoras
- Integración correcta de favicon mediante Flask (`/favicon.ico`)
- Iconos movidos a `static/icons/`
- Mejora en organización de archivos estáticos

---

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
- Importación masiva con servicio dedicado `services/openfood_importer.py`.
- Modo demo con límite de 30 días desde la instalación.
- Pantalla de licencia (`/licencia`) para activar el sistema con clave.

---

## [1.2.1] — 2026-02-24 — Corrección

### Corregido
- Sidebar con scroll vertical para pantallas pequeñas.
- `check_deps` robusto ante entornos sin pip.
- Módulo de respaldos automáticos con scheduler configurable.
- Botón de apagado del sistema desde el menú.

---

## [1.2.0] — 2026-02-01 — Nueva función

### Agregado
- Dashboard con gráficos de ventas mensuales (Chart.js).
- Módulo de estadísticas: ventas por mes, semana, medio de pago y temporada.
- Módulo de análisis de rentabilidad: top productos, bottom, margen estimado.
- Gestión de múltiples usuarios con roles admin/vendedor.
- Cierre de sesión automático al apagar. Sistema de actualización sin reinstalar. Ventana independiente tipo app nativa. Botón apagar en login.

---

## [1.1.0] — 2026-01-15 — Nueva función

### Agregado
- Módulo CC Clientes: cuenta corriente con movimientos y alertas de deuda.
- Módulo CC Proveedores: facturas pendientes, pagos, alertas de vencimiento.

---

## [1.0.0] — 2026-01-01 — Lanzamiento

### Agregado
- Primera versión de Nexar Almacen.
- Módulos de Ventas, Stock, Caja y Gastos.
