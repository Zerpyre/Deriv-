import json

def execute_fall_trade(ws,amount,symbol):
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









