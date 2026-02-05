import os
import glob
import logging
import pandas as pd
from kitetdx.downloader.sws import download_sws_data, get_default_cache_dir
from kitetdx.reader import Block

logger = logging.getLogger(__name__)

class SwsReader:
    """
    Reader for Shenwan (SWS) Industry Classification (2021 Version).
    """

    def __init__(self, cache_dir=None, auto_download=True, force_update=False, **kwargs):
        self.cache_dir = cache_dir or get_default_cache_dir()
        
        # Check if update is needed
        need_update = force_update
        
        if not need_update:
            if not os.path.exists(self.cache_dir):
                need_update = True
            else:
                stock_file = self._find_stock_file()
                if not stock_file:
                    need_update = True
                else:
                    # Check expiration (90 days)
                    import time
                    try:
                        mtime = os.path.getmtime(stock_file)
                        if time.time() - mtime > 90 * 86400:
                            print(f"[SWS] Cache expired (older than 90 days). Updating...")
                            need_update = True
                    except OSError:
                         need_update = True
        
        if need_update:
            if auto_download:
                print("[SWS] Downloading/Updating SWS data...")
                download_sws_data(self.cache_dir)
            elif not self._find_stock_file():
                # Only raise if we don't have ANY data
                raise FileNotFoundError(f"SWS data not found in {self.cache_dir}")

        self.df = self._load_data()

    def _find_stock_file(self):
        """Find the stock classification excel file."""
        # Pattern: *个股申万行业分类*.xlsx (Fuzzy match for changing date suffix)
        pattern = os.path.join(self.cache_dir, "*个股申万行业分类*.xlsx")
        files = glob.glob(pattern)
        if files:
            return files[0]
        return None

    def _load_data(self):
        """Load and normalize the data."""
        filepath = self._find_stock_file()
        if not filepath:
            raise FileNotFoundError("SWS stock classification file not found.")
            
        # Read Excel
        # Columns: ['交易所', '行业代码', '股票代码', '公司简称', '新版一级行业', '新版二级行业', '新版三级行业']
        df = pd.read_excel(filepath, dtype={'行业代码': str, '股票代码': str})
        
        # Normalize columns
        df = df.rename(columns={
            '股票代码': 'stock_code',
            '公司简称': 'stock_name',
            '行业代码': 'industry_code',
            '新版一级行业': 'l1_name',
            '新版二级行业': 'l2_name',
            '新版三级行业': 'l3_name'
        })
        
        # Clean stock_code (remove .SH, .SZ suffix)
        df['stock_code'] = df['stock_code'].astype(str).str.split('.').str[0]
        
        return df

    def block(self, concept_type='1', return_df=False):
        """
        获取板块数据
        :param concept_type: 板块层级，可选值 '1', '2', '3' (默认 '1')
        :param return_df: 是否返回 DataFrame 格式，默认为 False (返回 Block 对象列表)
        :return: list[Block] or pd.DataFrame
        """
        level = str(concept_type).lower().replace('l', '')
        if level not in ['1', '2', '3']:
            level = '1'

        col = f'l{level}_name'
        if col not in self.df.columns:
            return pd.DataFrame() if return_df else []
        
        blocks = []
        rows = []
        
        grouped = self.df.groupby(col)
        
        for name, group in grouped:
            stocks = group[['stock_code', 'stock_name']].to_dict('records')
            code = '' 
            
            if return_df:
                for s in stocks:
                    rows.append({
                        'concept_type': f'sws_l{level}',
                        'concept_name': name,
                        'concept_code': code,
                        'stock_code': s['stock_code'],
                        'stock_name': s['stock_name']
                    })
            else:
                blocks.append(Block(
                    concept_name=name,
                    concept_code=code,
                    concept_type=f'sws_l{level}',
                    stocks=stocks
                ))
        
        if return_df:
            return pd.DataFrame(rows)
            
        return blocks

    def get_industries(self, level=1, return_df=True):
        """
        Get list of industries. 
        """
        if level not in [1, 2]:
            logger.warning(f"Unsupported SWS level: {level}. Only levels 1 and 2 are supported.")
            return pd.DataFrame() if return_df else []

        col = f'l{level}_name'
        if col not in self.df.columns:
            return pd.DataFrame() if return_df else []
            
        names = self.df[col].dropna().unique().tolist()
        
        if return_df:
            # Return DataFrame with 'industry_name' column
            return pd.DataFrame({'industry_name': names, 'industry_code': '', 'level_type': str(level)})
            
        return names

    def get_industry_stocks(self, industry_name):
        """
        Get stocks for a specific industry (search levels 1 and 2).
        """
        mask = (self.df['l1_name'] == industry_name) | \
               (self.df['l2_name'] == industry_name)
        
        result = self.df[mask]['stock_code'].unique().tolist()
        return result

    def get_stock_industry(self, stock_code):
        """
        Get industry info for a stock (mapped to Level 1 and 2).
        """
        row = self.df[self.df['stock_code'] == str(stock_code)]
        if row.empty:
            return None
        
        # Return the first match
        rec = row.iloc[0]
        code = rec['industry_code'] # Example: 480301
        
        return {
            'stock_code': rec['stock_code'],
            'stock_name': rec['stock_name'],
            'l1_name': rec['l1_name'],
            'l1_code': code[:2] if len(code) >= 2 else '',
            'l2_name': rec['l2_name'],
            'l2_code': code[:4] if len(code) >= 4 else ''
        }