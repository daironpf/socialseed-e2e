# E-commerce Broken - Lista de Bugs

Este servicio contiene **35 bugs intencionales** en un flujo completo de e-commerce: inventario, carrito, checkout, órdenes y cupones.

## 🔴 Bugs Críticos (Concurrencia/Negocio)

### BUG #15: Race Condition en Checkout
**Ubicación:** `app.py:160-195` - función `checkout()`
**Problema:** Verificación de stock fuera del lock, procesamiento dentro
**Impacto:** Doble venta del último item - dos usuarios pueden comprar el mismo producto cuando hay 1 en stock
**Caso:** Stock=1, Usuario A y B hacen checkout simultáneo → ambos compran el mismo item
**Solución:** Lock debe cubrir verificación Y procesamiento

### BUG #16: Verificación de Stock Inconsistente
**Ubicación:** `app.py:168-174` - función `checkout()`
**Problema:** Stock verificado antes del lock
**Impacto:** Stock puede cambiar entre verificación y procesamiento
**Solución:** Re-verificar stock dentro del lock antes de reducir

### BUG #19: Procesamiento Dentro del Lock
**Ubicación:** `app.py:189-193` - función `checkout()`
**Problema:** Lock cubre solo la actualización, no toda la operación
**Impacto:** Ventana de race condition entre verificación y lock
**Solución:** Lock desde la verificación de stock hasta el final

### BUG #20: Sin Re-verificación de Stock
**Ubicación:** `app.py:191` - función `checkout()`
**Problema:** No verificar stock nuevamente dentro del lock
**Impacto:** Puede vender más items de los disponibles
**Solución:** `if product["stock"] < item["quantity"]: raise Error`

### BUG #26: Sin Restaurar Stock al Cancelar
**Ubicación:** `app.py:248` - función `cancel_order()`
**Problema:** Cancela orden pero no devuelve items al inventario
**Impacto:** Pérdida de inventario - items desaparecen del sistema
**Caso:** Stock inicial: 5 → Orden de 2 → Cancelar → Stock sigue: 3 (debería ser 5)
**Solución:** Restaurar stock al cancelar

## 🟠 Bugs de Seguridad/Autorización

### BUG #9: Stock Expuesto
**Ubicación:** `app.py:85` - función `get_product()`
**Problema:** Expone cantidad exacta de stock en API pública
**Impacto:** Competencia puede monitorear inventario en tiempo real
**Solución:** Retornar "in_stock": true/false en lugar de número exacto

### BUG #24: Órdenes de Otros Usuarios Visibles
**Ubicación:** `app.py:215` - función `get_order()`
**Problema:** Cualquiera puede ver cualquier orden con el ID
**Impacto:** Violación de privacidad - datos de compra expuestos
**Solución:** Verificar `request.user_id == order["user_id"]`

### BUG #25: Cancelar Órdenes de Otros
**Ubicación:** `app.py:238` - función `cancel_order()`
**Problema:** No verificar ownership de la orden
**Impacto:** Cualquiera puede cancelar cualquier orden
**Solución:** Verificar usuario antes de cancelar

### BUG #30: Crear Productos Sin Autenticación
**Ubicación:** `app.py:275` - función `create_product()`
**Problema:** Endpoint admin accesible públicamente
**Impacto:** Cualquiera puede crear/modificar productos
**Solución:** Requerir autenticación de admin

### BUG #32: Crear Cupones Sin Autenticación
**Ubicación:** `app.py:292` - función `create_coupon()`
**Problema:** Cualquiera puede crear cupones ilimitados
**Impacto:** Descuentos fraudulentos
**Solución:** Requerir autenticación de admin

## 🟡 Bugs Funcionales - Carrito

### BUG #1: Carritos No Expiran
**Ubicación:** `app.py:20` - variable global `carts_db`
**Problema:** Carritos persisten indefinidamente en memoria
**Impacto:** Memory leak, carritos abandonados ocupan espacio
**Solución:** TTL (time-to-live) + limpieza periódica

### BUG #2: Precio No Congelado
**Ubicación:** `app.py:37-42` - función `calculate_cart_total()`
**Problema:** Usa precio actual del producto, no el precio cuando se agregó
**Impacto:** Si el precio sube, el carrito muestra precio nuevo (inesperado para usuario)
**Solución:** Guardar `price_at_add` en el item del carrito

