# 使用指南

## 离线数据分析

使用 `Reader` 模块可以无需联网直接读取本地通达信数据。这是 `kitetdx` 的核心增强模块。

### 读取行情数据

```python
from kitetdx import Reader

# 初始化，指向你的通达信安装目录
reader = Reader.factory(market='std', tdxdir='/Volumes/SSDFull/stock/new_tdx')

# 读取平安银行日线
df = reader.daily('600036')
print(df.head())

# 读取分钟线
df_min = reader.minute('600036', suffix=5) # 5分钟线
```

### 读取板块数据 (增强)

`kitetdx` 提供了更强大的板块解析功能，直接返回实体对象。

```python
concepts = reader.block()
for concept in concepts:
    print(f"板块: {concept.concept_name} ({concept.concept_code})")
    print(f"包含股票数: {len(concept.stocks)}")
    # 打印前5只股票
    for stock in concept.stocks[:5]:
        print(f"  - {stock.stock_name} ({stock.stock_code})")
```

## 在线行情获取

使用 `Quotes` 模块获取实时数据。

### 实时 K 线与分时

```python
from kitetdx import Quotes

client = Quotes.factory(market='std')

# 获取日线
df = client.bars('600036')

# 获取分时
df_time = client.minute('600036')
```

### 查询 F10 资料

```python
# 获取所有 F10 分类
f10_data = client.F10('600036')
print(f10_data.keys())

# 获取特定分类
desc = client.F10('600036', name='公司简介')
print(desc)
```

## 财务数据处理

使用 `Affair` 模块下载和解析专业财务数据。

### 下载数据

```python
from kitetdx import Affair

# 获取文件列表
files = Affair.files()
print(f"可用文件: {files[:5]}...")

# 下载最新的财务文件
Affair.fetch(downdir='data', filename=files[-1]['filename'])
```

### 解析数据

```python
# 解析下载的文件
df = Affair.parse(downdir='data', filename=files[-1]['filename'])
print(df.head())
```
