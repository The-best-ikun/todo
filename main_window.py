# -*- coding: utf-8 -*-
"""
MainWindow：应用主窗口，标准窗口界面
- 工具栏、状态栏
- 完整的待办管理界面
- 可切换桌面卡片显示
"""

from datetime import datetime
import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QCheckBox, QDialog,
    QMessageBox, QMenu, QToolBar, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize
from PySide6.QtGui import (
    QAction, QColor, QCursor
)

from todo_model import TodoModel
from todo_dialogs import AddTodoDialog
from icon_utils import (
    get_app_icon, get_gear_icon, get_add_icon, get_edit_icon,
    get_delete_icon, get_list_icon, get_empty_icon, get_checked_icon,
    get_check_icon, get_clock_icon, get_sun_icon, get_moon_icon,
    get_todo_item_icons, get_deadline_icon,
    get_checkbox_empty_icon, get_checkbox_checked_icon, get_resource_dir,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("待办管家")
        self.setWindowIcon(get_app_icon())
        self.resize(900, 600)

        self.model = TodoModel()
        self._card_widget = None
        self._quitting = False
        self._current_filter = "pending"
        self._showing_from_tray = False

        self._build_ui()
        self._setup_tray()
        self._setup_timer()
        self._restore_geometry()
        self._refresh_list()
        self._update_stats()

        self._fix_taskbar_icon()

        self.model.todos_changed.connect(self._on_todos_changed)

        if self.model.is_card_visible():
            self._show_card()

    def _on_todos_changed(self):
        """当 TodoModel 数据变化（增/删/改）时，刷新主窗口列表与统计，同时刷新卡片"""
        self._refresh_list()
        self._update_stats()
        if self._card_widget and hasattr(self._card_widget, "refresh"):
            self._card_widget.refresh()

    def _build_ui(self):
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        from PySide6.QtGui import QShortcut, QKeySequence

        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_todo)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self.hide)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self._quit_app)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.open_settings)
        QShortcut(QKeySequence("F5"), self, activated=self._refresh_list)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, activated=self._toggle_theme)

    def _create_tool_bar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        theme = self.model.get_theme()

        self._act_add_toolbar = QAction(get_add_icon(24, theme=theme), "添加待办", self)
        self._act_add_toolbar.triggered.connect(self.add_todo)
        toolbar.addAction(self._act_add_toolbar)

        toolbar.addSeparator()

        self._act_card_toolbar = QAction(get_list_icon(24, theme=theme), "桌面卡片", self)
        self._act_card_toolbar.setCheckable(True)
        self._act_card_toolbar.setChecked(self.model.is_card_visible())
        self._act_card_toolbar.triggered.connect(self._toggle_card)
        toolbar.addAction(self._act_card_toolbar)

        toolbar.addSeparator()

        self._act_theme_toolbar = QAction(self._get_theme_icon(), "切换主题", self)
        self._act_theme_toolbar.triggered.connect(self._toggle_theme)
        toolbar.addAction(self._act_theme_toolbar)

        toolbar.addSeparator()

        self._act_settings_toolbar = QAction(get_gear_icon(24, theme=theme), "设置", self)
        self._act_settings_toolbar.triggered.connect(self.open_settings)
        toolbar.addAction(self._act_settings_toolbar)

    def _get_theme_icon(self):
        theme = self.model.get_theme()
        if theme == "light":
            return get_moon_icon(24, theme=theme)
        else:
            return get_sun_icon(24, theme=theme)

    def _toggle_theme(self):
        current = self.model.get_theme()
        new_theme = "light" if current == "dark" else "dark"
        self.model.set_theme(new_theme)
        self._apply_theme()

    def _apply_theme(self):
        theme = self.model.get_theme()
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()

        from icon_utils import apply_theme_stylesheet
        apply_theme_stylesheet(app, theme)

        self._act_add_toolbar.setIcon(get_add_icon(24, theme=theme))
        self._act_card_toolbar.setIcon(get_list_icon(24, theme=theme))
        self._act_settings_toolbar.setIcon(get_gear_icon(24, theme=theme))
        self._act_theme_toolbar.setIcon(self._get_theme_icon())
        self._act_theme_toolbar.setToolTip("切换到" + ("日间模式" if theme == "light" else "夜间模式"))

        self._refresh_nav_icons()

        self.btn_add_top.setIcon(get_add_icon(20, theme=theme))

        self.empty_icon_label.setPixmap(get_empty_icon(80, theme=theme).pixmap(80, 80))

        self._refresh_list()

        if self._card_widget and hasattr(self._card_widget, 'apply_theme'):
            self._card_widget.apply_theme()

    def _refresh_nav_icons(self):
        theme = self.model.get_theme()
        for btn, filt in self._nav_group:
            if filt == "all":
                btn.setIcon(get_list_icon(20, theme=theme))
            elif filt == "pending":
                btn.setIcon(get_check_icon(20, theme=theme))
            elif filt == "done":
                btn.setIcon(get_checked_icon(20, theme=theme))

    def _get_base_dir(self):
        return get_resource_dir()

    def _create_central_widget(self):
        central = QWidget()
        central.setObjectName("MainCentralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(10)

        header = QFrame()
        header.setObjectName("HeaderFrame")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        title_lbl = QLabel("待办管家")
        title_lbl.setObjectName("HeaderTitle")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        self.lbl_stats = QLabel()
        self.lbl_stats.setObjectName("StatsLabel")
        header_layout.addWidget(self.lbl_stats)

        root.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        side_panel = self._create_side_panel()
        content_layout.addWidget(side_panel)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)

        list_header = QHBoxLayout()
        list_header.setSpacing(8)
        lbl_list_title = QLabel("待办列表")
        lbl_list_title.setObjectName("ListTitle")
        list_header.addWidget(lbl_list_title)
        list_header.addStretch()

        self.btn_add_top = QPushButton()
        self.btn_add_top.setObjectName("SmallAddButton")
        theme = self.model.get_theme()
        self.btn_add_top.setIcon(get_add_icon(20, theme=theme))
        self.btn_add_top.setIconSize(QSize(14, 14))
        self.btn_add_top.setText("新建")
        self.btn_add_top.clicked.connect(self.add_todo)
        list_header.addWidget(self.btn_add_top)

        list_layout.addLayout(list_header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("MainTodoList")
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_layout.addWidget(self.list_widget, 1)

        self.empty_widget = QWidget()
        self.empty_widget.setObjectName("EmptyWidget")
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        self.empty_icon_label = QLabel()
        self.empty_icon_label.setPixmap(get_empty_icon(80, theme=theme).pixmap(80, 80))
        self.empty_icon_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_icon_label)
        empty_text = QLabel("暂无待办事项")
        empty_text.setObjectName("EmptyText")
        empty_text.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_text)
        empty_hint = QLabel('点击上方"新建"按钮添加第一个待办')
        empty_hint.setObjectName("EmptyHint")
        empty_hint.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_hint)
        self.empty_widget.setVisible(False)
        list_layout.addWidget(self.empty_widget, 1)

        content_layout.addWidget(list_container, 1)
        root.addLayout(content_layout, 1)

    def _create_side_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("SidePanel")
        panel.setFixedWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        lbl_nav = QLabel("导航")
        lbl_nav.setObjectName("NavTitle")
        layout.addWidget(lbl_nav)

        self._nav_group = []
        theme = self.model.get_theme()

        for name, filt in [
            ("待完成", "pending"),
            ("已完成", "done"),
            ("全部", "all"),
        ]:
            btn = QPushButton()
            btn.setObjectName("NavButton")
            btn.setText(f"  {name}")
            if filt == "all":
                btn.setIcon(get_list_icon(20, theme=theme))
            elif filt == "pending":
                btn.setIcon(get_check_icon(20, theme=theme))
            elif filt == "done":
                btn.setIcon(get_checked_icon(20, theme=theme))
            btn.setIconSize(QSize(18, 18))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked=False, f=filt, b=btn: self._set_filter(f))
            layout.addWidget(btn)
            self._nav_group.append((btn, filt))

        layout.addStretch()

        lbl_info = QLabel("提示")
        lbl_info.setObjectName("NavTitle")
        layout.addWidget(lbl_info)

        tip_text = QLabel("双击列表项可快速编辑待办内容")
        tip_text.setObjectName("TipText")
        tip_text.setWordWrap(True)
        layout.addWidget(tip_text)

        return panel

    def _create_status_bar(self):
        sb = QStatusBar()
        sb.setObjectName("MainStatusBar")
        self.setStatusBar(sb)

        self._status_msg = QLabel("就绪")
        sb.addWidget(self._status_msg, 1)

        self._status_time = QLabel("")
        sb.addPermanentWidget(self._status_time)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start()
        self._update_clock()

    def _update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._status_time.setText(now)

    def _setup_tray(self):
        from PySide6.QtWidgets import QSystemTrayIcon
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(get_app_icon())
        self._tray_icon.setToolTip("待办管家")

        menu = QMenu()

        act_show = QAction("显示主窗口", self)
        act_show.triggered.connect(self._show_and_raise)
        menu.addAction(act_show)

        act_toggle_card = QAction("桌面卡片", self)
        act_toggle_card.setCheckable(True)
        act_toggle_card.setChecked(self.model.is_card_visible())
        act_toggle_card.triggered.connect(self._toggle_card)
        self._act_tray_card = act_toggle_card
        menu.addAction(act_toggle_card)

        menu.addSeparator()

        act_settings = QAction("设置", self)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        menu.addSeparator()

        act_quit = QAction("退出", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)

        self._tray_icon.setContextMenu(menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _on_tray_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_and_raise()

    def _show_and_raise(self):
        self._showing_from_tray = True
        self.setWindowState(Qt.WindowNoState)
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(200, self._clear_showing_flag)

    def _clear_showing_flag(self):
        self._showing_from_tray = False

    def _fix_taskbar_icon(self):
        import sys
        if sys.platform != "win32":
            return

        import ctypes

        hwnd = int(self.winId())
        if not hwnd:
            return

        app_icon = get_app_icon()

        try:
            hicon = app_icon.pixmap(64, 64).toHICON()
            if hicon:
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)
                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)
        except Exception:
            pass

        try:
            GCL_HICON = -14
            GCL_HICONSM = -34
            hicon_big = app_icon.pixmap(32, 32).toHICON()
            hicon_small = app_icon.pixmap(16, 16).toHICON()
            if hicon_big:
                ctypes.windll.user32.SetClassLongW(hwnd, GCL_HICON, hicon_big)
            if hicon_small:
                ctypes.windll.user32.SetClassLongW(hwnd, GCL_HICONSM, hicon_small)
        except Exception:
            pass

    def _setup_timer(self):
        interval_min = int(self.model.get_settings().get("check_interval_min", 1))
        self._timer = QTimer(self)
        self._timer.setInterval(max(1000, interval_min * 60 * 1000))
        self._timer.timeout.connect(self.check_reminders)
        self._timer.start()

    def _restore_geometry(self):
        geom = self.model.get_main_window_geometry()
        if geom:
            self.resize(geom.get("w", 900), geom.get("h", 600))
            self.move(geom.get("x", 100), geom.get("y", 100))
        else:
            screen = self.screen().availableGeometry() if self.screen() else None
            if screen:
                self.move((screen.width() - self.width()) // 2,
                          (screen.height() - self.height()) // 2)

    def _save_geometry(self):
        g = self.geometry()
        self.model.set_main_window_geometry(g.x(), g.y(), g.width(), g.height())

    def _toggle_card(self, checked):
        self.model.set_card_visible(checked)
        if checked:
            self._show_card()
        else:
            self._hide_card()

        if hasattr(self, '_act_card_toolbar'):
            self._act_card_toolbar.blockSignals(True)
            self._act_card_toolbar.setChecked(checked)
            self._act_card_toolbar.blockSignals(False)
        if hasattr(self, '_act_tray_card'):
            self._act_tray_card.blockSignals(True)
            self._act_tray_card.setChecked(checked)
            self._act_tray_card.blockSignals(False)

    def _show_card(self):
        if self._card_widget is None:
            from desktop_card import DesktopCardWidget
            self._card_widget = DesktopCardWidget(self.model)
            self._card_widget.settings_requested.connect(self.open_settings)
            self._card_widget.close_requested.connect(lambda: self._toggle_card(False))
            self._card_widget.destroyed.connect(self._on_card_destroyed)
        self._card_widget.show()
        self._card_widget.raise_()

    def _hide_card(self):
        if self._card_widget:
            self._card_widget.hide()

    def _on_card_destroyed(self):
        self._card_widget = None

    def _set_filter(self, filter_type):
        self._current_filter = filter_type
        for btn, filt in self._nav_group:
            btn.setProperty("active", "true" if filt == filter_type else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._refresh_list()

    def _get_filtered_todos(self):
        todos = self.model.get_todos()
        filt = getattr(self, '_current_filter', 'all')
        if filt == 'pending':
            return [t for t in todos if not t.get("done")]
        elif filt == 'done':
            return [t for t in todos if t.get("done")]
        return todos

    def _refresh_list(self):
        self.list_widget.clear()
        todos = self._get_filtered_todos()

        if not todos:
            self.list_widget.setVisible(False)
            self.empty_widget.setVisible(True)
            filt = getattr(self, '_current_filter', 'all')
            if filt == 'pending':
                self.findChild(QLabel, "EmptyText").setText("没有待完成的待办")
                self.findChild(QLabel, "EmptyHint").setText("去休息一下吧")
            elif filt == 'done':
                self.findChild(QLabel, "EmptyText").setText("暂无已完成的待办")
                self.findChild(QLabel, "EmptyHint").setText("完成待办后会显示在这里")
            else:
                self.findChild(QLabel, "EmptyText").setText("暂无待办事项")
                self.findChild(QLabel, "EmptyHint").setText('点击上方"新建"按钮添加第一个待办')
            self._update_stats()
            return

        self.list_widget.setVisible(True)
        self.empty_widget.setVisible(False)

        all_todos = self.model.get_todos()
        for idx, item in enumerate(todos):
            real_idx = all_todos.index(item) if item in all_todos else idx
            w = self._create_todo_item_widget(item, real_idx)
            li = QListWidgetItem(self.list_widget)
            li.setSizeHint(w.sizeHint())
            li.setData(Qt.UserRole, int(real_idx))
            self.list_widget.addItem(li)
            self.list_widget.setItemWidget(li, w)

        self._update_stats()

    def _create_todo_item_widget(self, todo: dict, index: int) -> QWidget:
        container = QWidget()
        container.setProperty("class", "todo-item")
        container.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        theme = self.model.get_theme()
        icons = get_todo_item_icons(theme)

        is_done = bool(todo.get("done", False))
        chk_btn = QPushButton()
        chk_btn.setFixedSize(24, 24)
        chk_btn.setCursor(QCursor(Qt.PointingHandCursor))
        chk_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        if is_done:
            chk_btn.setIcon(get_checkbox_checked_icon(24, theme=theme))
        else:
            chk_btn.setIcon(get_checkbox_empty_icon(24, theme=theme))
        chk_btn.setIconSize(QSize(20, 20))
        chk_btn.clicked.connect(lambda _=False, i=index: self._on_toggle_done(i))
        layout.addWidget(chk_btn)

        vbox = QVBoxLayout()
        vbox.setSpacing(4)

        title_text = todo.get("title", "")
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("todo-title")
        lbl_title.setProperty("class", "todo-title")
        lbl_title.setProperty("done", "true" if todo.get("done") else "false")
        lbl_title.setWordWrap(True)
        if todo.get("done"):
            lbl_title.setText(f"<s>{title_text}</s>")
        vbox.addWidget(lbl_title)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        remind_enabled = bool(todo.get("remind_enabled", True))
        remind_dt_str = todo.get("remind_datetime", "")
        time_str = todo.get("time", "")
        if remind_dt_str:
            try:
                dt = datetime.strptime(remind_dt_str, "%Y-%m-%d %H:%M")
                time_str = dt.strftime("%m-%d %H:%M")
            except Exception:
                pass

        if remind_enabled and time_str:
            time_icon = QLabel()
            time_icon.setPixmap(get_clock_icon(16, color=icons["clock"], theme=theme).pixmap(16, 16))
            bottom_row.addWidget(time_icon)

            lbl_time = QLabel(time_str)
            lbl_time.setObjectName("todo-time")
            lbl_time.setProperty("class", "todo-time")
            lbl_time.setProperty("done", "true" if todo.get("done") else "false")
            lbl_time.setProperty("pending", "false" if todo.get("done") else "true")
            bottom_row.addWidget(lbl_time)

        deadline_text = self.model.get_deadline_text(todo)
        if deadline_text:
            deadline_status = self.model.get_deadline_status(todo)
            dl_icon = QLabel()
            dl_icon.setPixmap(
                get_deadline_icon(14, theme=theme).pixmap(14, 14)
            )
            bottom_row.addWidget(dl_icon)
            lbl_dl = QLabel(f"截止: {deadline_text}")
            lbl_dl.setObjectName("todo-deadline")
            lbl_dl.setProperty("class", "todo-deadline")
            lbl_dl.setProperty("status", deadline_status)
            bottom_row.addWidget(lbl_dl)

        if remind_enabled:
            remind_before = int(todo.get("remind_before_min", 0))
            if remind_before > 0:
                lbl_remind = QLabel(f"提前{remind_before}分")
                lbl_remind.setObjectName("todo-remind")
                lbl_remind.setProperty("class", "todo-remind")
                lbl_remind.setProperty("done", "true" if todo.get("done") else "false")
                bottom_row.addWidget(lbl_remind)

        bottom_row.addStretch()
        vbox.addLayout(bottom_row)
        layout.addLayout(vbox, 1)

        btn_container = QVBoxLayout()
        btn_container.setSpacing(6)

        edit_btn = QPushButton()
        edit_btn.setIcon(get_edit_icon(22, color=icons["edit"], theme=theme))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setFixedSize(28, 28)
        edit_btn.setCursor(QCursor(Qt.PointingHandCursor))
        edit_btn.setToolTip("编辑")
        edit_btn.clicked.connect(lambda _, i=index: self._on_edit(i))
        btn_container.addWidget(edit_btn)

        del_btn = QPushButton()
        del_btn.setIcon(get_delete_icon(22, color=icons["delete"], theme=theme))
        del_btn.setIconSize(QSize(14, 14))
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(QCursor(Qt.PointingHandCursor))
        del_btn.setToolTip("删除")
        del_btn.clicked.connect(lambda _, i=index: self._on_delete(i))
        btn_container.addWidget(del_btn)

        layout.addLayout(btn_container)

        container.setContextMenuPolicy(Qt.CustomContextMenu)

        def ctx_menu(point):
            menu = QMenu(container)
            menu.addAction("编辑", lambda i=index: self._on_edit(i))
            menu.addSeparator()
            menu.addAction("删除", lambda i=index: self._on_delete(i))
            menu.exec(container.mapToGlobal(point))

        container.customContextMenuRequested.connect(ctx_menu)

        return container

    def _update_stats(self):
        todos = self.model.get_todos()
        total = len(todos)
        pending = sum(1 for t in todos if not t.get("done"))
        done = total - pending
        self.lbl_stats.setText(f"共 {total} 项 | 待完成 {pending} | 已完成 {done}")

    def _on_toggle_done(self, index: int):
        todos = self.model.get_todos()
        if 0 <= index < len(todos):
            done = bool(todos[index].get("done"))
            new_done = not done
            self.model.update_todo(index, done=new_done)
            if not new_done:
                self.model.update_todo(index, notified=False)
            msg = "已标记为已完成" if new_done else "已恢复为待办"
            self._set_status(msg)
        else:
            self._set_status("待办不存在或已删除")
        self._refresh_list()

    def _on_item_double_clicked(self, item: QListWidgetItem):
        index_raw = item.data(Qt.UserRole)
        if index_raw is None:
            return
        try:
            index = int(index_raw)
        except (TypeError, ValueError):
            return
        self._on_edit(index)

    def _on_edit(self, index: int):
        todos = self.model.get_todos()
        if 0 <= index < len(todos):
            todo = todos[index]
            dlg = AddTodoDialog(self, todo_data=todo)
            if dlg.exec() == QDialog.Accepted:
                title, time_str, deadline, remind_before, remind_enabled, remind_datetime = dlg.get_data()
                if not title:
                    QMessageBox.warning(self, "输入错误", "请填写待办标题")
                    return
                try:
                    datetime.strptime(time_str, "%H:%M")
                except Exception:
                    QMessageBox.warning(self, "输入错误", "时间格式需为 HH:MM")
                    return
                self.model.update_todo(
                    index, title=title, time=time_str,
                    deadline=deadline, deadline_notified=False,
                    notified=False, remind_before_min=int(remind_before),
                    remind_enabled=remind_enabled, remind_datetime=remind_datetime
                )
                self._refresh_list()
                self._set_status("已保存修改")

    def _on_delete(self, index: int):
        reply = QMessageBox.question(
            self, "删除确认", "确定删除该待办吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.model.remove_todo(index)
            self._refresh_list()
            self._set_status("已删除待办")

    def add_todo(self):
        dlg = AddTodoDialog(self)
        if dlg.exec() == QDialog.Accepted:
            title, time_str, deadline, remind_before, remind_enabled, remind_datetime = dlg.get_data()
            if not title:
                QMessageBox.warning(self, "输入错误", "请填写待办标题")
                return
            try:
                datetime.strptime(time_str, "%H:%M")
            except Exception:
                QMessageBox.warning(self, "输入错误", "时间格式需为 HH:MM")
                return
            self.model.add_todo(title, time_str, deadline=deadline, remind_before_min=remind_before, remind_enabled=remind_enabled, remind_datetime=remind_datetime)
            self._refresh_list()
            self._set_status("已添加待办")

    def open_settings(self):
        from settings_dialog import SettingsDialog
        dlg = SettingsDialog(self, model=self.model)
        if dlg.exec() == QDialog.Accepted:
            interval_min = int(self.model.get_settings().get("check_interval_min", 1))
            self._timer.setInterval(max(1000, interval_min * 60 * 1000))

            card_visible = self.model.is_card_visible()
            self._toggle_card(card_visible)

            self._apply_theme()
            if self._card_widget and hasattr(self._card_widget, 'apply_theme'):
                self._card_widget.apply_theme()

            self._set_status("设置已更新")

    def check_reminders(self):
        now = datetime.now()
        now_dt_str = now.strftime("%Y-%m-%d %H:%M")
        now_time_str = now.strftime("%H:%M")

        todos = self.model.get_todos()

        for idx, t in enumerate(todos):
            if t.get("done"):
                continue

            if not bool(t.get("remind_enabled", True)):
                continue

            item_remind_dt_str = t.get("remind_datetime", "")
            item_time_str = t.get("time", "")

            target_dt = None
            display_time = item_time_str or item_remind_dt_str

            if item_remind_dt_str:
                try:
                    target_dt = datetime.strptime(item_remind_dt_str, "%Y-%m-%d %H:%M")
                    display_time = target_dt.strftime("%m-%d %H:%M")
                except Exception:
                    target_dt = None

            if target_dt is None and item_time_str and ":" in item_time_str:
                try:
                    item_h, item_m = map(int, item_time_str.split(":"))
                    target_dt = now.replace(hour=item_h, minute=item_m, second=0, microsecond=0)
                except Exception:
                    target_dt = None

            if target_dt is None:
                continue

            should_notify = False
            notify_kind = "due"

            if t.get("notified", False):
                continue

            now_trunc = now.replace(second=0, microsecond=0)
            if now_trunc == target_dt:
                should_notify = True
                notify_kind = "due"

            remind_before = int(t.get("remind_before_min", 0))
            if remind_before > 0 and not should_notify:
                try:
                    diff = target_dt - now
                    total_seconds = int(diff.total_seconds())
                    total_minutes = total_seconds // 60
                    if 0 < total_minutes <= remind_before and total_seconds % 60 <= 59:
                        should_notify = True
                        notify_kind = "early"
                except Exception:
                    pass

            if should_notify:
                title = t.get("title", "待办")
                if notify_kind == "due":
                    time_info = f"【待办提醒】{title}\n时间到了！({display_time})"
                else:
                    time_info = f"【待办提醒】{title}\n将在 {display_time} 提醒"
                try:
                    from PySide6.QtWidgets import QSystemTrayIcon
                    self._tray_icon.showMessage(
                        "待办提醒",
                        time_info,
                        QSystemTrayIcon.MessageIcon.Information,
                        12000
                    )
                except Exception:
                    pass
                self.model.update_todo(idx, notified=True)

        pending_deadlines = self.model.get_pending_deadlines()
        for idx in pending_deadlines:
            t = todos[idx]
            title = t.get("title", "待办")
            dl_text = self.model.get_deadline_text(t)
            try:
                from PySide6.QtWidgets import QSystemTrayIcon
                self._tray_icon.showMessage(
                    "待办截止提醒",
                    f"\"{title}\" 的截止时间已到！({dl_text})",
                    QSystemTrayIcon.MessageIcon.Warning,
                    15000
                )
            except Exception:
                pass
            self.model.mark_deadline_notified(idx)
            self._set_status(f"截止提醒: {title}")

    def _show_about(self):
        QMessageBox.about(
            self, "关于待办管家",
            "<h3>待办管家 v1.0</h3>"
            "<p>一款简洁的桌面待办提醒工具</p>"
            "<p>技术栈：Python 3 + PySide6</p>"
            "<p>支持桌面常驻卡片、系统通知、开机自启等功能。</p>"
        )

    def _set_status(self, msg):
        self._status_msg.setText(msg)

    def _quit_app(self):
        self._quitting = True
        self._save_geometry()
        try:
            self._tray_icon.hide()
        except Exception:
            pass
        if self._card_widget:
            self._card_widget.close()
        self.close()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def closeEvent(self, event):
        self._save_geometry()
        if self._card_widget:
            self._card_widget.close()
        if self._quitting:
            event.accept()
        else:
            self.hide()
            event.ignore()

    def changeEvent(self, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and self._showing_from_tray:
                self.setWindowState(Qt.WindowNoState)
        super().changeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self._fix_taskbar_icon()