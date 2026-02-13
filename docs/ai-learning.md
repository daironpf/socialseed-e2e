# AI Learning and Feedback Loop (Issue #125)

El sistema de **AI Learning and Feedback Loop** permite a los agentes de IA aprender de los resultados de ejecución de tests para mejorar la generación y ejecución futura.

## Características

- ✅ **Recolección automática de feedback** - Captura resultados de tests exitosos y fallidos
- ✅ **Aprendizaje de correcciones de usuarios** - Aprende de las correcciones manuales
- ✅ **Mejora de precisión** - Mejora la generación de tests basándose en patrones aprendidos
- ✅ **Optimización de orden de ejecución** - Ordena tests para feedback más rápido
- ✅ **Adaptación a cambios** - Se adapta automáticamente a cambios en el codebase

## Arquitectura

```
socialseed_e2e/ai_learning/
├── feedback_collector.py    # Recolección y almacenamiento de feedback
├── model_trainer.py         # Entrenamiento de modelos con feedback
├── adaptation_engine.py     # Motor de adaptación dinámica
└── __init__.py             # API pública
```

## Uso Básico

### 1. Feedback Automático

El feedback se recolecta automáticamente cuando ejecutas tests:

```bash
# Cada ejecución de test guarda feedback automáticamente
e2e run
```

### 2. Ver Feedback Recolectado

```bash
# Ver feedback reciente
e2e ai-learning feedback

# Analizar patrones
e2e ai-learning feedback --analyze

# Ver más items
e2e ai-learning feedback -l 50
```

### 3. Entrenar Modelo

```bash
# Entrenar con correcciones recolectadas
e2e ai-learning train

# Guardar modelo entrenado
e2e ai-learning train -o my_model.json
```

### 4. Obtener Sugerencias de Adaptación

```bash
# Sugerencias generales
e2e ai-learning adapt

# Sugerencias para un test específico
e2e ai-learning adapt --test-name test_login

# Estrategia agresiva de adaptación
e2e ai-learning adapt --strategy aggressive
```

### 5. Optimizar Orden de Tests

```bash
# Optimizar tests basándose en historial de ejecución
e2e ai-learning optimize users-api
```

## Uso Programático

### Recolectar Feedback Manualmente

```python
from socialseed_e2e import FeedbackCollector

# Crear collector
collector = FeedbackCollector(storage_path="./my_feedback")

# Recolectar resultado de test
collector.collect_test_result(
    test_name="test_login",
    success=True,
    execution_time=1.5,
    endpoint="/api/auth/login"
)

# Recolectar corrección de usuario
collector.collect_user_correction(
    test_name="test_login",
    original_assertion="assert response.status == 200",
    corrected_assertion="assert response.status_code == 200",
    user_comment="El atributo correcto es status_code"
)
```

### Entrenar Modelo

```python
from socialseed_e2e import ModelTrainer, TrainingData

trainer = ModelTrainer()

# Preparar datos de entrenamiento
training_data = TrainingData(
    inputs=["assert x == 1", "assert y == 2"],
    outputs=["assert x == 1.0", "assert y == 2.0"],
    contexts=["Type mismatch", "Type mismatch"]
)

# Entrenar
metrics = trainer.train_from_corrections(training_data)

print(f"Accuracy: {metrics.accuracy:.1%}")
print(f"Samples: {metrics.training_samples}")

# Predecir corrección
prediction = trainer.predict_correction("assert status == 200")
print(f"Sugerencia: {prediction}")
```

### Motor de Adaptación

```python
from socialseed_e2e import AdaptationEngine, AdaptationStrategy

# Crear engine con estrategia
engine = AdaptationEngine(strategy=AdaptationStrategy.BALANCED)

# Adaptar template de test basándose en patrones aprendidos
test_template = "assert status == 200"
learned_patterns = {
    "assert status": ["assert status_code"]
}
confidence_scores = {"assert status": 0.9}

adapted = engine.adapt_test_generation(
    test_template,
    learned_patterns,
    confidence_scores
)

print(f"Template adaptado: {adapted}")
```

## Estrategias de Adaptación

