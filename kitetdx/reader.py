from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import datetime  

import pandas as pd
from tdxpy.reader import TdxExHqDailyBarReader, TdxFileNotFoundException
from tdxpy.reader import TdxLCMinBarReader
from tdxpy.reader import TdxMinBarReader

from mootdx.contrib.compat import MooTdxDailyBarReader
from mootdx.utils import get_stock_market
from mootdx.logger import logger
from kitetdx.utils import read_data, to_data
from kitetdx.downloader import TdxSeleniumDownloader
import os

def get_default_tdx_dir():
    """
    获取默认的通达信数据目录
    优先级: 
    1. C:/new_tdx (如果存在，提示检测到 Windows 客户端)
    2. ~/.kitetdx/tdx (默认内部路径)
    """
    win_path = 'C:/new_tdx'
    if os.path.exists(win_path):
        print(f"[Reader] 检测到已安装 Windows 通达信客户端: {win_path}")
        return win_path

    return os.path.join(os.path.expanduser('~'), '.kitetdx', 'tdx')


def get_last_trading_day(date=None):
    """
    获取最近的交易日
    
    Args:
        date: 指定日期，默认为今天
        
    Returns:
        最近的交易日
    """
    if date is None:
        date = datetime.date.today()
    
    # 中国股市交易日：周一到周五，排除法定节假日
    # 这里先简单处理周末，不考虑节假日
    while date.weekday() >= 5:  # 周六(5)和周日(6)
        date -= datetime.timedelta(days=1)
    
    return date


def is_trading_day(date):
    """
    判断是否为交易日（简单版本，只判断周末）
    
    Args:
        date: 要判断的日期
        
    Returns:
        bool: 是否为交易日
    """
    return date.weekday() < 5  # 周一到周五


def is_after_market_close():
    """
    判断当前是否已收盘（15:00之后）
    
    Returns:
        bool: 是否已收盘
    """
    now = datetime.datetime.now()
    market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return now >= market_close



class Reader(object):
    @staticmethod
    def factory(market='std', **kwargs):
        """
        Reader 工厂方法

        :param market: std 标准市场, ext 扩展市场
        :param kwargs: 可变参数
        :return:
        """

        if market == 'ext':
            return ExtReader(**kwargs)

        # 优先从 kwargs 获取 tdxdir，没有则读环境变量，最后取默认值
        tdxdir = kwargs.get('tdxdir') or os.environ.get('TDXDIR') or get_default_tdx_dir()
        kwargs['tdxdir'] = tdxdir
        
        return StdReader(**kwargs)


@dataclass
class Block:
    concept_name: str
    concept_code: str
    concept_type: str
    stocks: List[dict]



class ReaderBase(ABC):
    # 默认通达信安装目录
    tdxdir = get_default_tdx_dir()
    _sws_reader = None

    @property
    def sws_reader(self):
        """Lazy-loaded SwsReader instance"""
        if self._sws_reader is None:
            from .sws import SwsReader
            self._sws_reader = SwsReader()
        return self._sws_reader

    def __init__(self, tdxdir=None):
        """
        构造函数

        :param tdxdir: 通达信安装目录
        """

        if not Path(tdxdir).exists():
            Path(tdxdir).mkdir(parents=True, exist_ok=True)

        self.tdxdir = tdxdir

    def find_path(self, symbol=None, subdir='lday', suffix=None, **kwargs):
        """
        自动匹配文件路径，辅助函数

        :param symbol:
        :param subdir:
        :param suffix:
        :return: pd.dataFrame or None
        """

        # 判断市场, 带#扩展市场
        if '#' in symbol:
            market = 'ds'
        # 通达信特有的板块指数88****开头的日线数据放在 sh 文件夹下
        elif symbol.startswith('88'):
            market = 'sh'
        else:
            # 判断是sh还是sz
            market = get_stock_market(symbol, True)

        # 判断前缀(市场是sh和sz重置前缀)
        if market.lower() in ['sh', 'sz', 'bj']:
            symbol = market + symbol.lower().replace(market, '')

        # 判断后缀
        suffix = suffix if isinstance(suffix, list) else [suffix]

        # 调试使用
        if kwargs.get('debug'):
            return market, symbol, suffix

        # 遍历扩展名
        for ex_ in suffix:
            ex_ = ex_.strip('.')
            vipdoc = Path(self.tdxdir) / 'vipdoc' / market / subdir / f'{symbol}.{ex_}'

            if Path(vipdoc).exists():
                return vipdoc

        return None


