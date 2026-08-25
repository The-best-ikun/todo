# -*- coding: utf-8 -*-
"""
icon_utils.py: 所有图标通过 QPainter 程序化绘制，不使用任何 emoji 字符。
支持主题感知的图标颜色。
"""

import os
import sys

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QBrush,
    QPainterPath, QRadialGradient, QLinearGradient, QFont
)


def get_resource_dir():
    """
    获取只读资源所在目录（qss 样式表等）。
    - 开发模式：返回源码目录（main.py 同级）
    - PyInstaller 打包：返回 sys._MEIPASS 临时解压目录
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir():
    """
    获取可写数据目录（todos.json、settings.json 等用户数据）。
    - 开发模式：返回源码目录
    - PyInstaller 打包：返回可执行文件（exe）同级目录
      这样用户数据不会随 _MEIPASS 临时目录丢失
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _debug_log(msg: str):
    """开发和打包模式下都打印信息到 stdout（便于排查 EXE 下资源路径问题）"""
    try:
        print(f"[样式调试] {msg}", flush=True)
    except Exception:
        pass


def resolve_qss_path(theme: str = "dark") -> str:
    """
    按优先级查找 style.qss / style_light.qss 位置，返回"实际存在"的那个文件路径。
    查找顺序（优先级从高到低）：
      1. get_resource_dir()（开发模式=源码目录；打包模式=_MEIPASS）
      2. get_data_dir()     （打包模式=exe 同级目录，手动放 qss 也能用）
    """
    filename = "style_light.qss" if theme == "light" else "style.qss"

    candidates = []
    for base in [get_resource_dir(), get_data_dir()]:
        candidates.append(os.path.join(base, filename))

    for path in candidates:
        exists = os.path.exists(path)
        _debug_log(f"检查 {path} -> {'存在' if exists else '不存在'}")
        if exists:
            _debug_log(f"找到 {filename}: {path}")
            return path

    _debug_log(f"找不到 {filename}！已尝试路径: {candidates}")
    return ""


def apply_theme_stylesheet(app, theme: str = "dark"):
    """统一的 QSS 加载入口（启动加载 & 主题切换都走这里），不再静默吞异常"""
    if app is None:
        return False

    qss_path = resolve_qss_path(theme)
    if not qss_path:
        _debug_log("QSS 未加载，将使用 Qt 默认样式（日间/夜间切换会失效）")
        app.setStyleSheet("")
        return False

    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            content = f.read()
        app.setStyleSheet(content)
        _debug_log(f"已加载 QSS（theme={theme}, {len(content)} 字符）")
        return True
    except Exception as e:
        _debug_log(f"加载 QSS 失败: {type(e).__name__}: {e}")
        return False


def _new_pixmap(size=64):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    return pix


def resolve_color(color, theme):
    if color is not None:
        if isinstance(color, str):
            return QColor(color)
        return color
    if theme == "light":
        return QColor(50, 50, 60)
    return QColor(255, 255, 255)


def resolve_icon_color(theme, fallback=None):
    if fallback is not None:
        if isinstance(fallback, str):
            return QColor(fallback)
        return fallback
    return resolve_color(None, theme)


def draw_app_icon():
    pix = _new_pixmap(64)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0, QColor(79, 195, 247))
    grad.setColorAt(1, QColor(41, 121, 255))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(4, 4, 56, 56), 14, 14)

    p.setPen(QPen(QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawLine(18, 22, 46, 22)
    p.drawLine(18, 32, 42, 32)
    p.drawLine(18, 42, 38, 42)

    check_grad = QLinearGradient(0, 40, 0, 58)
    check_grad.setColorAt(0, QColor(129, 212, 250))
    check_grad.setColorAt(1, QColor(79, 195, 247))
    p.setBrush(QBrush(check_grad))
    p.setPen(Qt.NoPen)
    path = QPainterPath()
    path.moveTo(40, 44)
    path.lineTo(44, 48)
    path.lineTo(52, 38)
    path.lineTo(54, 40)
    path.lineTo(44, 52)
    path.lineTo(38, 46)
    path.closeSubpath()
    p.drawPath(path)

    p.end()
    return QIcon(pix)


def draw_gear_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))

    center = size / 2
    outer_r = size * 0.38
    inner_r = size * 0.2
    tooth_len = size * 0.12
    tooth_width = size * 0.1

    for i in range(8):
        angle = i * 45
        p.save()
        p.translate(center, center)
        p.rotate(angle)
        tooth = QRectF(-tooth_width / 2, -outer_r - tooth_len, tooth_width, tooth_len)
        p.drawRoundedRect(tooth, 2, 2)
        p.restore()

    p.drawEllipse(QPointF(center, center), outer_r, outer_r)

    inner_bg = QColor(255, 255, 255) if theme == "light" else QColor(30, 30, 30)
    p.setBrush(QBrush(inner_bg))
    p.drawEllipse(QPointF(center, center), inner_r, inner_r)

    p.end()
    return QIcon(pix)


