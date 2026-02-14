# 🐛 Auth Service Broken - Lista de Bugs

Este servicio contiene **20 bugs intencionales** relacionados con autenticación y seguridad.
Úsalos para practicar la detección de problemas con SocialSeed E2E.

## 🔴 Bugs Críticos (Seguridad)

### BUG #1: MD5 en lugar de SHA-256
**Ubicación:** `app.py:37` - función `create_token()`
**Problema:** Usa MD5 para generar tokens, algoritmo criptográficamente roto
**Impacto:** Los tokens pueden ser fácilmente comprometidos
**Solución:** Usar SHA-256 o bcrypt

### BUG #10: Contraseñas en texto plano
**Ubicación:** `app.py:116` - función `register()`
**Problema:** Almacena contraseñas sin hash ni salt
**Impacto:** Si se filtra la base de datos, las contraseñas son legibles
**Solución:** Usar bcrypt con salt

### BUG #17: Exposición de contraseñas en respuestas
**Ubicación:** `app.py:200` - función `get_profile()`
**Problema:** La respuesta JSON incluye el campo "password"
**Impacto:** Cualquier usuario puede ver su propia contraseña
**Solución:** Filtrar campos sensibles en las respuestas

## 🟠 Bugs de Seguridad Media

### BUG #3: No validar firma del token
**Ubicación:** `app.py:50-65` - función `decode_token()`
**Problema:** No verifica la firma JWT, acepta cualquier token con 3 partes
**Impacto:** Tokens pueden ser falsificados
**Solución:** Validar firma con clave secreta

### BUG #6: No verificar expiración de tokens
**Ubicación:** `app.py:89-90` - decorador `require_auth()`
**Problema:** Ignora el campo 'exp' del token
**Impacto:** Tokens expirados siguen siendo válidos indefinidamente
**Solución:** Comparar datetime.utcnow() con token['exp']

### BUG #11: Timing Attack
**Ubicación:** `app.py:155` - función `login()`
**Problema:** Comparación de strings no constante `user["password"] != password`
**Impacto:** Permite ataques de timing para adivinar contraseñas
**Solución:** Usar `hmac.compare_digest()` para comparación constante

### BUG #19: No verificar rol de administrador
**Ubicación:** `app.py:217` - función `list_users()`
**Problema:** Cualquier usuario autenticado puede listar todos los usuarios
**Impacto:** Violación de principio de mínimo privilegio
**Solución:** Verificar `user["role"] == "admin"`

## 🟡 Bugs Funcionales

### BUG #2: Validación de token muy permisiva
**Ubicación:** `app.py:53-54` - función `decode_token()`
**Problema:** Solo verifica que el token tenga 3 partes separadas por puntos
**Impacto:** Acepta tokens malformados
**Solución:** Validar estructura JWT completa

### BUG #4: Refresh tokens sin expiración
**Ubicación:** `app.py:28` - variable global `refresh_tokens`
**Problema:** Los refresh tokens no tienen fecha de expiración
**Impacto:** Tokens de larga vida pueden ser comprometidos
**Solución:** Agregar timestamp de expiración y limpieza periódica

### BUG #5: Prefijo "Bearer" opcional
**Ubicación:** `app.py:79-81` - decorador `require_auth()`
**Problema:** Acepta tokens con o sin el prefijo "Bearer "
**Impacto:** Inconsistencia en formato de Authorization header
**Solución:** Requerir estrictamente "Bearer " y rechazar tokens sin prefijo

### BUG #7: Validación de email básica
**Ubicación:** `app.py:105` - función `register()`
**Problema:** Solo verifica que el email contenga "@"
**Impacto:** Acepta emails inválidos como "a@b"
**Solución:** Usar validación regex completa o librería email-validator

### BUG #8: Sin validación de contraseña
**Ubicación:** `app.py:109` - función `register()`
**Problema:** Acepta contraseñas de cualquier longitud (incluso vacías)
**Impacto:** Contraseñas débiles son permitidas
**Solución:** Validar longitud mínima, complejidad, etc.

