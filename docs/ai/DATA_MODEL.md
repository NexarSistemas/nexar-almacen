# Modelo de Datos

Proyecto: Sistema de Gestión de Almacén  
Base de datos: SQLite  
Archivo: almacen.db  

Este documento describe las tablas principales utilizadas por el sistema.

---

# Esquema general

El sistema se organiza en las siguientes áreas:

Productos
Ventas
Compras
Clientes
Proveedores
Caja
Gastos
Configuración
Usuarios
Historial del sistema

---

# Tabla: config

Configuración general del sistema.

| Campo | Tipo | Descripción |
|------|------|-------------|
clave | TEXT (PK) | nombre de configuración |
valor | TEXT | valor de la configuración |

Ejemplos:

- nombre_comercio
- moneda
- formato_ticket

---

# Tabla: usuarios

Usuarios que pueden acceder al sistema.

| Campo | Tipo | Descripción |
|------|------|-------------|
id | INTEGER PK | identificador |
username | TEXT | nombre de usuario |
password_hash | TEXT | contraseña en hash |
rol | TEXT | rol del usuario |
nombre_completo | TEXT | nombre visible |
activo | INTEGER | usuario activo |
created_at | TEXT | fecha creación |

Roles típicos:

- admin
- usuario

---

# Tabla: categorias

Categorías de productos.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
nombre | TEXT |
activa | INTEGER |

Ejemplos:

- Bebidas
- Almacén
- Limpieza

---

# Tabla: productos

Productos del inventario.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
codigo_interno | TEXT |
codigo_barras | TEXT |
descripcion | TEXT |
marca | TEXT |
categoria | TEXT |
unidad | TEXT |
por_peso | INTEGER |
costo | REAL |
precio_venta | REAL |
iva | TEXT |
activo | INTEGER |
created_at | TEXT |

Notas:

- `por_peso` indica si se vende por peso
- `unidad` puede ser Unidad, Kg, etc.

---

# Tabla: stock

Control de stock de productos.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
producto_id | INTEGER |
stock_actual | REAL |
stock_minimo | REAL |
stock_maximo | REAL |

Relación:

producto_id → productos.id

---

# Tabla: clientes

Registro de clientes.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
nombre | TEXT |
telefono | TEXT |
direccion | TEXT |
email | TEXT |
activo | INTEGER |

Se usa para:

- ventas
- cuentas corrientes

---

# Tabla: proveedores

Proveedores de mercadería.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
nombre | TEXT |
telefono | TEXT |
direccion | TEXT |
email | TEXT |
activo | INTEGER |

---

# Tabla: ventas

Registro de ventas.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
fecha | TEXT |
total | REAL |
metodo_pago | TEXT |
cliente_id | INTEGER |

Relaciones:

cliente_id → clientes.id

---

# Tabla: ventas_detalle

Detalle de productos vendidos.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
venta_id | INTEGER |
producto_id | INTEGER |
cantidad | REAL |
precio_unitario | REAL |
subtotal | REAL |

Relaciones:

venta_id → ventas.id  
producto_id → productos.id

---

# Tabla: compras

Registro de compras a proveedores.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
proveedor_id | INTEGER |
fecha | TEXT |
total | REAL |

Relación:

proveedor_id → proveedores.id

---

# Tabla: caja_historial

Movimientos de caja.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
fecha | TEXT |
tipo | TEXT |
monto | REAL |
descripcion | TEXT |

Tipos:

- ingreso
- egreso

---

# Tabla: gastos

Registro de gastos del comercio.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
fecha | TEXT |
concepto | TEXT |
monto | REAL |

Ejemplos:

- luz
- alquiler
- internet

---

# Tabla: cc_clientes_mov

Movimientos de cuenta corriente de clientes.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
cliente_id | INTEGER |
fecha | TEXT |
tipo | TEXT |
monto | REAL |
descripcion | TEXT |

Tipos:

- deuda
- pago

---

# Tabla: facturas_proveedores

Facturas registradas de proveedores.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
proveedor_id | INTEGER |
fecha | TEXT |
total | REAL |
numero_factura | TEXT |

---

# Tabla: barcode_blacklist

Lista negra de códigos de barras.

Se utiliza para evitar importar productos inválidos.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
barcode | TEXT |

---

# Tabla: changelog

Historial de versiones del sistema.

| Campo | Tipo |
|------|------|
id | INTEGER PK |
version | TEXT |
fecha | TEXT |
tipo | TEXT |
titulo | TEXT |
descripcion | TEXT |

---

# Relaciones principales

productos → stock  
ventas → ventas_detalle  
ventas → clientes  
compras → proveedores  
cc_clientes_mov → clientes  
facturas_proveedores → proveedores

---

# Reglas del sistema

1. El stock no debe ser negativo.
2. Una venta descuenta stock.
3. Una compra aumenta stock.
4. Las ventas registran movimientos de caja.
5. Las cuentas corrientes registran deudas y pagos.

---

# Posibles mejoras futuras

- tabla movimientos_stock
- historial de precios
- sistema de usuarios avanzado
- control de sucursales
