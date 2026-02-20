# Comandos de e2e - Lista para Testear

## Fecha de creación: 2026-02-19
## Fecha de testing: 2026-02-19
## Entorno de test: /tmp/e2e-test-v2 (demos installed)

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
| 7 | `dashboard` | Launch the interactive web dashboard | ⚠️ Requiere streamlit |
| 8 | `debug-execution` | Debug a failed test execution with AI | ⏳ No testado |
| 9 | `deep-scan` | Zero-config deep scan for automatic project mapping | ✅ PASS |
| 10 | `discover` | Generate AI Discovery Report | ⏳ No testado |
| 11 | `doctor` | Verify installation and dependencies | ✅ PASS |
| 12 | `generate-tests` | Autonomous test suite generation | ⏳ No testado |
| 13 | `gherkin-translate` | Convert Gherkin feature files to test code | ⏳ No testado |
| 14 | `healing-stats` | View self-healing statistics | ⏳ No testado |
| 15 | `import` | Import external formats | ✅ PASS (help verificado) |
| 16 | `init` | Initialize a new E2E project | ✅ PASS |
| 17 | `install-demo` | Install demo APIs | ✅ PASS |
| 18 | `install-extras` | Install optional dependencies | ✅ PASS |
| 19 | `lint` | Validate test files | ✅ PASS |
| 20 | `manifest` | Generate AI Project Manifest | ✅ PASS |
| 21 | `manifest-check` | Validate manifest freshness | ⏳ No testado |
| 22 | `manifest-query` | Query the AI Project Manifest | ✅ PASS |
| 23 | `mock-analyze` | Analyze project for external API dependencies | ⏳ No testado |
| 24 | `mock-generate` | Generate mock server | ⚠️ Issue #191 |
| 25 | `mock-run` | Run mock servers | ⚠️ Issue #191 |
| 26 | `mock-validate` | Validate API contract | ⚠️ Issue #191 |
| 27 | `new-service` | Create a new service | ✅ PASS |
| 28 | `new-test` | Create a new test module | ✅ PASS |
| 29 | `observe` | Auto-detect running services | ✅ PASS |
| 30 | `perf-profile` | Run performance profiling | ⚠️ Requiere dependencias |
| 31 | `perf-report` | Generate performance report | ⏳ No testado |
| 32 | `plan-strategy` | Generate AI-driven test strategy | ⚠️ Requiere manifest local |
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
| 43 | `shadow` | Shadow Runner - Capture traffic | ⚠️ Issue #194 |
| 44 | `telemetry` | Token-centric performance testing | ✅ PASS |
| 45 | `translate` | Translate natural language to test code | ⚠️ Baja confianza (24%) |
| 46 | `tui` | Launch Terminal Interface | ⚠️ Requiere dependencias |
| 47 | `watch` | Watch project files | ⏳ No testado |

---

## Resumen de Testing

| Estado | Cantidad |
|--------|----------|
| ✅ PASS | 17 |
| ⚠️ Issues | 12 |
| ⏳ No testado | 18 |

---

## Issues Encontrados

### Issue #001: dashboard requiere streamlit
- **Comando:** `e2e dashboard`
- **Estado:** ⚠️ Falla sin streamlit
- **Solución:** Instalar streamlit o agregar a extras
- **Prioridad:** Media

### Issue #002: build-index requiere RAG extras
- **Comando:** `e2e build-index`
- **Error:** "Missing dependency: Semantic search and RAG features"
- **Solución:** Ejecutar `e2e install-extras rag`
- **Prioridad:** Media

### Issue #003: search requiere RAG extras
- **Comando:** `e2e search`
- **Error:** "Missing dependency: Semantic search and RAG features"
- **Solución:** Ejecutar `e2e install-extras rag`
- **Prioridad:** Media

### Issue #004: retrieve requiere RAG extras
- **Comando:** `e2e retrieve`
- **Error:** "Missing dependency: Semantic search and RAG features"
- **Solución:** Ejecutar `e2e install-extras rag`
- **Prioridad:** Media

### Issue #005: translate tiene baja confianza
- **Comando:** `e2e translate -d "Test that health endpoint returns 200"`
- **Observación:** Confidence solo 24%
- **Solución:** Mejorar el NLP engine
- **Prioridad:** Alta

### Issue #006: plan-strategy requiere manifest local
- **Comando:** `e2e plan-strategy`
- **Error:** "Manifest not found at /tmp/e2e-test-v2/project_knowledge.json"
- **Nota:** El manifest se guarda en el framework, no en el proyecto
- **Solución:** Necesita investigación
- **Prioridad:** Alta

### Issue #007: autonomous-run requiere strategy-id
- **Comando:** `e2e autonomous-run`
- **Error:** Falta --strategy-id
- **Solución:** Primero ejecutar plan-strategy
- **Prioridad:** Baja

### Issue #008: mock-generate no implementado
- **Comando:** `e2e mock-generate`
- **Nota:** Issue #191 - No implementado aún
- **Prioridad:** Media

### Issue #009: mock-run no implementado
- **Comando:** `e2e mock-run`
- **Nota:** Issue #191 - No implementado aún
- **Prioridad:** Media

### Issue #010: mock-validate no implementado
- **Comando:** `e2e mock-validate`
- **Nota:** Issue #191 - No implementado aún
- **Prioridad:** Media

### Issue #011: shadow capture no implementado
- **Comando:** `e2e shadow capture`
- **Nota:** Issue #194 - No implementado aún
- **Prioridad:** Alta

### Issue #012: semantic-analyze requiere dependencias
- **Comando:** `e2e semantic-analyze`
- **Error:** Faltan dependencias específicas
- **Solución:** Documentar dependencias necesarias
- **Prioridad:** Alta

### Issue #013: perf-profile requiere dependencias
- **Comando:** `e2e perf-profile`
- **Error:** Faltan dependencias específicas
- **Solución:** Documentar dependencias necesarias
- **Prioridad:** Alta

---

## Comandos que requieren más testing

```
ai-learning
analyze-flaky
debug-execution
discover
generate-tests
gherkin-translate
healing-stats
manifest-check
mock-analyze
perf-report
recorder
red-team
regression
security-test
watch
```

---

## Notas de Testing

- Tests ejecutados en: `/tmp/e2e-test-v2`
- Demo server REST corriendo en puerto 5000
- Servicios: demo-api y example instalados
- Framework: socialseed-e2e v0.1.4

### Comandos verificados funcionando:
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