def draw_clock_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))

    center = size / 2
    r = size * 0.38
    p.drawEllipse(QPointF(center, center), r, r)

    inner_bg = QColor(255, 255, 255) if theme == "light" else QColor(30, 30, 30)
    p.setBrush(QBrush(inner_bg))
    p.drawEllipse(QPointF(center, center), r * 0.75, r * 0.75)

    p.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(center, center), QPointF(center, center - r * 0.5))
    p.drawLine(QPointF(center, center), QPointF(center + r * 0.35, center))

    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))
    p.drawEllipse(QPointF(center, center), 2, 2)

    p.end()
    return QIcon(pix)


def draw_check_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    p.setBrush(QBrush(color))
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 4, 4)

    check_line = QColor(255, 255, 255)
    p.setPen(QPen(check_line, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(QPointF(size * 0.3, size * 0.5), QPointF(size * 0.45, size * 0.65))
    p.drawLine(QPointF(size * 0.45, size * 0.65), QPointF(size * 0.7, size * 0.35))

    p.end()
    return QIcon(pix)


def draw_checked_icon(size=24, theme="dark"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(79, 195, 247))
    grad.setColorAt(1, QColor(41, 121, 255))
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 4, 4)

    p.setPen(QPen(QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(QPointF(size * 0.3, size * 0.5), QPointF(size * 0.45, size * 0.65))
    p.drawLine(QPointF(size * 0.45, size * 0.65), QPointF(size * 0.7, size * 0.35))

    p.end()
    return QIcon(pix)


def draw_checkbox_empty_icon(size=20, theme="dark"):
    color = QColor(255, 255, 255, 230) if theme == "dark" else QColor(70, 80, 100, 255)
    hover_color = QColor(255, 255, 255, 255) if theme == "dark" else QColor(40, 50, 70, 255)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    pen_w = max(1.5, size * 0.085)
    inner = QRectF(
        pen_w * 0.9 + 1,
        pen_w * 0.9 + 1,
        size - 2 * (pen_w * 0.9 + 1),
        size - 2 * (pen_w * 0.9 + 1),
    )
    border_radius = max(2.5, size * 0.14)

    fill_c = QColor(255, 255, 255, 18) if theme == "dark" else QColor(255, 255, 255, 110)
    p.setBrush(QBrush(fill_c))
    pen = QPen(QBrush(color), pen_w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.drawRoundedRect(inner, border_radius, border_radius)

    _ = hover_color
    p.end()
    return QIcon(pix)


def draw_checkbox_checked_icon(size=20, theme="dark"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    pen_w = max(1.5, size * 0.085)
    inner = QRectF(
        pen_w * 0.9 + 1,
        pen_w * 0.9 + 1,
        size - 2 * (pen_w * 0.9 + 1),
        size - 2 * (pen_w * 0.9 + 1),
    )
    border_radius = max(2.5, size * 0.14)

    grad = QLinearGradient(0, 0, size, size)
    if theme == "dark":
        grad.setColorAt(0.0, QColor(110, 215, 255))
        grad.setColorAt(1.0, QColor(65, 140, 255))
    else:
        grad.setColorAt(0.0, QColor(90, 200, 255))
        grad.setColorAt(1.0, QColor(50, 120, 248))
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(inner, border_radius, border_radius)

    border_c = QColor(255, 255, 255, 180) if theme == "dark" else QColor(80, 140, 230, 80)
    pen = QPen(QBrush(border_c), max(0.8, size * 0.04), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(inner, border_radius, border_radius)
    p.setPen(Qt.NoPen)

    check_c = QColor(255, 255, 255)
    pen2 = QPen(QBrush(check_c), max(1.8, size * 0.13), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen2)
    p.setBrush(Qt.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.28, size * 0.52)
    path.lineTo(size * 0.44, size * 0.68)
    path.lineTo(size * 0.74, size * 0.34)
    p.drawPath(path)

    p.end()
    return QIcon(pix)


def draw_edit_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)

    cx = size * 0.5
    cy = size * 0.5
    pen_w = max(2.2, size * 0.09)

    p.save()
    p.translate(cx, cy)
    p.rotate(-45)

    r = size * 0.3
    rect_pen = QRectF(-r, -r * 0.2, r * 2, r * 0.5)
    rect_fill = QRectF(-r * 0.8, -r * 0.1, r * 1.3, r * 0.3)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color, pen_w, Qt.SolidLine, Qt.SquareCap))
    p.drawRect(rect_pen)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))
    p.drawRect(rect_fill)

    stem_len = r * 0.7
    stem = QRectF(-pen_w / 2, r * 0.2, pen_w, stem_len)
    p.drawRect(stem)

    p.restore()
    p.end()
    return QIcon(pix)


def draw_delete_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    cx = size * 0.5
    cy = size * 0.5
    pen_w = max(2.2, size * 0.09)

    lid_y = size * 0.3
    lid_len = size * 0.56
    p.setPen(QPen(color, pen_w, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(cx - lid_len / 2, lid_y), QPointF(cx + lid_len / 2, lid_y))

    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))
    handle_w = size * 0.18
    handle_h = size * 0.12
    handle = QRectF(cx - handle_w / 2, size * 0.18, handle_w, handle_h)
    p.drawRoundedRect(handle, 2, 2)

    body_top = lid_y + size * 0.02
    body_left = cx - lid_len / 2 + pen_w * 0.2
    body_right = cx + lid_len / 2 - pen_w * 0.2
    body_bottom = size * 0.84
    body = QRectF(body_left, body_top, body_right - body_left, body_bottom - body_top)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(color, pen_w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawRoundedRect(body, 2, 2)

    line_top = body_top + (body_bottom - body_top) * 0.22
    line_bottom = body_bottom - (body_bottom - body_top) * 0.14
    p.setPen(QPen(color, pen_w * 0.85, Qt.SolidLine, Qt.RoundCap))
    x1 = cx - (body_right - body_left) * 0.18
    x2 = cx + (body_right - body_left) * 0.18
    p.drawLine(QPointF(x1, line_top), QPointF(x1, line_bottom))
    p.drawLine(QPointF(x2, line_top), QPointF(x2, line_bottom))

    p.end()
    return QIcon(pix)


def draw_add_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    cx = size / 2
    cy = size / 2
    r = size * 0.42

    grad = QRadialGradient(cx, cy, r)
    if theme == "light":
        grad.setColorAt(0, QColor(79, 195, 247))
        grad.setColorAt(1, QColor(41, 121, 255))
    else:
        grad.setColorAt(0, QColor(100, 205, 249))
        grad.setColorAt(1, QColor(41, 121, 255))

    p.setBrush(QBrush(grad))
    p.drawEllipse(QPointF(cx, cy), r, r)

    plus_color = QColor(255, 255, 255)
    arm = r * 0.45
    p.setPen(QPen(plus_color, max(2, size * 0.08), Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
    p.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

    p.end()
    return QIcon(pix)


def draw_list_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(color))

    dot_r = size * 0.06
    p.drawEllipse(QPointF(size * 0.2, size * 0.25), dot_r, dot_r)
    p.drawEllipse(QPointF(size * 0.2, size * 0.5), dot_r, dot_r)
    p.drawEllipse(QPointF(size * 0.2, size * 0.75), dot_r, dot_r)

    p.setPen(QPen(color, 2.5, Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(size * 0.35, size * 0.25), QPointF(size * 0.8, size * 0.25))
    p.drawLine(QPointF(size * 0.35, size * 0.5), QPointF(size * 0.8, size * 0.5))
    p.drawLine(QPointF(size * 0.35, size * 0.75), QPointF(size * 0.65, size * 0.75))

    p.end()
    return QIcon(pix)


def draw_empty_icon(size=64, theme="dark"):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    if theme == "light":
        base_color = QColor(0, 0, 0, 30)
        fold_color = QColor(0, 0, 0, 45)
        line_color = QColor(0, 0, 0, 60)
    else:
        base_color = QColor(255, 255, 255, 40)
        fold_color = QColor(255, 255, 255, 60)
        line_color = QColor(255, 255, 255, 80)

    doc_path = QPainterPath()
    doc_path.moveTo(size * 0.25, size * 0.15)
    doc_path.lineTo(size * 0.7, size * 0.15)
    doc_path.lineTo(size * 0.8, size * 0.25)
    doc_path.lineTo(size * 0.8, size * 0.85)
    doc_path.lineTo(size * 0.25, size * 0.85)
    doc_path.closeSubpath()

    p.setBrush(QBrush(base_color))
    p.drawPath(doc_path)

    fold_path = QPainterPath()
    fold_path.moveTo(size * 0.7, size * 0.15)
    fold_path.lineTo(size * 0.7, size * 0.25)
    fold_path.lineTo(size * 0.8, size * 0.25)
    p.setBrush(QBrush(fold_color))
    p.drawPath(fold_path)

    p.setPen(QPen(line_color, 2))
    p.drawLine(QPointF(size * 0.35, size * 0.4), QPointF(size * 0.65, size * 0.4))
    p.drawLine(QPointF(size * 0.35, size * 0.52), QPointF(size * 0.65, size * 0.52))
    p.drawLine(QPointF(size * 0.35, size * 0.64), QPointF(size * 0.55, size * 0.64))

    p.end()
    return QIcon(pix)


def draw_tray_icon(size=64):
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)

    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor(79, 195, 247))
    grad.setColorAt(1, QColor(41, 121, 255))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 12, 12)

    p.setPen(QPen(QColor(255, 255, 255), 2, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(size * 0.3, size * 0.38), QPointF(size * 0.6, size * 0.38))
    p.drawLine(QPointF(size * 0.3, size * 0.52), QPointF(size * 0.55, size * 0.52))
    p.drawLine(QPointF(size * 0.3, size * 0.66), QPointF(size * 0.5, size * 0.66))

    check_path = QPainterPath()
    check_path.moveTo(size * 0.42, size * 0.68)
    check_path.lineTo(size * 0.48, size * 0.74)
    check_path.lineTo(size * 0.58, size * 0.62)
    p.setBrush(QBrush(QColor(255, 255, 255)))
    p.setPen(Qt.NoPen)
    p.drawPath(check_path)

    p.end()
    return QIcon(pix)


def draw_sun_icon(size=24, color=None, theme="dark"):
    if color is None:
        color = QColor(255, 200, 50)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    center = size / 2
    r = size * 0.28
    p.setBrush(QBrush(color))
    p.drawEllipse(QPointF(center, center), r, r)

    p.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap))
    for i in range(8):
        angle = i * 45
        p.save()
        p.translate(center, center)
        p.rotate(angle)
        p.drawLine(QPointF(0, -r - size * 0.08), QPointF(0, -r - size * 0.18))
        p.restore()

    p.end()
    return QIcon(pix)


