# -*- coding: utf-8 -*-
"""
DesktopCardWidget：桌面常驻小卡片（可选功能）
- 无边框、半透明、置顶
- 拖拽移动、边缘缩放
- 轻量级待办展示面板
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QCheckBox, QDialog,
    QMessageBox, QMenu
)
from PySide6.QtCore import Qt, QPoint, QSize, QRect, QEvent, Signal, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPainterPath, QCursor,
    QPixmap, QLinearGradient, QRadialGradient
)

from todo_model import TodoModel
from todo_dialogs import AddTodoDialog
from icon_utils import (
    get_gear_icon, get_add_icon, get_empty_icon, get_clock_icon,
    get_edit_icon, get_delete_icon, get_todo_item_icons,
    get_deadline_icon, get_checkbox_empty_icon, get_checkbox_checked_icon,
    get_close_icon,
)

RESIZE_MARGIN = 10


class DesktopCardWidget(QWidget):
    settings_requested = Signal()
    close_requested = Signal()

    def __init__(self, model: TodoModel):
        super().__init__()
        self.setObjectName("DesktopCard")
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setMinimumSize(240, 280)

        self._drag_active = False
        self._drag_pos = QPoint()
        self._start_geom = None

        self._resize_active = False
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geom = None

        self.model = model

        self._init_ui()
        self._install_event_filter_recursive(self)
        self._refresh_list()
        self._restore_geometry()
        self._update_cursor_for_pos(self.mapFromGlobal(self.cursor().pos()))

        self.model.todos_changed.connect(self.refresh)

    def refresh(self):
        """供外部（主窗口/model 信号）调用的刷新入口"""
        self._refresh_list()

    def _get_theme_colors(self):
        theme = self.model.get_theme()
        if theme == "light":
            return {
                "bg": QColor(255, 255, 255, int(0.94 * 255)),
                "border": QColor(0, 0, 0, int(0.08 * 255)),
                "empty_primary": "#777",
                "empty_hint": "#aaa",
                "time_done": "#999",
                "time_pending": "#2979ff",
                "edit_icon": QColor(100, 100, 110),
                "delete_icon": QColor(160, 90, 90),
                "btn_hover": "rgba(0,0,0,0.08)",
                "btn_del_hover": "rgba(255,80,80,0.2)",
                "title_color": "#1a1a2e",
                "title_done": "#999",
                "top_bar_icon": QColor(70, 70, 80),
                "settings_icon": QColor(80, 80, 90),
            }
        else:
            return {
                "bg": QColor(40, 40, 40, int(0.92 * 255)),
                "border": QColor(255, 255, 255, int(0.06 * 255)),
                "empty_primary": "#888",
                "empty_hint": "#666",
                "time_done": "#666",
                "time_pending": "#4fc3f7",
                "edit_icon": QColor(200, 200, 200),
                "delete_icon": QColor(200, 110, 110),
                "btn_hover": "rgba(255,255,255,0.1)",
                "btn_del_hover": "rgba(255,80,80,0.3)",
                "title_color": "#f0f0f0",
                "title_done": "#6b7280",
                "top_bar_icon": QColor(230, 230, 230),
                "settings_icon": QColor(200, 200, 200),
            }

    def apply_theme(self):
        theme = self.model.get_theme()
        colors = self._get_theme_colors()

        self.clock_icon_label.setPixmap(
            get_clock_icon(22, color=colors["top_bar_icon"], theme=theme).pixmap(22, 22)
        )
        self.settings_btn.setIcon(
            get_gear_icon(24, color=colors["settings_icon"], theme=theme)
        )
        self.close_btn.setIcon(get_close_icon(24, theme=theme))
        self.add_btn.setIcon(get_add_icon(24, theme=theme))

        self.empty_icon_label.setPixmap(
            get_empty_icon(56, theme=theme).pixmap(56, 56)
        )

        empty_colors = self._get_theme_colors()
        self.empty_text.setStyleSheet(
            f"color: {empty_colors['empty_primary']}; font-size: 13px;"
        )
        self.empty_hint.setStyleSheet(
            f"color: {empty_colors['empty_hint']}; font-size: 11px;"
        )

        self._refresh_list()
        self.update()

    def _restore_geometry(self):
        geom = self.model.get_window_geometry()
        if geom:
            self.resize(geom.get("w", 300), geom.get("h", 400))
            self.move(geom.get("x", 100), geom.get("y", 100))
        else:
            screen = self.screen().availableGeometry() if self.screen() else None
            if screen:
                self.move(screen.width() - self.width() - 40, 80)

    def _save_geometry(self):
        g = self.geometry()
        self.model.set_window_geometry(g.x(), g.y(), g.width(), g.height())

    def _init_ui(self):
        theme = self.model.get_theme()
        colors = self._get_theme_colors()

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 10)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(6)

        self.clock_icon_label = QLabel()
        self.clock_icon_label.setPixmap(
            get_clock_icon(22, color=colors["top_bar_icon"], theme=theme).pixmap(22, 22)
        )
        self.clock_icon_label.setFixedWidth(26)
        top.addWidget(self.clock_icon_label)

        title = QLabel("待办")
        title.setObjectName("TitleLabel")
        title.setFixedHeight(28)
        top.addWidget(title)
        top.addStretch()

        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setIcon(
            get_gear_icon(24, color=colors["settings_icon"], theme=theme)
        )
        self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setToolTip("设置")
        self.settings_btn.clicked.connect(self._emit_settings_requested)
        top.addWidget(self.settings_btn)

        self.close_btn = QPushButton()
        self.close_btn.setObjectName("CloseCardButton")
        self.close_btn.setIcon(get_close_icon(24, theme=theme))
        self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setToolTip("隐藏桌面卡片")
        self.close_btn.clicked.connect(self._emit_close_requested)
        top.addWidget(self.close_btn)

        top_widget = QWidget()
        top_widget.setObjectName("TopBar")
        top_widget.setLayout(top)
        top_widget.setCursor(Qt.SizeAllCursor)
        root.addWidget(top_widget)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("TodoList")
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        root.addWidget(self.list_widget, 1)

        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        self.empty_icon_label = QLabel()
        self.empty_icon_label.setPixmap(get_empty_icon(56, theme=theme).pixmap(56, 56))
        self.empty_icon_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_icon_label)
        self.empty_text = QLabel("暂无待办事项")
        self.empty_text.setStyleSheet(f"color: {colors['empty_primary']}; font-size: 13px;")
        self.empty_text.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_text)
        self.empty_hint = QLabel("点击下方按钮添加")
        self.empty_hint.setStyleSheet(f"color: {colors['empty_hint']}; font-size: 11px;")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_hint)
        self.empty_widget.setVisible(False)
        root.addWidget(self.empty_widget, 1)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 6, 0, 6)
        btn_layout.setSpacing(8)

        self.add_btn = QPushButton()
        self.add_btn.setObjectName("AddButton")
        self.add_btn.setIcon(get_add_icon(24, theme=theme))
        self.add_btn.setIconSize(QSize(14, 14))
        self.add_btn.setText(" 添加新待办")
        self.add_btn.clicked.connect(self.add_todo)
        btn_layout.addWidget(self.add_btn)

        root.addWidget(btn_container)

    def _emit_settings_requested(self):
        self.settings_requested.emit()

    def _emit_close_requested(self):
        self.close_requested.emit()

    def _install_event_filter_recursive(self, widget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            self._install_event_filter_recursive(child)

    def _refresh_list(self):
        self.list_widget.clear()
        todos = self.model.get_todos()
        pending_todos = [(idx, t) for idx, t in enumerate(todos) if not t.get("done")]

        if not pending_todos:
            self.list_widget.setVisible(False)
            self.empty_widget.setVisible(True)
            return

        self.list_widget.setVisible(True)
        self.empty_widget.setVisible(False)

        for model_idx, item in pending_todos:
            w = self._create_todo_item_widget(item, model_idx)
            self._install_event_filter_recursive(w)
            li = QListWidgetItem(self.list_widget)
            li.setSizeHint(w.sizeHint())
            self.list_widget.addItem(li)
            self.list_widget.setItemWidget(li, w)

    def _create_todo_item_widget(self, todo: dict, index: int) -> QWidget:
        container = QWidget()
        container.setProperty("class", "todo-item")
        container.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        theme = self.model.get_theme()
        icons = get_todo_item_icons(theme)
        colors = self._get_theme_colors()

        is_done = bool(todo.get("done", False))
        chk_btn = QPushButton()
        chk_btn.setFixedSize(22, 22)
        chk_btn.setCursor(Qt.PointingHandCursor)
        chk_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        icon_size = 18
        if is_done:
            chk_btn.setIcon(get_checkbox_checked_icon(22, theme=theme))
        else:
            chk_btn.setIcon(get_checkbox_empty_icon(22, theme=theme))
        chk_btn.setIconSize(QSize(icon_size, icon_size))
        chk_btn.clicked.connect(lambda _=False, i=index: self._on_toggle_done(i))
        layout.addWidget(chk_btn, 0, Qt.AlignLeft | Qt.AlignVCenter)

        vbox = QVBoxLayout()
        vbox.setSpacing(5)
        vbox.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        title_text = todo.get("title", "")
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("todo-title")
        lbl_title.setProperty("class", "todo-title")
        lbl_title.setProperty("done", "true" if todo.get("done") else "false")
        lbl_title.setWordWrap(True)
        lbl_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if todo.get("done"):
            lbl_title.setText(f"<s>{title_text}</s>")
        vbox.addWidget(lbl_title, 0, Qt.AlignLeft)

        remind_enabled = bool(todo.get("remind_enabled", True))
        remind_dt_str = todo.get("remind_datetime", "")
        time_str = todo.get("time", "")
        if remind_dt_str:
            try:
                dt = datetime.strptime(remind_dt_str, "%Y-%m-%d %H:%M")
                time_str = dt.strftime("%m-%d %H:%M")
            except Exception:
                pass
        remind_before = int(todo.get("remind_before_min", 0)) if remind_enabled else 0
        deadline_text = self.model.get_deadline_text(todo)

        has_time = remind_enabled and bool(time_str)
        has_deadline = bool(deadline_text)
        has_advance = remind_enabled and remind_before > 0
        if has_time or has_deadline or has_advance:
            meta_row = QHBoxLayout()
            meta_row.setSpacing(6)
            meta_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            if has_time:
                time_icon = QLabel()
                time_icon.setPixmap(get_clock_icon(12, color=icons.get("clock"), theme=theme).pixmap(12, 12))
                meta_row.addWidget(time_icon, 0, Qt.AlignLeft | Qt.AlignVCenter)

                lbl_time = QLabel(time_str)
                lbl_time.setObjectName("todo-time")
                lbl_time.setProperty("class", "todo-time")
                lbl_time.setProperty("done", "true" if todo.get("done") else "false")
                lbl_time.setProperty("pending", "false" if todo.get("done") else "true")
                lbl_time.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                meta_row.addWidget(lbl_time, 0, Qt.AlignLeft | Qt.AlignVCenter)

            if has_deadline:
                deadline_status = self.model.get_deadline_status(todo)
                dl_icon = QLabel()
                dl_icon.setPixmap(
                    get_deadline_icon(12, theme=theme).pixmap(12, 12)
                )
                meta_row.addWidget(dl_icon, 0, Qt.AlignLeft | Qt.AlignVCenter)
                lbl_dl = QLabel(f"截止: {deadline_text}")
                lbl_dl.setObjectName("todo-deadline")
                lbl_dl.setProperty("class", "todo-deadline")
                lbl_dl.setProperty("status", deadline_status)
                lbl_dl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                meta_row.addWidget(lbl_dl, 0, Qt.AlignLeft | Qt.AlignVCenter)

            if has_advance:
                lbl_remind = QLabel(f"提前{remind_before}分")
                lbl_remind.setObjectName("todo-remind")
                lbl_remind.setProperty("class", "todo-remind")
                lbl_remind.setProperty("done", "true" if todo.get("done") else "false")
                lbl_remind.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if todo.get("done"):
                    lbl_remind.setStyleSheet("color: #6b7280; font-size: 11px;")
                else:
                    lbl_remind.setStyleSheet("color: #ab47bc; font-size: 11px;")
                meta_row.addWidget(lbl_remind, 0, Qt.AlignLeft | Qt.AlignVCenter)

            meta_row.addStretch(1)
            meta_wrap = QWidget()
            meta_wrap.setLayout(meta_row)
            meta_wrap.setContentsMargins(0, 0, 0, 0)
            vbox.addWidget(meta_wrap, 0, Qt.AlignLeft)

        layout.addLayout(vbox, 1)

        btn_wrap = QWidget()
        btn_container = QVBoxLayout(btn_wrap)
        btn_container.setContentsMargins(0, 0, 0, 0)
        btn_container.setSpacing(6)
        btn_container.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        edit_btn = QPushButton()
        edit_btn.setIcon(get_edit_icon(26, color=icons["edit"], theme=theme))
        edit_btn.setIconSize(QSize(18, 18))
        edit_btn.setFixedSize(30, 30)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 6px; }"
            f"QPushButton:hover {{ background: {colors['btn_hover']}; }}"
        )
        edit_btn.setToolTip("编辑")
        edit_btn.clicked.connect(lambda _, i=index: self._on_edit(i))
        btn_container.addWidget(edit_btn, 0, Qt.AlignRight)

        del_btn = QPushButton()
        del_btn.setIcon(get_delete_icon(26, color=icons["delete"], theme=theme))
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setFixedSize(30, 30)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 6px; }"
            f"QPushButton:hover {{ background: {colors['btn_del_hover']}; }}"
        )
        del_btn.setToolTip("删除")
        del_btn.clicked.connect(lambda _, i=index: self._on_delete(i))
        btn_container.addWidget(del_btn, 0, Qt.AlignRight)

        layout.addWidget(btn_wrap, 0, Qt.AlignRight | Qt.AlignVCenter)

        container.setContextMenuPolicy(Qt.CustomContextMenu)

        def ctx_menu(point):
            menu = QMenu(container)
            menu.addAction("编辑", lambda i=index: self._on_edit(i))
            menu.addSeparator()
            menu.addAction("删除", lambda i=index: self._on_delete(i))
            menu.exec(container.mapToGlobal(point))

        container.customContextMenuRequested.connect(ctx_menu)

        return container

    def _on_toggle_done(self, index: int):
        todos = self.model.get_todos()
        if 0 <= index < len(todos):
            done = bool(todos[index].get("done"))
            new_done = not done
            self.model.update_todo(index, done=new_done)
            if not new_done:
                self.model.update_todo(index, notified=False)
        self._refresh_list()

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

    def _on_delete(self, index: int):
        reply = QMessageBox.question(
            self, "删除确认", "确定删除该待办吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.model.remove_todo(index)
            self._refresh_list()

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

    def _get_bg_mode_and_opacity(self):
        s = self.model.get_settings()
        mode = s.get("card_bg_mode", "glass")
        opacity_pct = int(s.get("card_bg_opacity", 88))
        opacity_pct = max(30, min(100, opacity_pct))
        image_path = s.get("card_bg_image", "") if mode == "image" else ""
        return mode, opacity_pct, image_path

    def paintEvent(self, event):
        radius = 16
        rect = self.rect()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), radius, radius)

        colors = self._get_theme_colors()
        mode, opacity_pct, image_path = self._get_bg_mode_and_opacity()
        alpha = int(255 * (opacity_pct / 100.0))

        painter.save()
        painter.setClipPath(bg_path)

        if mode == "image" and image_path and os.path.isfile(image_path):
            pix = QPixmap(image_path)
            if not pix.isNull():
                source_rect = QRectF(pix.rect())
                target_rect = QRectF(rect)
                s_ratio = source_rect.width() / source_rect.height()
                t_ratio = target_rect.width() / target_rect.height()
                if s_ratio > t_ratio:
                    new_w = source_rect.height() * t_ratio
                    new_x = (source_rect.width() - new_w) / 2
                    source_rect = QRectF(new_x, 0, new_w, source_rect.height())
                else:
                    new_h = source_rect.width() / t_ratio
                    new_y = (source_rect.height() - new_h) / 2
                    source_rect = QRectF(0, new_y, source_rect.width(), new_h)
                painter.drawPixmap(target_rect, pix, source_rect)

            overlay = QColor(0, 0, 0, 0)
            base_c = QColor(colors["bg"])
            if self.model.get_theme() == "dark":
                overlay = QColor(base_c.red(), base_c.green(), base_c.blue(), int(alpha * 0.55))
            else:
                overlay = QColor(base_c.red(), base_c.green(), base_c.blue(), int(alpha * 0.45))
            painter.fillRect(rect, overlay)

        else:
            self._paint_frosted_glass(painter, rect, alpha, colors)

        painter.restore()

        border_color = QColor(colors["border"])
        if mode == "glass":
            if self.model.get_theme() == "dark":
                border_color = QColor(255, 255, 255, 50)
            else:
                border_color = QColor(0, 0, 0, 35)
        painter.setPen(border_color)
        painter.drawPath(bg_path)

        painter.end()

    def _paint_frosted_glass(self, painter: QPainter, rect: QRect, alpha: int, colors: dict):
        theme = self.model.get_theme()
        w, h = rect.width(), rect.height()

        if theme == "dark":
            base_alpha = int(alpha * 0.82)
            base_grad = QLinearGradient(0, 0, 0, h)
            base_grad.setColorAt(0.0, QColor(48, 56, 78, base_alpha))
            base_grad.setColorAt(0.5, QColor(40, 48, 70, base_alpha))
            base_grad.setColorAt(1.0, QColor(35, 42, 62, base_alpha))
            painter.fillRect(rect, base_grad)

            corner = QRadialGradient(0, 0, max(w, h) * 0.55)
            corner.setColorAt(0.0, QColor(120, 140, 185, int(alpha * 0.22)))
            corner.setColorAt(0.5, QColor(80, 100, 150, int(alpha * 0.06)))
            corner.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillRect(rect, corner)

            corner2 = QRadialGradient(w, h, max(w, h) * 0.55)
            corner2.setColorAt(0.0, QColor(130, 110, 170, int(alpha * 0.18)))
            corner2.setColorAt(0.55, QColor(90, 70, 130, int(alpha * 0.05)))
            corner2.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillRect(rect, corner2)

            top_highlight = QLinearGradient(0, 0, 0, h * 0.55)
            top_highlight.setColorAt(0.0, QColor(255, 255, 255, int(alpha * 0.12)))
            top_highlight.setColorAt(0.5, QColor(255, 255, 255, int(alpha * 0.03)))
            top_highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillRect(QRectF(0, 0, w, h * 0.55), top_highlight)

            bottom_highlight = QLinearGradient(0, h, 0, h * 0.55)
            bottom_highlight.setColorAt(0.0, QColor(110, 140, 220, int(alpha * 0.10)))
            bottom_highlight.setColorAt(0.5, QColor(110, 140, 220, int(alpha * 0.025)))
            bottom_highlight.setColorAt(1.0, QColor(110, 140, 220, 0))
            painter.fillRect(QRectF(0, h * 0.45, w, h * 0.55), bottom_highlight)

            vignette = QRadialGradient(w * 0.5, h * 0.55, max(w, h) * 0.6)
            vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
            vignette.setColorAt(0.7, QColor(0, 0, 0, int(alpha * 0.08)))
            vignette.setColorAt(1.0, QColor(0, 0, 0, int(alpha * 0.22)))
            painter.fillRect(rect, vignette)

        else:
            base_alpha = int(alpha * 0.86)
            base_grad = QLinearGradient(0, 0, 0, h)
            base_grad.setColorAt(0.0, QColor(255, 255, 255, base_alpha))
            base_grad.setColorAt(0.5, QColor(248, 250, 253, base_alpha))
            base_grad.setColorAt(1.0, QColor(236, 242, 250, base_alpha))
            painter.fillRect(rect, base_grad)

            corner = QRadialGradient(0, 0, max(w, h) * 0.55)
            corner.setColorAt(0.0, QColor(255, 255, 255, int(alpha * 0.65)))
            corner.setColorAt(0.5, QColor(225, 235, 250, int(alpha * 0.2)))
            corner.setColorAt(1.0, QColor(225, 235, 250, 0))
            painter.fillRect(rect, corner)

            corner2 = QRadialGradient(w, h, max(w, h) * 0.55)
            corner2.setColorAt(0.0, QColor(225, 215, 245, int(alpha * 0.22)))
            corner2.setColorAt(0.5, QColor(210, 195, 235, int(alpha * 0.06)))
            corner2.setColorAt(1.0, QColor(210, 195, 235, 0))
            painter.fillRect(rect, corner2)

            top_highlight = QLinearGradient(0, 0, 0, h * 0.55)
            top_highlight.setColorAt(0.0, QColor(255, 255, 255, int(alpha * 0.55)))
            top_highlight.setColorAt(0.5, QColor(255, 255, 255, int(alpha * 0.14)))
            top_highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillRect(QRectF(0, 0, w, h * 0.55), top_highlight)

            vignette = QRadialGradient(w * 0.5, h * 0.55, max(w, h) * 0.58)
            vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
            vignette.setColorAt(0.75, QColor(0, 0, 0, int(alpha * 0.04)))
            vignette.setColorAt(1.0, QColor(0, 0, 0, int(alpha * 0.12)))
            painter.fillRect(rect, vignette)

        noise_layer = QRectF(rect)
        noise_alpha = int(alpha * 0.06) if theme == "dark" else int(alpha * 0.035)
        painter.fillRect(noise_layer, QColor(255, 255, 255, noise_alpha))

        noise_alt = QRectF(rect)
        noise_alpha2 = int(alpha * 0.03) if theme == "dark" else int(alpha * 0.02)
        painter.fillRect(noise_alt, QColor(0, 0, 0, noise_alpha2))

    def _get_edge(self, pos):
        edge = 0
        if pos.x() <= RESIZE_MARGIN:
            edge |= 1
        if pos.x() >= self.width() - RESIZE_MARGIN:
            edge |= 2
        if pos.y() <= RESIZE_MARGIN:
            edge |= 4
        if pos.y() >= self.height() - RESIZE_MARGIN:
            edge |= 8
        return edge

    def _cursor_for_edge(self, edge):
        if edge in (1, 2):
            return Qt.SizeHorCursor
        if edge in (4, 8):
            return Qt.SizeVerCursor
        if edge in (5, 12):
            return Qt.SizeFDiagCursor
        if edge in (6, 9):
            return Qt.SizeBDiagCursor
        if edge:
            return Qt.SizeAllCursor
        return Qt.ArrowCursor

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            edge = self._get_edge(event.pos())

            if edge:
                self._resize_active = True
                self._resize_edge = edge
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geom = self.geometry()
                event.accept()
                return

            top_bar = self.findChild(QWidget, "TopBar")
            if top_bar and top_bar.geometry().contains(event.pos()):
                self._drag_active = True
                self._drag_pos = event.globalPosition().toPoint()
                self._start_geom = self.frameGeometry()
                event.accept()
                return

            if child is None:
                self._drag_active = True
                self._drag_pos = event.globalPosition().toPoint()
                self._start_geom = self.frameGeometry()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_active:
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_geom = QRect(self._resize_start_geom)

            edge = self._resize_edge
            min_w = self.minimumWidth()
            min_h = self.minimumHeight()

            if edge & 1:
                new_geom.setLeft(new_geom.left() + delta.x())
            if edge & 2:
                new_geom.setRight(new_geom.right() + delta.x())
            if edge & 4:
                new_geom.setTop(new_geom.top() + delta.y())
            if edge & 8:
                new_geom.setBottom(new_geom.bottom() + delta.y())

            if new_geom.width() < min_w:
                if edge & 1:
                    new_geom.setLeft(new_geom.right() - min_w)
                else:
                    new_geom.setRight(new_geom.left() + min_w)
            if new_geom.height() < min_h:
                if edge & 4:
                    new_geom.setTop(new_geom.bottom() - min_h)
                else:
                    new_geom.setBottom(new_geom.top() + min_h)

            self.setGeometry(new_geom)
            self._save_geometry()
            event.accept()
        elif self._drag_active:
            delta = event.globalPosition().toPoint() - self._drag_pos
            new_top_left = self._start_geom.topLeft() + delta
            self.move(new_top_left)
            self._save_geometry()
            event.accept()
        else:
            edge = self._get_edge(event.pos())
            self.setCursor(self._cursor_for_edge(edge))
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._resize_active:
                self._resize_active = False
                self._resize_edge = None
                self._resize_start_pos = None
                self._resize_start_geom = None
                event.accept()
            elif self._drag_active:
                self._drag_active = False
                event.accept()
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        self._save_geometry()
        event.accept()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.setWindowState(Qt.WindowNoState)
                self.hide()
        super().changeEvent(event)

    def enterEvent(self, event):
        self._update_cursor_for_pos(self.mapFromGlobal(self.cursor().pos()))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def _update_cursor_for_pos(self, pos):
        if self._resize_active or self._drag_active:
            return
        edge = self._get_edge(pos)
        self.setCursor(self._cursor_for_edge(edge))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            p = self.mapFromGlobal(event.globalPosition().toPoint())
            self._update_cursor_for_pos(p)
        elif event.type() == QEvent.Leave:
            if obj is self:
                self.unsetCursor()
        return super().eventFilter(obj, event)