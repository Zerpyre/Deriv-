def fibonacci_levels(min_price, max_price):
    return {
        "30.0%": max_price - (max_price - min_price) * 0.3,
        "40.0%": max_price - (max_price - min_price) * 0.4,
        "50%": (max_price + min_price) / 2,
        "60.0%": max_price - (max_price - min_price) * 0.6,
        "70.0%": min_price - (max_price - min_price) * 0.7
    }









