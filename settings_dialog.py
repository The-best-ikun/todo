# -*- coding: utf-8 -*-
"""
SettingsDialog：设置窗口
- 开机自启
- 提醒检查间隔
- 桌面卡片显示开关
- 桌面卡片外观（液态玻璃 / 自定义图片 / 透明度）
"""

import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QSpinBox, QMessageBox, QGroupBox, QComboBox,
    QSlider, QFileDialog, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from autostart_manager import AutostartManager
from todo_model import TodoModel


class SettingsDialog(QDialog):
    CARD_BG_MODES = [
        ("磨砂玻璃（默认）", "glass"),
        ("自定义图片背景", "image"),
    ]

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("设置")
        self.setMinimumWidth(420)
        self.model = model or TodoModel()
        self.autostart = AutostartManager()
        self._original_theme = self.model.get_theme()
        self._accepted = False
        self._closing = False

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        general_group = QGroupBox("常规设置")
        general_layout = QVBoxLayout(general_group)
        general_layout.setSpacing(10)

        h1 = QHBoxLayout()
        lbl_card = QLabel("显示桌面卡片")
        lbl_card.setToolTip("开启后，桌面上将显示一个常驻的小卡片")
        self.chk_card = QCheckBox()
        self.chk_card.setCursor(Qt.PointingHandCursor)
        h1.addWidget(lbl_card)
        h1.addStretch()
        h1.addWidget(self.chk_card)
        general_layout.addLayout(h1)

        h2 = QHBoxLayout()
        lbl_auto = QLabel("开机自启动")
        lbl_auto.setToolTip("开启后，下次开机时会自动启动本程序")
        self.chk_autostart = QCheckBox()
        self.chk_autostart.setCursor(Qt.PointingHandCursor)
        h2.addWidget(lbl_auto)
        h2.addStretch()
        h2.addWidget(self.chk_autostart)
        general_layout.addLayout(h2)

        h3 = QHBoxLayout()
        lbl_interval = QLabel("提醒检查间隔")
        lbl_interval.setToolTip("每隔多久检查一次待办提醒和截止时间")
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 1440)
        self.spin_interval.setSuffix(" 分钟")
        self.spin_interval.setCursor(Qt.PointingHandCursor)
        h3.addWidget(lbl_interval)
        h3.addStretch()
        h3.addWidget(self.spin_interval)
        general_layout.addLayout(h3)

        h4 = QHBoxLayout()
        lbl_theme = QLabel("界面主题")
        lbl_theme.setToolTip("选择应用的日间或夜间显示模式")
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItem("夜间模式", "dark")
        self.cmb_theme.addItem("日间模式", "light")
        self.cmb_theme.setCursor(Qt.PointingHandCursor)
        self.cmb_theme.setFixedWidth(120)
        h4.addWidget(lbl_theme)
        h4.addStretch()
        h4.addWidget(self.cmb_theme)
        general_layout.addLayout(h4)

        layout.addWidget(general_group)

        card_group = QGroupBox("桌面卡片外观")
        card_layout = QVBoxLayout(card_group)
        card_layout.setSpacing(12)

        h5 = QHBoxLayout()
        lbl_bg_mode = QLabel("背景模式")
        lbl_bg_mode.setToolTip("磨砂玻璃：经典半透明磨砂质感；自定义图片：选择本地图片作为背景")
        self.cmb_bg_mode = QComboBox()
        for text, val in self.CARD_BG_MODES:
            self.cmb_bg_mode.addItem(text, val)
        self.cmb_bg_mode.setCursor(Qt.PointingHandCursor)
        self.cmb_bg_mode.setMinimumWidth(180)
        h5.addWidget(lbl_bg_mode)
        h5.addStretch()
        h5.addWidget(self.cmb_bg_mode)
        card_layout.addLayout(h5)

        self.image_widget = QWidget()
        image_layout = QVBoxLayout(self.image_widget)
        image_layout.setContentsMargins(0, 4, 0, 0)
        image_layout.setSpacing(8)

        image_row = QHBoxLayout()
        self.btn_select_image = QPushButton("选择图片...")
        self.btn_select_image.setCursor(Qt.PointingHandCursor)
        self.btn_select_image.setMinimumHeight(30)
        self.btn_select_image.setToolTip("支持 PNG / JPG / BMP / WEBP 等常见图片格式")

        self.btn_clear_image = QPushButton("清除")
        self.btn_clear_image.setCursor(Qt.PointingHandCursor)
        self.btn_clear_image.setMinimumHeight(30)
        self.btn_clear_image.setToolTip("清除当前设置的背景图片，使用默认")

        self.lbl_image_path = QLabel("未设置图片")
        self.lbl_image_path.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_image_path.setWordWrap(True)

        image_row.addWidget(self.btn_select_image)
        image_row.addWidget(self.btn_clear_image)
        image_row.addStretch()
        image_layout.addLayout(image_row)
        image_layout.addWidget(self.lbl_image_path)

        self.lbl_image_preview = QLabel()
        self.lbl_image_preview.setFixedHeight(70)
        self.lbl_image_preview.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_image_preview.setStyleSheet(
            "background: rgba(128,128,128,0.08); border-radius: 6px;"
        )
        image_layout.addWidget(self.lbl_image_preview)

        card_layout.addWidget(self.image_widget)

        opacity_row = QVBoxLayout()
        opacity_row.setSpacing(4)
        opacity_header = QHBoxLayout()
        lbl_opacity = QLabel("背景透明度")
        lbl_opacity.setToolTip("数值越小，卡片背景越透明；100% 表示完全不透明")
        self.lbl_opacity_value = QLabel("88%")
        self.lbl_opacity_value.setStyleSheet("font-weight: 600;")
        opacity_header.addWidget(lbl_opacity)
        opacity_header.addStretch()
        opacity_header.addWidget(self.lbl_opacity_value)
        opacity_row.addLayout(opacity_header)

        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(30, 100)
        self.slider_opacity.setCursor(Qt.PointingHandCursor)
        self.slider_opacity.setTickPosition(QSlider.NoTicks)
        opacity_row.addWidget(self.slider_opacity)

        card_layout.addLayout(opacity_row)
        layout.addWidget(card_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ok = QPushButton("确定")
        self.btn_ok.setObjectName("DialogOkButton")
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("DialogCancelButton")
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

        self.btn_ok.clicked.connect(self._on_ok)
        self.btn_cancel.clicked.connect(self.close)
        self.chk_autostart.stateChanged.connect(self._on_autostart_changed)
        self.cmb_theme.currentIndexChanged.connect(self._on_theme_changed)
        self.cmb_bg_mode.currentIndexChanged.connect(self._on_bg_mode_changed)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        self.btn_select_image.clicked.connect(self._on_select_image)
        self.btn_clear_image.clicked.connect(self._on_clear_image)

    def _update_image_widget_visibility(self):
        mode = self.cmb_bg_mode.currentData()
        self.image_widget.setVisible(mode == "image")

    def _on_opacity_changed(self, value: int):
        self.lbl_opacity_value.setText(f"{value}%")

    def _on_bg_mode_changed(self, idx: int):
        self._update_image_widget_visibility()

    def _on_select_image(self):
        default_dir = os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", default_dir,
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.gif);;所有文件 (*.*)"
        )
        if path and os.path.isfile(path):
            self._current_bg_image = path
            self.lbl_image_path.setText(os.path.basename(path))
            self.lbl_image_path.setToolTip(path)
            self._update_image_preview(path)

    def _on_clear_image(self):
        self._current_bg_image = ""
        self.lbl_image_path.setText("未设置图片")
        self.lbl_image_path.setToolTip("")
        self.lbl_image_preview.setPixmap(QPixmap())
        self.lbl_image_preview.setText("  (无预览)")
        self.lbl_image_preview.setStyleSheet(
            "background: rgba(128,128,128,0.08); border-radius: 6px; color: #888; padding: 8px;"
        )

    def _update_image_preview(self, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            self.lbl_image_preview.setText("  (图片加载失败)")
            self.lbl_image_preview.setStyleSheet(
                "background: rgba(200,80,80,0.15); border-radius: 6px; color: #a33; padding: 8px;"
            )
            return
        max_h = self.lbl_image_preview.height()
        scaled = pix.scaledToHeight(max_h - 8, Qt.SmoothTransformation)
        self.lbl_image_preview.setPixmap(scaled)
        self.lbl_image_preview.setText("")
        self.lbl_image_preview.setStyleSheet(
            "background: rgba(128,128,128,0.08); border-radius: 6px; padding: 4px;"
        )

    def _load_settings(self):
        settings = self.model.get_settings()

        self.chk_card.setChecked(self.model.is_card_visible())

        interval = settings.get("check_interval_min", 1)
        self.spin_interval.setValue(int(interval))

        theme = self.model.get_theme()
        idx = self.cmb_theme.findData(theme)
        if idx >= 0:
            self.cmb_theme.setCurrentIndex(idx)

        try:
            enabled = self.autostart.is_enabled()
        except Exception:
            enabled = False
        self.chk_autostart.setChecked(enabled)

        bg_mode = settings.get("card_bg_mode", "glass")
        i = self.cmb_bg_mode.findData(bg_mode)
        if i >= 0:
            self.cmb_bg_mode.setCurrentIndex(i)

        opacity = int(settings.get("card_bg_opacity", 88))
        opacity = max(30, min(100, opacity))
        self.slider_opacity.setValue(opacity)
        self.lbl_opacity_value.setText(f"{opacity}%")

        img = settings.get("card_bg_image", "")
        self._current_bg_image = img if isinstance(img, str) else ""
        if self._current_bg_image and os.path.isfile(self._current_bg_image):
            self.lbl_image_path.setText(os.path.basename(self._current_bg_image))
            self.lbl_image_path.setToolTip(self._current_bg_image)
            self._update_image_preview(self._current_bg_image)
        else:
            self._on_clear_image()

        self._update_image_widget_visibility()

    def _on_autostart_changed(self, state):
        checked = bool(state)
        try:
            if checked:
                self.autostart.enable()
            else:
                self.autostart.disable()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"设置开机自启失败：{e}")
            try:
                self.chk_autostart.blockSignals(True)
                self.chk_autostart.setChecked(self.autostart.is_enabled())
                self.chk_autostart.blockSignals(False)
            except Exception:
                self.chk_autostart.setChecked(False)

    def _on_ok(self):
        self._accepted = True
        self.model.set_card_visible(self.chk_card.isChecked())
        interval = int(self.spin_interval.value())
        self.model.set_setting("check_interval_min", interval)
        theme = self.cmb_theme.currentData()
        self.model.set_theme(theme)

        bg_mode = self.cmb_bg_mode.currentData()
        self.model.set_setting("card_bg_mode", bg_mode)
        opacity = int(self.slider_opacity.value())
        self.model.set_setting("card_bg_opacity", opacity)
        self.model.set_setting("card_bg_image", self._current_bg_image if bg_mode == "image" else "")

        self.accept()

    def _on_theme_changed(self, index):
        theme = self.cmb_theme.currentData()
        self.model.set_theme(theme)
        self._apply_theme_to_main()

    def _apply_theme_to_main(self):
        parent = self.parent()
        if parent and hasattr(parent, '_apply_theme'):
            parent._apply_theme()

    def closeEvent(self, event):
        if self._closing:
            event.accept()
            return
        self._closing = True
        if not self._accepted:
            self.model.set_theme(self._original_theme)
            self._apply_theme_to_main()
        event.accept()