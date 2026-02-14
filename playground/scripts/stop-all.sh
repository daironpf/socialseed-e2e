#!/bin/bash
#
# stop-all.sh - Detiene todas las aplicaciones del playground
#
# Uso: ./stop-all.sh [opciones]
# Opciones:
#   -f, --force    Forzar detención (kill -9)
#   -h, --help     Mostrar ayuda
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
    echo -e "${BLUE}SocialSeed E2E Playground - Stop All Apps${NC}"
    echo ""
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -f, --force    Forzar detención (kill -9)"
    echo "  -h, --help     Mostrar esta ayuda"
    echo ""
}

# Variables
FORCE_MODE=false

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE_MODE=true
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

echo -e "${BLUE}🛑 Deteniendo aplicaciones del playground...${NC}"
echo ""

# Función para detener app por PID
stop_by_pid() {
    local name=$1
    local pid_file="/tmp/playground-${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            if [ "$FORCE_MODE" = true ]; then
                kill -9 "$pid" 2>/dev/null || true
            else
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
            echo -e "${GREEN}  ✅ $name detenido${NC}"
        else
            echo -e "${YELLOW}  ⚠️  $name no estaba corriendo${NC}"
            rm -f "$pid_file"
        fi
    else
        # Intentar encontrar por nombre
        local pids=$(pgrep -f "python.*${name}.*app.py" || true)
        if [ -n "$pids" ]; then
            if [ "$FORCE_MODE" = true ]; then
                echo "$pids" | xargs kill -9 2>/dev/null || true
            else
                echo "$pids" | xargs kill 2>/dev/null || true
            fi
            echo -e "${GREEN}  ✅ $name detenido${NC}"
        else
            echo -e "${YELLOW}  ⚠️  $name no encontrado${NC}"
        fi
    fi
}

# Detener cada app
stop_by_pid "auth-service"
stop_by_pid "payment-service"
stop_by_pid "ecommerce"

# Limpiar archivos de log
echo ""
echo -e "${BLUE}🧹 Limpiando archivos temporales...${NC}"
rm -f /tmp/playground-*.log /tmp/playground-*.pid

echo ""
echo -e "${GREEN}✅ Todas las apps detenidas${NC}"
