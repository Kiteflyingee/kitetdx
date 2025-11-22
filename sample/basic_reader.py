from mootdx.reader import Reader

# 初始化通达信文件读取类
reader = Reader.factory(market="std", tdxdir="/Volumes/SSDFull/stock/new_tdx")  # 标准市场

# 读取日数据
daily = reader.daily(symbol="600000")

print(daily)

concept = reader.block()
print(concept)
