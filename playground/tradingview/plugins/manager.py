from typing import List, Dict
from plugins.base import ObservabilityPlugin

class PluginManager:
    """Gestiona el ciclo de vida de los plugins comunitarios (SOLID - Single Responsibility)."""
    
    def __init__(self):
        self._plugins: List[ObservabilityPlugin] = []

    def register(self, plugin: ObservabilityPlugin):
        """Registra un nuevo plugin para escuchar eventos de telemetría."""
        self._plugins.append(plugin)
        print(f"[Sistema de Plugins] Cargado exitosamente: {plugin.name} - {plugin.description}")

    async def dispatch_log(self, log: Dict):
        """Notifica a todos los plugins registrados que entró un nuevo log desde el Sniffer."""
        if not self._plugins:
            return
            
        for p in self._plugins:
            try:
                await p.on_log_captured(log)
            except Exception as e:
                print(f"[Error de Plugin] El plugin {p.name} falló y no completó su tarea: {e}")

# Instancia Singleton Global
plugin_manager = PluginManager()
