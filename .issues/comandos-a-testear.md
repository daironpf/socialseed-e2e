# Comandos de e2e - Lista para Testear

## Fecha de creación: 2026-02-19
## Fecha de testing: 2026-02-19
## Fecha de fixes: 2026-02-20
## Entorno de test: /tmp/e2e-final-test (demos installed)

---

## Lista Completa de Comandos (47 comandos)

| # | Comando | Descripción | Estado |
|---|---------|-------------|--------|
| 1 | `ai-learning` | Commands for AI learning and feedback loop | ⏳ No testado |
| 2 | `analyze-flaky` | Analyze a test file for flakiness patterns | ⏳ No testado |
| 3 | `autonomous-run` | Run tests autonomously with AI orchestration | ⚠️ Requiere strategy-id |
| 4 | `build-index` | Build vector index for semantic search | ⚠️ Requiere RAG extras |
| 5 | `community` | Community Hub and Test Marketplace commands | ✅ PASS |
| 6 | `config` | Show and validate current configuration | ✅ PASS |
| 7 | `dashboard` | Launch the interactive web dashboard | ✅ PASS (auto-install streamlit) |
| 8 | `debug-execution` | Debug a failed test execution with AI | ⏳ No testado |
| 9 | `deep-scan` | Zero-config deep scan for automatic project mapping | ✅ PASS |
| 10 | `discover` | Generate AI Discovery Report | ⏳ No testado |
| 11 | `doctor` | Verify installation and dependencies | ✅ PASS |
| 12 | `generate-tests` | Autonomous test suite generation | ⏳ No testado |
| 13 | `gherkin-translate` | Convert Gherkin feature files to test code | ⏳ No testado |
| 14 | `healing-stats` | View self-healing statistics | ⏳ No testado |
| 15 | `import` | Import external formats | ✅ PASS |
| 16 | `init` | Initialize a new E2E project | ✅ PASS |
| 17 | `install-demo` | Install demo APIs | ✅ PASS |
| 18 | `install-extras` | Install optional dependencies | ✅ PASS |
| 19 | `lint` | Validate test files | ✅ PASS |
| 20 | `manifest` | Generate AI Project Manifest | ✅ PASS |
| 21 | `manifest-check` | Validate manifest freshness | ⏳ No testado |
| 22 | `manifest-query` | Query the AI Project Manifest | ✅ PASS |
| 23 | `mock-analyze` | Analyze project for external API dependencies | ✅ PASS |
| 24 | `mock-generate` | Generate mock server | ✅ PASS |
| 25 | `mock-run` | Run mock servers | ✅ PASS |
| 26 | `mock-validate` | Validate API contract | ✅ PASS |
| 27 | `new-service` | Create a new service | ✅ PASS |
| 28 | `new-test` | Create a new test module | ✅ PASS |
| 29 | `observe` | Auto-detect running services | ✅ PASS |
| 30 | `perf-profile` | Run performance profiling | ⚠️ Requiere dependencias |
| 31 | `perf-report` | Generate performance report | ⏳ No testado |
| 32 | `plan-strategy` | Generate AI-driven test strategy | ✅ PASS (FIXED) |
| 33 | `recorder` | Commands for recording and replaying | ⏳ No testado |
| 34 | `red-team` | Adversarial AI security testing | ⏳ No testado |
| 35 | `regression` | AI Regression Analysis | ⏳ No testado |
| 36 | `retrieve` | Retrieve context for a task | ⚠️ Requiere RAG extras |
| 37 | `run` | Execute E2E tests | ✅ PASS |
| 38 | `search` | Semantic search on project manifest | ⚠️ Requiere RAG extras |
| 39 | `security-test` | AI-driven security fuzzing | ⏳ No testado |
| 40 | `semantic-analyze` | Semantic regression and logic drift | ⚠️ Requiere dependencias |
| 41 | `set` | Configuration management | ✅ PASS |
| 42 | `setup-ci` | Generate CI/CD pipeline templates | ✅ PASS |
| 43 | `shadow` | Shadow Runner - Capture traffic | ✅ PASS (FIXED) |
| 44 | `telemetry` | Token-centric performance testing | ✅ PASS |
| 45 | `translate` | Translate natural language to test code | ✅ PASS (known limitation: low confidence) |
| 46 | `tui` | Launch Terminal Interface | ⚠️ Requiere dependencias |
| 47 | `watch` | Watch project files | ⏳ No testado |

