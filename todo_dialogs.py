# -*- coding: utf-8 -*-
"""
todo_dialogs.py: 共享的对话框组件
- AddTodoDialog: 添加/编辑待办
"""

from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QCheckBox, QDateEdit, QTimeEdit, QSpinBox,
    QComboBox, QWidget,
)
from PySide6.QtCore import QTime, QDate, Qt, QDateTime


class AddTodoDialog(QDialog):
    REMIND_PRESETS = [
        ("不提前提醒", 0),
        ("提前 5 分钟", 5),
        ("提前 10 分钟", 10),
        ("提前 15 分钟", 15),
        ("提前 30 分钟", 30),
        ("提前 1 小时", 60),
        ("提前 2 小时", 120),
        ("提前 3 小时", 180),
        ("提前 12 小时", 720),
        ("提前 24 小时", 1440),
        ("自定义...", -1),
    ]

    def __init__(self, parent=None, todo_data: dict = None):
        super().__init__(parent)
        self.setObjectName("AddTodoDialog")
        self.setWindowTitle("添加待办" if not todo_data else "编辑待办")
        self.setModal(True)
        self.resize(500, 460)
        self.setMinimumSize(480, 440)
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 22, 22, 18)

        lbl_title_label = QLabel("标题")
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("请输入待办事项内容...")
        self.edit_title.setMinimumHeight(36)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        lbl_title_label.setFixedWidth(80)
        title_row.addWidget(lbl_title_label)
        title_row.addWidget(self.edit_title, 1)
        layout.addLayout(title_row)

        self.chk_remind = QCheckBox("开启提醒")
        self.chk_remind.setObjectName("RemindCheckbox")
        self.chk_remind.setMinimumHeight(30)
        self.chk_remind.setChecked(True)
        layout.addWidget(self.chk_remind)

        self.remind_container = QWidget()
        remind_layout = QVBoxLayout(self.remind_container)
        remind_layout.setContentsMargins(28, 4, 0, 0)
        remind_layout.setSpacing(12)

        datetime_row = QHBoxLayout()
        datetime_row.setSpacing(10)
        lbl_rd = QLabel("提醒日期")
        lbl_rd.setFixedWidth(62)
        self.remind_date_edit = QDateEdit()
        self.remind_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.remind_date_edit.setCalendarPopup(True)
        self.remind_date_edit.setDate(QDate.currentDate())
        self.remind_date_edit.setMinimumHeight(34)
        self.remind_date_edit.setWrapping(True)
        self.remind_date_edit.setAccelerated(True)
        self.remind_date_edit.setToolTip("选择提醒的日期")

        lbl_rt = QLabel("时间")
        lbl_rt.setFixedWidth(34)
        self.remind_time_edit = QTimeEdit()
        self.remind_time_edit.setDisplayFormat("HH:mm")
        self.remind_time_edit.setTime(QTime.currentTime().addSecs(300))
        self.remind_time_edit.setMinimumHeight(34)
        self.remind_time_edit.setWrapping(True)
        self.remind_time_edit.setAccelerated(True)
        self.remind_time_edit.setToolTip("选择提醒的具体时间")

        datetime_row.addWidget(lbl_rd)
        datetime_row.addWidget(self.remind_date_edit, 1)
        datetime_row.addWidget(lbl_rt)
        datetime_row.addWidget(self.remind_time_edit, 1)
        remind_layout.addLayout(datetime_row)

        before_row = QHBoxLayout()
        before_row.setSpacing(10)
        lbl_rb = QLabel("提前提醒")
        lbl_rb.setFixedWidth(62)
        lbl_rb.setToolTip("在提醒时间之前先提醒一次")

        self.cmb_remind_before = QComboBox()
        for text, _ in self.REMIND_PRESETS:
            self.cmb_remind_before.addItem(text)
        self.cmb_remind_before.setCursor(Qt.PointingHandCursor)
        self.cmb_remind_before.setMinimumHeight(34)
        self.cmb_remind_before.setToolTip("选择提前提醒的时间")

        self.spin_custom_remind = QSpinBox()
        self.spin_custom_remind.setRange(1, 1440)
        self.spin_custom_remind.setSuffix(" 分钟")
        self.spin_custom_remind.setCursor(Qt.PointingHandCursor)
        self.spin_custom_remind.setMinimumHeight(34)
        self.spin_custom_remind.setVisible(False)
        self.spin_custom_remind.setValue(10)

        before_row.addWidget(lbl_rb)
        before_row.addWidget(self.cmb_remind_before, 1)
        before_row.addWidget(self.spin_custom_remind, 1)
        remind_layout.addLayout(before_row)

        layout.addWidget(self.remind_container)

        deadline_box = QVBoxLayout()
        deadline_box.setSpacing(10)

        self.chk_deadline = QCheckBox("设置截止时间")
        self.chk_deadline.setObjectName("DeadlineCheckbox")
        self.chk_deadline.setMinimumHeight(30)
        deadline_box.addWidget(self.chk_deadline)

        self.deadline_container = QWidget()
        dl_layout = QHBoxLayout(self.deadline_container)
        dl_layout.setContentsMargins(28, 4, 0, 0)
        dl_layout.setSpacing(10)

        lbl_date = QLabel("截止日期")
        lbl_date.setFixedWidth(62)
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setEnabled(False)
        self.date_edit.setMinimumHeight(34)
        self.date_edit.setWrapping(True)
        self.date_edit.setAccelerated(True)
        self.date_edit.setToolTip("选择截止的日期")

        lbl_dl_time = QLabel("时间")
        lbl_dl_time.setFixedWidth(34)
        self.dl_time_edit = QTimeEdit()
        self.dl_time_edit.setDisplayFormat("HH:mm")
        self.dl_time_edit.setTime(QTime.currentTime())
        self.dl_time_edit.setEnabled(False)
        self.dl_time_edit.setMinimumHeight(34)
        self.dl_time_edit.setWrapping(True)
        self.dl_time_edit.setAccelerated(True)
        self.dl_time_edit.setToolTip("选择截止的具体时间")

        dl_layout.addWidget(lbl_date)
        dl_layout.addWidget(self.date_edit, 1)
        dl_layout.addWidget(lbl_dl_time)
        dl_layout.addWidget(self.dl_time_edit, 1)

        deadline_box.addWidget(self.deadline_container)
        layout.addLayout(deadline_box)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok = QPushButton("保存")
        ok.setObjectName("DialogOkButton")
        ok.setMinimumHeight(36)
        ok.setMinimumWidth(96)
        cancel = QPushButton("取消")
        cancel.setObjectName("DialogCancelButton")
        cancel.setMinimumHeight(36)
        cancel.setMinimumWidth(96)
        btn_layout.addWidget(cancel)
        btn_layout.addWidget(ok)
        layout.addLayout(btn_layout)

        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        self.chk_remind.toggled.connect(self._on_remind_toggled)
        self.chk_deadline.toggled.connect(self._on_deadline_toggled)
        self.cmb_remind_before.currentIndexChanged.connect(self._on_preset_changed)

        if todo_data:
            self.edit_title.setText(todo_data.get("title", ""))

            remind_enabled = bool(todo_data.get("remind_enabled", True))
            self.chk_remind.setChecked(remind_enabled)

            remind_dt_str = todo_data.get("remind_datetime", "")
            if remind_dt_str:
                try:
                    dt = QDateTime.fromString(remind_dt_str, "yyyy-MM-dd HH:mm")
                    if dt.isValid():
                        self.remind_date_edit.setDate(dt.date())
                        self.remind_time_edit.setTime(dt.time())
                except Exception:
                    pass
            else:
                time_str = todo_data.get("time", "")
                if time_str and ":" in time_str:
                    parts = time_str.split(":")
                    if len(parts) == 2:
                        self.remind_time_edit.setTime(QTime(int(parts[0]), int(parts[1])))

            remind_before = int(todo_data.get("remind_before_min", 0))
            self._set_remind_before_value(remind_before)

            dl = todo_data.get("deadline")
            if dl:
                try:
                    self.date_edit.setDate(QDate(dl["year"], dl["month"], dl["day"]))
                    self.dl_time_edit.setTime(
                        QTime(dl.get("hour", 0), dl.get("minute", 0))
                    )
                    self.chk_deadline.setChecked(True)
                except Exception:
                    pass

        self._on_remind_toggled(self.chk_remind.isChecked())
        self._on_deadline_toggled(self.chk_deadline.isChecked())

    def _set_remind_before_value(self, minutes: int):
        found_preset = False
        for idx, (_, val) in enumerate(self.REMIND_PRESETS):
            if val == minutes and val != -1:
                self.cmb_remind_before.setCurrentIndex(idx)
                self.spin_custom_remind.setVisible(False)
                found_preset = True
                break
        if not found_preset:
            self.cmb_remind_before.setCurrentIndex(len(self.REMIND_PRESETS) - 1)
            self.spin_custom_remind.setValue(max(1, min(1440, minutes)))
            self.spin_custom_remind.setVisible(True)

    def _on_preset_changed(self, idx: int):
        _, val = self.REMIND_PRESETS[idx]
        if val == -1:
            self.spin_custom_remind.setVisible(True)
        else:
            self.spin_custom_remind.setVisible(False)

    def _on_remind_toggled(self, checked):
        self.remind_container.setEnabled(checked)

    def _on_deadline_toggled(self, checked):
        self.date_edit.setEnabled(checked)
        self.dl_time_edit.setEnabled(checked)
        self.deadline_container.setEnabled(checked)

    def _get_remind_before_min(self) -> int:
        idx = self.cmb_remind_before.currentIndex()
        _, val = self.REMIND_PRESETS[idx]
        if val == -1:
            return int(self.spin_custom_remind.value())
        return int(val)

    def get_data(self):
        deadline = None
        if self.chk_deadline.isChecked():
            d = self.date_edit.date()
            t = self.dl_time_edit.time()
            deadline = {
                "year": d.year(),
                "month": d.month(),
                "day": d.day(),
                "hour": t.hour(),
                "minute": t.minute(),
            }

        remind_enabled = bool(self.chk_remind.isChecked())
        if remind_enabled:
            rd = self.remind_date_edit.date()
            rt = self.remind_time_edit.time()
            remind_datetime = f"{rd.year():04d}-{rd.month():02d}-{rd.day():02d} {rt.hour():02d}:{rt.minute():02d}"
            display_time_str = rt.toString("HH:mm")
        else:
            remind_datetime = ""
            rt = self.remind_time_edit.time()
            display_time_str = rt.toString("HH:mm")

        return (
            self.edit_title.text().strip(),
            display_time_str,
            deadline,
            self._get_remind_before_min(),
            remind_enabled,
            remind_datetime,
        )

    def closeEvent(self, event):
        self.reject()
        event.accept()