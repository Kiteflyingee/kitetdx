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
```
返回Dataframe
```
          ID concept_type concept_name concept_code stock_code stock_name
0          1           GN        通达信88       880515     000025        特力Ａ
1          2           GN        通达信88       880515     000100      TCL科技
2          3           GN        通达信88       880515     000538       云南白药
3          4           GN        通达信88       880515     000708       中信特钢
4          5           GN        通达信88       880515     000725       京东方Ａ
```

## 行业板块信息

`kitetdx` 提供了统一的接口来获取通达信 (TDX) 和申万 (SWS) 的行业分类数据。

### 通达信行业 (TDX)

使用 `Reader` 模块获取本地通达信的行业分类。

```python
from kitetdx import Reader

reader = Reader.factory()

# 1. 获取行业列表 (Level 1: 一级行业, Level 2: 二级行业)
industries = reader.get_industries(source='tdx', level=1)
print(industries.head())
#   industry_name industry_code  level_type block_code
# 0            煤炭         T1001           1     880301

# 2. 获取行业成分股
stocks = reader.get_industry_stocks('T1001') # 使用行业代码
# 或者
stocks = reader.get_industry_stocks('煤炭')  # 使用行业名称

# 3. 查询个股所属行业
info = reader.get_stock_industry('600036')
print(info)
# {'industry': '银行', 'industry_code': 'T1002', 'sub_industry': '股份制银行'}
```

### 申万行业 (SWS)

使用 `SwsReader` (或通用接口) 获取申万行业分类。

```python
from kitetdx import SwsReader

sws = SwsReader(auto_download=True)

# 1. 获取行业列表
l1_industries = sws.get_industries(level=1)
print(l1_industries[:5]) # ['农林牧渔', '基础化工', ...]

# 2. 获取行业成分股
stocks = sws.get_industry_stocks('银行')

# 3. 查询个股所属行业
info = sws.get_stock_industry('600036')
print(info)
# {'industry': '银行', 'industry_code': '480000', 'sub_industry': '股份制银行'}
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
