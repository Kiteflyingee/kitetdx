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

    # 2. 读取板块数据
    print("\n[3] 读取板块数据:")
    df_block = reader.block()
    print(f"共读取到 {len(df_block)} 条板块记录")
    
    if not df_block.empty:
        print("示例数据 (前5条):")
        print(df_block.head())
        
        # 筛选示例
        print("\n[4] 筛选 'GN' (概念) 板块:")
        df_gn = reader.block(concept_type='GN')
        print(f"共读取到 {len(df_gn)} 条概念板块记录")
        print(df_gn.head())

if __name__ == "__main__":
    main()
