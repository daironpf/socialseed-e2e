# Deep Context Awareness for AI Agents (Issue #126)

El sistema de **Deep Context Awareness** proporciona comprensión profunda del contexto del proyecto más allá del manifiesto básico.

## Características

- ✅ **Codebase Semantic Understanding** - Comprensión semántica del código
- ✅ **Business Logic Inference** - Inferencia de lógica de negocio
- ✅ **User Behavior Pattern Learning** - Aprendizaje de patrones de usuario
- ✅ **API Relationship Mapping** - Mapeo de relaciones entre APIs
- ✅ **Domain Model Understanding** - Comprensión del modelo de dominio

## Arquitectura

```
socialseed_e2e/project_manifest/
├── deep_context.py              # Motor integrador principal
├── semantic_analyzer.py         # Análisis semántico de código
├── behavior_learner.py          # Aprendizaje de comportamiento
├── relationship_mapper.py       # Mapeo de relaciones API
├── domain_understanding.py      # Comprensión de dominio
└── business_logic_inference.py  # Inferencia de negocio (existente)
```

## Uso Básico

### Análisis Completo de Contexto

```python
from socialseed_e2e.project_manifest import DeepContextAwarenessEngine
from socialseed_e2e.project_manifest import ManifestAPI

# Cargar manifiesto existente
api = ManifestAPI("/path/to/project")
manifest = api._load_manifest()

# Crear motor de contexto profundo
engine = DeepContextAwarenessEngine(
    project_root="/path/to/project",
    manifest=manifest
)

# Ejecutar análisis completo
context = engine.analyze(include_behavior=True)

# Obtener contexto para generación de tests
gen_context = engine.get_context_for_generation()
```

### Análisis Semántico del Código

```python
from socialseed_e2e.project_manifest import SemanticCodebaseAnalyzer

analyzer = SemanticCodebaseAnalyzer("/path/to/project")
semantic_context = analyzer.analyze()

# Ver conceptos de dominio detectados
for concept in semantic_context.domain_concepts:
    print(f"Concepto: {concept.name} ({concept.concept_type})")
    print(f"  Atributos: {concept.attributes}")

# Ver reglas de negocio
for rule in semantic_context.business_rules:
    print(f"Regla: {rule.description}")

# Ver patrones detectados
for pattern in semantic_context.patterns:
    print(f"Patrón: {pattern.pattern_type.value}")
```

### Aprendizaje de Comportamiento del Usuario

```python
from socialseed_e2e.project_manifest import UserBehaviorLearner

learner = UserBehaviorLearner()

# Registrar acciones del usuario
learner.record_action("test_generation", {"test_type": "integration"})

# Registrar correcciones
learner.record_correction(
    original="assert x == 1",
    corrected="assert x == 1.0",
    context_type="assertion"
)

# Obtener preferencias aprendidas
preferences = learner.get_learned_preferences()
print(f"Tipos de test preferidos: {preferences['preferred_test_types']}")

# Sugerir correcciones
suggestions = learner.suggest_corrections("assert status == 200")
```

### Mapeo de Relaciones API

```python
from socialseed_e2e.project_manifest import APIRelationshipMapper

mapper = APIRelationshipMapper(manifest.services)
relationships = mapper.map_relationships()

# Ver dependencias
for dep in relationships["dependencies"]:
    print(f"{dep.source_endpoint} → {dep.target_endpoint}")
    print(f"  Tipo: {dep.category.value}, Fuerza: {dep.strength.value}")

# Analizar impacto de cambios
impact = mapper.analyze_impact("users.create_user")
print(f"Nivel de riesgo: {impact.risk_level}")
print(f"Endpoints afectados: {impact.directly_affected}")

# Obtener grafo de dependencias
graph = mapper.get_dependency_graph()
```

### Comprensión del Modelo de Dominio

```python
from socialseed_e2e.project_manifest import DomainModelUnderstanding

understanding = DomainModelUnderstanding("/path/to/project")
domain_model = understanding.analyze()

# Ver elementos de dominio
for element in domain_model.elements:
    print(f"{element.name} ({element.element_type.value})")
    print(f"  Atributos: {[a.name for a in element.attributes]}")

# Ver contextos delimitados
for context in domain_model.bounded_contexts:
    print(f"Contexto: {context.name}")
    print(f"  Elementos: {context.elements}")

# Obtener raíces de agregado
aggregate_roots = understanding.get_aggregate_roots()
```

