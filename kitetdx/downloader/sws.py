import os
import requests
import subprocess
import shutil
from pathlib import Path

# SWS 2021 Industry Classification Download URLs (Direct XLS)
SWS_XLS_URLS = [
    "https://www.swsresearch.com/swindex/pdf/SwClass2021/StockClassifyUse_stock.xls",
    "https://www.swsresearch.com/swindex/pdf/SwClass2021/SwClassCode_2021.xls"
]

def get_default_cache_dir():
    """
    Returns the default cache directory: ~/.kitetdx/cache
    """
    return os.path.join(os.path.expanduser('~'), '.kitetdx', 'cache')

def download_sws_data(cache_dir=None, verbose=True):
    """
    Download Shenwan Industry Classification data directly as Excel files.
    
    :param cache_dir: Directory to store the downloaded files.
    :param verbose: Print status messages.
    """
    if cache_dir is None:
        cache_dir = get_default_cache_dir()
    
    if verbose:
        print(f"[SWS] 缓存目录: {cache_dir}")
        
    os.makedirs(cache_dir, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    success_count = 0
    
    for url in SWS_XLS_URLS:
        filename = os.path.basename(url)
        dest_path = os.path.join(cache_dir, filename)
        
        if verbose:
            print(f"[SWS] 正在下载 {url}...")
            
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            if verbose:
                print(f"[SWS] {filename} 下载完成。")
            success_count += 1
                
        except Exception as e:
            print(f"[SWS] {filename} 下载失败: {e}")

    return success_count == len(SWS_XLS_URLS)

if __name__ == "__main__":
    download_sws_data()
