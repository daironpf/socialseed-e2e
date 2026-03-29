"""
SocialSeed Observability Main Application
Arquitectura Modular y SOLID para integrar Plugins de IA y Ecosistema Comunitario.
"""
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Importando Módulos del Core (Domain Driven Architecture)
from core.storage import store
from core.aggregator import CandlestickAggregator
from core.config import DEFAULT_TIMEFRAME_SEC

# Importando el Motor de Inserción (Infrastructure)
from sniffer.bot import traffic_generator_bot

# Importando el Ecosistema de Plugins Libres
from plugins.manager import plugin_manager
from plugins.implementations import TerminalAlertPlugin

# Inicialización Limpia de FastAPI (Presentation Layer)
app = FastAPI(title="SocialSeed API APM Modificable", description="Application Performance Management using TradingView OHLCV")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Cargar Plugins Comunitarios en el gestor global (Extensible Plugin Arch)
    plugin_manager.register(TerminalAlertPlugin())
    
    # Iniciar el Sniffer Bot en background sin bloquear WebRequests
    asyncio.create_task(traffic_generator_bot())

@app.get("/")
def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/services")
def get_services():
    """Devuelve los servicios únicos detectados por el sniffer de red."""
    logs = store.get_logs()
    unique_services = list(set([log["service"] for log in logs]))
    return ["Toda la Aplicacion"] + sorted(unique_services)

@app.get("/api/candlesticks")
def get_candlesticks(tf: int = DEFAULT_TIMEFRAME_SEC, svc: str = "Toda la Aplicacion"):
    """
    Controlador Limpio: Toma datos del Core Storage y se los pasa al Engine 
    Financiero (CandlestickAggregator) de FORMA AGNOSTICA a FastAPI.
    """
    logs = store.get_logs()
    if not logs:
        return []
    return CandlestickAggregator.aggregate(logs, tf, svc)

if __name__ == "__main__":
    import uvicorn
    # Lanzar el framework 
    uvicorn.run("app:app", host="0.0.0.0", port=8181, reload=True)
