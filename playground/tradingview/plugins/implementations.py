from typing import Dict
from plugins.base import ObservabilityPlugin

class TerminalAlertPlugin(ObservabilityPlugin):
    """Ejemplo de Plugin Comunitario que alerta si la latencia es crítica conectándose por Hook."""
    
    @property
    def name(self) -> str:
        return "Terminal Alerter Plugin"
        
    @property
    def description(self) -> str:
        return "Avisa por terminal si la latencia de un servicio experimenta picos anormales."

    async def on_log_captured(self, log: Dict) -> None:
        """Lógica de Fuzzing Opcional: Detecta picos anómalos de latencia al vuelo."""
        if log.get("latency", 0) > 40: # Un pico ridículo para un ping a localhost
            print(f"🚨 [ALERT TACTICO] El servicio {log.get('service')} sufre latencia alta: {log['latency']} ms!")
