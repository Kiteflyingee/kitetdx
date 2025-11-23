from mootdx.quotes import Quotes as MooQuotes
from mootdx.consts import MARKET_SH

class Quotes(object):
    """
    Kitetdx Quotes Module
    
    Wraps mootdx.quotes.Quotes to provide a unified and documented API.
    """

    @staticmethod
    def factory(market='std', **kwargs):
        """
        Quotes Factory Method
        
        :param market: std (Standard Market), ext (Extended Market)
        :param kwargs: Variable arguments
        :return: Quotes object
        """
        return MooQuotes.factory(market=market, **kwargs)

    def __init__(self, **kwargs):
        self._client = MooQuotes.factory(**kwargs)

    def bars(self, symbol='000001', frequency=9, start=0, offset=800, **kwargs):
        """
        获取实时日K线数据
        
        :param symbol: 股票代码
        :param frequency: 数据频次 9=日线
        :param start: 开始位置
        :param offset: 每次获取条数
        :return: pd.DataFrame or None
        """
        return self._client.bars(symbol=symbol, frequency=frequency, start=start, offset=offset, **kwargs)

    def index_bars(self, symbol='000001', frequency=9, start=0, offset=800, **kwargs):
        """
        获取指数K线数据
        
        :param symbol: 股票代码
        :param frequency: 数据频次
        :param start: 开始位置
        :param offset: 获取数量
        :return: pd.DataFrame or None
        """
        return self._client.index_bars(symbol=symbol, frequency=frequency, start=start, offset=offset, **kwargs)

    def minute(self, symbol=None, **kwargs):
        """
        获取实时分时数据
        
        :param symbol: 股票代码
        :return: pd.DataFrame
        """
        return self._client.minute(symbol=symbol, **kwargs)

    def minutes(self, symbol=None, date='20191023', **kwargs):
        """
        分时历史数据
        
        :param symbol: 股票代码
        :param date: 查询日期
        :return: pd.DataFrame or None
        """
        return self._client.minutes(symbol=symbol, date=date, **kwargs)

    def transaction(self, symbol='', start=0, offset=800, **kwargs):
        """
        查询分笔成交
        
        :param symbol: 股票代码
        :param start: 起始位置
        :param offset: 结束位置
        :return: pd.DataFrame or None
        """
        return self._client.transaction(symbol=symbol, start=start, offset=offset, **kwargs)

    def transactions(self, symbol='', start=0, offset=800, date='20170209', **kwargs):
        """
        查询历史分笔成交
        
        :param symbol: 股票代码
        :param start: 起始位置
        :param offset: 获取数量
        :param date: 查询日期
        :return: pd.DataFrame or None
        """
        return self._client.transactions(symbol=symbol, start=start, offset=offset, date=date, **kwargs)

    def F10(self, symbol='', name=''):
        """
        读取公司信息详情
        
        :param name: 公司 F10 标题
        :param symbol: 股票代码
        :return: pd.DataFrame or None
        """
        return self._client.F10(symbol=symbol, name=name)

    def finance(self, symbol='000001', **kwargs):
        """
        读取财务信息
        
        :param symbol: 股票代码
        :return: pd.DataFrame
        """
        return self._client.finance(symbol=symbol, **kwargs)

    def k(self, symbol='', begin=None, end=None, **kwargs):
        """
        读取k线信息
        
        :param symbol: 股票代码
        :param begin: 开始日期
        :param end: 截止日期
        :return: pd.DataFrame or None
        """
        return self._client.k(symbol=symbol, begin=begin, end=end, **kwargs)

    def ohlc(self, **kwargs):
        """
        读取k线信息 (Alias for k)
        """
        return self.k(**kwargs)

    def block(self, tofile='block.dat', **kwargs):
        """
        获取证券板块信息
        
        :param tofile: 保存文件
        :return: pd.DataFrame or None
        """
        return self._client.block(tofile=tofile, **kwargs)

    def stock_count(self, market=MARKET_SH):
        """
        获取市场股票数量
        
        :param market: 股票市场代码 sh 上海， sz 深圳
        :return: int
        """
        return self._client.stock_count(market=market)

    def stocks(self, market=MARKET_SH):
        """
        获取股票列表
        
        :param market: 股票市场
        :return: pd.DataFrame
        """
        return self._client.stocks(market=market)

    def stock_all(self):
        """
        获取所有股票列表
        
        :return: pd.DataFrame
        """
        return self._client.stock_all()

    def xdxr(self, symbol='', **kwargs):
        """
        读取除权除息信息
        
        :param symbol: 股票代码
        :return: pd.DataFrame or None
        """
        return self._client.xdxr(symbol=symbol, **kwargs)
