# Kitetdx 文档

欢迎使用 Kitetdx 文档。Kitetdx 是一个基于 mootdx 的二次封装项目，旨在提供更稳定、统一的金融数据访问接口。

## 核心模块

- **[API 参考](api.md)**: 详细的 API 文档，包括 `Reader` 和 `Quotes`。
- **[使用指南](guide.md)**: 常见使用场景和示例代码。

## 快速开始

```python
from kitetdx import Reader

reader = Reader.factory(tdxdir='C:/new_tdx')
# 如果没有安装客户端可以手动更新数据
reader.update_data()
# 读取股票日线数据
print(reader.daily(symbol='600036'))
```
