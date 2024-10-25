def is_bullish_pattern(current_candle, previous_candle):
    # Ejemplo: Verificar si la vela actual es un Pin Bar alcista
    return (current_candle['close'] > current_candle['open'] and
            current_candle['close'] > previous_candle['high'])

def is_bearish_pattern(current_candle, previous_candle):
    # Ejemplo: Verificar si la vela actual es un Pin Bar bajista
    return (current_candle['close'] < current_candle['open'] and
            current_candle['close'] < previous_candle['low'])