### BUG #10: Carritos Sin Usuario
**Ubicación:** `app.py:108` - función `create_cart()`
**Problema:** No requerir user_id para crear carrito
**Impacto:** Carritos huérfanos en el sistema
**Solución:** Validar user_id obligatorio

### BUG #11: Carritos No Expiran (Individual)
**Ubicación:** `app.py:112-118` - función `create_cart()`
**Problema:** No campo `expires_at`
**Impacto:** Carrito creado hace meses sigue "activo"
**Solución:** Agregar expiración de 24-48 horas

### BUG #12: Sin Verificar Stock al Agregar
**Ubicación:** `app.py:132` - función `add_to_cart()`
**Problema:** Stock verificado solo en checkout, no al agregar
**Impacto:** Usuario puede agregar 100 items cuando hay solo 5
**Solución:** Verificar stock al agregar al carrito

### BUG #13: Quantity Negativo Reduce Items
**Ubicación:** `app.py:135-145` - función `add_to_cart()`
**Problema:** Quantity negativo reduce items del carrito
**Impacto:** Bug funcional - no debería aceptar quantity negativo
**Solución:** Validar quantity > 0

### BUG #23: Carrito No Se Limpia Después de Checkout
**Ubicación:** `app.py:195` - función `checkout()`
**Problema:** Items permanecen en carrito después de orden
**Impacto:** Usuario puede hacer checkout dos veces con el mismo carrito
**Solución:** Limpiar carrito después de orden exitosa

## 🟡 Bugs Funcionales - Cupones

### BUG #3: Cupón Sin Expiración
**Ubicación:** `app.py:49-57` - función `apply_coupon()`
**Problema:** No verificar `expires_at`
**Impacto:** Cupones "vencidos" siguen funcionando
**Solución:** Verificar fecha de expiración

### BUG #4: Cupón Reutilizable Infinitamente
**Ubicación:** `app.py:49-57` - función `apply_coupon()`
**Problema:** No tracking de uso por usuario o global
**Impacto:** Un cupón "único" puede usarse 1000 veces
**Solución:** Contador de usos por cupón

### BUG #5: Sin Mínimo de Compra
**Ubicación:** `app.py:49-57` - función `apply_coupon()`
**Problema:** No verificar `min_purchase`
**Impacto:** Cupón de $50 aplicado a compra de $5
**Solución:** Validar subtotal >= min_purchase

### BUG #6: Descuento Porcentual Sin Límite
**Ubicación:** `app.py:55-56` - función `apply_coupon()`
**Problema:** Descuento puede ser 100% o más
**Impacto:** Compra gratis o dinero "negativo"
**Solución:** Límite máximo de descuento (ej: 50%)

### BUG #7: Descuento Fijo Puede Resultar Negativo
**Ubicación:** `app.py:58-59` - función `apply_coupon()`
**Problema:** `total = total - discount` puede ser < 0
**Impacto:** Total negativo - el sistema "debe" dinero al cliente
**Caso:** Compra $30, cupón $50 → total -$20
**Solución:** `max(total - discount, 0)`

### BUG #27: Validación Sin Expiración
**Ubicación:** `app.py:267` - función `validate_coupon()`
**Problema:** No verificar expires_at en validación
**Impacto:** Validación dice "válido" pero en checkout falla (inconsistencia)
**Solución:** Consistente con BUG #3

### BUG #28: Validación Sin Usos Máximos
**Ubicación:** `app.py:267` - función `validate_coupon()`
**Problema:** No verificar max_uses
**Solución:** Contador de usos

### BUG #29: Validación Sin Mínimo
**Ubicación:** `app.py:267` - función `validate_coupon()`
**Problema:** No verificar min_purchase
**Solución:** Validar contra cart_total

### BUG #33: Cupón Sin Expiración (Definición)
**Ubicación:** `app.py:299-305` - función `create_coupon()`
**Problema:** No campo expires_at al crear
**Solución:** Agregar campo obligatorio

### BUG #34: Sin Usos Máximos (Definición)
**Ubicación:** `app.py:299-305` - función `create_coupon()`
**Problema:** No campo max_uses
**Solución:** Agregar campo

### BUG #35: Sin Mínimo de Compra (Definición)
**Ubicación:** `app.py:299-305` - función `create_coupon()`
**Problema:** No campo min_purchase
**Solución:** Agregar campo

## 🟡 Bugs Funcionales - Checkout/Órdenes

### BUG #8: Sin Paginación
**Ubicación:** `app.py:75-78` - función `list_products()`
**Problema:** Retorna todos los productos
**Impacto:** DoS si hay 10,000 productos
**Solución:** Implementar limit/offset

