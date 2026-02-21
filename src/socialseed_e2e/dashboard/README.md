# SocialSeed E2E Dashboard

Interfaz web moderna para ejecución y depuración de tests E2E. Este dashboard sirve como el "Centro de Control" del framework, construido con Vue.js 3 y FastAPI.

## 🚀 Características

### ✅ Implementadas

- **Dashboard**: Vista general con estadísticas y acciones rápidas
- **Test Explorer**: Vista en árbol de todos los módulos de tests
- **Run Tests**: Ejecutar tests individuales o todos con progreso en tiempo real
- **Live Logs**: Streaming de logs via WebSocket
- **History**: Ver historial de ejecuciones anteriores
- **Settings**: Configuración de preferencias del dashboard

## 📦 Instalación

El dashboard se instala con el comando `e2e install-extras`:

```bash
# Instalar dependencias del dashboard
e2e install-extras dashboard

# O instalar todos los extras
e2e install-extras --all

# Ver todos los extras disponibles
e2e install-extras --list
```

Para desarrollo (con Node.js):

```bash
cd src/socialseed_e2e/dashboard/vue
npm install
```

## 🎯 Uso

### Lanzar el Dashboard

```bash
# Producción (servir archivos Vue construidos)
e2e dashboard

# Puerto personalizado
e2e dashboard --port 8080

# No abrir navegador automáticamente
e2e dashboard --no-browser

# Desarrollo (requiere Node.js)
e2e dashboard --dev
```

### Opciones del Comando

| Opción | Descripción | Default |
|--------|-------------|---------|
| `-p, --port` | Puerto del servidor | 5173 |
| `-h, --host` | Host del servidor | localhost |
| `--no-browser` | No abrir navegador | false |
| `--dev` | Modo desarrollo (Node.js) | false |

## 📱 Interfaz de Usuario

### 1. Dashboard (Inicio)

Vista general con:
- **Estadísticas**: Total tests, pasados, fallados, duración
- **Recent Runs**: Últimas ejecuciones con estado
- **Services Overview**: Tests por servicio
- **Quick Actions**: Acciones rápidas (Run All, Explore, History, Settings)

### 2. Test Explorer

- Vista en árbol de servicios y tests
- Filtrado por nombre
- Selección de tests individuales
- Ver detalles de cada test

### 3. Run Tests

- Seleccionar tests a ejecutar
- Ver progreso en tiempo real
- Streaming de logs via WebSocket
- Resultados detallados al finalizar

### 4. History

- Tabla de ejecuciones anteriores
- Filtros por status y servicio
- Ver detalles de cada ejecución
- Re-ejecutar tests desde historial
- Eliminar entradas

### 5. Settings

- **General**: Auto-refresh, max history
- **Test Execution**: Parallel execution, retries, timeout
- **Notifications**: Notificaciones desktop, sonidos
- **API Configuration**: Base URL, API key
- **Dashboard**: Dark mode, theme color
- **Data Management**: Export/Import, Clear history

## 🏗️ Arquitectura

```
dashboard/
├── vue/                      # Frontend Vue.js 3
│   ├── src/
│   │   ├── App.vue          # Layout principal
│   │   ├── main.js          # Bootstrap Vue
│   │   ├── router/          # Vue Router
│   │   ├── stores/          # Pinia stores
│   │   │   ├── testStore.js # Estado de tests
│   │   │   └── logStore.js  # Estado de logs
│   │   └── views/           # Vistas
│   │       ├── Dashboard.vue
│   │       ├── TestExplorer.vue
│   │       ├── RunTests.vue
│   │       ├── History.vue
│   │       └── Settings.vue
│   ├── package.json
│   └── vite.config.js
├── vue_api.py                # Backend FastAPI
└── README.md
```

## 🔌 API Backend

El dashboard expone una API REST y WebSocket:

### Endpoints REST

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/tests` | Obtener todos los tests |
| POST | `/api/tests/run` | Ejecutar un test |
| GET | `/api/history` | Obtener historial |
| GET | `/api/config` | Obtener configuración |
| POST | `/api/config` | Guardar configuración |

### WebSocket Events

| Evento | Descripción |
|--------|-------------|
| `connect` | Cliente conectado |
| `test_progress` | Progreso de test |
| `test_log` | Log en tiempo real |
| `test_complete` | Test completado |
| `all_tests_complete` | Todos los tests completados |

## 💾 Base de Datos

SQLite en `.e2e/dashboard.db`:

```sql
-- Tabla de ejecuciones
CREATE TABLE test_runs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    test_name TEXT,
    test_path TEXT,
    service_name TEXT,
    status TEXT,
    duration_ms INTEGER,
    output TEXT,
    error_message TEXT
);

-- Tabla de suites
CREATE TABLE test_suites (
    id INTEGER PRIMARY KEY,
    name TEXT,
    tests TEXT,
    created_at TEXT
);
```

## 🔧 Troubleshooting

### Dependencias faltantes

```bash
e2e install-extras dashboard
```

### Puerto ocupado

```bash
e2e dashboard --port 8080
```

### No se encuentran tests

1. Verificar proyecto inicializado: `e2e init`
2. Verificar tests en `services/<name>/modules/`
3. Verificar función `run(page)` en cada test

### Error WebSocket

El dashboard requiere WebSocket para live logs. Verificar:
1. Navegador soporta WebSocket
2. No hay proxy bloqueando conexiones

### Build Vue (Producción)

```bash
cd src/socialseed_e2e/dashboard/vue
npm install
npm run build

# Luego ejecutar
e2e dashboard
```

## 🎨 Desarrollo

### Modo Desarrollo

```bash
# Instalar Node.js primero
# https://nodejs.org/

# Terminal 1: Backend
python -m socialseed_e2e dashboard --no-browser

# Terminal 2: Frontend
cd src/socialseed_e2e/dashboard/vue
npm run dev
```

### Estructura Vue

- **Vue 3** con Composition API
- **Vite** como bundler
- **Pinia** para estado
- **Vue Router** para navegación
- **Socket.IO client** para WebSocket

## 🚀 Roadmap

- [ ] Test Suite Management
- [ ] Comparación de resultados
- [ ] Exportación (CSV/JSON/HTML)
- [ ] Autenticación
- [ ] Editor de tests integrado

---

**Versión:** 2.0.0 (Vue.js)  
**Última actualización:** 2026-02-21
