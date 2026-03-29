import os

# Conectando con los Microservicios Reales (Docker/Environments)
# El sistema ahora busca las URLs en variables de entorno para facilitar despliegues
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8085/actuator/health"),
    "socialuser": os.getenv("SOCIALUSER_SERVICE_URL", "http://localhost:8090/actuator/health")
}

# Límites de seguridad para no consumir toda la RAM en producción
MAX_LOG_HISTORY = 10000

# Tiempo base de agrupación de velas (default)
DEFAULT_TIMEFRAME_SEC = 5
