from kitetdx import Reader
import pandas as pd

def test_sws_via_reader():
    print("=== 正在通过 Reader 初始化申万行业测试 ===")
    
    # 1. 初始化 Reader
    reader = Reader.factory()
    
    print("\n--- 1. 获取申万一级行业列表 ---")
    l1_industries = reader.get_industries(source='sws', level=1)
    if not l1_industries.empty:
        print(f"找到 {len(l1_industries)} 个一级行业")
        print(l1_industries.head())
    else:
        print("未获取到一级行业数据")

    print("\n--- 2. 获取申万二级行业列表 ---")
    l2_industries = reader.get_industries(source='sws', level=2)
    if not l2_industries.empty:
        print(f"找到 {len(l2_industries)} 个二级行业")
        print(l2_industries.head())
    else:
        print("未获取到二级行业数据")

    # 3. 获取特定行业的成分股 (以 '银行' 为例)
    target_industry = '银行'
    print(f"\n--- 3. 获取 '{target_industry}' 行业的成分股 ---")
    stocks = reader.get_industry_stocks(target_industry, source='sws')
    print(f"'{target_industry}' 行业下共有 {len(stocks)} 只股票")
    if stocks:
        print(f"前 5 只股票代码: {stocks[:5]}")

    # 4. 查询特定股票的所属行业 (以 '600036' 招商银行为例)
    stock_code = '600036'
    print(f"\n--- 4. 查询股票 {stock_code} 的申万行业归属 ---")
    info = reader.get_stock_industry(stock_code, source='sws')
    if info:
        print(f"股票: {info.get('stock_name')} ({info.get('stock_code')})")
        print(f"一级行业: {info.get('l1_name')} ({info.get('l1_code')})")
        print(f"二级行业: {info.get('l2_name')} ({info.get('l2_code')})")
    else:
        print(f"未找到股票 {stock_code} 的行业信息")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_sws_via_reader()
