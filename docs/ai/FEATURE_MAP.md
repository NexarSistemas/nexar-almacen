# Feature Map

Proyecto: Sistema de Gestión de Almacén  
Tecnología: Python + Flask + SQLite  

Este documento describe los módulos funcionales del sistema y cómo se relacionan entre sí.

Sirve para que desarrolladores y asistentes de IA entiendan rápidamente el funcionamiento del software.

---

# Vista general del sistema

El sistema está compuesto por los siguientes módulos principales:

1. Productos
2. Stock
3. Ventas
4. Compras
5. Clientes
6. Proveedores
7. Caja
8. Gastos
9. Cuentas Corrientes
10. Estadísticas
11. Importación de Productos
12. Configuración
13. Usuarios
14. Backup del sistema

---

# 1. Módulo de Productos

Responsabilidad:

Gestión del catálogo de productos.

Funciones principales:

- crear productos
- editar productos
- eliminar productos
- buscar productos
- asociar categoría
- registrar código de barras
- definir precio y costo

Archivos relacionados:

app.py  
database.py  
templates/productos.html  

Tablas relacionadas:

productos  
categorias  

---

# 2. Módulo de Stock

Responsabilidad:

Control del inventario.

Funciones:

- consultar stock actual
- alertas de stock mínimo
- actualización automática por ventas
- actualización automática por compras

Archivos relacionados:

database.py  
app.py  

Tablas relacionadas:

stock  
productos  

---

# 3. Módulo de Ventas

Responsabilidad:

Registro de ventas (Punto de Venta).

Funciones:

- seleccionar productos
- calcular total
- registrar venta
- registrar detalle de venta
- descontar stock
- registrar movimiento de caja

Archivos relacionados:

app.py  
templates/ventas.html  

Tablas relacionadas:

ventas  
ventas_detalle  
stock  

---

# 4. Módulo de Compras

Responsabilidad:

Registro de compras a proveedores.

Funciones:

- registrar proveedor
- registrar compra
- registrar detalle de compra
- actualizar stock

Archivos relacionados:

app.py  

Tablas relacionadas:

compras  
proveedores  
stock  

---

# 5. Módulo de Clientes

Responsabilidad:

Administrar clientes del comercio.

Funciones:

- registrar cliente
- editar cliente
- historial de compras
- cuentas corrientes

Tablas relacionadas:

clientes  

---

# 6. Módulo de Proveedores

Responsabilidad:

Administrar proveedores.

Funciones:

- registrar proveedor
- editar proveedor
- historial de compras

Tablas relacionadas:

proveedores  

---

# 7. Módulo de Caja

Responsabilidad:

Control del flujo de dinero.

Funciones:

- registrar ingresos
- registrar egresos
- ver historial de caja

Tablas relacionadas:

caja_historial  

---

# 8. Módulo de Gastos

Responsabilidad:

Registro de gastos operativos.

Ejemplos:

- alquiler
- electricidad
- internet
- proveedores menores

Tablas relacionadas:

gastos  

---

# 9. Módulo de Cuentas Corrientes

Responsabilidad:

Gestión de deudas y pagos de clientes.

Funciones:

- registrar deuda
- registrar pago
- consultar saldo

Tablas relacionadas:

cc_clientes_mov  
clientes  

---

# 10. Módulo de Estadísticas

Responsabilidad:

Generar información del negocio.

Ejemplos:

- ventas diarias
- ventas mensuales
- productos más vendidos
- ingresos totales

Datos utilizados:

ventas  
ventas_detalle  

---

# 11. Importación de Productos

Responsabilidad:

Importar productos desde fuentes externas.

Implementación:

OpenFoodFacts API.

Archivos relacionados:

openfoodfacts.py  
services/openfood_importer.py  

Funciones:

- buscar producto por código de barras
- importar datos automáticamente

---

# 12. Configuración

Responsabilidad:

Configuración general del sistema.

Ejemplos:

- nombre del comercio
- formato de ticket
- moneda

Tablas relacionadas:

config  

---

# 13. Usuarios

Responsabilidad:

Control de acceso al sistema.

Funciones:

- login
- gestión de usuarios
- roles

Tablas relacionadas:

usuarios  

---

# 14. Backup del sistema

Responsabilidad:

Respaldo de la base de datos.

Funciones:

- crear backup
- restaurar backup

Archivos relacionados:

app.py  

---

# Dependencias entre módulos

Productos → Stock  
Ventas → Stock  
Ventas → Caja  
Compras → Stock  
Clientes → Cuentas Corrientes  
Proveedores → Compras  

---

# Flujo típico de operación

Venta:

cliente selecciona productos  
→ calcular total  
→ registrar venta  
→ registrar detalle  
→ descontar stock  
→ registrar ingreso en caja  

---

# Flujo de compra

registrar proveedor  
→ registrar compra  
→ registrar detalle  
→ actualizar stock  

---

# Objetivo del sistema

Brindar un sistema simple y eficiente para:

- almacenes
- kioscos
- minimercados
- pequeños comercios

El diseño prioriza simplicidad, estabilidad y facilidad de mantenimiento.
