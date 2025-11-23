from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd
from tdxpy.reader import TdxExHqDailyBarReader
from tdxpy.reader import TdxLCMinBarReader
from tdxpy.reader import TdxMinBarReader

from mootdx.contrib.compat import MooTdxDailyBarReader
from mootdx.utils import get_stock_market
# from mootdx.utils import read_data
from mootdx.utils import to_data
from mootdx.logger import logger

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
        返回: {股票代码: 股票名称} 的字典
        """
        stock_mapping = {}

        try:
            lines = read_data(Path(self.tdxdir) / 'T0002' / 'hq_cache' / file_path)
            if not lines:
                return {}

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
                stock_mapping[stock_code] = stock_name
            return stock_mapping

        except Exception as e:
            logger.error(f"解析文件时出错: {e}")
            return {}

    def parse_concept_data(self, concept_type=None) -> pd.DataFrame:
        """
        解析原始数据格式为 DataFrame
        """
        stock_mapping = self.parse_stock_mapping('infoharbor_ex.code')
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

