# Diseño Técnico: Gráficos de Velas Japonesas para Tráfico API (TradingView Style)

Esta especificación detalla cómo transformar los logs de tráfico HTTP crudos que intercepta `socialseed-e2e` en datos financieros (OHLCV: Open, High, Low, Close, Volume) para ser visualizados como velas japonesas reales en el Dashboard de Vue.js.

## 1. El Concepto Matemático: HTTP a OHLCV

En trading, una vela representa el movimiento del precio en un periodo de tiempo (Ej. 1 minuto). Para nuestra API de `SocialSeed`, el "precio" será el **Tiempo de Respuesta (Latencia en milisegundos)**.

Para agrupar los logs interceptados en un marco temporal (Ej. Vela de 1 Minuto - M1), calcularemos:

*   **Open (Apertura)**: La latencia (ms) de la *primera* petición HTTP de ese minuto.
*   **High (Máximo)**: La latencia de la petición *más lenta* (el pico más alto) de ese minuto.
*   **Low (Mínimo)**: La latencia de la petición *más rápida* de ese minuto.
*   **Close (Cierre)**: La latencia de la *última* petición HTTP de ese minuto.
*   **Volume (Volumen)**: La *cantidad total de peticiones* (Requests) recibidas en ese minuto.

### Significado de los Colores (Rojo/Verde)
*   🟢 **Vela Verde (Cierre < Apertura)**: Significa que la latencia disminuyó al final del periodo (el servidor empezó lento y terminó rápido). *¡Buen rendimiento!*
*   🔴 **Vela Roja (Cierre > Apertura)**: Significa que la latencia aumentó al final del periodo (el servidor se volvió más lento). *¡Alerta temprana de saturación!*
*   💥 **Marca Especial (Errores 4xx/5xx)**: Si en ese minuto hubo un error HTTP 500 o 404, la vela puede pintarse de un color especial (ej. Amarillo/Morado) o mostrar un icono encima de la mecha superior.

## 2. Arquitectura de Implementación (Local y Realizable)

Todo esto es 100% construible ahora mismo desde tu PC usando librerías Open Source gratuitas.

### A. Backend (Python / FastAPI / Pandas)
Debemos transformar los logs crudos a JSON de OHLCV.

1.  **Recolección**: `socialseed-e2e` guarda cada latencia en un log (Ej. SQLite o un CSV temporal).
2.  **Procesamiento Rápido**: Podemos usar la librería `pandas` en Python. Pandas tiene una función mágica llamada `resample()` que agrupa series de tiempo exactamente como las gráficas de bolsa.

```python
# Ejemplo de pseudocódigo en el backend para agrupar por minuto ('1Min')
import pandas as pd

# df es un DataFrame con ['timestamp', 'latency_ms', 'status_code']
df.set_index('timestamp', inplace=True)
ohlcv = df['latency_ms'].resample('1Min').ohlc() # Genera Open, High, Low, Close automáticamente
ohlcv['volume'] = df['latency_ms'].resample('1Min').count()
# Convertir a JSON para enviar al Dashboard
return ohlcv.reset_index().to_dict(orient='records')
```

### B. Frontend (Vue.js + Tailwind)
Para graficar verdaderas Velas Japonesas fluidas sin que el navegador se trabe, **NO** hay que reinventar la rueda. Usaremos la librería oficial de TradingView, que es abierta y gratuita.

**Librería Recomendada**: `lightweight-charts` (Desarrollada por TradingView).
*   **NPM**: `npm install lightweight-charts`
*   Es súper ligera, nativa en HTML5 Canvas y permite hacer Zoom in/out fluido con el ratón.

```javascript
// Ejemplo conceptual Vue component con Lightweight Charts
import { createChart } from 'lightweight-charts';

const chart = createChart(document.getElementById('chart-container'), { width: 800, height: 400 });
const candlestickSeries = chart.addCandlestickSeries({
    upColor: '#26a69a', // Verde Tailwind
    downColor: '#ef5350', // Rojo Tailwind
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
});

// data_from_fastapi tiene { time, open, high, low, close }
candlestickSeries.setData(data_from_fastapi);
```

## 3. Plan de Acción (Siguiente Paso Manual)

Para aterrizar esto hoy mismo:
1.  En tu carpeta `D:\.dev\proyectos\socialseed-e2e\dashboard` (donde tienes tu Vue.js + Tailwind), instalar `lightweight-charts`.
2.  Levantar el microservicio `auth` de tu proyecto SocialSeed (`D:\.dev\proyectos\SocialSeed`).
3.  Escribir un pequeño script Python local que haga peticiones continuas al `/login` e imprima las latencias reales.
4.  Mostrar esa gráfica en tu dashboard.

Este es un paso 100% realista, sin IA espacial, que dejará a cualquiera con la boca abierta al ver "Tráfico HTTP" moviéndose como Bitcoin en la pantalla.
