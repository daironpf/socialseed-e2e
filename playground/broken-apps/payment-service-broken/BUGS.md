# Payment Service Broken - Lista de Bugs

Este servicio contiene **31 bugs intencionales** relacionados con procesamiento de pagos, concurrencia e idempotencia.

## 🔴 Bugs Críticos (Seguridad/Concurrencia)

### BUG #8: Race Condition en Verificación de Balance
**Ubicación:** `app.py:95-99` - función `create_payment()`
**Problema:** Verifica balance fuera del lock, luego procesa dentro del lock
**Impacto:** Doble gasto posible - dos requests simultáneos pueden superar el balance
**Caso:** User tiene $100, dos pagos de $60 simultáneos → ambos exitosos → balance -$20
**Solución:** Verificar balance DENTRO del lock

### BUG #9: Race Condition en Procesamiento
**Ubicación:** `app.py:101-125` - función `create_payment()`
**Problema:** Ventana de tiempo entre verificación y procesamiento
**Impacto:** Condiciones de carrera en pagos simultáneos
**Solución:** Lock debe cubrir toda la operación atómica

### BUG #10: Doble Verificación Omitida
**Ubicación:** `app.py:108` - función `create_payment()`
**Problema:** No re-verificar balance dentro del lock
**Impacto:** Balance puede cambiar entre verificación inicial y procesamiento
**Solución:** Re-verificar `users_balance[user_id] >= amount` dentro del lock

### BUG #15: Reembolsos Múltiples
**Ubicación:** `app.py:160` - función `refund_payment()`
**Problema:** No verificar si el pago ya fue reembolsado
**Impacto:** Reembolsar el mismo pago múltiples veces → pérdida de dinero
**Caso:** Pago de $100 → reembolsar 5 veces → $500 reembolsados
**Solución:** Agregar campo `refunded` al payment y verificar antes

### BUG #18: Race Condition en Reembolso
**Ubicación:** `app.py:173-180` - función `refund_payment()`
**Problema:** Similar a #8, operación no atómica
**Impacto:** Reembolsos simultáneos pueden procesarse múltiples veces
**Solución:** Lock + verificación de estado

## 🟠 Bugs de Seguridad Media

### BUG #4: Idempotencia Inconsistente
**Ubicación:** `app.py:61-67` - función `create_payment()`
**Problema:** Solo verifica si key existe, no retorna el pago original
**Impacto:** Cliente no puede recuperar el pago original si repite la request
**Solución:** Si key existe, retornar el pago original en lugar de error

### BUG #12: Idempotency Key Expuesto
**Ubicación:** `app.py:120` - función `create_payment()`
**Problema:** Almacena key sin encriptar en la base de datos
**Impacto:** Si hay brecha de seguridad, se filtran keys sensibles
**Solución:** Hashear la key antes de almacenar

### BUG #14: Idempotency Key en Respuesta
**Ubicación:** `app.py:137` - función `get_payment()`
**Problema:** Incluye idempotency_key en la respuesta JSON
**Impacto:** Expone información sensible que podría usarse para ataques
**Solución:** Excluir campos sensibles de la respuesta

### BUG #16: Reembolso Sin Autorización
**Ubicación:** `app.py:160` - función `refund_payment()`
**Problema:** Cualquiera puede reembolsar cualquier pago
**Impacto:** Reembolsos fraudulentos
**Solución:** Verificar que el request venga del dueño del pago o admin

### BUG #25: Balance Expuesto
**Ubicación:** `app.py:193` - función `get_balance()`
**Problema:** Cualquiera puede consultar balance de cualquier usuario
**Impacto:** Violación de privacidad
**Solución:** Requerir autenticación del dueño del balance

### BUG #28: Admin Endpoint Sin Autenticación
**Ubicación:** `app.py:207` - función `generate_report()`
**Problema:** Reporte admin accesible sin autenticación
**Impacto:** Información financiera sensible expuesta
**Solución:** Requerir autenticación de administrador

## 🟡 Bugs Funcionales

### BUG #1: Validación de Monto Débil
**Ubicación:** `app.py:33-38` - función `validate_amount()`
**Problema:** Acepta notación científica y formatos extraños
**Caso:** "1e2" se convierte en 100.00, "Infinity" es válido
**Solución:** Validar formato decimal estándar

### BUG #2: Precisión Decimal Infinita
**Ubicación:** `app.py:36` - función `validate_amount()`
**Problema:** No limitar cantidad de decimales
**Caso:** 0.00000000000000000001 es válido
**Impacto:** Problemas de redondeo y almacenamiento
**Solución:** Limitar a 2 decimales para moneda

### BUG #3: Error de Precisión en Comisión
**Ubicación:** `app.py:43-47` - función `calculate_fee()`
**Problema:** Usa float para cálculo intermedio
**Caso:** $10.00 → fee calculado con error de precisión float
**Solución:** Usar Decimal para todo el cálculo

### BUG #6: Montos Negativos Permitidos
**Ubicación:** `app.py:77` - función `create_payment()`
**Problema:** No validar monto mínimo > 0
**Caso:** Monto -$100 → el usuario GANA dinero
**Solución:** Verificar amount > 0

### BUG #7: Moneda No Validada
**Ubicación:** `app.py:56` - función `create_payment()`
**Problema:** Acepta cualquier string como moneda
**Caso:** "HACKED", "", "XYZ123" son monedas válidas
**Solución:** Validar contra lista de monedas ISO

