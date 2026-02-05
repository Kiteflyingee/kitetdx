import sys
import os
import pandas as pd

# Ensure we import local kitetdx
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kitetdx import Reader

def test_industry_functions():
    # Use the path from the user's environment
    tdx_dir = '/Volumes/SSDFull/stock/new_tdx'
    reader = Reader.factory(market='std', tdxdir=tdx_dir)

    print("--- Testing get_industries ---")
    industries = reader.get_industries()
    if industries.empty:
        print("FAILED: get_industries returned empty DataFrame")
    else:
        print(f"SUCCESS: Got {len(industries)} industries")
        
        # Level 0 (Sector): Code length 3 (e.g. T01)
        level0 = industries[industries['industry_code'].str.len() == 3]
        print(f"\n--- 行业门类 (Level 0, {len(level0)}) ---")
        for idx, row in level0.iterrows():
            print(f"{row['industry_name']} ({row['industry_code']})")
            
        # Level 1 (Industry): Code length 5 (e.g. T0101)
        level1 = industries[industries['industry_code'].str.len() == 5]
        print(f"\n--- 一级行业 (Level 1, {len(level1)}) ---")
        for idx, row in level1.iterrows():
            print(f"  {row['industry_name']} ({row['industry_code']}) -> {row['industry_code'][:3]}")

        # Level 2 (Sub-Industry): Code length 7 (e.g. T010101)
        level2 = industries[industries['industry_code'].str.len() == 7]
        print(f"\n--- 二级行业 (Level 2, {len(level2)}) ---")
        for idx, row in level2.iterrows():
            print(f"    {row['industry_name']} ({row['industry_code']}) -> {row['industry_code'][:5]}")
        
        # Check for specific industry
        bank_ind = industries[industries['industry_name'] == '银行']
        if not bank_ind.empty:
            print(f"\nFound '银行': {bank_ind.iloc[0].to_dict()}")
        else:
            print("\nWARNING: '银行' industry not found in list")

    print("\n--- Testing get_industry_stocks ('银行') ---")
    bank_stocks = reader.get_industry_stocks('银行')
    print(f"Bank stocks count: {len(bank_stocks)}")
    if '000001' in bank_stocks:
        print("SUCCESS: 000001 (Ping An Bank) found in '银行' stocks")
    else:
        print("FAILED: 000001 not found in '银行' stocks")
        
    print("\n--- Testing get_industry_stocks ('T1001') ---")
    t_stocks = reader.get_industry_stocks('T1001')
    if len(t_stocks) == len(bank_stocks):
         print("SUCCESS: T1001 returns same count as '银行'")
    else:
         print(f"WARNING: Count mismatch. '银行': {len(bank_stocks)}, 'T1001': {len(t_stocks)}")

    print("\n--- Testing get_stock_industry ('000001') ---")
    ind_info = reader.get_stock_industry('000001')
    if ind_info:
        print(f"SUCCESS: 000001 industry info: {ind_info}")
        if ind_info.get('industry_name') == '银行':
            print("SUCCESS: Industry name matches '银行'")
        else:
            print(f"WARNING: Expected '银行', got {ind_info.get('industry_name')}")
    else:
        print("FAILED: get_stock_industry('000001') returned None")

if __name__ == "__main__":
    test_industry_functions()
