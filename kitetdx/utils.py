import pandas as pd
from pandas import DataFrame
from mootdx.logger import logger


def to_data(v, first=True, **kwargs):
    """
    数值转换为 pd.DataFrame，优先使用 mootdx 的方法，失败时回退到自定义实现
    
    :param v: mixed
    :return: pd.DataFrame
    """
    # 优先尝试使用 mootdx 的 to_data
    if first:
        return _to_data_fallback(v, **kwargs)
    try:
        from mootdx.utils import to_data as mootdx_to_data
        return mootdx_to_data(v, **kwargs)
    except Exception as e:
        logger.warning(f"mootdx to_data 失败，使用自定义实现: {e}")
        return _to_data_fallback(v, **kwargs)


def _to_data_fallback(v, **kwargs):
    """
    自定义的数值转换方法（备用）
    
    :param v: mixed
    :return: pd.DataFrame
    """
    symbol = kwargs.get('symbol')
    adjust = kwargs.get('adjust', '')
    
    if adjust:
        adjust = adjust.lower()
        if adjust in ['01', 'qfq', 'before']:
            adjust = 'qfq'
        elif adjust in ['02', 'hfq', 'after']:
            adjust = 'hfq'
        else:
            adjust = None

    # 空值
    if not isinstance(v, DataFrame) and not v:
        return pd.DataFrame(data=None)

    # DataFrame
    if isinstance(v, DataFrame):
        result = v
    # 列表
    elif isinstance(v, list):
        result = pd.DataFrame(data=v) if len(v) else None
    # 字典
    elif isinstance(v, dict):
        result = pd.DataFrame(data=[v])
    # 空值
    else:
        result = pd.DataFrame(data=[])

    if 'datetime' in result.columns:
        result.index = pd.to_datetime(result.datetime)

    if 'date' in result.columns:
        result.index = pd.to_datetime(result.date)

    if 'vol' in result.columns:
        result['volume'] = result.vol

    # 使用自定义复权方法
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
