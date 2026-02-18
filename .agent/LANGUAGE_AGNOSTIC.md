# Language-Agnostic Testing Guide

**Meta:** Usar socialseed-e2e para testear APIs escritas en CUALQUIER lenguaje de programación.

---

## 🌍 Filosofía Agnóstica

`socialseed-e2e` está diseñado para ser **completamente agnóstico del lenguaje del backend**. No importa si tu API está escrita en:

- **Java** (Spring Boot, Jakarta EE)
- **JavaScript/TypeScript** (Node.js, Express, NestJS)
- **Python** (Flask, FastAPI, Django)
- **Go** (Gin, Echo, Fiber)
- **C#** (.NET Core, ASP.NET)
- **Ruby** (Rails, Sinatra)
- **PHP** (Laravel, Symfony)
- **Rust** (Actix, Rocket)
- **C++** (Crow, Pistache)
- **Kotlin** (Ktor, Spring)
- **Scala** (Play Framework)
- **Elixir** (Phoenix)
- **Clojure** (Ring)
- **Haskell** (Yesod, Scotty)
- **Cualquier otro**

**Si habla HTTP/REST, gRPC o WebSocket, podemos testearlo.**

---

## 🔧 Protocolos Soportados

### 1. HTTP/REST ✅
**Soportado nativamente** - Sin configuración adicional

```yaml
# e2e.conf
services:
  java-api:
    base_url: http://localhost:8080  # Spring Boot
  node-api:
    base_url: http://localhost:3000  # Express
  go-api:
    base_url: http://localhost:8081  # Gin
```

### 2. gRPC ⚙️
**Requiere instalación de extras**

```bash
e2e install-extras grpc
```

```yaml
# e2e.conf
services:
  go-grpc:
    base_url: localhost:50051
    protocol: grpc
```

### 3. WebSocket 🔌
**Soportado via Playwright**

```python
# En tu page object
def do_connect_websocket(self, endpoint: str):
    return self.ws_connect(endpoint)
```

### 4. GraphQL 📊
**Via HTTP POST**

```python
def do_graphql_query(self, query: str, variables: dict = None):
    return self.post("/graphql", data={
        "query": query,
        "variables": variables or {}
    })
```

---

## 🎯 Ejemplos por Lenguaje

### Java (Spring Boot)

**API de ejemplo:**
```java
@RestController
@RequestMapping("/api/v1")
public class UserController {
    
    @PostMapping("/users")
    public ResponseEntity<User> createUser(@RequestBody @Valid UserRequest request) {
        // Implementation
    }
    
    @GetMapping("/users/{id}")
    public ResponseEntity<User> getUser(@PathVariable String id) {
        // Implementation
    }
}
```

**Test en socialseed-e2e:**
```python
# services/spring_api/data_schema.py
class UserRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    email: EmailStr
    firstName: str  # Spring usa camelCase
    lastName: str

ENDPOINTS = {
    "create": "/api/v1/users",
    "get": "/api/v1/users/{id}"
}
```

### Node.js (Express)

**API de ejemplo:**
```javascript
app.post('/api/users', async (req, res) => {
    const user = await User.create(req.body);
    res.status(201).json({ data: user });
});
```

**Test en socialseed-e2e:**
```python
# Mismo data_schema que cualquier otro
# El framework no distingue el backend
```

### Go (Gin)

**API de ejemplo:**
```go
r.POST("/api/v1/users", func(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    // Create user
    c.JSON(201, gin.H{"data": user})
})
```

**Test en socialseed-e2e:**
```python
# Identico a Java y Node.js
# El framework solo ve HTTP/JSON
```

### Python (FastAPI)

**API de ejemplo:**
```python
@app.post("/api/v1/users")
async def create_user(user: UserCreate):
    return {"data": user}
```

**Test en socialseed-e2e:**
```python
# Ya conoces esto - es el ejemplo principal
```

---

## 🔍 Detección Automática de Tech Stack

El framework puede detectar automáticamente el stack tecnológico de tu proyecto:

```bash
e2e deep-scan
```

**Detecta:**
- Framework web (Spring, Express, Flask, etc.)
- Puerto típico del framework
- Estructura de directorios
- Archivos de configuración

**Ejemplo de output:**
```
🔍 Deep scanning: /project

📋 Scan Summary:
--------------------------------------------------
🛠️  Detected Frameworks:
   • spring-boot (java) - 98% confidence
   • Maven project structure detected

📦 Services Found: 1
   • application (port 8080)

🌐 Recommended Base URL: http://localhost:8080
```

---

## 📋 Convenciones por Lenguaje

### Nombres de Campos (Serialización)