### BUG #11: Montos No Normalizados
**Ubicación:** `app.py:116` - función `create_payment()`
**Problema:** Almacena como string sin formato consistente
**Caso:** "10", "10.0", "10.00", "010.00" son diferentes en DB
**Solución:** Normalizar a formato consistente (2 decimales)

### BUG #13: Idempotency Key No Atómico
**Ubicación:** `app.py:123-124` - función `create_payment()`
**Problema:** Registra key solo después de éxito
**Impacto:** Si falla después del pago pero antes de registrar key, queda inconsistente
**Solución:** Registrar key al inicio, eliminar si falla

### BUG #17: Validación de Reason Débil
**Ubicación:** `app.py:167` - función `refund_payment()`
**Problema:** No validar longitud ni contenido de reason
**Impacto:** Podría inyectar caracteres especiales o texto muy largo
**Solución:** Validar longitud máxima y sanitizar input

### BUG #19: Reembolso Sin Fee
**Ubicación:** `app.py:176` - función `refund_payment()`
**Problema:** Reembolsa amount completo, no net_amount
**Impacto:** Usuario gana dinero (fee) al reembolsar
**Caso:** Pago $100, fee $3.20, net $96.80 → reembolso $100
**Solución:** Reembolsar net_amount

### BUG #20: Tracking de Reembolso Ausente
**Ubicación:** `app.py:178-180` - función `refund_payment()`
**Problema:** Solo agrega campos al pago, no marca estado
**Impacto:** No se puede saber cuántos reembolsos se hicieron
**Solución:** Agregar campo `refund_count` y `total_refunded`

### BUG #21: User ID Opcional en Listado
**Ubicación:** `app.py:186` - función `list_payments()`
**Problema:** Si no se proporciona user_id, lista todos los pagos
**Impacto:** Exposición de datos de todos los usuarios
**Solución:** Requerir user_id obligatoriamente

### BUG #22: Filtro Inseguro
**Ubicación:** `app.py:191-194` - función `list_payments()`
**Problema:** `if not user_id` permite listar todo
**Impacto:** Data leak si se omite parámetro
**Solución:** Validar user_id está presente

### BUG #23: Sin Paginación
**Ubicación:** `app.py:196` - función `list_payments()`
**Problema:** Retorna todos los pagos sin límite
**Impacto:** Respuesta masiva si hay muchos pagos → DoS
**Solución:** Implementar paginación con limit/offset

### BUG #24: Sin Ordenamiento
**Ubicación:** `app.py:199` - función `list_payments()`
**Problema:** Resultados en orden arbitrario
**Impacto:** Tests flaky, UX inconsistente
**Solución:** Ordenar por created_at DESC

### BUG #26: Depósito Sin Verificación
**Ubicación:** `app.py:210` - función `deposit()`
**Problema:** No verificar método de pago
**Impacto:** Depósitos falsos, lavado de dinero
**Solución:** Integrar con gateway de pago real

### BUG #27: Sin Límite de Depósito
**Ubicación:** `app.py:215` - función `deposit()`
**Problema:** No hay límite máximo de depósito
**Impacto:** Potencial lavado de dinero
**Solución:** Agregar límites por día/usuario

### BUG #29: Sin Rate Limiting
**Ubicación:** `app.py:207` - función `generate_report()`
**Problema:** Reportes pueden generarse infinitamente
**Impacto:** Consumo excesivo de recursos
**Solución:** Implementar rate limiting

### BUG #30: Anular Pago Completado
**Ubicación:** `app.py:227` - función `void_payment()`
**Problema:** Permite anular pagos con status "completed"
**Impacto:** Dinero cobrado pero pago anulado → inconsistencia
**Solución:** Solo permitir anular pagos "pending"

### BUG #31: Anular Sin Reembolso
**Ubicación:** `app.py:230-235` - función `void_payment()`
**Problema:** Anula pero no reembolsa el dinero
**Impacto:** Dinero desaparece del sistema
**Solución:** Reembolsar automáticamente al anular

## 🎯 Ejercicios Sugeridos

### Ejercicio 1: Probar Race Conditions
```bash
# Ejecutar dos requests simultáneos
# Ambos deberían fallar por balance insuficiente
# Pero uno podría pasar por el race condition
```

### Ejercicio 2: Reembolso Múltiple
```bash
# Reembolsar el mismo pago 3 veces
# Verificar que el balance aumenta cada vez
```

### Ejercicio 3: Montos Negativos
```bash
# Crear pago con monto -$100
# Verificar que el balance del usuario aumenta
```

## 🧪 Usuarios de Prueba

| User ID | Balance Inicial | Propósito |
|---------|----------------|-----------|
| user_1  | $1000.00       | Testing normal |
| user_2  | $500.00        | Testing límite |
| user_3  | $50.00         | Testing insuficiente |

## 🔗 Endpoints

- `GET /health` - Health check
- `POST /api/v1/payments` - Crear pago
- `GET /api/v1/payments/<id>` - Ver pago
- `GET /api/v1/payments` - Listar pagos (filtrar por user_id)
- `POST /api/v1/payments/<id>/refund` - Reembolsar
- `POST /api/v1/payments/<id>/void` - Anular
- `GET /api/v1/users/<id>/balance` - Ver balance
- `POST /api/v1/users/<id>/deposit` - Depositar
- `GET /api/v1/admin/payments/report` - Reporte admin
