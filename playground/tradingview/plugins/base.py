from typing import Dict

class ObservabilityPlugin:
    """
    Interfaz Base (SOLID - Dependency Inversion) para crear plugins de la comunidad.
    Cualquier plugin nuevo debe heredar de esta clase y sobreescribir los hooks.
    """
    
    @property
    def name(self) -> str:
        return "BasePlugin"

    @property
    def description(self) -> str:
        return "Un plugin genérico de observabilidad"

    async def on_log_captured(self, log: Dict) -> None:
        """Hook que se dispara cada vez que la red intercepta una nueva latencia HTTP."""
        pass
        
    async def on_candle_closed(self, candle: Dict) -> None:
        """Hook que se dispara cuando una vela temporal completa se calcula y cierra."""
        pass
