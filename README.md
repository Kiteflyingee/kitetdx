# Kitetdx

**Kitetdx** 是一个基于 [mootdx](https://github.com/mootdx/mootdx) 的二次封装与扩展项目。它提供了一套统一且稳定的 API 用于访问金融数据，**重点增强了离线读取 (Reader) 模块**，内置了深度定制化的逻辑，并对 `Quotes` 进行了完整的封装。


## 功能特性

- **定制化 Reader 模块**: 位于 `kitetdx.reader`，针对特定项目需求重写了数据读取逻辑（如概念板块解析），完全独立于 `mootdx` 的 reader 实现。
- **统一 API 接口**: 对 `Quotes` 等模块进行了显式封装，提供了完整的文档注释，确保用户代码与底层实现解耦。
- **可扩展架构**: 设计上允许未来替换底层实现（如从 `mootdx` 切换到 `tushare` 或自研协议），而无需修改用户侧代码。

## 安装指南

```bash
pip install kitetdx
```

## 目录结构与数据准备

为了获得最佳体验（特别是离线读取分时数据），建议按照以下说明配置通达信目录。

### 关键目录结构
只保留最常见且核心的目录结构：
```text
/path/to/tdx/
├── vipdoc/
│   ├── sh/
│   │   ├── lday/      # 上海证券交易所日线数据 (.day)
│   │   └── minline/   # 上海证券交易所分时数据 (.lc1, .lc5)
│   └── sz/
│       ├── lday/      # 深圳证券交易所日线数据 (.day)
│       └── minline/   # 深圳证券交易所分时数据 (.lc1, .lc5)
└── T0002/             # 个人配置与数据
```

> [!CAUTION]
> **关于通达信客户端的必要性说明**
>
> 1.  **安装通达信客户端**：虽然理论上只需要数据文件，但为了数据的完整性和更新便利，强烈建议安装 Windows 版通达信客户端。通常数据存放在C:/new_tdx目录下。（只需要日K、财务信息无需安装Windows通达信客户端）
> 2.  **日线 vs 分时**：如果不安装客户端，通常只能读取静态的日线数据。
> 3.  **获取离线分时数据**：
>     *   通达信客户端会自动缓存最近浏览股票的分时数据（通常保留 **最近 100 天**）。
>     *   你可以在客户端中浏览感兴趣的股票，然后 `kitetdx` 就可以直接从本地 `minline` 目录读取这些高频数据，无需频繁进行在线 API 请求，极大提高回测和分析效率。
> 4.  **板块与基础信息更新**：
>     *   股票名称、板块信息（概念、风格等）依赖于客户端的本地缓存文件（如 `T0002/hq_cache` 下的数据）。
>     *   **每日打开一次通达信客户端**（建议早上 9:00 后），软件会自动下载并更新最新的板块定义和股票名称映射。

## 使用说明

### 离线数据读取 (定制实现)

`kitetdx` 的 `Reader` 模块提供了增强的离线数据读取功能。

```python
from kitetdx import Reader

# 初始化 Reader，指定通达信安装目录
reader = Reader.factory(market='std', tdxdir='/path/to/tdx')

# 读取日线数据
df = reader.daily(symbol='600036')
print(df)

# 读取板块数据 (定制逻辑)

# 获取所有板块数据，默认返回 Block 对象列表
concepts = reader.block()

# Block 对象结构
# @dataclass
# class Block:
#     concept_name: str      # 板块名称
#     concept_code: str      # 板块代码
#     concept_type: str      # 板块类型 ('GN': 概念, 'FG': 风格, 'ZS': 指数)
#     stocks: List[dict]     # 包含股票信息的列表 [{'stock_code': '...', 'stock_name': '...'}, ...]

for concept in concepts:
    print(f"概念: {concept.concept_name} ({concept.concept_type}), 股票数: {len(concept.stocks)}")

# 高级用法：

# 1. 指定板块类型 (只获取 'GN' 概念板块)
gn_blocks = reader.block(concept_type='GN')

# 2. 返回 DataFrame 格式 (return_df=True)
# 直接返回包含所有板块数据的 DataFrame，方便进行批量分析
df = reader.block(return_df=True)
print(df.head())
# DataFrame 列包含: ID, concept_type, concept_name, concept_code, stock_code, stock_name

# 3. 获取行业板块信息 
# 注意：通达信的行业分类与申万(Shenwan)或证监会行业分类不同：

# - Level 0: 行业门类 (Sector) - 代码长度 3位 (如 T01 能源, T10 金融)
# - Level 1: 一级行业 (Industry) - 代码长度 5位 (如 T0101 煤炭, T1001 银行)
# - Level 2: 二级行业 (Sub-Industry) - 代码长度 7位 (如 T010101 煤炭开采)
#   (注: 并非所有一级行业都有二级细分，如银行 T1001 下就没有二级行业)

# 获取所有行业列表
industries = reader.get_industries()
print(industries) 
# 输出包含 columns: industry_name, industry_code (T代码), block_code (88xxxx), level_type

# 获取指定行业的成分股 (支持查询任意级别的行业)
# 例如查询 "银行" (T1001, 一级行业)
bank_stocks = reader.get_industry_stocks('银行') 
print(f"银行股数量: {len(bank_stocks)}")

# 或者查询 "白酒" (T030501, 二级行业)
liquor_stocks = reader.get_industry_stocks('白酒')
print(f"白酒股数量: {len(liquor_stocks)}")

# 获取指定股票的所属行业
stock_ind = reader.get_stock_industry('000001')
print(f"平安银行所属行业: {stock_ind['industry_name']} (代码: {stock_ind['industry_code']})")

# 自动向上回溯父行业，构建完整分类链
# Output example: 平安银行所属行业: 银行 (T1001) -> 父行业: TDX 金融 (T10)
if 'parent_industry_name_1' in stock_ind:
    print(f"父行业: {stock_ind['parent_industry_name_1']}")
```

### 在线行情 (封装 Mootdx)

`Quotes` 模块封装了 `mootdx.quotes`，提供了一致的 API。

```python
from kitetdx import Quotes

# 初始化行情客户端
client = Quotes.factory(market='std', multithread=True, heartbeat=True)

# 获取实时 K 线
df = client.bars(symbol='600036', frequency=9, offset=10)
print(df)

# 获取实时分时
df = client.minute(symbol='000001')
print(df)
```

## 文档

- [API 参考](docs/api.md)
- [使用指南](docs/guide.md)

## 致谢

本项目基于 [mootdx](https://github.com/mootdx/mootdx) 构建，感谢原作者的卓越工作。
