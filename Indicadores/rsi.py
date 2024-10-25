import numpy as np

# Función para calcular el RSI
def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Inicializa las primeras ganancias y pérdidas promedio
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    rsi = [100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss != 0 else 100]

    # Iterar sobre los precios restantes para calcular el RSI acumulativo
    for i in range(period, len(prices) - 1):
        current_gain = gains[i]
        current_loss = losses[i]

        # Actualizar la ganancia y pérdida promedio
        avg_gain = (avg_gain * (period - 1) + current_gain) / period
        avg_loss = (avg_loss * (period - 1) + current_loss) / period

        # Evitar divisiones por cero y calcular el RSI
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi_value = 100 - (100 / (1 + rs))
        rsi.append(rsi_value)

    return rsi[-1]  # Devuelve el último valor del RSI









