# @Author  : kitetdx
# @Time    : 2024
# @Function: 复权因子获取和复权计算

import json
import datetime
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import urllib.request

from mootdx.logger import logger


# 新浪复权因子接口
ZH_SINA_HFQ_URL = 'https://finance.sina.com.cn/realstock/company/{}/hfq.js'
ZH_SINA_QFQ_URL = 'https://finance.sina.com.cn/realstock/company/{}/qfq.js'

# 缓存目录和过期时间（一周 = 7天）
CACHE_DIR = Path.home() / '.kitetdx' / 'fq_cache'
CACHE_EXPIRE_DAYS = 7


def _get_sina_symbol(symbol: str) -> str:
    """
    将股票代码转换为新浪格式
    
    Args:
        symbol: 股票代码，如 '000001' 或 '600000'
        
    Returns:
        新浪格式的股票代码，如 'sz000001' 或 'sh600000'
    """
    symbol = str(symbol).strip()
    
    # 如果已经有前缀，直接返回
    if symbol.startswith(('sh', 'sz', 'SH', 'SZ')):
        return symbol.lower()
    
    # 根据股票代码判断市场
    if symbol.startswith(('6', '9', '5')):
        return f'sh{symbol}'
    else:
        return f'sz{symbol}'


def _get_cache_path(symbol: str, method: str) -> Path:
    """获取缓存文件路径"""
    sina_symbol = _get_sina_symbol(symbol)
    return CACHE_DIR / f'{sina_symbol}_{method}.json'


def _is_cache_valid(cache_path: Path) -> bool:
    """检查缓存是否有效（一周内）"""
    if not cache_path.exists():
        return False
    
    try:
        mtime = cache_path.stat().st_mtime
        cache_age_days = (time.time() - mtime) / (24 * 3600)
        return cache_age_days < CACHE_EXPIRE_DAYS
    except Exception:
        return False


def _load_cache(cache_path: Path) -> Optional[pd.DataFrame]:
    """从缓存加载复权因子"""
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data.get('data'):
            return None
        
        df = pd.DataFrame(data['data'])
        df.columns = ['date', 'factor']
        df['date'] = pd.to_datetime(df['date'])
        df['factor'] = df['factor'].astype(float)
        df = df.set_index('date')
        return df
    except Exception as e:
        logger.warning(f"加载缓存失败: {e}")
        return None


def _save_cache(cache_path: Path, data: list):
    """保存复权因子到缓存"""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({'data': data, 'update_time': time.time()}, f)
    except Exception as e:
        logger.warning(f"保存缓存失败: {e}")


def fetch_fq_factor(symbol: str, method: str = 'qfq', timeout: int = 10) -> Optional[pd.DataFrame]:
    """
    从新浪获取复权因子（带缓存，一周内不重复请求）
    
    Args:
        symbol: 股票代码
        method: 复权方式，'qfq' 前复权，'hfq' 后复权
        timeout: 请求超时时间（秒）
        
    Returns:
        复权因子DataFrame，包含 date 和 factor 列
    """
    # 检查缓存
    cache_path = _get_cache_path(symbol, method)
    if _is_cache_valid(cache_path):
        logger.debug(f"使用缓存的复权因子: {symbol} {method}")
        cached_df = _load_cache(cache_path)
        if cached_df is not None:
            return cached_df
    
    # 缓存无效，从网络获取
    sina_symbol = _get_sina_symbol(symbol)
    
    if method == 'hfq':
        url = ZH_SINA_HFQ_URL.format(sina_symbol)
    else:
        url = ZH_SINA_QFQ_URL.format(sina_symbol)
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode('utf-8')
        
        # 解析返回的JS格式数据
        # 格式: var _sh600000qfq={"total":30,"data":[...]};\n/* 注释 */
        json_str = text.split('=')[1].strip()
        
        # 去掉末尾的分号
        if json_str.endswith(';'):
            json_str = json_str[:-1]
        
        # 去掉末尾的JS注释 /* ... */
        if '/*' in json_str:
            json_str = json_str[:json_str.index('/*')].strip()
        
        # 去掉可能的换行符
        json_str = json_str.strip()
        
        data = json.loads(json_str)
        
        if not data.get('data'):
            logger.warning(f"获取 {symbol} {method} 复权因子为空")
            return None
        
        # 保存到缓存
        _save_cache(cache_path, data['data'])
        logger.debug(f"已缓存复权因子: {symbol} {method}")
        
        df = pd.DataFrame(data['data'])
        df.columns = ['date', 'factor']
        df['date'] = pd.to_datetime(df['date'])
        df['factor'] = df['factor'].astype(float)
        df = df.set_index('date')
        
        return df
        
    except Exception as e:
        logger.error(f"获取 {symbol} {method} 复权因子失败: {e}")
        # 网络失败时尝试使用过期缓存
        if cache_path.exists():
            logger.info(f"网络失败，尝试使用过期缓存: {symbol}")
            return _load_cache(cache_path)
        return None



