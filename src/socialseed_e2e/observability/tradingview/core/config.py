import os

# Conectando con los Microservicios Reales (Docker) del Proyecto
SERVICES = {
    "auth": "http://localhost:8085/actuator/health",
    "socialuser": "http://localhost:8090/actuator/health"
}

# Límites de seguridad para no consumir toda la RAM en producción
MAX_LOG_HISTORY = 10000

# Tiempo base de agrupación de velas (default)
DEFAULT_TIMEFRAME_SEC = 5
