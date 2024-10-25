import numpy as np

def calculate_ema(prices, period):

    if len(prices) < period:
        return np.nan  # No se puede calcular EMA si no hay suficientes datos

    multiplier = 2 / (period + 1)
    ema = [np.mean(prices[:period])]  # Usar el promedio simple como el primer valor de la EMA

    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])

    return np.array(ema)









