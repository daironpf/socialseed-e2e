import os
from pathlib import Path

# Base path for issues
BASE_DIR = Path(r"d:\.dev\proyectos\socialseed-e2e\.issues\vision_v2")

# Create structure if not exists
os.makedirs(BASE_DIR, exist_ok=True)

# Define the epics and their linked tasks
epics = [
    {
        "id": "EPIC-001",
        "title": "Discovery & Traffic Generator Bot",
        "description": "Un bot que se conecte a la red de microservicios, descubra los endpoints y DTOs a partir del código fuente y comience a enviar tráfico constante y estructurado para simular uso real.",
        "tasks": [
            "Crear parser de código fuente para detección de Endpoints (FastAPI, SpringBoot).",
            "Crear extractor de DTOs basados en el código fuente (Python BaseModel, Java Records).",
            "Desarrollar el core del bot generador de tráfico utilizando los DTOs descubiertos.",
            "Implementar scheduler para envío recurrente y concurrencia ajustable de los requests.",
            "Integrarse con el servicio `auth` y `socialuser` del entorno SocialSeed real.",
            "Validar y manejar tokens generados al momento del tráfico simulado para mantener las sesiones activas.",
        ],
        "test_criteria": "El bot descubre correctamente los DTOs de Auth/SocialUser y genera 100 requests por minuto sin errores de formato. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-002",
        "title": "Network Interceptor Container (Traffic Sniffer)",
        "description": "Contenedor acoplado a la red de docker de SocialSeed que escanea, filtra y almacena el tráfico generado tanto por el Traffic Bot como por usuarios reales.",
        "tasks": [
            "Crear imagen Docker del Interceptor basada en eBPF o interceptación Proxy Inverso.",
            "Desarrollar middleware de filtrado pasivo (no interfiere latencia).",
            "Capturar Request Headers, Body, Response Headers, Response Body, y latencia en milisegundos.",
            "Indexar tráfico interceptado en motor de almacenamiento en tiempo real (Redis o SQLite en memoria para test).",
            "Aislar las llamadas exclusivas referentes a testing (evitar loops entre el interceptor y el sistema analizado).",
        ],
        "test_criteria": "El contenedor se despliega junto a la red docker y captura exitosamente todos los requests realizados por el Traffic Bot hacia Auth/SocialUser. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-003",
        "title": "Auto-Test Generator based on Traffic",
        "description": "Módulo que analiza el tráfico capturado por el Network Interceptor y genera dinámicamente tests End-to-End con Playwright basándose en flujos exitosos.",
        "tasks": [
            "Agrupar flujos de llamadas dependientes (Ej. Login -> GetProfile) en base al JWT o session ID.",
            "Mapear secuencias HTTP a llamadas nativas del framework `socialseed-e2e` (Commands generados).",
            "Generar scripts modulares (`01_auth_flow.py`) con assertions auto-generados que validen el estado HTTP y body keys.",
            "Integrador de Tests que coloque los scripts en la carpeta del servicio correspondiente (Ej. `services/socialuser/modules`).",
        ],
        "test_criteria": "Tras capturar tráfico de Login, el sistema auto-genera un test exitoso en la carpeta de testing del entorno real. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-004",
        "title": "Time-Machine Debugging Logging",
        "description": "Módulo para detección de errores (4xx, 5xx), almacenamiento comprensivo del contexto temporal, y recreación de la falla.",
        "tasks": [
            "Crear Listener en tiempo real capaz de accionar triggers al encontrar un status code de error.",
            "Serializar el payload fallido, variables de entorno y traza de tiempo asociadas.",
            "Desarrollar CLI command `e2e time-machine replay <id-error>` para re-lanzar exactamente el request anómalo.",
        ],
        "test_criteria": "El bot envía una llamada con datos corruptos al servicio `socialuser`, esto detona un Time-Machine Record que posteriormente puede ser re-ejecutado por un Test QA mediante el UI o CLI. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-005",
        "title": "Vue/Tailwind Real-Time Local Web Dashboard",
        "description": "Unificar todo el motor desarrollado en el Dashboard web (ya iniciado con Vue.js y Tailwind) para observar en tiempo real la situación del proyecto.",
        "tasks": [
            "Desarrollar el puente de conexión WebSockets desde el FastAPI Backend al Dashboard Vue.js.",
            "Establecer la estructura base del layout en Tailwind para Sidebar, Header y Main Data Panel.",
            "Crear tabla interactiva 'Live Traffic' para visualizar el log de la red, similar a Chrome Network Tab.",
            "Crear la sección 'Manual Tester' donde el usuario QA pueda presionar 'Correr Suites' e inspeccionar logs visuales.",
        ],
        "test_criteria": "El dashboard carga por el puerto web local. Al estar desplegado el Traffic Bot en la red SocialSeed, el tráfico debe fluir e imprimirse en tiempo real en la vista 'Live Traffic'. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-006",
        "title": "TradingView API Traffic Charts Analyzer",
        "description": "Implementación de gráficas avanzadas (estilo TradingView o ECharts) para mostrar el comportamiento de latencias, aciertos y fallos a lo largo del tiempo.",
        "tasks": [
            "Integrar librería de visualización de datos de tiempo cronológico (Ej. Apache ECharts o Chart.js).",
            "Mapear los latencias HTTP a la gráfica Y, y el tiempo cronológico a la gráfica X.",
            "Implementar 'Velas rojas' indicativas para la visibilidad de picos de inestabilidad (errores 500 consecutivos).",
            "Desarrollar herramienta de slider de zoom en el tiempo cronológico para analizar lapsos (H1, M15, M1) del comportamiento del tráfico."
        ],
        "test_criteria": "La vista 'Charts' despliega los gráficos temporales sobre los requests recibidos en `auth` y `socialuser`, detectando correctamente un pico en caso de estrés programado. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-007",
        "title": "AI Prompt Command Center & Autonomous Agent",
        "description": "Una terminal Chat-UI en el Dashboard con un agente de IA conectado al contenedor y a todo e2e, para ejecutar tareas, pedir análisis y auto-recreación de trazas de fallo.",
        "tasks": [
            "Desarrollar componente de Chat UI embebido en el Dashboard con envío de markdown e interpretador de comandos.",
            "Conectar motor LLM / Motor OpenAI del usuario (RAG incluido) con el Chat UI.",
            "Incorporar API local para que el agente reciba el Request: 'Analiza el pico de errores a las 10am' y el Agente devuelva los Time-Machine Logs interceptados.",
            "Permitir al usuario indicar al agente: 'Genera un test E2E de regresión para cubrir esa falla y fuzzealo'. El agente ejecuta los comandos de la serie `e2e` que resuelvan la solicitud.",
        ],
        "test_criteria": "El usuario QA interactúa en el chat AI pidiendo que observe un Time-Machine ID concreto, y el Agente contesta con un test autogenerado en la carpeta del servicio real y procede a validarlo satisfactoriamente. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
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
        
print(f"Generadas {len(epics)} Epics y {sum([len(e['tasks']) for e in epics])} Tasks en {BASE_DIR}")
