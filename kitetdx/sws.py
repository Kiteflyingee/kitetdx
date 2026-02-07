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
        self.force_update = force_update
        
        # If force_update, download new data to cache
        if force_update and auto_download:
            print("[SWS] 正在下载/更新申万行业数据... (请耐心等待)")
            download_sws_data(self.cache_dir)

        self.df = self._load_data()

    def _find_stock_file(self, use_cache=False):
        """Find the required SWS excel files.
        
        Priority:
        1. If use_cache=True, look in cache_dir first
        2. Otherwise, use built-in data files from kitetdx/data
        """
        # Built-in data directory (packaged with the library)
        builtin_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        # Define search directories based on use_cache flag
        search_dirs = [self.cache_dir, builtin_dir] if use_cache else [builtin_dir, self.cache_dir]
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            stock_file = os.path.join(search_dir, "StockClassifyUse_stock.xls")
            
            # Fuzzy search for SwClassCode (year may change)
            class_pattern = os.path.join(search_dir, "SwClassCode_*.xls")
            class_files = glob.glob(class_pattern)
            class_file = class_files[0] if class_files else None
            
            if os.path.exists(stock_file) and class_file:
                return stock_file, class_file
            
        return None, None

    def _load_data(self):
        """Load and normalize the data."""
        # If force_update, prioritize cache (newly downloaded); otherwise use built-in
        stock_file, class_file = self._find_stock_file(use_cache=self.force_update)
        if not stock_file:
            raise FileNotFoundError("未找到申万行业分类文件")

            
        if class_file:
            # 1. Read Stock mappings
            # Columns: ['股票代码', '计入日期', '行业代码', '更新日期']
            df_stock = pd.read_excel(stock_file, dtype={'股票代码': str, '行业代码': str})
            
            # Normalize stock_code to 6 digits
            df_stock['股票代码'] = df_stock['股票代码'].str.zfill(6)
            
            # Sort by date and keep latest
            df_stock = df_stock.sort_values('计入日期', ascending=True)
            df_stock = df_stock.drop_duplicates('股票代码', keep='last')
            
            # 2. Read Industry Class codes
            # Columns: ['行业代码', '一级行业名称', '二级行业名称', '三级行业名称']
            df_class = pd.read_excel(class_file, dtype={'行业代码': str})
            
            # 3. Merge
            df = pd.merge(df_stock, df_class, on='行业代码', how='left')
            
            # 4. Normalize columns
            df = df.rename(columns={
                '股票代码': 'stock_code',
                '行业代码': 'industry_code',
                '一级行业名称': 'l1_name',
                '二级行业名称': 'l2_name'
            })
            
            # 5. Handle missing L2
            # Use fillna for L2 name
            df['l2_name'] = df['l2_name'].fillna('无二级行业')
            
            # Note: stock_name might be missing in this source, we might need to get it elsewhere if needed
            # For now, just set it to empty if not present
            if '公司简称' in df.columns:
                df = df.rename(columns={'公司简称': 'stock_name'})
            else:
                df['stock_name'] = ''
                
            return df
        else:
            # Old implementation for .xlsx file
            df = pd.read_excel(stock_file, dtype={'行业代码': str, '股票代码': str})
            df = df.rename(columns={
                '股票代码': 'stock_code',
                '公司简称': 'stock_name',
                '行业代码': 'industry_code',
                '新版一级行业': 'l1_name',
                '新版二级行业': 'l2_name'
            })
            df['stock_code'] = df['stock_code'].astype(str).str.split('.').str[0].str.zfill(6)
            return df

    def block(self, concept_type='1', return_df=False):
        """
        获取板块数据
        :param concept_type: 板块层级，可选值 '1', '2', '3' (默认 '1')
        :param return_df: 是否返回 DataFrame 格式，默认为 False (返回 Block 对象列表)
        :return: list[Block] or pd.DataFrame
        """
        level = str(concept_type).lower().replace('l', '')
        if level not in ['1', '2']:
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
            logger.warning(f"不支持的申万行业级别: {level}。仅支持 1 和 2 级。")
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
        Returns: dict with industry, industry_code, sub_industry
        """
        # Ensure stock_code is 6-digit string
        target_code = str(stock_code).split('.')[0].zfill(6)
        
        row = self.df[self.df['stock_code'] == target_code]
        if row.empty:
            return None
        
        # Return the first match
        rec = row.iloc[0]
        code = str(rec['industry_code']) # Example: 480301
        
        l1_code = code[:2] if len(code) >= 2 else ''
            
        return {
            'industry': rec['l1_name'],
            'industry_code': l1_code,
            'sub_industry': rec['l2_name']
        }