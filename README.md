# TinyPNG Compressor

基于 [TinyPNG](https://tinypng.com/) 的桌面批量图片压缩工具，支持 API 和网页两种模式。

## 功能

- **批量压缩** — 支持拖拽/选择多张图片或文件夹，一次处理
- **双模式** — API 模式（官方 tinify 接口，支持并发）和网页模式（自动化 tinypng.com）
- **实时进度** — 多线程后台压缩，界面实时显示进度
- **历史记录** — SQLite 存储所有压缩记录，支持搜索、筛选、分页
- **压缩对比** — 原图与压缩图并排对比，显示压缩率和节省空间
- **便携绿色** — 所有数据（数据库、配置）跟随 exe 存放，即拷即用

### 支持格式

PNG / JPG / WebP / AVIF

## 安装方式

### 方式一：安装包（推荐）

下载 `TinyPNGCompressor_Setup_v1.0.0.exe`，按向导完成安装：
- 自动创建开始菜单和桌面快捷方式
- 包含卸载程序

### 方式二：绿色版

直接下载 `TinyPNGCompressor.exe`，放到任意目录双击运行：
- 无需安装，即刻使用
- 数据库和配置文件自动在 exe 同目录生成
- 删除 exe 即完成卸载

## 使用步骤

1. **获取 API Key**（API 模式必需）
   - 访问 [tinify.com/developers](https://tinify.com/developers) 注册
   - 免费额度：每月 500 次压缩
2. **配置** — 打开「设置」填入 API Key，点击「验证」
3. **添加图片** — 拖拽图片/文件夹到窗口，或点击「添加文件」
4. **选择输出目录** — 默认为原图所在目录，可更改
5. **开始压缩** — 点击按钮，等待完成
6. **查看历史** — 切换到「历史记录」标签页查看所有记录

> 如果不想注册 API Key，可在设置中将模式切换为「网页模式」。

## 开发

### 环境要求

- Python 3.10+
- Windows 10/11

### 本地运行

```bash
pip install -r requirements.txt
python main.py
```

### 打包

```bash
# 绿色版 exe
python build_exe.py

# 安装包 (需要 Inno Setup 6)
iscc setup.iss
```

### 项目结构

```
tinypng/
├── main.py                    # 入口
├── requirements.txt           # Python 依赖
├── build_exe.py               # PyInstaller 打包脚本
├── setup.iss                  # Inno Setup 安装包脚本
├── src/
│   ├── core/
│   │   ├── base_engine.py     # 压缩引擎抽象基类
│   │   ├── api_engine.py      # Tinify API 引擎
│   │   └── web_engine.py      # 网页自动化引擎
│   ├── gui/
│   │   ├── main_window.py     # 主窗口
│   │   ├── compress_tab.py    # 压缩操作页
│   │   ├── history_tab.py     # 历史记录页
│   │   ├── settings_dialog.py # 设置对话框
│   │   └── widgets/
│   │       ├── image_list.py      # 拖拽添加控件
│   │       ├── progress_panel.py  # 进度面板
│   │       └── compare_dialog.py  # 压缩对比弹窗
│   └── data/
│       ├── database.py        # SQLite 操作
│       └── settings_manager.py# 配置管理
└── resources/                 # 资源文件
```

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI | PySide6 (Qt for Python) |
| API 引擎 | [tinify](https://pypi.org/project/tinify/) |
| 网页引擎 | [DrissionPage](https://github.com/g1879/DrissionPage) |
| 图片处理 | Pillow |
| 打包 | PyInstaller + Inno Setup |
| 数据存储 | SQLite + QSettings |

## License

MIT
