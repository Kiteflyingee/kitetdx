import os
import sys
import pandas as pd

# Ensure local kitetdx is used
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kitetdx import Reader, SwsReader, Affair

def test_industry_levels(reader):
    print("\n--- Testing Unified Industry Levels ---")
    
    # 1. Test Level 1 (Default)
    print("\n[Level 1: Primary]")
    for source in ['tdx', 'sws']:
        try:
            df = reader.get_industries(source=source, level=1)
            print(f"Source {source.upper()} Level 1: {len(df)} industries")
            if not df.empty:
                print(df.head(2))
        except Exception as e:
            print(f"[FAIL] {source} Level 1 error: {e}")

    # 2. Test Level 2 (Secondary)
    print("\n[Level 2: Secondary]")
    for source in ['tdx', 'sws']:
        try:
            df = reader.get_industries(source=source, level=2)
            print(f"Source {source.upper()} Level 2: {len(df)} industries")
            if not df.empty:
                print(df.head(2))
        except Exception as e:
            print(f"[FAIL] {source} Level 2 error: {e}")

    # 3. Test Source Specific Levels
    print("\n[Special Levels - Verification]")
    # TDX Level 0
    df0 = reader.get_industries(source='tdx', level=0)
    print(f"TDX Level 0 (Expect 0): {len(df0)} industries")

def test_stock_industry_consistency(reader):
    print("\n--- Testing Stock-to-Industry Consistency ---")
    stocks = ['600036', '000001']
    for symbol in stocks:
        print(f"\n[Stock: {symbol}]")
        for source in ['tdx', 'sws']:
            try:
                info = reader.get_stock_industry(symbol, source=source)
                print(f"Source {source.upper()}: {info}")
            except Exception as e:
                print(f"[FAIL] {symbol} {source} error: {e}")

def test_affair_path():
    print("\n--- Testing Affair Centralized Path ---")
    try:
        from kitetdx.affair import get_default_downdir
        default_dir = get_default_downdir()
        print(f"Default Affair downdir: {default_dir}")
        
        home = os.path.expanduser('~')
        expected_suffix = os.path.join('.kitetdx', 'tmp')
        
        if expected_suffix not in default_dir:
            print(f"[FAIL] Default downdir isn't centralized: {default_dir}")
            return
            
        print(f"[OK] Default downdir is centralized: {default_dir}")
        
        if os.path.exists(default_dir):
            print(f"[OK] Centralized directory exists.")
            local_files = os.listdir(default_dir)
            print(f"Local files in cache: {len(local_files)}")
        else:
            print(f"[WARNING] Centralized directory does not exist yet (but will be created on fetch)")
            
    except Exception as e:
        print(f"[FAIL] Affair path test error: {e}")

if __name__ == "__main__":
    USER_TDX_DIR = "/Volumes/SSDFull/stock/new_tdx"
    try:
        reader = Reader.factory(tdxdir=USER_TDX_DIR)
        print(f"=== Starting Comprehensive Offline API Test ===")
        test_industry_levels(reader)
        test_stock_industry_consistency(reader)
        test_affair_path()
        print("\n=== Test Finished ===")
    except Exception as e:
        print(f"FATAL: {e}")
