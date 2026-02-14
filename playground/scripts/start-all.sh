#!/bin/bash
#
# start-all.sh - Inicia todas las aplicaciones del playground
#
# Uso: ./start-all.sh [opciones]
# Opciones:
#   -d, --daemon    Ejecutar en background
#   -l, --logs      Mostrar logs en tiempo real
#   -h, --help      Mostrar ayuda
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYGROUND_DIR="$(dirname "$SCRIPT_DIR")"
APPS_DIR="$PLAYGROUND_DIR/broken-apps"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Puertos por app
AUTH_PORT=5001
PAYMENT_PORT=5002
ECOMMERCE_PORT=5003

# Función de ayuda
show_help() {
    echo -e "${BLUE}SocialSeed E2E Playground - Start All Apps${NC}"
    echo ""
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -d, --daemon     Ejecutar apps en background"
    echo "  -l, --logs       Mostrar logs en tiempo real (solo con -d)"
    echo "  -s, --sequential Iniciar secuencialmente (no paralelo)"
    echo "  -h, --help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                    # Iniciar en foreground"
    echo "  $0 -d                 # Iniciar en background"
    echo "  $0 -d -l              # Iniciar en background y mostrar logs"
    echo ""
    echo "Apps disponibles:"
    echo "  - Auth Service:       http://localhost:$AUTH_PORT"
    echo "  - Payment Service:    http://localhost:$PAYMENT_PORT"
    echo "  - E-commerce Service: http://localhost:$ECOMMERCE_PORT"
}

# Variables de configuración
DAEMON_MODE=false
SHOW_LOGS=false
SEQUENTIAL=false

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        -s|--sequential)
            SEQUENTIAL=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Opción desconocida: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Función para verificar si un puerto está en uso
check_port() {
    local port=$1
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Función para iniciar una app
start_app() {
    local name=$1
    local dir=$2
    local port=$3
    local log_file="/tmp/playground-${name}.log"
    
    echo -e "${BLUE}Iniciando $name en puerto $port...${NC}"
    
    # Verificar si ya está corriendo
    if check_port "$port"; then
        echo -e "${YELLOW}  ⚠️  $name ya está corriendo en puerto $port${NC}"
        return 0
    fi
    
    # Verificar dependencias
    if [ ! -f "$dir/requirements.txt" ]; then
        echo -e "${RED}  ❌ No se encontró requirements.txt en $dir${NC}"
        return 1
    fi
    
    # Instalar dependencias si es necesario
    if ! python -c "import flask" 2>/dev/null; then
        echo -e "${YELLOW}  📦 Instalando dependencias...${NC}"
        pip install -q -r "$dir/requirements.txt"
    fi
    
    # Iniciar la app
    if [ "$DAEMON_MODE" = true ]; then
        cd "$dir" && python app.py > "$log_file" 2>&1 &
        local pid=$!
        echo $pid > "/tmp/playground-${name}.pid"
        
        # Esperar a que inicie
        local retries=0
        while ! check_port "$port" && [ $retries -lt 10 ]; do
            sleep 1
            retries=$((retries + 1))
        done
        
        if check_port "$port"; then
            echo -e "${GREEN}  ✅ $name iniciado (PID: $pid)${NC}"
        else
            echo -e "${RED}  ❌ Error iniciando $name${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}  ✅ $name iniciando en foreground${NC}"
        echo -e "${YELLOW}  Presiona Ctrl+C para detener${NC}"
        echo ""
        cd "$dir" && python app.py
    fi
}

# Función para mostrar logs
show_logs() {
    echo ""
    echo -e "${BLUE}📋 Logs de las aplicaciones:${NC}"
    echo ""
    
    # Combinar logs de todos los archivos
    tail -f /tmp/playground-*.log 2>/dev/null &
    local tail_pid=$!
    
    # Esperar interrupción
    trap "kill $tail_pid 2>/dev/null; exit 0" INT
    wait
}

# Main
echo -e "${GREEN}🚀 SocialSeed E2E Playground${NC}"
echo -e "${BLUE}============================${NC}"
echo ""

if [ "$DAEMON_MODE" = false ] && [ "$SEQUENTIAL" = false ]; then
    # Modo interactivo - iniciar todas en paralelo con tmux o similar
    echo -e "${YELLOW}Nota: Para iniciar todas las apps en background, usa:$0 -d${NC}"
    echo ""
fi

# Iniciar apps
if [ "$SEQUENTIAL" = true ]; then
    # Modo secuencial
    start_app "auth-service" "$APPS_DIR/auth-service-broken" "$AUTH_PORT"
    start_app "payment-service" "$APPS_DIR/payment-service-broken" "$PAYMENT_PORT"
    start_app "ecommerce" "$APPS_DIR/ecommerce-broken" "$ECOMMERCE_PORT"
else
    # Modo paralelo (background)
    if [ "$DAEMON_MODE" = true ]; then
        start_app "auth-service" "$APPS_DIR/auth-service-broken" "$AUTH_PORT"
        start_app "payment-service" "$APPS_DIR/payment-service-broken" "$PAYMENT_PORT"
        start_app "ecommerce" "$APPS_DIR/ecommerce-broken" "$ECOMMERCE_PORT"
    else
        # Sin daemon y sin sequential - solo mostrar ayuda
        echo -e "${YELLOW}Por favor especifica un modo:${NC}"
        echo "  -d    Para iniciar en background"
        echo "  -s    Para iniciar secuencialmente en foreground"
        echo ""
        echo "Ejemplo: $0 -d"
        exit 1
    fi
fi

# Mostrar resumen si es modo daemon
if [ "$DAEMON_MODE" = true ]; then
    echo ""
    echo -e "${GREEN}✅ Todas las apps iniciadas${NC}"
    echo ""
    echo -e "${BLUE}URLs de acceso:${NC}"
    echo "  Auth Service:       http://localhost:$AUTH_PORT/health"
    echo "  Payment Service:    http://localhost:$PAYMENT_PORT/health"
    echo "  E-commerce Service: http://localhost:$ECOMMERCE_PORT/health"
    echo ""
    echo -e "${BLUE}Comandos útiles:${NC}"
    echo "  ./scripts/stop-all.sh       # Detener todas las apps"
    echo "  ./scripts/health-check.sh   # Verificar estado"
    echo "  ./scripts/test-all.sh       # Ejecutar tests"
    echo ""
    
    # Mostrar logs si se solicitó
    if [ "$SHOW_LOGS" = true ]; then
        show_logs
    fi
fi
