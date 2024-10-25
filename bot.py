import websocket
import json
import numpy as np
import time
import datetime
import certifi
from datetime import datetime

# Variables globales
app_id = 'Your_id'
token = 'Your_token'
symbol = 'R_100'
last_update_time = None
amount = 1
loses = 0
support = 0
resistance = 0
ticks_data = []  # Almacena los ticks recibidos
candles = []  # Lista para almacenar las velas generadas
contract_open = False  # Controla si hay un contrato abierto

def on_open(ws):
    print("Conexión abierta.")
    authorize_message = {
        "authorize": token
    }
    ws.send(json.dumps(authorize_message))

def on_message(ws, message):
    global contract_open, ticks_data , amount , loses
    data = json.loads(message)

    if 'error' in data.keys():
        print('Error:', data['error']['message'])

    elif data.get("msg_type") == "authorize":
        #print("Autorización exitosa. Obteniendo las primeras 50 velas...")
        subscribe_to_candles(ws)

    elif data.get("msg_type") == "candles":
        #print("Velas históricas recibidas.")
        process_candles(ws, data['candles'])

    elif data.get("msg_type") == "tick":
        tick = data['tick']
        #print(f"Tick recibido: {tick}")
        ticks_data.append(tick)
        process_ticks(ws)

    elif data.get("msg_type") == "buy":
        contract_id = data['buy']['contract_id']
        contract_open = True  # Marcar contrato como abierto
        print(f"Operación ejecutada. ID del contrato: {contract_id}")
        subscribe_to_contract(ws, contract_id)

    elif data.get("msg_type") == "proposal_open_contract":
        if data['proposal_open_contract']['is_sold']:
            profit = data['proposal_open_contract']['profit']
            if profit > 0:
                print(f"El contrato ha sido vendido. Ganancia:{data['proposal_open_contract']['profit']}")
                amount = 1
                loses = 0
            elif profit < 0:
                print("El contrato perdió.")
                amount = amount * 2
                loses += 1
            else:
                print("El contrato terminó en empate.")
            print("El contrato ha finalizado. Buscando una nueva señal...")
            contract_open = False  # Contrato finalizado, se puede abrir otro
            process_ticks(ws)

def subscribe_to_candles(ws):
    candles_message = {
        "ticks_history": symbol,
        "end": "latest",
        "style": "candles",
        "count": 90,
        "granularity": 60  # 1 vela por minuto
    }
    ws.send(json.dumps(candles_message))

def process_candles(ws, received_candles):
    global candles
    for candle in received_candles:
        timestamp = datetime.utcfromtimestamp(candle['epoch'])
        new_candle = {
            'timestamp': timestamp,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close']
        }
        candles.append(new_candle)
    subscribe_to_ticks(ws)

def subscribe_to_ticks(ws):
    ticks_message = {
        "ticks": symbol,
        "subscribe": 1
    }
    ws.send(json.dumps(ticks_message))
    print("Suscripción a ticks enviada.")

def process_ticks(ws):
    global candles

    # Crear velas manualmente a partir de los ticks recibidos
    if len(ticks_data) > 0:
        tick_time = datetime.utcfromtimestamp(ticks_data[-1]['epoch'])
        tick_close = ticks_data[-1]['quote']

        # Si ya existe una vela y la estamos actualizando
        if len(candles) > 0 and candles[-1]['timestamp'].minute == tick_time.minute:
            # Actualiza la vela existente
            candles[-1]['close'] = tick_close
            candles[-1]['high'] = max(candles[-1]['high'], tick_close)
            candles[-1]['low'] = min(candles[-1]['low'], tick_close)
        else:
            # Nueva vela: El open es el close de la última vela, si existe
            if len(candles) > 0:
                open_price = candles[-1]['close']  # El open es el close de la última vela
                high_price = max(candles[-1]['high'], tick_close)  # High es el máximo entre el high anterior y el tick actual
                low_price = min(candles[-1]['low'], tick_close)  # Low es el mínimo entre el low anterior y el tick actual
            else:
                open_price = tick_close  # Si no hay velas, el open es el tick actual
                high_price = tick_close  # En la primera vela, high y low son iguales al tick
                low_price = tick_close

            new_candle = {
                'timestamp': tick_time,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': tick_close
            }
            candles.append(new_candle)
            print(f"Vela creada: {new_candle}")

        # Solo mantiene las últimas 90 velas para el análisis
        if len(candles) > 90:
            candles = candles[-90:]

        analyze_market(ws)



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

def calculate_ema(prices, period):

    if len(prices) < period:
        return np.nan  # No se puede calcular EMA si no hay suficientes datos

    multiplier = 2 / (period + 1)
    ema = [np.mean(prices[:period])]  # Usar el promedio simple como el primer valor de la EMA

    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])

    return np.array(ema)

