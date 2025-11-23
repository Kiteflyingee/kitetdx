import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kitetdx import Reader

def main():
    # 请修改为您的通达信安装路径
    tdx_dir = '/Volumes/SSDFull/stock/new_tdx'
    
    if not os.path.exists(tdx_dir):
        print(f"警告: 路径 {tdx_dir} 不存在，请修改脚本中的 tdx_dir 变量")
        return

    print("-" * 30)
    print("初始化 Reader...")
    reader = Reader.factory(market='std', tdxdir=tdx_dir)

    # 1. 读取日线数据
    symbol = '600036'
    print(f"\n[1] 读取 {symbol} 日线数据 (前5条):")
    df = reader.daily(symbol)
    if df is not None and not df.empty:
        print(df.head())
    else:
        print("未找到数据")

    # 2. 读取5分钟线
    print(f"\n[2] 读取 {symbol} 5分钟线数据 (前5条):")
    df_min = reader.minute(symbol, suffix=5)
    if df_min is not None and not df_min.empty:
        print(df_min.head())
    else:
        print("未找到数据")

    # 3. 读取板块数据
    print("\n[3] 读取板块数据:")
    concepts = reader.block()
    print(f"共读取到 {len(concepts)} 个板块概念")
    
    if concepts:
        c = concepts[0]
        print(f"示例板块: {c.concept_name} ({c.concept_code})")
        print(f"包含股票数量: {len(c.stocks)}")
        if c.stocks:
            print(f"首只股票: {c.stocks[0].stock_name} ({c.stocks[0].stock_code})")

if __name__ == "__main__":
    main()
