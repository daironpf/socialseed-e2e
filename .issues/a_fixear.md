# Issues a Fixear

## Resumen de Testing
Fecha: 2026-02-22
Framework: socialseed-e2e v0.1.5
Entorno: Python 3.12, Ubuntu

## Estado: PARCIALMENTE RESUELTO

### Issues Resueltos:

✅ **Issue 1: Falta pytest como dependencia** - RESUELTO
- Agregado pytest>=7.0.0 a dependencias en pyproject.toml

✅ **Issue 2: RuntimeWarning de coroutine no awaitada** - RESUELTO
- Corregido test_runner.py para manejar funciones async con asyncio.iscoroutinefunction()

✅ **Issue 5: ShadowRunner.analyze_capture** - RESUELTO
- Agregado método analyze_capture a ShadowRunner
- Corregido shadow analyze command en cli.py

✅ **Issue 6: Errores de tipo en LSP** - RESUELTO
- Corregidos tipos en runner.py, resource_agent.py, flakiness_predictor.py

---

## Issues Pendientes:

### Issue 3: Tests con formato incorrecto (falta función run)
**Severidad:** Media
**Descripción:** Algunos módulos de test generados no tienen la función `run()` requerida.
**Archivos afectados (en entorno de demo):**
- services/chat-demo/modules/01_auth.py
- services/booking-demo/modules/08_waitlist.py
- services/booking-demo/modules/10_booking_workflow.py

**Comando afectado:** `e2e run`
**Solución:** Revisar las plantillas de generación de demos para asegurar que incluyen función run()

```
Error: No 'run' function found in module
```

---

### Issue 4: Módulos de demo no instalados completamente
**Severidad:** Baja
**Descripción:** Algunos servicios de demo no tienen URLs configuradas en e2e.conf después de install-demo.
**Servicios afectados:**
- filestorage-demo
- payments-demo
- social-demo

**Comando afectado:** `e2e config`, `e2e run`
**Solución:** Actualizar install-demo para configurar automáticamente las URLs de todos los servicios.

---

### Issue 4: Módulos de demo no instalados completamente
**Severidad:** Baja
**Descripción:** Algunos servicios de demo no tienen URLs configuradas en e2e.conf después de install-demo.
**Servicios afectados:**
- filestorage-demo
- payments-demo  
- social-demo

**Comando afectado:** `e2e config`, `e2e run`
**Solución:** Actualizar install-demo para configurar automáticamente las URLs de todos los servicios.

---

### Issue 5: Error en ShadowRunner.analyze_capture
**Severidad:** Alta
**Descripción:** El comando `e2e shadow analyze` falla porque ShadowRunner no tiene el método analyze_capture.
**Ubicación:** src/socialseed_e2e/shadow_runner/runner.py
**Comando afectado:** `e2e shadow analyze`
**Error LSP:**
```
ERROR [130:27] Cannot access attribute "analyze_capture" for class "ShadowRunner"
  Attribute "analyze_capture" is unknown
```
**Solución:** Agregar el método analyze_capture a la clase ShadowRunner o actualizar el comando para usar el método correcto.

---

### Issue 6: Errores de tipo en modelos Pydantic
**Severidad:** Baja
**Descripción:** Hay varios errores de tipo en el código que causan warnings del LSP.
**Archivos afectados:**
- src/socialseed_e2e/shadow_runner/runner.py
- src/socialseed_e2e/agents/resource_optimizer/resource_agent.py
- src/socialseed_e2e/ai_orchestrator/flakiness_predictor.py

**Comando afectado:** Ninguno (solo warnings)
**Solución:** Corregir las anotaciones de tipo.

---

## Notas

- Los módulos nuevos implementados (debugging, ai_mocking stateful, security PII, nlp living_docs, agents xai, core ml_orchestrator) funcionan correctamente cuando se importan.
- El comando `e2e shadow fuzz` está disponible y funciona.
- Los tests básicos pasan correctamente para demo-api y ecommerce-demo.

## Recomendaciones

1. Agregar pytest como dependencia required en pyproject.toml
2. Revisar y corregir el manejo de corutinas en test_runner.py
3. Verificar que todos los módulos de test generados tengan la función run()
4. Agregar método analyze_capture a ShadowRunner o actualizar shadow_cmd.py
5. Actualizar install-demo para configurar todas las URLs de servicios
