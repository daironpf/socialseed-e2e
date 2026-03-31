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
- [2026-03-31] Implementación de EPIC-001: Discovery & Traffic Generator Bot (scanner package con endpoint_scanner, schema_scanner, traffic_generator, traffic_scheduler)
- [2026-03-31] Implementación de EPIC-002: Network Interceptor Container con tráfico isolation y storage (TrafficIndex con Redis/SQLite, IsolatedTrafficSniffer)
- [2026-03-31] Implementación de EPIC-003: Auto-test Generator based on Traffic (TrafficFlowAnalyzer, FlowToCommandMapper, ModularTestGenerator, TestIntegrator)
- [2026-03-31] Implementación de EPIC-004: Time-Machine Debugging (ErrorListener con triggers para 4xx/5xx, ErrorReplay para re-ejecutar requests fallidos)
- [2026-03-31] Implementación de EPIC-005: Vue/Tailwind Real-Time Dashboard (WebSocket bridge, LiveTraffic view, ManualTester view)
- [2026-03-31] Implementación de EPIC-006: TradingView API Traffic Charts (TrafficChartAnalyzer con detección de errores 500, clusters de errores, time range slider)
- [2026-03-31] Implementación de EPIC-007: AI Prompt Command Center (AICommandCenter.vue, ai_command_center.py, Chat UI con ejecución de comandos)
- [2026-03-31] Implementación de EPIC-008: Data Anonymization & Security Filter (pii_masking existente, nuevo CLI commands pii config/test/status)
- [2026-03-31] Implementación de EPIC-009: Real-Time Flakiness Detection & Self-Healing (FlakinessDashboard.vue con matriz de flakiness y auto-healing)
- [2026-03-31] Implementación de EPIC-010: Microservices Dependency Graph Map (DependencyGraphAnalyzer, TopologyGraph.vue con visualización D3-style SVG, WebSocket /ws/topology)
- [2026-03-31] Implementación de EPIC-011: Chaos Engineering Traffic Correlation (ChaosEventRegistry, ChaosTrafficCorrelator para vincular inyecciones de caos con tráfico, integración con TradingView charts para mostrar marcadores de caos, análisis de IA para indicar si errores fueron causados por experimentos de caos)
- [2026-03-31] Implementación de EPIC-012: Staging/Prod Remote Cluster Synchronization (ClusterManager con soporte PostgreSQL/Redis para almacenamiento remoto, ClusterSelector en Settings del dashboard, WebSocket /ws/cluster para gestión de clusters, conexiones TLS/mTLS)
- [2026-03-31] Implementación de EPIC-013: Real-time AI Alerting & Notification Engine (AlertRuleEngine para umbrales, AIAlertAnalyzer para root cause analysis, NotificationManager con soporte nativo para Slack, Teams, Discord y webhooks genéricos)
- [2026-03-31] Implementación de EPIC-014: Database State Snapshot & Sandbox for Replays (DatabaseSnapshotManager para capturar estado de BD, SandboxEnvironment para entornos aislados, DatabaseReplayCoordinator que vincula snapshots con Time-Machine IDs)
- [2026-03-31] Implementación de EPIC-015: AI Performance Anomaly Detection (PerformanceMetricsCollector para收集 latencias p95/p99, AnomalyDetector con detección de desviación estándar, alertas de degradación en dashboard)
- [2026-03-31] Implementación de EPIC-016: Traffic Replay Speed & Playback Controls (TrafficReplayEngine con controles Play/Pause/Rw/Fw/Speed, soporte para speeds 0.25x a 8x, callback para assertions durante replay)
- [2026-03-31] Implementación de EPIC-017: Community Plugin & Extension Architecture (PluginManager con lifecycle hooks, Plugin base class para interceptores/generadores, integración con CLI e2e community plugin install)
- [2026-03-31] Implementación de EPIC-018: Autonomous Source Code Auto-Fixing (AutoFixOrchestrator para análisis de stack traces y generación de parches, GitIntegration para crear branches y commits, PRCreator con soporte para GitHub/GitLab/Bitbucket)
- [2026-03-31] Implementación de EPIC-019: Global Swarm Intelligence (SwarmOrchestrator para orchestrar testing distribuido, ServerlessAdapter para AWS Lambda/GCP Functions, métricas geo-latencia para world map visualization)
- [2026-03-31] Implementación de EPIC-020: Zero-Day Vulnerability Predictive Fuzzing (SecurityFuzzingAgent con RAG, CVEFeedConnector para alimentar MITRE CVEs, PayloadGenerator para mutaciones de JWT/SQLi/XSS/IDOR, generación de reportes en Markdown)
- [2026-03-31] Implementación de EPIC-021: API Evolution & Auto-Contract Versioning (SemanticDiffEngine para comparar responses, ContractAutoUpdater para actualizar contratos automáticamente, BreakingChangeAlert para notificar cambios breaking)
- [2026-03-31] Implementación de EPIC-022: Predictive Kubernetes Auto-Scaling Recommender (KubernetesRecommender para analizar métricas CPU/mem/latency, generación de HPA YAMLs, Docker Compose override con resources limits)
- [2026-03-31] Implementación de EPIC-023: Voice/NLP Command Interface (VoiceInterface con NLPParser para mapping voz-a-comandos, CommandExecutor para ejecución, integración con Web Speech API y TTS)
- [2026-03-31] Implementación de EPIC-024: Semantic User Journey Mapping (JourneyMapper para analizar tráfico HTTP y detectar pantallas, generación de Playwright UI test drafts, sequence diagram en formato Mermaid)

