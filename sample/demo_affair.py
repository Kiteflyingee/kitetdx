import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kitetdx import Affair

def main():
    print("-" * 30)
    print("测试 Affair (财务数据)...")

    # 1. 获取远程文件列表
    print("\n[1] 获取远程财务文件列表:")
    try:
        files = Affair.files()
        if files:
            print(f"获取成功，共 {len(files)} 个文件")
            print("最新文件:", files[-1])
        else:
            print("未获取到文件列表")
    except Exception as e:
        print(f"获取失败: {e}")

    # 2. 提示下载 (不实际执行以节省时间/流量)
    print("\n[2] 下载示例 (代码演示):")
    print("Affair.fetch(downdir='tmp', filename='gpcw20230930.zip')")

if __name__ == "__main__":
    main()
