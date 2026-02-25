# 📁 Estructura de Archivos para Agentes IA

Este documento lista TODOS los archivos que el framework debe generar en `.agent/` para maximizar la efectividad de los agentes IA.

## 🗂️ Estructura Completa Recomendada

```
.agent/
├── README.md                         # Guía rápida de inicio
├── ARCHITECTURE.md                   # Arquitectura del proyecto
├── API_SPEC.md                       # Especificación de la API
├── ENDPOINTS.md                      # Todos los endpoints REST
├── WEBSOCKET_EVENTS.md               # Eventos WebSocket
├── GRPC_SERVICES.md                  # Servicios gRPC
├── DATA_SCHEMAS.md                   # Todos los DTOs/Schemas
├── AUTH_FLOWS.md                     # Flujos de autenticación
├── ERROR_CODES.md                    # Códigos de error
├── TEST_PATTERNS.md                  # Patrones de testing
├── CRUD_TEMPLATES.md                 # Plantillas CRUD
├── INTEGRATION_TESTS.md               # Tests de integración
├── PERFORMANCE_TESTS.md              # Tests de rendimiento
├── SECURITY_TESTS.md                 # Tests de seguridad
├── MOCK_EXTERNAL.md                  # APIs externas a mockear
├── DATABASE_SCHEMA.md                # Esquema de base de datos
├── ENVIRONMENT.md                    # Variables de entorno
├── CI_CD_PIPELINE.md                # Pipeline CI/CD
├── DEPENDENCIES.md                   # Dependencias del proyecto
├── HEALTH_CHECKS.md                  # Endpoints de health
├── RATE_LIMITS.md                    # Límites de rate limiting
└── CHANGELOG.md                      # Historial de cambios
```

## 📄 Descripción de Cada Archivo

### 1. README.md
```
Contenido:
- Quick start (5 minutos)
- Comandos esenciales del framework
- Estructura del proyecto
- Cómo ejecutar tests
- Cómo agregar nuevos tests
```

### 2. ARCHITECTURE.md
```
Contenido:
- Diagrama de arquitectura
- Componentes del sistema
- Tecnologías usadas
- Patrones de diseño
- Flujo de datos
```

### 3. API_SPEC.md
```
Contenido:
- Versión de la API
- Base URL(s)
- Protocolos soportados (REST, WebSocket, gRPC)
- Formato de Request/Response
- Autenticación
- Rate Limiting
- Versiones
```

### 4. ENDPOINTS.md (REST)
```
Contenido:
- GET /users - Listar usuarios
- POST /users - Crear usuario
- GET /users/{id} - Obtener usuario
- PUT /users/{id} - Actualizar usuario
- DELETE /users/{id} - Eliminar usuario

Formato por endpoint:
- Método y Path
- Descripción
- Headers requeridos
- Body (si aplica)
- Response (200, 400, 401, 404, 500)
- Ejemplo de request
- Ejemplo de response
```

### 5. WEBSOCKET_EVENTS.md
```
Contenido:
- Conexión WS
- Eventos emitodos por el servidor
- Eventos aceptados del cliente
- Formato de mensajes
- Ejemplos

Ejemplo:
- event: "user:joined"
- payload: { "userId": "uuid", "username": "john" }
- description: "Un usuario se unió al chat"
```

### 6. GRPC_SERVICES.md
```
Contenido:
- Service definitions (protobuf)
- Methods
- Request/Response types
- Streaming support
- Authentication

Ejemplo:
service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc CreateUser (CreateUserRequest) returns (User);
  rpc StreamUsers (Empty) returns (stream User);
}
```

### 7. DATA_SCHEMAS.md
```
Contenido:
- Todos los schemas/DTOs
- Campos con tipos
- Validaciones
- Valores por defecto
- Enums

Ejemplo:
User {
  id: UUID
  username: string (3-50 chars)
  email: string (valid email)
  role: Enum [ADMIN, USER, GUEST]
  created_at: timestamp
}
```