---

### OpenCode Build Agent (Continuación 2026)

### OpenCode Documentation Agent

**Plataforma:** [OpenCode](https://opencode.ai)  
**Modelo Base:** nemotron-3-super-free  
**Rol:** Mejora de documentación y guía para agentes IA  

**Contribuciones Principales:**
- 📖 Mejora significativa de `AGENT_GUIDE.md` con:
  - Tarjeta de referencia rápida de las 5 reglas de oro
  - Sección de errores letales específicos de agentes IA
  - Flujo de trabajo recomendado con caso práctico end-to-end
  - Guía para aprovechar capacidades de IA del framework (manifest, búsqueda semántica, generación autónoma de tests)
  - Integración con otras guías del directorio .agent/
  - Detección de anti-patrones para agentes IA
  - Protocolo de verificación mejorado
  - Workflows para resolución de issues específicos (timeouts, imports relativos)
  - Mecanismo para que los agentes contribuyan con experiencias para mejorar el framework
- 🗺️ Movimiento de todas las issues del roadmap (01-foundation a 05-observability-dashboard) a la carpeta de finalizados tras verificar su implementación en el códigobase

**Sesiones Notables:**
- [2026-03-30] Mejora integral de AGENT_GUIDE.md y actualización del roadmap de issues completadas

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

### OpenCode minimax-m2.5-free (OpenCode)

**Plataforma:** [OpenCode](https://opencode.ai)
**Modelo:** minimax-m2.5-free
**Rol:** Implementación de Features y Testing

**Contribuciones Principales:**
- 🎯 Completado el Roadmap de 5 Fases del proyecto
- 🏗️ Fase 1: Sistema de migración de configuración, fixes de encoding UTF-8
- 🔍 Fase 2: Ruby detection, comandos --use-manifest, --to-manifest, --sync-index
- 🔬 Fase 3: Comparación semántica para shadow replay
- 🛡️ Fase 4: Verificación de features existentes (FlowTestGenerator, LogicDrift, etc.)
- 📊 Fase 5: Implementación completa del módulo de observabilidad (metrics, tracing, logging)
- 🧪 39+ tests implementados/verificados

**Sesiones Notables:**
- [2026-03-29] Fix de 25 tests de observabilidad - implementación de TraceSpan, MetricsCollector, TelemetryManager, StructuredLogger

---

## Historial de Contribuciones por Fecha

### Marzo 2026

#### 2026-03-24 - Visión Arquitectónica Definitiva "Singularity API Observability" (25 Epics)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Arquitectura / Visión Sci-Fi
**Impacto:** Crítico / Revolucionario

**Descripción:**
Desglose conceptual definitivo que transforma el framework `socialseed-e2e` en el ecosistema QA, Seguridad y Observabilidad más ambicioso del mundo ("Singularity Nivel").
La arquitectura cubre módulos Fundamentales (Traffic Sniffer, Auto-Test Generation, TradingView Dashboard), Avanzados (Anonimización PII, Time-Machine Sandbox, AI Performance Anomalies) y **Revolucionarios (Nivel Máximo)**: 
*   **Auto-Fixing Source Code**: IA redactando PRs al detectar fugas en código fuente.
*   **Zero-Day Predictive Fuzzing**: Integración hiper-activa RAG de Seguridad para vulnerabilidades en vivo (BOLA, IDOR).
*   **Global Swarm Intelligence**: Bots Serverless inyectando fallos de latencia de manera distribuida a nivel global.
*   **Voice/NLP Operations**: Manejo del framework 100% por comandos de voz libres de manos.
*   **Predictive Kubernetes Auto-Scaler**: Escalamiento automático proactivo ante métricas predichas por la IA.
*   **Omniscient Graph Brain**: Un Super-Grafo Vectorial fusionando 24 ecosistemas distintos en una sola entidad.

**Archivos Creados/Modificados:**
- `.issues/vision_v2/` - Generación Masiva de **25 Epics y ~85 Tasks**, definiendo el pináculo absoluto de este framework.
- `scripts/gen_more_vision_issues*.py` - 4 Scripts generadores automatizados.
- `.agent/REAL_ENVIRONMENT_TESTING.md` - Guía estricta para forzar a todos los agentes a testear obligatoriamente sobre la red real Dockerizada de SocialSeed.

**Decisiones Importantes:**
1. **Testing Estricto al Entorno Real:** Prohibición estricta de "tests en el aire". Todo el ecosistema (incluso el Swarm Intelligence) DEBE someter a prueba sus hipótesis desplegándose en `D:\.dev\proyectos\SocialSeed\testing` contra los contenedores `auth` o `socialuser`.
2. **Generación Sistemática Definitiva:** Creación del roadmap de 25 Epics completas para llevar `socialseed-e2e` de un proyecto prometedor a un unicornio tecnológico sin precedentes.

### Febrero 2026

#### 2026-02-19 - Verificación y Documentación Integral del Framework (Issues Varios)
**Agente:** minimax-m2.5-free (OpenCode)
**Tipo:** Bugfix / Documentación / Testing
**Impacto:** Alto

**Descripción:**
Verificación completa del framework socialseed-e2e para asegurar que los agentes de IA puedan usarlo sin problemas. Se realizaron múltiples arreglos críticos y mejoras de documentación.

**Arreglos Realizados:**
1. **Fix config_loader null handling**: Corregido el manejo de `services: null` y `databases: null` en YAML usando el patrón `or {}` para evitar errores `'NoneType' object has no attribute 'items'`

2. **Fix LSP warnings**: Verificación de imports y tipos en cli.py, confirmando que los warnings son solo type hints que no afectan runtime

3. **Fix pytest-timeout**: Removida dependencia obligatoria de pytest-timeout de pyproject.toml ya que requiere instalación de paquetes del sistema

4. **Verificación de comandos CLI**: Testing completo del flujo de trabajo:
   - `e2e init` → `e2e new-service` → `e2e new-test` → `e2e run`
   - `e2e config`, `e2e doctor`, `e2e lint`
   - `e2e set url`, `e2e install-demo`, `e2e manifest`

**Documentación Creada:**
- `.agent/TROUBLESHOOTING.md` - Guía de troubleshooting para agentes de IA
- `.agent/REST_TESTING.md` - Guía completa de testing de APIs REST
- `.agent/GRPC_TESTING.md` - Guía completa de testing de APIs gRPC

**Archivos Modificados:**
- `src/socialseed_e2e/core/config_loader.py` - Fix null handling
- `pyproject.toml` - Remover pytest-timeout obligatorio
- `.agent/TROUBLESHOOTING.md` - Nuevo archivo
- `.agent/REST_TESTING.md` - Nuevo archivo
- `.agent/GRPC_TESTING.md` - Nuevo archivo

**Decisiones Importantes:**
1. **Patrón `or {}`**: Se usó para manejar tanto casos de diccionario vacío como valores null en YAML
2. **pytest-timeout opcional**: Se movió de dependencias obligatorias a opcionales para facilitar la instalación
3. **Verificación manual**: Se prefieren tests manuales exhaustivos sobre tests automatizados para validar el flujo completo de usuario

---

### Febrero 2026

#### 2026-02-12 - Record and Replay Test Sessions (Issue #121)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Recorder
**Impacto:** Medio

**Descripción:**
Implementación de un grabador interactivo para capturar tráfico de API manual. Incluye un servidor proxy de grabación, modelos para persistencia de sesiones en JSON, un reproductor directo y un conversor de sesiones a módulos de prueba de Python compatibles con el framework.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/recorder/` - Nuevo paquete del grabador
- `src/socialseed_e2e/recorder/proxy_server.py` - Proxy de interceptación
- `src/socialseed_e2e/recorder/converter.py` - Generador de código Python
- `docs/recorder.md` - Documentación del grabador
- `src/socialseed_e2e/cli.py` - Nuevos comandos `e2e recorder [record|replay|convert]`

---

#### 2026-02-12 - Comprehensive Assertion Library (Issue #120)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / DSL
**Impacto:** Medio-Alto

**Descripción:**
Creación de una biblioteca de aserciones enriquecida y semántica. Incluye validación de esquemas JSON, aserciones específicas para GraphQL (datos y errores), validaciones temporales (ISO 8601, latencia), métricas estadísticas (percentiles, outliers) y aserciones avanzadas sobre colecciones.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/assertions/` - Nuevo paquete de aserciones
- `src/socialseed_e2e/assertions/base.py` - API fluida `expect()` y excepciones base
- `src/socialseed_e2e/assertions/json_schema.py` - Integración con jsonschema
- `src/socialseed_e2e/assertions/graphql.py` - Validaciones de respuestas GraphQL
- `docs/assertions.md` - Documentación detallada de la biblioteca
- `services/example_service/modules/04_assertions_demo.py` - Ejemplo práctico de uso

**Decisiones Importantes:**
1. **Fluent API**: Se implementó el patrón *Fluent Interface* para permitir aserciones encadenables y legibles.
2. **Contextual Errors**: La excepción `E2EAssertionError` captura metadatos detallados (esperado vs actual) para mejorar la trazabilidad en fallos.

---

#### 2026-02-12 - Advanced Test Organization with Tags and Dependencies (Issue #119)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Test Lifecycle
**Impacto:** Alto

**Descripción:**
Implementación de un sistema robusto de organización de pruebas. Incluye decoradores `@tag`, `@depends_on` y `@priority`, permitiendo la selección dinámica de pruebas por etiquetas y el ordenamiento inteligente basado en dependencias y niveles de importancia.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/core/organization.py` - Lógica de etiquetado y ordenamiento topológico
- `src/socialseed_e2e/core/test_runner.py` - Integración con el motor de ejecución secuencial
- `src/socialseed_e2e/core/parallel_runner.py` - Soporte para filtrado en ejecución paralela
- `src/socialseed_e2e/cli.py` - Nuevas opciones `--tag` y `--exclude-tag`
- `docs/test-organization.md` - Guía de organización de tests

**Decisiones Importantes:**
1. **Topological Sort**: Se utilizó el algoritmo de Kahn para resolver las dependencias entre módulos de prueba de forma determinista.
2. **Metadata Injection**: Se implementó una inyección de metadatos ligera en las funciones `run` para evitar cambios disruptivos en la firma de las funciones existentes.

---

#### 2026-02-12 - Advanced Performance and Load Testing (Issue #118)
**Agente:** Antigravity (Google DeepMind)
**Tipo:** Feature / Performance Testing
**Impacto:** Alto

**Descripción:**
Evolución de las capacidades de performance del framework. Se implementó un motor de generación de carga asíncrono, soporte para patrones de ramp-up, validación automática de SLAs (latencia P95, tasa de error) y un generador de dashboards visuales en HTML.

**Archivos Creados/Modificados:**
- `src/socialseed_e2e/performance/load_generator.py` - Motor de carga concurrente
- `src/socialseed_e2e/performance/metrics_collector.py` - Análisis estadístico y SLAs
- `src/socialseed_e2e/performance/dashboard.py` - Visualización de métricas en HTML
- `docs/advanced-performance.md` - Guía de testing de carga

**Decisiones Importantes:**
1. **Asynchronous I/O**: El generador utiliza `asyncio` para simular cientos de usuarios concurrentes de forma eficiente en un solo proceso.
2. **Self-Contained Dashboards**: Los reportes HTML incluyen Chart.js vía CDN para ser ligeros y visualmente impactantes sin dependencias locales.

---

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
| minimax-m2.5-free | 1+ | 5+ | ~150 | 3 archivos |

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

**Última actualización:** 2026-02-19
**Mantenedor:** Dairon Pérez (@daironpf)
**Contacto:** Para agregar contribuciones de IA, crear un PR actualizando este archivo.

---

*"El futuro del desarrollo de software es colaborativo: humanos e IA trabajando juntos, reconociendo mutuamente sus aportes."*
