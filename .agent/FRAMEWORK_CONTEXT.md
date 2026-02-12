# Contexto del Framework socialseed-e2e para Agentes de IA

Este documento te proporciona el contexto necesario para trabajar con el framework `socialseed-e2e`. Tu objetivo es ayudar al desarrollador a crear pruebas end-to-end (E2E) para APIs REST de manera autónoma.

## 1. Arquitectura del Framework

El framework sigue una arquitectura hexagonal simplificada para desacoplar la lógica de prueba de la lógica del servicio.

### Estructura de Directorios Clave

```
.
├── e2e.conf                 # Configuración principal (URLs, timeouts)
├── services/               # Directorio de definición de servicios
│   └── <service-name>/     # Cada API/Microservicio tiene su carpeta
│       ├── __init__.py
│       ├── config.py       # Configuración específica del servicio
│       ├── data_schema.py  # DTOs (Pydantic), Endpoints y Constantes
│       ├── <name>_page.py  # Page Object Model (hereda de BasePage)
│       └── modules/        # Tests individuales
│           ├── 01_register_flow.py
│           ├── 02_login_flow.py
│           └── ...
└── tests/                  # Tests generales o de integración del propio framework
```

## 2. Conceptos Principales

### Service Page (Page Object)
Cada servicio tiene una clase "Page" (ej. `UsersApiPage`) que hereda de `BasePage`.
- **Responsabilidad**: Abstraer las llamadas HTTP.
- **Ubicación**: `services/<service-name>/<name>_page.py`.
- **Métodos**: Deben corresponder a acciones de negocio (ej. `register_user`, `get_profile`) y retornar `APIResponse` de Playwright.

### Test Modules
Los tests se dividen en archivos pequeños y numerados dentro de `services/<service-name>/modules/`.
- **Naming**: `XX_description_flow.py` (ej. `01_register_flow.py`).
- **Estructura**: Cada módulo debe tener una función `run(context)` o `run(page)`.
- **Orden**: Se ejecutan secuencialmente según su numeración.
- **Estado**: El estado se comparte a través de la instancia de la `Page`. Si el test 01 guarda un token en `page.auth_token`, el test 02 puede usarlo.

### Data Schema
- **Ubicación**: `services/<service-name>/data_schema.py`.
- **Contenido**: Modelos Pydantic para request/response bodies y costantes de rutas.

## 3. Tu Rol como Agente

Cuando el usuario te pida "generar tests", debes:
1. **Analizar** el código fuente del controlador REST que te provea el usuario.
2. **Identificar** los endpoints, métodos HTTP, y estructuras de datos.
3. **Mapear** estos endpoints a métodos en la `ServicePage`.
4. **Generar** módulos de prueba secuenciales que cubran flujos lógicos (crear -> obtener -> actualizar -> borrar).

---
Lee `WORKFLOW_GENERATION.md` para instrucciones paso a paso sobre cómo generar código.
