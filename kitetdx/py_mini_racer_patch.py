"""
py_mini_racer 兼容性补丁

在 Mac M1/M2/M3 芯片上，py_mini_racer 可能存在兼容性问题。
本模块使用 quickjs 作为替代方案，提供与 py_mini_racer.MiniRacer 兼容的接口。

使用方法:
    在项目入口处（如 __init__.py）导入此模块即可自动应用补丁：
    
    import kitetdx.py_mini_racer_patch  # 自动应用 monkey patch

这样 akshare 等依赖 py_mini_racer 的库将自动使用 quickjs 替代。
"""

import json
import sys

try:
    import quickjs
except ImportError:
    raise ImportError(
        "quickjs is required for M1 compatibility. "
        "Please install it: pip install quickjs"
    )


class MiniRacer:
    """
    py_mini_racer.MiniRacer 的 quickjs 兼容实现
    
    提供与原始 MiniRacer 相同的 eval() 和 call() 接口。
    """
    
    def __init__(self):
        self._context = quickjs.Context()
    
    def _convert_result(self, result):
        """
        将 quickjs 返回的对象转换为 Python 原生类型
        
        quickjs 返回 _quickjs.Object 类型，需要通过 JSON 序列化转换为 Python 对象
        """
        if result is None:
            return None
        
        # 基础类型直接返回
        if isinstance(result, (bool, int, float, str)):
            return result
        
        # 对于 quickjs.Object 类型，使用 JSON.stringify 转换
        try:
            # 使用 JavaScript 的 JSON.stringify 将对象转为字符串
            json_str = self._context.eval(f"JSON.stringify({self._last_expr})")
            if json_str and isinstance(json_str, str):
                return json.loads(json_str)
        except Exception:
            pass
        
        # 如果转换失败，返回原始结果
        return result
    
    def eval(self, code: str):
        """
        执行 JavaScript 代码
        
        Args:
            code: JavaScript 代码字符串
            
        Returns:
            执行结果
        """
        result = self._context.eval(code)
        
        # 基础类型直接返回
        if result is None or isinstance(result, (bool, int, float, str)):
            return result
        
        # 尝试将复杂对象转换为 Python 类型
        try:
            # 将代码包装后再次执行以获取 JSON 字符串
            # 这里需要判断代码是表达式还是语句
            json_str = self._context.eval(f"JSON.stringify(({code}))")
            if json_str and isinstance(json_str, str):
                return json.loads(json_str)
        except Exception:
            pass
        
        return result
    
    def call(self, func_name: str, *args):
        """
        调用已定义的 JavaScript 函数
        
        Args:
            func_name: 函数名
            *args: 传递给函数的参数
            
        Returns:
            函数执行结果（转换为 Python 原生类型）
        """
        # 将 Python 参数转换为 JavaScript 调用
        js_args = []
        for arg in args:
            if isinstance(arg, str):
                # 转义字符串中的特殊字符
                escaped = arg.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                js_args.append(f'"{escaped}"')
            elif isinstance(arg, bool):
                js_args.append('true' if arg else 'false')
            elif isinstance(arg, (int, float)):
                js_args.append(str(arg))
            elif arg is None:
                js_args.append('null')
            else:
                # 对于其他类型，尝试转换为字符串
                escaped = str(arg).replace('\\', '\\\\').replace('"', '\\"')
                js_args.append(f'"{escaped}"')
        
        js_call = f"{func_name}({', '.join(js_args)})"
        result = self._context.eval(js_call)
        
        # 基础类型直接返回
        if result is None or isinstance(result, (bool, int, float, str)):
            return result
        
        # 对于复杂对象，使用 JSON.stringify 转换为 Python 对象
        try:
            json_str = self._context.eval(f"JSON.stringify({js_call})")
            if json_str and isinstance(json_str, str):
                return json.loads(json_str)
        except Exception:
            pass
        
        return result


class _FakePyMiniRacer:
    """
    模拟 py_mini_racer 模块的类
    """
    MiniRacer = MiniRacer


# 应用 monkey patch
# 创建一个假的 py_mini_racer 模块并注入到 sys.modules
_fake_module = _FakePyMiniRacer()
sys.modules['py_mini_racer'] = _fake_module

print("[py_mini_racer_patch] Successfully patched py_mini_racer with quickjs backend")
