# Scripts de Automatización del Playground

Este directorio contiene scripts de automatización para facilitar el uso y la extensión del playground de SocialSeed E2E.

## 📜 Scripts Disponibles

### 🔧 Gestión de Servicios

#### `start-all.sh`
Inicia todas las aplicaciones del playground.

```bash
./scripts/start-all.sh [opciones]

Opciones:
  -d, --daemon      Ejecutar en background
  -l, --logs        Mostrar logs en tiempo real (con -d)
  -s, --sequential  Iniciar secuencialmente
  -h, --help        Mostrar ayuda

Ejemplos:
  ./scripts/start-all.sh -d           # Iniciar en background
  ./scripts/start-all.sh -d -l        # Iniciar y ver logs
  ./scripts/start-all.sh -s           # Iniciar en foreground
```

#### `stop-all.sh`
Detiene todas las aplicaciones del playground.

```bash
./scripts/stop-all.sh [opciones]

Opciones:
  -f, --force    Forzar detención (kill -9)
  -h, --help     Mostrar ayuda

Ejemplos:
  ./scripts/stop-all.sh          # Detener normalmente
  ./scripts/stop-all.sh -f       # Forzar detención
```

#### `health-check.sh`
Verifica el estado de todas las aplicaciones.

```bash
./scripts/health-check.sh [opciones]

Opciones:
  -v, --verbose    Mostrar información detallada
  -j, --json       Output en formato JSON
  -h, --help       Mostrar ayuda

Ejemplos:
  ./scripts/health-check.sh          # Verificar estado
  ./scripts/health-check.sh -j       # Output JSON
  ./scripts/health-check.sh -v       # Modo verbose
```

### 🧪 Generación de Tests

#### `generate-tests.py`
Genera tests automáticamente basándose en el archivo BUGS.md de una aplicación.

```bash
python scripts/generate-tests.py <app-name> [opciones]

Opciones:
  -o, --output       Directorio de salida (default: ./generated-tests)
  -b, --bug          Números de bugs específicos (ej: 1,2,3)
  --only-critical    Solo bugs críticos
  --page-object      Solo generar Page Object
  --dry-run          No escribir archivos, solo mostrar
  -h, --help         Mostrar ayuda

Ejemplos:
  # Generar todos los tests para auth-service
  python scripts/generate-tests.py auth-service-broken

  # Generar solo bugs específicos
  python scripts/generate-tests.py payment-service-broken --bug 8,9,10

  # Solo bugs críticos
  python scripts/generate-tests.py ecommerce-broken --only-critical

  # Ver qué se generaría sin escribir archivos
  python scripts/generate-tests.py auth-service-broken --dry-run

  # Solo Page Object
  python scripts/generate-tests.py payment-service-broken --page-object
```

## 🚀 Flujos de Trabajo Comunes

### 1. Iniciar y Verificar

```bash
# Iniciar todas las apps en background
./scripts/start-all.sh -d

# Verificar que están funcionando
./scripts/health-check.sh

# Output esperado:
# ✅ Auth Service        http://localhost:5001
# ✅ Payment Service     http://localhost:5002
# ✅ E-commerce Service  http://localhost:5003
```

### 2. Generar Tests Automáticamente

```bash
# Generar tests para auth-service
python scripts/generate-tests.py auth-service-broken --output ./my-tests

# Revisar los tests generados
ls -la ./my-tests/

# Implementar la lógica específica de cada test
# (editar los archivos generados)
```

### 3. Detener Todo

```bash
# Detener todas las apps
./scripts/stop-all.sh

# O forzar si no responden
./scripts/stop-all.sh -f
```

## 🛠️ Para Desarrolladores

### Crear un Nuevo Script

1. Crea el archivo en `scripts/`
2. Hazlo ejecutable: `chmod +x scripts/mi-script.sh`
3. Agrega encabezado con documentación
4. Usa colores para mejor UX (ver ejemplos existentes)

### Ejemplo de Plantilla

```bash
#!/bin/bash
#
# mi-script.sh - Descripción del script
#
# Uso: ./mi-script.sh [opciones]
#

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función de ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help    Mostrar ayuda"
}

# Lógica principal
echo -e "${GREEN}✅ Script ejecutado!${NC}"
```

## 🤖 Para Agentes de IA

### Análisis Automatizado

```python
# Usar generate-tests.py para análisis
import subprocess

# Generar tests y analizar estructura
result = subprocess.run(
    ['python', 'scripts/generate-tests.py', 'auth-service-broken', '--dry-run'],
    capture_output=True,
    text=True
)

# El output incluye información sobre bugs y endpoints
print(result.stdout)
```

### Health Check Programático

```python
import subprocess
import json

# Obtener estado en JSON
result = subprocess.run(
    ['./scripts/health-check.sh', '-j'],
    capture_output=True,
    text=True
)

status = json.loads(result.stdout)
for service, info in status['services'].items():
    print(f"{service}: {info['status']}")
```

## 📊 Integración CI/CD

### GitHub Actions

```yaml
name: Playground Health Check

on:
  schedule:
    - cron: '0 */6 * * *'  # Cada 6 horas

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: ./playground/scripts/start-all.sh -d
      
      - name: Wait for services
        run: sleep 10
      
      - name: Health check
        run: ./playground/scripts/health-check.sh
      
      - name: Stop services
        run: ./playground/scripts/stop-all.sh
```

### Makefile

```makefile
.PHONY: playground-start playground-stop playground-health

playground-start:
	./playground/scripts/start-all.sh -d

playground-stop:
	./playground/scripts/stop-all.sh

playground-health:
	./playground/scripts/health-check.sh

playground-test:
	./playground/scripts/start-all.sh -d
	./playground/scripts/health-check.sh
	./playground/scripts/stop-all.sh
```

## 🔧 Troubleshooting

### "Permission denied"

```bash
# Hacer scripts ejecutables
chmod +x scripts/*.sh scripts/*.py
```

### "Command not found"

```bash
# Ejecutar desde directorio playground
cd playground
./scripts/start-all.sh

# O usar ruta completa
./playground/scripts/start-all.sh
```

### Puerto ya en uso

```bash
# Ver qué proceso usa el puerto
lsof -i :5001

# Matar proceso
kill -9 <PID>

# O usar stop-all
./scripts/stop-all.sh -f
```

## 📈 Métricas y Monitoreo

### Contador de Bugs

```bash
# Contar bugs por app
for app in auth-service-broken payment-service-broken ecommerce-broken; do
  count=$(grep -c "^### BUG" playground/broken-apps/$app/BUGS.md)
  echo "$app: $count bugs"
done
```

### Reporte de Estado

```bash
#!/bin/bash
# Generar reporte de estado

echo "# Playground Status Report" > report.md
echo "Generated: $(date)" >> report.md
echo "" >> report.md

./scripts/health-check.sh -j | jq -r '.services | to_entries[] | "- \(.key): \(.value.status)"' >> report.md
```

## 📝 Notas

- Todos los scripts están diseñados para ser **idempotentes** (ejecutar múltiples veces es seguro)
- Usan **colores** para mejorar la experiencia de usuario
- Incluyen **manejo de errores** apropiado
- Soportan **modo verbose** para debugging
- Son **portables** (bash + python estándar)

## 🆘 Soporte

- GitHub Issues: [socialseed-e2e/issues](https://github.com/daironpf/socialseed-e2e/issues)
- Documentación: [Guía de Desarrolladores](../DEVELOPER_GUIDE.md)
- Guía IA: [Guía para Agentes](../AI_AGENT_GUIDE.md)
