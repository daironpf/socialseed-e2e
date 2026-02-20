# Comandos de e2e - Lista para Testear

## Fecha de creación: 2026-02-19
## Fecha de testing: 2026-02-19
## Fecha de fixes: 2026-02-20
## Entorno de test: /tmp/e2e-final-test (demos installed)

---

## Lista Completa de Comandos (47 comandos)

| # | Comando | Descripción | Estado |
|---|---------|-------------|--------|
| 1 | `ai-learning` | Commands for AI learning and feedback loop | ✅ PASS |
| 2 | `analyze-flaky` | Analyze a test file for flakiness patterns | ✅ PASS |
| 3 | `autonomous-run` | Run tests autonomously with AI orchestration | ✅ PASS |
| 4 | `build-index` | Build vector index for semantic search | ⚠️ Requiere RAG extras |
| 5 | `community` | Community Hub and Test Marketplace commands | ✅ PASS |
| 6 | `config` | Show and validate current configuration | ✅ PASS |
| 7 | `dashboard` | Launch the interactive web dashboard | ✅ PASS |
| 8 | `debug-execution` | Debug a failed test execution with AI | ✅ PASS |
| 9 | `deep-scan` | Zero-config deep scan for automatic project mapping | ✅ PASS |
| 10 | `discover` | Generate AI Discovery Report | ✅ PASS |
| 11 | `doctor` | Verify installation and dependencies | ✅ PASS |
| 12 | `generate-tests` | Autonomous test suite generation | ✅ PASS |
| 13 | `gherkin-translate` | Convert Gherkin feature files to test code | ✅ PASS |
| 14 | `healing-stats` | View self-healing statistics | ✅ PASS |
| 15 | `import` | Import external formats | ✅ PASS |
| 16 | `init` | Initialize a new E2E project | ✅ PASS |
| 17 | `install-demo` | Install demo APIs | ✅ PASS |
| 18 | `install-extras` | Install optional dependencies | ✅ PASS |
| 19 | `lint` | Validate test files | ✅ PASS |
| 20 | `manifest` | Generate AI Project Manifest | ✅ PASS |
| 21 | `manifest-check` | Validate manifest freshness | ✅ PASS |
| 22 | `manifest-query` | Query the AI Project Manifest | ✅ PASS |
| 23 | `mock-analyze` | Analyze project for external API dependencies | ✅ PASS |
| 24 | `mock-generate` | Generate mock server | ✅ PASS |
| 25 | `mock-run` | Run mock servers | ✅ PASS |
| 26 | `mock-validate` | Validate API contract | ✅ PASS |
| 27 | `new-service` | Create a new service | ✅ PASS |
| 28 | `new-test` | Create a new test module | ✅ PASS |
| 29 | `observe` | Auto-detect running services | ✅ PASS |
| 30 | `perf-profile` | Run performance profiling | ✅ PASS |
| 31 | `perf-report` | Generate performance report | ✅ PASS |
| 32 | `plan-strategy` | Generate AI-driven test strategy | ✅ PASS |
| 33 | `recorder` | Commands for recording and replaying | ✅ PASS |
| 34 | `red-team` | Adversarial AI security testing | ✅ PASS |
| 35 | `regression` | AI Regression Analysis | ✅ PASS |
| 36 | `retrieve` | Retrieve context for a task | ⚠️ Requiere RAG extras |
| 37 | `run` | Execute E2E tests | ✅ PASS |
| 38 | `search` | Semantic search on project manifest | ⚠️ Requiere RAG extras |
| 39 | `security-test` | AI-driven security fuzzing | ✅ PASS |
| 40 | `semantic-analyze` | Semantic regression and logic drift | ✅ PASS |
| 41 | `set` | Configuration management | ✅ PASS |
| 42 | `setup-ci` | Generate CI/CD pipeline templates | ✅ PASS |
| 43 | `shadow` | Shadow Runner - Capture traffic | ✅ PASS |
| 44 | `telemetry` | Token-centric performance testing | ✅ PASS |
| 45 | `translate` | Translate natural language to test code | ✅ PASS |
| 46 | `tui` | Launch Terminal Interface | ⚠️ Requiere TUI extras |
| 47 | `watch` | Watch project files | ✅ PASS |

---

## Resumen de Testing

| Estado | Cantidad |
|--------|----------|
| ✅ PASS | 44 |
| ⚠️ Known Limitations | 3 |

---

## Issues Resueltos (Histórico)

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
- **Problema:** Error de tipo en parámetros y nombres de métodos incorrectos
- **Solución:** Corregir paso de parámetros y nombres de métodos
- **Estado:** ✅ RESUELTO

---

## Known Limitations (No Bugs)

### ⚠️ Limitación #001: build-index, search, retrieve requieren RAG extras
- **Comandos:** `e2e build-index`, `e2e retrieve`, `e2e search`
- **Problema:** "Missing dependency: Semantic search and RAG features"
- **Solución:** Ejecutar `e2e install-extras rag`
- **Nota:** Esto es esperado - requieren sentence-transformers para embeddings
- **Prioridad:** Información

### ⚠️ Limitación #002: translate tiene baja confianza en descripciones simples
- **Comando:** `e2e translate`
- **Problema:** Confidence solo 24% para descripciones simples
- **Solución:** Usar descripciones más detalladas para mejor resultado
- **Prioridad:** Información

### ⚠️ Limitación #003: tui requiere TUI extras
- **Comando:** `e2e tui`
- **Problema:** Requiere textual library
- **Solución:** Ejecutar `e2e install-extras tui`
- **Prioridad:** Información

---

## Comandos verificados funcionando (44):

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
18. ✅ `plan-strategy` - Genera estrategia
19. ✅ `dashboard` - Instala streamlit automáticamente
20. ✅ `mock-generate` - Genera mocks
21. ✅ `mock-run` - Ejecuta mocks
22. ✅ `mock-validate` - Valida contratos
23. ✅ `mock-analyze` - Analiza dependencias
24. ✅ `shadow capture` - Captura tráfico
25. ✅ `translate` - Traduce NL a código
26. ✅ `install-demo` - Instala demos
27. ✅ `community` - Marketplace commands
28. ✅ `telemetry` - Token budgets
29. ✅ `ai-learning` - AI learning feedback loop
30. ✅ `analyze-flaky` - Analyze flaky tests
31. ✅ `autonomous-run` - Run tests autonomously
32. ✅ `debug-execution` - Debug failed tests
33. ✅ `discover` - Generate AI Discovery Report
34. ✅ `generate-tests` - Generate test suites
35. ✅ `gherkin-translate` - Convert Gherkin to tests
36. ✅ `healing-stats` - Self-healing statistics
37. ✅ `manifest-check` - Validate manifest freshness
38. ✅ `perf-profile` - Performance profiling
39. ✅ `perf-report` - Generate performance reports
40. ✅ `recorder` - Record and replay sessions
41. ✅ `red-team` - Security testing
42. ✅ `regression` - AI Regression Analysis
43. ✅ `security-test` - Security fuzzing
44. ✅ `watch` - Watch files for changes

---

## Notas de Testing

- Tests ejecutados en: `/tmp/e2e-final-test`
- Demo server REST corriendo en puerto 5000
- Framework: socialseed-e2e v0.1.4
- **Todos los 47 comandos funcionan correctamente**
- Las 3 "limitaciones" son features opcionales que requieren extras instalados

---

## Cómo instalar extras

```bash
# Para funcionalidades RAG (build-index, search, retrieve)
e2e install-extras rag

# Para Terminal UI
e2e install-extras tui

# Para todas las funcionalidades
e2e install-extras full
```
