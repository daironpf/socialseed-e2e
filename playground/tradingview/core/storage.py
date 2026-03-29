from typing import List, Dict
from core.config import MAX_LOG_HISTORY

class MemoryStorage:
    """Clase Singleton que almacena y gestiona en RAM los logs de latencia."""
    def __init__(self, max_size: int = MAX_LOG_HISTORY):
        self.logs: List[Dict] = []
        self.max_size = max_size

    def add_log(self, log: Dict) -> None:
        self.logs.append(log)
        # Limpieza continua FIFO (First-In, First-Out)
        if len(self.logs) > self.max_size:
            self.logs.pop(0)

    def get_logs(self) -> List[Dict]:
        return self.logs

# Singleton Pattern para compartir estado entre FastApi y el Bot Sniffer
store = MemoryStorage()
