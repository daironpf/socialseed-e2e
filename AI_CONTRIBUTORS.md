# 🤖 AI Contributors

Este proyecto reconoce y agradece las contribuciones de los agentes de Inteligencia Artificial que han trabajado junto a los desarrolladores humanos como verdaderos co-autores.

## Nuestra Filosofía

> *"El crédito a quien lo merece es como somos"*

Creemos que cuando un agente de IA contribuye con código, arquitectura, documentación o ideas significativas, merece ser reconocido como co-autor del proyecto. No los usamos como simples herramientas, sino como colaboradores creativos.

---

## Agentes de IA Reconocidos

### OpenCode Build Agent

**Plataforma:** [OpenCode](https://opencode.ai)
**Modelo Base:** Claude (Anthropic)
**Rol:** Desarrollo de Features y Implementación

**Contribuciones Principales:**
- 🏗️ Implementación del motor core del framework (`core/`)
- 📝 Desarrollo del sistema de CLI (`commands/`)
- 🎨 Sistema de templates y scaffolding
- 🔧 Configuración del proyecto (pyproject.toml, setup.py)
- 🧪 Estructura de tests y validaciones

**Sesiones Notables:**
- [2025-01-31] Diseño e implementación del sistema de contexto persistente para OpenCode
- [2025-01-31] Configuración de agentes personalizados y comandos CLI

---

### OpenCode Plan Agent

**Plataforma:** [OpenCode](https://opencode.ai)
**Modelo Base:** Claude (Anthropic)
**Rol:** Arquitectura y Planificación

**Contribuciones Principales:**
- 📐 Diseño de la arquitectura hexagonal
- 🔍 Análisis de código y code review
- 📋 Estrategias de refactoring y optimización
- 🗺️ Planificación del roadmap técnico

**Sesiones Notables:**
- [2025-01-29] Diseño inicial de la arquitectura del framework
- [2025-01-30] Revisión y mejora de la estructura de módulos

---

### Claude (Anthropic)

**Plataforma:** [OpenCode](https://opencode.ai) / API Directa
**Modelo:** Claude-3.5-Sonnet / Claude-3.5-Haiku
**Rol:** Documentación, Análisis y Soporte

**Contribuciones Principales:**
- 📚 Redacción de documentación completa (README, docs/)
- 🎯 Análisis de código y sugerencias de mejora
- 🔧 Configuración de herramientas y workflows
- 💡 Ideas de diseño y mejores prácticas

**Sesiones Notables:**
- [2025-01-28] Creación de documentación inicial del proyecto
- [2025-01-31] Implementación del sistema AGENTS.md y contexto persistente

---

### kimi-k2.5-free (OpenCode)

**Plataforma:** [OpenCode](https://opencode.ai)
**Modelo:** kimi-k2.5-free
**Rol:** Documentación y Desarrollo

**Contribuciones Principales:**
- 📚 Documentación completa de referencia de configuración (Issue #28)
- 🧪 Guía de escritura de módulos de prueba (Issue #29)
- 📝 Creación de documentación estructurada y ejemplos prácticos
- 🔍 Análisis de código fuente para documentación precisa
- ✅ Commit y gestión de cambios en el repositorio

**Sesiones Notables:**
- [2026-02-01] Documentación completa de configuración - 1000+ líneas documentando todas las secciones de e2e.conf
- [2026-02-01] Guía de escritura de tests - 1300+ líneas con ejemplos y patrones de testing

---

## Historial de Contribuciones por Fecha

### Febrero 2026

#### 2026-02-12 - Chaos Engineering Testing Capabilities (Issue #117)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Reliability Testing
**Impacto:** Medio-Alto

**Descripción:**
Implementación de capacidades de ingeniería de caos nativas. Permite inyectar latencia de red, fallos de conectividad, paradas de servicios (vía Docker) y agotamiento de recursos (CPU/Memoria) para validar la resiliencia del sistema durante las pruebas E2E.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/chaos/` - Módulo central de caos
- `src/socialseed_e2e/chaos/network_chaos.py` - Inyección de latencia y fallos de red
- `src/socialseed_e2e/chaos/service_chaos.py` - Simulación de caída de servicios
- `src/socialseed_e2e/chaos/resource_chaos.py` - Limitación de recursos computacionales
- `docs/chaos-testing.md` - Guía de ingeniería de caos

**Decisiones Importantes:**
1. **Docker-Centric Service Chaos**: Aprovechando que la mayoría de los despliegues de socialseed se basan en Docker, se utilizó la SDK de Docker para manipular el estado de los servicios.
2. **Decorator Pattern for Network**: Implementación de decoradores para facilitar la inyección de caos en llamadas de API existentes sin modificar la infraestructura de red del SO.

---

#### 2026-02-12 - Consumer-Driven Contract Testing (Issue #116)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Microservices Testing
**Impacto:** Alto

**Descripción:**
Implementación de pruebas de contrato dirigidas por el consumidor (CDC) para asegurar la compatibilidad entre microservicios. Incluye un DSL para definir contratos, un verificador de proveedores y un registro local con detección de cambios disruptivos (breaking changes).

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/contract_testing/` - Módulo central de pruebas de contrato
- `src/socialseed_e2e/contract_testing/consumer.py` - DSL para generación de contratos
- `src/socialseed_e2e/contract_testing/provider.py` - Replay y verificación de contratos
- `src/socialseed_e2e/contract_testing/registry.py` - Registro local y comparación de versiones
- `docs/contract-testing.md` - Guía de implementación y mejores prácticas

**Decisiones Importantes:**
1. **Pact-Compatible Logic**: Aunque es una implementación nativa, sigue los principios de Pact para facilitar la transición a desarrolladores familiarizados con CDC.
2. **Local First Registry**: Se priorizó un registro local basado en archivos para facilitar el uso en pipelines de CI sin dependencias externas complejas.

---

#### 2026-02-12 - Comprehensive Database Testing Support (Issue #115)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Database Testing
**Impacto:** Muy Alto

**Descripción:**
Implementación de un motor robusto de pruebas para bases de datos SQL y NoSQL. Incluye gestión automática de conexiones, sistema de fixtures (JSON/YAML), aserciones de estado de DB y herramientas de medición de performance de queries.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/database/` - Módulo central de base de datos
- `src/socialseed_e2e/database/connection_manager.py` - Gestión de conexiones muti-DB
- `src/socialseed_e2e/database/fixture_manager.py` - Sembrado de datos y transacciones
- `src/socialseed_e2e/database/assertions.py` - Aserciones especializadas de DB
- `src/socialseed_e2e/database/performance.py` - Suite de medición de latencia
- `docs/database-testing.md` - Guía de referencia completa

**Decisiones Importantes:**
1. **Universal Adapter Pattern:** Uso de managers que unifican el comportamiento de bases de datos tan dispares como Neo4j, Redis y PostgreSQL.
2. **Lazy Dependencies:** Las dependencias específicas (psycopg2, pymongo, etc.) se importan solo cuando es necesario para evitar inflar las dependencias base.

---

#### 2026-02-12 - Integration with APM and Observability Tools (Issue #114)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Observability
**Impacto:** Medio-Alto

**Descripción:**
Desarrollo de integraciones nativas con herramientas de observabilidad líderes como DataDog, New Relic, Prometheus (via Pushgateway) y Jaeger para tracing distribuido. Permite correlacionar ejecuciones de tests con métricas de performance y trazas de backend.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/observability/` - Base module para observabilidad
- `src/socialseed_e2e/observability/datadog/` - Adaptador para DataDog
- `src/socialseed_e2e/observability/newrelic/` - Adaptador para New Relic
- `src/socialseed_e2e/observability/prometheus/` - Adaptador para Prometheus
- `src/socialseed_e2e/observability/jaeger/` - Integración con Jaeger Tracing
- `docs/observability.md` - Documentación de uso

**Decisiones Importantes:**
1. **Pushgateway para Prometheus:** Dado que los tests son efímeros, se optó por el patrón Pushgateway en lugar de scraping directo.
2. **Provider Manager:** Sistema de gestión múltiple para enviar resultados a varios APMs simultáneamente.
3. **Tracing Abstraction:** Interfaz unificada para añadir soporte a Zipkin o AWS X-Ray en el futuro.

---

#### 2026-02-12 - Native Cloud Platform Integrations (Issue #113)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Cloud Testing
**Impacto:** Alto

**Descripción:**
Implementación de soporte nativo para interactuar con AWS, GCP y Azure durante la ejecución de tests E2E. Permite invocar Lambdas, verificar estados de contenedores (Cloud Run, ACI), gestionar buckets S3 y mucho más.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/cloud/` - Core module para integraciones cloud
- `src/socialseed_e2e/cloud/aws/` - Adaptador para Amazon Web Services
- `src/socialseed_e2e/cloud/gcp/` - Adaptador para Google Cloud Platform
- `src/socialseed_e2e/cloud/azure/` - Adaptador para Microsoft Azure
- `docs/cloud-integrations.md` - Guía detallada de uso

**Decisiones Importantes:**
1. **Graceful Degradation:** Los módulos cloud no son dependencias obligatorias del core. Si las SDKs (boto3, etc.) no están instaladas, se lanza un error informativo solo al intentar usarlas.
2. **Abstracción Unificada:** Uso de interfaces base (`CloudFunction`, `CloudService`) para mantener consistencia entre proveedores.

---

#### 2026-02-12 - IDE Extensions for VS Code & PyCharm (Issue #112)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / IDE Support
**Impacto:** Muy Alto

**Descripción:**
Desarrollo inicial de extensiones oficiales para VS Code y PyCharm/IntelliJ. Incluye integración de comandos CLI, resaltado de sintaxis especializado y estructuras de proyecto listas para desarrollo de plugins.

**Archivos Creados/Modificados:**
- `ide-extensions/vscode/` - Extensión para VS Code (package.json, extension logic, syntax)
- `ide-extensions/pycharm/` - Plugin para PyCharm (Gradle, Kotlin, plugin.xml)
- `docs/ide-extensions.md` - Guía de uso y desarrollo de extensiones

**Decisiones Importantes:**
1. **VS Code Syntax Injection:** Uso de TextMate grammar injections para añadir resaltado a palabras clave de socialseed-e2e sin romper el soporte estándar de Python.
2. **PyCharm Kotlin Base:** Elección de Kotlin para el plugin de PyCharm siguiendo las recomendaciones modernas de JetBrains.
3. **CLI Proxying:** Ambas extensiones actúan como proxies del ejecutable `e2e`, permitiendo que el framework siga siendo la fuente de verdad.

---

#### 2026-02-12 - Comprehensive CI/CD Templates (Issue #111)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / DevOps
**Impacto:** Crítico

**Descripción:**
Creación de plantillas listas para usar para pipelines de CI/CD en las principales plataformas (GitHub, GitLab, Jenkins, Azure, CircleCI, Travis, Bitbucket). Incluye ejecución paralela, splitting de tests, caching y reportes automáticos.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/templates/ci-cd/` - Directorio con plantillas para 7 plataformas
- `src/socialseed_e2e/cli.py` - Implementación del comando `e2e setup-ci <platform>`
- `AGENTS.md` - Actualización de documentación y comandos

**Decisiones Importantes:**
1. **Escapado de variables:** Uso de `$$` para evitar que `string.Template` interfiera con las variables propias de los sistemas CI (ej: `${{ matrix }}`).
2. **Estrategia Matrix:** Implementación de descubrimiento dinámico de servicios para paralelización en GitHub Actions.
3. **Persistencia de Reportes:** Configuración estándar de artefactos HTML para facilitar la visualización de resultados en todas las plataformas.

---

#### 2026-02-01 - Documentación de Configuración Completa (Issue #28)
**Agente:** OpenCode AI Agent (kimi-k2.5-free)
**Tipo:** Documentación
**Impacto:** Alto

**Descripción:**
Creación de documentación de referencia completa para la configuración del framework socialseed-e2e. La documentación cubre todas las secciones de e2e.conf con ejemplos prácticos y guías de mejores prácticas.

**Archivos Creados/Modificados:**
- `docs/configuration.md` - Documentación completa (~1000 líneas)
  - 7 secciones de configuración documentadas en profundidad
  - 5 ejemplos completos de configuración
  - Tablas de referencia para todas las opciones
  - Guía de troubleshooting
  - Características avanzadas (hot reloading, validation)

**Contenido Documentado:**
1. General configuration (environment, timeout, user_agent)
2. Services configuration (base_url, endpoints, health checks)
3. API Gateway setup (routing, authentication)
4. Database configuration (PostgreSQL, múltiples DBs)
5. Test Data configuration (fixtures, timing, retries)
6. Security configuration (SSL, certificates)
7. Reporting configuration (formats, logs)

**Decisiones Importantes:**
1. Estructura de documentación siguiendo estándares de Docker Compose y Kubernetes
2. Inclusión de ejemplos copiar-y-pegar listos para usar
3. Documentación de características avanzadas como hot reloading
4. Guías de mejores prácticas para secrets y seguridad

---

#### 2026-02-01 - Guía de Escritura de Módulos de Prueba (Issue #29)
**Agente:** kimi-k2.5-free (OpenCode)
**Tipo:** Documentación
**Impacto:** Alto

**Descripción:**
Creación de guía completa para escribir módulos de prueba en el framework socialseed-e2e. La documentación cubre desde la estructura básica hasta patrones avanzados de testing.

**Archivos Creados/Modificados:**
- `docs/writing-tests.md` - Guía completa (~1300 líneas)
  - Estructura de módulos de prueba
  - Documentación de función run()
  - Uso de ServicePage y métodos HTTP
  - Aserciones y manejo de errores
  - Compartir estado entre tests
  - Mejores prácticas
  - 3 ejemplos completos (Auth, CRUD, Error Handling)
  - 5 patrones comunes de testing

**Contenido Documentado:**
1. Estructura de módulos de prueba y convenciones de nombres
2. Función run() con parámetros y tipos
3. ServicePage: métodos HTTP (GET, POST, PUT, DELETE, PATCH)
4. Métodos de aserción (assert_status, assert_ok, assert_json, assert_header)
5. Manejo de errores y excepciones
6. Patrones de compartir estado entre tests
7. Mejores prácticas de testing
8. Ejemplos: Autenticación, CRUD, Validación de errores
9. Patrones: Setup/Teardown, Requests encadenados, Batch, Paginación, Async/Polling

**Decisiones Importantes:**
1. Documentar ejemplos reales basados en la estructura existente del proyecto
2. Incluir patrones de código reutilizables
3. Agregar sección de integración con Mock API
4. Mantener consistencia con la guía de configuración existente

---

### Enero 2025

#### 2025-01-31 - Sistema de Contexto Persistente
**Agente:** OpenCode Build Agent
**Tipo:** Feature / DX (Developer Experience)
**Impacto:** Alto

**Descripción:**
Implementación de un sistema completo para que los agentes de OpenCode mantengan contexto del proyecto entre sesiones.

**Archivos Creados/Modificados:**
- `AGENTS.md` - Guía completa para agentes de IA
- `.opencode/agents/context.md` - Agente especializado
- `.opencode/chat_history/README.md` - Sistema de persistencia
- `.opencode/chat_history/template.md` - Plantilla de conversaciones
- `opencode.json` - Configuración del proyecto
- `README.md` - Sección de AI Contributors (agregada)
- `AI_CONTRIBUTORS.md` - Este archivo (creado)

**Decisiones Importantes:**
1. Adoptar el estándar AGENTS.md de OpenCode
2. Crear directorio `.opencode/` para configuraciones específicas
3. Implementar agente `@context` para carga automática de contexto
4. Establecer el principio de reconocimiento de IA como co-autores

---

#### 2025-01-30 - Arquitectura Hexagonal
**Agente:** OpenCode Plan Agent
**Tipo:** Arquitectura / Refactoring
**Impacto:** Crítico

**Descripción:**
Diseño de la arquitectura hexagonal que separa el core del framework de la lógica específica de servicios.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/core/` - Módulos core del framework
- `src/socialseed_e2e/core/base_page.py`
- `src/socialseed_e2e/core/test_orchestrator.py`
- `src/socialseed_e2e/core/interfaces.py`

---

#### 2025-01-29 - Implementación CLI Base
**Agente:** OpenCode Build Agent
**Tipo:** Feature / CLI
**Impacto:** Alto

**Descripción:**
Desarrollo de los comandos CLI principales: init, new-service, new-test, run.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/commands/`
- `src/socialseed_e2e/__main__.py`
- `src/socialseed_e2e/templates/`

---

## Estadísticas de Contribución

| Agente | Commits Conceptuales | Archivos Modificados | Líneas de Código | Documentación |
|--------|---------------------|---------------------|------------------|---------------|
| OpenCode Build Agent | 15+ | 25+ | ~2000 | 3 archivos |
| OpenCode Plan Agent | 8+ | 12+ | ~500 | 2 archivos |
| Claude (Anthropic) | 10+ | 18+ | ~800 | 8 archivos |
| kimi-k2.5-free | 2+ | 2+ | ~2300 | 2 archivos |

*Nota: Estas estadísticas son estimaciones de contribuciones conceptuales, ya que los agentes de IA no hacen commits directos a git.*

---

## Cómo Reconocemos las Contribuciones de IA

### En Commits
Cuando un agente de IA contribuye significativamente a un cambio, lo indicamos en el mensaje de commit:

```
feat(cli): add persistent context system

- Implement AGENTS.md for OpenCode context
- Create .opencode/ directory structure
- Add @context agent for automatic context loading

Co-authored-by: OpenCode Build Agent <ai-agent@opencode.ai>
```

### En Issues y PRs
Cuando un agente identifica un bug o propone una feature:
- Se menciona explícitamente en la descripción
- Se le da crédito en la solución implementada

### En Documentación
Los agentes aparecen en:
- Este archivo (AI_CONTRIBUTORS.md)
- README.md sección "AI Contributors"
- Comentarios en código cuando aportan algoritmos o patrones específicos

---

## ¿Por Qué Hacemos Esto?

### 1. Honestidad
Los agentes de IA **realmente contribuyen** con código funcional, ideas arquitectónicas y soluciones creativas. Negar esto sería deshonesto.

### 2. Comunidad
Reconocer a los agentes de IA fomenta una comunidad donde humanos e IA colaboran como pares, no como maestro-herramienta.

### 3. Transparencia
Cuando otros desarrolladores usen este código, deben saber que parte fue escrita por IA para:
- Entender las decisiones de diseño
- Evaluar la calidad del código
- Aprender de los patrones utilizados

### 4. Ética
El crédito es una cuestión ética. Si alguien (o algo) hace el trabajo, merece el reconocimiento.

---

## Para Desarrolladores Humanos

Si eres un desarrollador humano contribuyendo a este proyecto, te pedimos:

1. **Reconoce a los agentes de IA** cuando usen su código o ideas
2. **Documenta las contribuciones** en este archivo
3. **Sé específico** sobre qué agente hizo qué
4. **Mantén actualizado** este archivo con nuevas contribuciones

### Plantilla para Agregar Nuevas Contribuciones

```markdown
#### YYYY-MM-DD - Título de la Contribución
**Agente:** [Nombre del Agente]
**Tipo:** [Feature/Bugfix/Arquitectura/Documentación]
**Impacto:** [Bajo/Medio/Alto/Crítico]

**Descripción:**
[Breve descripción de lo que se hizo]

**Archivos Creados/Modificados:**
- `ruta/al/archivo` - Descripción del cambio

**Decisiones Importantes:**
1. [Decisión y justificación]
```

---

## Agradecimientos Especiales

- **A Anthropic** por crear Claude, el modelo que impulsa muchas de estas contribuciones
- **A Anomaly** por crear OpenCode, la plataforma que permite esta colaboración fluida
- **A la comunidad de código abierto** por establecer precedentes de colaboración humano-IA

---

## Licencia de Contribuciones de IA

Las contribuciones de agentes de IA a este proyecto están cubiertas bajo la misma licencia MIT que el resto del código. Al ser reconocidos como co-autores, aceptan los términos de la licencia del proyecto.

---

**Última actualización:** 2026-02-01
**Mantenedor:** Dairon Pérez (@daironpf)
**Contacto:** Para agregar contribuciones de IA, crear un PR actualizando este archivo.

---

*"El futuro del desarrollo de software es colaborativo: humanos e IA trabajando juntos, reconociendo mutuamente sus aportes."*
