import os
from pathlib import Path

BASE_DIR = Path(r"d:\.dev\proyectos\socialseed-e2e\.issues\vision_v2")
os.makedirs(BASE_DIR, exist_ok=True)

epics = [
    {
        "id": "EPIC-008",
        "title": "Data Anonymization & Security Filter",
        "description": "Módulo de seguridad crítica que inspecciona el tráfico capturado por el interceptor y ofusca/anonimiza información sensible (PII, contraseñas, emails) antes de guardarlo en los logs o enviarlo al Agente de IA.",
        "tasks": [
            "Crear motor de expresiones regulares y detección semántica para PII (Personally Identifiable Information).",
            "Integrarse como middleware en el Network Interceptor (EPIC-002) para mutar en tiempo real los valores de los JSON Response/Request.",
            "Desarrollar comandos CLI para configurar qué llaves (keys) o campos deben ser censurados (ej: `password`, `ssn`, `credit_card`)."
        ],
        "test_criteria": "Al interceptar llamadas de login hacia el servicio `auth` del proyecto SocialSeed (D:\\.dev\\proyectos\\SocialSeed\\testing), el password debe aparecer como '[REDACTED]' en los logs y el Dashboard. El servicio en sí debe funcionar sin alteración."
    },
    {
        "id": "EPIC-009",
        "title": "Real-Time Flakiness Detection & Self-Healing",
        "description": "Sistema autónomo que detecta Inestabilidad (Flakiness). Si un test auto-generado falla esporádicamente debido a latencia o dependencias, este módulo inyecta lógicas de espera (waits/retries) de forma inteligente.",
        "tasks": [
            "Crear motor estadístico que marque un test como 'Flaky' si en múltiples ejecuciones bajo el mismo contexto varía su resultado.",
            "Implementar lógica de 'Self-Healing': Modificar el código fuente del test en vivo para aumentar timeouts o agregar polling si falla por latencia.",
            "Reportar el ratio de sanación y la matriz de flakiness en una sección especializada del Dashboard Vue."
        ],
        "test_criteria": "Induciendo latencia artificial en el servicio `socialuser` de SocialSeed, el generador creará un test que podría fallar. El motor debe detectar la flakiness y auto-arreglar el test inyectando waits necesarios. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-010",
        "title": "Microservices Dependency Graph Map",
        "description": "Visor Topológico en el Dashboard que renderiza un mapa interactivo de nodos mostrando cómo los microservicios se comunican entre sí basándose unicamente en el tráfico interceptado.",
        "tasks": [
            "Desarrollar analizador de trazas que conecte Request ID y Correlated ID para entender el flujo multi-servicio (Ej. SocialUser -> Auth).",
            "Agregar librería gráfica topológica (como D3.js o Vis.js) al frontend Vue + Tailwind.",
            "Mostrar el estado de salud de cada conexión/nodo (Verde: OK, Amarillo: Lento, Rojo: Errores 5xx) en tiempo real."
        ],
        "test_criteria": "Cuando el Traffic Generator Bot hable con `socialuser` y este internamente valide tokens con `auth`, el mapa debe pintar dos nodos (socialuser y auth) y una flecha verde conectándolos. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-011",
        "title": "Chaos Engineering Traffic Correlation",
        "description": "Correlacionar directamente los resultados del Network Interceptor (EPIC-002) con el módulo nativo de Ingeniería de Caos ya existente en el proyecto, para saber exactamente qué originó un error.",
        "tasks": [
            "Vincular el inicio de inyección de caos (ej: CPU Chaos Limit) con un 'Event Marker' en la base de datos temporal del Interceptor.",
            "Pintar 'Banderas de Caos' en la Gráfica estilo TradingView (EPIC-006) en la escala de tiempo en que ocurrió el experimento.",
            "Que la IA del Chat (EPIC-007) tenga contexto para responder: 'El error fue inducido a propósito por la prueba de caos X'."
        ],
        "test_criteria": "Correr el comando `e2e chaos` sobre `socialuser` al mismo tiempo que se recibe tráfico. La gráfica debe mostrar el evento de caos y los subsecuentes errores en la misma línea temporal. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-012",
        "title": "Staging/Prod Remote Cluster Synchronization",
        "description": "Adaptar todo el ecosistema para que el Agente Interceptor y el Traffic Bot no sólo funcionen de forma estrictamente local, sino que envíen telemetría de forma centralizada al Dashboard si corren en Kubernetes remoto, AWS O Azure.",
        "tasks": [
            "Refactorizar el almacenamiento de captura hacia persistencia remota (Postgres o servicio cloud central).",
            "Asegurar conexiones API encriptadas (gRPC o WebSockets) entre múltiples interceptores remotos y el único Dashboard local/central.",
            "Añadir dropdown en el Dashboard para elegir clúster 'SocialSeed-Prod', 'SocialSeed-Staging', o 'Local'."
        ],
        "test_criteria": "Desplegando el interceptor en un contenedor separado configurado remoto, los datos deben fluir perfectamente al Dashboard centralizado asumiendo la conexión exitosa. Probado usando redes docker separadas de D:\\.dev\\proyectos\\SocialSeed."
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