def fibonacci_levels(min_price, max_price):
    return {
        "30.0%": max_price - (max_price - min_price) * 0.3,
        "40.0%": max_price - (max_price - min_price) * 0.4,
        "50%": (max_price + min_price) / 2,
        "60.0%": max_price - (max_price - min_price) * 0.6,
        "70.0%": min_price - (max_price - min_price) * 0.7
    }

def is_bullish_pattern(current_candle, previous_candle):
    # Ejemplo: Verificar si la vela actual es un Pin Bar alcista
    return (current_candle['close'] > current_candle['open'] and
            current_candle['close'] > previous_candle['high'])

def is_bearish_pattern(current_candle, previous_candle):
    # Ejemplo: Verificar si la vela actual es un Pin Bar bajista
    return (current_candle['close'] < current_candle['open'] and
            current_candle['close'] < previous_candle['low'])

def analyze_market(ws):
    global candles, contract_open, amount, loses, support, resistance, last_update_time

    print("Analizando velas...")

    if loses > 3:
        amount = 1
        loses = 0

    if len(candles) < 50:
        print("No hay suficientes velas para realizar el análisis.")
        return

    current_time = candles[-1]['timestamp']

    # Actualizar soporte, resistencia y niveles de Fibonacci cada dos minutos
    if last_update_time is None or (current_time - last_update_time).seconds >= 120:
        closes = [candle['close'] for candle in candles]
        support = np.min(closes[-50:])
        resistance = np.max(closes[-50:])
        fibonacci = fibonacci_levels(support, resistance)
        last_update_time = current_time
        print(f"Soporte y resistencia actualizados: Soporte = {support}, Resistencia = {resistance}")
        print(f"Niveles de Fibonacci: {fibonacci}")

    current_price = candles[-1]['close']
    print(f"Precio actual: {current_price}, Soporte: {support}, Resistencia: {resistance}")

    # Calcular la tendencia usando RSI o MACD
    closes = [candle['close'] for candle in candles]
    rsi = calculate_rsi(closes)
    macd_line, signal_line = calculate_macd(closes)

    # Determinar la tendencia: alcista si MACD está por encima de la signal line o RSI > 50, bajista si MACD está por debajo de la signal line o RSI < 50
    is_bullish = macd_line[-1] > signal_line[-1] or rsi > 50
    is_bearish = macd_line[-1] < signal_line[-1] or rsi < 50

    if fibonacci["40.0%"] <= current_price <= fibonacci["50%"] and is_bullish and not contract_open:
        print(f"Cerca del nivel de Fibonacci entre 40% y 50% en tendencia alcista. Ejecutando operación Rise.")
        execute_rise_trade(ws, amount)

    
    elif fibonacci["60.0%"] <= current_price <= fibonacci["70.0%"] and is_bearish and not contract_open:
        print(f"Cerca del nivel de Fibonacci entre 60% y 70% en tendencia bajista. Ejecutando operación Fall.")
        execute_fall_trade(ws, amount)

def execute_rise_trade(ws,amount):
    rise_trade_message = {
        "buy": 1,
        "subscribe": 1,
        "price": 20,
        "parameters": {
            "amount": amount,
            "basis": "stake",
            "contract_type": "CALL",
            "currency": "USD",
            "duration": 2,
            "duration_unit": "m",
            "symbol": symbol
        }
    }
    ws.send(json.dumps(rise_trade_message))
    print("Operación Rise enviada. Esperando confirmación...")

def execute_fall_trade(ws,amount):
    fall_trade_message = {
        "buy": 1,
        "subscribe": 1,
        "price": 20,
        "parameters": {
            "amount": amount,
            "basis": "stake",
            "contract_type": "PUT",
            "currency": "USD",
            "duration": 2,
            "duration_unit": "m",
            "symbol": symbol
        }
    }
    ws.send(json.dumps(fall_trade_message))
    print("Operación Fall enviada. Esperando confirmación...")

def subscribe_to_contract(ws, contract_id):
    contract_message = {
        "proposal_open_contract": 1,
        "contract_id": contract_id
    }
    ws.send(json.dumps(contract_message))

def on_error(ws, error):
    print("Error en WebSocket:", error)

def on_close(ws, close_status_code, close_msg):
    print("Conexión cerrada. Intentando reconectar...")
    time.sleep(10)
    ws.run_forever()

# Iniciar WebSocket
ws = websocket.WebSocketApp(
    "wss://ws.binaryws.com/websockets/v3?app_id=" + app_id,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close)
ws.run_forever(sslopt={"ca_certs": certifi.where()})









