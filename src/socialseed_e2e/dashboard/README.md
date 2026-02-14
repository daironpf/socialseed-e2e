# SocialSeed E2E Dashboard

Interfaz web local para ejecución y depuración manual de tests. Este dashboard sirve como el "Centro de Control" del framework, permitiendo a los usuarios explorar, ejecutar y depurar tests sin escribir código constantemente.

## 🚀 Características

### ✅ Implementadas

- **Test Explorer**: Vista en árbol de todos los módulos de tests
- **One-Click Run**: Ejecutar tests individuales, suites o carpetas con un clic
- **Rich Request/Response Viewer**: Inspeccionar headers, bodies (JSON/HTML) y códigos de estado
- **Parameterization**: Inputs de UI para sobrescribir variables de tests en runtime
- **Live Logs**: Streaming en tiempo real de logs de ejecución
- **Run History**: Ver ejecuciones anteriores y sus resultados

## 📦 Instalación

El dashboard requiere Streamlit:

```bash
pip install streamlit
```

O instalar con el extra dashboard:

```bash
pip install socialseed-e2e[dashboard]
```

## 🎯 Uso

### Lanzar el Dashboard

```bash
# Lanzar en el puerto por defecto (8501)
e2e dashboard

# Lanzar en puerto personalizado
e2e dashboard --port 8080

# No abrir navegador automáticamente
e2e dashboard --no-browser

# Especificar host
e2e dashboard --host 0.0.0.0
```

### Interfaz de Usuario

#### 1. Test Explorer (Sidebar)
- Visualización en árbol de todos los servicios y tests
- Contador de tests por servicio
- Selección de servicios específicos
- Navegación rápida entre tests

#### 2. Panel de Ejecución
- Visualización del test seleccionado
- Configuración de parámetros:
  - Base URL
  - Timeout
  - Retries
  - Variables personalizadas (JSON)
- Botón de ejecución con spinner de carga
- Limpieza de resultados

#### 3. Visualización de Resultados
- Estado de ejecución (✅ Pasado / ❌ Fallado)
- Duración en milisegundos
- Timestamp
- Request/Response detallado:
  - Método HTTP
  - URL
  - Headers
  - Body (formateado JSON)
- Output y errores

#### 4. Live Logs
- Streaming en tiempo real
- Filtro por nivel (All, Info, Success, Error)
- Últimos 50 logs visibles
- Limpieza de logs

#### 5. Historial de Ejecuciones
- Base de datos SQLite local (`.e2e/dashboard.db`)
- Últimas 20 ejecuciones
- Tabla con timestamp, nombre, estado y duración
- Persistente entre sesiones

## 🏗️ Estructura del Módulo

```
dashboard/
├── __init__.py         # Exporta DashboardServer
├── app.py              # Aplicación Streamlit principal
├── server.py           # Lógica del servidor y CLI
└── components/         # Componentes UI (para extensión futura)
```

## 🎨 Personalización

### CSS Personalizado

El dashboard incluye estilos CSS personalizados para:
- Headers principales
- Indicadores de estado (passed/failed/skipped)
- Badges de estado
- Logs en monospaced
- Visualizador JSON

### Configuración de Streamlit

La aplicación se configura con:
- Título: "SocialSeed E2E Dashboard"
- Icono: 🌱
- Layout: wide
- Sidebar: expandido por defecto

## 💾 Base de Datos

El dashboard utiliza SQLite para persistir:

### Tabla: test_runs
```sql
CREATE TABLE test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    test_name TEXT,
    test_path TEXT,
    status TEXT,
    duration_ms INTEGER,
    output TEXT,
    error_message TEXT
);
```

### Tabla: test_suites
```sql
CREATE TABLE test_suites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    tests TEXT,
    created_at TEXT
);
```

Ubicación: `.e2e/dashboard.db` en el directorio del proyecto.

## 🔧 Integración con el Framework

### Descubrimiento de Tests

El dashboard automáticamente descubre tests en:
```
<project_root>/services/<service_name>/modules/*.py
```

### Ejecución de Tests

Los tests se ejecutan a través de una implementación simplificada que:
1. Carga el test module
2. Ejecuta la función `run(page)`
3. Captura request/response
4. Almacena resultados

### Session State

Streamlit session state mantiene:
- `test_history`: Historial de tests ejecutados
- `live_logs`: Logs en tiempo real
- `selected_test`: Test actualmente seleccionado
- `test_results`: Resultados de ejecuciones

## 📝 Ejemplos de Uso

### Escenario 1: Ejecutar un Test Específico

1. Abrir dashboard: `e2e dashboard`
2. Seleccionar servicio del sidebar
3. Click en el test deseado
4. Ajustar parámetros si es necesario
5. Click en "▶️ Run Test"
6. Ver resultados y request/response

### Escenario 2: Ejecutar Todos los Tests

1. Click en "🚀 Run All Tests" en el sidebar
2. Ver progress bar de ejecución
3. Revisar Live Logs en tiempo real
4. Ver resumen al finalizar

### Escenario 3: Depuración con Variables Personalizadas

1. Seleccionar test
2. Expandir "🔧 Custom Variables"
3. Modificar JSON con valores deseados:
   ```json
   {"user_email": "debug@example.com", "timeout": 10000}
   ```
4. Ejecutar test
5. Ver resultado con variables aplicadas

### Escenario 4: Revisar Historial

1. Panel derecho muestra historial
2. Tabla con últimas 20 ejecuciones
3. Filtrar por status si es necesario
4. Identificar tests flaky

## 🐛 Troubleshooting

### "Streamlit not found"

```bash
pip install streamlit
```

### Puerto ocupado

```bash
# Usar puerto diferente
e2e dashboard --port 8080
```

### No se encuentran tests

Asegúrate de:
1. Estar en un proyecto inicializado (`e2e init`)
2. Tener tests en `services/<name>/modules/`
3. Los tests tengan función `run(page)`

### Error de base de datos

Limpiar caché:
```bash
rm -rf .e2e/dashboard.db
```

## 🔮 Roadmap Futuro

### Características Planificadas

- [ ] **Test Suite Management**: Crear y guardar suites de tests
- [ ] **Comparación de Resultados**: Comparar ejecuciones lado a lado
- [ ] **Exportación**: Exportar resultados a CSV/JSON/HTML
- [ ] **Filtros Avanzados**: Filtrar tests por tags, status, etc.
- [ ] **Autenticación**: Login para acceso protegido
- [ ] **Dark Mode**: Tema oscuro
- [ ] **Keyboard Shortcuts**: Atajos de teclado
- [ ] **Test Editor**: Editar tests desde el dashboard

### Mejoras de UI

- [ ] Drag & drop para reordenar tests
- [ ] Gráficos de tendencias
- [ ] Heatmap de ejecuciones
- [ ] Collapsible sections mejorado

## 🤝 Contribuir

Para extender el dashboard:

1. Crear nuevo componente en `components/`
2. Importar en `app.py`
3. Agregar al layout principal
4. Documentar en este README

## 📚 Recursos

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Component Gallery](https://streamlit.io/components)
- [Customization Guide](https://docs.streamlit.io/library/advanced-features/configuration)

---

**Versión:** 1.0.0  
**Última actualización:** 2026-02-14  
**Mantenido por:** SocialSeed E2E Team
