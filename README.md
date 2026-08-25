# Todo 桌面常驻提醒工具

简单好用的 Windows 桌面常驻待办提醒工具，基于 Python + PySide6 开发，支持桌面悬浮卡片、个性化磨砂玻璃背景、完整的提醒与截止时间管理。

## ✨ 功能特性

- 🎯 **主界面待办管理**：全功能待办列表（全部 / 未完成 / 已完成），快速添加、编辑、删除
- 🪟 **桌面常驻卡片**：无边框置顶悬浮窗，支持自由拖拽移动 + 边缘 8 向缩放（带光标提示）
- 🎨 **卡片外观个性化**
  - 磨砂玻璃背景（默认）：经典半透明毛玻璃质感，支持日间 / 夜间两套配色
  - 自定义图片背景：上传本地图片（PNG / JPG / WEBP 等），自动居中裁剪适配
  - 背景透明度滑块：30% ~ 100% 任意调节
- 🌗 **双主题切换**：日间 / 夜间模式一键切换（工具栏按钮 / 设置）
- ⏰ **时间与提醒**
  - 每个待办独立设置**是否开启提醒**，关闭后不打扰
  - 提醒时间支持精确到**年-月-日 时:分**
  - 提前提醒：预设 5 / 10 / 15 / 30 分钟、1 / 2 / 3 / 12 / 24 小时，或自定义分钟数（最多 24 小时）
  - 截止时间：完全自定义年-月-日 时:分
- 📝 **自动记录**：创建时间由系统自动生成，无需手动填写
- 🔔 **提醒轮询**：自定义检查间隔（1~1440 分钟），到期弹窗提醒
- 🚀 **开机自启**：在 Windows 启动文件夹创建快捷方式，登录后自动运行
- 🎨 **全部图标程序化绘制**（QPainter）：不依赖任何外部图片 / emoji，分辨率无损

## 📁 项目文件结构

| 文件 | 说明 |
|---|---|
| `main.py` | 程序入口 |
| `main_window.py` | 主窗口，待办管理界面、主题切换、定时提醒检查 |
| `desktop_card.py` | 桌面悬浮卡片（磨砂玻璃/图片背景渲染、拖拽移动、边缘缩放） |
| `todo_dialogs.py` | 添加 / 编辑待办对话框（截止时间、提醒开关、提前提醒） |
| `settings_dialog.py` | 设置对话框（开机自启、检查间隔、外观、卡片模式/透明度/图片） |
| `autostart_manager.py` | Windows 开机自启管理（启动文件夹快捷方式） |
| `todo_model.py` | 数据模型，JSON 持久化（`todos.json`, `settings.json`） |
| `icon_utils.py` | 所有图标程序化绘制（弯月、太阳、编辑、删除、齿轮…） |
| `style.qss` / `style_light.qss` | 夜间 / 日间主题全局样式表 |
| `requirements.txt` | 依赖列表 |
| `todos.json` | 待办数据（运行后生成） |
| `settings.json` | 全局设置（运行后生成） |

## 🚀 快速开始

### 环境要求

- Windows 10 / 11
- Python 3.9+

### 开发环境运行

```powershell
python -m pip install -r requirements.txt
python main.py
```

### 打包为单文件 EXE（可选）

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean Todo提醒.spec
```

或手动指定资源文件（不推荐，优先用 spec 文件）：

```powershell
pyinstaller --noconfirm --onefile --windowed ^
  --name "Todo提醒" ^
  --add-data "style.qss;." ^
  --add-data "style_light.qss;." ^
  main.py
```

生成的可执行文件位于 `dist/Todo提醒.exe`。打包后的 EXE 内置 QSS 样式表，无需外部文件；待办和设置数据保存在 EXE 同级目录下（`todos.json` / `settings.json`）。

## ⚙️ 配置项说明

设置保存在程序运行目录的 `settings.json` 中，主要字段：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `card_visible` | `true` | 是否显示桌面悬浮卡片 |
| `check_interval_min` | `1` | 提醒轮询间隔，单位分钟（1~1440） |
| `theme` | `"dark"` | 主题：`dark` 夜间 / `light` 日间 |
| `card_bg_mode` | `"glass"` | 卡片背景模式：`glass` 磨砂玻璃 / `image` 自定义图片 |
| `card_bg_image` | `""` | 自定义图片绝对路径（仅 image 模式） |
| `card_bg_opacity` | `88` | 卡片背景不透明度 %（30~100） |

## ⚠️ 注意事项

1. **开机自启功能**仅在 Windows 下可用，依赖 `pywin32`（requirements 中已包含）。开发环境下快捷方式会指向 `pythonw.exe` + `main.py` 参数；打包后的 EXE 会直接作为目标。
2. 自定义图片背景引用的是用户选择时的**绝对路径**，图片删除 / 改名后会自动回退到磨砂玻璃渲染。
3. 卡片最小尺寸 `240×280` 像素，无最大尺寸限制；在卡片 4 条边的 10px 范围内或 4 角处会出现双向/斜向调节光标，按住拖动即可缩放。
4. 程序使用 JSON 本地存储数据。**开发模式**下数据文件（`todos.json` / `settings.json`）在源码目录；**EXE 模式**下在 EXE 同级目录，不会随 PyInstaller 临时目录丢失。
5. 打包请务必使用 `Todo提醒.spec` 文件（或 `--add-data` 手动带上 `style.qss` 和 `style_light.qss`），否则样式表无法被打包进去，界面会显示为 Qt 默认样式（无背景色、无圆角、无磨砂效果）。