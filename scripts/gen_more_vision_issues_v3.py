import os
from pathlib import Path

BASE_DIR = Path(r"d:\.dev\proyectos\socialseed-e2e\.issues\vision_v2")
os.makedirs(BASE_DIR, exist_ok=True)

epics = [
    {
        "id": "EPIC-013",
        "title": "Real-time AI Alerting & Notification Engine",
        "description": "Motor de notificaciones que escucha la gráfica de TradingView/métricas y dispara alertas hiper-enriquecidas (a Slack, Discord, Webhooks) que incluyen contexto de la IA sobre qué falló y por qué.",
        "tasks": [
            "Crear motor de reglas para umbrales de alerta (ej: '5% de errores 5xx en 1 minuto').",
            "Integrar Agente IA para que analice el pico antes de enviar la alerta (resumen RCA - Root Cause Analysis).",
            "Desarrollar integraciones nativas para Slack, Microsoft Teams, Discord y Webhooks genéricos."
        ],
        "test_criteria": "Al inyectar 10 requests fallidos(500) en el servicio `auth` de SocialSeed, el sistema debe disparar inmediatamente un webhook con un resumen escrito por la IA diagnosticando la causa."
    },
    {
        "id": "EPIC-014",
        "title": "Database State Snapshot & Sandbox for Replays",
        "description": "Al usar la 'Máquina del Tiempo' (EPIC-004), ejecutar un request de ayer en la BD de hoy puede no tener sentido. Este módulo tomará snapshots ligeros del estado de la DB o generará Mocks Inteligentes del estado en ese milisegundo exacto.",
        "tasks": [
            "Implementar interceptor a nivel de base de datos o capturador de respuestas de bases de datos para aislar y guardar el estado.",
            "Desarrollar entorno de 'Sandbox' para Database Replays (ej. iniciar un contenedor Postgres transitorio con los datos restaurados del snapshot).",
            "Sincronizar el ID del Time-Machine de red con el ID del Snapshot de DB."
        ],
        "test_criteria": "Replayar mediante `e2e time-machine replay` un proceso de registro hacia `auth` utilizando el estado aislado (sandbox) de la base de datos para garantizar que el replay pase con éxito independientemente del estado actual del sistema vivo. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-015",
        "title": "AI Performance Anomaly Detection",
        "description": "No basta con atrapar errores 500. Este modelo de ML detectará anomalías de rendimiento progresivo (ej. Latencia de 50ms sube silenciosamente a 80ms) creando 'Baselines' históricos del tráfico pasivo.",
        "tasks": [
            "Crear recolector de latencias promedio (percentiles p95, p99) por cada endpoint extraído por el Discovery Bot.",
            "Implementar detección de desviaciones estándar para advertir de degradación silenciosa sin intervención humana.",
            "Mostrar Alertas de Degradación en la vista de Dashboard (Nodos amarillos en EPIC-010 y etiquetas en EPIC-006)."
        ],
        "test_criteria": "Al bombardear gradualmente con peticiones pesadas el servicio `socialuser`, el sistema detectará el aumento de p95 de latencia de 20ms a 70ms y levantará un baseline anomaly alert en el Dashboard. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-016",
        "title": "Traffic Replay Speed & Playback Controls",
        "description": "Si la máquina del tiempo almacena 5 minutos de tráfico conflictivo, el usuario QA debe poder dar 'Play', 'Pausa', 'x2' o 'x0.5' velocidad a la repetición del tráfico sobre un entorno de pruebas.",
        "tasks": [
            "Crear motor de inyección de tráfico basado en timestamps relativos del archivo de captura (.har o json).",
            "Incorporar botones multimedia (Play, Pause, Rw, Fw, Speed) en el Vue.js Dashboard interactuando con el backend.",
            "Permitir ejecución de asserts E2E (EPIC-003) en tiempo real mientras el tráfico es replayado visualmente."
        ],
        "test_criteria": "Cargar un trace de 10 requests separados por 1 segundo cada uno. Al darle Play en x2.0, los 10 requests se ejecutan contra el entorno SocialSeed en exactamente 5 segundos. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-017",
        "title": "Community Plugin & Extension Architecture",
        "description": "Para que este ecosistema se expanda sin límites, construimos una arquitectura orientada a Plugins, donde cualquier desarrollador pueda agregar protocolos de análisis (GraphQL, WebSockets) o nuevos Agentes IA.",
        "tasks": [
            "Desarrollar sistema Core de Hook-Points (Lifecycle hooks) en el sniffer, generator y dashboard.",
            "Crear el comando `e2e plugin install <name>` para descargar extensiones del ecosistema.",
            "Publicar API Docs de la interfaz de Interceptación para facilitar a la comunidad la creación de interceptores personalizados."
        ],
        "test_criteria": "Desarrollar localmente un Dummy Plugin que agregue un sufijo a los logs de red. Instalarlo mediante CLI y probar que el interceptor loguea tráfico hacia `auth` o `socialuser` con el sufijo inyectado. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    }
]

for epic in epics:
    file_path = BASE_DIR / f"{epic['id']}_{epic['title'].replace(' ', '_').replace('/','_').lower()}.md"
    
    content = f"""# {epic['id']}: {epic['title']}

## Objetivo de la Visión
{epic['description']}

## Tareas Correspondientes
"""
    for i, task in enumerate(epic['tasks'], 1):
        content += f"- [ ] **Task {epic['id']}-T{i:02d}**: {task}\n"
        
    content += f"""
## Escenario de Pruebas (Test Criteria)
> 🚨 **REQUISITO ABSOLUTO DE TESTING**: No se considerará terminada la tarea si no fue aprobada y verificada contra el servidor `D:\.dev\proyectos\SocialSeed` instalando el framework en `D:\.dev\proyectos\SocialSeed\testing`.
> 
> **Criterio de Aceptación**: {epic['test_criteria']}

## Progreso y Bitácora de Agentes IA
- **Estado**: Pendiente
- **Agentes Participantes**: [Lista de agentes IA que tocaron el issue o dejaron feedback de intentos aquí]
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
print(f"Generadas {len(epics)} Epics adicionales en {BASE_DIR}")
