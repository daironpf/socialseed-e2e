# 🛒 E-commerce Broken

Aplicación de e-commerce completa con bugs en flujos end-to-end: inventario, carrito, checkout, cupones y órdenes.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servicio
python app.py
```

El servicio estará disponible en: `http://localhost:5003`

## 📖 Documentación

- **[BUGS.md](BUGS.md)** - Lista completa de 35 bugs intencionales

## 🎯 Objetivos de Aprendizaje

1. **Flujos E2E**: Testing de flujos completos de usuario
2. **Gestión de estado**: Carrito, órdenes, inventario
3. **Concurrencia**: Race conditions en e-commerce
4. **Cálculos financieros**: Impuestos, descuentos, totales
5. **State machines**: Ciclo de vida de una orden

## 🛍️ Productos de Prueba

| ID | Nombre | Precio | Stock |
|----|--------|--------|-------|
| prod_laptop | Laptop Gaming | $999.99 | 5 |
| prod_mouse | Mouse Inalámbrico | $29.99 | 10 |
| prod_keyboard | Teclado Mecánico | $79.99 | 3 |

## 🎟️ Cupones de Prueba

| Código | Tipo | Valor |
|--------|------|-------|
| SAVE10 | Porcentaje | 10% |
| DISCOUNT50 | Fijo | $50 |

## 🔗 Endpoints

### Productos
- `GET /api/v1/products` - Listar productos
- `GET /api/v1/products/<id>` - Ver producto

### Carrito
- `POST /api/v1/carts` - Crear carrito
- `GET /api/v1/carts/<id>` - Ver carrito con totales
- `POST /api/v1/carts/<id>/items` - Agregar item (product_id, quantity)

### Checkout
- `POST /api/v1/checkout` - Procesar compra (cart_id, coupon_code?)

### Órdenes
- `GET /api/v1/orders/<id>` - Ver orden
- `POST /api/v1/orders/<id>/cancel` - Cancelar orden

### Cupones
- `POST /api/v1/coupons/validate` - Validar cupón (code, cart_total)

### Admin
- `POST /api/v1/admin/products` - Crear producto
- `POST /api/v1/admin/coupons` - Crear cupón

## 🎮 Ejemplos de Uso

### Flujo completo de compra
```bash
# 1. Ver productos
curl http://localhost:5003/api/v1/products

# 2. Crear carrito
curl -X POST http://localhost:5003/api/v1/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123"}'

# 3. Agregar items al carrito
curl -X POST http://localhost:5003/api/v1/carts/cart_xxx/items \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod_laptop", "quantity": 1}'

# 4. Ver carrito
curl http://localhost:5003/api/v1/carts/cart_xxx

# 5. Checkout
curl -X POST http://localhost:5003/api/v1/checkout \
  -H "Content-Type: application/json" \
  -d '{"cart_id": "cart_xxx", "coupon_code": "SAVE10"}'
```

### Probar Race Condition (Bug #15)
```bash
# Dos terminales simultáneos - último item en stock (prod_keyboard tiene 3)
# Terminal 1
curl -X POST http://localhost:5003/api/v1/checkout \
  -H "Content-Type: application/json" \
  -d '{"cart_id": "cart_1", "items": [{"product_id": "prod_keyboard", "quantity": 1}]}' &

# Terminal 2
curl -X POST http://localhost:5003/api/v1/checkout \
  -H "Content-Type: application/json" \
  -d '{"cart_id": "cart_2", "items": [{"product_id": "prod_keyboard", "quantity": 1}]}' &

wait
# BUG: Ambos podrían tener éxito aunque solo hay 1 en stock
```

### Probar Total Negativo (Bug #7)
```bash
# Carrito con $30, cupón de $50
curl -X POST http://localhost:5003/api/v1/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "cart_xxx",
    "coupon_code": "DISCOUNT50"
  }'
# BUG: Total = -$20
```

### Probar Pérdida de Stock (Bug #26)
```bash
# Crear orden
curl -X POST http://localhost:5003/api/v1/checkout \
  -d '{"cart_id": "cart_xxx"}'
# Orden creada: ord_yyy

# Cancelar orden
curl -X POST http://localhost:5003/api/v1/orders/ord_yyy/cancel

# Verificar stock del producto - BUG: No se restauró!
curl http://localhost:5003/api/v1/products/prod_laptop
```

## 🐛 Lista de Bugs (Resumen)

### Concurrencia (5 bugs)
- #15, #16, #19, #20: Race conditions en checkout
- #26: Sin restaurar stock al cancelar

### Seguridad (6 bugs)
- #9, #24, #25: Exposición de datos
- #30, #32: Endpoints admin sin auth

### Carrito (7 bugs)
- #1, #2, #10, #11, #12, #13, #23

### Cupones (10 bugs)
- #3, #4, #5, #6, #7, #27, #28, #29, #33, #34, #35

### Funcionales (7 bugs)
- #8, #14, #17, #18, #21, #22, #31

Ver [BUGS.md](BUGS.md) para detalles completos.

## 🧪 Tests Sugeridos

### Test de Flujo E2E
```python
async def test_complete_purchase_flow(page):
    """Flujo completo: productos → carrito → checkout → orden."""
    # Listar productos
    # Crear carrito
    # Agregar items
    # Checkout
    # Verificar orden creada
```

### Test de Race Condition
```python
async def test_concurrent_checkout_race_condition(page):
    """Dos usuarios intentan comprar el último item."""
    # Producto con stock=1
    # Usuario A crea carrito con el item
    # Usuario B crea carrito con el item
    # Ambos hacen checkout simultáneamente
    # Solo uno debería tener éxito
    # BUG: Ambos podrían tener éxito
```

### Test de Cálculo de Total
```python
async def test_total_calculation_with_coupon(page):
    """Total no debería ser negativo con cupón grande."""
    # Carrito: $30
    # Cupón: $50
    # Total esperado: $0
    # BUG: Total = -$20
```

## 🔧 Cómo Ejecutar Tests

```bash
# Inicializar proyecto
e2e init

# Configurar e2e.conf
# services:
#   ecommerce:
#     name: ecommerce
#     base_url: http://localhost:5003
#     health_endpoint: /health

# Ejecutar tests
e2e run
```

## 📚 Recursos

- [Patrones de E-commerce](https://docs.example.com/ecommerce-patterns)
- [Testing de Concurrencia](https://docs.example.com/concurrency-testing)
- [State Machines](https://docs.example.com/state-machines)

## 🆘 Troubleshooting

### "Insufficient stock"
- Verificar stock: `GET /api/v1/products/<id>`
- prod_keyboard solo tiene 3 unidades

### "Cart is empty"
- Agregar items antes de checkout
- Usar el cart_id correcto

### "Invalid coupon"
- Códigos válidos: SAVE10, DISCOUNT50
- Diferencia mayúsculas/minúsculas

## 📖 Licencia

Parte del playground de SocialSeed E2E para fines educativos.
