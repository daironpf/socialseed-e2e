from typing import List, Dict

class CandlestickAggregator:
    """Motor Financiero que convierte logs crudos de red en Velas Japonesas OHLCV."""
    
    @staticmethod
    def aggregate(logs: List[Dict], timeframe_sec: int, service_filter: str) -> List[Dict]:
        candles_dict = {}
        
        for log in logs:
            # Filtrado Semántico por Microservicio
            if service_filter != "Toda la Aplicacion" and log.get("service") != service_filter:
                continue
                
            # Truncar el timestamp al múltiplo del timeframe para agrupar
            period_timestamp = int(log["timestamp"] // timeframe_sec) * timeframe_sec
            latency = log["latency"]
            
            if period_timestamp not in candles_dict:
                candles_dict[period_timestamp] = {
                    "time": period_timestamp,
                    "open": latency,
                    "high": latency,
                    "low": latency,
                    "close": latency,
                    "volume": 1,
                    "errors": 1 if log.get("status", 200) >= 400 else 0
                }
            else:
                c = candles_dict[period_timestamp]
                if latency > c["high"]: c["high"] = latency
                if latency < c["low"]: c["low"] = latency
                c["close"] = latency
                c["volume"] += 1
                if log.get("status", 200) >= 400: c["errors"] += 1
                
        # Retorna el array ordenado cronológicamente para el render de TradingView
        return sorted(list(candles_dict.values()), key=lambda x: x["time"])
