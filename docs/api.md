# API 参考

## Quotes (在线行情)

`kitetdx.Quotes` 封装了 `mootdx` 的行情接口，提供实时和历史行情数据。

### 工厂方法

```python
Quotes.factory(market='std', **kwargs)
```
- `market`: 'std' (标准市场), 'ext' (扩展市场)
- `multithread`: 是否开启多线程 (默认 True)
- `heartbeat`: 是否开启心跳检测 (默认 True)
- `bestip`: 是否自动选择最优 IP (默认 True)
- `timeout`: 超时时间 (默认 15s)

### 方法列表

#### `bars(symbol, frequency=9, start=0, offset=800)`
获取实时日K线数据。
- `symbol`: 股票代码 (str)
- `frequency`: 数据频次 (9=日线, 0=5分钟, 1=15分钟, 2=30分钟, 3=1小时, 4=日线, 5=周线, 6=月线, 7=1分钟, 8=1分钟K线, 10=季线, 11=年线)
- `start`: 开始位置 (int)
- `offset`: 每次获取条数 (int)
- **返回**: `pd.DataFrame`

#### `index_bars(symbol, frequency=9, start=0, offset=800)`
获取指数K线数据。参数同 `bars`。

#### `minute(symbol)`
获取实时分时数据。
- `symbol`: 股票代码
- **返回**: `pd.DataFrame`

#### `minutes(symbol, date)`
获取历史分时数据。
- `symbol`: 股票代码
- `date`: 日期 (str, e.g., '20191023')
- **返回**: `pd.DataFrame`

#### `transaction(symbol, start, offset)`
查询分笔成交。
- `symbol`: 股票代码
- `start`: 起始位置
- `offset`: 结束位置
- **返回**: `pd.DataFrame`

#### `transactions(symbol, start, offset, date)`
查询历史分笔成交。
- `date`: 日期 (str, e.g., '20170209')

#### `F10(symbol, name)`
读取公司 F10 信息。
- `symbol`: 股票代码
- `name`: 栏目名称 (可选)
- **返回**: `pd.DataFrame` 或 `dict`

#### `finance(symbol)`
读取财务信息。
- `symbol`: 股票代码
- **返回**: `pd.DataFrame`

#### `xdxr(symbol)`
读取除权除息信息。
- `symbol`: 股票代码
- **返回**: `pd.DataFrame`

#### `k(symbol, begin=None, end=None)`
读取K线信息。
- `symbol`: 股票代码 (str)
- `begin`: 开始日期 (str, 可选, e.g., '20230101')
- `end`: 截止日期 (str, 可选, e.g., '20231231')
- **返回**: `pd.DataFrame` 或 `None`

#### `ohlc(**kwargs)`
读取K线信息 (k 方法的别名)。
- 参数同 `k` 方法
- **返回**: `pd.DataFrame` 或 `None`

#### `stock_count(market=MARKET_SH)`
获取市场股票数量。
- `market`: 股票市场代码 (`MARKET_SH` = 上海, `MARKET_SZ` = 深圳)
- **返回**: `int`

#### `stocks(market=MARKET_SH)`
获取股票列表。
- `market`: 股票市场代码 (`MARKET_SH` = 上海, `MARKET_SZ` = 深圳)
- **返回**: `pd.DataFrame`

#### `stock_all()`
获取所有股票列表（包含沪深两市）。
- **返回**: `pd.DataFrame`

#### `block(tofile='block.dat')`
获取证券板块信息 (在线)。
- `tofile`: 保存文件名

## Reader (离线读取)

`kitetdx.Reader` 提供了读取本地通达信数据的功能，特别增强了板块数据的解析。

### 工厂方法

```python
Reader.factory(market='std', tdxdir='C:/new_tdx')
```
- `tdxdir`: 通达信安装目录

### 方法列表

#### `daily(symbol)`
读取日线数据。
- `symbol`: 股票代码
- **返回**: `pd.DataFrame`

#### `minute(symbol, suffix=1)`
读取分钟线数据。
- `symbol`: 股票代码
- `suffix`: 1 (1分钟) 或 5 (5分钟)

#### `fzline(symbol)`
读取5分钟线数据 (Alias for minute(suffix=5))。

#### `block(concept_type=None)`
读取板块数据。
- `concept_type`: 可选，筛选板块类型 ('GN', 'FG', 'ZS')
- **返回**: `pd.DataFrame`
- **列名**: `ID`, `concept_type`, `concept_name`, `concept_code`, `stock_code`, `stock_name`


## Affair (财务数据)

`kitetdx.Affair` 提供了财务数据的下载和解析功能。

### 方法列表

#### `files()`
获取远程财务文件列表。
- **返回**: `list`

#### `fetch(downdir='tmp', filename='')`
下载财务文件。
- `downdir`: 下载目录
- `filename`: 指定文件名 (可选)
- **返回**: `bool`

#### `parse(downdir='tmp', filename='')`
解析本地财务文件。
- `downdir`: 文件所在目录
- `filename`: 指定文件名 (可选)
- **返回**: `pd.DataFrame`
