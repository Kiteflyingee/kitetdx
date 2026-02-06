import os
import requests
import subprocess
import shutil
from pathlib import Path

# SWS 2021 Industry Classification Download URL
SWS_RAR_URL = "https://www.swsresearch.com/swindex/pdf/SwClass2021/SwClass.rar"

def get_default_cache_dir():
    """
    Returns the default cache directory: kitetdx/cache
    """
    # Assuming this file is in kitetdx/downloader/sws.py
    # User requested: ~/.kitetdx/cache
    return os.path.join(os.path.expanduser('~'), '.kitetdx', 'cache')

def download_sws_data(cache_dir=None, verbose=True):
    """
    Download and extract Shenwan Industry Classification data.
    
    :param cache_dir: Directory to store the downloaded and extracted files.
    :param verbose: Print status messages.
    """
    if cache_dir is None:
        cache_dir = get_default_cache_dir()
    
    if verbose:
        print(f"[SWS] 缓存目录: {cache_dir}")
        
    os.makedirs(cache_dir, exist_ok=True)
    
    rar_path = os.path.join(cache_dir, "SwClass.rar")
    
    # 1. Download
    if verbose:
        print(f"[SWS] 正在下载 {SWS_RAR_URL}...")
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(SWS_RAR_URL, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(rar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        if verbose:
            print("[SWS] 下载完成。")
            
    except Exception as e:
        print(f"[SWS] 下载失败: {e}")
        return False

    # 2. Extract
    # Try using 'unrar' first, then 'bsdtar' (common on macOS/Linux), then '7z'
    # Since dependency analysis showed 'bsdtar' is available, we prioritize standard tools.
    
    if verbose:
        print(f"[SWS] 正在解压 {rar_path}...")
        
    extracted = False
    
    # Method A: bsdtar (Mac/Linux default)
    try:
        # bsdtar -xf file.rar -C dest_dir
        subprocess.run(["bsdtar", "-xf", rar_path, "-C", cache_dir], check=True, capture_output=True)
        extracted = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
        
    # Method B: unrar
    if not extracted:
        try:
            subprocess.run(["unrar", "x", "-y", rar_path, cache_dir], check=True, capture_output=True)
            extracted = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    if extracted:
        if verbose:
            print("[SWS] 解压缩完成。")
        return True
    else:
        print("[SWS] 解压缩失败。请安装 'unrar' 或 'bsdtar' (libarchive)。")
        print(f"[SWS] 您可以手动将 {rar_path} 解压缩到 {cache_dir}")
        return False

if __name__ == "__main__":
    download_sws_data()
