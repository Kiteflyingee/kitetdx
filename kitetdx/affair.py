import os
from pathlib import Path
from mootdx.affair import Affair as MooAffair

def get_default_downdir():
    """
    获取默认的下载目录: ~/.kitetdx/tmp
    """
    path = os.path.join(os.path.expanduser('~'), '.kitetdx', 'tmp')
    os.makedirs(path, exist_ok=True)
    return path

class Affair(object):
    """
    Kitetdx Affair Module
    
    Wraps mootdx.affair.Affair to provide financial data access.
    """

    @staticmethod
    def files():
        """
        获取远程文件列表
        
        :return: list
        """
        return MooAffair.files()

    @staticmethod
    def fetch(downdir=None, filename=''):
        """
        下载财务文件
        
        :param downdir: 下载目录 (默认为 ~/.kitetdx/tmp)
        :param filename: 文件名
        :return: bool
        """
        downdir = downdir or get_default_downdir()
        return MooAffair.fetch(downdir=downdir, filename=filename)

    @staticmethod
    def parse(downdir=None, filename=''):
        """
        解析财务文件
        
        :param downdir: 下载目录 (默认为 ~/.kitetdx/tmp)
        :param filename: 文件名 (可选，如果不指定则解析目录下所有)
        :return: pd.DataFrame or None
        """
        downdir = downdir or get_default_downdir()
        return MooAffair.parse(downdir=downdir, filename=filename)
