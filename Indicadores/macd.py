# Función para calcular MACD
def calculate_macd(prices, short_period=12, long_period=26, signal_period=9):
    # Calcular las EMAs de corto y largo plazo
    short_ema = calculate_ema(prices, short_period)
    long_ema = calculate_ema(prices, long_period)

    # Asegurarse de que ambas EMAs tengan la misma longitud
    min_length = min(len(short_ema), len(long_ema))
    short_ema = short_ema[-min_length:]  # Cortar para que tenga la misma longitud
    long_ema = long_ema[-min_length:]

    # Calcular la línea MACD
    macd_line = short_ema - long_ema

    # Calcular la signal line usando el EMA de la línea MACD
    signal_line = calculate_ema(macd_line, signal_period)

    return macd_line, signal_line









