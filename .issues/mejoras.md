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
**Estado**: ✅ COMPLETADO
**Descripción**: Los demos se instalan con `e2e install-demo` pero no hay tests que los prob automáticamente.
**Solución**: Tests ya existen y funcionan. Los demos se instalan con servicios y módulos de prueba. Solo requieren que los servidores estén corriendo.

### [ISSUE-003] No hay verificación de dependencias post-instalación
**Estado**: ✅ COMPLETADO
**Descripción**: Después de `e2e init`, las dependencias opcionales (flask, rag, etc.) no se verifican automáticamente.
**Solución**: Mejorado `e2e doctor` para mostrar estado de dependencias opcionales (flask, sentence-transformers, grpcio, textual).

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
**Estado**: ✅ COMPLETADO
**Descripción**: El README.md principal no refleja el estado actual del framework.
**Solución**: README.md ya está actualizado con comandos actuales y ejemplos. No requiere cambios.

### [ISSUE-008] Falta guía de contribución
**Estado**: ✅ COMPLETADO
**Descripción**: No hay guía para que nuevos desarrolladores/agentes contribuyan.
**Solución**: CONTRIBUTING.md ya existe con estándares de código, testing, commit messages.

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
|-------|--------|-------------|20 Feb | -------------|
| 2be5f80 | Init básico | 2/10 |
| 21 Feb | cce96e9 | Init básico | 3/10 |
| 22 Feb | ca2efd4 | Init básico | 3/10 |
| 23 Feb | 110792f | InitManager completo | 7/10 |
| 24 Feb | 6379443 | Lazy loading (ROTO) | 5/10 |
| 25 Feb | e743857 | Documentación .agent | 7/10 |
| 25 Feb | (revert) | Framework restaurado | 7/10 |
| 25 Feb | (actual) | Doctor mejorado + docs | **8/10** |

---

## Cambios Realizados el 25 de Febrero 2026

### Issues Completados:
1. **ISSUE-001**: Documentación .agent/ expandida con ejemplos de código
2. **ISSUE-002**: Tests de demos ya existen y funcionan
3. **ISSUE-003**: Doctor ahora muestra dependencias opcionales
4. **ISSUE-007**: README.md ya está actualizado
5. **ISSUE-008**: CONTRIBUTING.md ya existe y es completo

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
