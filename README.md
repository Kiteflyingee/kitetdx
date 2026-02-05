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
> 1.  **安装通达信客户端**：虽然理论上只需要数据文件，但为了数据的完整性和更新便利，强烈建议安装 Windows 版通达信客户端。通常数据存放在C:/new_tdx目录下。
> 2.  **日线 vs 分时**：如果不安装客户端，通常只能读取静态的日线数据。
> 3.  **获取离线分时数据**：
>     *   通达信客户端会自动缓存最近浏览股票的分时数据（通常保留 **最近 100 天**）。
>     *   你可以在客户端中浏览感兴趣的股票，然后 `kitetdx` 就可以直接从本地 `minline` 目录读取这些高频数据，无需频繁进行在线 API 请求，极大提高回测和分析效率。

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
