# Issues de Documentación y Funcionalidad Encontrados

## Fecha: 2026-02-19
## Entorno: Instalación limpia en /tmp/agent-test
## Estado: ✅ TODOS LOS ISSUES RESUELTOS (2026-02-20)

---

## Issues Críticos

### Issue #001: Falta archivo SERVICE_DETECTION.md
- **Ubicación:** `.agent/`
- **Problema:** Los archivos AGENT_GUIDE.md y WORKFLOW_GENERATION.md referencian `SERVICE_DETECTION.md` pero no existe
- **Solución:** Crear el archivo SERVICE_DETECTION.md con instrucciones de detección de puertos
- **Estado:** ✅ RESUELTO (el archivo ya existe)

### Issue #002: install-demo no actualiza e2e.conf
- **Ubicación:** CLI install_demo
- **Problema:** Después de `e2e install-demo`, el e2e.conf no tiene los servicios configurados
- **Error:** `e2e run` falla con "'NoneType' object has no attribute 'items'"
- **Solución:** La función install_demo debe actualizar e2e.conf con los servicios instalados
- **Estado:** ✅ RESUELTO (install_demo ahora actualiza e2e.conf con servicios demo)

### Issue #003: Falta GRPC_AGENT_GUIDE.md.template referenciado
- **Ubicación:** `.agent/WORKFLOW_GENERATION.md`
- **Problema:** Línea 56 menciona "GRPC_AGENT_GUIDE.md.template" pero no existe
- **Solución:** Crear guía para agentes sobre cómo testing servicios gRPC
- **Estado:** ✅ RESUELTO (actualizado WORKFLOW_GENERATION.md para referenciar GRPC_TESTING.md existente)

---

## Issues de Documentación

### Issue #004: e2e init crea e2e.conf con services: null
- **Ubicación:** CLI init
- **Problema:** El e2e.conf inicial tiene `services: null` en lugar de `services: {}`
- **Error:** Comandos como `e2e set url` fallan con TypeError
- **Solución:** Inicializar services como diccionario vacío
- **Estado:** ✅ RESUELTO (init ahora crea servicios como diccionario con comentarios)

### Issue #005: No hay guía de Quick Start para agentes
- **Ubicación:** `.agent/`
- **Problema:** Un agente nuevo no tiene un punto de entrada claro
- **Solución:** Crear QUICK_START.md con flujo básico para agentes
- **Estado:** ✅ RESUELTO (QUICKSTART.md ya existe)

### Issue #006: No hay ejemplos de config.yaml por servicio
- **Ubicación:** Templates
- **Problema:** No hay ejemplo de cómo crear config.py por servicio
- **Solución:** Agregar ejemplo en los templates
- **Estado:** ✅ RESUELTO (existen config.py.template y demo_config.py.template)

---

## Issues de Mejora

### Issue #007: El README.md generado no tiene información de demos
- **Ubicación:** Template README.md
- **Problema:** El README.md creado por `e2e init` no menciona los demos disponibles
- **Solución:** Actualizar template para incluir sección de demos
- **Estado:** ✅ RESUELTO (actualizado example_README.md.template con sección de Demo APIs)

### Issue #008: No hay documentación de variables de entorno
- **Ubicación:** `.agent/`
- **Problema:** No hay guía sobre qué variables de entorno usa el framework
- **Solución:** Crear ENV_VARIABLES.md
- **Estado:** ✅ RESUELTO (creado .agent/ENV_VARIABLES.md)

### Issue #009: Falta troubleshooting común
- **Ubicación:** `.agent/`
- **Problema:** No hay guía de problemas comunes y soluciones
- **Solución:** Crear TROUBLESHOOTING.md
- **Estado:** ✅ RESUELTO (TROUBLESHOOTING.md ya existe)

---

## Resumen de Testing

| Funcionalidad | Estado |
|--------------|--------|
| e2e init | ✅ Funciona |
| e2e install-demo | ✅ Funciona (actualiza e2e.conf) |
| e2e run | ✅ Funciona |
| .agent/AGENT_GUIDE.md | ✅ Existe |
| .agent/EXAMPLE_TEST.md | ✅ Existe |
| .agent/FRAMEWORK_CONTEXT.md | ✅ Existe |
| .agent/WORKFLOW_GENERATION.md | ✅ Existe (actualizado para referenciar GRPC_TESTING.md) |
| .agent/SERVICE_DETECTION.md | ✅ Existe |
| .agent/GRPC_TESTING.md | ✅ Existe |
| .agent/QUICKSTART.md | ✅ Existe |
| .agent/TROUBLESHOOTING.md | ✅ Existe |
| .agent/ENV_VARIABLES.md | ✅ CREADO |