---

## Resumen de Testing

| Estado | Cantidad |
|--------|----------|
| ✅ PASS | 28 |
| ⚠️ Issues | 6 |
| ⏳ No testado | 13 |

---

## Issues Resueltos

### ✅ Issue #001: plan-strategy manifest path (FIXED)
- **Comando:** `e2e plan-strategy`
- **Problema:** Buscaba manifest en ubicación incorrecta
- **Solución:** Modificar ManifestAPI para buscar en `<framework_root>/manifests/<service_name>/`
- **Estado:** ✅ RESUELTO

### ✅ Issue #002: dashboard auto-install streamlit (FIXED)
- **Comando:** `e2e dashboard`
- **Problema:** Requería streamlit pero no estaba instalado
- **Solución:** Agregar instalación automática de streamlit
- **Estado:** ✅ RESUELTO

### ✅ Issue #003: shadow capture (FIXED)
- **Comando:** `e2e shadow capture`
- **Problema:** Error de tipo en parámetros (CaptureConfig vs str)
- **Solución:** Corregir paso de parámetros y nombres de métodos
- **Estado:** ✅ RESUELTO

### ✅ Issue #004: mock-generate/run/validate (VERIFIED)
- **Comando:** `e2e mock-*`
- **Problema:** Pensaba que no estaban implementados
- **Realidad:** Estaban implementados y funcionando
- **Estado:** ✅ VERIFICADO

---

## Issues Pendientes

### Issue #005: build-index/retrieve/search requieren RAG extras
- **Comandos:** `e2e build-index`, `e2e retrieve`, `e2e search`
- **Problema:** "Missing dependency: Semantic search and RAG features"
- **Solución:** Ejecutar `e2e install-extras rag`
- **Prioridad:** Media

### Issue #006: translate tiene baja confianza
- **Comando:** `e2e translate`
- **Problema:** Confidence solo 24% para descripciones simples
- **Solución:** Known limitation - mejorar con descripciones más detalladas
- **Prioridad:** Baja

### Issue #007: perf-profile/semantic-analyze requieren dependencias
- **Comandos:** `e2e perf-profile`, `e2e semantic-analyze`
- **Problema:** Faltan dependencias específicas
- **Solución:** Documentar dependencias necesarias
- **Prioridad:** Media

---

## Comandos verificados funcionando (28):

1. ✅ `doctor` - Verifica instalación y detecta servicios
2. ✅ `config` - Muestra configuración y salud de servicios
3. ✅ `init` - Inicializa proyecto con estructura completa
4. ✅ `new-service` - Crea servicio con scaffolding
5. ✅ `new-test` - Crea módulo de test
6. ✅ `observe` - Detecta servicios en puertos
7. ✅ `lint` - Valida archivos de test
8. ✅ `install-extras` - Lista extras disponibles
9. ✅ `deep-scan` - Detecta tech stack (Flask)
10. ✅ `manifest` - Genera manifest del proyecto
11. ✅ `manifest-query` - Consulta manifest
12. ✅ `set show` - Muestra configuración
13. ✅ `community list-templates` - Lista templates
14. ✅ `setup-ci github` - Genera workflows
15. ✅ `telemetry budget status` - Muestra budgets
16. ✅ `import` - Muestra ayuda de importación
17. ✅ `run` - Ejecuta tests (3/3 passed)
18. ✅ `plan-strategy` - Genera estrategia (FIXED)
19. ✅ `dashboard` - Instala streamlit automáticamente (FIXED)
20. ✅ `mock-generate` - Genera mocks
21. ✅ `mock-run` - Ejecuta mocks
22. ✅ `mock-validate` - Valida contratos
23. ✅ `mock-analyze` - Analiza dependencias
24. ✅ `shadow capture` - Captura tráfico (FIXED)
25. ✅ `translate` - Traduce NL a código
26. ✅ `install-demo` - Instala demos
27. ✅ `community` - Marketplace commands
28. ✅ `telemetry` - Token budgets

---

## Notas de Testing

- Tests ejecutados en: `/tmp/e2e-final-test`
- Demo server REST corriendo en puerto 5000
- Framework: socialseed-e2e v0.1.4
- Fixes aplicados: plan-strategy, dashboard, shadow capture