### BUG #14: Impuestos No Incluidos
**Ubicación:** `app.py:155-158` - función `get_cart()`
**Problema:** Siempre retorna tax=0
**Impacto:** Precio final incorrecto
**Solución:** Calcular impuestos basado en ubicación

### BUG #17: Cupón Aplicado Antes de Impuestos
**Ubicación:** `app.py:180-184` - función `checkout()`
**Problema:** Descuento aplicado a subtotal, luego impuestos sobre el descuento
**Impacto:** Impuestos calculados sobre monto menor (ilegal en muchos países)
**Caso:** $100 + 10% descuento = $90 + 8% impuesto = $97.2
**Correcto:** $100 + 8% impuesto = $108 - 10% = $97.2 (igual, pero concepto)
**Solución:** Impuestos sobre subtotal, luego descuento

### BUG #18: Tasa de Impuestos Fija
**Ubicación:** `app.py:187` - función `checkout()`
**Problema:** 8% fijo sin importar ubicación
**Impacto:** Impuestos incorrectos para diferentes estados/países
**Solución:** Calcular basado en dirección de envío

### BUG #21: Orden Marcada Como Completada Inmediatamente
**Ubicación:** `app.py:194` - función `checkout()`
**Problema:** Status "completed" sin pasar por procesamiento
**Impacto:** Flujo de estados incorrecto
**Solución:** Estados: pending → processing → completed

### BUG #22: Sin Tracking de Estados
**Ubicación:** `app.py:194-200` - función `checkout()`
**Problema:** No hay history de cambios de estado
**Impacto:** No auditoría
**Solución:** Agregar `status_history`

## 🟡 Bugs de Validación

### BUG #31: Precio de Producto Sin Validar
**Ubicación:** `app.py:283` - función `create_product()`
**Problema:** No validar price > 0
**Impacto:** Productos con precio negativo o cero
**Solución:** Validación de precio

## 🎯 Flujos de Testing Sugeridos

### Flujo 1: Compra Exitosa
1. Listar productos
2. Crear carrito
3. Agregar items
4. Ver carrito
5. Checkout con cupón
6. Ver orden

### Flujo 2: Race Condition de Stock
```python
# Dos requests simultáneos al último item
# Producto con stock=1
# Ambos usuarios agregan al carrito
# Ambos hacen checkout simultáneo
# BUG: Ambos podrían tener éxito
```

### Flujo 3: Cupón Vencido
```python
# Crear cupón vencido
# Intentar usarlo
# BUG: Funciona aunque esté vencido
```

### Flujo 4: Cancelar y Perder Stock
```python
# Crear orden con 2 items
# Verificar stock disminuye en 2
# Cancelar orden
# BUG: Stock no se restaura
```

### Flujo 5: Descuento Que Genera Total Negativo
```python
# Carrito con $30
# Aplicar cupón de $50
# BUG: Total = -$20
```

## 🛍️ Productos de Prueba

| ID | Nombre | Precio | Stock | Propósito |
|----|--------|--------|-------|-----------|
| prod_laptop | Laptop Gaming | $999.99 | 5 | Testing normal |
| prod_mouse | Mouse Inalámbrico | $29.99 | 10 | Testing múltiples |
| prod_keyboard | Teclado Mecánico | $79.99 | 3 | Testing stock bajo |

## 🎟️ Cupones de Prueba

| Código | Tipo | Valor | Propósito |
|--------|------|-------|-----------|
| SAVE10 | % | 10% | Descuento normal |
| DISCOUNT50 | $ | $50 | Testing total negativo |

## 🔗 Endpoints

### Productos
- `GET /api/v1/products` - Listar productos
- `GET /api/v1/products/<id>` - Ver producto

### Carrito
- `POST /api/v1/carts` - Crear carrito
- `GET /api/v1/carts/<id>` - Ver carrito
- `POST /api/v1/carts/<id>/items` - Agregar item

### Checkout
- `POST /api/v1/checkout` - Procesar compra

### Órdenes
- `GET /api/v1/orders/<id>` - Ver orden
- `POST /api/v1/orders/<id>/cancel` - Cancelar orden

### Cupones
- `POST /api/v1/coupons/validate` - Validar cupón

### Admin
- `POST /api/v1/admin/products` - Crear producto
- `POST /api/v1/admin/coupons` - Crear cupón
