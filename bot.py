import websocket
import json
import numpy as np
import time
import datetime
import certifi
from datetime import datetime
from Indicadores.fibonacci import fibonacci_levels
from Indicadores.rsi import calculate_rsi
from Indicadores.macd import calculate_macd
from eventos.Rise import execute_rise_trade
from eventos.Fall import execute_fall_trade

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

def analyze_market(ws):
    global candles, contract_open, amount, loses, support, resistance, last_update_time , symbol

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
        execute_rise_trade(ws, amount , symbol)

    
    elif fibonacci["60.0%"] <= current_price <= fibonacci["70.0%"] and is_bearish and not contract_open:
        print(f"Cerca del nivel de Fibonacci entre 60% y 70% en tendencia bajista. Ejecutando operación Fall.")
        execute_fall_trade(ws, amount , symbol)



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