## Componentes Detallados

### SemanticCodebaseAnalyzer

Detecta:
- **Conceptos de dominio**: Entidades, value objects, servicios
- **Reglas de negocio**: Validaciones, constraints, assertions
- **Patrones de código**: Repository, Service, State Machine, etc.
- **Terminología del dominio**: Glosario de términos

```python
# Obtener resumen del dominio
summary = analyzer.get_domain_summary()
print(f"Conceptos totales: {summary['total_concepts']}")
print(f"Reglas de negocio: {summary['total_business_rules']}")
print(f"Patrones: {summary['detected_patterns']}")

# Encontrar conceptos relacionados
related = analyzer.find_related_concepts("User")
```

### UserBehaviorLearner

Aprende:
- **Preferencias de test**: Tipos de tests favoritos
- **Patrones de corrección**: Correcciones frecuentes
- **Áreas de enfoque**: Qué partes del sistema usa más
- **Convenciones de nomenclatura**: Estilos preferidos

```python
# Obtener hints para generación
hints = learner.get_test_generation_hints()
print(f"Convención de nombres: {hints['naming_convention']}")
print(f"Áreas de enfoque: {hints['focus_areas']}")

# Analizar tendencias
trends = learner.analyze_behavior_trends(days=30)
print(f"Acciones recientes: {trends['total_actions']}")
```

### APIRelationshipMapper

Mapea:
- **Dependencias directas**: Llamadas entre endpoints
- **Dependencias de datos**: Compartición de DTOs
- **Dependencias secuenciales**: Flujos de trabajo
- **Clusters de API**: Grupos relacionados

```python
# Ver clusters
for cluster in relationships["clusters"]:
    print(f"Cluster: {cluster.name}")
    print(f"  Endpoints: {cluster.endpoints}")
    print(f"  Operaciones: {cluster.operations}")

# Flujos de datos
for flow in relationships["data_flows"]:
    print(f"Flujo: {flow.source} → {flow.target}")
    print(f"  Campos: {flow.fields}")
```

### DomainModelUnderstanding

Entiende:
- **Elementos de dominio**: Entities, Value Objects, Services
- **Jerarquías**: Herencia y composición
- **Contextos delimitados**: Bounded contexts
- **Repositorios**: Capa de acceso a datos

```python
# Obtener jerarquía de entidades
hierarchy = understanding.get_entity_hierarchy()

# Encontrar repositorios
repos = understanding.get_repositories_for_entity("User")

# Resumen del dominio
summary = understanding.get_domain_summary()
```

## DeepContextAwarenessEngine

El motor integrador combina todos los analizadores:

```python
# Análisis completo
engine = DeepContextAwarenessEngine(project_root, manifest)
context = engine.analyze()

# Contexto para generación de tests
gen_context = engine.get_context_for_generation()
# Incluye:
# - Comprensión semántica
# - Flujos de negocio
# - Dependencias API
# - Elementos de dominio
# - Hints de comportamiento

# Recomendaciones basadas en contexto
recommendations = engine.get_recommendations()
for rec in recommendations:
    print(f"[{rec['category']}] {rec['message']}")

# Exportar reporte completo
engine.export_context_report(Path("context_report.json"))
```

## Flujo de Trabajo Completo

```python
from socialseed_e2e.project_manifest import (
    ManifestGenerator,
    DeepContextAwarenessEngine,
)

# 1. Generar manifiesto base
generator = ManifestGenerator("/path/to/project")
manifest = generator.generate()

# 2. Analizar contexto profundo
engine = DeepContextAwarenessEngine("/path/to/project", manifest)
context = engine.analyze()

# 3. Obtener contexto para generación
gen_context = engine.get_context_for_generation()

# 4. Aplicar comportamiento aprendido
hints = engine.behavior_learner.get_test_generation_hints()

# 5. Generar tests con contexto completo
# ... usar gen_context y hints para generación inteligente
```

