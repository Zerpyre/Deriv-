import json

def execute_rise_trade(ws,amount,symbol):
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









