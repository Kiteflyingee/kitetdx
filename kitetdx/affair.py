from mootdx.affair import Affair as MooAffair

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
    def fetch(downdir='tmp', filename=''):
        """
        下载财务文件
        
        :param downdir: 下载目录
        :param filename: 文件名
        :return: bool
        """
        return MooAffair.fetch(downdir=downdir, filename=filename)

    @staticmethod
    def parse(downdir='tmp', filename=''):
        """
        解析财务文件
        
        :param downdir: 下载目录
        :param filename: 文件名 (可选，如果不指定则解析目录下所有)
        :return: pd.DataFrame or None
        """
        return MooAffair.parse(downdir=downdir, filename=filename)
