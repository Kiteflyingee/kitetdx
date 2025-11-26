from mootdx.logger import logger

def read_data(file_path):
    """
    读取文件内容
    """
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            return f.read().strip().split('\n')
    except FileNotFoundError:
        logger.error(f"错误: 文件 {file_path} 不存在")
        return None
    except Exception as e:
        logger.error(f"读取文件时出错: {e}")
        return None
