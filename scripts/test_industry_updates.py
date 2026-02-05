import sys
import os
import pandas as pd

# Ensure we import local kitetdx
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kitetdx import Reader
from kitetdx.sws import SwsReader

def test_tdx_industry(reader):
    print("\n=== Testing TDX Industry (source='tdx') ===")
    
    # 1. Test get_industries
    print("Testing get_industries(level=1)...")
    l1 = reader.get_industries(level=1, source='tdx')
    print(f"L1 Industries: {len(l1)}")
    if not l1.empty:
        print(l1.head(3))
        
    print("\nTesting get_industries(level=2)...")
    l2 = reader.get_industries(level=2, source='tdx')
    print(f"L2 Industries: {len(l2)}")
    if not l2.empty:
        print(l2.head(3))

    # 2. Test get_industry_stocks
    test_ind = '银行'
    print(f"\nTesting get_industry_stocks('{test_ind}')...")
    stocks = reader.get_industry_stocks(test_ind, source='tdx')
    print(f"Stocks in '{test_ind}': {len(stocks)}")
    if stocks:
        print(f"First 5: {stocks[:5]}")

    # 3. Test get_stock_industry
    test_stock = '000001'
    print(f"\nTesting get_stock_industry('{test_stock}')...")
    info = reader.get_stock_industry(test_stock, source='tdx')
    print(f"Industry info for {test_stock}: {info}")

def test_sws_industry(reader):
    print("\n=== Testing SWS Industry (source='sws') ===")
    
    # 1. Test get_industries
    print("Testing get_industries(level=1, source='sws')...")
    try:
        l1 = reader.get_industries(level=1, source='sws')
        print(f"L1 Industries: {len(l1)}")
        if isinstance(l1, pd.DataFrame) and not l1.empty:
            print(l1.head(3))
        elif isinstance(l1, list):
            print(f"First 3: {l1[:3]}")
    except Exception as e:
        print(f"Error testing SWS get_industries: {e}")

    # 2. Test get_industry_stocks
    test_ind = '银行' # SWS should have '银行' or '银行业'
    print(f"\nTesting get_industry_stocks('{test_ind}', source='sws')...")
    try:
        stocks = reader.get_industry_stocks(test_ind, source='sws')
        print(f"Stocks in '{test_ind}': {len(stocks)}")
        if stocks:
            print(f"First 5: {stocks[:5]}")
    except Exception as e:
        print(f"Error testing SWS get_industry_stocks: {e}")

    # 3. Test get_stock_industry
    test_stock = '000001'
    print(f"\nTesting get_stock_industry('{test_stock}', source='sws')...")
    try:
        info = reader.get_stock_industry(test_stock, source='sws')
        print(f"Industry info for {test_stock}: {info}")
    except Exception as e:
        print(f"Error testing SWS get_stock_industry: {e}")

def test_sws_block_method():
    print("\n=== Testing SwsReader.block() method ===")
    try:
        sws = SwsReader()
        print("Testing sws.block(concept_type=1, return_df=True)...")
        df = sws.block(concept_type=1, return_df=True)
        print(f"Block DF shape: {df.shape}")
        if not df.empty:
            print(df.head(3))
            
        print("\nTesting sws.block(concept_type=2, return_df=False)...")
        blocks = sws.block(concept_type=2, return_df=False)
        print(f"Blocks count: {len(blocks)}")
        if blocks:
            b = blocks[0]
            print(f"First block: {b.concept_name}, Stocks count: {len(b.stocks)}")
    except Exception as e:
        print(f"Error testing SwsReader.block: {e}")

if __name__ == "__main__":
    tdx_dir = '/Volumes/SSDFull/stock/new_tdx'
    if not os.path.exists(tdx_dir):
        # Try a common alternative if not found
        tdx_dir = os.path.expanduser('~/.kitetdx/tdx')
        
    print(f"Using TDX directory: {tdx_dir}")
    
    try:
        reader = Reader.factory(market='std', tdxdir=tdx_dir)
        
        test_tdx_industry(reader)
        test_sws_industry(reader)
        test_sws_block_method()
        
    except Exception as e:
        print(f"Failed to initialize reader or run tests: {e}")
        import traceback
        traceback.print_exc()