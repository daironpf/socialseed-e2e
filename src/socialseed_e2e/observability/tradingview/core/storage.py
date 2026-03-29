from typing import List, Dict
from core.config import MAX_LOG_HISTORY

class MemoryStorage:
    """Clase Singleton que almacena y gestiona en RAM los logs de latencia."""
    def __init__(self, max_size: int = MAX_LOG_HISTORY):
        self.logs: List[Dict] = []
        self.endpoints: Dict[str, List[Dict[str, str]]] = {}
        self.max_size = max_size

    def add_log(self, log: Dict) -> None:
        self.logs.append(log)
        self.add_endpoint(log)
        # Limpieza continua FIFO (First-In, First-Out)
        if len(self.logs) > self.max_size:
            self.logs.pop(0)

    def add_endpoint(self, log: Dict) -> None:
        """Extrae y almacena endpoints únicos de los logs de tráfico."""
        service = log.get("service", "Unknown")
        method = log.get("method", "GET")
        path = log.get("path", "/")
        
        if service not in self.endpoints:
            self.endpoints[service] = []
            
        endpoint = {"method": method, "path": path}
        if endpoint not in self.endpoints[service]:
            self.endpoints[service].append(endpoint)

    def get_logs(self) -> List[Dict]:
        return self.logs

    def get_endpoints(self) -> Dict[str, List[Dict[str, str]]]:
        return self.endpoints

# Singleton Pattern para compartir estado entre FastApi y el Bot Sniffer
store = MemoryStorage()
