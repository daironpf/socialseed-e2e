# SocialSeed E2E - Issues y Mejoras Pendientes

## Estado del Framework

**Versión funcional**: 23 de febrero 2026 (commit 110792f)
**Puntuación actual**: 7/10

---

## Issues Críticos (Alta Prioridad)

### [ISSUE-001] Documentación .agent/ insuficiente para agentes IA
**Estado**: ✅ CORREGIDO
**Descripción**: El README.md en .agent/ solo tenía 4 comandos básicos, insuficiente para que un agente IA trabaje sin explorar el código fuente.
**Solución**: Ampliado con ejemplos de código, patrones comunes, estructura completa del proyecto.

### [ISSUE-002] Faltan tests funcionales para los demos
**Estado**: ⚠️ PENDIENTE
**Descripción**: Los demos se instalan con `e2e install-demo` pero no hay tests que los prob automáticamente.
**Solución**: Crear tests automáticos para demos que verifiquen que los endpoints funcionan.

### [ISSUE-003] No hay verificación de dependencias post-instalación
**Estado**: ⚠️ PENDIENTE
**Descripción**: Después de `e2e init`, las dependencias opcionales (flask, rag, etc.) no se verifican automáticamente.
**Solución**: Agregar verificación y sugerencia de instalación en `e2e doctor` o al primer `e2e run`.

---

## Issues de Funcionalidad (Media Prioridad)

### [ISSUE-004] Falta comando para auto-detectar puertos de servicios
**Estado**: ⚠️ PENDIENTE
**Descripción**: El usuario debe configurar manualmente los puertos en e2e.conf.
**Solución**: Mejorar `e2e observe` para que detecte servicios en Docker y cree la configuración automáticamente.

### [ISSUE-005] No hay templates para servicios comunes
**Estado**: ⚠️ PENDIENTE
**Descripción**: Al crear un nuevo servicio, no hay templates para Spring Boot, FastAPI, Express, etc.
**Solución**: Crear templates de data_schema.py y _page.py para diferentes frameworks.

### [ISSUE-006] Falta generación automática de tests desde endpoints
**Estado**: ⚠️ PENDIENTE
**Descripción**: No hay forma de generar tests automáticamente desde los endpoints detectados.
**Solución**: Integrar con `e2e deep-scan` para generar skeletons de tests.

---

## Issues de Documentación (Baja Prioridad)

### [ISSUE-007] README.md del proyecto obsoleto
**Estado**: ⚠️ PENDIENTE
**Descripción**: El README.md principal no refleja el estado actual del framework.
**Solución**: Actualizar con features implementadas, comandos actuales, ejemplos.

### [ISSUE-008] Falta guía de contribución
**Estado**: ⚠️ PENDIENTE
**Descripción**: No hay guía para que nuevos desarrolladores/agentes contribuyan.
**Solución**: Crear CONTRIBUTING.md con estándares de código, testing, commit messages.

---

## Mejoras Nice-to-Have

### [ISSUE-009] Sistema de plugins incompleto
**Estado**: ⚠️ PENDIENTE
**Descripción**: El sistema de plugins existe pero faltan plugins populares.
**Solución**: Crear plugins para: JMeter, Postman, Swagger, GraphQL.

### [ISSUE-010] Dashboard necesita mejoras UI
**Estado**: ⚠️ PENDIENTE
**Descripción**: El dashboard web existe pero la UI podría mejorar.
**Solución**: Agregar temas, más métricas, integración con Grafana.

---

## Historial de Cambios

| Fecha | Commit | Descripción | Puntuación |
|-------|--------|-------------|-------------|
| 20 Feb | 2be5f80 | Init básico | 2/10 |
| 21 Feb | cce96e9 | Init básico | 3/10 |
| 22 Feb | ca2efd4 | Init básico | 3/10 |
| 23 Feb | 110792f | InitManager completo | 7/10 |
| 24 Feb | 6379443 | Lazy loading (ROTO) | 5/10 |
| 25 Feb | (revert) | Framework restaurado | 7/10 |

---

## Próximos Pasos Recomendados

1. **Inmediato**: Actualizar README.md principal del proyecto
2. **Corto plazo**: Agregar tests para demos
3. **Mediano plazo**: Templates para frameworks comunes
4. **Largo plazo**: Sistema de plugins completo

---

## Notas para Agentes IA

Cuando trabajes con este framework:

1. **Siempre verifica** que el servicio esté corriendo antes de crear tests:
   ```bash
   curl http://localhost:8085/actuator/health
   ```

2. **Lee los controladores** del servicio (Java, Python, etc.) para conocer los endpoints reales

3. **Usa los patrones** definidos en services/ de proyectos existentes

4. **No asumas** URLs - siempre configura base_url en e2e.conf

5. **Ejecuta lint** después de crear tests: `e2e lint`

---

*Documento generado el 25 de febrero de 2026*
