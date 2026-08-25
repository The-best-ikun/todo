# -*- coding: utf-8 -*-
"""
AutostartManager：负责在 Windows 启动文件夹创建/删除快捷方式以实现开机自启
使用 pywin32 的 win32com.client.Dispatch("WScript.Shell") 创建 .lnk 快捷方式
兼容开发环境和 PyInstaller 打包后的运行：
- 开发环境：Target 指向 pythonw.exe，Arguments 为 main.py 的绝对路径
- 打包后：sys.frozen == True 时，Target 指向可执行文件（sys.executable），无 Arguments
"""

import os
import sys

try:
    import win32com.client
except Exception:
    win32com = None  # 在没有 pywin32 时，相关方法会抛出异常

from typing import Optional


class AutostartManager:
    """
    处理开机自启快捷方式的创建、删除与检查
    """
    def __init__(self, shortcut_name: str = "TodoTool.lnk"):
        # 启动文件夹路径（Roaming AppData 下）
        self.startup_path = os.path.join(
            os.getenv("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        self.shortcut_path = os.path.join(self.startup_path, shortcut_name)

    def _get_target_and_args(self) -> (str, str):
        """
        返回 (target, arguments)：
        - 如果是 PyInstaller 打包后（sys.frozen），使用可执行文件作为 target
        - 否则尝试使用 pythonw.exe（如果存在）作为 target，arguments 为 main.py 的完整路径
        """
        if getattr(sys, "frozen", False):
            # 打包模式下，直接执行 exe
            target = sys.executable
            args = ""
            return target, args

        # 开发模式：尝试查找 pythonw.exe
        python_exec = sys.executable  # 可能是 python.exe
        python_dir = os.path.dirname(python_exec)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        if os.path.exists(pythonw):
            target = pythonw
        else:
            # 回退到当前 python 可执行文件（会弹出控制台）
            target = python_exec

        # main.py 的绝对路径（假设位于项目根或与本模块同层）
        # 尝试查找 main.py 相对当前工作目录或脚本目录
        candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        if not os.path.exists(candidate):
            candidate = os.path.abspath(os.path.join(os.getcwd(), "main.py"))
        args = f'"{candidate}"'
        return target, args

    def is_enabled(self) -> bool:
        """
        检查启动目录中是否存在快捷方式且指向我们期望的目标
        """
        if not os.path.exists(self.shortcut_path):
            return False

        if win32com is None:
            # 无法核验内容，但文件存在则认为已启用
            return True

        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(self.shortcut_path)
            target, args = self._get_target_and_args()
            # 只粗略核验 Target 是否一致（忽略 args 差异）
            path_ok = os.path.abspath(shortcut.TargetPath) == os.path.abspath(target)
            return path_ok
        except Exception:
            return False

    def enable(self) -> bool:
        """
        创建快捷方式以启用开机自启。返回是否成功。
        """
        if win32com is None:
            raise RuntimeError("pywin32 未安装，无法创建 Windows 快捷方式（pip install pywin32）")

        os.makedirs(self.startup_path, exist_ok=True)
        target, args = self._get_target_and_args()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(self.shortcut_path)
            shortcut.TargetPath = target
            # Arguments 只有在开发模式下才有意义；打包后为空
            if args:
                shortcut.Arguments = args
            # 工作目录：打包模式=exe所在目录；开发模式=main.py 所在目录
            if getattr(sys, "frozen", False):
                shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            else:
                shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
            shortcut.IconLocation = target  # 使用目标可执行程序的图标
            shortcut.Save()
            return True
        except Exception as e:
            raise RuntimeError(f"创建快捷方式失败：{e}")

    def disable(self) -> bool:
        """
        删除快捷方式以取消开机自启。返回是否成功。
        """
        try:
            if os.path.exists(self.shortcut_path):
                os.remove(self.shortcut_path)
            return True
        except Exception as e:
            raise RuntimeError(f"删除快捷方式失败：{e}")