import os
from pathlib import Path

BASE_DIR = Path(r"d:\.dev\proyectos\socialseed-e2e\.issues\vision_v2")
os.makedirs(BASE_DIR, exist_ok=True)

epics = [
    {
        "id": "EPIC-018",
        "title": "Autonomous Source Code Auto-Fixing (Self-Healing Code)",
        "description": "Si la IA detecta que un endpoint es el causante de un error 500 persistente o de fugas de memoria, no solo creará el test que falla, sino que generará automáticamente un Pull Request al repositorio del servicio (ej. `socialuser`) proponiendo la corrección del código fuente real.",
        "tasks": [
            "Conectar el Agente de IA al repositorio maestro de SocialSeed para tener visibilidad de AST (Abstract Syntax Tree) del código fuente.",
            "Construir un generador de parches bidireccionales que una el trace del error HTTP con la línea de código exacta del microservicio.",
            "Desarrollar integración nativa con GitHub/GitLab/Bitbucket APIs para abrir PRs/Merge Requests incluyendo el test E2E y el fix del código simultáneamente."
        ],
        "test_criteria": "Provocar un crash tipo `IndexError` en `auth`. El Interceptor y el Agente generarán el test E2E 01_auth_crash_flow.py, y acto seguido, el framework mostrará en el CLI/Dashboard un parche de código generado proponiendo la validación de la lista para arreglar el `auth`. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-019",
        "title": "Global Swarm Intelligence Distributed Testing",
        "description": "Dejar de depender de un solo Traffic Bot local. El framework desplegará dinámicamente lambdas o contenedores serverless en múltiples regiones globales (AWS, GCP) para simular tráfico desde Japón, Brasil o Europa contra tus microservicios.",
        "tasks": [
            "Crear adaptador Serverless (AWS Lambda / Google Cloud Run) para empaquetar el Traffic Bot de la EPIC-001.",
            "Establecer orquestador Swarm local que envíe comandos a los bots globales indicando a qué endpoint atacar y con qué cadencia.",
            "Recopilar métricas de latencia geográfica (Geo-Latency) y trazarlas en un Mapa Mundial animado dentro del Dashboard Vue.js."
        ],
        "test_criteria": "Al ejecutar `e2e swarm auth`, el framework despliega simuladores en la nube y la vista 'World Map' del Dashboard muestra de qué continente provienen los requests hacia el microservicio `auth` y la diferencia de ms. Probado simulando IPs globales contra el contenedor D:\\.dev\\proyectos\\SocialSeed."
    },
    {
        "id": "EPIC-020",
        "title": "Zero-Day Vulnerability Predictive Fuzzing (RAG-Security Agent)",
        "description": "Llevar la seguridad un paso más allá del fuzzing tradicional. Alimentaremos al Agente IA con la base de datos más reciente de MITRE CVEs usando RAG. La IA 'intuirá' y mutará payloads para buscar BOLA (Broken Object Level Authorization), Inyecciones ciegas e IDORs lógicos.",
        "tasks": [
            "Conectar Vector Store del Project Manifest (ya existente en e2e) con un feed diario de vulnerabilidades OWASP y CVEs.",
            "Dotar al Agente con capacidad de crear iteraciones de payloads (JWT manipulation, Parameter Pollution) sin que ningún humano lo guíe.",
            "Crear un nuevo tipo de 'Vela visual' en el TradingView chart (EPIC-006): 'Security Breach', resaltando en púrpura oscilación sospechosa."
        ],
        "test_criteria": "Pedirle al Agente: 'Encuentra agujeros en socialuser'. El Agente intentará listar perfiles inyectando IDs ajenos (IDOR) o manipulando su propio token y reportará las brechas en Markdown. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-021",
        "title": "API Evolution & Auto-Contract Versioning",
        "description": "Si la API de SocialSeed cambia y comienza a responder con un campo `is_premium` que no estaba en el manifest ni en OpenAPI, el framework lo detecta pasivamente mediante el tráfico y propone un Versioning V2 del API Contract de forma fluida.",
        "tasks": [
            "Implementar Diff Engine Semántico entre el JSON actual capturado y el DTO previamente parseado (EPIC-001).",
            "Auto-actualizar el `project_knowledge.json` sin comando manual, en cuanto el tráfico cambie sustancialmente la forma de los datos.",
            "Generar alertas de 'Breaking Change' o 'Undocumented Feature' en el Dashboard de Alertas de IA (EPIC-013)."
        ],
        "test_criteria": "Modificar el código de `auth` manualmente para retornar un nuevo campo ficticio. Al siguiente request del bot, el dashboard notificará 'New API Field Detected' y actualizará los DTOs autogenerados del testing. Probado en D:\\.dev\\proyectos\\SocialSeed."
    },
    {
        "id": "EPIC-022",
        "title": "Predictive Kubernetes Auto-Scaling Recommender",
        "description": "Si el análisis de métricas (EPIC-015) detecta que los microservicios están saturándose, la IA no se limitará a alertar, redactará automáticamente un archivo Kubernetes HPA (Horizontal Pod Autoscaler) u optimizará el `docker-compose.yml` para proponer más recursos.",
        "tasks": [
            "Crear algoritmo traductor de Carga/Latencia a Unidades M/Cores de Docker.",
            "Generar automáticamente YAMLs de infraestructura (K8s Manifests o Docker Compose Overrides) con recomendaciones de límites.",
            "Botón de '1-Click Apply' en Vue.js que ejecute el re-despliegue de los contenedores para absorber la presión."
        ],
        "test_criteria": "Tras inyectar carga pesada al punto de saturación sobre `socialuser`, el sistema generará un parche (ej: `docker-compose.override.yml`) aumentando Limits y Replicas, validando que el performance vuelve a la normalidad en TradingView. Probado en D:\\.dev\\proyectos\\SocialSeed."
    },
    {
        "id": "EPIC-023",
        "title": "Voice/NLP Command Interface for Dashboard Operations",
        "description": "Un nivel más allá del Chat UI. Permitir interacciones basadas puramente en la voz (Speech-to-Text integrado vía browser) para operar la suite de DevSecOps con manos libres, dictando los comandos a tu asistente IA.",
        "tasks": [
            "Integrar Web Speech API o Whisper AI modelo ligero en el Frontend de Vue.",
            "Mapear lenguaje natural auditivo al analizador de comandos E2E. (Ej: 'Framework, corre la suite de Auth a velocidad por dos').",
            "Añadir lector TTS (Text-To-Speech) para que el Agente IA 'recite' las alertas críticas de seguridad si detecta un fallo letal."
        ],
        "test_criteria": "A través del micrófono del PC conectado al localhost del Dashboard, el usuario ordena vocalmente: 'Inicia el interceptor'. El frontend transforma la onda a texto, el backend lo procesa y el contenedor inicia el sniffing en la red SocialSeed. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-024",
        "title": "Semantic User Journey Mapping (AI UI Test Drafts)",
        "description": "El framework de E2E es para backend API, pero la IA descifrará la pantalla front-end basada puramente en el flujo de tráfico HTTP, y te entregará el código Playwright para testear la UI en un futuro.",
        "tasks": [
            "Crear motor RAG invertido que asocie patrones de llamadas API a vistas front-end clásicas (Auth llamadas => Pantalla Login).",
            "Generar archivos `browser_test_draft.py` estructurados con el código de Playwright UI (usando selectores provisionales semánticos).",
            "Visor de Secuencia de Pantallas en el Dashboard (Diagrama de Estados) dibujando cómo se ve el viaje de usuario lógicamente."
        ],
        "test_criteria": "Sin abrir ningún navegador, puramente escuchando tráfico de `auth`, el motor creará un `ui_login_draft.py` asumiendo que el usuario llenó `email` y `password` en unos inputs. Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    },
    {
        "id": "EPIC-025",
        "title": "The Omniscient Project Manifest (Master Graph Brain)",
        "description": "Una entidad central que envuelve las 24 epics previas. Es un Super-Grafo Vectorial que conoce: Qué línea de código generó qué DTO, qué request 500 originó qué Alerta, qué test fue Auto-Healed y qué vulnerabilidad Mitre fue detectada. Un RAG Definitivo.",
        "tasks": [
            "Unificar todos los subsistemas en un motor central de base de datos de grafos (Neo4j o memoria relacional in-memory Vector Graph).",
            "Integrar capa GraphQL universal para que el Frontend y la IA consulten la totalidad del ecosistema unificado.",
            "Soportar consultas IA super-avanzadas: '¿En qué despliegue la Latencia p95 de la función X de Auth subió por un Chaos Test?'."
        ],
        "test_criteria": "Usar comandos CLI o GraphQL para consultar conexiones profundas sobre la red `SocialSeed` cruzando 5 dominios distintos en un solo query (Latencia, Código, Caos, Seguridad, Replay). Probado en D:\\.dev\\proyectos\\SocialSeed\\testing."
    }
]

for epic in epics:
    file_path = BASE_DIR / f"{epic['id']}_{epic['title'].replace(' ', '_').replace('/','_').lower()}.md"
    
    content = f"""# {epic['id']}: {epic['title']}

## Objetivo de la Visión Extremada
{epic['description']}

## Tareas Correspondientes
"""
    for i, task in enumerate(epic['tasks'], 1):
        content += f"- [ ] **Task {epic['id']}-T{i:02d}**: {task}\n"
        
    content += f"""
## Escenario de Pruebas Absoluto (Test Criteria)
> 🚨 **REQUISITO ABSOLUTO DE TESTING EN ENTORNO REAL**: Este proyecto Sci-Fi debe anclarse en la realidad. La validación se ejecutará 100% integrándose contra los contenedores vivos de `auth` y `socialuser` instalando el repositorio local en `D:\.dev\proyectos\SocialSeed\testing`. Nada de mocks al aire.
> 
> **Criterio de Aceptación Universal**: {epic['test_criteria']}

## Progreso y Bitácora de Agentes IA (Singularity Nivel)
- **Estado**: Por Implementar
- **Agentes Participantes**: [Ingresa aportes arquitectónicos de IA superior u operarios humanos aquí]
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
print(f"Generadas {len(epics)} Epics de Visión Sci-Fi en {BASE_DIR}")