## Almacenamiento y Persistencia

### Comportamiento del Usuario

```python
# Guardar datos aprendidos
engine.behavior_learner.save()

# Los datos se guardan en:
# - .e2e/behavior_learning/actions.jsonl
# - .e2e/behavior_learning/patterns.json
# - .e2e/behavior_learning/correction_patterns.json
```

## Métricas y Reportes

### Reporte de Contexto

```python
# Exportar reporte completo
engine.export_context_report(Path("context_report.json"))

# El reporte incluye:
# - Resumen del análisis
# - Contexto para generación
# - Recomendaciones
```

### Métricas de Comprensión

```python
# Métricas semánticas
semantic_summary = analyzer.get_domain_summary()

# Métricas de dominio
domain_summary = understanding.get_domain_summary()

# Métricas de comportamiento
behavior_summary = learner.analyze_behavior_trends()
```

## Integración con Generación de Tests

El contexto profundo mejora la generación de tests:

```python
# 1. Analizar contexto
context = engine.analyze()

# 2. Obtener contexto optimizado
gen_context = engine.get_context_for_generation()

# 3. Usar en generación
from socialseed_e2e.project_manifest import FlowBasedTestSuiteGenerator

for service in manifest.services:
    generator = FlowBasedTestSuiteGenerator(
        service_info=service,
        deep_context=gen_context  # Incluir contexto profundo
    )
    suite = generator.generate_test_suite()
```

## Casos de Uso

### 1. Comprensión de Legacy Code

```python
# Analizar código existente para entenderlo
analyzer = SemanticCodebaseAnalyzer("/legacy/project")
context = analyzer.analyze()

# Identificar conceptos clave
for concept in context.domain_concepts[:10]:
    print(f"{concept.name}: {concept.description}")

# Detectar patrones arquitectónicos
for pattern in context.patterns:
    print(f"Patrón {pattern.pattern_type.value}: {pattern.description}")
```

### 2. Análisis de Impacto

```python
# Evaluar impacto de cambios antes de hacerlos
mapper = APIRelationshipMapper(services)
mapper.map_relationships()

impact = mapper.analyze_impact("api_v1.users.create")
if impact.risk_level in ["high", "critical"]:
    print("⚠️ Cambio de alto riesgo - revisar:")
    for rec in impact.recommendations:
        print(f"  - {rec}")
```

### 3. Aprendizaje Continuo

```python
# El sistema aprende de cada interacción
learner = UserBehaviorLearner()

# Registrar cada corrección
learner.record_correction(original, corrected, context_type)

# Con el tiempo, las sugerencias mejoran
suggestions = learner.suggest_corrections(new_code)
```

## Referencia API

### SemanticCodebaseAnalyzer

- `analyze()` - Ejecuta análisis semántico completo
- `get_domain_summary()` - Obtiene resumen del dominio
- `find_related_concepts(name)` - Encuentra conceptos relacionados

### UserBehaviorLearner

- `record_action(type, context)` - Registra acción
- `record_correction(orig, corr, type)` - Registra corrección
- `get_learned_preferences()` - Obtiene preferencias
- `suggest_corrections(text)` - Sugiere correcciones
- `get_test_generation_hints()` - Hints para generación

### APIRelationshipMapper

- `map_relationships()` - Mapea todas las relaciones
- `analyze_impact(endpoint)` - Analiza impacto de cambios
- `get_dependency_graph()` - Obtiene grafo de dependencias
- `find_alternative_paths(src, tgt)` - Encuentra caminos alternativos

### DomainModelUnderstanding

- `analyze()` - Analiza modelo de dominio
- `get_aggregate_roots()` - Obtiene raíces de agregado
- `get_repositories_for_entity(name)` - Busca repositorios
- `get_domain_summary()` - Resumen del dominio

### DeepContextAwarenessEngine

- `analyze(include_behavior)` - Análisis completo
- `get_context_for_generation()` - Contexto para generación
- `get_recommendations()` - Recomendaciones basadas en contexto
- `export_context_report(path)` - Exporta reporte
- `save()` - Guarda datos aprendidos