| Lenguaje | Convención | Ejemplo | Config en Pydantic |
|----------|------------|---------|-------------------|
| Java | camelCase | `firstName` | `alias="firstName"` |
| Python | snake_case | `first_name` | Default |
| Go | PascalCase/CamelCase | `FirstName` | `alias="FirstName"` |
| Node.js | camelCase | `firstName` | `alias="firstName"` |
| C# | PascalCase | `FirstName` | `alias="FirstName"` |
| Ruby | snake_case | `first_name` | Default |

**Ejemplo configuración:**
```python
class UserCreate(BaseModel):
    model_config = {"populate_by_name": True}
    
    # Java/Spring usa camelCase
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: EmailStr
```

### Estructuras de Respuesta

Diferentes frameworks estructuran las respuestas diferente:

**Java/Spring (typical):**
```json
{
  "data": { ... },
  "message": "Success",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Express (flexible):**
```json
{
  "data": { ... },
  "success": true
}
```

**FastAPI (puede variar):**
```json
{ ... }  // Directo, sin wrapper
```

**Adaptar en tu page:**
```python
def do_create_user(self, request: UserCreate) -> APIResponse:
    response = self.post(ENDPOINTS["create"], data=request.model_dump(by_alias=True))
    
    if response.ok:
        data = response.json()
        # Manejar diferentes estructuras
        if "data" in data:
            self.user_id = data["data"]["id"]
        else:
            self.user_id = data["id"]
    
    return response
```

---

## 🚀 Setup por Lenguaje

### Java (Maven/Gradle)

```bash
# 1. Compilar y ejecutar
./mvnw spring-boot:run
# o
./gradlew bootRun

# 2. Detectar
 e2e observe

# 3. Configurar e2e.conf
```

**e2e.conf:**
```yaml
services:
  spring-api:
    base_url: http://localhost:8080
    health_endpoint: /actuator/health  # Spring Boot Actuator
```

### Node.js

```bash
# 1. Ejecutar
npm start

# 2. Detectar
e2e observe
```

**e2e.conf:**
```yaml
services:
  node-api:
    base_url: http://localhost:3000
    health_endpoint: /health
```

### Go

```bash
# 1. Ejecutar
go run main.go

# 2. Detectar
e2e observe
```

**e2e.conf:**
```yaml
services:
  go-api:
    base_url: http://localhost:8080
```

---

## 🧪 Testing Cross-Language

### Escenario: Microservicios Heterogéneos

```yaml
# e2e.conf
services:
  auth-service:      # Java/Spring
    base_url: http://localhost:8081
    
  users-service:     # Node.js/Express
    base_url: http://localhost:3000
    
  payments-service:  # Go
    base_url: http://localhost:8082
    
  notification-service:  # Python/FastAPI
    base_url: http://localhost:8000
```

**Flujo cross-language:**
```python
# 1. Autenticar en Java service
auth_page.do_login(credentials)
token = auth_page.access_token

# 2. Crear usuario en Node service
users_page.set_auth_token(token)
user_response = users_page.do_create_user(user_data)
user_id = users_page.get_user_id()

# 3. Procesar pago en Go service
payments_page.set_auth_token(token)
payment_response = payments_page.do_process_payment(user_id, amount)

# 4. Enviar notificación en Python service
notification_page.set_auth_token(token)
notification_page.do_send_notification(user_id, "Payment processed")
```

---

## 📊 Formatos de Intercambio

### JSON (Default) ✅
```python
data = {"key": "value"}
response = self.post("/endpoint", data=data)
```

### XML
```python
xml_data = """<?xml version="1.0"?>
<request>
    <key>value</key>
</request>"""

response = self.post(
    "/endpoint",
    data=xml_data,
    headers={"Content-Type": "application/xml"}
)
```

### Form Data
```python
from multipart import MultipartEncoder

multipart_data = MultipartEncoder(
    fields={
        'field0': 'value',
        'field1': 'value',
        'file': ('filename', open('file.py', 'rb'), 'text/plain')
    }
)

response = self.post(
    "/upload",
    data=multipart_data,
    headers={"Content-Type": multipart_data.content_type}
)
```

---

## 🔐 Autenticación por Framework

### Spring Security (JWT)
```python
# Header típico
headers = {"Authorization": f"Bearer {token}"}
```

### Express (Passport.js)
```python
# Puede ser Bearer, Basic, o custom
headers = {"Authorization": f"Bearer {token}"}
# o
headers = {"X-API-Key": api_key}
```

### FastAPI (OAuth2)
```python
# OAuth2 con Bearer
headers = {"Authorization": f"Bearer {token}"}
```

### Gin (JWT)
```python
# Similar a Spring
headers = {"Authorization": f"Bearer {token}"}
```

---

## 🛠️ Herramientas Específicas por Lenguaje

### Java
```bash
# Ver endpoints disponibles (Actuator)
curl http://localhost:8080/actuator/mappings

