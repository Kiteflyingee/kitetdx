# API 参考手册

`kitetdx` 基于 `mootdx` 开发，提供了一套统一的金融数据获取接口。本手册详细说明了主要模块及其方法。

## 目录

- [Quotes (在线行情)](#quotes-在线行情)
  - [初始化](#quotes-初始化)
  - [K线数据](#quotes-k线数据)
  - [分时数据](#quotes-分时数据)
  - [分笔成交](#quotes-分笔成交)
  - [财务与除权](#quotes-财务与除权)
  - [市场列表](#quotes-市场列表)
- [Reader (离线读取)](#reader-离线读取)
  - [初始化](#reader-初始化)
  - [数据读取](#reader-数据读取)
  - [板块数据](#reader-板块数据)
- [Affair (财务文件)](#affair-财务文件)

---

## Quotes (在线行情)

用于连接通达信服务器，获取实时或历史行情数据。

> **注意**: 在线接口依赖于第三方服务器，连接稳定性可能有所波动。

### Quotes 初始化

#### `Quotes.factory(market='std', **kwargs)`

创建行情客户端实例。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `market` | str | `'std'` | 市场类型：`'std'` (标准市场), `'ext'` (扩展市场) |
| `multithread` | bool | `True` | 是否开启多线程 |
| `heartbeat` | bool | `True` | 是否开启心跳检测 |
| `bestip` | bool | `True` | 是否自动选择最优 IP |
| `timeout` | int | `15` | 连接超时时间 (秒) |

**返回**: `Quotes` 对象实例

---

### Quotes K线数据

#### `bars(symbol, frequency=9, start=0, offset=800, **kwargs)`

获取实时 K 线数据（包含指数）。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | `'000001'` | 股票代码 |
| `frequency` | int | `9` | K线周期代码 (见下方说明) |
| `start` | int | `0` | 起始位置 (0 为最新一条) |
| `offset` | int | `800` | 获取数量 (最大 800) |

> **Frequency 代码表**:
> - `0`: 5分钟
> - `1`: 15分钟
> - `2`: 30分钟
> - `3`: 1小时
> - `4`: 日线
> - `5`: 周线
> - `6`: 月线
> - `7`: 1分钟
> - `8`: 1分钟K线
> - `9`: 日线
> - `10`: 季线
> - `11`: 年线

**返回**: `pd.DataFrame`

#### `index_bars(symbol, frequency=9, start=0, offset=800, **kwargs)`

获取指数 K 线数据。参数与 `bars` 相同。

#### `k(symbol, begin=None, end=None, **kwargs)`

获取历史 K 线数据（按日期范围）。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `begin` | str | `None` | 开始日期 (如 `'20230101'`) |
| `end` | str | `None` | 结束日期 (如 `'20231231'`) |

**返回**: `pd.DataFrame`

#### `ohlc(**kwargs)`

`k` 方法的别名。

---

### Quotes 分时数据

#### `minute(symbol, **kwargs)`

获取实时分时图数据。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |

**返回**: `pd.DataFrame`

#### `minutes(symbol, date, **kwargs)`

获取历史分时数据。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `date` | str | `'20191023'` | 查询日期 (如 `'20230101'`) |

**返回**: `pd.DataFrame`

---

### Quotes 分笔成交

#### `transaction(symbol, start=0, offset=800, **kwargs)`

获取实时分笔成交。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `start` | int | `0` | 起始位置 |
| `offset` | int | `800` | 获取数量 |

**返回**: `pd.DataFrame`

#### `transactions(symbol, start=0, offset=800, date='20170209', **kwargs)`

获取历史分笔成交。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `start` | int | `0` | 起始位置 |
| `offset` | int | `800` | 获取数量 |
| `date` | str | `'20170209'` | 查询日期 |

**返回**: `pd.DataFrame`

---

### Quotes 财务与除权

#### `F10(symbol, name='')`

读取公司 F10 信息。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `name` | str | `''` | 栏目名称 (如 "最新提示", "公司概况"等) |

**返回**: `pd.DataFrame` 或 `dict`

#### `finance(symbol, **kwargs)`

读取财务信息。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | `'000001'` | 股票代码 |

**返回**: `pd.DataFrame`

#### `xdxr(symbol, **kwargs)`

读取除权除息信息。优先从新浪接口获取复权因子以提高准确性。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `method` | str | `'qfq'` | 复权方式: `'qfq'` (前复权), `'hfq'` (后复权) |

**返回**: `pd.DataFrame` (包含 `date`, `factor` 等列)

---

### Quotes 市场列表

#### `stock_count(market=MARKET_SH)`

获取市场股票数量。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `market` | int | `1` | 市场代码: `1` (沪), `0` (深), `2` (北) |

**返回**: `int`

#### `stocks(market=MARKET_SH)`

获取指定市场的股票列表。

**返回**: `pd.DataFrame`

#### `stock_all()`

获取所有市场的股票列表。

**返回**: `pd.DataFrame`

#### `block(tofile='block.dat', **kwargs)`

获取证券板块信息。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `tofile` | str | `'block.dat'` | 保存文件名 |

**返回**: `pd.DataFrame`

---

## Reader (离线读取)

用于直接读取本地通达信安装目录下的数据文件（`.day`, `.lc1`, `.lc5` 等）。

### Reader 初始化

#### `Reader.factory(market='std', **kwargs)`

创建 Reader 实例。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `market` | str | `'std'` | 市场类型 |
| `tdxdir` | str | `'C:/new_tdx'` | 通达信安装目录 (必须指定) |

**返回**: `Reader` 对象实例

---

### Reader 数据读取

#### `update_data()`

手动检查并更新本地数据。
- 检查本地 `lday` 目录时间戳。
- 如果数据过期（早于最近交易日）且当前未收盘，或者目录不存在，则通过 Selenium 下载最新数据。
- 建议在每日收盘后或首次使用前调用。

#### `daily(symbol, **kwargs)`

读取日线数据。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `adjust` | str | `None` | 复权方式: `'qfq'` (前复权), `'hfq'` (后复权) |

> **注意**: 该方法不再自动检查更新。如需获取最新数据，请先调用 `update_data()`。

**调用示例**:
```python
from kitetdx import Reader

reader = Reader.factory(tdxdir='C:/new_tdx')

# 读取原始数据
df = reader.daily('600036')

# 读取前复权数据
df_qfq = reader.daily('600036', adjust='qfq')

# 读取后复权数据
df_hfq = reader.daily('600036', adjust='hfq')
```

**返回**: `pd.DataFrame`

**列说明**:
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量 (手)
- `amount`: 成交额 (元)

**返回示例**:
```python
                     open   high    low  close     volume       amount
date
2023-11-20  10.20  10.35  10.15  10.30  123456.0  1.234560e+08
2023-11-21  10.30  10.40  10.25  10.38  110000.0  1.150000e+08
```

#### `minute(symbol, suffix=1, **kwargs)`

读取分钟线数据。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `suffix` | int | `1` | 周期: `1` (1分钟), `5` (5分钟) |

**调用示例**:
```python
# 读取1分钟线
df = reader.minute('600036', suffix=1)
# 读取5分钟线
df_5 = reader.minute('600036', suffix=5)
```

**返回**: `pd.DataFrame`

**列说明**:
- `open`, `high`, `low`, `close`
- `vol`: 成交量
- `amount`: 成交额

**返回示例**:
```python
                       open   high    low  close      vol      amount
datetime
2023-11-21 09:30:00  10.30  10.32  10.29  10.31  1000.00  1031000.0
2023-11-21 09:31:00  10.31  10.33  10.30  10.32   800.00   825600.0
```

#### `fzline(symbol)`

读取 5 分钟线数据。(`minute(suffix=5)` 的别名)

#### `xdxr(symbol, **kwargs)`

读取除权除息信息（调用在线接口辅助）。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `symbol` | str | - | 股票代码 |
| `method` | str | `'qfq'` | 复权方式 (用于缓存文件名) |

**调用示例**:
```python
df = reader.xdxr('600036')
```

**返回**: `pd.DataFrame`

**列说明**:
- `date`: 除权日期 (Index)
- `factor`: 复权因子

**返回示例**:
```python
            factor
date
2022-05-20   1.05
2023-06-15   1.12
```

---

### Reader 板块数据

#### `block(concept_type=None)`

读取通达信本地板块与概念数据。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `concept_type` | str | `None` | 筛选类型: `'GN'` (概念), `'FG'` (风格), `'ZS'` (指数) |

**调用示例**:
```python
# 读取所有概念
blocks = reader.block(concept_type='GN')
# 筛选出锂电池板块的股票
lithium_stocks = blocks[blocks['concept_name'] == '锂电池']
```

**返回**: `pd.DataFrame`

**列说明**:
- `ID`: 序号
- `concept_type`: 类型
- `concept_name`: 板块名称
- `concept_code`: 板块代码
- `stock_code`: 股票代码
- `stock_name`: 股票名称

**返回示例**:
```python
   ID concept_type concept_name concept_code stock_code stock_name
0   1           GN         锂电池       880534     300750      宁德时代
1   2           GN         锂电池       880534     002594      比亚迪
2   3           FG         高价股       880801     600519      贵州茅台
```


---

### Reader 行业数据

#### `get_industries(source='tdx')`

获取通达信行业分类列表。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `source` | str | `'tdx'` | 数据源 (目前仅支持 'tdx') |

**返回**: `pd.DataFrame`

**列说明**:
- `industry_name`: 行业名称
- `industry_code`: 行业代码 (T开头)
- `block_code`: 板块代码 (88xxxx)
- `level_type`: 级别 (2=二级行业)

#### `get_industry_stocks(industry_code, source='tdx')`

获取指定行业的成分股列表。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `industry_code` | str | - | 行业代码 (Txxxx)、板块代码 (88xxxx) 或行业名称 |
| `source` | str | `'tdx'` | 数据源 |

**返回**: `list[str]` (股票代码列表)

#### `get_stock_industry(stock_code, source='tdx')`

获取股票所属行业信息。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `stock_code` | str | - | 股票代码 |
| `source` | str | `'tdx'` | 数据源 |

**返回**: `dict` (包含 industry_code, industry_name, parent_industry_name_x 等)

---

## Affair (财务文件)

用于下载和解析通达信专业财务数据文件，包含上市公司季报、中报、年报等财务指标。

### 文件命名规则

| 文件名格式 | 说明 |
| :--- | :--- |
| `gpcw20231231.zip` | 2023年年报 (12月31日) |
| `gpcw20230930.zip` | 2023年三季报 (9月30日) |
| `gpcw20230630.zip` | 2023年中报 (6月30日) |
| `gpcw20230331.zip` | 2023年一季报 (3月31日) |

---

#### `files()`

获取远程财务文件列表。

**调用示例**:
```python
from kitetdx import Affair

# 获取可用的财务文件列表
files = Affair.files()
print(files[:3])
# [{'filename': 'gpcw20231231.zip', 'hash': '...', 'filesize': 5648421}, ...]
```

**返回**: `list[dict]` - 包含 `filename`, `hash`, `filesize` 字段

---

#### `fetch(downdir='tmp', filename='')`

下载财务文件。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `downdir` | str | `'tmp'` | 本地下载目录 (不存在会自动创建) |
| `filename` | str | `''` | 指定文件名 (留空则下载所有文件) |

**调用示例**:
```python
# 下载2023年年报数据
Affair.fetch(downdir='财务数据', filename='gpcw20231231.zip')
```

**返回**: `bool`

---

#### `parse(downdir='tmp', filename='')`

解析本地财务文件。如果文件不存在，会自动调用 `fetch()` 下载。

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `downdir` | str | `'tmp'` | 文件所在目录 |
| `filename` | str | - | 文件名 (**必填**) |

**调用示例**:
```python
# 解析2023年年报
df = Affair.parse(downdir='财务数据', filename='gpcw20231231.zip')
print(df.head())
```

**返回**: `pd.DataFrame`

**主要列说明** (共 585 列):

| 列名 | 说明 |
| :--- | :--- |
| `code` | 股票代码 (Index) |
| `report_date` | 报告日期 |
| `基本每股收益` | 基本每股收益 (元) |
| `扣除非经常性损益每股收益` | 扣非每股收益 (元) |
| `每股净资产` | 每股净资产 (元) |
| `净资产收益率` | ROE (%) |
| ... | 更多财务指标 |

**返回示例**:
```python
        report_date  基本每股收益  扣除非经常性损益每股收益  ...
code                                              
000001     20231231     2.25              2.25  ...
000002     20231231     1.03              0.83  ...
600036     20231231     5.28              5.12  ...
```

