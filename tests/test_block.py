import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kitetdx import Reader

# 初始化 Reader，指定通达信安装目录
reader = Reader.factory(market='std', tdxdir='/Volumes/SSDFull/stock/new_tdx')

# 读取日线数据
df = reader.daily(symbol='600036')
print(df)

# 读取板块数据 (定制逻辑)
concepts = reader.block(concept_type='GN')
for concept in concepts:
    print(f"概念: {concept.concept_name}, 股票数: {len(concept.stocks)}")