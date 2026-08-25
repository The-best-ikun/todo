# -*- coding: utf-8 -*-
"""
TodoModel：负责加载/保存待办事项与部分设置（JSON 存储）
文件：
- todos.json : 存储待办项列表，格式如下：
  [
    {"title": "开会", "time": "10:00", "done": false, "notified": false, "deadline": null}
  ]
- settings.json : 存储应用设置（例如检查间隔、窗口位置等）
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from PySide6.QtCore import QObject, Signal

from icon_utils import get_data_dir


class TodoModel(QObject):
    todos_changed = Signal()
    settings_changed = Signal()

    def __init__(self):
        super().__init__()
        base_dir = get_data_dir()
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            pass
        self.todos_path = os.path.join(base_dir, "todos.json")
        self.settings_path = os.path.join(base_dir, "settings.json")

        self.todos: List[Dict[str, Any]] = []
        self.settings: Dict[str, Any] = {
            "check_interval_min": 1,
            "window_geometry": None,
            "remind_before_min": 0,
            "auto_start": False,
            "card_visible": True,
            "main_window_geometry": None,
            "theme": "dark",
        }

        self.load()

    def load(self):
        if os.path.exists(self.todos_path):
            try:
                with open(self.todos_path, "r", encoding="utf-8") as f:
                    self.todos = json.load(f)
            except Exception:
                self.todos = []
        else:
            self.todos = []

        for t in self.todos:
            t.setdefault("id", str(uuid.uuid4())[:8])
            t.setdefault("title", "")
            t.setdefault("time", "")
            t.setdefault("done", False)
            t.setdefault("notified", False)
            t.setdefault("deadline", None)
            t.setdefault("deadline_notified", False)
            t.setdefault("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            t.setdefault("remind_before_min", 0)
            t.setdefault("remind_enabled", True)
            t.setdefault("remind_datetime", "")

        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception:
                pass

        self.settings.setdefault("check_interval_min", 1)
        self.settings.setdefault("remind_before_min", 0)
        self.settings.setdefault("card_bg_mode", "glass")
        self.settings.setdefault("card_bg_image", "")
        self.settings.setdefault("card_bg_opacity", 88)
        self.settings.setdefault("card_glass_blur", 60)

        self.save()

    def save(self):
        try:
            with open(self.todos_path, "w", encoding="utf-8") as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_todo(self, title: str, time_str: str, deadline: Optional[Dict[str, int]] = None, remind_before_min: int = 0, remind_enabled: bool = True, remind_datetime: str = "") -> str:
        item_id = str(uuid.uuid4())[:8]
        item = {
            "id": item_id,
            "title": title,
            "time": time_str,
            "done": False,
            "notified": False,
            "deadline": deadline,
            "deadline_notified": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remind_before_min": int(remind_before_min),
            "remind_enabled": bool(remind_enabled),
            "remind_datetime": remind_datetime,
        }
        self.todos.append(item)
        self._sort_todos()
        self.save()
        self.todos_changed.emit()
        return item_id

    def update_todo(self, index: int, **kwargs):
        if 0 <= index < len(self.todos):
            self.todos[index].update(kwargs)
            self._sort_todos()
            self.save()
            self.todos_changed.emit()

    def remove_todo(self, index: int):
        if 0 <= index < len(self.todos):
            del self.todos[index]
            self.save()
            self.todos_changed.emit()

    def update_todo_by_id(self, item_id: str, **kwargs):
        for i, t in enumerate(self.todos):
            if t.get("id") == item_id:
                self.update_todo(i, **kwargs)
                return True
        return False

    def remove_todo_by_id(self, item_id: str):
        for i, t in enumerate(self.todos):
            if t.get("id") == item_id:
                self.remove_todo(i)
                return True
        return False

    def _sort_todos(self):
        def keyfn(item):
            dl = item.get("deadline")
            if dl:
                try:
                    return datetime(
                        dl["year"], dl["month"], dl["day"],
                        dl.get("hour", 0), dl.get("minute", 0)
                    ).timestamp()
                except Exception:
                    pass
            t = item.get("time", "")
            try:
                h, m = t.split(":")
                return int(h) * 60 + int(m)
            except Exception:
                return 9999999999

        self.todos.sort(key=keyfn)

    def get_todos(self) -> List[Dict[str, Any]]:
        return self.todos

    def get_settings(self) -> Dict[str, Any]:
        return self.settings

    def set_setting(self, key: str, value):
        self.settings[key] = value
        self.save()
        self.settings_changed.emit()

    def get_window_geometry(self) -> Optional[Dict[str, int]]:
        return self.settings.get("window_geometry")

    def _save_silent(self):
        """只保存到磁盘，不发送 settings_changed 信号（用于频繁的几何/状态写入）"""
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_window_geometry(self, x: int, y: int, w: int, h: int):
        self.settings["window_geometry"] = {"x": x, "y": y, "w": w, "h": h}
        self._save_silent()

    def is_card_visible(self) -> bool:
        return bool(self.settings.get("card_visible", True))

    def set_card_visible(self, visible: bool):
        self.settings["card_visible"] = visible
        self.save()
        self.settings_changed.emit()

    def get_main_window_geometry(self) -> Optional[Dict[str, int]]:
        return self.settings.get("main_window_geometry")

    def set_main_window_geometry(self, x: int, y: int, w: int, h: int):
        self.settings["main_window_geometry"] = {"x": x, "y": y, "w": w, "h": h}
        self._save_silent()

    def get_theme(self) -> str:
        return self.settings.get("theme", "dark")

    def set_theme(self, theme: str):
        self.settings["theme"] = theme
        self.save()
        self.settings_changed.emit()

    def get_pending_deadlines(self) -> List[int]:
        now = datetime.now()
        result = []
        for i, t in enumerate(self.todos):
            if t.get("done"):
                continue
            dl = t.get("deadline")
            if not dl:
                continue
            if t.get("deadline_notified"):
                continue
            try:
                dl_dt = datetime(
                    dl["year"], dl["month"], dl["day"],
                    dl.get("hour", 0), dl.get("minute", 0)
                )
                if dl_dt <= now:
                    result.append(i)
            except Exception:
                pass
        return result

    def get_deadline_status(self, todo: Dict[str, Any]) -> str:
        dl = todo.get("deadline")
        if not dl:
            return ""
        now = datetime.now()
        try:
            dl_dt = datetime(
                dl["year"], dl["month"], dl["day"],
                dl.get("hour", 0), dl.get("minute", 0)
            )
            diff = dl_dt - now
            total_secs = int(diff.total_seconds())
            if total_secs < 0:
                return "expired"
            if total_secs <= 300:
                return "soon"
            return "upcoming"
        except Exception:
            return ""

    def get_deadline_text(self, todo: Dict[str, Any]) -> str:
        dl = todo.get("deadline")
        if not dl:
            return ""
        try:
            return f"{dl['year']}-{dl['month']:02d}-{dl['day']:02d} {dl.get('hour', 0):02d}:{dl.get('minute', 0):02d}"
        except Exception:
            return ""

    def mark_deadline_notified(self, index: int):
        if 0 <= index < len(self.todos):
            self.todos[index]["deadline_notified"] = True
            self.save()