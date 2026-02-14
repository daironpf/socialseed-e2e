# 💳 Payment Service Broken

Servicio de procesamiento de pagos intencionalmente roto para aprender sobre concurrencia, idempotencia y transacciones.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servicio
python app.py
```

El servicio estará disponible en: `http://localhost:5002`

## 📖 Documentación

- **[BUGS.md](BUGS.md)** - Lista completa de 31 bugs intencionales

## 🎯 Objetivos de Aprendizaje

1. **Concurrencia**: Race conditions, deadlocks, locks
2. **Idempotencia**: Claves de idempotencia, operaciones atómicas
3. **Transacciones**: Consistencia de datos, rollback
4. **Precisión decimal**: Manejo de dinero con Decimal
5. **Seguridad financiera**: Validaciones, límites, autorización

## 🧪 Usuarios de Prueba

| User ID | Balance | Propósito |
|---------|---------|-----------|
| user_1  | $1000.00 | Testing normal |
| user_2  | $500.00  | Testing de límites |
| user_3  | $50.00   | Testing insuficiente |

## 🔗 Endpoints

### Pagos
- `POST /api/v1/payments` - Crear pago (Header: Idempotency-Key)
- `GET /api/v1/payments/<id>` - Obtener pago
- `GET /api/v1/payments?user_id=xxx` - Listar pagos
- `POST /api/v1/payments/<id>/refund` - Reembolsar pago
- `POST /api/v1/payments/<id>/void` - Anular pago

### Usuarios
- `GET /api/v1/users/<id>/balance` - Consultar balance
- `POST /api/v1/users/<id>/deposit` - Depositar fondos

### Admin
- `GET /api/v1/admin/payments/report` - Reporte de transacciones

## 🎮 Ejemplos de Uso

### Crear un pago
```bash
curl -X POST http://localhost:5002/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "user_id": "user_1",
    "amount": "100.00",
    "currency": "USD"
  }'
```

### Reembolsar (Bug #15)
```bash
# Intentar reembolsar el mismo pago múltiples veces
curl -X POST http://localhost:5002/api/v1/payments/pay_xxx/refund \
  -H "Content-Type: application/json" \
  -d '{"reason": "Customer request"}'
```

### Probar Race Condition (Bug #8)
```bash
# Ejecutar dos veces simultáneamente (user_3 solo tiene $50)
curl -X POST http://localhost:5002/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_3", "amount": "30.00"}' &
curl -X POST http://localhost:5002/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_3", "amount": "30.00"}' &
wait
```

### Monto negativo (Bug #6)
```bash
curl -X POST http://localhost:5002/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_1",
    "amount": "-100.00",
    "currency": "USD"
  }'
```

## 🐛 Lista de Bugs (Resumen)

### Concurrencia (5 bugs)
- #8, #9, #10: Race conditions en pagos
- #18: Race condition en reembolsos

### Seguridad (9 bugs)
- #4, #12, #14: Idempotencia
- #15, #16: Reembolsos
- #25, #28: Autorización

### Funcionales (17 bugs)
- Precisión decimal, validaciones, paginación

Ver [BUGS.md](BUGS.md) para detalles completos.

## 🧪 Tests Sugeridos

### Test de Concurrencia
```python
async def test_race_condition_double_spending(page):
    """Dos pagos simultáneos no deberían superar el balance."""
    # Crear dos pagos de $30 cada uno para user_3 (balance: $50)
    # Ambos deberían fallar, pero por el race condition uno podría pasar
```

### Test de Idempotencia
```python
async def test_idempotent_payment(page):
    """Mismo idempotency key debería retornar mismo pago."""
    # BUG: Actualmente retorna error 409 en lugar del pago original
```

### Test de Monto Negativo
```python
async def test_negative_amount_rejected(page):
    """Montos negativos deberían ser rechazados."""
    # BUG: Permite montos negativos (el usuario gana dinero)
```

## 🔧 Cómo Ejecutar Tests

```bash
# Inicializar proyecto
e2e init

# Configurar e2e.conf
# services:
#   payment-service:
#     name: payment-service
#     base_url: http://localhost:5002
#     health_endpoint: /health

# Ejecutar tests
e2e run
```

## 📚 Recursos

- [Decimal en Python](https://docs.python.org/3/library/decimal.html)
- [Race Conditions](https://en.wikipedia.org/wiki/Race_condition)
- [Idempotency Keys](https://stripe.com/docs/api/idempotent_requests)
- [Tutorial de Concurrencia](../../tutorials/01-getting-started/)

## 🆘 Troubleshooting

### "Insufficient funds"
- Verifica el balance con `GET /api/v1/users/<id>/balance`
- user_3 solo tiene $50.00

### "Duplicate idempotency key"
- Cambia el header `Idempotency-Key` a uno único
- O usa el bug #4 para ver el comportamiento incorrecto

## 📖 Licencia

Parte del playground de SocialSeed E2E para fines educativos.
