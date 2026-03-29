import asyncio
import time
import httpx
import random
from typing import Dict

from core.config import SERVICES
from core.storage import store
from plugins.manager import plugin_manager

async def hit_service() -> Dict:
    """Lanza una petición orgánica al array de microservicios e inyecta jitter."""
    service_name, target_url = random.choice(list(SERVICES.items()))
    
    start_time = time.time()
    status = 0
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(target_url)
            status = resp.status_code
    except Exception:
        status = 500  # Error de conexión
    end_time = time.time()
    
    latency_ms = int((end_time - start_time) * 1000)
    
    # Inyectar una ínfima variabilidad simulando el ping de internet real
    latency_ms += random.randint(1, 15)
    
    if latency_ms < 1: latency_ms = 1

    return {
        "timestamp": start_time,
        "latency": latency_ms,
        "status": status,
        "service": service_name
    }

async def traffic_generator_bot():
    """Bot en background de Sniffer disparando ráfagas continuas asíncronas."""
    while True:
        try:
            log = await hit_service()
            
            # 1. Guardar en Storage Core App
            store.add_log(log)
            
            # 2. Notificar al sistema de plugins de red global
            await plugin_manager.dispatch_log(log)
            
        except Exception as e:
            print(f"Error crítico en Sniffer Bot: {e}")
            
        # Velocidad de ráfaga: aprox 5 requests / segundo
        await asyncio.sleep(0.2)
