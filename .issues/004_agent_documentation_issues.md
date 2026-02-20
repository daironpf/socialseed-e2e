# Issues de Documentación y Funcionalidad Encontrados

## Fecha: 2026-02-19
## Entorno: Instalación limpia en /tmp/agent-test

---

## Issues Críticos

### Issue #001: Falta archivo SERVICE_DETECTION.md
- **Ubicación:** `.agent/`
- **Problema:** Los archivos AGENT_GUIDE.md y WORKFLOW_GENERATION.md referencian `SERVICE_DETECTION.md` pero no existe
- **Solución:** Crear el archivo SERVICE_DETECTION.md con instrucciones de detección de puertos

### Issue #002: install-demo no actualiza e2e.conf
- **Ubicación:** CLI install_demo
- **Problema:** Después de `e2e install-demo`, el e2e.conf no tiene los servicios configurados
- **Error:** `e2e run` falla con "'NoneType' object has no attribute 'items'"
- **Solución:** La función install_demo debe actualizar e2e.conf con los servicios instalados

### Issue #003: Falta GRPC_AGENT_GUIDE.md.template referenciado
- **Ubicación:** `.agent/WORKFLOW_GENERATION.md`
- **Problema:** Línea 56 menciona "GRPC_AGENT_GUIDE.md.template" pero no existe
- **Solución:** Crear guía para agentes sobre cómo testing servicios gRPC

---

## Issues de Documentación

### Issue #004: e2e init crea e2e.conf con services: null
- **Ubicación:** CLI init
- **Problema:** El e2e.conf inicial tiene `services: null` en lugar de `services: {}`
- **Error:** Comandos como `e2e set url` fallan con TypeError
- **Solución:** Inicializar services como diccionario vacío

### Issue #005: No hay guía de Quick Start para agentes
- **Ubicación:** `.agent/`
- **Problema:** Un agente nuevo no tiene un punto de entrada claro
- **Solución:** Crear QUICK_START.md con flujo básico para agentes

### Issue #006: No hay ejemplos de config.yaml por servicio
- **Ubicación:** Templates
- **Problema:** No hay ejemplo de cómo crear config.py por servicio
- **Solución:** Agregar ejemplo en los templates

---

## Issues de Mejora

### Issue #007: El README.md generado no tiene información de demos
- **Ubicación:** Template README.md
- **Problema:** El README.md creado por `e2e init` no menciona los demos disponibles
- **Solución:** Actualizar template para incluir sección de demos

### Issue #008: No hay documentación de variables de entorno
- **Ubicación:** `.agent/`
- **Problema:** No hay guía sobre qué variables de entorno usa el framework
- **Solución:** Crear ENV_VARIABLES.md

### Issue #009: Falta troubleshooting común
- **Ubicación:** `.agent/`
- **Problema:** No hay guía de problemas comunes y soluciones
- **Solución:** Crear TROUBLESHOOTING.md

---

## Resumen de Testing

| Funcionalidad | Estado |
|--------------|--------|
| e2e init | ✅ Funciona |
| e2e install-demo | ✅ Funciona (pero no actualiza e2e.conf) |
| e2e run | ✅ Funciona (con e2e.conf corregido) |
| .agent/AGENT_GUIDE.md | ✅ Existe |
| .agent/EXAMPLE_TEST.md | ✅ Existe |
| .agent/FRAMEWORK_CONTEXT.md | ✅ Existe |
| .agent/WORKFLOW_GENERATION.md | ✅ Existe |
| .agent/SERVICE_DETECTION.md | ❌ FALTA |
| .agent/GRPC_AGENT_GUIDE.md | ❌ FALTA |
