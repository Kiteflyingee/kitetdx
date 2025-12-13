"""
TDX 数据下载器模块

优先使用 urllib 下载，失败时回退到 Selenium 绕过反爬虫机制
"""

import shutil
import time
import urllib.request
import zipfile
from pathlib import Path

from mootdx.logger import logger


class TdxSeleniumDownloader:
    """
    使用 Selenium 自动下载 TDX 数据
    
    通过模拟真实浏览器行为绕过 WAF 反爬虫机制
    """
    
    def __init__(self, save_dir: str):
        """
        初始化下载器
        
        Args:
            save_dir: 保存目录路径
        """
        # 必须使用绝对路径，Chrome 下载配置要求绝对路径
        self.save_dir = Path(save_dir).resolve()
        self.vipdoc_dir = self.save_dir / 'vipdoc'
        self.vipdoc_dir.mkdir(parents=True, exist_ok=True)
        
        # 目标文件
        self.zip_filename = "hsjday.zip"
        self.target_url = "https://data.tdx.com.cn/vipdoc/hsjday.zip"
        self.auth_url = "https://data.tdx.com.cn/vipdoc/"
    
    def _get_chrome_driver(self):
        """
        获取 Chrome WebDriver
        
        优先尝试使用本地 ChromeDriver，如果失败则使用 webdriver-manager 下载
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # 配置 Chrome 下载选项
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # 使用新版无头模式，更像真实浏览器
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-dev-shm-usage")  # 避免内存问题
        
        # 关键配置：设置自动下载路径，禁止弹窗
        prefs = {
            "download.default_directory": str(self.save_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 方法1：尝试直接使用系统 Chrome（不需要单独的 chromedriver）
        # Selenium 4.6+ 支持 Selenium Manager 自动管理驱动
        try:
            logger.info("尝试使用 Selenium Manager 自动管理驱动...")
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium Manager 启动成功！")
            return driver
        except Exception as e1:
            logger.warning(f"Selenium Manager 失败: {e1}")
        
        # 方法2：尝试使用 webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            logger.info("尝试使用 webdriver-manager 下载 ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("webdriver-manager 启动成功！")
            return driver
        except Exception as e2:
            logger.warning(f"webdriver-manager 失败: {e2}")
        
        # 方法3：尝试使用常见的本地 chromedriver 路径
        common_paths = [
            "/usr/local/bin/chromedriver",
            "/opt/homebrew/bin/chromedriver",
            shutil.which("chromedriver"),  # 查找 PATH 中的 chromedriver
        ]
        
        for path in common_paths:
            if path and Path(path).exists():
                try:
                    logger.info(f"尝试使用本地 chromedriver: {path}")
                    service = Service(path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info(f"本地 chromedriver 启动成功！")
                    return driver
                except Exception as e3:
                    logger.warning(f"本地 chromedriver 失败: {e3}")
        
        # 全部失败
        raise RuntimeError(
            "无法启动 Chrome WebDriver。请尝试以下解决方案：\n"
            "1. 确保已安装 Google Chrome 浏览器\n"
            "2. 安装 chromedriver: brew install chromedriver (macOS)\n"
            "3. 或者手动下载 chromedriver 放到 PATH 中\n"
            "4. 如果网络有问题，请检查代理设置"
        )
    
    def download(self, timeout: int = 300) -> bool:
        """
        执行下载操作（优先使用 urllib，失败时回退到 Selenium）
        
        Args:
            timeout: 下载超时时间（秒），默认5分钟
            
        Returns:
            bool: 下载是否成功
        """
        logger.info(f"下载目录已设置为: {self.save_dir}")
        
        # 优先尝试 urllib 下载
        logger.info("尝试使用 urllib 直接下载...")
        if self._download_with_urllib(timeout):
            return True
        
        logger.warning("urllib 下载失败，回退到 Selenium 方式...")
        return self._download_with_selenium(timeout)
    
    def _download_with_urllib(self, timeout: int = 300) -> bool:
        """使用 urllib 直接下载"""
        zip_path = self.save_dir / self.zip_filename
        
        try:
            logger.info(f"开始从 {self.target_url} 下载...")
            urllib.request.urlretrieve(self.target_url, zip_path)
            logger.info("下载完成")
            return self._unzip_file(zip_path)
        except Exception as e:
            logger.warning(f"urllib 下载失败: {e}")
            return False
    
    def _download_with_selenium(self, timeout: int = 300) -> bool:
        """
        使用 Selenium 下载（绕过反爬虫）
        
        Args:
            timeout: 下载超时时间（秒）
            
        Returns:
            bool: 下载是否成功
        """
        # 延迟导入 Selenium 相关模块，避免未安装时影响其他功能
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
        except ImportError as e:
            logger.error(
                f"Selenium 未安装，请先安装依赖: pip install selenium webdriver-manager\n"
                f"错误信息: {e}"
            )
            return False
        
        driver = None
        try:
            logger.info("启动浏览器...")
            driver = self._get_chrome_driver()
            
            # 第一步：访问目录页过 WAF
            logger.info(f"访问验证页: {self.auth_url}")
            driver.get(self.auth_url)
            
            logger.info("等待 WAF 验证 (约 8 秒)...")
            time.sleep(8)  # 给足时间让 JS 跑完
            
            # 第二步：触发下载
            logger.info(f"验证通过，请求下载链接: {self.target_url}")
            driver.get(self.target_url)
            
            # 第三步：监控下载进度
            target_file = self.save_dir / self.zip_filename
            
            logger.info("等待下载开始...")
            start_time = time.time()
            
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError("下载超时")
                
                # 检查是否存在 .crdownload 临时文件 (Chrome 正在下载)
                temp_files = list(self.save_dir.glob("*.crdownload"))
                
                if target_file.exists():
                    # 如果目标文件存在，且没有 .crdownload 文件，说明下载完了
                    if not temp_files:
                        logger.info("下载完成！")
                        break
                    else:
                        # 虽然目标文件出现了，但可能有临时文件（正在写入），继续等
                        current_size = target_file.stat().st_size / 1024 / 1024
                        logger.debug(f"正在下载... 已下载 {current_size:.2f} MB")
                elif temp_files:
                    logger.debug("正在下载 (缓存中)...")
                
                time.sleep(1)
            
            # 校验文件大小
            final_size = target_file.stat().st_size
            if final_size < 5000:
                logger.error(f"下载失败：文件太小 ({final_size} bytes)，可能是 HTML 错误页。")
                try:
                    with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                        logger.debug(f"文件内容预览: {f.read(200)}")
                except:
                    pass
                return False
            
            # 第四步：解压
            return self._unzip_file(target_file)
            
        except Exception as e:
            logger.error(f"Selenium 下载过程发生错误: {e}")
            return False
        finally:
            if driver:
                driver.quit()
    
    def _unzip_file(self, zip_path: Path) -> bool:
        """
        解压 ZIP 文件
        
        Args:
            zip_path: ZIP 文件路径
            
        Returns:
            bool: 解压是否成功
        """
        logger.info(f"开始解压: {zip_path}")
        try:
            if not zipfile.is_zipfile(zip_path):
                logger.error("文件损坏，不是有效的 ZIP")
                return False
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                logger.info(f"包含 {len(file_list)} 个文件，解压中...")
                
                for member in file_list:
                    # 处理路径分隔符和安全检查
                    member.filename = member.filename.replace('\\', '/').lstrip('/')
                    target_path = self.vipdoc_dir / member.filename
                    
                    # 安全检查：确保解压路径在 vipdoc_dir 内
                    if str(target_path.resolve()).startswith(str(self.vipdoc_dir.resolve())):
                        zip_ref.extract(member, self.vipdoc_dir)
            
            logger.info(f"成功！数据已解压至: {self.vipdoc_dir}")
            
            # 删除原始 zip
            zip_path.unlink()
            logger.info("已删除临时 ZIP 文件")
            
            return True
            
        except Exception as e:
            logger.error(f"解压失败: {e}")
            return False


def download_tdx_data(tdxdir: str, timeout: int = 300) -> bool:
    """
    便捷函数：下载 TDX 日线数据
    
    Args:
        tdxdir: TDX 数据目录
        timeout: 超时时间（秒）
        
    Returns:
        bool: 是否成功
    """
    downloader = TdxSeleniumDownloader(tdxdir)
    return downloader.download(timeout=timeout)