### BUG #9: Case sensitivity inconsistente
**Ubicación:** `app.py:112-113` - función `register()`
**Problema:** Verifica email exacto pero no username
**Impacto:** Pueden existir usuarios "John" y "john"
**Solución:** Normalizar username a lowercase antes de verificar

### BUG #12: Tokens de acceso sin expiración
**Ubicación:** `app.py:158-159` - función `login()`
**Problema:** Los access tokens no tienen tiempo de expiración
**Impacto:** Tokens válidos para siempre
**Solución:** Agregar `expires_in` (ej: 3600 segundos)

### BUG #13: Refresh tokens sin expiración
**Ubicación:** `app.py:162` - función `login()`
**Problema:** Mismo que #4 pero en código diferente
**Impacto:** Refresh tokens válidos indefinidamente
**Solución:** Agregar expiración a refresh tokens

### BUG #14: Falta expires_in en respuesta
**Ubicación:** `app.py:164-169` - función `login()`
**Problema:** La respuesta no incluye cuando expira el token
**Impacto:** Clientes no saben cuándo refrescar
**Solución:** Incluir `expires_in: 3600` en respuesta

### BUG #15: Validación de refresh token débil
**Ubicación:** `app.py:179-185` - función `refresh()`
**Problema:** Solo busca el token en el diccionario
**Impacto:** No hay validación estructural del token
**Solución:** Validar estructura JWT del refresh token

### BUG #16: Refresh token reutilizable
**Ubicación:** `app.py:188-189` - función `refresh()`
**Problema:** No revoca el refresh token anterior
**Impacto:** Mismo refresh token puede usarse múltiples veces
**Solución:** Generar nuevo refresh token y eliminar el anterior

### BUG #18: Logout incompleto
**Ubicación:** `app.py:212-215` - función `logout()`
**Problema:** Solo revoca refresh token, no access token
**Impacto:** Access token sigue siendo válido después del logout
**Solución:** Mantener blacklist de tokens revocados

### BUG #20: User enumeration en reset de contraseña
**Ubicación:** `app.py:232-237` - función `reset_password()`
**Problema:** Mensaje diferente si el email existe o no
**Impacto:** Permite enumerar usuarios registrados
**Solución:** Mensaje idéntico independientemente de existencia

## 🎯 Ejercicios Sugeridos

### Ejercicio 1: Encontrar bugs de seguridad
**Dificultad:** ⭐⭐ Fácil
**Tiempo:** 20 minutos
**Tarea:** Identifica los 5 bugs críticos de seguridad

### Ejercicio 2: Escribir tests que fallen
**Dificultad:** ⭐⭐⭐ Medio
**Tiempo:** 30 minutos
**Tarea:** Crea tests de SocialSeed E2E que detecten cada bug

### Ejercicio 3: Corregir bugs
**Dificultad:** ⭐⭐⭐⭐ Difícil
**Tiempo:** 45 minutos
**Tarea:** Corrige todos los bugs y verifica que los tests pasen

## 📝 Notas para Instructores

- Los bugs están numerados y documentados para facilitar la enseñanza
- Algunos bugs son intencionalmente obvios, otros más sutiles
- Se recomienda empezar con los bugs críticos (seguridad)
- Los bugs funcionales son buenos para practicar assertions

## 🔧 Cómo ejecutar

```bash
cd playground/broken-apps/auth-service-broken
pip install -r requirements.txt
python app.py
```

El servicio estará disponible en `http://localhost:5001`

## 🧪 Endpoints disponibles

- `GET /health` - Health check
- `POST /api/v1/auth/register` - Registro de usuarios
- `POST /api/v1/auth/login` - Inicio de sesión
- `POST /api/v1/auth/refresh` - Refrescar token
- `POST /api/v1/auth/logout` - Cerrar sesión
- `GET /api/v1/auth/profile` - Perfil de usuario
- `GET /api/v1/auth/admin/users` - Listar usuarios (admin)
- `POST /api/v1/auth/reset-password` - Reset de contraseña
