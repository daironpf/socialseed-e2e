# Documentation

Welcome to the socialseed-e2e documentation!

## 🆕 Nuevo: Generación Autónoma de Tests (Issue #185)

Genera tests automáticamente analizando tu código fuente. Ideal para APIs con muchos endpoints.

```bash
e2e manifest        # Analizar proyecto
e2e generate-tests  # Generar tests automáticamente
e2e run             # Ejecutar tests generados
```

📖 **[Guía Completa de Generación Autónoma](autonomous-test-generation-guide.md)** - Paso a paso con ejemplos

## Table of Contents

### Guías Principales
- [Installation](installation.md) - Instalación del framework
- [Quick Start](quickstart.md) - Primeros pasos en 15 minutos
- [Autonomous Test Generation](autonomous-test-generation-guide.md) - **🆕 Generación automática de tests**

### Configuración y Uso
- [Configuration](configuration.md) - Configuración de e2e.conf
- [CLI Reference](cli-reference.md) - Referencia completa de comandos
- [Writing Tests](writing-tests.md) - Cómo escribir tests manualmente
- [CI/CD Integration](ci-cd.md) - **🆕 Integración continua y plantillas**
- [IDE Extensions](ide-extensions.md) - **🆕 Extensiones para VS Code y PyCharm**
- [API Reference](api-reference.md) - Referencia de la API

### Testing Avanzado
- [Mock API for Testing](mock-api.md) - API mock basada en Flask
- [Cloud Integrations](cloud-integrations.md) - **🆕 Integración nativa con AWS, GCP y Azure**
- [Observability & APM](observability.md) - **🆕 Integración con DataDog, New Relic y Prometheus**
- [Testing Guide](testing-guide.md) - Configuración de pytest, marcadores y cobertura
- [Agent Guide](AGENT_GUIDE.md) - Guía para agentes de IA

### Otros
- [GitHub Pages Setup](github-pages-setup.md) - Despliegue automático de documentación

## Quick Links

| Tema | Documentación |
|------|---------------|
| **🆕 Generación Automática** | [autonomous-test-generation-guide.md](autonomous-test-generation-guide.md) |
| **CLI Commands** | [CLI Reference](cli-reference.md) |
| **Running Tests** | [Testing Guide](testing-guide.md) |
| **Writing Tests** | [Writing Tests](writing-tests.md) |
| **Agent IA Guide** | [Agent Guide](AGENT_GUIDE.md) |
| **Coverage Reports** | Automatic coverage reporting to codecov.io (minimum 80%) |

## Getting Started

### Opción 1: Generación Automática (Recomendado para APIs existentes)

Si ya tienes una API con código fuente:

```bash
# 1. Inicializar proyecto
e2e init

# 2. Analizar código fuente
e2e manifest

# 3. Generar tests automáticamente
e2e generate-tests

# 4. Personalizar datos (opcional)
vim services/*/data_schema.py

# 5. Ejecutar tests
e2e run
```

📖 **[Ver guía completa](autonomous-test-generation-guide.md)**

### Opción 2: Manual (Para control total)

Si prefieres escribir los tests manualmente:

```bash
# 1. Inicializar proyecto
e2e init

# 2. Crear servicio
e2e new-service users-api

# 3. Crear tests
e2e new-test login --service users-api

# 4. Ejecutar
e2e run
```

📖 **[Ver Quick Start](quickstart.md)**

---

## 🚀 Características Principales

- **Generación Autónoma**: Analiza tu código y genera tests automáticamente
- **Multi-ORM**: Soporta SQLAlchemy, Prisma, Hibernate
- **Detección de Flujos**: Detecta automáticamente flujos de autenticación, CRUD, etc.
- **Datos Inteligentes**: Genera datos de prueba válidos basados en constraints
- **Tests de Validación**: Crea automáticamente tests para casos edge y chaos