class StdReader(ReaderBase):
    """股票市场"""

    def update_data(self):
        """
        手动检查并更新数据
        """
        # 检查 lday 目录的更新时间
        need_download = False
        lday_dir = Path(self.tdxdir) / 'vipdoc' / 'sh' / 'lday'
        
        if lday_dir.exists():
            try:
                mtime = lday_dir.stat().st_mtime
                dir_date = datetime.date.fromtimestamp(mtime)
                today = datetime.date.today()
                
                # 获取最近的交易日
                last_trading_day = get_last_trading_day(today)
                
                # 定义必须满足的目标日期
                if is_trading_day(today) and not is_after_market_close():
                    # 如果是交易日且未收盘，我们需要至少有上个交易日的数据
                    target_date = get_last_trading_day(today - datetime.timedelta(days=1))
                    log_msg = "今天尚未收盘，检查是否落后于上个交易日"
                else:
                    # 如果已收盘或非交易日，我们需要有最新的交易日数据
                    target_date = last_trading_day
                    log_msg = "检查是否落后于最新交易日"

                # 如果目录日期早于目标日期，则需要下载
                if dir_date < target_date:
                    logger.info(f"数据目录过期 (目录日期: {dir_date}, 目标日期: {target_date}) - {log_msg}")
                    need_download = True
                else:
                    logger.debug(f"数据目录满足要求 (目录日期: {dir_date}, 目标日期: {target_date})")
                    need_download = False
            except Exception as e:
                logger.warning(f"无法检查目录日期，准备重新下载: {e}")
                need_download = True
        else:
            need_download = True

        if need_download:
            should_download = True
            # 旧逻辑删除：不再进行额外的 is_trading_day 判断来阻止下载
            # 因为上面的逻辑已经很精细地控制了 need_download
            
            if should_download:
                print("未找到数据目录或数据过期，开始下载... (请耐心等待)")
                
                try:
                    downloader = TdxSeleniumDownloader(self.tdxdir)
                    success = downloader.download(timeout=300)
                    
                    if success:
                        logger.info("数据更新完成")
                        print("数据更新完成")
                    else:
                        logger.error("下载失败")
                except Exception as e:
                    logger.error(f"下载或解压失败: {e}")
            else:
                logger.info("暂无需下载")
                print("暂无需下载")
        else:
            logger.info("数据已是最新，无需下载")
            print("数据已是最新，无需下载")

    def daily(self, symbol=None, **kwargs):
        """
        获取日线数据

        :param symbol: 证券代码
        :return: pd.dataFrame or None
        """
        symbol = Path(symbol).stem
        reader = MooTdxDailyBarReader(vipdoc_path=Path(self.tdxdir) / 'vipdoc')
        
        # 查找股票文件
        vipdoc = self.find_path(symbol=symbol, subdir='lday', suffix='day')
        
        if vipdoc is None:
            logger.warning(f"未找到 {symbol} 的日线数据文件")
            return None
        
        result = reader.get_df(str(vipdoc))
        
        if result is None or result.empty:
            logger.warning(f"读取 {symbol} 日线数据为空")
            return None
       
        return to_data(result, symbol=symbol, **kwargs)

    def xdxr(self, symbol='', **kwargs):
        """
        读取除权除息信息
        
        :param symbol: 股票代码
        :return: pd.DataFrame or None
        """
        from .adjust import fetch_fq_factor
        
        # 尝试使用sina的除权信息
        method = kwargs.get('method', 'qfq')
        df = fetch_fq_factor(symbol=symbol, method=method)
        
        if df is not None:
            return df
            
        return None

    def minute(self, symbol=None, suffix=1, **kwargs):  # noqa
        """
        获取1, 5分钟线

        :param suffix: 文件前缀
        :param symbol: 证券代码
        :return: pd.dataFrame or None
        """
        symbol = Path(symbol).stem
        subdir = 'fzline' if str(suffix) == '5' else 'minline'
        suffix = ['lc5', '5'] if str(suffix) == '5' else ['lc1', '1']
        symbol = self.find_path(symbol, subdir=subdir, suffix=suffix)

        if symbol is not None:
            reader = TdxMinBarReader() if 'lc' not in symbol.suffix else TdxLCMinBarReader()
            return reader.get_df(str(symbol))

        return None

    def fzline(self, symbol=None):
        """
        分钟线数据

        :param symbol: 自定义板块股票列表, 类型 list
        :return: pd.dataFrame or Bool
        """
        return self.minute(symbol, suffix=5)

    def block_new(self, name: str = None, symbol: list = None, group=False, **kwargs):
        """
        自定义板块数据操作

        :param name: 自定义板块名称
        :param symbol: 自定义板块股票列表, 类型 list
        :param group:
        :return: pd.dataFrame or Bool
        """
        from mootdx.tools.customize import Customize

        reader = Customize(tdxdir=self.tdxdir)

        if symbol:
            return reader.create(name=name, symbol=symbol, **kwargs)

        return reader.search(name=name, group=group)

    def block(self, concept_type=None, return_df=False):
        """
        获取板块数据
        :param concept_type: 板块类型，可选值 'GN' (概念), 'FG' (风格), 'ZS' (指数)
        :param return_df: 是否返回 DataFrame 格式，默认为 False (返回 Block 对象列表)
        :return: list[Block] or pd.DataFrame
        """
        df = self.parse_concept_data(concept_type=concept_type)
        
        if return_df:
            return df
            
        if df.empty:
            return []
            
        blocks = []
        # 按板块分组
        grouped = df.groupby(['concept_name', 'concept_code', 'concept_type'])
        
        for (name, code, ctype), group in grouped:
            stocks = group[['stock_code', 'stock_name']].to_dict('records')
            blocks.append(Block(
                concept_name=name,
                concept_code=code,
                concept_type=ctype,
                stocks=stocks
            ))
            
        return blocks

    def parse_stock_mapping(self, file_path):
        """
        解析股票代码-名称映射文件
        返回: pd.DataFrame
        """
        data = []

        try:
            lines = read_data(Path(self.tdxdir) / 'T0002' / 'hq_cache' / file_path)
            if not lines:
                return pd.DataFrame()

            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # 解析格式: 000001|平安银行|平安保险,谢永林,冀光恒
                parts = line.split('|')

                if len(parts) < 2:
                    logger.warning(f"警告: 第{line_num}行格式不正确: {line}")
                    continue

                stock_code = parts[0].strip()
                stock_name = parts[1].strip()

                stock_name = stock_name.replace(' ', '').replace('　', '')  # 全角和半角空格
                data.append({'stock_code': stock_code, 'stock_name': stock_name})
            
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"解析文件时出错: {e}")
            return pd.DataFrame()

    def parse_concept_data(self, concept_type=None) -> pd.DataFrame:
        """
        解析原始数据格式为 DataFrame
        """
        stock_mapping_df = self.parse_stock_mapping('infoharbor_ex.code')
        stock_mapping = dict(zip(stock_mapping_df['stock_code'], stock_mapping_df['stock_name'])) if not stock_mapping_df.empty else {}
        data_rows = []

        current_type = None
        current_name = None
        current_code = None

        # 读取 GN/FG/ZS
        file_path = Path(self.tdxdir) / 'T0002' / 'hq_cache' / 'infoharbor_block.dat'
        gn_lines = read_data(file_path)
        
        if gn_lines:
            for line in gn_lines:
                if line.startswith('#'):
                    parts = line.strip('#').split(',')
                    concept_info = parts[0].split('_')
                    
                    # concept_info example: ['GN', '银行']
                    # parts example: ['GN_银行', '1', '880471']
                    
                    c_type = concept_info[0]
                    c_name = concept_info[1]
                    c_code = parts[2] if len(parts) > 2 else ''
                    
                    # Filter by concept_type if provided
                    if concept_type and c_type != concept_type:
                        current_type = None # Skip this block
                        continue
                        
                    current_type = c_type
                    current_name = c_name
                    current_code = c_code
                    
                else:
                    if current_type is None:
                        continue
                        
                    stock_items = line.split(',')
                    for item in stock_items:
                        if item and '#' in item:
                            exchange, code = item.split('#')
                            stock_name = stock_mapping.get(code)
                            
                            data_rows.append({
                                'concept_type': current_type,
                                'concept_name': current_name,
                                'concept_code': current_code,
                                'stock_code': code,
                                'stock_name': stock_name
                            })

        df = pd.DataFrame(data_rows)
        if not df.empty:
            # Reorder columns and add ID
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'ID'}, inplace=True)
            df['ID'] = df['ID'] + 1
            df = df[['ID', 'concept_type', 'concept_name', 'concept_code', 'stock_code', 'stock_name']]
            
        return df


    def _parse_industry_config(self):
        """
        解析行业配置文件 tdxzs3.cfg
        返回: pd.DataFrame
        """
        file_path = Path(self.tdxdir) / 'T0002' / 'hq_cache' / 'tdxzs3.cfg'
        data = []
        
        if not file_path.exists():
            return pd.DataFrame()
            
        try:
            # tdxzs3.cfg 通常使用 GBK 编码
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                content = f.read()
                
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split('|')
                # 格式: 银行|880471|2|1|1|T1001
                # parts[4] -> 0: 通达信行业, 1: 一级行业, 2: 二级行业
                if len(parts) >= 6:
                    industry_name = parts[0]
                    # block_code = parts[1] # 88xxxx
                    block_code = parts[1]
                    
                # industry_code (T代码 or X代码)
                industry_code = parts[5]
                
                # 用户要求 1级行业、2级行业对应。根据深度映射：
                # T代码: Len 3 -> L0, Len 5 -> L1, Len 7 -> L2
                # X代码: Len 3 -> L1, Len 5 -> L2, Len 7 -> L3
                level = "0"
                code_len = len(industry_code)
                if industry_code.startswith('T'):
                    if code_len == 5: level = "1"
                    elif code_len >= 7: level = "2"
                    elif code_len == 3: level = "0"
                elif industry_code.startswith('X'):
                    if code_len == 3: level = "1"
                    elif code_len == 5: level = "2"
                    elif code_len >= 7: level = "3"

                if industry_code.startswith('T') or industry_code.startswith('X'):
                    data.append({
                        'industry_name': industry_name,
                        'industry_code': industry_code,
                        'block_code': block_code,
                        'level_type': level
                    })
                        
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"解析 tdxzs3.cfg 失败: {e}")
            return pd.DataFrame()

    def _parse_stock_industry_mapping(self):
        """
        解析股票-行业映射文件 tdxhy.cfg
        返回: pd.DataFrame (columns: stock_code, industry_code)
        """
        file_path = Path(self.tdxdir) / 'T0002' / 'hq_cache' / 'tdxhy.cfg'
        data = []
        
        if not file_path.exists():
            return pd.DataFrame()

        try:
            # 优先尝试 GBK 读取
            lines = []
            try:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    lines = f.readlines()
            except:
                lines = read_data(file_path)

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split('|')
                if len(parts) >= 3:
                    stock_code = parts[1]
                    industry_code = parts[2] # T代码
                    industry_code_x = parts[5] if len(parts) > 5 else '' # 可能是 X代码 (SWS)
                    
                    if industry_code or industry_code_x:
                        data.append({
                            'stock_code': stock_code,
                            'industry_code': industry_code,
                            'industry_code_x': industry_code_x
                        })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"解析 tdxhy.cfg 失败: {e}")
            return pd.DataFrame()

    def get_industries(self, source='tdx', **kwargs):
        """
        获取行业列表
        :param source: 数据源，默认 'tdx'
        :param kwargs: level (1 或 2，对应一级/二级行业)
        :return: pd.DataFrame
        """
        level = kwargs.get('level', 1)
        
        # 仅支持一级行业 (1) 和 二级行业 (2)
        if level not in [1, 2]:
            logger.warning(f"不支持的行业级别: {level}，目前仅支持 1 (一级行业) 或 2 (二级行业)")
            return pd.DataFrame()
            
        if source == 'sws':
            return self.sws_reader.get_industries(level=level, return_df=True)
            
        if source == 'tdx':
            df = self._parse_industry_config()
            if not df.empty:
                # TDX Level Mapping: 1: 一级行业, 2: 二级行业
                return df[df['level_type'] == str(level)]
            return df
            
        return pd.DataFrame()

    def get_industry_stocks(self, industry_code, source='tdx', **kwargs):
        """
        获取指定行业的成分股
        :param industry_code: 行业代码 (如 'T1001', '880471', 或名称 '银行')
        :param source: 数据源，默认 'tdx'
        :return: list[str] 股票代码列表
        """
        if source == 'sws':
            return self.sws_reader.get_industry_stocks(industry_code)

        if source != 'tdx':
            return []
            
        ind_df = self._parse_industry_config()
        map_df = self._parse_stock_industry_mapping()
        
        if ind_df.empty or map_df.empty:
            return []
            
        # 查找匹配的 industry_code (支持 T代码, Block代码, 名称)
        target_code = None
        
        # 1. 尝试直接匹配 T代码
        if industry_code in ind_df['industry_code'].values:
            target_code = industry_code
        # 2. 尝试匹配 Block代码 (88xxxx)
        elif industry_code in ind_df['block_code'].values:
            target_code = ind_df[ind_df['block_code'] == industry_code]['industry_code'].iloc[0]
        # 3. 尝试匹配 名称
        elif industry_code in ind_df['industry_name'].values:
            target_code = ind_df[ind_df['industry_name'] == industry_code]['industry_code'].iloc[0]
            
        if not target_code:
            logger.warning(f"未找到行业: {industry_code}")
            return []
            
        # 筛选股票 - 前缀匹配以支持父行业查询 (e.g. T10 金融 -> T1001 银行, T1002 证券)
        stocks = map_df[map_df['industry_code'].str.startswith(target_code)]['stock_code'].tolist()
        return stocks

    def get_stock_industry(self, stock_code, source='tdx', **kwargs):
        """
        获取股票所属行业
        :param stock_code: 股票代码
        :param source: 数据源，默认 'tdx'
        :return: dict 行业信息 {'industry_code': ..., 'industry_name': ...}
        """
        if source == 'sws':
            return self.sws_reader.get_stock_industry(stock_code)

        if source != 'tdx':
            return None
            
        map_df = self._parse_stock_industry_mapping()
        ind_df = self._parse_industry_config()
        
        if map_df.empty or ind_df.empty:
            return None
            
        # 查找股票的行业代码
        row = map_df[map_df['stock_code'] == stock_code]
        if row.empty:
            return None
            
        # 提取所有相关的行业代码 (T代码, X代码)
        rec = row.iloc[0]
        # 优先使用 T代码 (通达信原生行业代码)
        codes = [rec['industry_code'], rec['industry_code_x']]
        codes = [c for c in codes if c] # 过滤空值
        
        info = {
            'stock_code': stock_code,
            'stock_name': '', 
            'l1_name': '', 'l1_code': '',
            'l2_name': '', 'l2_code': ''
        }
        
        # 尝试获取股票名称
        try:
            stocks = self.block(concept_type='GN', return_df=True)
            if not stocks.empty:
                s_rec = stocks[stocks['stock_code'] == stock_code]
                if not s_rec.empty:
                    info['stock_name'] = s_rec.iloc[0]['stock_name']
        except:
            pass
            
        # 遍历代码，尝试填充 L1/L2
        for code in codes:
            ind_rec = ind_df[ind_df['industry_code'] == code]
            if ind_rec.empty:
                continue
                
            cur_info = ind_rec.iloc[0]
            level = cur_info['level_type']
            
            # 如果命中的是 Level 2
            if level == '2':
                if not info['l2_name']:
                    info['l2_name'] = cur_info['industry_name']
                    info['l2_code'] = code
                
                # 寻找父级 Level 1 (T0101 -> T01, X5001 -> X50)
                p1_code = code[:3]
                if len(p1_code) == 3:
                    p_rec = ind_df[ind_df['industry_code'] == p1_code]
                    if not p_rec.empty and not info['l1_name']:
                        info['l1_name'] = p_rec.iloc[0]['industry_name']
                        info['l1_code'] = p1_code
            
            # 如果命中的是 Level 1
            elif level == '1':
                if not info['l1_name']:
                    info['l1_name'] = cur_info['industry_name']
                    info['l1_code'] = code
            
            # 如果命中的是 Level 3 (仅 X代码可能)
            elif level == '3':
                p2_code = code[:5]
                p1_code = code[:3]
                
                p2_rec = ind_df[ind_df['industry_code'] == p2_code]
                if not p2_rec.empty and not info['l2_name']:
                    info['l2_name'] = p2_rec.iloc[0]['industry_name']
                    info['l2_code'] = p2_code
                
                p1_rec = ind_df[ind_df['industry_code'] == p1_code]
                if not p1_rec.empty and not info['l1_name']:
                    info['l1_name'] = p1_rec.iloc[0]['industry_name']
                    info['l1_code'] = p1_code

        # 如果最终还是空，尝试捕获第一个代码信息填充 l1
        if not info['l1_name'] and not info['l2_name'] and codes:
            first_ind = ind_df[ind_df['industry_code'] == codes[0]]
            if not first_ind.empty:
                info['l1_name'] = first_ind.iloc[0]['industry_name']
                info['l1_code'] = codes[0]

        return info


class ExtReader(ReaderBase):
    """扩展市场读取"""

    def __init__(self, tdxdir=None):
        super(ExtReader, self).__init__(tdxdir)
        self.reader = TdxExHqDailyBarReader(vipdoc_path=Path(tdxdir) / 'vipdoc')

    def daily(self, symbol=None):
        """
        获取扩展市场日线数据

        :return: pd.dataFrame or None
        """

        vipdoc = self.find_path(symbol=symbol, subdir='lday', suffix='day')
        return self.reader.get_df(str(vipdoc)) if vipdoc else None

    def minute(self, symbol=None):
        """
        获取扩展市场分钟线数据

        :return: pd.dataFrame or None
        """

        if not symbol:
            return None

        vipdoc = self.find_path(symbol=symbol, subdir='minline', suffix=['lc1', '1'])
        return self.reader.get_df(str(vipdoc)) if vipdoc else None

    def fzline(self, symbol=None):
        """
        获取日线数据

        :return: pd.dataFrame or None
        """

        vipdoc = self.find_path(symbol=symbol, subdir='fzline', suffix='lc5')
        return self.reader.get_df(str(vipdoc)) if symbol else None

