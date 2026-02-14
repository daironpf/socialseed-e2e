#!/bin/bash
#
# health-check.sh - Verifica el estado de todas las aplicaciones
#
# Uso: ./health-check.sh [opciones]
# Opciones:
#   -v, --verbose    Mostrar información detallada
#   -j, --json       Output en formato JSON
#   -h, --help       Mostrar ayuda
#

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
AUTH_URL="http://localhost:5001"
PAYMENT_URL="http://localhost:5002"
ECOMMERCE_URL="http://localhost:5003"
TIMEOUT=5

# Variables
VERBOSE=false
JSON_OUTPUT=false

# Función de ayuda
show_help() {
    echo -e "${BLUE}SocialSeed E2E Playground - Health Check${NC}"
    echo ""
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -v, --verbose    Mostrar información detallada"
    echo "  -j, --json       Output en formato JSON"
    echo "  -h, --help       Mostrar esta ayuda"
    echo ""
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -j|--json)
            JSON_OUTPUT=true
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

# Función para verificar salud de un servicio
check_health() {
    local name=$1
    local url=$2
    local health_endpoint="$url/health"
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$health_endpoint" 2>/dev/null || echo "000")
    elif command -v wget >/dev/null 2>&1; then
        response=$(wget -q --timeout="$TIMEOUT" --server-response "$health_endpoint" 2>&1 | grep "HTTP/" | tail -1 | awk '{print $2}' || echo "000")
    else
        echo "Error: curl o wget requeridos"
        exit 1
    fi
    
    if [ "$response" = "200" ]; then
        echo "healthy"
    else
        echo "unhealthy"
    fi
}

# Función para obtener info adicional
get_service_info() {
    local url=$1
    local info="{}"
    
    if command -v curl >/dev/null 2>&1; then
        info=$(curl -s --max-time "$TIMEOUT" "$url/health" 2>/dev/null || echo "{}")
    fi
    
    echo "$info"
}

# Verificar cada servicio
auth_status=$(check_health "auth-service" "$AUTH_URL")
payment_status=$(check_health "payment-service" "$PAYMENT_URL")
ecommerce_status=$(check_health "ecommerce" "$ECOMMERCE_URL")

# Output en JSON
if [ "$JSON_OUTPUT" = true ]; then
    cat <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "services": {
    "auth-service": {
      "url": "$AUTH_URL",
      "status": "$auth_status"
    },
    "payment-service": {
      "url": "$PAYMENT_URL",
      "status": "$payment_status"
    },
    "ecommerce": {
      "url": "$ECOMMERCE_URL",
      "status": "$ecommerce_status"
    }
  },
  "overall": "$([ "$auth_status" = "healthy" ] && [ "$payment_status" = "healthy" ] && [ "$ecommerce_status" = "healthy" ] && echo "healthy" || echo "unhealthy")"
}
EOF
    exit 0
fi

# Output normal
echo -e "${BLUE}🏥 Health Check - Playground Services${NC}"
echo ""

# Auth Service
if [ "$auth_status" = "healthy" ]; then
    echo -e "${GREEN}✅ Auth Service${NC}        http://localhost:5001"
else
    echo -e "${RED}❌ Auth Service${NC}        http://localhost:5001"
fi

# Payment Service
if [ "$payment_status" = "healthy" ]; then
    echo -e "${GREEN}✅ Payment Service${NC}     http://localhost:5002"
else
    echo -e "${RED}❌ Payment Service${NC}     http://localhost:5002"
fi

# E-commerce Service
if [ "$ecommerce_status" = "healthy" ]; then
    echo -e "${GREEN}✅ E-commerce Service${NC}  http://localhost:5003"
else
    echo -e "${RED}❌ E-commerce Service${NC}  http://localhost:5003"
fi

echo ""

# Veredicto general
if [ "$auth_status" = "healthy" ] && [ "$payment_status" = "healthy" ] && [ "$ecommerce_status" = "healthy" ]; then
    echo -e "${GREEN}✅ Todos los servicios están saludables${NC}"
    exit 0
else
    echo -e "${RED}❌ Algunos servicios no están disponibles${NC}"
    echo ""
    echo -e "${YELLOW}Para iniciar los servicios:${NC}"
    echo "  ./scripts/start-all.sh -d"
    exit 1
fi
