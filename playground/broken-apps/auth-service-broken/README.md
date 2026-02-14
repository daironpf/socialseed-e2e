# Auth Service Broken

Servicio de autenticación intencionalmente roto para aprender a detectar bugs con SocialSeed E2E.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servicio
python app.py
```

El servicio estará disponible en: `http://localhost:5001`

## 📖 Documentación

- **[BUGS.md](BUGS.md)** - Lista completa de 20 bugs intencionales
- **Tests de ejemplo** en la carpeta `tests/`

## 🎯 Objetivos de Aprendizaje

1. **Detección de bugs de seguridad**: JWT, contraseñas, autenticación
2. **Validación de APIs**: Status codes, respuestas, headers
3. **Tests E2E**: Crear tests que detecten los bugs

## 🧪 Usuarios de Prueba

| Email | Contraseña | Rol |
|-------|------------|-----|
| admin@example.com | admin123 | admin |
| user@example.com | password123 | user |

## 🔗 Endpoints

- `GET /health` - Health check
- `POST /api/v1/auth/register` - Registro
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/profile` - Perfil (requiere auth)
- `GET /api/v1/auth/admin/users` - Listar usuarios (requiere auth)
- `POST /api/v1/auth/reset-password` - Reset password

## 🎮 Ejemplo de uso

```bash
# Health check
curl http://localhost:5001/health

# Registrar usuario
curl -X POST http://localhost:5001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "123", "username": "test"}'

# Login
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

## 🐛 Lista de Bugs (Resumen)

- **5 bugs críticos** de seguridad
- **5 bugs de seguridad media**
- **10 bugs funcionales**

Ver [BUGS.md](BUGS.md) para detalles completos.

## 📝 Licencia

Parte del playground de SocialSeed E2E para fines educativos.
