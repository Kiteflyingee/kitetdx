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
# from mootdx.utils import read_data
from mootdx.utils import to_data
from mootdx.logger import logger
from kitetdx.utils import read_data
from kitetdx.downloader import TdxSeleniumDownloader


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

        return StdReader(**kwargs)


class ReaderBase(ABC):
    # 默认通达信安装目录
    tdxdir = 'C:/new_tdx'

    def __init__(self, tdxdir=None):
        """
        构造函数

        :param tdxdir: 通达信安装目录
        """

        if not Path(tdxdir).is_dir():
            raise Exception('tdxdir 目录不存在')

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

    def daily(self, symbol=None, **kwargs):
        """
        获取日线数据

        :param symbol: 证券代码
        :return: pd.dataFrame or None
        """
        symbol = Path(symbol).stem
        reader = MooTdxDailyBarReader()
        vipdoc = self.find_path(symbol=symbol, subdir='lday', suffix='day')
        
        need_download = False
        if vipdoc is not None:
            try:
                mtime = vipdoc.stat().st_mtime
                file_date = datetime.date.fromtimestamp(mtime)
                today = datetime.date.today()
                
                # 获取最近的交易日
                last_trading_day = get_last_trading_day(today)
                
                # 如果文件日期早于最近的交易日，则需要下载
                if file_date < last_trading_day:
                    if is_trading_day(today):
                        logger.info(f"文件过期 (文件日期: {file_date}, 最近交易日: {last_trading_day})")
                    else:
                        logger.info(f"文件过期 (文件日期: {file_date}, 最近交易日: {last_trading_day}, 今天非交易日)")
                    need_download = True
                else:
                    logger.info(f"文件是最新的 (文件日期: {file_date}, 最近交易日: {last_trading_day})")
            except Exception as e:
                logger.warning(f"无法检查文件日期，准备重新下载: {e}")
                need_download = True
        else:
            need_download = True

        if vipdoc is None or need_download:
            # 使用 Selenium 下载并解压文件（绕过反爬虫）
            logger.info("未找到本地文件或文件过期，开始使用 Selenium 下载...")
            
            try:
                downloader = TdxSeleniumDownloader(self.tdxdir)
                success = downloader.download(timeout=300)
                
                if success:
                    # 重新查找文件
                    vipdoc = self.find_path(symbol=symbol, subdir='lday', suffix='day')
                else:
                    logger.error("下载失败")
            except Exception as e:
                logger.error(f"下载或解压失败: {e}")
        
        result = reader.get_df(str(vipdoc)) if vipdoc else None
       
        return to_data(result, symbol=symbol, **kwargs)

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

    def block(self, concept_type=None):
        """
        获取板块数据
        :param concept_type: 板块类型，可选值 'GN' (概念), 'FG' (风格), 'ZS' (指数)
        :return: pd.DataFrame
        """
        return self.parse_concept_data(concept_type=concept_type)

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


class ExtReader(ReaderBase):
    """扩展市场读取"""

    def __init__(self, tdxdir=None):
        super(ExtReader, self).__init__(tdxdir)
        self.reader = TdxExHqDailyBarReader()

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

