from kitetdx import Reader

def test_lazy_loading():
    print("--- Initializing Reader ---")
    reader = Reader.factory()
    
    print("\n--- First call to SWS industry (should trigger instantiation/check) ---")
    ind1 = reader.get_industries(source='sws', level=1)
    print(f"Got {len(ind1)} industries")
    
    print("\n--- Second call to SWS industry (should NOT trigger instantiation/check) ---")
    ind2 = reader.get_industries(source='sws', level=2)
    print(f"Got {len(ind2)} industries")
    
    print("\n--- Call to stock industry (should NOT trigger instantiation/check) ---")
    stock_ind = reader.get_stock_industry('600036', source='sws')
    print(f"Stock Info: {stock_ind['l1_name']} / {stock_ind['l2_name']}")
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_lazy_loading()