### Conservative (Conservadora)
- Umbral de confianza: 90%
- Cambios mínimos, alta seguridad
- Recomendada para proyectos en producción

### Balanced (Balanceada) - Default
- Umbral de confianza: 70%
- Cambios moderados basados en patrones
- Buena para la mayoría de los casos

### Aggressive (Agresiva)
- Umbral de confianza: 50%
- Adaptación rápida a cambios
- Ideal para desarrollo activo

## Almacenamiento de Feedback

El feedback se almacena en formato JSONL en `./ai_feedback/feedback.jsonl`:

```json
{
  "feedback_id": "test_login_1234567890",
  "feedback_type": "test_success",
  "test_name": "test_login",
  "timestamp": "2025-02-12T10:30:00",
  "execution_time": 1.5,
  "endpoint": "/api/auth/login"
}
```

## Integración con Test Runner

El sistema está integrado automáticamente con el test runner:

```python
from socialseed_e2e import run_all_tests, get_feedback_collector

# Ejecutar tests (recolecta feedback automáticamente)
results = run_all_tests()

# Acceder al collector para análisis
collector = get_feedback_collector()
patterns = collector.analyze_patterns()

print(f"Success rate: {patterns['success_rate']:.1%}")
```

## Flujo de Trabajo Completo

```bash
# 1. Ejecutar tests y recolectar feedback
e2e run

# 2. Ver feedback recolectado
e2e ai-learning feedback --analyze

# 3. El usuario corrige tests manualmente
# (edita los tests según sea necesario)

# 4. Registrar correcciones (opcional, puede hacerse programáticamente)
# El sistema aprende de las correcciones automáticamente

# 5. Entrenar modelo
e2e ai-learning train

# 6. Obtener sugerencias para próxima generación
e2e ai-learning adapt

# 7. Generar nuevos tests con aprendizaje aplicado
e2e generate-tests --strategy valid
```

## Métricas de Aprendizaje

El sistema rastrea métricas clave:

- **Accuracy**: Precisión de las predicciones
- **Precision**: Precisión de las correcciones sugeridas
- **Recall**: Cobertura de correcciones posibles
- **F1 Score**: Balance entre precision y recall
- **Success Rate**: Tasa de éxito de tests
- **User Corrections**: Número de correcciones manuales

## Buenas Prácticas

1. **Recolectar feedback consistentemente**: Ejecuta tests regularmente para acumular datos
2. **Documentar correcciones**: Añade comentarios cuando corrijas tests manualmente
3. **Revisar métricas**: Monitorea las métricas de aprendizaje periódicamente
4. **Estrategia apropiada**: Usa Conservative en producción, Aggressive en desarrollo
5. **Exportar modelos**: Guarda modelos entrenados para compartir entre equipos

## Troubleshooting

### No se recolecta feedback

Verifica que el test runner esté configurado correctamente:

```python
from socialseed_e2e import get_feedback_collector

collector = get_feedback_collector()
print(f"Storage path: {collector.storage_path}")
```

### Modelo no mejora

- Asegúrate de tener suficientes correcciones (mínimo 10)
- Verifica la calidad de las correcciones
- Considera usar estrategia Aggressive

### Feedback duplicado

El sistema automáticamente maneja duplicados basándose en timestamps y test names.

## Referencia API

### FeedbackCollector

- `collect_test_result()` - Recolecta resultado de test
- `collect_user_correction()` - Recolecta corrección manual
- `get_recent_feedback()` - Obtiene feedback reciente
- `analyze_patterns()` - Analiza patrones en feedback
- `load_all_feedback()` - Carga todo el feedback

### ModelTrainer

- `train_from_corrections()` - Entrena con correcciones
- `predict_correction()` - Predice corrección
- `optimize_test_order()` - Optimiza orden de tests
- `suggest_test_improvements()` - Sugiere mejoras
- `export_model()` / `load_model()` - Persistencia

### AdaptationEngine

- `adapt_test_generation()` - Adapta generación de tests
- `detect_codebase_changes()` - Detecta cambios en código
- `prioritize_test_execution()` - Prioriza ejecución
- `suggest_test_updates()` - Sugiere actualizaciones
- `adapt_to_api_changes()` - Adapta a cambios de API
