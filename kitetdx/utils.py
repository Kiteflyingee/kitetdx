import logging
import pandas as pd
from pandas import DataFrame


logger = logging.getLogger(__name__)


def to_data(v, **kwargs):
    """
    数值转换为 pd.DataFrame，并支持复权处理
    
    :param v: 输入数据，支持 DataFrame、list、dict
    :param symbol: 股票代码（复权时需要）
    :param adjust: 复权方式，'qfq'/'01' 前复权，'hfq'/'02' 后复权
    :return: pd.DataFrame
    """
    symbol = kwargs.get('symbol')
    adjust = kwargs.get('adjust', '')
    
    # 标准化复权参数
    if adjust:
        adjust = adjust.lower()
        if adjust in ['01', 'qfq', 'before']:
            adjust = 'qfq'
        elif adjust in ['02', 'hfq', 'after']:
            adjust = 'hfq'
        else:
            adjust = None

    # 空值处理
    if not isinstance(v, DataFrame) and not v:
        return pd.DataFrame(data=None)

    # 转换为 DataFrame
    if isinstance(v, DataFrame):
        result = v
    elif isinstance(v, list):
        result = pd.DataFrame(data=v) if len(v) else pd.DataFrame()
    elif isinstance(v, dict):
        result = pd.DataFrame(data=[v])
    else:
        result = pd.DataFrame(data=[])

    # 设置日期索引
    if 'datetime' in result.columns:
        result.index = pd.to_datetime(result.datetime)

    if 'date' in result.columns:
        result.index = pd.to_datetime(result.date)

    # 统一成交量列名
    if 'vol' in result.columns:
        result['volume'] = result.vol

    # 复权处理
    if adjust and adjust in ['qfq', 'hfq'] and symbol:
        from kitetdx.adjust import to_adjust
        result = to_adjust(result, symbol=symbol, adjust=adjust)

    return result


def read_data(file_path):
    """
    读取文件内容
    """
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            return f.read().strip().split('\n')
    except FileNotFoundError:
        logger.error(f"错误: 文件 {file_path} 不存在")
        return None
    except Exception as e:
        logger.error(f"读取文件时出错: {e}")
        return None
