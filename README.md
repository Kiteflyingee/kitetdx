# Kitetdx

**Kitetdx** 是一个基于 [mootdx](https://github.com/mootdx/mootdx) 的二次封装与扩展项目。它提供了一套统一且稳定的 API 用于访问金融数据，内置了定制化的 `Reader` 模块，并对 `Quotes` 进行了完整的封装。


## 功能特性

- **定制化 Reader 模块**: 位于 `kitetdx.reader`，针对特定项目需求重写了数据读取逻辑（如概念板块解析），完全独立于 `mootdx` 的 reader 实现。
- **统一 API 接口**: 对 `Quotes` 等模块进行了显式封装，提供了完整的文档注释，确保用户代码与底层实现解耦。
- **可扩展架构**: 设计上允许未来替换底层实现（如从 `mootdx` 切换到 `tushare` 或自研协议），而无需修改用户侧代码。

## 安装指南

```bash
pip install kitetdx
```

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
concepts = reader.block()
for concept in concepts:
    print(f"概念: {concept.concept_name}, 股票数: {len(concept.stocks)}")
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