def draw_moon_icon(size=24, color=None, theme="dark"):
    if color is None:
        if theme == "light":
            color = QColor(42, 52, 82)
        else:
            color = QColor(240, 240, 255)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    center = size / 2
    arm_long = size * 0.42
    arm_short = size * 0.125
    inner_r = size * 0.10

    star_path = QPainterPath()
    star_path.moveTo(center, center - arm_long)
    star_path.lineTo(center + inner_r, center - inner_r)
    star_path.lineTo(center + arm_long, center)
    star_path.lineTo(center + inner_r, center + inner_r)
    star_path.lineTo(center, center + arm_long)
    star_path.lineTo(center - inner_r, center + inner_r)
    star_path.lineTo(center - arm_long, center)
    star_path.lineTo(center - inner_r, center - inner_r)
    star_path.closeSubpath()

    if theme == "light":
        star_grad = QRadialGradient(center, center, arm_long * 1.1)
        star_grad.setColorAt(0.0, QColor(72, 86, 126))
        star_grad.setColorAt(0.6, QColor(50, 64, 104))
        star_grad.setColorAt(1.0, QColor(30, 42, 78))
        p.setBrush(QBrush(star_grad))
    else:
        p.setBrush(QBrush(color))
    p.drawPath(star_path)

    if theme == "light":
        outline_c = QColor(16, 24, 48, 220)
        outline_pen = QPen(
            QBrush(outline_c), max(0.7, size * 0.035),
            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
        )
        p.setPen(outline_pen)
        p.setBrush(Qt.NoBrush)
        p.drawPath(star_path)
        p.setPen(Qt.NoPen)

    tiny_c = QColor(255, 255, 255, 70) if theme == "dark" else QColor(255, 255, 255, 0)
    if tiny_c.alpha() > 0:
        p.setBrush(QBrush(tiny_c))
        p.drawEllipse(QPointF(center - arm_long * 0.05, center - arm_long * 0.45),
                      size * 0.04, size * 0.04)

    small_s = max(1.2, size * 0.055)
    p.setBrush(QBrush(color))
    p.drawEllipse(QPointF(center + arm_long * 0.6, center - arm_long * 0.7), small_s, small_s)
    s2 = max(0.9, size * 0.04)
    p.drawEllipse(QPointF(center - arm_long * 0.75, center + arm_long * 0.35), s2, s2)

    p.end()
    return QIcon(pix)


