import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kitetdx import Quotes

def main():
    print("-" * 30)
    print("初始化 Quotes (在线行情)...")
    client = Quotes.factory(market='std', multithread=True)

    # 1. 获取实时日K线
    symbol = '600036'
    print(f"\n[1] 获取 {symbol} 实时日K线 (最近10条):")
    try:
        df = client.bars(symbol=symbol, frequency=9, offset=10)
        print(df)
    except Exception as e:
        print(f"获取失败: {e}")

    # 2. 获取实时分时
    print(f"\n[2] 获取 {symbol} 实时分时数据:")
    try:
        df_min = client.minute(symbol=symbol)
        print(df_min)
    except Exception as e:
        print(f"获取失败: {e}")

    # 3. 获取 F10 信息
    print(f"\n[3] 获取 {symbol} F10 资料分类:")
    try:
        f10 = client.F10(symbol=symbol)
        if f10:
            print("可用分类:", list(f10.keys()))
            if '公司简介' in f10:
                print("\n公司简介摘要:")
                print(f10['公司简介'][:200] + "...")
    except Exception as e:
        print(f"获取失败: {e}")

if __name__ == "__main__":
    main()
