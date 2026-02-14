# Tutorial 1: Primeros Pasos con SocialSeed E2E

Bienvenido a tu primer tutorial de SocialSeed E2E. En 15 minutos aprenderás los conceptos básicos y crearás tu primer test.

## 🎯 Objetivos

- Instalar SocialSeed E2E
- Configurar un servicio para testing
- Crear tu primer test E2E
- Ejecutar y ver resultados

## 📋 Prerrequisitos

- Python 3.8+
- pip instalado
- Terminal/Consola

## 🚀 Paso 1: Instalación (2 min)

```bash
# Instalar SocialSeed E2E
pip install socialseed-e2e

# Verificar instalación
e2e --version
```

Deberías ver la versión instalada, algo como: `socialseed-e2e 0.1.2`

## 🏗️ Paso 2: Inicializar Proyecto (3 min)

```bash
# Crear directorio para tu proyecto de tests
mkdir my-first-e2e-tests
cd my-first-e2e-tests

# Inicializar proyecto
e2e init
```

Esto creará:
```
my-first-e2e-tests/
├── e2e.conf          # Configuración principal
├── services/         # Aquí irán tus servicios
└── reports/          # Reportes de ejecución
```

## ⚙️ Paso 3: Configurar el Servicio (3 min)

Para este tutorial usaremos el **Auth Service Broken** del playground:

```bash
# En otra terminal, iniciar el servicio
cd ../playground/broken-apps/auth-service-broken
pip install -r requirements.txt
python app.py
```

El servicio estará en `http://localhost:5001`

Ahora configúralo en tu proyecto de tests. Edita `e2e.conf`:

```yaml
services:
  auth-service:
    name: auth-service
    base_url: http://localhost:5001
    health_endpoint: /health
    timeout: 5000
    auto_start: false
    required: true
```

## 📝 Paso 4: Crear tu Primer Test (4 min)

Crea el archivo `services/auth_service_page.py`:

```python
from socialseed_e2e import BasePage

class AuthServicePage(BasePage):
    """Page object for Auth Service."""

    async def check_health(self):
        """Check if service is healthy."""
        response = await self.page.request.get(f"{self.base_url}/health")
        return response.status == 200

    async def login(self, email: str, password: str):
        """Login with credentials."""
        response = await self.page.request.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"email": email, "password": password}
        )
        return response

    async def get_profile(self, token: str):
        """Get user profile."""
        response = await self.page.request.get(
            f"{self.base_url}/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response
```

Ahora crea tu test en `services/modules/test_01_health_check.py`:

```python
async def run(page):
    """Test: Health check endpoint should return 200."""
    # Arrange
    auth_page = page

    # Act
    response = await auth_page.check_health()

    # Assert
    assert response is True, "Health check should return True"
    print("✅ Health check passed!")
```

## ▶️ Paso 5: Ejecutar el Test (2 min)

```bash
# Ejecutar todos los tests
e2e run

# O específicamente el módulo de health check
e2e run --service auth-service --module test_01_health_check
```

Deberías ver:
```
🚀 SocialSeed E2E Test Runner
=============================

✅ Health check passed!

Test Results:
  Passed: 1
  Failed: 0
  Skipped: 0

Execution time: 2.34s
```

## 🐛 Paso 6: Detectar un Bug (1 min)

Ahora vamos a encontrar un bug. Crea `services/modules/test_02_login_bugs.py`:

```python
async def run(page):
    """Test: Login should not expose passwords in profile response."""
    # Login
    response = await page.login("admin@example.com", "admin123")
    assert response.status == 200, "Login should succeed"

    data = await response.json()
    token = data["access_token"]

    # Get profile
    profile_response = await page.get_profile(token)
    assert profile_response.status == 200, "Profile should be accessible"

    profile_data = await profile_response.json()

    # BUG: Profile should NOT contain password!
    assert "password" not in profile_data, "BUG: Password exposed in profile!"

    print("✅ Profile doesn't expose password")
```

Ejecuta el test:
```bash
e2e run --service auth-service --module test_02_login_bugs
```

¡El test fallará! Esto es correcto - acabas de encontrar el **BUG #17**: La API expone la contraseña en la respuesta del perfil.

## 📊 Paso 7: Ver Reporte (Opcional)

```bash
# Ejecutar con reporte HTML
e2e run --report html

# Abrir reporte
open reports/report.html  # macOS
# o
xdg-open reports/report.html  # Linux
```

## 🎉 ¡Felicitaciones!

Has completado tu primer tutorial de SocialSeed E2E. Ahora sabes:

✅ Instalar el framework
✅ Configurar un servicio
✅ Crear un Page Object
✅ Escribir tests E2E
✅ Ejecutar tests
✅ Detectar bugs reales

## 🎯 Siguientes Pasos

- **Tutorial 2**: [Generación de Tests con IA](../02-ai-test-generation/)
- **Explorar**: Más bugs en [Auth Service Broken](../../broken-apps/auth-service-broken/)
- **Desafío**: [Encuentra el Bug](../../challenges/find-the-bug-01/)

## 💡 Tips

1. **Usa async/await**: Todos los métodos son asíncronos
2. **Page Objects**: Organiza tu código en clases reutilizables
3. **Assertions claras**: Mensajes descriptivos ayudan al debugging
4. **Módulos numerados**: Usa prefijos como `01_`, `02_` para orden

## 🆘 Troubleshooting

### "Connection refused"
- Asegúrate de que el servicio esté corriendo en el puerto correcto
- Verifica `base_url` en `e2e.conf`

### "Module not found"
- Verifica que el archivo esté en `services/modules/`
- El nombre del archivo debe empezar con `test_`

### Test pasa cuando debería fallar
- Revisa la lógica del assertion
- Imprime variables con `print()` para debugging

## 📚 Recursos

- [Documentación completa](../../../docs/)
- [Ejemplos](../../../examples/)
- [API Reference](../../../docs/api.md)

---

**¿Preguntas?** Únete a nuestras [GitHub Discussions](https://github.com/daironpf/socialseed-e2e/discussions)