# Health check
curl http://localhost:8080/actuator/health
```

### Node.js
```bash
# Listar rutas (si usa express-list-endpoints)
npx express-list-endpoints
```

### Go
```bash
# Swagger/OpenAPI
# Visitar: http://localhost:8080/swagger/index.html
```

### Python
```bash
# FastAPI docs
# Visitar: http://localhost:8000/docs
```

---

## 📝 Checklist por Lenguaje

### Antes de empezar a testear:

- [ ] ¿API ejecutándose? (`e2e observe`)
- [ ] ¿Puerto detectado correctamente?
- [ ] ¿Health endpoint responde?
- [ ] ¿Formato de respuesta identificado? (JSON/XML)
- [ ] ¿Convención de nombres de campos? (camelCase/snake_case)
- [ ] ¿Estructura de respuesta? (con/sin wrapper `data`)
- [ ] ¿Tipo de autenticación? (JWT/API Key/Basic)

### Configuración en data_schema.py:

- [ ] Modelos Pydantic con aliases correctos
- [ ] Endpoints mapeados
- [ ] Headers específicos del framework
- [ ] Test data representativo

---

## 🎯 Caso de Uso: Migración de Lenguaje

**Escenario:** Migrando de Express (Node.js) a Spring Boot (Java)

**Antes (Node.js):**
```javascript
// POST /api/users - creaba usuario directamente
res.json(user);
```

**Después (Java):**
```java
// POST /api/v1/users - wrapper de respuesta
return ResponseEntity.ok(Map.of("data", user));
```

**Adaptación en tests:**
```python
def run(page):
    response = page.do_create_user(request)
    data = response.json()
    
    # Manejar ambas estructuras
    if "data" in data:
        user = data["data"]  # Java
    else:
        user = data          # Node.js
    
    assert "id" in user
```

---

## 🚀 Comandos Útiles para Cualquier Lenguaje

```bash
# Detectar automáticamente
e2e deep-scan

# Observar servicios en ejecución
e2e observe

# Verificar conectividad
e2e doctor

# Importar desde OpenAPI (cualquier lenguaje)
e2e import --format openapi api.yaml

# Generar tests automáticamente
e2e generate-tests
```

---

## 📚 Recursos por Lenguaje

### Java
- [Spring Testing](https://docs.spring.io/spring-framework/docs/current/reference/html/testing.html)
- [REST Assured](https://rest-assured.io/) (alternativa Java nativa)

### Node.js
- [Supertest](https://github.com/visionmedia/supertest) (alternativa JS nativa)
- [Jest](https://jestjs.io/)

### Go
- [httpexpect](https://github.com/gavv/httpexpect) (alternativa Go nativa)

### Python
- [Requests](https://docs.python-requests.org/) (ya incluido)
- [Pytest](https://docs.pytest.org/)

---

## ✅ Ventajas de socialseed-e2e vs Testing Nativo

| Característica | Testing Nativo | socialseed-e2e |
|---------------|----------------|----------------|
| Lenguaje agnóstico | ❌ Mismo lenguaje | ✅ Cualquier lenguaje |
| Testear desde fuera | ⚠️ Difícil | ✅ Diseñado para eso |
| Cross-service | ❌ Complicado | ✅ Built-in |
| AI Generation | ❌ No | ✅ Sí |
| Reportes | ⚠️ Básicos | ✅ Avanzados |
| CI/CD templates | ❌ Manual | ✅ Automático |
| Mocking externo | ⚠️ Configuración | ✅ Comandos integrados |

---

## 🎓 Conclusión

**No importa en qué lenguaje esté escrita tu API.**

Si habla HTTP/REST, gRPC o WebSocket, `socialseed-e2e` puede testearla.

El framework se enfoca en:
1. **Protocolos** (HTTP, gRPC, WebSocket)
2. **Formatos** (JSON, XML, etc.)
3. **Comportamiento** (requests/responses)

No en:
- Lenguaje del backend
- Framework específico
- Implementación interna

**Esto te permite:**
- Testear APIs legacy sin modificar código
- Hacer testing de integración cross-language
- Migrar entre tecnologías sin reescribir tests
- Unificar testing en organizaciones polyglot

---

**Versión:** 1.0  
**Framework:** socialseed-e2e v0.1.2  
**Última actualización:** 2026-02-17