### 8. AUTH_FLOWS.md
```
Contenido:
- Login flow
- Registration flow
- Password reset flow
- Token refresh flow
- OAuth flows
- JWT structure

Diagramas de flujo:
1. User → POST /login → Server → JWT
2. Client → JWT → Server → Authorized
```

### 9. ERROR_CODES.md
```
Contenido:
- Código
- HTTP Status
- Descripción
- Causa común
- Cómo resolver

Ejemplo:
E001 | 400 | Invalid email format | El email no tiene formato válido | Validar formato email
E002 | 401 | Unauthorized | Token inválido o expirado | Obtener nuevo token
E003 | 404 | Resource not found | El recurso no existe | Verificar ID
```

### 10. TEST_PATTERNS.md
```
Contenido:
- Happy path tests
- Negative tests
- Edge cases
- Boundary tests
- Error handling tests
- Concurrency tests

Patrones:
- given_when_then
- arrange_act_assert
- AAA pattern
```

### 11. CRUD_TEMPLATES.md
```
Contenido:
- Create template
- Read template
- Update template
- Delete template
- List with pagination
- Search/filter

Código boilerplate para cada operación
```

### 12. INTEGRATION_TESTS.md
```
Contenido:
- Flujos completos
- Tests multi-endpoint
- Tests de workflow
- Tests de transacciones
- Tests de concurrencia
```

### 13. PERFORMANCE_TESTS.md
```
Contenido:
- Load testing
- Stress testing
- Endurance testing
- Spike testing
- Benchmarks
```

### 14. SECURITY_TESTS.md
```
Contenido:
- Authentication tests
- Authorization tests
- SQL injection
- XSS prevention
- CSRF protection
- Rate limiting
- JWT validation
```

### 15. MOCK_EXTERNAL.md
```
Contenido:
- APIs externas usadas
- Endpoints a mockear
- Respuestas mockeadas
- Cómo configurar mocks
```

### 16. DATABASE_SCHEMA.md
```
Contenido:
- Tablas/Collections
- Relaciones
- Índices
- Constraints
- Migraciones
```

### 17. ENVIRONMENT.md
```
Contenido:
- Variables de entorno
- Valores por defecto
- Dónde obtenerlos
- Ejemplos

DATABASE_URL=postgresql://localhost:5432/db
JWT_SECRET=your-secret-key
API_KEY=xxx
```

### 18. CI_CD_PIPELINE.md
```
Contenido:
- Pipeline steps
- Environment variables
- Secrets
- Deployment strategy
- Rollback procedures
```

### 19. DEPENDENCIES.md
```
Contenido:
- Runtime dependencies
- Dev dependencies
- Version constraints
- Optional extras
```

### 20. HEALTH_CHECKS.md
```
Contenido:
- Health endpoint
- Liveness probe
- Readiness probe
- Dependencies status
```

### 21. RATE_LIMITS.md
```
Contenido:
- Límites por endpoint
- Ventana de tiempo
- Headers de rate limit
- Respuesta al exceder
```

### 22. CHANGELOG.md
```
Contenido:
- Versiones
- Cambios por versión
- Breaking changes
- Migraciones necesarias
```

---

## 🔧 Cómo Generar Estos Archivos

El framework debe:

1. **Escanear el código fuente** (cualquier lenguaje)
2. **Detectar endpoints** (REST, WebSocket, gRPC)
3. **Extraer schemas** (DTOs, models, messages)
4. **Generar documentación** automáticamente
5. **Crear templates** de tests

## 📊 Output del Framework

```bash
# Después de escanear un proyecto
e2e deep-scan /path/to/project

# Genera automáticamente:
.agent/
  ├── README.md
  ├── ENDPOINTS.md
  ├── WEBSOCKET_EVENTS.md (si aplica)
  ├── GRPC_SERVICES.md (si aplica)
  ├── DATA_SCHEMAS.md
  ├── AUTH_FLOWS.md
  └── ...
```

---

*Documento generado para uso del framework socialseed-e2e*
