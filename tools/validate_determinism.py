import os
import sys
import hashlib
from data_generator import DataGenerator

def get_hash(data_str: str) -> str:
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()

def test_seed(seed: int):
    print(f"Testing seed {seed}...")
    
    # Run 1
    gen1 = DataGenerator(seed)
    users1 = gen1.generate_users(20)
    orders1 = gen1.generate_orders(50)
    trades1 = gen1.generate_trades(100)
    ticks1 = gen1.generate_ticks("BTC/USD", 100)
    candles1 = gen1.generate_candles("BTC/USD", 60, 50)
    
    hash1_users = get_hash(str(users1))
    hash1_orders = get_hash(str(orders1))
    hash1_trades = get_hash(str(trades1))
    hash1_ticks = get_hash(str(ticks1))
    hash1_candles = get_hash(str(candles1))

    # Run 2
    gen2 = DataGenerator(seed)
    users2 = gen2.generate_users(20)
    orders2 = gen2.generate_orders(50)
    trades2 = gen2.generate_trades(100)
    ticks2 = gen2.generate_ticks("BTC/USD", 100)
    candles2 = gen2.generate_candles("BTC/USD", 60, 50)
    
    hash2_users = get_hash(str(users2))
    hash2_orders = get_hash(str(orders2))
    hash2_trades = get_hash(str(trades2))
    hash2_ticks = get_hash(str(ticks2))
    hash2_candles = get_hash(str(candles2))
    
    assert hash1_users == hash2_users, "Users mismatch!"
    assert hash1_orders == hash2_orders, "Orders mismatch!"
    assert hash1_trades == hash2_trades, "Trades mismatch!"
    assert hash1_ticks == hash2_ticks, "Ticks mismatch!"
    assert hash1_candles == hash2_candles, "Candles mismatch!"
    
    print(f"  [OK] Seed {seed} is perfectly deterministic!")

def main():
    print("Validating determinism across 3 different seeds...")
    try:
        test_seed(42)
        test_seed(1337)
        test_seed(99999)
        print("\nAll determinism tests passed successfully!")
    except AssertionError as e:
        print(f"\n[ERROR] Determinism validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