def draw_close_icon(size=20, color=None, theme="dark"):
    if color is None:
        if theme == "light":
            color = QColor(140, 60, 60)
        else:
            color = QColor(230, 230, 230)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)

    pad = size * 0.18
    bg_r = (size - 2 * pad) * 0.5

    if theme == "light":
        bg_color = QColor(255, 236, 236, 220)
    else:
        bg_color = QColor(90, 50, 50, 220)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(bg_color))
    p.drawRoundedRect(int(pad), int(pad), int(size - 2 * pad), int(size - 2 * pad),
                      int(size * 0.18), int(size * 0.18))

    line_color = color
    pen = QPen(QBrush(line_color), max(1.4, size * 0.11), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    c = size / 2
    line_len = bg_r * 1.05
    p.drawLine(QPointF(c - line_len * 0.62, c - line_len * 0.62),
               QPointF(c + line_len * 0.62, c + line_len * 0.62))
    p.drawLine(QPointF(c + line_len * 0.62, c - line_len * 0.62),
               QPointF(c - line_len * 0.62, c + line_len * 0.62))

    p.end()
    return QIcon(pix)


def get_close_icon(size=20, color=None, theme="dark"):
    return draw_close_icon(size, color, theme)


def draw_deadline_icon(size=24, color=None, theme="dark"):
    color = resolve_color(color, theme)
    pix = _new_pixmap(size)
    p = QPainter(pix)
    p.setRenderHints(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    body_w = size * 0.72
    body_h = size * 0.6
    body_x = (size - body_w) / 2
    body_y = size * 0.28

    p.setBrush(QBrush(color))
    p.drawRoundedRect(QRectF(body_x, body_y, body_w, body_h), 3, 3)

    top_bar = QRectF(body_x, body_y, body_w, size * 0.16)
    bar_color = QColor(41, 121, 255) if theme == "light" else QColor(79, 195, 247)
    p.setBrush(QBrush(bar_color))
    p.drawRoundedRect(top_bar, 3, 3)

    p.setBrush(QBrush(color))
    left_leg_x = body_x + body_w * 0.25
    right_leg_x = body_x + body_w * 0.65
    leg_top = body_y - size * 0.1
    leg_bottom = body_y
    p.drawRect(QRectF(left_leg_x, leg_top, size * 0.06, size * 0.1))
    p.drawRect(QRectF(right_leg_x, leg_top, size * 0.06, size * 0.1))

    inner_color = QColor(255, 255, 255) if theme == "light" else QColor(30, 30, 30)
    p.setBrush(QBrush(inner_color))
    inner = QRectF(body_x + body_w * 0.12, body_y + body_h * 0.35, body_w * 0.76, body_h * 0.55)
    p.drawRoundedRect(inner, 2, 2)

    p.setPen(Qt.NoPen)
    dot_color = QColor(41, 121, 255) if theme == "light" else QColor(79, 195, 247)
    p.setBrush(QBrush(dot_color))
    dot_r = max(1, size * 0.04)
    dots = [
        (inner.left() + inner.width() * 0.25, inner.top() + inner.height() * 0.28),
        (inner.left() + inner.width() * 0.55, inner.top() + inner.height() * 0.28),
        (inner.left() + inner.width() * 0.25, inner.top() + inner.height() * 0.6),
        (inner.left() + inner.width() * 0.55, inner.top() + inner.height() * 0.6),
    ]
    for dx, dy in dots:
        p.drawEllipse(QPointF(dx, dy), dot_r, dot_r)

    p.end()
    return QIcon(pix)


def get_app_icon():
    return draw_app_icon()


def get_tray_icon():
    return draw_tray_icon()


def get_gear_icon(size=24, color=None, theme="dark"):
    return draw_gear_icon(size, color, theme)


def get_clock_icon(size=24, color=None, theme="dark"):
    return draw_clock_icon(size, color, theme)


def get_check_icon(size=24, color=None, theme="dark"):
    return draw_check_icon(size, color, theme)


def get_checked_icon(size=24, theme="dark"):
    return draw_checked_icon(size, theme)


def get_checkbox_empty_icon(size=20, theme="dark"):
    return draw_checkbox_empty_icon(size, theme)


def get_checkbox_checked_icon(size=20, theme="dark"):
    return draw_checkbox_checked_icon(size, theme)


def get_edit_icon(size=24, color=None, theme="dark"):
    return draw_edit_icon(size, color, theme)


def get_delete_icon(size=24, color=None, theme="dark"):
    return draw_delete_icon(size, color, theme)


def get_add_icon(size=24, color=None, theme="dark"):
    return draw_add_icon(size, color, theme)


def get_list_icon(size=24, color=None, theme="dark"):
    return draw_list_icon(size, color, theme)


def get_deadline_icon(size=24, color=None, theme="dark"):
    return draw_deadline_icon(size, color, theme)


def get_empty_icon(size=64, theme="dark"):
    return draw_empty_icon(size, theme)


def get_sun_icon(size=24, color=None, theme="dark"):
    return draw_sun_icon(size, color, theme)


def get_moon_icon(size=24, color=None, theme="dark"):
    return draw_moon_icon(size, color, theme)


def get_theme_icon(theme, size=24):
    if theme == "light":
        return get_moon_icon(size, theme=theme)
    else:
        return get_sun_icon(size, theme=theme)


def get_nav_icon(nav_type, size=20, theme="dark"):
    if nav_type == "all":
        return get_list_icon(size, theme=theme)
    elif nav_type == "pending":
        c = QColor(100, 100, 110) if theme == "light" else QColor(150, 150, 150)
        return get_check_icon(size, color=c, theme=theme)
    elif nav_type == "done":
        return get_checked_icon(size, theme=theme)
    return get_list_icon(size, theme=theme)


def get_toolbar_icon(icon_type, size=24, theme="dark"):
    if icon_type == "add":
        return get_add_icon(size, theme=theme)
    elif icon_type == "list":
        return get_list_icon(size, theme=theme)
    elif icon_type == "settings":
        return get_gear_icon(size, theme=theme)
    elif icon_type == "theme_sun":
        return get_sun_icon(size, theme=theme)
    elif icon_type == "theme_moon":
        return get_moon_icon(size, theme=theme)
    return get_list_icon(size, theme=theme)


def get_todo_item_icons(theme):
    if theme == "light":
        return {
            "clock": QColor(140, 140, 150),
            "edit": QColor(100, 100, 110),
            "delete": QColor(190, 90, 90),
            "time_pending": "#2979ff",
            "time_done": "#999999",
            "title_color": "#1a1a2e",
            "title_done": "#999999",
        }
    else:
        return {
            "clock": QColor(150, 150, 150),
            "edit": QColor(180, 180, 180),
            "delete": QColor(200, 110, 110),
            "time_pending": "#4fc3f7",
            "time_done": "#6b7280",
            "title_color": "#f0f0f0",
            "title_done": "#6b7280",
        }