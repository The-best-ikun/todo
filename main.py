# -*- coding: utf-8 -*-
"""
程序入口
启动主窗口（MainWindow），桌面卡片根据设置自动显示
可通过 PyInstaller 打包为单文件 exe
"""

import sys
import os
from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from icon_utils import get_app_icon, apply_theme_stylesheet


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(get_app_icon())
    app.setApplicationName("待办管家")
    app.setOrganizationName("TodoApp")

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("待办管家")
        except Exception:
            pass

    from todo_model import TodoModel
    model = TodoModel()
    theme = model.get_theme()

    apply_theme_stylesheet(app, theme)

    w = MainWindow()
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()