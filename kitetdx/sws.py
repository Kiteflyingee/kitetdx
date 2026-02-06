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
                stock_file, _ = self._find_stock_file()
                if not stock_file:
                    need_update = True
                else:
                    # Check expiration (90 days)
                    import time
                    try:
                        mtime = os.path.getmtime(stock_file)
                        if time.time() - mtime > 90 * 86400:
                            print(f"[SWS] 缓存已过期 (超过 90 天)，正在更新...")
                            need_update = True
                    except OSError:
                         need_update = True
        
        if need_update:
            if auto_download:
                print("[SWS] 正在下载/更新申万行业数据... (请耐心等待)")
                download_sws_data(self.cache_dir)
            else:
                stock_file, _ = self._find_stock_file()
                if not stock_file:
                    # Only raise if we don't have ANY data
                    raise FileNotFoundError(f"未在 {self.cache_dir} 找到申万数据")

        self.df = self._load_data()

    def _find_stock_file(self):
        """Find the required SWS excel files."""
        stock_file = os.path.join(self.cache_dir, "StockClassifyUse_stock.xls")
        class_file = os.path.join(self.cache_dir, "SwClassCode_2021.xls")
        
        if os.path.exists(stock_file) and os.path.exists(class_file):
            return stock_file, class_file
        
        # Fallback to old pattern if new files not found
        pattern = os.path.join(self.cache_dir, "*个股申万行业分类*.xlsx")
        files = glob.glob(pattern)
        if files:
            return files[0], None
            
        return None, None

    def _load_data(self):
        """Load and normalize the data."""
        stock_file, class_file = self._find_stock_file()
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
        Returns: dict with l1_name, l1_code, l2_name
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