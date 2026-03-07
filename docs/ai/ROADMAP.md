# Roadmap del Proyecto

Proyecto: Sistema de Gestión de Almacén

Objetivo del roadmap:
Planificar la evolución del sistema en futuras versiones.

El sistema está pensado para pequeños comercios y debe
mantener simplicidad y estabilidad.

---

# Versión actual

Serie 1.x

Características principales:

- gestión de productos
- control de stock
- registro de ventas
- registro de compras
- clientes
- proveedores
- control de caja
- registro de gastos
- estadísticas básicas
- cuentas corrientes
- importación de productos
- backup del sistema

Tecnología actual:

Python  
Flask  
SQLite  

---

# Objetivos para versión 2.0

La versión 2 debe mejorar:

- organización del código
- funcionalidades comerciales
- experiencia de usuario

---

# Mejoras de arquitectura

Separar capas del sistema:

modelo (base de datos)  
servicios (lógica de negocio)  
controladores (rutas Flask)  
vistas (templates)

Objetivo:

facilitar mantenimiento y escalabilidad.

---

# Nuevas funcionalidades propuestas

## Historial de precios

Guardar cambios de precio de productos.

Tabla sugerida:

historial_precios

Campos:

producto_id  
precio_anterior  
precio_nuevo  
fecha  

---

## Movimientos de stock

Registrar cada cambio de stock.

Tabla sugerida:

movimientos_stock

Campos:

producto_id  
tipo_movimiento  
cantidad  
fecha  
referencia  

Tipos:

venta  
compra  
ajuste  

---

## Control de usuarios avanzado

Permitir distintos niveles de acceso.

Roles:

administrador  
cajero  
empleado  

Permisos:

- ver reportes
- registrar ventas
- modificar productos
- acceder a configuración

---

## Reportes avanzados

Agregar:

- ventas por día
- ventas por mes
- ventas por producto
- ganancias estimadas
- ranking de productos

---

## Alertas automáticas

Notificaciones para:

- stock mínimo
- productos sin ventas
- productos vencidos (si se implementa vencimiento)

---

# Mejoras en la interfaz

- interfaz más moderna
- dashboard más claro
- buscador rápido de productos
- acceso rápido a ventas

---

# Integraciones futuras

Posibles integraciones:

- lector de códigos de barras
- impresora térmica
- exportación a Excel
- API para integraciones externas

---

# Posible versión 3.0

La versión 3 podría incluir:

- soporte multiusuario real
- sistema multi-sucursal
- sincronización entre computadoras
- base de datos PostgreSQL
- versión web remota

---

# Objetivo final

Construir un sistema de gestión de almacén:

- simple
- rápido
- confiable
- fácil de mantener
- ampliable en el tiempo
