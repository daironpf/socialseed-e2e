# Issues a Fixear

## Resumen de Testing
Fecha: 2026-02-22
Framework: socialseed-e2e v0.1.5
Entorno: Python 3.12, Ubuntu

## Estado: RESUELTO

### Issues Resueltos:

✅ **Issue 1: Falta pytest como dependencia** - RESUELTO
- Agregado pytest>=7.0.0 a dependencias en pyproject.toml

✅ **Issue 2: RuntimeWarning de coroutine no awaitada** - RESUELTO
- Corregido test_runner.py para manejar funciones async con asyncio.iscoroutinefunction()

✅ **Issue 3: Tests con formato incorrecto (falta función run)** - RESUELTO
- Agregada función `run()` a todas las plantillas de demo que faltaban:
  - chat_test_01_auth.py.template
  - chat_test_04_rooms.py.template
  - chat_test_05_messages.py.template
  - chat_test_06_membership.py.template
  - chat_test_07_typing.py.template
  - chat_test_08_reactions.py.template
  - chat_test_09_threads.py.template
  - chat_test_10_chat_workflow.py.template
  - booking_test_08_waitlist.py.template
  - booking_test_10_booking_workflow.py.template
  - notifications_test_04_channels.py.template
  - notifications_test_05_templates.py.template
  - notifications_test_06_webhooks.py.template
  - notifications_test_10_notifications_workflow.py.template

✅ **Issue 4: Módulos de demo no instalados completamente** - RESUELTO
- Actualizado install_demo_cmd.py para agregar los servicios faltantes:
  - filestorage-demo (puerto 5008)
  - social-demo (puerto 5009)
  - payments-demo (puerto 5010)

✅ **Issue 5: ShadowRunner.analyze_capture** - RESUELTO
- Agregado método analyze_capture a ShadowRunner
- Corregido shadow analyze command en cli.py

✅ **Issue 6: Errores de tipo en LSP** - RESUELTO
- Corregidos tipos en runner.py, resource_agent.py, flakiness_predictor.py

---

## Issues Pendientes:

(None - all issues resolved)

---

## Notas

- Los módulos nuevos implementados (debugging, ai_mocking stateful, security PII, nlp living_docs, agents xai, core ml_orchestrator) funcionan correctamente cuando se importan.
- El comando `e2e shadow fuzz` está disponible y funciona.
- Los tests básicos pasan correctamente para demo-api y ecommerce-demo.

## Verificación de Fixes (2026-02-22)

Se ejecutó el ciclo completo de testing:

1. **Instalación limpia**: `e2e init` + `e2e install-demo --force`
2. **Ejecución de tests**: `e2e run --service demo-api` 
3. **Resultado**: 3/3 tests passed (100%)

### Fixes adicionales realizados durante el ciclo:

1. **Templates convertidos a sync**: 
   - 40+ plantillas de test convertidas de async a sync
   - Corregido el formato de URLs (de `f"{BASE_URL}/endpoint"` a `/endpoint`)
   - Corregido el bloque `__main__` para usar sync Playwright

2. **BasePage.post() mejorado**:
   - Agregado parámetro `params` faltante

3. **Test runner mejorado**:
   - Mejor manejo de funciones async con asyncio.run()

## Recomendaciones

1. Agregar pytest como dependencia required en pyproject.toml ✅
2. Revisar y corregir el manejo de corutinas en test_runner.py ✅
3. Verificar que todos los módulos de test generados tengan la función run() ✅
4. Agregar método analyze_capture a ShadowRunner o actualizar shadow_cmd.py ✅
5. Actualizar install-demo para configurar todas las URLs de servicios ✅
