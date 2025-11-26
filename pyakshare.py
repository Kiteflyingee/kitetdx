import akshare as ak

# stock_individual_info_em_df = ak.stock_individual_info_em(symbol="000001")
# print(stock_individual_info_em_df)

# stock_individual_spot_xq_df = ak.stock_individual_spot_xq(symbol="SH600000")
# print(stock_individual_spot_xq_df)

# qfq因子都是用的新浪的复权因子
# qfq_factor_df = ak.stock_zh_a_daily(symbol="sz000002", adjust="qfq-factor")
# print(qfq_factor_df)

# 这个接口有集合竞价成交信息
# stock_zh_a_tick_tx_js_df = ak.stock_zh_a_tick_tx_js(symbol="sz000001")
# print(stock_zh_a_tick_tx_js_df)

# stock_zh_growth_comparison_em_df = ak.stock_zh_growth_comparison_em(symbol="SZ000938")
# print(stock_zh_growth_comparison_em_df)

stock_zh_valuation_comparison_em_df = ak.stock_zh_valuation_comparison_em(symbol="SZ000938")
print(stock_zh_valuation_comparison_em_df)

# from mootdx.quotes import Quotes

# client = Quotes.factory(market='std')
# client.quotes(symbol=["000001", "600300"])

# client.bars(symbol='600036', frequency=9, offset=10)

# # 前复权
# client.bars(symbol='600036', adjust='qfq')

# # 后复权
# client.bars(symbol='600036', adjust='hfq')