def adjust_price(df: pd.DataFrame, symbol: str, method: str = 'qfq') -> pd.DataFrame:
    """
    对股票数据进行复权处理
    
    Args:
        df: 原始股票数据，需要包含 date, open, high, low, close 列
        symbol: 股票代码
        method: 复权方式，'qfq' 前复权，'hfq' 后复权，None 或其他值不复权
        
    Returns:
        复权后的DataFrame
    """
    if method not in ('qfq', 'hfq'):
        return df
    
    if df is None or df.empty:
        return df
    
    # 获取复权因子
    factor_df = fetch_fq_factor(symbol, method)
    
    if factor_df is None or factor_df.empty:
        logger.warning(f"无法获取 {symbol} 的复权因子，返回原始数据")
        return df
    
    # 确保df有date索引
    df_copy = df.copy()
    
    # 检查是否需要设置date索引
    if 'date' in df_copy.columns and not isinstance(df_copy.index, pd.DatetimeIndex):
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        df_copy = df_copy.set_index('date')
    elif isinstance(df_copy.index, pd.DatetimeIndex):
        pass
    else:
        # 尝试从year, month, day列构建date
        if all(col in df_copy.columns for col in ['year', 'month', 'day']):
            df_copy['date'] = pd.to_datetime(df_copy[['year', 'month', 'day']])
            df_copy = df_copy.set_index('date')
        else:
            logger.warning("数据中没有日期信息，无法进行复权")
            return df
    
    # 合并复权因子
    df_copy = df_copy.sort_index()
    factor_df = factor_df.sort_index()
    
    # 只取数据范围内的因子
    start_date = df_copy.index.min()
    end_date = df_copy.index.max()
    
    df_merged = pd.merge(
        df_copy, 
        factor_df, 
        left_index=True, 
        right_index=True, 
        how='left'
    )
    
    # 填充缺失的因子
    if method == 'qfq':
        # 前复权：向后填充
        df_merged['factor'] = df_merged['factor'].bfill()
    else:
        # 后复权：向前填充
        df_merged['factor'] = df_merged['factor'].ffill()
    
    # 如果还有缺失，填充为1
    df_merged['factor'] = df_merged['factor'].fillna(1.0)
    
    # 应用复权因子
    price_cols = ['open', 'high', 'low', 'close']
    
    for col in price_cols:
        if col in df_merged.columns:
            if method == 'hfq':
                # 后复权：价格 * 因子
                df_merged[col] = df_merged[col] * df_merged['factor']
            else:
                # 前复权：价格 / 因子
                df_merged[col] = df_merged[col] / df_merged['factor']
    
    # 删除因子列
    df_merged = df_merged.drop('factor', axis=1)
    
    return df_merged


def to_adjust(df: pd.DataFrame, symbol: str, adjust: str = None) -> pd.DataFrame:
    """
    复权接口（兼容mootdx的接口）
    
    Args:
        df: 原始股票数据
        symbol: 股票代码
        adjust: 复权方式，'qfq'/'01' 前复权，'hfq'/'02' 后复权
        
    Returns:
        复权后的DataFrame
    """
    if adjust is None:
        return df
    
    # 兼容mootdx的参数格式
    if adjust in ('01', 'qfq'):
        method = 'qfq'
    elif adjust in ('02', 'hfq'):
        method = 'hfq'
    else:
        return df
    
    return adjust_price(df, symbol, method)
