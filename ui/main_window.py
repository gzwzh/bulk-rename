"""
主窗口 - 批量重命名
"""
from core.i18n import _
import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QLabel, QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QMenu, QMenuBar,
    QStatusBar, QGridLayout, QFrame, QAbstractItemView, QToolButton,
    QToolTip, QSizePolicy
)
from PyQt6.QtCore import Qt, QDir, QModelIndex, QPoint, QThread, pyqtSignal, QObject, QUrl, QTimer
from PyQt6.QtGui import QFileSystemModel, QAction, QDragEnterEvent, QDropEvent, QPixmap, QIcon, QDesktopServices
from ui.update_dialog import UpdateDialog


class FolderSizeWorker(QObject):
    """后台计算文件夹大小的工作线程"""
    size_calculated = pyqtSignal(int, str, int)  # row, path, size (-2表示超过限制)
    finished = pyqtSignal()
    
    # 文件夹大小计算限制：100MB
    SIZE_LIMIT = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, folders: list):
        super().__init__()
        self.folders = folders  # [(row, path), ...]
        self._is_running = True
    
    def stop(self):
        """停止计算"""
        self._is_running = False
    
    def run(self):
        """计算所有文件夹大小"""
        for row, folder_path in self.folders:
            if not self._is_running:
                break
            try:
                size = self._calculate_folder_size(folder_path)
                if self._is_running:
                    self.size_calculated.emit(row, folder_path, size)
            except (OSError, PermissionError):
                if self._is_running:
                    self.size_calculated.emit(row, folder_path, -1)
        self.finished.emit()
    
    def _calculate_folder_size(self, folder_path: str) -> int:
        """计算单个文件夹大小，超过100MB时停止计算并返回-2"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                if not self._is_running:
                    return 0
                for filename in filenames:
                    if not self._is_running:
                        return 0
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                        # 超过100MB限制，停止计算
                        if total_size > self.SIZE_LIMIT:
                            return -2  # 返回-2表示超过限制
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total_size

from core.rename_engine import RenameEngine, RenameRules, CaseMode
from core.config_manager import ConfigManager
from core.version import VERSION, SOFTWARE_ID
from core.feedback_api import FeedbackAPI
from .auth_integration import AuthIntegration
import requests
import subprocess


def get_file_type_map():
    """获取动态翻译的文件类型映射"""
    return {
        # 图片文件
        '.jpg': _('main_window.file_type.jpg'),
        '.jpeg': _('main_window.file_type.jpeg'),
        '.png': _('main_window.file_type.png'),
        '.gif': _('main_window.file_type.gif'),
        '.bmp': _('main_window.file_type.bmp'),
        '.ico': _('main_window.file_type.ico'),
        '.svg': _('main_window.file_type.svg'),
        '.webp': _('main_window.file_type.webp'),
        '.tiff': _('main_window.file_type.tiff'),
        '.tif': _('main_window.file_type.tif'),
        '.psd': _('main_window.file_type.psd'),
        '.raw': _('main_window.file_type.raw'),
        
        # 文档文件
        '.txt': _('main_window.file_type.txt'),
        '.doc': _('main_window.file_type.doc'),
        '.docx': _('main_window.file_type.docx'),
        '.pdf': _('main_window.file_type.pdf'),
        '.rtf': _('main_window.file_type.rtf'),
        '.odt': _('main_window.file_type.odt'),
        '.md': _('main_window.file_type.md'),
        
        # 表格文件
        '.xls': _('main_window.file_type.xls'),
        '.xlsx': _('main_window.file_type.xlsx'),
        '.csv': _('main_window.file_type.csv'),
        '.ods': _('main_window.file_type.ods'),
        
        # 演示文件
        '.ppt': _('main_window.file_type.ppt'),
        '.pptx': _('main_window.file_type.pptx'),
        '.odp': _('main_window.file_type.odp'),
        
        # 压缩文件
        '.zip': _('main_window.file_type.zip'),
        '.rar': _('main_window.file_type.rar'),
        '.7z': _('main_window.file_type.7z'),
        '.tar': _('main_window.file_type.tar'),
        '.gz': _('main_window.file_type.gz'),
        '.bz2': _('main_window.file_type.bz2'),
        
        # 音频文件
        '.mp3': _('main_window.file_type.mp3'),
        '.wav': _('main_window.file_type.wav'),
        '.flac': _('main_window.file_type.flac'),
        '.aac': _('main_window.file_type.aac'),
        '.ogg': _('main_window.file_type.ogg'),
        '.wma': _('main_window.file_type.wma'),
        '.m4a': _('main_window.file_type.m4a'),
        
        # 视频文件
        '.mp4': _('main_window.file_type.mp4'),
        '.avi': _('main_window.file_type.avi'),
        '.mkv': _('main_window.file_type.mkv'),
        '.mov': _('main_window.file_type.mov'),
        '.wmv': _('main_window.file_type.wmv'),
        '.flv': _('main_window.file_type.flv'),
        '.webm': _('main_window.file_type.webm'),
        '.m4v': _('main_window.file_type.m4v'),
        '.rmvb': _('main_window.file_type.rmvb'),
        '.rm': _('main_window.file_type.rm'),
        
        # 可执行文件
        '.exe': _('main_window.file_type.exe'),
        '.msi': _('main_window.file_type.msi'),
        '.bat': _('main_window.file_type.bat'),
        '.cmd': _('main_window.file_type.cmd'),
        '.ps1': _('main_window.file_type.ps1'),
        '.sh': _('main_window.file_type.sh'),
        
        # 代码文件
        '.py': _('main_window.file_type.py'),
        '.js': _('main_window.file_type.js'),
        '.ts': _('main_window.file_type.ts'),
        '.html': _('main_window.file_type.html'),
        '.htm': _('main_window.file_type.htm'),
        '.css': _('main_window.file_type.css'),
        '.java': _('main_window.file_type.java'),
        '.c': _('main_window.file_type.c'),
        '.cpp': _('main_window.file_type.cpp'),
        '.h': _('main_window.file_type.h'),
        '.hpp': _('main_window.file_type.hpp'),
        '.cs': _('main_window.file_type.cs'),
        '.go': _('main_window.file_type.go'),
        '.rs': _('main_window.file_type.rs'),
        '.php': _('main_window.file_type.php'),
        '.rb': _('main_window.file_type.rb'),
        '.swift': _('main_window.file_type.swift'),
        '.kt': _('main_window.file_type.kt'),
        '.sql': _('main_window.file_type.sql'),
        
        # 数据文件
        '.json': _('main_window.file_type.json'),
        '.xml': _('main_window.file_type.xml'),
        '.yaml': _('main_window.file_type.yaml'),
        '.yml': _('main_window.file_type.yml'),
        '.ini': _('main_window.file_type.ini'),
        '.cfg': _('main_window.file_type.cfg'),
        '.conf': _('main_window.file_type.conf'),
        '.log': _('main_window.file_type.log'),
        '.db': _('main_window.file_type.db'),
        '.sqlite': _('main_window.file_type.sqlite'),
        
        # 快捷方式
        '.lnk': _('main_window.file_type.lnk'),
        '.url': _('main_window.file_type.url'),
        
        # 字体文件
        '.ttf': _('main_window.file_type.ttf'),
        '.otf': _('main_window.file_type.otf'),
        '.woff': _('main_window.file_type.woff'),
        '.woff2': _('main_window.file_type.woff2'),
        
        # 其他
        '.iso': _('main_window.file_type.iso'),
        '.img': _('main_window.file_type.img'),
        '.dll': _('main_window.file_type.dll'),
        '.sys': _('main_window.file_type.sys'),
        '.tmp': _('main_window.file_type.tmp'),
        '.bak': _('main_window.file_type.bak'),
    }


def get_file_type_description(filename: str) -> str:
    """根据文件名获取文件类型描述"""
    ext = os.path.splitext(filename)[1].lower()
    file_type_map = get_file_type_map()
    if ext in file_type_map:
        return file_type_map[ext]
    elif ext:
        # 未知扩展名，显示为 "XXX 文件"
        return _('main_window.file_type.unknown_file').format(ext=ext[1:].upper())
    else:
        return _('main_window.file_type.file')


def get_module_help_info():
    """获取动态翻译的模块帮助信息"""
    return {
        "regex": {
            "title": _("main_window.help.regex.title"),
            "content": _("main_window.help.regex.content")
        },
        "replace": {
            "title": _("main_window.help.replace.title"),
            "content": _("main_window.help.replace.content")
        },
        "remove": {
            "title": _("main_window.help.remove.title"),
            "content": _("main_window.help.remove.content")
        },
        "add": {
            "title": _("main_window.help.add.title"),
            "content": _("main_window.help.add.content")
        },
        "auto_date": {
            "title": _("main_window.help.auto_date.title"),
            "content": _("main_window.help.auto_date.content")
        },
        "number": {
            "title": _("main_window.help.number.title"),
            "content": _("main_window.help.number.content")
        },
        "file": {
            "title": _("main_window.help.file.title"),
            "content": _("main_window.help.file.content")
        },
        "case": {
            "title": _("main_window.help.case.title"),
            "content": _("main_window.help.case.content")
        },
        "move_copy": {
            "title": _("main_window.help.move_copy.title"),
            "content": _("main_window.help.move_copy.content")
        },
        "folder": {
            "title": _("main_window.help.folder.title"),
            "content": _("main_window.help.folder.content")
        },
        "extension": {
            "title": _("main_window.help.extension.title"),
            "content": _("main_window.help.extension.content")
        },
        "selection": {
            "title": _("main_window.help.selection.title"),
            "content": _("main_window.help.selection.content")
        },
        "new_location": {
            "title": _("main_window.help.new_location.title"),
            "content": _("main_window.help.new_location.content")
        }
    }



class ModuleHelpPopup(QLabel):
    """模块帮助弹出框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            QLabel {
                background-color: #FFFFD0;
                border: 1px solid #C0C0A0;
                border-radius: 4px;
                padding: 10px;
                font-size: 9pt;
            }
        """)
        self.setWordWrap(True)
        self.setMaximumWidth(380)
        self.setMinimumWidth(260)
    
    def showHelp(self, title: str, content: str, pos: QPoint):
        """显示帮助信息"""
        html = f"<b style='font-size:10pt;color:#333;'>{title}</b><hr style='margin:5px 0;'>"
        html += f"<div style='color:#444;line-height:1.4;'>{content.replace(chr(10), '<br>')}</div>"
        self.setText(html)
        self.adjustSize()
        
        # 确保提示框在屏幕内
        screen = self.screen().availableGeometry() if self.screen() else None
        if screen:
            if pos.x() + self.width() > screen.right():
                pos.setX(screen.right() - self.width() - 10)
            if pos.y() + self.height() > screen.bottom():
                pos.setY(pos.y() - self.height() - 30)
        
        self.move(pos)
        self.show()


class ResetableGroupBox(QGroupBox):
    TITLE_KEY_ALIASES = {
        "number": "numbering",
        "file": "name",
        "folder": "folder_name",
    }

    TRANSLATABLE_TITLES = {
        "regex", "replace", "remove", "add", "auto_date", "numbering",
        "name", "case", "move_copy", "folder_name", "extension",
        "selection", "new_location",
    }
    """带重置按钮和帮助按钮的GroupBox"""
    
    # 共享的帮助弹出框
    _help_popup = None
    # 当前显示帮助的模块
    _current_help_module = None
    
    # 样式定义 - 紧凑布局
    STYLE_UNCHECKED = """
        QGroupBox {
            border: 2px solid #ccc;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 5px;
            padding: 0 4px;
            color: #666;
        }
        QGroupBox::indicator {
            width: 14px;
            height: 14px;
        }
        QGroupBox::indicator:unchecked {
            border: 2px solid #999;
            border-radius: 3px;
            background-color: #fff;
        }
        QGroupBox::indicator:unchecked:hover {
            border-color: #4CAF50;
            background-color: #e8f5e9;
        }
    """
    
    STYLE_CHECKED = """
        QGroupBox {
            border: 2px solid #4CAF50;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 15px;
            background-color: #f1f8e9;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 5px;
            padding: 0 4px;
            color: #2e7d32;
            font-weight: bold;
        }
        QGroupBox::indicator {
            width: 14px;
            height: 14px;
        }
        QGroupBox::indicator:checked {
            border: 2px solid #4CAF50;
            border-radius: 3px;
            background-color: #4CAF50;
            image: none;
        }
        QGroupBox::indicator:checked:hover {
            border-color: #388e3c;
            background-color: #388e3c;
        }
    """
    
    @classmethod
    def _normalize_title_key(cls, title: str) -> str:
        return cls.TITLE_KEY_ALIASES.get(title, title)

    def __init__(self, title: str, parent=None):
        # 如果 title 是预定义的 key，则翻译它
        title_key = self._normalize_title_key(title)
        translated_title = title
        if title_key in self.TRANSLATABLE_TITLES:
            translated_title = _(f"main_window.rules.{title_key}.title")
            
        super().__init__(translated_title, parent)
        self.reset_callback = None
        self._original_title = title # 保存原始 key 用于帮助信息
        self._original_title = title_key
        self._setup_buttons()
        self._setup_tooltip()
        self._update_style(False)
        # 连接toggled信号以更新样式，但保持子控件可用
        self.toggled.connect(self._on_toggled)

    def setTitle(self, title: str):
        """重写 setTitle 以支持通过 key 翻译"""
        title_key = self._normalize_title_key(title)
        translated_title = title
        if title_key in self.TRANSLATABLE_TITLES:
            translated_title = _(f"main_window.rules.{title_key}.title")
        super().setTitle(translated_title)

    def retranslate_ui(self):
        """更新组件内部的翻译"""
        self.setTitle(self._original_title)
        self.help_btn.setToolTip(_("main_window.group_box.help_tooltip"))
        self.reset_btn.setToolTip(_("main_window.group_box.reset_tooltip"))
        self._setup_tooltip()
    
    def showEvent(self, event):
        """窗口显示时确保所有子控件启用"""
        super().showEvent(event)
        self._enable_all_children()
    
    def _setup_buttons(self):
        """设置帮助按钮和重置按钮"""
        # 帮助按钮 - 问号
        self.help_btn = QToolButton(self)
        self.help_btn.setText("?")
        self.help_btn.setToolTip(_("main_window.group_box.help_tooltip"))
        self.help_btn.setFixedSize(18, 18)
        self.help_btn.setStyleSheet("""
            QToolButton {
                background-color: #4a90d9;
                border: 1px solid #3a7bc8;
                border-radius: 9px;
                font-weight: bold;
                font-size: 10pt;
                color: white;
            }
            QToolButton:hover {
                background-color: #5ba0e9;
                border-color: #4a90d9;
            }
            QToolButton:pressed {
                background-color: #3a7bc8;
            }
        """)
        self.help_btn.clicked.connect(self._toggle_help)
        
        # 重置按钮
        self.reset_btn = QToolButton(self)
        self.reset_btn.setText("R")
        self.reset_btn.setToolTip(_("main_window.group_box.reset_tooltip"))
        self.reset_btn.setFixedSize(18, 18)
        self.reset_btn.setStyleSheet("""
            QToolButton {
                background-color: #e0e0e0;
                border: 1px solid #999;
                border-radius: 2px;
                font-weight: bold;
                font-size: 8pt;
                color: #333;
            }
            QToolButton:hover {
                background-color: #ffcccc;
                border-color: #cc6666;
                color: #990000;
            }
            QToolButton:pressed {
                background-color: #ff9999;
            }
        """)
        self.reset_btn.clicked.connect(self._on_reset)
    
    def _setup_tooltip(self):
        """设置简短的工具提示"""
        tooltip_text = _("main_window.group_box.module_status")
        self.setToolTip(tooltip_text)
    
    def _toggle_help(self):
        """切换帮助显示状态"""
        # 检查是否有该模块的帮助信息
        module_help_info = get_module_help_info()
        if self._original_title not in module_help_info:
            return
        
        # 创建共享的帮助弹出框
        if ResetableGroupBox._help_popup is None:
            ResetableGroupBox._help_popup = ModuleHelpPopup()
        
        popup = ResetableGroupBox._help_popup
        
        # 如果当前模块的帮助已显示，则隐藏
        if popup.isVisible() and ResetableGroupBox._current_help_module == self._original_title:
            popup.hide()
            ResetableGroupBox._current_help_module = None
            return
        
        # 显示帮助
        help_info = module_help_info[self._original_title]
        
        # 计算显示位置（在帮助按钮下方）
        btn_pos = self.help_btn.mapToGlobal(QPoint(0, self.help_btn.height() + 5))
        
        popup.showHelp(help_info["title"], help_info["content"], btn_pos)
        ResetableGroupBox._current_help_module = self._original_title
    
    def _on_toggled(self, checked: bool):
        """勾选状态变化时更新样式，但保持子控件始终可用"""
        self._update_style(checked)
        # 关键：无论勾选状态如何，都保持所有子控件启用
        self._enable_all_children()
    
    def _enable_all_children(self):
        """启用所有子控件，覆盖QGroupBox的默认禁用行为"""
        for child in self.findChildren(QWidget):
            child.setEnabled(True)
    
    def _update_style(self, checked: bool):
        """更新样式以反映当前状态"""
        if checked:
            self.setStyleSheet(self.STYLE_CHECKED)
        else:
            self.setStyleSheet(self.STYLE_UNCHECKED)
    
    def resizeEvent(self, event):
        """调整按钮位置"""
        super().resizeEvent(event)
        # 帮助按钮在重置按钮左边
        self.help_btn.move(self.width() - 44, 0)
        # 重置按钮在最右边
        self.reset_btn.move(self.width() - 22, 0)
    
    def set_reset_callback(self, callback):
        """设置重置回调函数"""
        self.reset_callback = callback
    
    def _on_reset(self):
        """重置按钮点击事件"""
        if self.reset_callback:
            self.reset_callback()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.engine = RenameEngine()
        self.config_manager = ConfigManager()
        self.file_list = []
        self.last_rules_state = None  # 保存上一次的规则状态用于恢复
        
        # 后台计算文件夹大小的线程
        self._folder_size_thread = None
        self._folder_size_worker = None
        self._pending_folder_sizes = []  # [(row, path), ...]
        
        # 初始化认证集成
        self.auth_integration = AuthIntegration(self)
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(_("main_window.title"))
        
        # 设置窗口图标
        icon_path = "inco.ico"
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, icon_path)
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setMinimumSize(1200, 800)
        self.resize(1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 启动自动检查更新（延迟调用，避免影响启动速度）
        QTimer.singleShot(3000, lambda: self.check_update(silent=True))
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # 创建操作栏（用于放置登录按钮和其他功能按钮）
        action_bar = self.create_action_bar()
        main_layout.addWidget(action_bar)
        
        # 上部分：文件浏览器和文件列表
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self.create_folder_tree())
        top_splitter.addWidget(self.create_file_table())
        top_splitter.setSizes([200, 950])
        
        # 下部分：重命名规则面板
        rules_widget = self.create_rules_panel()
        
        # 主分割器
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(rules_widget)
        main_splitter.setSizes([320, 380])
        
        main_layout.addWidget(main_splitter)
        
        # 状态栏 - 添加品牌标识在中间
        self._setup_status_bar()
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def create_action_bar(self) -> QWidget:
        """创建操作栏 - 用于放置登录按钮和其他功能按钮"""
        action_bar = QFrame()
        action_bar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 0px;
            }
        """)
        action_bar.setFixedHeight(38)
        
        layout = QHBoxLayout(action_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 左上角品牌区：图标 + 软件名
        self.header_brand = QWidget()
        header_brand_layout = QHBoxLayout(self.header_brand)
        header_brand_layout.setContentsMargins(0, 0, 12, 0)
        header_brand_layout.setSpacing(8)

        self.header_brand_icon = QLabel()
        brand_icon_path = "inco.ico"
        if hasattr(sys, '_MEIPASS'):
            candidate = os.path.join(sys._MEIPASS, brand_icon_path)
            if os.path.exists(candidate):
                brand_icon_path = candidate
        if os.path.exists(brand_icon_path):
            brand_pixmap = QPixmap(brand_icon_path)
            brand_pixmap = brand_pixmap.scaled(
                18, 18,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.header_brand_icon.setPixmap(brand_pixmap)
        self.header_brand_icon.setFixedSize(20, 20)
        header_brand_layout.addWidget(self.header_brand_icon)

        self.header_brand_text = QLabel(_("main_window.title"))
        self.header_brand_text.setStyleSheet(
            "QLabel { color: #222; font-size: 12pt; font-weight: 600; }"
        )
        header_brand_layout.addWidget(self.header_brand_text)
        layout.addWidget(self.header_brand)
        
        # 添加问题反馈按钮
        self.feedback_btn = QPushButton(_("main_window.feedback"))
        self.feedback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.feedback_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #eee;
                color: #333;
                border-color: #ccc;
            }
        """)
        self.feedback_btn.clicked.connect(self.open_feedback)
        layout.addWidget(self.feedback_btn)

        # 添加登录按钮和广告（通过认证集成）
        # 认证集成模块内部会自动添加一个弹簧(Stretch)将后续按钮推向右侧
        self.auth_integration.setup_ui_in_action_bar(action_bar, layout)
        
        return action_bar

    def open_feedback(self):
        """打开问题反馈页面"""
        try:
            url = FeedbackAPI.get_feedback_url()
            if url:
                opened = False
                if hasattr(self, 'auth_integration') and self.auth_integration:
                    opened, _ = self.auth_integration.auth_manager.open_external_url(url)
                if not opened:
                    QDesktopServices.openUrl(QUrl(url))
            else:
                QMessageBox.warning(self, _("main_window.error"), _("main_window.feedback_fail"))
        except Exception as e:
            QMessageBox.warning(self, _("main_window.error"), _("main_window.open_feedback_fail").format(error=str(e)))
    
    def _setup_status_bar(self):
        """设置状态栏 - 在中间添加 brand 标识和版本号"""
        status_bar = self.statusBar()
        
        # 创建左侧状态消息标签
        self.status_msg_label = QLabel(_("main_window.status_ready"))
        status_bar.addWidget(self.status_msg_label, 1)
        
        # 创建中间品牌标识容器
        self.brand_container = QWidget()
        brand_layout = QHBoxLayout(self.brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(6)
        
        # 添加图标
        self.status_icon_label = QLabel()
        icon_path = "鲲穹01.ico"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            pixmap = pixmap.scaledToHeight(16, Qt.TransformationMode.SmoothTransformation)
            self.status_icon_label.setPixmap(pixmap)
        self.status_icon_label.setFixedSize(16, 16)
        brand_layout.addWidget(self.status_icon_label)
        
        # 添加品牌文字
        self.brand_text = QLabel(_("main_window.title"))
        self.brand_text.setStyleSheet("QLabel { color: #999; font-size: 8pt; }")
        brand_layout.addWidget(self.brand_text)
        
        status_bar.addPermanentWidget(self.brand_container, 0)
        
        # 添加右侧版本号显示
        self.version_label = QLabel(_("main_window.version").format(version=VERSION) + "  ")
        self.version_label.setStyleSheet("QLabel { color: #666; font-size: 9pt; margin-right: 10px; }")
        status_bar.addPermanentWidget(self.version_label, 0)
    
    def _retranslate_combo(self, combo, key):
        """Helper to retranslate combo box items while preserving selection"""
        if not hasattr(self, combo):
            return
        widget = getattr(self, combo)
        current_index = widget.currentIndex()
        widget.blockSignals(True)
        widget.clear()
        widget.addItems(_(key))
        widget.setCurrentIndex(current_index)
        widget.blockSignals(False)

    def retranslate_ui(self):
        """重新翻译所有UI元素，实现实时语言切换"""
        # 1. 窗口标题
        self.setWindowTitle(_("main_window.title"))
        
        # 2. 状态栏消息
        if hasattr(self, 'status_msg_label'):
            self.status_msg_label.setText(_("main_window.status_ready"))
        if hasattr(self, 'header_brand_text'):
            self.header_brand_text.setText(_("main_window.title"))
        if hasattr(self, 'brand_text'):
            self.brand_text.setText(_("main_window.title"))
        if hasattr(self, 'version_label'):
            self.version_label.setText(_("main_window.version").format(version=VERSION) + "  ")
        
        # 3. 菜单栏
        if hasattr(self, 'file_menu'):
            self.file_menu.setTitle(_("main_window.menu.file"))
            self.open_action.setText(_("main_window.menu.open"))
            self.save_config_action.setText(_("main_window.menu.save"))
            self.save_config_as_action.setText(_("main_window.menu.save_as"))
            self.restore_config_action.setText(_("main_window.menu.restore"))
            self.import_pairs_action.setText(_("main_window.menu.import_pairs"))
            self.exit_action.setText(_("main_window.menu.exit"))
        
        if hasattr(self, 'action_menu'):
            self.action_menu.setTitle(_("main_window.menu.action"))
            self.rename_action.setText(_("main_window.menu.rename"))
            self.select_all_action.setText(_("main_window.menu.select_all"))
            self.deselect_all_action.setText(_("main_window.menu.deselect_all"))
            self.invert_selection_action.setText(_("main_window.menu.invert_selection"))
            self.select_clipboard_action.setText(_("main_window.menu.select_clipboard"))
            self.goto_path_action.setText(_("main_window.menu.goto_path"))
            self.refresh_files_action.setText(_("main_window.menu.refresh_files"))
            self.refresh_dir_action.setText(_("main_window.menu.refresh_dir"))
            self.toggle_tree_action.setText(_("main_window.menu.toggle_tree"))
            self.undo_action.setText(_("main_window.menu.undo_rename"))
            self.create_undo_action.setText(_("main_window.menu.create_undo_batch"))
        
        if hasattr(self, 'option_menu'):
            self.option_menu.setTitle(_("main_window.menu.options"))
            self.always_top_action.setText(_("main_window.menu.always_on_top"))
            self.show_hidden_action.setText(_("main_window.menu.show_hidden"))
            self.full_row_action.setText(_("main_window.menu.row_select"))
            self.zoom_action.setText(_("main_window.menu.zoom"))
            self.random_sort_action.setText(_("main_window.menu.random_sort"))
            self.clear_import_action.setText(_("main_window.menu.clear_import"))
            self.debug_names_action.setText(_("main_window.menu.debug_names"))
            self.char_convert_action.setText(_("main_window.menu.char_convert"))
        
        if hasattr(self, 'help_menu'):
            self.help_menu.setTitle(_("main_window.menu.help"))
            self.help_content_action.setText(_("main_window.menu.content"))
            self.help_index_action.setText(_("main_window.menu.index"))
            self.help_search_action.setText(_("main_window.menu.search"))
            self.tip_action.setText(_("main_window.menu.tip"))
            self.update_action.setText(_("main_window.menu.update"))
            self.about_action.setText(_("main_window.menu.about"))
        
        # 4. 表格标题
        self.update_header_sort_indicator()
        
        # 5. 操作栏
        if hasattr(self, 'feedback_btn'):
            self.feedback_btn.setText(_("main_window.feedback"))
        
        # 6. 文件夹浏览
        if hasattr(self, 'folder_tree_label'):
            self.folder_tree_label.setText(_("main_window.folder_tree.title"))
        if hasattr(self, 'pc_item'):
            self.pc_item.setText(0, _("main_window.folder_tree.this_pc"))
            # 注意：子目录名称可能需要重新加载，但通常它们是系统路径名或已翻译
        
        # 7. 文件表格工具栏
        if hasattr(self, 'load_folder_btn'):
            self.load_folder_btn.setText(_("main_window.buttons.select_folder"))
            self.load_folder_btn.setToolTip(_("main_window.buttons.select_folder_tooltip"))
        if hasattr(self, 'confirm_select_btn'):
            self.confirm_select_btn.setText(_("main_window.buttons.confirm_select"))
            self.confirm_select_btn.setToolTip(_("main_window.buttons.confirm_select_tooltip"))
        if hasattr(self, 'cancel_select_btn'):
            self.cancel_select_btn.setText(_("main_window.buttons.deselect"))
            self.cancel_select_btn.setToolTip(_("main_window.buttons.deselect_tooltip"))
        if hasattr(self, 'select_all_btn'):
            self.select_all_btn.setText(_("main_window.buttons.select_all"))
        if hasattr(self, 'clear_list_btn'):
            self.clear_list_btn.setText(_("main_window.buttons.clear_list"))
        
        # 8. 规则面板
        # 正则
        if hasattr(self, 'regex_check'):
            self.regex_check.retranslate_ui()
            self.regex_match_label.setText(_("main_window.rules.regex.match"))
            self.regex_replace_label.setText(_("main_window.rules.regex.replace"))
            self.regex_include_ext.setText(_("main_window.rules.regex.include_ext"))
        
        # 替换
        if hasattr(self, 'replace_check'):
            self.replace_check.retranslate_ui()
            self.replace_find_label.setText(_("main_window.rules.replace.find"))
            self.replace_with_label.setText(_("main_window.rules.replace.with"))
            self.replace_case_sensitive.setText(_("main_window.rules.replace.case_sensitive"))
            
        # 移除
        if hasattr(self, 'remove_check'):
            self.remove_check.retranslate_ui()
            self.remove_first_label.setText(_("main_window.rules.remove.first"))
            self.remove_last_label.setText(_("main_window.rules.remove.last"))
            self.remove_from_label.setText(_("main_window.rules.remove.from"))
            self.remove_to_label.setText(_("main_window.rules.remove.to"))
            self.remove_chars_label.setText(_("main_window.rules.remove.chars"))
            self.remove_words_label.setText(_("main_window.rules.remove.words"))
            self.remove_crop_label.setText(_("main_window.rules.remove.crop"))
            self._retranslate_combo('remove_crop_mode', "main_window.rules.remove.crop_modes")
            self.remove_crop_text.setPlaceholderText(_("main_window.rules.remove.crop_placeholder"))
            self.remove_digits.setText(_("main_window.rules.remove.digits"))
            self.remove_chinese.setText(_("main_window.rules.remove.chinese"))
            self.remove_trim.setText(_("main_window.rules.remove.trim"))
            self.remove_trim.setToolTip(_("main_window.rules.remove.trim_tooltip"))
            self.remove_chars_check.setText(_("main_window.rules.remove.chars_check"))
            self.remove_chars_check.setToolTip(_("main_window.rules.remove.chars_check_tooltip"))
            self.remove_ds.setText(_("main_window.rules.remove.ds"))
            self.remove_ds.setToolTip(_("main_window.rules.remove.ds_tooltip"))
            self.remove_accents.setText(_("main_window.rules.remove.accents"))
            self.remove_symbols.setText(_("main_window.rules.remove.symbols"))
            self.remove_lead_dots_label.setText(_("main_window.rules.remove.lead_dots"))
            self._retranslate_combo('remove_lead_dots', "main_window.rules.remove.lead_dots_modes")

        # 添加
        if hasattr(self, 'add_check'):
            self.add_check.retranslate_ui()
            self.add_prefix_label.setText(_("main_window.rules.add.prefix"))
            self.add_insert_label.setText(_("main_window.rules.add.insert"))
            self.add_insert_pos_label.setText(_("main_window.rules.add.pos"))
            self.add_suffix_label.setText(_("main_window.rules.add.suffix"))
            self.add_word_space.setText(_("main_window.rules.add.word_space"))

        # 自动日期
        if hasattr(self, 'auto_date_check'):
            self.auto_date_check.retranslate_ui()
            self.auto_date_mode_label.setText(_("main_window.rules.auto_date.mode"))
            self._retranslate_combo('auto_date_type', "main_window.rules.auto_date.modes")
            self.auto_date_type_label.setText(_("main_window.rules.auto_date.type"))
            self._retranslate_combo('auto_date_mode', "main_window.rules.auto_date.types")
            self.auto_date_format_label.setText(_("main_window.rules.auto_date.format"))
            # auto_date_format 是可编辑的，重新填充
            current_format = self.auto_date_format.currentText()
            self.auto_date_format.blockSignals(True)
            self.auto_date_format.clear()
            self.auto_date_format.addItems(_("main_window.rules.auto_date.formats"))
            self.auto_date_format.setCurrentText(current_format)
            self.auto_date_format.blockSignals(False)
            self.auto_date_sep_label.setText(_("main_window.rules.auto_date.sep"))
            self.auto_date_connect_label.setText(_("main_window.rules.auto_date.connect"))
            self.auto_date_custom_label.setText(_("main_window.rules.auto_date.custom"))
            self.auto_date_custom.setPlaceholderText(_("main_window.rules.auto_date.custom_placeholder"))
            self.auto_date_center.setText(_("main_window.rules.auto_date.center"))
            self.auto_date_distance_label.setText(_("main_window.rules.auto_date.distance"))

        # 编号
        if hasattr(self, 'numbering_check'):
            self.numbering_check.retranslate_ui()
            self.numbering_mode_label.setText(_("main_window.rules.numbering.mode"))
            self._retranslate_combo('numbering_mode', "main_window.rules.numbering.modes")
            self.numbering_at_label.setText(_("main_window.rules.numbering.at"))
            self.numbering_start_label.setText(_("main_window.rules.numbering.start"))
            self.numbering_increment_label.setText(_("main_window.rules.numbering.increment"))
            self.numbering_padding_label.setText(_("main_window.rules.numbering.padding"))
            self.numbering_sep_label.setText(_("main_window.rules.numbering.sep"))
            self.numbering_break_label.setText(_("main_window.rules.numbering.break"))
            self.numbering_folder.setText(_("main_window.rules.numbering.folder"))
            self.numbering_type_label.setText(_("main_window.rules.numbering.type"))
            self._retranslate_combo('numbering_type', "main_window.rules.numbering.types")
            self.numbering_roman_label.setText(_("main_window.rules.numbering.roman"))
            self._retranslate_combo('numbering_roman', "main_window.rules.numbering.roman_modes")

        # 文件名
        if hasattr(self, 'name_check'):
            self.name_check.retranslate_ui()
            self.name_mode_label.setText(_("main_window.rules.name.name"))
            self._retranslate_combo('name_mode', "main_window.rules.name.modes")
            self.name_fixed_label.setText(_("main_window.rules.name.fixed"))

        # 大小写
        if hasattr(self, 'case_check'):
            self.case_check.retranslate_ui()
            self.case_mode_label.setText(_("main_window.rules.case.mode"))
            self._retranslate_combo('case_mode', "main_window.rules.case.modes")
            self.case_digits.setText(_("main_window.rules.remove.digits"))
            self.case_symbols.setText(_("main_window.rules.remove.symbols"))
            self.case_exception_label.setText(_("main_window.rules.case.exception"))
            self.case_exception.setPlaceholderText(_("main_window.rules.case.exception"))

        # 移动/复制
        if hasattr(self, 'move_check'):
            self.move_check.retranslate_ui()
            self.move_copy_mode.setToolTip(_("main_window.rules.move_copy.mode"))
            self._retranslate_combo('move_copy_mode', "main_window.rules.move_copy.modes")
            self.move_from.setToolTip(_("main_window.rules.move_copy.from"))
            self.move_target.setToolTip(_("main_window.rules.move_copy.target"))
            self._retranslate_combo('move_target', "main_window.rules.move_copy.targets")
            self.move_count.setToolTip(_("main_window.rules.move_copy.count"))
            self.move_sep_label.setText(_("main_window.rules.move_copy.sep"))
            self.move_separator.setToolTip(_("main_window.rules.move_copy.sep"))

        # 文件夹名
        if hasattr(self, 'folder_name_check'):
            self.folder_name_check.retranslate_ui()
            self.folder_name_mode_label.setText(_("main_window.rules.folder_name.mode"))
            self._retranslate_combo('folder_name_mode', "main_window.rules.folder_name.modes")
            self.folder_name_sep_label.setText(_("main_window.rules.folder_name.sep"))
            self.folder_name_levels_label.setText(_("main_window.rules.folder_name.levels"))

        # 扩展名
        if hasattr(self, 'ext_check'):
            self.ext_check.retranslate_ui()
            self.ext_mode_label.setText(_("main_window.rules.extension.mode"))
            self._retranslate_combo('ext_mode', "main_window.rules.extension.modes")
            self.ext_fixed_label.setText(_("main_window.rules.extension.fixed"))
            self.ext_fixed.setPlaceholderText(_("main_window.rules.extension.fixed"))

        # 选择过滤
        if hasattr(self, 'filter_check'):
            self.filter_check.retranslate_ui()
            self.filter_label.setText(_("main_window.rules.selection.filter") + ":")
            self.filter_folders.setText(_("main_window.rules.selection.folders"))
            self.filter_hidden.setText(_("main_window.rules.selection.hidden"))
            self.filter_min_name_label.setText(_("main_window.rules.selection.min") + _("main_window.rules.selection.name_len"))
            self.filter_max_name_label.setText(_("main_window.rules.selection.max"))
            self.filter_case_sensitive.setText(_("main_window.rules.selection.case"))
            self.filter_files.setText(_("main_window.rules.selection.files"))
            self.filter_subfolders.setText(_("main_window.rules.selection.folders"))
            self.filter_min_path_label.setText(_("main_window.rules.selection.min") + _("main_window.rules.selection.path_len"))
            self.filter_max_path_label.setText(_("main_window.rules.selection.max"))

        # 新位置
        if hasattr(self, 'new_location_check'):
            self.new_location_check.retranslate_ui()
            self.new_location_path_label.setText(_("main_window.rules.new_location.path") + ":")
            self.new_location_copy.setText(_("main_window.rules.new_location.copy"))
        if hasattr(self, 'new_location_path'):
            self.new_location_path.setPlaceholderText("C:\\Example")

        # 操作按钮
        if hasattr(self, 'action_group'):
            self.action_group.setTitle(_("main_window.menu.action"))
        if hasattr(self, 'restore_btn'):
            self.restore_btn.setText(_("main_window.menu.restore"))
            self.restore_btn.setToolTip(_("main_window.menu.restore"))
        if hasattr(self, 'rename_btn'):
            self.rename_btn.setText(_("main_window.menu.rename"))
        if hasattr(self, 'reset_all_btn'):
            self.reset_all_btn.setText(_("main_window.menu.reset_all"))
        
        # 9. 路径显示前缀
        if hasattr(self, 'path_label'):
            path_text = self.path_label.text()
            prefix = _("main_window.file_table.path_prefix")
            not_selected = _("main_window.file_table.not_selected")
            
            # 无论当前语言如何，如果有实际路径（包含:或\），保留实际路径
            # 这里简单判断：如果不是默认的"未选择"状态，就提取真实路径
            if "未选择" in path_text or "Not Selected" in path_text or not_selected in path_text:
                self.path_label.setText(prefix + not_selected)
            elif ":" in path_text:
                # 提取实际路径部分
                actual_path = path_text.split(":", 1)[1].strip()
                # 去除可能存在的旧前缀
                if actual_path.startswith("未选择") or actual_path.startswith("Not Selected"):
                    self.path_label.setText(prefix + not_selected)
                else:
                    self.path_label.setText(prefix + actual_path)
            
        # 强制界面重绘
        self.update()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # --- 文件菜单 ---
        self.file_menu = menubar.addMenu(_("main_window.menu.file"))
        
        # 打开
        self.open_action = QAction(_("main_window.menu.open"), self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_folder)
        self.file_menu.addAction(self.open_action)
        
        self.file_menu.addSeparator()
        
        # 保存
        self.save_config_action = QAction(_("main_window.menu.save"), self)
        self.save_config_action.setShortcut("Ctrl+S")
        self.save_config_action.triggered.connect(self.save_config)
        self.file_menu.addAction(self.save_config_action)
        
        # 另存为
        self.save_config_as_action = QAction(_("main_window.menu.save_as"), self)
        self.save_config_as_action.triggered.connect(self.save_config_as)
        self.file_menu.addAction(self.save_config_as_action)
        
        # 恢复
        self.restore_config_action = QAction(_("main_window.menu.restore"), self)
        self.restore_config_action.triggered.connect(self.restore_config)
        self.file_menu.addAction(self.restore_config_action)
        
        self.file_menu.addSeparator()
        
        # 导入重命名配对
        self.import_pairs_action = QAction(_("main_window.menu.import_pairs"), self)
        self.import_pairs_action.triggered.connect(self.import_rename_pairs)
        self.file_menu.addAction(self.import_pairs_action)
        
        self.file_menu.addSeparator()
        
        # 退出
        self.exit_action = QAction(_("main_window.menu.exit"), self)
        self.exit_action.setShortcut("Alt+F4")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # --- 动作菜单 ---
        self.action_menu = menubar.addMenu(_("main_window.menu.action"))
        
        # 重命名
        self.rename_action = QAction(_("main_window.menu.rename"), self)
        self.rename_action.setShortcut("Ctrl+R")
        self.rename_action.triggered.connect(self.execute_rename)
        self.action_menu.addAction(self.rename_action)

        # 全选
        self.select_all_action = QAction(_("main_window.menu.select_all"), self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(self.select_all_files)
        self.action_menu.addAction(self.select_all_action)
        
        # 取消所有
        self.deselect_all_action = QAction(_("main_window.menu.deselect_all"), self)
        self.deselect_all_action.setShortcut("Ctrl+D")
        self.deselect_all_action.triggered.connect(self.deselect_all_files)
        self.action_menu.addAction(self.deselect_all_action)
        
        # 反向选择
        self.invert_selection_action = QAction(_("main_window.menu.invert_selection"), self)
        self.invert_selection_action.setShortcut("Ctrl+I")
        self.invert_selection_action.triggered.connect(self.invert_selection)
        self.action_menu.addAction(self.invert_selection_action)
        
        # 从剪贴板选择
        self.select_clipboard_action = QAction(_("main_window.menu.select_clipboard"), self)
        self.select_clipboard_action.triggered.connect(self.select_from_clipboard)
        self.action_menu.addAction(self.select_clipboard_action)
        
        self.action_menu.addSeparator()
        
        # 转跳到路径
        self.goto_path_action = QAction(_("main_window.menu.goto_path"), self)
        self.goto_path_action.setShortcut("Ctrl+J")
        self.goto_path_action.triggered.connect(self.goto_path)
        self.action_menu.addAction(self.goto_path_action)
        
        self.action_menu.addSeparator()
        
        # 刷新文件
        self.refresh_files_action = QAction(_("main_window.menu.refresh_files"), self)
        self.refresh_files_action.setShortcut("F5")
        self.refresh_files_action.triggered.connect(self.refresh_files)
        self.action_menu.addAction(self.refresh_files_action)
        
        # 刷新目录
        self.refresh_dir_action = QAction(_("main_window.menu.refresh_dir"), self)
        self.refresh_dir_action.setShortcut("Ctrl+F5")
        self.refresh_dir_action.triggered.connect(self.refresh_directory)
        self.action_menu.addAction(self.refresh_dir_action)
        
        # 显示/隐藏树状目录
        self.toggle_tree_action = QAction(_("main_window.menu.toggle_tree"), self)
        self.toggle_tree_action.setShortcut("F11")
        self.toggle_tree_action.triggered.connect(self.toggle_folder_tree)
        self.action_menu.addAction(self.toggle_tree_action)
        
        self.action_menu.addSeparator()
        
        # 撤消重命名
        self.undo_action = QAction(_("main_window.menu.undo_rename"), self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo_rename)
        self.action_menu.addAction(self.undo_action)
        
        # 创建撤消批处理
        self.create_undo_action = QAction(_("main_window.menu.create_undo_batch"), self)
        self.create_undo_action.setShortcut("Ctrl+B")
        self.create_undo_action.triggered.connect(self.create_undo_batch)
        self.action_menu.addAction(self.create_undo_action)
        
        # --- 选项菜单 ---
        self.option_menu = menubar.addMenu(_("main_window.menu.options"))
        
        # 总在最前
        self.always_top_action = QAction(_("main_window.menu.always_on_top"), self)
        self.always_top_action.setCheckable(True)
        self.always_top_action.triggered.connect(self.toggle_always_on_top)
        self.option_menu.addAction(self.always_top_action)
        
        # 显示隐藏文件
        self.show_hidden_action = QAction(_("main_window.menu.show_hidden"), self)
        self.show_hidden_action.setCheckable(True)
        self.show_hidden_action.triggered.connect(self.toggle_show_hidden)
        self.option_menu.addAction(self.show_hidden_action)
        
        # 整行选择
        self.full_row_action = QAction(_("main_window.menu.row_select"), self)
        self.full_row_action.setCheckable(True)
        self.full_row_action.triggered.connect(self.toggle_row_selection)
        self.option_menu.addAction(self.full_row_action)
        
        self.option_menu.addSeparator()
        
        # 最大化切换
        self.zoom_action = QAction(_("main_window.menu.zoom"), self)
        self.zoom_action.setShortcut("F8")
        self.zoom_action.triggered.connect(self.toggle_zoom)
        self.option_menu.addAction(self.zoom_action)
        
        # 随机排序
        self.random_sort_action = QAction(_("main_window.menu.random_sort"), self)
        self.random_sort_action.triggered.connect(self.random_sort)
        self.option_menu.addAction(self.random_sort_action)
        
        # 清除导入
        self.clear_import_action = QAction(_("main_window.menu.clear_import"), self)
        self.clear_import_action.triggered.connect(self.clear_import_pairs)
        self.option_menu.addAction(self.clear_import_action)
        
        self.option_menu.addSeparator()
        
        # 调试新名称
        self.debug_names_action = QAction(_("main_window.menu.debug_names"), self)
        self.debug_names_action.triggered.connect(self.debug_new_names)
        self.option_menu.addAction(self.debug_names_action)
        
        # 字符转换
        self.char_convert_action = QAction(_("main_window.menu.char_convert"), self)
        self.char_convert_action.setShortcut("Ctrl+F6")
        self.char_convert_action.triggered.connect(self.show_char_convert)
        self.option_menu.addAction(self.char_convert_action)
        
        # --- 帮助菜单 ---
        self.help_menu = menubar.addMenu(_("main_window.menu.help"))
        
        # 内容
        self.help_content_action = QAction(_("main_window.menu.content"), self)
        self.help_content_action.setShortcut("F1")
        self.help_content_action.triggered.connect(self.show_help_content)
        self.help_menu.addAction(self.help_content_action)
        
        # 索引
        self.help_index_action = QAction(_("main_window.menu.index"), self)
        self.help_index_action.triggered.connect(self.show_help_index)
        self.help_menu.addAction(self.help_index_action)
        
        # 搜索
        self.help_search_action = QAction(_("main_window.menu.search"), self)
        self.help_search_action.triggered.connect(self.show_help_search)
        self.help_menu.addAction(self.help_search_action)
        
        self.help_menu.addSeparator()
        
        # 每日提示
        self.tip_action = QAction(_("main_window.menu.tip"), self)
        self.tip_action.triggered.connect(self.show_daily_tip)
        self.help_menu.addAction(self.tip_action)
        
        self.help_menu.addSeparator()
        
        # 检查更新
        self.update_action = QAction(_("main_window.menu.update"), self)
        self.update_action.triggered.connect(self.check_update)
        self.help_menu.addAction(self.update_action)
        
        # 关于
        self.about_action = QAction(_("main_window.menu.about"), self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)

    
    def create_folder_tree(self) -> QWidget:
        """创建文件夹树 - 显示此电脑结构"""
        from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
        from PyQt6.QtGui import QIcon
        import ctypes
        import string
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.folder_tree_label = QLabel(_("main_window.folder_tree.title"))
        self.folder_tree_label.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(self.folder_tree_label)
        
        # 使用QTreeWidget创建自定义树结构
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self.on_tree_item_clicked)
        self.folder_tree.itemExpanded.connect(self.on_tree_item_expanded)
        
        # 创建"此电脑"根节点
        self.pc_item = QTreeWidgetItem(self.folder_tree, [_("main_window.folder_tree.this_pc")])
        self.pc_item.setData(0, Qt.ItemDataRole.UserRole, "")  # 空路径表示根
        
        # 获取用户文件夹路径
        user_home = os.path.expanduser("~")
        
        # 用户特殊文件夹列表
        user_folders = [
            (_("main_window.folder_tree.desktop"), os.path.join(user_home, "Desktop")),
            (_("main_window.folder_tree.documents"), os.path.join(user_home, "Documents")),
            (_("main_window.folder_tree.downloads"), os.path.join(user_home, "Downloads")),
            (_("main_window.folder_tree.pictures"), os.path.join(user_home, "Pictures")),
            (_("main_window.folder_tree.videos"), os.path.join(user_home, "Videos")),
            (_("main_window.folder_tree.music"), os.path.join(user_home, "Music")),
        ]
        
        # 添加用户文件夹
        for folder_name, folder_path in user_folders:
            if os.path.exists(folder_path):
                item = QTreeWidgetItem(self.pc_item, [folder_name])
                item.setData(0, Qt.ItemDataRole.UserRole, folder_path)
                # 添加占位子项以显示展开箭头
                if self._has_subdirs(folder_path):
                    placeholder = QTreeWidgetItem(item, [""])
                    placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
        
        # 获取所有磁盘驱动器
        drives = self._get_drives()
        for drive_letter, drive_name in drives:
            if os.name == 'nt':
                drive_path = f"{drive_letter}:\\"
                display_name = f"{drive_name} ({drive_letter}:)"
            else:
                drive_path = drive_letter
                display_name = drive_name
                
            item = QTreeWidgetItem(self.pc_item, [display_name])
            item.setData(0, Qt.ItemDataRole.UserRole, drive_path)
            # 添加占位子项以显示展开箭头
            if self._has_subdirs(drive_path):
                placeholder = QTreeWidgetItem(item, [""])
                placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
        
        # 展开"此电脑"节点
        self.pc_item.setExpanded(True)
        
        layout.addWidget(self.folder_tree)
        return widget
    
    def _get_drives(self):
        """获取所有磁盘驱动器"""
        import string
        drives = []
        
        # Windows 平台
        if os.name == 'nt':
            import ctypes
            try:
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive_path = f"{letter}:\\"
                        # 获取驱动器类型
                        drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                        # 2=可移动, 3=本地磁盘, 4=网络, 5=光驱, 6=RAM
                        if drive_type in (2, 3, 4, 5, 6):
                            try:
                                # 获取卷标
                                volume_name = ctypes.create_unicode_buffer(1024)
                                ctypes.windll.kernel32.GetVolumeInformationW(
                                    drive_path, volume_name, 1024, None, None, None, None, 0
                                )
                                name = volume_name.value if volume_name.value else _("main_window.folder_tree.local_disk")
                            except:
                                name = _("main_window.folder_tree.local_disk")
                            drives.append((letter, name))
                    bitmask >>= 1
            except Exception as e:
                print(f"Error getting Windows drives: {e}")
        
        # Linux / Unix 平台
        else:
            # 在 Linux 下通常显示根目录或挂载点
            # 简化处理：显示根目录 / 
            drives.append(("/", _("main_window.folder_tree.root_directory", "Root Directory")))
            
            # 如果是 WSL，尝试获取 Windows 的挂载磁盘
            if os.path.exists("/mnt"):
                for entry in os.listdir("/mnt"):
                    mnt_path = os.path.join("/mnt", entry)
                    if os.path.isdir(mnt_path) and len(entry) == 1: # c, d, e 等
                        drives.append((mnt_path, f"{entry.upper()} { _('main_window.folder_tree.disk', 'Disk') }"))
                        
        return drives
    
    def _has_subdirs(self, path):
        """检查路径是否有子目录"""
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            return True
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass
        return False
    
    def on_tree_item_clicked(self, item, column):
        """树节点点击事件"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path and path != "__placeholder__":
            self.load_folder(path)
    
    def on_tree_item_expanded(self, item):
        """树节点展开事件 - 延迟加载子目录"""
        from PyQt6.QtWidgets import QTreeWidgetItem
        
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or path == "__placeholder__":
            return
        
        # 检查是否有占位子项
        if item.childCount() == 1:
            child = item.child(0)
            if child.data(0, Qt.ItemDataRole.UserRole) == "__placeholder__":
                # 移除占位项
                item.removeChild(child)
                # 加载实际子目录
                self._load_subdirs(item, path)
    
    def _load_subdirs(self, parent_item, path):
        """加载子目录"""
        from PyQt6.QtWidgets import QTreeWidgetItem
        
        try:
            with os.scandir(path) as entries:
                dirs = []
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            dirs.append((entry.name, entry.path))
                    except (PermissionError, OSError):
                        continue
                
                # 按名称排序
                dirs.sort(key=lambda x: x[0].lower())
                
                for dir_name, dir_path in dirs:
                    item = QTreeWidgetItem(parent_item, [dir_name])
                    item.setData(0, Qt.ItemDataRole.UserRole, dir_path)
                    # 检查是否有子目录
                    if self._has_subdirs(dir_path):
                        placeholder = QTreeWidgetItem(item, [""])
                        placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
        except (PermissionError, OSError):
            pass

    def create_file_table(self) -> QWidget:
        """创建文件列表表格"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        # 选择文件夹按钮
        self.load_folder_btn = QPushButton(_("main_window.buttons.select_folder"))
        self.load_folder_btn.setToolTip(_("main_window.buttons.select_folder_tooltip"))
        self.load_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5ba0e9;
            }
            QPushButton:pressed {
                background-color: #3a7bc8;
            }
        """)
        self.load_folder_btn.clicked.connect(self.select_folder_dialog)
        toolbar.addWidget(self.load_folder_btn)
        
        self.path_label = QLabel(_("main_window.file_table.path_prefix") + _("main_window.file_table.not_selected"))
        self.path_label.setStyleSheet("padding: 0 10px;")
        toolbar.addWidget(self.path_label)
        toolbar.addStretch()
        
        # 确认选择按钮 - 将点击的文件确认为选中状态
        self.confirm_select_btn = QPushButton(_("main_window.buttons.confirm_select"))
        self.confirm_select_btn.setToolTip(_("main_window.buttons.confirm_select_tooltip"))
        self.confirm_select_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.confirm_select_btn.clicked.connect(self.confirm_selection)
        toolbar.addWidget(self.confirm_select_btn)
        
        # 取消选择按钮
        self.cancel_select_btn = QPushButton(_("main_window.buttons.deselect"))
        self.cancel_select_btn.setToolTip(_("main_window.buttons.deselect_tooltip"))
        self.cancel_select_btn.clicked.connect(self.clear_selection)
        toolbar.addWidget(self.cancel_select_btn)
        
        self.select_all_btn = QPushButton(_("main_window.buttons.select_all"))
        self.select_all_btn.clicked.connect(self.select_all_files)
        toolbar.addWidget(self.select_all_btn)
        
        self.clear_list_btn = QPushButton(_("main_window.buttons.clear_list"))
        self.clear_list_btn.clicked.connect(self.clear_file_list)
        toolbar.addWidget(self.clear_list_btn)
        
        layout.addLayout(toolbar)
        
        # 临时点击列表 - 存储连续点击的行索引
        self.temp_clicked_rows = set()
        # 已确认选择的行索引
        self.multi_selected_rows = set()
        
        # 文件表格
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(8)
        self.file_table.setHorizontalHeaderLabels([
            _("main_window.file_table.orig_name"),
            _("main_window.file_table.new_name"),
            _("main_window.file_table.size"),
            _("main_window.file_table.type"),
            _("main_window.file_table.create_date"),
            _("main_window.file_table.modify_date"),
            _("main_window.file_table.length"),
            _("main_window.file_table.status")
        ])
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(False)  # 关闭交替行颜色，统一白色背景
        # 所有列都使用 Interactive 模式，允许用户自由调节宽度
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # 设置各列的默认宽度（总宽度约850，适合非最大化窗口）
        self.file_table.setColumnWidth(0, 180)  # 原文件名
        self.file_table.setColumnWidth(1, 180)  # 新文件名
        self.file_table.setColumnWidth(2, 65)   # 大小
        self.file_table.setColumnWidth(3, 100)  # 类型
        self.file_table.setColumnWidth(4, 120)  # 创建日期
        self.file_table.setColumnWidth(5, 120)  # 修改日期
        self.file_table.setColumnWidth(6, 40)   # 长度
        self.file_table.setColumnWidth(7, 50)   # 状态
        # 最后一列自动拉伸填充剩余空间
        self.file_table.horizontalHeader().setStretchLastSection(True)
        
        # 启用表头点击排序
        self.file_table.setSortingEnabled(False)  # 禁用自动排序，使用自定义排序
        self.file_table.horizontalHeader().setSectionsClickable(True)
        self.file_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        # 修复滚动方向问题：设置正确的滚动模式
        self.file_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.file_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # 点击文件名时选中并激活重命名
        self.file_table.cellClicked.connect(self.on_file_cell_clicked)
        self.file_table.cellDoubleClicked.connect(self.on_file_cell_double_clicked)
        
        # 排序状态
        self.sort_column = -1  # 当前排序列
        self.sort_ascending = True  # 排序方向
        
        # 当前选中的文件索引
        self.selected_file_index = -1
        
        layout.addWidget(self.file_table)
        return widget
    
    def select_folder_dialog(self):
        """打开文件夹选择对话框"""
        path = QFileDialog.getExistingDirectory(
            self, 
            _("main_window.dialogs.select_folder_title"),
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.load_folder(path)
    
    def on_file_cell_clicked(self, row: int, column: int):
        """文件单元格点击事件 - 连续点击添加到临时列表"""
        self.selected_file_index = row
        
        # 如果该行已在临时列表中，则移除；否则添加
        if row in self.temp_clicked_rows:
            self.temp_clicked_rows.discard(row)
        else:
            self.temp_clicked_rows.add(row)
        
        # 更新临时点击的高亮显示
        self.highlight_temp_clicked()
        
        # 获取文件信息并显示状态
        item = self.file_table.item(row, 0)
        if item:
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath:
                filename = os.path.basename(filepath)
                temp_count = len(self.temp_clicked_rows)
                selected_count = len(self.multi_selected_rows)
                
                if temp_count > 0:
                    self.statusBar().showMessage(
                        _("main_window.file_table.click_info").format(temp=temp_count, selected=selected_count)
                    )
                else:
                    self.statusBar().showMessage(_("main_window.file_table.selected_info").format(count=selected_count))
    
    def confirm_selection(self):
        """确认选择 - 将临时点击的文件添加到已选择列表"""
        if not self.temp_clicked_rows:
            self.statusBar().showMessage(_("main_window.file_table.please_click_first"))
            return
        
        # 将临时点击的行添加到已选择列表
        added_count = len(self.temp_clicked_rows)
        self.multi_selected_rows.update(self.temp_clicked_rows)
        self.temp_clicked_rows.clear()
        
        # 清除表格的原生选中状态（这会导致蓝色高亮覆盖我们的背景色）
        self.file_table.clearSelection()
        
        # 立即更新所有选中行的背景色为浅绿色
        from PyQt6.QtGui import QColor, QBrush
        selected_color = QColor(180, 220, 180)  # 浅绿色
        white_color = QColor(255, 255, 255)  # 白色
        
        for r in range(self.file_table.rowCount()):
            if r in self.multi_selected_rows:
                brush = QBrush(selected_color)
            else:
                brush = QBrush(white_color)
            
            for c in range(self.file_table.columnCount()):
                item = self.file_table.item(r, c)
                if item:
                    item.setBackground(brush)
        
        # 强制刷新表格显示
        self.file_table.viewport().update()
        self.file_table.repaint()
        
        # 更新预览
        self.update_preview()
        
        self.statusBar().showMessage(_("main_window.file_table.confirm_selected_info").format(added=added_count, total=len(self.multi_selected_rows)))
    
    def clear_selection(self):
        """清除所有选择"""
        self.multi_selected_rows.clear()
        self.temp_clicked_rows.clear()
        self.highlight_all_selections()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.file_table.cancel_selected"))
    
    def highlight_temp_clicked(self):
        """高亮显示临时点击的文件（浅蓝色）和已确认选择的文件（深色）"""
        from PyQt6.QtGui import QColor
        
        for r in range(self.file_table.rowCount()):
            if r in self.multi_selected_rows:
                # 已确认选择的文件 - 深绿色背景
                color = QColor(200, 230, 200)  # 浅绿色
            elif r in self.temp_clicked_rows:
                # 临时点击的文件 - 浅蓝色背景
                color = QColor(200, 220, 255)  # 浅蓝色
            else:
                # 未选择的文件 - 白色背景
                color = QColor(255, 255, 255)
            
            for c in range(self.file_table.columnCount()):
                item = self.file_table.item(r, c)
                if item:
                    item.setBackground(color)
    
    def highlight_all_selections(self):
        """高亮显示所有已确认选择的文件"""
        from PyQt6.QtGui import QColor
        
        for r in range(self.file_table.rowCount()):
            if r in self.multi_selected_rows:
                # 已确认选择的文件 - 深绿色背景
                color = QColor(180, 220, 180)  # 浅绿色
            else:
                # 未选择的文件 - 白色背景
                color = QColor(255, 255, 255)
            
            for c in range(self.file_table.columnCount()):
                item = self.file_table.item(r, c)
                if item:
                    item.setBackground(color)
    
    def on_file_cell_double_clicked(self, row: int, column: int):
        """文件单元格双击事件 - 打开文件所在位置"""
        item = self.file_table.item(row, 0)
        if item:
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath and os.path.exists(filepath):
                # 在资源管理器中打开并选中文件
                import subprocess
                subprocess.run(['explorer', '/select,', filepath])
    
    def create_rules_panel(self) -> QWidget:
        """创建重命名规则面板 - 仿 Bulk Rename Utility 布局，支持拖动调整模块宽度"""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # 第一行: 正则(1), 替换(3), 移除(5), 添加(7), 自动日期(8), 编号(10)
        # 使用 QSplitter 实现可调节宽度
        row1_splitter = QSplitter(Qt.Orientation.Horizontal)
        row1_splitter.setChildrenCollapsible(False)  # 防止模块被完全折叠
        row1_splitter.addWidget(self.create_regex_group())
        row1_splitter.addWidget(self.create_replace_group())
        row1_splitter.addWidget(self.create_remove_group())
        row1_splitter.addWidget(self.create_add_group())
        row1_splitter.addWidget(self.create_auto_date_group())
        row1_splitter.addWidget(self.create_numbering_group())
        # 设置初始比例 (1:1:2:1:1:1)
        row1_splitter.setSizes([150, 150, 300, 150, 180, 180])
        main_layout.addWidget(row1_splitter)
        
        # 第二行: 文件(2), 大小写(4), 移动/复制(6), 附加文件夹名(9), 扩展名(11)
        row2_splitter = QSplitter(Qt.Orientation.Horizontal)
        row2_splitter.setChildrenCollapsible(False)
        row2_splitter.addWidget(self.create_name_group())
        row2_splitter.addWidget(self.create_case_group())
        row2_splitter.addWidget(self.create_move_copy_group())
        row2_splitter.addWidget(self.create_folder_name_group())
        row2_splitter.addWidget(self.create_extension_group())
        # 设置初始比例 (1:1:1:1:1)
        row2_splitter.setSizes([200, 200, 250, 200, 200])
        main_layout.addWidget(row2_splitter)
        
        # 第三行: 选择(12), 新位置(13), 操作按钮
        row3_splitter = QSplitter(Qt.Orientation.Horizontal)
        row3_splitter.setChildrenCollapsible(False)
        row3_splitter.addWidget(self.create_filter_group())
        row3_splitter.addWidget(self.create_new_location_group())
        row3_splitter.addWidget(self.create_action_group())
        # 设置初始比例 (2:1:1)
        row3_splitter.setSizes([500, 250, 200])
        main_layout.addWidget(row3_splitter)
        
        return widget
    
    def create_regex_group(self) -> QGroupBox:
        """正则表达式组"""
        group = ResetableGroupBox("regex")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(1)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.regex_match_label = QLabel(_("main_window.rules.regex.match"))
        layout.addWidget(self.regex_match_label, 0, 0)
        self.regex_pattern = QLineEdit()
        layout.addWidget(self.regex_pattern, 0, 1)
        
        self.regex_replace_label = QLabel(_("main_window.rules.regex.replace"))
        layout.addWidget(self.regex_replace_label, 1, 0)
        self.regex_replace = QLineEdit()
        layout.addWidget(self.regex_replace, 1, 1)
        
        self.regex_include_ext = QCheckBox(_("main_window.rules.regex.include_ext"))
        layout.addWidget(self.regex_include_ext, 2, 0, 1, 2)
        
        group.set_reset_callback(self.reset_regex_group)
        self.regex_check = group
        return group
    
    def create_replace_group(self) -> QGroupBox:
        """替换组"""
        group = ResetableGroupBox("replace")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(1)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.replace_find_label = QLabel(_("main_window.rules.replace.find"))
        layout.addWidget(self.replace_find_label, 0, 0)
        self.replace_find = QLineEdit()
        layout.addWidget(self.replace_find, 0, 1)
        
        self.replace_with_label = QLabel(_("main_window.rules.replace.with"))
        layout.addWidget(self.replace_with_label, 1, 0)
        self.replace_with = QLineEdit()
        layout.addWidget(self.replace_with, 1, 1)
        
        self.replace_case_sensitive = QCheckBox(_("main_window.rules.replace.case_sensitive"))
        layout.addWidget(self.replace_case_sensitive, 2, 0, 1, 2)
        
        group.set_reset_callback(self.reset_replace_group)
        self.replace_check = group
        return group

    def create_remove_group(self) -> QGroupBox:
        """移除组"""
        group = ResetableGroupBox("remove")
        group.setCheckable(True)
        group.setChecked(False)
        main_layout = QGridLayout(group)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(5, 12, 5, 5)
        
        # 第一行: 最初 最后
        self.remove_first_label = QLabel(_("main_window.rules.remove.first"))
        main_layout.addWidget(self.remove_first_label, 0, 0)
        self.remove_first_n = QSpinBox()
        self.remove_first_n.setRange(0, 999)
        self.remove_first_n.setFixedWidth(50)
        main_layout.addWidget(self.remove_first_n, 0, 1)
        
        self.remove_last_label = QLabel(_("main_window.rules.remove.last"))
        main_layout.addWidget(self.remove_last_label, 0, 2)
        self.remove_last_n = QSpinBox()
        self.remove_last_n.setRange(0, 999)
        self.remove_last_n.setFixedWidth(50)
        main_layout.addWidget(self.remove_last_n, 0, 3)
        
        # 第二行: 从 到
        self.remove_from_label = QLabel(_("main_window.rules.remove.from"))
        main_layout.addWidget(self.remove_from_label, 1, 0)
        self.remove_from = QSpinBox()
        self.remove_from.setRange(0, 999)
        self.remove_from.setFixedWidth(50)
        main_layout.addWidget(self.remove_from, 1, 1)
        
        self.remove_to_label = QLabel(_("main_window.rules.remove.to"))
        main_layout.addWidget(self.remove_to_label, 1, 2)
        self.remove_to = QSpinBox()
        self.remove_to.setRange(0, 999)
        self.remove_to.setFixedWidth(50)
        main_layout.addWidget(self.remove_to, 1, 3)
        
        # 第三行: 字符 单词
        self.remove_chars_label = QLabel(_("main_window.rules.remove.chars"))
        main_layout.addWidget(self.remove_chars_label, 2, 0)
        self.remove_chars = QLineEdit()
        self.remove_chars.setFixedWidth(50)
        main_layout.addWidget(self.remove_chars, 2, 1)
        
        self.remove_words_label = QLabel(_("main_window.rules.remove.words"))
        main_layout.addWidget(self.remove_words_label, 2, 2)
        self.remove_words = QLineEdit()
        main_layout.addWidget(self.remove_words, 2, 3)
        
        # 第四行: 裁切
        self.remove_crop_label = QLabel(_("main_window.rules.remove.crop"))
        main_layout.addWidget(self.remove_crop_label, 3, 0)
        self.remove_crop_mode = QComboBox()
        self.remove_crop_mode.addItems(_("main_window.rules.remove.crop_modes"))
        self.remove_crop_mode.setFixedWidth(65)
        main_layout.addWidget(self.remove_crop_mode, 3, 1)
        
        self.remove_crop_text = QLineEdit()
        self.remove_crop_text.setPlaceholderText(_("main_window.rules.remove.crop_placeholder"))
        main_layout.addWidget(self.remove_crop_text, 3, 2, 1, 2)
        
        # 复选框部分 - 使用流式布局或新的网格行
        checkbox_layout = QGridLayout()
        checkbox_layout.setSpacing(4)
        
        self.remove_digits = QCheckBox(_("main_window.rules.remove.digits"))
        checkbox_layout.addWidget(self.remove_digits, 0, 0)
        self.remove_chinese = QCheckBox(_("main_window.rules.remove.chinese"))
        checkbox_layout.addWidget(self.remove_chinese, 0, 1)
        self.remove_trim = QCheckBox(_("main_window.rules.remove.trim"))
        self.remove_trim.setToolTip(_("main_window.rules.remove.trim_tooltip"))
        checkbox_layout.addWidget(self.remove_trim, 0, 2)
        
        self.remove_chars_check = QCheckBox(_("main_window.rules.remove.chars_check"))
        self.remove_chars_check.setToolTip(_("main_window.rules.remove.chars_check_tooltip"))
        checkbox_layout.addWidget(self.remove_chars_check, 1, 0)
        self.remove_ds = QCheckBox(_("main_window.rules.remove.ds"))
        self.remove_ds.setToolTip(_("main_window.rules.remove.ds_tooltip"))
        checkbox_layout.addWidget(self.remove_ds, 1, 1)
        self.remove_accents = QCheckBox(_("main_window.rules.remove.accents"))
        checkbox_layout.addWidget(self.remove_accents, 1, 2)
        
        self.remove_symbols = QCheckBox(_("main_window.rules.remove.symbols"))
        checkbox_layout.addWidget(self.remove_symbols, 2, 0)
        self.remove_lead_dots_label = QLabel(_("main_window.rules.remove.lead_dots"))
        checkbox_layout.addWidget(self.remove_lead_dots_label, 2, 1)
        self.remove_lead_dots = QComboBox()
        self.remove_lead_dots.addItems(_("main_window.rules.remove.lead_dots_modes"))
        self.remove_lead_dots.setFixedWidth(60)
        checkbox_layout.addWidget(self.remove_lead_dots, 2, 2)
        
        main_layout.addLayout(checkbox_layout, 4, 0, 1, 4)
        
        group.set_reset_callback(self.reset_remove_group)
        self.remove_check = group
        return group
        
        group.set_reset_callback(self.reset_remove_group)
        self.remove_check = group
        return group
    
    def create_add_group(self) -> QGroupBox:
        """添加组"""
        group = ResetableGroupBox("add")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(1)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.add_prefix_label = QLabel(_("main_window.rules.add.prefix"))
        layout.addWidget(self.add_prefix_label, 0, 0)
        self.add_prefix = QLineEdit()
        layout.addWidget(self.add_prefix, 0, 1)
        
        self.add_insert_label = QLabel(_("main_window.rules.add.insert"))
        layout.addWidget(self.add_insert_label, 1, 0)
        self.add_insert = QLineEdit()
        layout.addWidget(self.add_insert, 1, 1)
        
        self.add_insert_pos_label = QLabel(_("main_window.rules.add.pos"))
        layout.addWidget(self.add_insert_pos_label, 2, 0)
        self.add_insert_pos = QSpinBox()
        self.add_insert_pos.setRange(0, 999)
        self.add_insert_pos.setFixedWidth(50)
        layout.addWidget(self.add_insert_pos, 2, 1)
        
        self.add_suffix_label = QLabel(_("main_window.rules.add.suffix"))
        layout.addWidget(self.add_suffix_label, 3, 0)
        self.add_suffix = QLineEdit()
        layout.addWidget(self.add_suffix, 3, 1)
        
        self.add_word_space = QCheckBox(_("main_window.rules.add.word_space"))
        layout.addWidget(self.add_word_space, 4, 0, 1, 2)
        
        group.set_reset_callback(self.reset_add_group)
        self.add_check = group
        return group
    
    def create_auto_date_group(self) -> QGroupBox:
        """自动日期组"""
        group = ResetableGroupBox("auto_date")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 12, 5, 5)
        
        # 第一行: 方式 类型
        self.auto_date_mode_label = QLabel(_("main_window.rules.auto_date.mode"))
        layout.addWidget(self.auto_date_mode_label, 0, 0)
        self.auto_date_type = QComboBox()
        self.auto_date_type.addItems(_("main_window.rules.auto_date.modes"))
        self.auto_date_type.setMinimumWidth(60)
        layout.addWidget(self.auto_date_type, 0, 1)
        
        self.auto_date_type_label = QLabel(_("main_window.rules.auto_date.type"))
        layout.addWidget(self.auto_date_type_label, 0, 2)
        self.auto_date_mode = QComboBox()
        self.auto_date_mode.addItems(_("main_window.rules.auto_date.types"))
        self.auto_date_mode.setMinimumWidth(80)
        layout.addWidget(self.auto_date_mode, 0, 3)
        
        # 第二行: 格式 分隔
        self.auto_date_format_label = QLabel(_("main_window.rules.auto_date.format"))
        layout.addWidget(self.auto_date_format_label, 1, 0)
        self.auto_date_format = QComboBox()
        self.auto_date_format.setEditable(True)
        self.auto_date_format.addItems(_("main_window.rules.auto_date.formats"))
        self.auto_date_format.setMinimumWidth(60)
        layout.addWidget(self.auto_date_format, 1, 1)
        
        self.auto_date_sep_label = QLabel(_("main_window.rules.auto_date.sep"))
        layout.addWidget(self.auto_date_sep_label, 1, 2)
        self.auto_date_sep = QLineEdit()
        self.auto_date_sep.setFixedWidth(50)
        layout.addWidget(self.auto_date_sep, 1, 3)
        
        # 第三行: 连接 定制
        self.auto_date_connect_label = QLabel(_("main_window.rules.auto_date.connect"))
        layout.addWidget(self.auto_date_connect_label, 2, 0)
        self.auto_date_connect = QLineEdit()
        self.auto_date_connect.setText("_")
        self.auto_date_connect.setFixedWidth(60)
        layout.addWidget(self.auto_date_connect, 2, 1)
        
        self.auto_date_custom_label = QLabel(_("main_window.rules.auto_date.custom"))
        layout.addWidget(self.auto_date_custom_label, 2, 2)
        self.auto_date_custom = QLineEdit()
        self.auto_date_custom.setPlaceholderText(_("main_window.rules.auto_date.custom_placeholder"))
        layout.addWidget(self.auto_date_custom, 2, 3)
        
        # 第四行: 中心 距离
        self.auto_date_center = QCheckBox(_("main_window.rules.auto_date.center"))
        layout.addWidget(self.auto_date_center, 3, 0)
        
        self.auto_date_distance_label = QLabel(_("main_window.rules.auto_date.distance"))
        layout.addWidget(self.auto_date_distance_label, 3, 1)
        self.auto_date_distance = QSpinBox()
        self.auto_date_distance.setRange(0, 999)
        self.auto_date_distance.setFixedWidth(60)
        layout.addWidget(self.auto_date_distance, 3, 2, 1, 2)
        
        group.set_reset_callback(self.reset_auto_date_group)
        self.auto_date_check = group
        return group
    
    def create_numbering_group(self) -> QGroupBox:
        """编号组"""
        group = ResetableGroupBox("numbering")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 12, 5, 5)
        
        # 第一行: 方式 在
        self.numbering_mode_label = QLabel(_("main_window.rules.numbering.mode"))
        layout.addWidget(self.numbering_mode_label, 0, 0)
        self.numbering_mode = QComboBox()
        self.numbering_mode.addItems(_("main_window.rules.numbering.modes"))
        self.numbering_mode.setMinimumWidth(60)
        layout.addWidget(self.numbering_mode, 0, 1)
        
        self.numbering_at_label = QLabel(_("main_window.rules.numbering.at"))
        layout.addWidget(self.numbering_at_label, 0, 2)
        self.numbering_at = QSpinBox()
        self.numbering_at.setRange(0, 999)
        self.numbering_at.setFixedWidth(50)
        layout.addWidget(self.numbering_at, 0, 3)
        
        # 第二行: 开始 递增
        self.numbering_start_label = QLabel(_("main_window.rules.numbering.start"))
        layout.addWidget(self.numbering_start_label, 1, 0)
        self.numbering_start = QSpinBox()
        self.numbering_start.setRange(0, 99999)
        self.numbering_start.setValue(1)
        self.numbering_start.setFixedWidth(60)
        layout.addWidget(self.numbering_start, 1, 1)
        
        self.numbering_increment_label = QLabel(_("main_window.rules.numbering.increment"))
        layout.addWidget(self.numbering_increment_label, 1, 2)
        self.numbering_increment = QSpinBox()
        self.numbering_increment.setRange(1, 999)
        self.numbering_increment.setValue(1)
        self.numbering_increment.setFixedWidth(50)
        layout.addWidget(self.numbering_increment, 1, 3)
        
        # 第三行: 对齐 分隔
        self.numbering_padding_label = QLabel(_("main_window.rules.numbering.padding"))
        layout.addWidget(self.numbering_padding_label, 2, 0)
        self.numbering_padding = QSpinBox()
        self.numbering_padding.setRange(0, 10)
        self.numbering_padding.setFixedWidth(60)
        layout.addWidget(self.numbering_padding, 2, 1)
        
        self.numbering_sep_label = QLabel(_("main_window.rules.numbering.sep"))
        layout.addWidget(self.numbering_sep_label, 2, 2)
        self.numbering_separator = QLineEdit()
        self.numbering_separator.setFixedWidth(50)
        layout.addWidget(self.numbering_separator, 2, 3)
        
        # 第四行: 打断 文件夹
        self.numbering_break_label = QLabel(_("main_window.rules.numbering.break"))
        layout.addWidget(self.numbering_break_label, 3, 0)
        self.numbering_break = QSpinBox()
        self.numbering_break.setRange(0, 999)
        self.numbering_break.setFixedWidth(60)
        layout.addWidget(self.numbering_break, 3, 1)
        
        self.numbering_folder = QCheckBox(_("main_window.rules.numbering.folder"))
        layout.addWidget(self.numbering_folder, 3, 2, 1, 2)
        
        # 第五行: 类型
        self.numbering_type_label = QLabel(_("main_window.rules.numbering.type"))
        layout.addWidget(self.numbering_type_label, 4, 0)
        self.numbering_type = QComboBox()
        self.numbering_type.addItems(_("main_window.rules.numbering.types"))
        self.numbering_type.setCurrentIndex(8)  # 默认选择 Base 10
        layout.addWidget(self.numbering_type, 4, 1, 1, 3)
        
        # 第六行: 罗马数
        self.numbering_roman_label = QLabel(_("main_window.rules.numbering.roman"))
        layout.addWidget(self.numbering_roman_label, 5, 0)
        self.numbering_roman = QComboBox()
        self.numbering_roman.addItems(_("main_window.rules.numbering.roman_modes"))
        layout.addWidget(self.numbering_roman, 5, 1, 1, 3)
        
        group.set_reset_callback(self.reset_numbering_group)
        self.numbering_check = group
        return group

    def create_name_group(self) -> QGroupBox:
        """文件名组"""
        group = ResetableGroupBox("name")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.name_mode_label = QLabel(_("main_window.rules.name.name"))
        layout.addWidget(self.name_mode_label, 0, 0)
        self.name_mode = QComboBox()
        self.name_mode.addItems(_("main_window.rules.name.modes"))
        layout.addWidget(self.name_mode, 0, 1)
        
        self.name_fixed_label = QLabel(_("main_window.rules.name.fixed"))
        layout.addWidget(self.name_fixed_label, 1, 0)
        self.name_fixed = QLineEdit()
        layout.addWidget(self.name_fixed, 1, 1)
        
        group.set_reset_callback(self.reset_name_group)
        self.name_check = group
        return group
    
    def create_case_group(self) -> QGroupBox:
        """大小写组"""
        group = ResetableGroupBox("case")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.case_mode_label = QLabel(_("main_window.rules.case.mode"))
        layout.addWidget(self.case_mode_label, 0, 0)
        self.case_mode = QComboBox()
        self.case_mode.addItems(_("main_window.rules.case.modes"))
        layout.addWidget(self.case_mode, 0, 1)
        
        self.case_digits = QCheckBox(_("main_window.rules.remove.digits"))
        layout.addWidget(self.case_digits, 1, 0)
        self.case_symbols = QCheckBox(_("main_window.rules.remove.symbols"))
        layout.addWidget(self.case_symbols, 1, 1)
        
        self.case_exception_label = QLabel(_("main_window.rules.case.exception"))
        layout.addWidget(self.case_exception_label, 2, 0)
        self.case_exception = QLineEdit()
        self.case_exception.setPlaceholderText(_("main_window.rules.case.exception"))
        layout.addWidget(self.case_exception, 2, 1)
        
        group.set_reset_callback(self.reset_case_group)
        self.case_check = group
        return group
    
    def create_move_copy_group(self) -> QGroupBox:
        """移动/复制组 - 参照原版布局"""
        group = ResetableGroupBox("move_copy")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QHBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        # 第一个下拉框：操作类型（无、复制开始、复制最后、移动开始、移动最后）
        self.move_copy_mode = QComboBox()
        self.move_copy_mode.addItems(_("main_window.rules.move_copy.modes"))
        self.move_copy_mode.setToolTip(_("main_window.rules.move_copy.mode"))
        self.move_copy_mode.setFixedWidth(80)
        layout.addWidget(self.move_copy_mode)
        
        # 第一个数字框：从位置/字符数
        self.move_from = QSpinBox()
        self.move_from.setRange(0, 999)
        self.move_from.setFixedWidth(45)
        self.move_from.setToolTip(_("main_window.rules.move_copy.from"))
        layout.addWidget(self.move_from)
        
        # 第二个下拉框：目标位置
        self.move_target = QComboBox()
        self.move_target.addItems(_("main_window.rules.move_copy.targets"))
        self.move_target.setToolTip(_("main_window.rules.move_copy.target"))
        self.move_target.setFixedWidth(60)
        layout.addWidget(self.move_target)
        
        # 第二个数字框：字符数/目标位置
        self.move_count = QSpinBox()
        self.move_count.setRange(0, 999)
        self.move_count.setFixedWidth(45)
        self.move_count.setToolTip(_("main_window.rules.move_copy.count"))
        layout.addWidget(self.move_count)
        
        # 分隔符
        self.move_sep_label = QLabel(_("main_window.rules.move_copy.sep"))
        layout.addWidget(self.move_sep_label)
        self.move_separator = QLineEdit()
        self.move_separator.setFixedWidth(40)
        self.move_separator.setToolTip(_("main_window.rules.move_copy.sep"))
        layout.addWidget(self.move_separator)
        
        layout.addStretch()
        
        group.set_reset_callback(self.reset_move_copy_group)
        self.move_check = group
        return group
    
    def _on_move_target_changed(self, index: int):
        """目标位置变化时的处理"""
        # 索引: 0=无, 1=到开头, 2=到结尾, 3=到位置
        # 当选择"到位置"时，第二个数字框用于指定目标位置
        self.on_rule_changed()
    
    def create_folder_name_group(self) -> QGroupBox:
        """附加文件夹名组"""
        group = ResetableGroupBox("folder_name")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.folder_name_mode_label = QLabel(_("main_window.rules.folder_name.mode"))
        layout.addWidget(self.folder_name_mode_label, 0, 0)
        self.folder_name_mode = QComboBox()
        self.folder_name_mode.addItems(_("main_window.rules.folder_name.modes"))
        layout.addWidget(self.folder_name_mode, 0, 1)
        
        self.folder_name_sep_label = QLabel(_("main_window.rules.folder_name.sep"))
        layout.addWidget(self.folder_name_sep_label, 1, 0)
        self.folder_name_sep = QLineEdit()
        self.folder_name_sep.setText("_")
        layout.addWidget(self.folder_name_sep, 1, 1)
        
        self.folder_name_levels_label = QLabel(_("main_window.rules.folder_name.levels"))
        layout.addWidget(self.folder_name_levels_label, 2, 0)
        self.folder_name_levels = QSpinBox()
        self.folder_name_levels.setRange(1, 10)
        self.folder_name_levels.setValue(1)
        layout.addWidget(self.folder_name_levels, 2, 1)
        
        group.set_reset_callback(self.reset_folder_name_group)
        self.folder_name_check = group
        return group
    
    def create_extension_group(self) -> QGroupBox:
        """扩展名组"""
        group = ResetableGroupBox("extension")
        group.setCheckable(True)
        group.setChecked(False)
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.ext_mode_label = QLabel(_("main_window.rules.extension.mode"))
        layout.addWidget(self.ext_mode_label, 0, 0)
        self.ext_mode = QComboBox()
        self.ext_mode.addItems(_("main_window.rules.extension.modes"))
        layout.addWidget(self.ext_mode, 0, 1)
        
        self.ext_fixed_label = QLabel(_("main_window.rules.extension.fixed"))
        layout.addWidget(self.ext_fixed_label, 1, 0)
        self.ext_fixed = QLineEdit()
        self.ext_fixed.setPlaceholderText(_("main_window.rules.extension.fixed"))
        layout.addWidget(self.ext_fixed, 1, 1)
        
        group.set_reset_callback(self.reset_extension_group)
        self.ext_check = group
        return group
    
    def create_action_group(self) -> QGroupBox:
        """操作按钮组"""
        group = QGroupBox(_("main_window.menu.action"))
        self.action_group = group
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        self.restore_btn = QPushButton(_("main_window.menu.restore"))
        self.restore_btn.setToolTip(_("main_window.menu.restore"))
        self.restore_btn.clicked.connect(self.restore_last_input)
        layout.addWidget(self.restore_btn)
        
        self.rename_btn = QPushButton(_("main_window.menu.rename"))
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.rename_btn.clicked.connect(self.execute_rename)
        layout.addWidget(self.rename_btn)
        
        self.reset_all_btn = QPushButton(_("main_window.menu.reset_all"))
        self.reset_all_btn.clicked.connect(self.clear_rules)
        layout.addWidget(self.reset_all_btn)
        
        layout.addStretch()
        
        return group

    def create_filter_group(self) -> QGroupBox:
        """选择过滤组 - 均匀分布布局，始终生效无需勾选"""
        group = ResetableGroupBox("selection")
        group.setCheckable(False)  # 取消勾选框，始终生效
        main_layout = QVBoxLayout(group)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(3, 12, 3, 2)
        
        # 第一行: 过滤 + 复选框 + 名称长度 - 使用弹性间距均匀分布
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        self.filter_label = QLabel(_("main_window.rules.selection.filter") + ":")
        row1.addWidget(self.filter_label)
        self.filter_pattern = QLineEdit()
        self.filter_pattern.setPlaceholderText("*")
        self.filter_pattern.setMinimumWidth(60)
        row1.addWidget(self.filter_pattern, 1)  # 拉伸
        row1.addStretch(1)
        self.filter_folders = QCheckBox(_("main_window.rules.selection.folders"))
        self.filter_folders.setChecked(True)  # 默认勾选文件夹
        row1.addWidget(self.filter_folders)
        row1.addStretch(1)
        self.filter_hidden = QCheckBox(_("main_window.rules.selection.hidden"))
        row1.addWidget(self.filter_hidden)
        row1.addStretch(1)
        self.filter_min_name_label = QLabel(_("main_window.rules.selection.min") + _("main_window.rules.selection.name_len"))
        row1.addWidget(self.filter_min_name_label)
        self.filter_min_name_len = QSpinBox()
        self.filter_min_name_len.setRange(0, 999)
        self.filter_min_name_len.setFixedWidth(55)
        row1.addWidget(self.filter_min_name_len)
        row1.addStretch(1)
        self.filter_max_name_label = QLabel(_("main_window.rules.selection.max"))
        row1.addWidget(self.filter_max_name_label)
        self.filter_max_name_len = QSpinBox()
        self.filter_max_name_len.setRange(0, 999)
        self.filter_max_name_len.setFixedWidth(55)
        row1.addWidget(self.filter_max_name_len)
        main_layout.addLayout(row1)
        
        # 第二行: 区分大小写 + 更多复选框 + 路径长度 - 使用弹性间距均匀分布
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        self.filter_case_sensitive = QCheckBox(_("main_window.rules.selection.case"))
        row2.addWidget(self.filter_case_sensitive)
        row2.addStretch(1)
        self.filter_files = QCheckBox(_("main_window.rules.selection.files"))
        self.filter_files.setChecked(True)
        row2.addWidget(self.filter_files)
        row2.addStretch(1)
        self.filter_subfolders = QCheckBox(_("main_window.rules.selection.folders"))
        row2.addWidget(self.filter_subfolders)
        row2.addStretch(1)
        self.filter_min_path_label = QLabel(_("main_window.rules.selection.min") + _("main_window.rules.selection.path_len"))
        row2.addWidget(self.filter_min_path_label)
        self.filter_min_path_len = QSpinBox()
        self.filter_min_path_len.setRange(0, 999)
        self.filter_min_path_len.setFixedWidth(55)
        row2.addWidget(self.filter_min_path_len)
        row2.addStretch(1)
        self.filter_max_path_label = QLabel(_("main_window.rules.selection.max"))
        row2.addWidget(self.filter_max_path_label)
        self.filter_max_path_len = QSpinBox()
        self.filter_max_path_len.setRange(0, 999)
        self.filter_max_path_len.setFixedWidth(55)
        row2.addWidget(self.filter_max_path_len)
        main_layout.addLayout(row2)
        
        group.set_reset_callback(self.reset_filter_group)
        self.filter_check = group
        return group
    
    def create_new_location_group(self) -> QGroupBox:
        """新位置组 - 紧凑布局，始终生效无需勾选"""
        group = ResetableGroupBox("new_location")
        group.setCheckable(False)  # 取消勾选框，始终生效
        layout = QGridLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(3, 12, 3, 2)
        
        # 路径选择
        self.new_location_path_label = QLabel(_("main_window.rules.new_location.path") + ":")
        layout.addWidget(self.new_location_path_label, 0, 0)
        self.new_location_path = QLineEdit()
        self.new_location_path.setPlaceholderText("C:\\Example")
        layout.addWidget(self.new_location_path, 0, 1)
        
        self.new_location_browse_btn = QPushButton("...")
        self.new_location_browse_btn.setFixedWidth(25)
        self.new_location_browse_btn.clicked.connect(self.browse_new_location)
        layout.addWidget(self.new_location_browse_btn, 0, 2)
        
        # 复制不移动选项
        self.new_location_copy = QCheckBox(_("main_window.rules.new_location.copy"))
        layout.addWidget(self.new_location_copy, 1, 0, 1, 3)
        
        group.set_reset_callback(self.reset_new_location_group)
        self.new_location_check = group
        return group
    
    def browse_new_location(self):
        """浏览选择新位置"""
        path = QFileDialog.getExistingDirectory(self, _("main_window.dialogs.select_folder_title"))
        if path:
            self.new_location_path.setText(path)
    
    def reset_filter_group(self):
        """重置选择过滤模块"""
        self.save_current_input_state()
        self.filter_pattern.clear()
        self.filter_case_sensitive.setChecked(False)
        self.filter_folders.setChecked(True)  # 默认勾选文件夹
        self.filter_files.setChecked(True)
        self.filter_hidden.setChecked(False)
        self.filter_subfolders.setChecked(False)
        self.filter_min_name_len.setValue(0)
        self.filter_max_name_len.setValue(0)
        self.filter_min_path_len.setValue(0)
        self.filter_max_path_len.setValue(0)
        self.apply_filter()
        self.statusBar().showMessage(_("main_window.status.filter_reset"))
    
    def reset_new_location_group(self):
        """重置新位置模块"""
        self.save_current_input_state()
        self.new_location_path.clear()
        self.new_location_copy.setChecked(False)
        self.statusBar().showMessage(_("main_window.status.new_location_reset"))
    
    def apply_filter(self):
        """应用过滤条件 - 始终生效，根据设置的条件过滤文件"""
        import fnmatch
        pattern = self.filter_pattern.text().strip()
        case_sensitive = self.filter_case_sensitive.isChecked()
        show_files = self.filter_files.isChecked()
        show_folders = self.filter_folders.isChecked()
        min_name_len = self.filter_min_name_len.value()
        max_name_len = self.filter_max_name_len.value()
        min_path_len = self.filter_min_path_len.value()
        max_path_len = self.filter_max_path_len.value()
        
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if not item:
                continue
            
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if not filepath:
                continue
            
            filename = os.path.basename(filepath)
            is_file = os.path.isfile(filepath)
            is_folder = os.path.isdir(filepath)
            show = True
            
            # 文件/文件夹类型过滤
            if is_file and not show_files:
                show = False
            if is_folder and not show_folders:
                show = False
            
            # 名称模式过滤（支持扩展名筛选，如 *.txt, *.jpg）
            if show and pattern:
                # 处理多个模式（用分号或逗号分隔）
                patterns = [p.strip() for p in pattern.replace(',', ';').split(';') if p.strip()]
                if patterns:
                    match_any = False
                    for p in patterns:
                        if case_sensitive:
                            if fnmatch.fnmatch(filename, p):
                                match_any = True
                                break
                        else:
                            if fnmatch.fnmatch(filename.lower(), p.lower()):
                                match_any = True
                                break
                    if not match_any:
                        show = False
            
            # 名称长度过滤
            if show and min_name_len > 0 and len(filename) < min_name_len:
                show = False
            if show and max_name_len > 0 and len(filename) > max_name_len:
                show = False
            
            # 路径长度过滤
            if show and min_path_len > 0 and len(filepath) < min_path_len:
                show = False
            if show and max_path_len > 0 and len(filepath) > max_path_len:
                show = False
            
            self.file_table.setRowHidden(row, not show)
        
        # 统计可见文件数
        visible_count = sum(1 for row in range(self.file_table.rowCount()) 
                          if not self.file_table.isRowHidden(row))
        self.statusBar().showMessage(_("main_window.status.filtered_info").format(count=visible_count))

    def setup_connections(self):
        """设置信号连接"""
        # 所有规则组的变化时更新预览
        rule_groups = [
            self.regex_check, self.replace_check, self.remove_check,
            self.add_check, self.auto_date_check, self.numbering_check,
            self.name_check, self.case_check, self.move_check,
            self.folder_name_check, self.ext_check
        ]
        
        for group in rule_groups:
            group.toggled.connect(self.on_rule_changed)
        
        # 文本框变化
        text_widgets = [
            self.regex_pattern, self.regex_replace,
            self.replace_find, self.replace_with,
            self.remove_chars, self.remove_words, self.remove_crop_text,
            self.add_prefix, self.add_suffix, self.add_insert,
            self.name_fixed, self.ext_fixed,
            self.folder_name_sep, self.numbering_separator,
            self.auto_date_sep, self.auto_date_connect, self.auto_date_custom,
            self.case_exception, self.move_separator
        ]
        
        for widget in text_widgets:
            widget.textChanged.connect(self.on_rule_changed)
        
        # 数值框变化
        spin_widgets = [
            self.remove_first_n, self.remove_last_n, self.remove_from, self.remove_to,
            self.add_insert_pos,
            self.numbering_start, self.numbering_increment, self.numbering_padding, 
            self.numbering_at, self.numbering_break,
            self.move_from, self.move_count,
            self.folder_name_levels,
            self.auto_date_distance
        ]
        
        for widget in spin_widgets:
            widget.valueChanged.connect(self.on_rule_changed)
        
        # 下拉框变化
        combo_widgets = [
            self.name_mode, self.case_mode, self.ext_mode,
            self.auto_date_type, self.auto_date_mode, self.auto_date_format,
            self.numbering_mode, self.numbering_type, self.numbering_roman,
            self.move_copy_mode, self.move_target, self.folder_name_mode,
            self.remove_crop_mode, self.remove_lead_dots
        ]
        
        for widget in combo_widgets:
            widget.currentIndexChanged.connect(self.on_rule_changed)
        
        # 复选框变化
        check_widgets = [
            self.regex_include_ext, self.replace_case_sensitive,
            self.remove_digits, self.remove_symbols, self.remove_chinese,
            self.remove_trim, self.remove_ds, self.remove_accents, self.remove_chars_check,
            self.add_word_space,
            self.case_digits, self.case_symbols,
            self.numbering_folder,
            self.auto_date_center
        ]
        
        for widget in check_widgets:
            widget.stateChanged.connect(self.on_rule_changed)
        
        # 过滤模块的信号连接（不再需要toggled信号，因为已取消勾选框）
        self.filter_pattern.textChanged.connect(self.apply_filter)
        self.filter_case_sensitive.stateChanged.connect(self.apply_filter)
        self.filter_folders.stateChanged.connect(self.apply_filter)
        self.filter_files.stateChanged.connect(self.apply_filter)
        self.filter_hidden.stateChanged.connect(self.apply_filter)
        self.filter_subfolders.stateChanged.connect(self.on_subfolders_changed)
        self.filter_min_name_len.valueChanged.connect(self.apply_filter)
        self.filter_max_name_len.valueChanged.connect(self.apply_filter)
        self.filter_min_path_len.valueChanged.connect(self.apply_filter)
        self.filter_max_path_len.valueChanged.connect(self.apply_filter)
    
    def on_rule_changed(self):
        """规则变化时更新"""
        self.sync_rules_to_engine(for_preview=True)
        self.update_preview()
    
    def sync_rules_to_engine(self, for_preview=False):
        """同步UI规则到引擎
        
        Args:
            for_preview: 如果为True，则只有勾选的模块才启用（用于预览和执行）
                        如果为False，则只有勾选且有内容的模块才启用（用于执行重命名）
        
        关键修复：只有勾选的模块才会在预览中显示效果，取消勾选时立即恢复原始状态
        """
        rules = self.engine.rules
        
        # 正则 - 必须勾选才启用
        has_regex_content = bool(self.regex_pattern.text())
        rules.regex_enabled = self.regex_check.isChecked() and has_regex_content
        rules.regex_pattern = self.regex_pattern.text()
        rules.regex_replace = self.regex_replace.text()
        
        # 替换 - 必须勾选才启用
        has_replace_content = bool(self.replace_find.text())
        rules.replace_enabled = self.replace_check.isChecked() and has_replace_content
        rules.replace_find = self.replace_find.text()
        rules.replace_with = self.replace_with.text()
        rules.replace_case_sensitive = self.replace_case_sensitive.isChecked()
        
        # 移除 - 必须勾选才启用
        has_remove_content = (self.remove_first_n.value() > 0 or self.remove_last_n.value() > 0 or
                              self.remove_from.value() > 0 or self.remove_to.value() > 0 or
                              bool(self.remove_chars.text()) or bool(self.remove_words.text()) or
                              self.remove_crop_mode.currentIndex() > 0 or
                              self.remove_digits.isChecked() or self.remove_symbols.isChecked() or
                              self.remove_chinese.isChecked() or self.remove_trim.isChecked() or
                              self.remove_ds.isChecked() or self.remove_accents.isChecked() or
                              self.remove_chars_check.isChecked() or self.remove_lead_dots.currentIndex() > 0)
        rules.remove_enabled = self.remove_check.isChecked() and has_remove_content
        rules.remove_first_n = self.remove_first_n.value()
        rules.remove_last_n = self.remove_last_n.value()
        rules.remove_from = self.remove_from.value()
        rules.remove_to = self.remove_to.value()
        rules.remove_chars = self.remove_chars.text()
        rules.remove_words = self.remove_words.text()
        rules.remove_crop_mode = self.remove_crop_mode.currentIndex()
        rules.remove_crop_text = self.remove_crop_text.text()
        rules.remove_digits = self.remove_digits.isChecked()
        rules.remove_chinese = self.remove_chinese.isChecked()
        rules.remove_trim = self.remove_trim.isChecked()
        rules.remove_ds = self.remove_ds.isChecked()
        rules.remove_accents = self.remove_accents.isChecked()
        rules.remove_chars_check = self.remove_chars_check.isChecked()
        rules.remove_symbols = self.remove_symbols.isChecked()
        rules.remove_lead_dots = self.remove_lead_dots.currentIndex()
        
        # 添加 - 必须勾选才启用
        has_add_content = (bool(self.add_prefix.text()) or bool(self.add_suffix.text()) or
                          bool(self.add_insert.text()))
        rules.add_enabled = self.add_check.isChecked() and has_add_content
        rules.add_prefix = self.add_prefix.text()
        rules.add_suffix = self.add_suffix.text()
        rules.add_insert = self.add_insert.text()
        rules.add_insert_pos = self.add_insert_pos.value()
        
        # 自动日期 - 必须勾选才启用
        has_auto_date_content = self.auto_date_type.currentIndex() > 0 or bool(self.auto_date_custom.text())
        rules.auto_date_enabled = self.auto_date_check.isChecked() and has_auto_date_content
        rules.auto_date_mode = self.auto_date_mode.currentIndex()
        rules.auto_date_format = self.auto_date_format.currentText()
        rules.auto_date_pos = self.auto_date_type.currentIndex()
        rules.auto_date_sep = self.auto_date_sep.text()
        rules.auto_date_connect = self.auto_date_connect.text()
        rules.auto_date_custom = self.auto_date_custom.text()
        rules.auto_date_center = self.auto_date_center.isChecked()
        rules.auto_date_distance = self.auto_date_distance.value()
        
        # 编号 - 必须勾选才启用
        has_numbering_content = self.numbering_mode.currentIndex() > 0
        rules.numbering_enabled = self.numbering_check.isChecked() and has_numbering_content
        rules.numbering_mode = self.numbering_mode.currentIndex()
        rules.numbering_start = self.numbering_start.value()
        rules.numbering_increment = self.numbering_increment.value()
        rules.numbering_padding = self.numbering_padding.value()
        rules.numbering_separator = self.numbering_separator.text()
        rules.numbering_insert_pos = self.numbering_at.value()
        rules.numbering_break = self.numbering_break.value()
        rules.numbering_type = self.numbering_type.currentIndex()
        rules.numbering_roman = self.numbering_roman.currentIndex()
        
        # 文件名 - 必须勾选才启用
        has_name_content = self.name_mode.currentIndex() > 0 or bool(self.name_fixed.text())
        rules.name_enabled = self.name_check.isChecked() and has_name_content
        rules.name_mode = self.name_mode.currentIndex()
        rules.name_fixed = self.name_fixed.text()
        
        # 大小写 - 必须勾选才启用
        rules.case_enabled = self.case_check.isChecked()
        # UI下拉框: 0=大写, 1=小写, 2=首字母大写, 3=句首大写, 4=反转
        # CaseMode: NONE=0, LOWER=1, UPPER=2, TITLE=3, SENTENCE=4, INVERT=5
        case_mapping = [CaseMode.UPPER, CaseMode.LOWER, CaseMode.TITLE, CaseMode.SENTENCE, CaseMode.INVERT]
        rules.case_mode = case_mapping[self.case_mode.currentIndex()]
        
        # 移动/复制 - 必须勾选才启用
        has_move_content = self.move_copy_mode.currentIndex() > 0 and self.move_target.currentIndex() > 0
        rules.move_enabled = self.move_check.isChecked() and has_move_content
        # 移动/复制参数
        rules.move_copy_mode = self.move_copy_mode.currentIndex()  # 0=无, 1=复制开始, 2=复制最后, 3=移动开始, 4=移动最后
        rules.move_copy_from = self.move_from.value()  # 从位置/字符数
        rules.move_copy_target = self.move_target.currentIndex()  # 目标位置: 0=无, 1=到开头, 2=到结尾, 3=到位置
        rules.move_copy_count = self.move_count.value()  # 字符数/目标位置
        rules.move_copy_separator = self.move_separator.text()
        
        # 文件夹名 - 必须勾选才启用
        has_folder_name_content = self.folder_name_mode.currentIndex() > 0
        rules.folder_name_enabled = self.folder_name_check.isChecked() and has_folder_name_content
        rules.folder_name_pos = self.folder_name_mode.currentIndex()
        rules.folder_name_separator = self.folder_name_sep.text()
        rules.folder_name_levels = self.folder_name_levels.value()
        
        # 扩展名 - 必须勾选才启用
        has_ext_content = self.ext_mode.currentIndex() > 0 or bool(self.ext_fixed.text())
        rules.ext_enabled = self.ext_check.isChecked() and has_ext_content
        rules.ext_mode = self.ext_mode.currentIndex()
        rules.ext_fixed = self.ext_fixed.text()
    
    def update_preview(self):
        """更新预览 - 只预览选中文件的重命名效果"""
        self.engine.reset_counter()
        
        # 获取选中的行
        selected_rows = self.get_selected_rows()
        
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                filepath = item.data(Qt.ItemDataRole.UserRole)
                if filepath:
                    old_name = os.path.basename(filepath)
                    is_folder = os.path.isdir(filepath)
                    
                    # 只有选中的文件才显示预览效果
                    if selected_rows and row in selected_rows:
                        # 选中的文件：显示新文件名预览
                        new_name = self.engine.preview_rename(filepath, row)
                        # 如果是文件夹，添加📁前缀
                        display_name = "📁 " + new_name if is_folder else new_name
                        new_item = QTableWidgetItem(display_name)
                        self.file_table.setItem(row, 1, new_item)
                        
                        # 如果有变化，用深蓝色显示
                        if old_name != new_name:
                            new_item.setForeground(Qt.GlobalColor.darkBlue)
                            # 加粗显示
                            font = new_item.font()
                            font.setBold(True)
                            new_item.setFont(font)
                    elif not selected_rows:
                        # 没有选中任何文件时，显示所有文件的预览
                        new_name = self.engine.preview_rename(filepath, row)
                        # 如果是文件夹，添加📁前缀
                        display_name = "📁 " + new_name if is_folder else new_name
                        new_item = QTableWidgetItem(display_name)
                        self.file_table.setItem(row, 1, new_item)
                        if old_name != new_name:
                            new_item.setForeground(Qt.GlobalColor.blue)
                    else:
                        # 未选中的文件：显示原文件名，不显示预览效果
                        display_name = "📁 " + old_name if is_folder else old_name
                        new_item = QTableWidgetItem(display_name)
                        self.file_table.setItem(row, 1, new_item)
    
    def load_folder(self, path: str, include_subfolders: bool = None):
        """加载文件夹中的文件和子文件夹 - 优化性能版本
        
        Args:
            path: 文件夹路径
            include_subfolders: 是否包含子文件夹中的文件，None表示使用UI设置
        """
        self.current_folder = path  # 保存当前文件夹路径
        self.path_label.setText(_("main_window.file_table.path_prefix") + path)
        self.file_list.clear()
        self.multi_selected_rows.clear()  # 清除已选择列表
        self.temp_clicked_rows.clear()  # 清除临时点击列表
        
        # 停止之前的文件夹大小计算线程
        self._stop_folder_size_calculation()
        self._pending_folder_sizes.clear()
        
        # 禁用表格更新以提高性能
        self.file_table.setUpdatesEnabled(False)
        self.file_table.setSortingEnabled(False)
        self.file_table.setRowCount(0)
        
        # 确定是否包含子文件夹
        if include_subfolders is None:
            include_subfolders = self.filter_subfolders.isChecked()
        
        file_count = 0
        folder_count = 0
        
        try:
            if include_subfolders:
                # 递归加载所有子文件夹中的文件
                for root, dirs, files in os.walk(path):
                    # 添加文件
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        try:
                            self.add_file_to_table(filepath)
                            file_count += 1
                        except (PermissionError, OSError):
                            continue
                    # 添加文件夹（只添加直接子文件夹，不重复添加）
                    if root == path:
                        for dirname in dirs:
                            dirpath = os.path.join(root, dirname)
                            try:
                                row = self.file_table.rowCount()
                                self.add_folder_to_table(dirpath)
                                self._pending_folder_sizes.append((row, dirpath))
                                folder_count += 1
                            except (PermissionError, OSError):
                                continue
            else:
                # 只加载当前目录
                with os.scandir(path) as entries:
                    for entry in entries:
                        try:
                            if entry.is_file(follow_symlinks=False):
                                self.add_file_to_table_fast(entry)
                                file_count += 1
                            elif entry.is_dir(follow_symlinks=False):
                                row = self.file_table.rowCount()
                                self.add_folder_to_table_fast(entry)
                                # 记录需要计算大小的文件夹
                                self._pending_folder_sizes.append((row, entry.path))
                                folder_count += 1
                        except (PermissionError, OSError):
                            continue
        except PermissionError:
            QMessageBox.warning(self, _("main_window.dialogs.error_permission"), _("main_window.dialogs.error_access_fail").format(path=path))
        finally:
            # 重新启用表格更新
            self.file_table.setUpdatesEnabled(True)
        
        subfolder_text = _("main_window.status.subfolder_included") if include_subfolders else ""
        self.statusBar().showMessage(_("main_window.status.loaded_info").format(file_count=file_count, folder_count=folder_count, subfolder=subfolder_text))
        self.update_preview()
        
        # 应用过滤条件（根据选择模块的设置过滤显示）
        self.apply_filter()
        
        # 启动后台线程计算文件夹大小
        if self._pending_folder_sizes:
            self._start_folder_size_calculation()
    
    def on_subfolders_changed(self):
        """子文件夹选项变化时重新加载"""
        if hasattr(self, 'current_folder') and self.current_folder:
            self.load_folder(self.current_folder)

    def add_file_to_table_fast(self, entry):
        """添加文件到表格 - 使用 DirEntry 优化性能"""
        import datetime
        
        filename = entry.name
        filepath = entry.path
        self.file_list.append(filepath)
        
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # 原文件名
        item = QTableWidgetItem(filename)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        self.file_table.setItem(row, 0, item)
        
        # 新文件名（预览）
        self.file_table.setItem(row, 1, QTableWidgetItem(filename))
        
        # 文件大小 - 使用 entry.stat() 缓存，超过100MB不显示
        try:
            stat_info = entry.stat(follow_symlinks=False)
            if stat_info.st_size <= 100 * 1024 * 1024:  # 100MB限制
                size_str = self.format_size(stat_info.st_size)
            else:
                size_str = ""
        except (OSError, PermissionError):
            size_str = ""
        self.file_table.setItem(row, 2, QTableWidgetItem(size_str))
        
        # 文件类型 - 使用友好的类型描述
        file_type = get_file_type_description(filename)
        self.file_table.setItem(row, 3, QTableWidgetItem(file_type))
        
        # 创建日期和修改日期 - 使用已获取的 stat_info
        try:
            cdate_str = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M")
        except:
            cdate_str = ""
        self.file_table.setItem(row, 4, QTableWidgetItem(cdate_str))
        
        try:
            mdate_str = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
        except:
            mdate_str = ""
        self.file_table.setItem(row, 5, QTableWidgetItem(mdate_str))
        
        # 文件名长度
        self.file_table.setItem(row, 6, QTableWidgetItem(str(len(filename))))
        
        # 状态
        self.file_table.setItem(row, 7, QTableWidgetItem(""))

    def add_file_to_table(self, filepath: str):
        """添加文件到表格 - 兼容旧接口"""
        import datetime
        
        filename = os.path.basename(filepath)
        self.file_list.append(filepath)
        
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # 原文件名
        item = QTableWidgetItem(filename)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        self.file_table.setItem(row, 0, item)
        
        # 新文件名（预览）
        self.file_table.setItem(row, 1, QTableWidgetItem(filename))
        
        # 文件大小 - 超过100MB不显示
        try:
            size = os.path.getsize(filepath)
            if size <= 100 * 1024 * 1024:  # 100MB限制
                size_str = self.format_size(size)
            else:
                size_str = ""
        except:
            size_str = ""
        self.file_table.setItem(row, 2, QTableWidgetItem(size_str))
        
        # 文件类型 - 使用友好的类型描述
        file_type = get_file_type_description(filename)
        self.file_table.setItem(row, 3, QTableWidgetItem(file_type))
        
        # 创建日期
        try:
            ctime = os.path.getctime(filepath)
            cdate_str = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
        except:
            cdate_str = ""
        self.file_table.setItem(row, 4, QTableWidgetItem(cdate_str))
        
        # 修改日期
        try:
            mtime = os.path.getmtime(filepath)
            mdate_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except:
            mdate_str = ""
        self.file_table.setItem(row, 5, QTableWidgetItem(mdate_str))
        
        # 文件名长度
        self.file_table.setItem(row, 6, QTableWidgetItem(str(len(filename))))
        
        # 状态
        self.file_table.setItem(row, 7, QTableWidgetItem(""))
    
    def add_folder_to_table_fast(self, entry):
        """添加文件夹到表格 - 使用 DirEntry 优化性能"""
        import datetime
        
        filename = entry.name
        filepath = entry.path
        self.file_list.append(filepath)
        
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # 原文件名（文件夹用📁标记）
        item = QTableWidgetItem("📁 " + filename)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        self.file_table.setItem(row, 0, item)
        
        # 新文件名（预览）
        self.file_table.setItem(row, 1, QTableWidgetItem("📁 " + filename))
        
        # 文件大小 - 先显示"计算中..."，后台线程计算完成后更新
        self.file_table.setItem(row, 2, QTableWidgetItem(_("main_window.file_table.calculating")))
        
        # 文件类型
        self.file_table.setItem(row, 3, QTableWidgetItem(_("main_window.file_table.folder")))
        
        # 创建日期和修改日期 - 使用 entry.stat()
        try:
            stat_info = entry.stat(follow_symlinks=False)
            cdate_str = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M")
        except:
            cdate_str = ""
        self.file_table.setItem(row, 4, QTableWidgetItem(cdate_str))
        
        try:
            mdate_str = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
        except:
            mdate_str = ""
        self.file_table.setItem(row, 5, QTableWidgetItem(mdate_str))
        
        # 文件名长度
        self.file_table.setItem(row, 6, QTableWidgetItem(str(len(filename))))
        
        # 状态
        self.file_table.setItem(row, 7, QTableWidgetItem(""))

    def add_folder_to_table(self, filepath: str):
        """添加文件夹到表格 - 兼容旧接口"""
        import datetime
        
        filename = os.path.basename(filepath)
        self.file_list.append(filepath)
        
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # 原文件名（文件夹用📁标记）
        item = QTableWidgetItem("📁 " + filename)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        self.file_table.setItem(row, 0, item)
        
        # 新文件名（预览）
        self.file_table.setItem(row, 1, QTableWidgetItem("📁 " + filename))
        
        # 文件大小 - 不再计算文件夹大小，直接显示 <DIR>
        self.file_table.setItem(row, 2, QTableWidgetItem("<DIR>"))
        
        # 文件类型
        self.file_table.setItem(row, 3, QTableWidgetItem(_("main_window.file_table.folder")))
        
        # 创建日期
        try:
            ctime = os.path.getctime(filepath)
            cdate_str = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
        except:
            cdate_str = ""
        self.file_table.setItem(row, 4, QTableWidgetItem(cdate_str))
        
        # 修改日期
        try:
            mtime = os.path.getmtime(filepath)
            mdate_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except:
            mdate_str = ""
        self.file_table.setItem(row, 5, QTableWidgetItem(mdate_str))
        
        # 文件名长度
        self.file_table.setItem(row, 6, QTableWidgetItem(str(len(filename))))
        
        # 状态
        self.file_table.setItem(row, 7, QTableWidgetItem(""))
    
    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_folder_size(self, folder_path: str) -> int:
        """计算文件夹总大小 - 同步版本，用于兼容"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
        return total_size
    
    def _start_folder_size_calculation(self):
        """启动后台线程计算文件夹大小"""
        if not self._pending_folder_sizes:
            return
        
        # 创建工作线程
        self._folder_size_thread = QThread()
        self._folder_size_worker = FolderSizeWorker(self._pending_folder_sizes.copy())
        self._folder_size_worker.moveToThread(self._folder_size_thread)
        
        # 连接信号
        self._folder_size_thread.started.connect(self._folder_size_worker.run)
        self._folder_size_worker.size_calculated.connect(self._on_folder_size_calculated)
        self._folder_size_worker.finished.connect(self._on_folder_size_finished)
        
        # 启动线程
        self._folder_size_thread.start()
    
    def _stop_folder_size_calculation(self):
        """停止后台计算线程"""
        if self._folder_size_worker:
            self._folder_size_worker.stop()
        if self._folder_size_thread and self._folder_size_thread.isRunning():
            self._folder_size_thread.quit()
            self._folder_size_thread.wait(1000)  # 等待最多1秒
    
    def _on_folder_size_calculated(self, row: int, path: str, size: int):
        """文件夹大小计算完成的回调"""
        # 检查行是否还有效
        if row >= self.file_table.rowCount():
            return
        
        # 检查路径是否匹配（防止切换目录后更新错误的行）
        item = self.file_table.item(row, 0)
        if item:
            item_path = item.data(Qt.ItemDataRole.UserRole)
            if item_path != path:
                return
        
        # 更新大小显示
        if size >= 0:
            size_str = self.format_size(size)
        elif size == -2:
            # 超过100MB限制，不显示大小
            size_str = ""
        else:
            size_str = ""
        
        size_item = self.file_table.item(row, 2)
        if size_item:
            size_item.setText(size_str)
    
    def _on_folder_size_finished(self):
        """所有文件夹大小计算完成"""
        if self._folder_size_thread:
            self._folder_size_thread.quit()
            self._folder_size_thread.wait()
            self._folder_size_thread = None
            self._folder_size_worker = None
    
    def closeEvent(self, event):
        """窗口关闭时停止后台线程"""
        self._stop_folder_size_calculation()
        super().closeEvent(event)
    
    def on_header_clicked(self, column: int):
        """表头点击排序"""
        if column == self.sort_column:
            # 同一列，切换排序方向
            self.sort_ascending = not self.sort_ascending
        else:
            # 新列，默认升序
            self.sort_column = column
            self.sort_ascending = True
        
        # 根据列进行排序
        sort_keys = {
            0: lambda x: os.path.basename(x).lower(),  # 原文件名
            2: lambda x: os.path.getsize(x) if os.path.isfile(x) else 0,  # 大小
            3: lambda x: os.path.splitext(x)[1].lower(),  # 类型
            4: lambda x: os.path.getctime(x) if os.path.exists(x) else 0,  # 创建日期
            5: lambda x: os.path.getmtime(x) if os.path.exists(x) else 0,  # 修改日期
            6: lambda x: len(os.path.basename(x)),  # 长度
        }
        
        if column in sort_keys:
            try:
                self.file_list.sort(key=sort_keys[column], reverse=not self.sort_ascending)
                
                # 重新填充表格
                saved_selections = self.multi_selected_rows.copy()
                self.file_table.setRowCount(0)
                temp_list = self.file_list[:]
                self.file_list.clear()
                
                for filepath in temp_list:
                    if os.path.isfile(filepath):
                        self.add_file_to_table(filepath)
                    elif os.path.isdir(filepath):
                        self.add_folder_to_table(filepath)
                
                # 恢复选择状态（注意：排序后行号可能变化）
                self.multi_selected_rows.clear()
                self.highlight_all_selections()
                self.update_preview()
                
                direction = _("main_window.status.sort_asc") if self.sort_ascending else _("main_window.status.sort_desc")
                self.statusBar().showMessage(_("main_window.status.sorted_by_column").format(column=column+1, direction=direction))
            except Exception as e:
                self.statusBar().showMessage(_("main_window.status.sort_fail").format(error=e))
    
    def get_selected_rows(self) -> list:
        """获取选中的行索引列表 - 使用多选列表"""
        return sorted(list(self.multi_selected_rows))
    
    def execute_rename(self):
        """执行重命名 - 只对选中的文件进行重命名"""
        from core.logger import get_logger
        
        if not self.file_list:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.dialogs.no_files_to_rename"))
            return
        
        # 获取选中的行
        selected_rows = self.get_selected_rows()
        
        # 如果没有选中任何文件，提示用户
        if not selected_rows:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.dialogs.please_select_files"))
            return
        
        # 获取选中的文件路径
        selected_files = []
        for row in selected_rows:
            if row < len(self.file_list):
                selected_files.append((row, self.file_list[row]))
        
        if not selected_files:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.dialogs.no_valid_files_selected"))
            return
        
        # 检查是否有勾选的重命名模块
        checked_modules = []
        if self.regex_check.isChecked() and self.regex_pattern.text():
            checked_modules.append(_("main_window.help.regex.title"))
        if self.replace_check.isChecked() and self.replace_find.text():
            checked_modules.append(_("main_window.help.replace.title"))
        if self.remove_check.isChecked():
            # 检查移除模块是否有实际内容
            has_remove_content = (self.remove_first_n.value() > 0 or self.remove_last_n.value() > 0 or
                                  self.remove_from.value() > 0 or self.remove_to.value() > 0 or
                                  self.remove_chars.text() or self.remove_words.text() or
                                  self.remove_crop_mode.currentIndex() > 0 or
                                  self.remove_digits.isChecked() or self.remove_symbols.isChecked() or
                                  self.remove_chinese.isChecked() or self.remove_trim.isChecked() or
                                  self.remove_ds.isChecked() or self.remove_accents.isChecked() or
                                  self.remove_chars_check.isChecked() or self.remove_lead_dots.currentIndex() > 0)
            if has_remove_content:
                checked_modules.append(_("main_window.help.remove.title"))
        if self.add_check.isChecked() and (self.add_prefix.text() or self.add_suffix.text() or self.add_insert.text()):
            checked_modules.append(_("main_window.help.add.title"))
        if self.auto_date_check.isChecked() and (self.auto_date_type.currentIndex() > 0 or self.auto_date_custom.text()):
            checked_modules.append(_("main_window.help.auto_date.title"))
        if self.numbering_check.isChecked() and self.numbering_mode.currentIndex() > 0:
            checked_modules.append(_("main_window.help.number.title"))
        if self.name_check.isChecked() and (self.name_mode.currentIndex() > 0 or self.name_fixed.text()):
            checked_modules.append(_("main_window.help.file.title"))
        if self.case_check.isChecked():
            checked_modules.append(_("main_window.help.case.title"))
        if self.move_check.isChecked() and self.move_copy_mode.currentIndex() > 0 and self.move_target.currentIndex() > 0:
            checked_modules.append(_("main_window.help.move_copy.title"))
        if self.folder_name_check.isChecked() and self.folder_name_mode.currentIndex() > 0:
            checked_modules.append(_("main_window.help.folder.title"))
        if self.ext_check.isChecked() and (self.ext_mode.currentIndex() > 0 or self.ext_fixed.text()):
            checked_modules.append(_("main_window.help.extension.title"))
        
        # 检查新位置模块（移动/复制文件到新位置）- 只要有路径就生效
        has_new_location = bool(self.new_location_path.text().strip())
        if has_new_location:
            checked_modules.append(_("main_window.help.new_location.title"))
        
        if not checked_modules:
            QMessageBox.warning(
                self, _("main_window.dialogs.no_module_selected_title"),
                _("main_window.dialogs.no_module_selected_msg")
            )
            return
        
        reply = QMessageBox.question(
            self, _("main_window.dialogs.confirm_rename_title"),
            _("main_window.dialogs.confirm_rename_msg").format(count=len(selected_files), modules=', '.join(checked_modules)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 执行重命名时只应用勾选的模块
        self.sync_rules_to_engine(for_preview=False)
        
        # 重置计数器确保编号正确
        self.engine.reset_counter()
        
        success_count = 0
        error_count = 0
        rename_batch = []  # 记录本次重命名用于撤消
        
        # 获取日志记录器
        logger = get_logger()
        logger.log_batch_start(len(selected_files))
        
        # 只对选中的文件执行重命名
        for idx, (row, filepath) in enumerate(selected_files):
            status_item = self.file_table.item(row, 7)
            
            try:
                new_name = self.engine.preview_rename(filepath, idx)
                old_name = os.path.basename(filepath)
                
                if new_name == old_name:
                    status_item.setText(_("main_window.status.rename_no_change"))
                    logger.log_rename_operation(filepath, filepath, True, _("main_window.status.rename_no_change"))
                    continue
                
                # 确定目标目录（检查新位置模块）- 只要有路径就生效
                if self.new_location_path.text().strip():
                    target_dir = self.new_location_path.text().strip()
                    # 确保目标目录存在
                    if not os.path.exists(target_dir):
                        try:
                            os.makedirs(target_dir)
                        except Exception as e:
                            status_item.setText(_("main_window.status.rename_mkdir_fail"))
                            status_item.setForeground(Qt.GlobalColor.red)
                            error_count += 1
                            logger.log_rename_operation(filepath, "", False, f"{_('main_window.status.rename_mkdir_fail')}: {e}")
                            continue
                else:
                    target_dir = os.path.dirname(filepath)
                
                new_path = os.path.join(target_dir, new_name)
                
                # 检查目标文件是否已存在（排除仅大小写变化的情况）
                # Windows文件系统不区分大小写，所以需要特殊处理
                is_case_only_change = filepath.lower() == new_path.lower() and filepath != new_path
                if os.path.exists(new_path) and not is_case_only_change:
                    status_item.setText(_("main_window.status.rename_target_exists"))
                    status_item.setForeground(Qt.GlobalColor.red)
                    error_count += 1
                    logger.log_rename_operation(filepath, new_path, False, _("main_window.status.rename_target_exists"))
                    continue
                
                # 执行重命名/移动/复制
                import shutil
                if self.new_location_path.text().strip():
                    if self.new_location_copy.isChecked():
                        # 复制到新位置
                        shutil.copy2(filepath, new_path)
                    else:
                        # 移动到新位置
                        shutil.move(filepath, new_path)
                else:
                    # 原地重命名（Windows上仅改变大小写需要两步）
                    if is_case_only_change:
                        # 先重命名为临时文件，再重命名为目标文件
                        temp_path = filepath + ".tmp_rename"
                        os.rename(filepath, temp_path)
                        os.rename(temp_path, new_path)
                    else:
                        os.rename(filepath, new_path)
                
                success_count += 1
                status_item.setText(_("main_window.status.rename_success"))
                status_item.setForeground(Qt.GlobalColor.darkGreen)
                rename_batch.append((filepath, new_path))
                logger.log_rename_operation(filepath, new_path, True, _("main_window.status.rename_success"))
                
                # 更新文件列表和表格
                self.file_list[row] = new_path
                item = self.file_table.item(row, 0)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, new_path)
                    item.setText(new_name)
                    
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                status_item.setText(_("main_window.status.rename_fail").format(error=error_msg))
                status_item.setForeground(Qt.GlobalColor.red)
                logger.log_rename_operation(filepath, "", False, error_msg)
        
        # 记录批量操作结束
        logger.log_batch_end(success_count, error_count)
        
        # 保存重命名历史用于撤消
        if rename_batch:
            if not hasattr(self, 'rename_history'):
                self.rename_history = []
            self.rename_history.append(rename_batch)
        
        self.statusBar().showMessage(_("main_window.status.rename_complete").format(success=success_count, error=error_count))
        
        # 重命名完成后，重置所有模块到初始状态
        self.reset_all_modules()
        
        self.update_preview()
    
    def reset_all_modules(self):
        """重置所有模块到初始状态（不显示消息）"""
        self.engine.rules = RenameRules()
        
        # 取消所有模块的勾选（filter_check和new_location_check已取消勾选框，不需要处理）
        for group in [self.regex_check, self.replace_check, self.remove_check,
                      self.add_check, self.auto_date_check, self.numbering_check,
                      self.name_check, self.case_check, self.move_check,
                      self.folder_name_check, self.ext_check]:
            group.setChecked(False)
        
        # 清除所有文本输入框
        for line_edit in [self.regex_pattern, self.regex_replace, self.replace_find,
                          self.replace_with, self.remove_chars, self.remove_words,
                          self.remove_crop_text, self.add_prefix, self.add_suffix, 
                          self.add_insert, self.name_fixed, self.ext_fixed,
                          self.auto_date_sep, self.auto_date_custom, self.case_exception,
                          self.move_separator, self.folder_name_sep, self.numbering_separator,
                          self.filter_pattern, self.new_location_path]:
            line_edit.clear()
        
        # 重置所有数值输入框
        for spinbox in [self.remove_first_n, self.remove_last_n, self.remove_from,
                        self.remove_to, self.add_insert_pos, self.move_from, self.move_count,
                        self.auto_date_distance, self.filter_min_name_len, self.filter_max_name_len,
                        self.filter_min_path_len, self.filter_max_path_len]:
            spinbox.setValue(0)
        
        # 重置编号模块
        self.numbering_start.setValue(1)
        self.numbering_increment.setValue(1)
        self.numbering_padding.setValue(0)
        self.numbering_break.setValue(0)
        self.numbering_at.setValue(0)
        self.numbering_mode.setCurrentIndex(0)
        self.numbering_type.setCurrentIndex(0)
        self.numbering_roman.setCurrentIndex(0)
        self.numbering_folder.setChecked(False)
        
        # 重置其他下拉框
        self.name_mode.setCurrentIndex(0)
        self.case_mode.setCurrentIndex(0)
        self.move_copy_mode.setCurrentIndex(0)
        self.move_target.setCurrentIndex(0)
        self.folder_name_mode.setCurrentIndex(0)
        self.ext_mode.setCurrentIndex(0)
        self.auto_date_type.setCurrentIndex(0)
        self.auto_date_mode.setCurrentIndex(0)
        self.auto_date_format.setCurrentIndex(0)
        self.remove_crop_mode.setCurrentIndex(0)
        self.remove_lead_dots.setCurrentIndex(0)
        
        # 重置复选框
        self.regex_include_ext.setChecked(False)
        self.replace_case_sensitive.setChecked(False)
        self.remove_digits.setChecked(False)
        self.remove_chinese.setChecked(False)
        self.remove_symbols.setChecked(False)
        self.remove_trim.setChecked(False)
        self.remove_ds.setChecked(False)
        self.remove_accents.setChecked(False)
        self.remove_chars_check.setChecked(False)
        self.add_word_space.setChecked(False)
        self.auto_date_center.setChecked(False)
        self.case_digits.setChecked(False)
        self.case_symbols.setChecked(False)
        self.filter_case_sensitive.setChecked(False)
        self.filter_folders.setChecked(True)  # 默认勾选文件夹
        self.filter_files.setChecked(True)
        self.filter_hidden.setChecked(False)
        self.filter_subfolders.setChecked(False)
        self.new_location_copy.setChecked(False)
        
        # 重置默认值
        self.auto_date_connect.setText("_")
        self.folder_name_sep.setText("_")
        self.folder_name_levels.setValue(1)
    
    def clear_rules(self):
        """清除所有规则"""
        # 先保存当前状态用于恢复
        self.save_current_input_state()
        
        self.reset_all_modules()
        
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.rules_cleared"))
    
    def open_folder(self):
        """打开文件夹对话框"""
        path = QFileDialog.getExistingDirectory(self, _("main_window.dialogs.select_folder_title"))
        if path:
            self.load_folder(path)
    
    def select_all_files(self):
        """全选文件"""
        self.multi_selected_rows = set(range(self.file_table.rowCount()))
        self.temp_clicked_rows.clear()
        self.highlight_all_selections()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.all_selected").format(count=len(self.multi_selected_rows)))
    
    def clear_file_list(self):
        """清除文件列表"""
        self.file_list.clear()
        self.file_table.setRowCount(0)
        self.multi_selected_rows.clear()
        self.temp_clicked_rows.clear()
        self.statusBar().showMessage(_("main_window.status.files_cleared"))
    
    def save_config(self):
        """保存配置"""
        filepath, _ = QFileDialog.getSaveFileName(self, _("main_window.menu.save_current_config"), "", "JSON (*.json)")
        if filepath:
            self.sync_rules_to_engine()
            if self.config_manager.save_rules(self.engine.rules, filepath):
                QMessageBox.information(self, _("main_window.dialogs.success_title"), _("main_window.dialogs.save_config_success"))
            else:
                QMessageBox.warning(self, _("main_window.dialogs.error_title"), _("main_window.dialogs.save_config_fail"))
    
    def load_config(self):
        """加载配置"""
        filepath, _ = QFileDialog.getOpenFileName(self, _("main_window.menu.load_config"), "", "JSON (*.json)")
        if filepath:
            rules = self.config_manager.load_rules(filepath)
            if rules:
                self.engine.rules = rules
                self.sync_rules_from_engine()
                self.update_preview()
                QMessageBox.information(self, _("main_window.dialogs.success_title"), _("main_window.dialogs.load_config_success"))
            else:
                QMessageBox.warning(self, _("main_window.dialogs.error_title"), _("main_window.dialogs.load_config_fail"))

    def sync_rules_from_engine(self):
        """从引擎同步规则到UI"""
        rules = self.engine.rules
        
        self.regex_check.setChecked(rules.regex_enabled)
        self.regex_pattern.setText(rules.regex_pattern)
        self.regex_replace.setText(rules.regex_replace)
        
        self.replace_check.setChecked(rules.replace_enabled)
        self.replace_find.setText(rules.replace_find)
        self.replace_with.setText(rules.replace_with)
        self.replace_case_sensitive.setChecked(rules.replace_case_sensitive)
        
        self.remove_check.setChecked(rules.remove_enabled)
        self.remove_first_n.setValue(rules.remove_first_n)
        self.remove_last_n.setValue(rules.remove_last_n)
        self.remove_from.setValue(rules.remove_from)
        self.remove_to.setValue(rules.remove_to)
        self.remove_chars.setText(rules.remove_chars)
        self.remove_words.setText(rules.remove_words)
        self.remove_digits.setChecked(rules.remove_digits)
        
        self.add_check.setChecked(rules.add_enabled)
        self.add_prefix.setText(rules.add_prefix)
        self.add_suffix.setText(rules.add_suffix)
        self.add_insert.setText(rules.add_insert)
        self.add_insert_pos.setValue(rules.add_insert_pos)
        
        self.auto_date_check.setChecked(rules.auto_date_enabled)
        self.auto_date_mode.setCurrentIndex(rules.auto_date_mode)
        self.auto_date_format.setCurrentText(rules.auto_date_format)
        self.auto_date_type.setCurrentIndex(rules.auto_date_pos)
        
        self.numbering_check.setChecked(rules.numbering_enabled)
        self.numbering_mode.setCurrentIndex(rules.numbering_mode)
        self.numbering_start.setValue(rules.numbering_start)
        self.numbering_increment.setValue(rules.numbering_increment)
        self.numbering_padding.setValue(rules.numbering_padding)
        self.numbering_separator.setText(rules.numbering_separator)
        self.numbering_at.setValue(rules.numbering_insert_pos)
        self.numbering_break.setValue(rules.numbering_break)
        self.numbering_type.setCurrentIndex(rules.numbering_type)
        self.numbering_roman.setCurrentIndex(rules.numbering_roman)
        
        self.name_check.setChecked(rules.name_enabled)
        self.name_mode.setCurrentIndex(rules.name_mode)
        self.name_fixed.setText(rules.name_fixed)
        
        self.case_check.setChecked(rules.case_enabled)
        if rules.case_mode.value > 0:
            self.case_mode.setCurrentIndex(rules.case_mode.value - 1)
        
        self.move_check.setChecked(rules.move_enabled)
        self.move_copy_mode.setCurrentIndex(rules.move_copy_mode)
        self.move_from.setValue(rules.move_copy_from)
        self.move_target.setCurrentIndex(rules.move_copy_target)
        self.move_count.setValue(rules.move_copy_count)
        self.move_separator.setText(rules.move_copy_separator)
        
        self.folder_name_check.setChecked(rules.folder_name_enabled)
        self.folder_name_mode.setCurrentIndex(rules.folder_name_pos)
        self.folder_name_sep.setText(rules.folder_name_separator)
        self.folder_name_levels.setValue(rules.folder_name_levels)
        
        self.ext_check.setChecked(rules.ext_enabled)
        self.ext_mode.setCurrentIndex(rules.ext_mode)
        self.ext_fixed.setText(rules.ext_fixed)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, _("main_window.dialogs.about_title"),
            _("main_window.dialogs.about_content")
        )
    
    def changeEvent(self, event):
        """窗口状态变化事件 - 处理最小化时隐藏帮助弹出框"""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            # 当窗口最小化时，隐藏帮助弹出框
            if self.isMinimized():
                if ResetableGroupBox._help_popup is not None:
                    ResetableGroupBox._help_popup.hide()
                    ResetableGroupBox._current_help_module = None
        super().changeEvent(event)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖放进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖放事件"""
        urls = event.mimeData().urls()
        files_added = 0
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isfile(path):
                if path not in self.file_list:
                    self.add_file_to_table(path)
                    files_added += 1
            elif os.path.isdir(path):
                self.load_folder(path)
                return
        
        if files_added > 0:
            self.update_preview()
            self.statusBar().showMessage(_("main_window.status.files_added").format(count=files_added))

    # ========== 选项菜单功能 ==========
    
    def toggle_always_on_top(self):
        """切换窗口总在最前"""
        if self.always_on_top_action.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()
    
    def toggle_show_hidden(self):
        """切换显示隐藏文件"""
        # 重新加载当前文件夹
        if hasattr(self, 'current_folder') and self.current_folder:
            self.load_folder(self.current_folder)
    
    def toggle_row_selection(self):
        """切换整行选择模式"""
        if self.row_select_action.isChecked():
            self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        else:
            self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
    
    def sort_files(self, sort_by: str):
        """排序文件列表"""
        if not self.file_list:
            return
        
        if sort_by == "name":
            self.file_list.sort(key=lambda x: os.path.basename(x).lower())
        elif sort_by == "size":
            self.file_list.sort(key=lambda x: os.path.getsize(x) if os.path.exists(x) else 0)
        elif sort_by == "date":
            self.file_list.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
        elif sort_by == "type":
            self.file_list.sort(key=lambda x: os.path.splitext(x)[1].lower())
        
        # 重新填充表格
        self.file_table.setRowCount(0)
        for filepath in self.file_list[:]:
            self.file_list.remove(filepath)
            self.add_file_to_table(filepath)
        
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.sorted_by").format(by=sort_by))
    
    def extract_numbers(self):
        """提取文件名中的数字"""
        import re
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                filename = item.text()
                name, ext = os.path.splitext(filename)
                numbers = re.findall(r'\d+', name)
                if numbers:
                    new_name = ''.join(numbers) + ext
                    self.file_table.setItem(row, 1, QTableWidgetItem(new_name))
    
    def extract_letters(self):
        """提取文件名中的字母"""
        import re
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                filename = item.text()
                name, ext = os.path.splitext(filename)
                letters = re.findall(r'[a-zA-Z]+', name)
                if letters:
                    new_name = ''.join(letters) + ext
                    self.file_table.setItem(row, 1, QTableWidgetItem(new_name))
    
    def show_log(self):
        """显示操作日志"""
        from core.logger import get_logger
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
        
        logger = get_logger()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(_("main_window.menu.log"))
        dialog.resize(800, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 日志内容显示
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(logger.get_log_content())
        text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 10pt;")
        layout.addWidget(text_edit)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton(_("main_window.menu.refresh_files"))
        refresh_btn.clicked.connect(lambda: text_edit.setPlainText(logger.get_log_content()))
        btn_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton(_("main_window.menu.log") + " " + _("main_window.menu.save"))
        def export_log():
            filepath, _ = QFileDialog.getSaveFileName(dialog, _("main_window.menu.log") + " " + _("main_window.menu.save"), "rename_log.txt", "文本文件 (*.txt)")
            if filepath:
                if logger.export_log(filepath):
                    QMessageBox.information(dialog, _("main_window.dialogs.success_title"), _("main_window.status.export_success").format(path=filepath))
                else:
                    QMessageBox.warning(dialog, _("main_window.dialogs.error_title"), _("logger.fail"))
        export_btn.clicked.connect(export_log)
        btn_layout.addWidget(export_btn)
        
        open_folder_btn = QPushButton(_("main_window.menu.open") + " " + _("main_window.menu.log") + _("main_window.file_table.folder"))
        def open_log_folder():
            import subprocess
            log_dir = os.path.dirname(logger.get_log_file_path())
            if os.path.exists(log_dir):
                subprocess.run(['explorer', log_dir])
        open_folder_btn.clicked.connect(open_log_folder)
        btn_layout.addWidget(open_folder_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton(_("login_dialog.close"))
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def show_char_convert(self):
        """显示字符转换对话框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTextEdit, QPushButton, QLabel, QGroupBox, QRadioButton, QButtonGroup, QCheckBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(_("main_window.menu.char_convert"))
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 转换选项组
        options_group = QGroupBox(_("main_window.menu.options"))
        options_layout = QGridLayout(options_group)
        
        # 全角/半角转换
        fullwidth_group = QGroupBox(_("main_window.char_convert_fullwidth"))
        fullwidth_layout = QVBoxLayout(fullwidth_group)
        self.char_fullwidth_none = QRadioButton(_("main_window.rules.remove.crop_modes")[0])
        self.char_fullwidth_none.setChecked(True)
        self.char_fullwidth_to_half = QRadioButton(_("main_window.char_convert_fullwidth_to_half"))
        self.char_fullwidth_to_full = QRadioButton(_("main_window.char_convert_fullwidth_to_full"))
        fullwidth_layout.addWidget(self.char_fullwidth_none)
        fullwidth_layout.addWidget(self.char_fullwidth_to_half)
        fullwidth_layout.addWidget(self.char_fullwidth_to_full)
        options_layout.addWidget(fullwidth_group, 0, 0)
        
        # 大小写转换
        case_group = QGroupBox(_("main_window.rules.case.mode"))
        case_layout = QVBoxLayout(case_group)
        self.char_case_none = QRadioButton(_("main_window.rules.remove.crop_modes")[0])
        self.char_case_none.setChecked(True)
        self.char_case_upper = QRadioButton(_("main_window.rules.case.modes")[2])
        self.char_case_lower = QRadioButton(_("main_window.rules.case.modes")[1])
        self.char_case_title = QRadioButton(_("main_window.rules.case.modes")[3])
        case_layout.addWidget(self.char_case_none)
        case_layout.addWidget(self.char_case_upper)
        case_layout.addWidget(self.char_case_lower)
        case_layout.addWidget(self.char_case_title)
        options_layout.addWidget(case_group, 0, 1)
        
        # 特殊字符处理
        special_group = QGroupBox(_("main_window.char_convert_special"))
        special_layout = QVBoxLayout(special_group)
        self.char_remove_spaces = QCheckBox(_("main_window.char_convert_remove_spaces"))
        self.char_underscore_to_space = QCheckBox(_("main_window.char_convert_underscore_to_space"))
        self.char_space_to_underscore = QCheckBox(_("main_window.char_convert_space_to_underscore"))
        self.char_remove_brackets = QCheckBox(_("main_window.char_convert_remove_brackets"))
        self.char_normalize_unicode = QCheckBox(_("main_window.char_convert_normalize_unicode"))
        special_layout.addWidget(self.char_remove_spaces)
        special_layout.addWidget(self.char_underscore_to_space)
        special_layout.addWidget(self.char_space_to_underscore)
        special_layout.addWidget(self.char_remove_brackets)
        special_layout.addWidget(self.char_normalize_unicode)
        options_layout.addWidget(special_group, 1, 0, 1, 2)
        
        layout.addWidget(options_group)
        
        # 预览区域
        preview_group = QGroupBox(_("main_window.char_convert_preview"))
        preview_layout = QVBoxLayout(preview_group)
        self.char_preview_text = QTextEdit()
        self.char_preview_text.setReadOnly(True)
        self.char_preview_text.setMaximumHeight(150)
        preview_layout.addWidget(self.char_preview_text)
        layout.addWidget(preview_group)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        
        preview_btn = QPushButton(_("main_window.char_convert_preview_btn"))
        preview_btn.clicked.connect(lambda: self._preview_char_convert())
        btn_layout.addWidget(preview_btn)
        
        apply_btn = QPushButton(_("main_window.char_convert_apply_btn"))
        apply_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        apply_btn.clicked.connect(lambda: self._apply_char_convert(dialog))
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton(_("login_dialog.close"))
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _preview_char_convert(self):
        """预览字符转换效果"""
        preview_lines = []
        selected_rows = self.get_selected_rows()
        rows_to_preview = selected_rows if selected_rows else range(min(10, self.file_table.rowCount()))
        
        for row in rows_to_preview:
            item = self.file_table.item(row, 0)
            if item:
                old_name = item.text()
                new_name = self._convert_filename(old_name)
                if old_name != new_name:
                    preview_lines.append(f"{old_name} → {new_name}")
        
        if preview_lines:
            self.char_preview_text.setPlainText("\n".join(preview_lines))
        else:
            self.char_preview_text.setPlainText(_("main_window.char_convert_no_files"))

    
    def _convert_filename(self, filename: str) -> str:
        """根据选项转换文件名"""
        import unicodedata
        import re
        
        name, ext = os.path.splitext(filename)
        result = name
        
        # 全角/半角转换
        if hasattr(self, 'char_fullwidth_to_half') and self.char_fullwidth_to_half.isChecked():
            result = self._fullwidth_to_halfwidth(result)
        elif hasattr(self, 'char_fullwidth_to_full') and self.char_fullwidth_to_full.isChecked():
            result = self._halfwidth_to_fullwidth(result)
        
        # 大小写转换
        if hasattr(self, 'char_case_upper') and self.char_case_upper.isChecked():
            result = result.upper()
        elif hasattr(self, 'char_case_lower') and self.char_case_lower.isChecked():
            result = result.lower()
        elif hasattr(self, 'char_case_title') and self.char_case_title.isChecked():
            result = result.title()
        
        # 特殊字符处理
        if hasattr(self, 'char_remove_spaces') and self.char_remove_spaces.isChecked():
            result = result.replace(" ", "")
        if hasattr(self, 'char_underscore_to_space') and self.char_underscore_to_space.isChecked():
            result = result.replace("_", " ")
        if hasattr(self, 'char_space_to_underscore') and self.char_space_to_underscore.isChecked():
            result = result.replace(" ", "_")
        if hasattr(self, 'char_remove_brackets') and self.char_remove_brackets.isChecked():
            result = re.sub(r'\([^)]*\)', '', result)
            result = re.sub(r'\[[^\]]*\]', '', result)
            result = re.sub(r'【[^】]*】', '', result)
        if hasattr(self, 'char_normalize_unicode') and self.char_normalize_unicode.isChecked():
            result = unicodedata.normalize('NFC', result)
        
        return result + ext
    
    def _fullwidth_to_halfwidth(self, text: str) -> str:
        """全角转半角"""
        result = []
        for char in text:
            code = ord(char)
            if code == 0x3000:  # 全角空格
                result.append(' ')
            elif 0xFF01 <= code <= 0xFF5E:  # 全角字符
                result.append(chr(code - 0xFEE0))
            else:
                result.append(char)
        return ''.join(result)
    
    def _halfwidth_to_fullwidth(self, text: str) -> str:
        """半角转全角"""
        result = []
        for char in text:
            code = ord(char)
            if code == 0x20:  # 半角空格
                result.append('\u3000')
            elif 0x21 <= code <= 0x7E:  # 半角字符
                result.append(chr(code + 0xFEE0))
            else:
                result.append(char)
        return ''.join(result)
    
    def _apply_char_convert(self, dialog):
        """应用字符转换"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.dialogs.please_select_files"))
            return
        
        # 更新预览列
        for row in selected_rows:
            item = self.file_table.item(row, 0)
            if item:
                old_name = item.text()
                new_name = self._convert_filename(old_name)
                self.file_table.setItem(row, 1, QTableWidgetItem(new_name))
        
        dialog.close()
        self.statusBar().showMessage(_("main_window.status.char_convert_preview").format(count=len(selected_rows)))

    # ========== 帮助菜单功能 ==========
    
    def show_help_content(self):
        """显示帮助内容"""
        help_text = f"""
<h2>{_("main_window.menu.help")}</h2>

<h3>{_("main_window.help.file.title")}</h3>
<p>{_("main_window.help.file.content")}</p>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle(_("main_window.menu.content"))
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def show_help_index(self):
        """显示帮助索引"""
        index_text = f"""
<h3>{_("main_window.menu.index")}</h3>
<ul>
<li>{_("main_window.help.regex.title")}</li>
<li>{_("main_window.help.replace.title")}</li>
<li>{_("main_window.help.remove.title")}</li>
</ul>
"""
        msg = QMessageBox(self)
        msg.setWindowTitle(_("main_window.menu.index"))
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(index_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def show_help_search(self):
        """显示帮助搜索"""
        from PyQt6.QtWidgets import QInputDialog
        keyword, ok = QInputDialog.getText(self, _("main_window.menu.search"), _("main_window.menu.search") + ":")
        if ok and keyword:
            found = False
            module_help_info = get_module_help_info()
            for key, info in module_help_info.items():
                if keyword.lower() in info["title"].lower() or keyword.lower() in info["content"].lower():
                    QMessageBox.information(self, _("main_window.status.search_result_title").format(key=info["title"]), info["content"])
                    found = True
                    break
            
            if not found:
                QMessageBox.information(self, _("main_window.dialogs.search_result"), _("main_window.status.search_no_result").format(keyword=keyword))
    
    def show_daily_tip(self):
        """显示每日提示"""
        import random
        tips = [
            _("main_window.help.regex.content"),
            _("main_window.help.replace.content"),
            _("main_window.help.remove.content"),
            _("main_window.help.number.content")
        ]
        tip = random.choice(tips)
        QMessageBox.information(self, _("main_window.menu.tip"), tip)
    
    def check_update(self, silent=False):
        """检查更新"""
        try:
            # 1. 调用检查更新接口
            api_url = "http://software.kunqiongai.com:8000/api/v1/updates/check/"
            params = {
                "software": SOFTWARE_ID,
                "version": VERSION
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("has_update"):
                new_version = data.get("version")
                update_log = data.get("update_log", _("logger.no_log"))
                download_url = data.get("download_url")
                package_hash = data.get("package_hash")
                
                # 2. 提示用户发现新版本 (使用自定义对话框)
                def perform_update():
                    # 3. 准备启动参数
                    # 确定基础路径
                    if getattr(sys, 'frozen', False):
                        base_path = os.path.dirname(sys.executable)
                        main_exe = os.path.basename(sys.executable)
                    else:
                        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        main_exe = "批量重命名.exe"  # 假设打包后的名称
                    
                    updater_exe = os.path.join(base_path, "updater.exe")
                    if not os.path.exists(updater_exe):
                        # 如果没有 exe，尝试找 py
                        updater_exe = os.path.join(base_path, "updater.py")
                        launch_cmd = ["python", updater_exe]
                    else:
                        launch_cmd = [updater_exe]
                    
                    # 4. 启动 Updater
                    args = [
                        "--url", download_url,
                        "--hash", package_hash,
                        "--dir", base_path,
                        "--exe", main_exe,
                        "--pid", str(os.getpid())
                    ]
                    
                    # 使用 Popen 启动并脱离父进程
                    subprocess.Popen(launch_cmd + args, creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                    
                    # 5. 立即退出主程序
                    QApplication.instance().quit()

                dialog = UpdateDialog(self, new_version, update_log, download_url, perform_update)
                dialog.exec()
            else:
                if not silent:
                    QMessageBox.information(
                        self, _("main_window.menu.update"),
                        _("main_window.status.current_version_info").format(version=VERSION) + 
                        _("update_dialog.latest_version").format(version=VERSION)
                    )
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, _("main_window.dialogs.update_error_title"), _("main_window.status.update_error").format(error=str(e)))

    # ========== 动作菜单功能 ==========
    
    def deselect_all_files(self):
        """取消所有选择"""
        self.multi_selected_rows.clear()
        self.temp_clicked_rows.clear()
        self.file_table.clearSelection()
        self.highlight_all_selections()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.file_table.cancel_selected"))
    
    def invert_selection(self):
        """反向选择"""
        all_rows = set(range(self.file_table.rowCount()))
        # 反转选择：未选中的变为选中，已选中的变为未选中
        self.multi_selected_rows = all_rows - self.multi_selected_rows
        self.temp_clicked_rows.clear()
        self.highlight_all_selections()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.invert_selection_info").format(count=len(self.multi_selected_rows)))
    
    def select_from_clipboard(self):
        """从剪贴板选择文件"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.status.none"))
            return
        
        # 按行分割剪贴板内容
        names = [line.strip() for line in text.split('\n') if line.strip()]
        selected_count = 0
        
        self.file_table.clearSelection()
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item and item.text() in names:
                self.file_table.selectRow(row)
                selected_count += 1
        
        self.statusBar().showMessage(_("main_window.status.clipboard_selection_info").format(count=selected_count))
    
    def goto_path(self):
        """转跳到指定路径"""
        from PyQt6.QtWidgets import QInputDialog
        path, ok = QInputDialog.getText(self, _("main_window.menu.goto_path"), _("main_window.rules.new_location.path") + ":")
        if ok and path:
            if os.path.isdir(path):
                self.load_folder(path)
            else:
                QMessageBox.warning(self, _("main_window.dialogs.error_title"), _("main_window.status.path_not_exist").format(path=path))
    
    def refresh_files(self):
        """刷新文件列表（重新读取文件信息并更新预览）"""
        if not self.file_list:
            self.statusBar().showMessage(_("main_window.status.none"))
            return
        
        # 保存当前选择状态
        saved_selections = self.multi_selected_rows.copy()
        
        # 更新每个文件的信息
        import datetime
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item:
                filepath = item.data(Qt.ItemDataRole.UserRole)
                if filepath and os.path.exists(filepath):
                    # 更新文件大小
                    try:
                        size = os.path.getsize(filepath)
                        self.file_table.setItem(row, 2, QTableWidgetItem(self.format_size(size)))
                    except:
                        pass
                    
                    # 更新修改日期
                    try:
                        mtime = os.path.getmtime(filepath)
                        mdate_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                        self.file_table.setItem(row, 5, QTableWidgetItem(mdate_str))
                    except:
                        pass
        
        # 恢复选择状态
        self.multi_selected_rows = saved_selections
        self.highlight_all_selections()
        
        # 更新预览
        self.update_preview()
        self.statusBar().showMessage(_("main_window.menu.refresh_files"))
    
    def refresh_directory(self):
        """刷新当前目录（重新加载文件夹）"""
        # 尝试从路径标签获取当前路径
        path_text = self.path_label.text()
        if path_text.startswith(_("main_window.file_table.path_prefix")):
            path = path_text[len(_("main_window.file_table.path_prefix")):]
            if os.path.isdir(path):
                self.load_folder(path)
                self.statusBar().showMessage(_("main_window.menu.refresh_dir"))
                return
        
        # 如果有current_folder属性
        if hasattr(self, 'current_folder') and self.current_folder:
            if os.path.isdir(self.current_folder):
                self.load_folder(self.current_folder)
                self.statusBar().showMessage(_("main_window.menu.refresh_dir"))
                return
        
        self.statusBar().showMessage(_("main_window.status.none"))
    
    def toggle_folder_tree(self):
        """显示/隐藏文件夹树（包括标签和整个容器）"""
        # 获取文件夹树的父容器（包含"文件夹浏览"标签和树控件）
        folder_widget = self.folder_tree.parent()
        if folder_widget:
            if folder_widget.isVisible():
                # 隐藏整个容器，包括标签
                folder_widget.hide()
                # 同时设置最小宽度为0，确保完全隐藏
                folder_widget.setMinimumWidth(0)
                folder_widget.setMaximumWidth(0)
                self.statusBar().showMessage(_("main_window.menu.toggle_tree") + " [OFF]")
            else:
                # 显示容器
                folder_widget.show()
                # 恢复正常宽度
                folder_widget.setMinimumWidth(0)
                folder_widget.setMaximumWidth(16777215)  # Qt默认最大值
                self.statusBar().showMessage(_("main_window.menu.toggle_tree") + " [ON]")
    
    def undo_rename(self):
        """撤消重命名"""
        if not hasattr(self, 'rename_history') or not self.rename_history:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.status.none"))
            return
        
        # 获取最后一次重命名记录
        last_rename = self.rename_history.pop()
        undo_count = 0
        
        for old_path, new_path in last_rename:
            try:
                if os.path.exists(new_path) and not os.path.exists(old_path):
                    os.rename(new_path, old_path)
                    undo_count += 1
            except Exception as e:
                print(f"撤消失败: {e}")
        
        # 刷新文件列表
        self.refresh_directory()
        QMessageBox.information(self, _("main_window.dialogs.undo_complete_title"), _("main_window.status.undo_complete").format(count=undo_count))
    
    def create_undo_batch(self):
        """创建撤消批处理文件"""
        if not hasattr(self, 'rename_history') or not self.rename_history:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.status.none"))
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, _("main_window.menu.create_undo_batch"), "undo_rename.bat", "批处理文件 (*.bat)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("@echo off\n")
                    f.write("chcp 65001\n")
                    f.write(f"echo {_('main_window.menu.undo_rename')}...\n")
                    
                    for rename_batch in reversed(self.rename_history):
                        for old_path, new_path in rename_batch:
                            f.write(f'ren "{new_path}" "{os.path.basename(old_path)}"\n')
                    
                    f.write(f"echo {_('main_window.status.rename_success')}!\n")
                    f.write("pause\n")
                
                QMessageBox.information(self, _("main_window.dialogs.success_title"), _("main_window.status.undo_batch_saved").format(path=filepath))
            except Exception as e:
                QMessageBox.warning(self, _("main_window.dialogs.error_title"), f"{_('main_window.status.rename_fail').format(error=e)}")
    
    def toggle_zoom(self):
        """切换缩放模式"""
        if not hasattr(self, 'is_zoomed'):
            self.is_zoomed = False
            self.normal_geometry = self.geometry()
        
        if self.is_zoomed:
            self.setGeometry(self.normal_geometry)
            self.is_zoomed = False
            self.statusBar().showMessage(_("main_window.menu.zoom") + " [OFF]")
        else:
            self.normal_geometry = self.geometry()
            screen = self.screen().availableGeometry()
            self.setGeometry(screen)
            self.is_zoomed = True
            self.statusBar().showMessage(_("main_window.menu.zoom") + " [ON]")
    
    def random_sort(self):
        """随机排序文件列表"""
        import random
        if not self.file_list:
            return
        
        random.shuffle(self.file_list)
        
        # 重新填充表格
        self.file_table.setRowCount(0)
        temp_list = self.file_list[:]
        self.file_list.clear()
        for filepath in temp_list:
            self.add_file_to_table(filepath)
        
        self.update_preview()
        self.statusBar().showMessage(_("main_window.menu.random_sort"))
    
    def clear_import_pairs(self):
        """清除导入配对"""
        self.file_list.clear()
        self.file_table.setRowCount(0)
        self.statusBar().showMessage(_("main_window.menu.clear_import"))
    
    def debug_new_names(self):
        """调试新名称 - 显示所有新名称的详细信息"""
        if self.file_table.rowCount() == 0:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.status.none"))
            return
        
        debug_info = _("main_window.menu.debug_names") + ":\n" + "=" * 50 + "\n\n"
        
        for row in range(self.file_table.rowCount()):
            old_item = self.file_table.item(row, 0)
            new_item = self.file_table.item(row, 1)
            
            if old_item and new_item:
                old_name = old_item.text()
                new_name = new_item.text()
                changed = "✓" if old_name != new_name else "-"
                
                debug_info += f"[{row + 1}] {changed}\n"
                debug_info += f"    {_('main_window.file_table.orig_name')}: {old_name}\n"
                debug_info += f"    {_('main_window.file_table.new_name')}: {new_name}\n"
                debug_info += f"    {_('main_window.file_table.length')}: {len(old_name)} -> {len(new_name)}\n\n"
        
        # 显示在消息框中
        from PyQt6.QtWidgets import QTextEdit, QDialog, QVBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle(_("main_window.menu.debug_names"))
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setPlainText(debug_info)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        dialog.exec()

    # ========== 文件菜单功能 ==========
    
    def save_config_as(self):
        """另存为配置"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, _("main_window.menu.save_as"), "", "配置文件 (*.json);;所有文件 (*.*)"
        )
        if filepath:
            self.sync_rules_to_engine()
            if self.config_manager.save_rules(self.engine.rules, filepath):
                self.current_config_file = filepath
                QMessageBox.information(self, _("main_window.dialogs.success_title"), _("main_window.status.config_saved_to").format(path=filepath))
            else:
                QMessageBox.warning(self, _("main_window.dialogs.error_title"), _("main_window.dialogs.save_config_fail"))
    
    def restore_config(self):
        """恢复默认配置"""
        reply = QMessageBox.question(
            self, _("main_window.menu.restore"),
            _("main_window.status.filter_reset"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_rules()
            self.statusBar().showMessage(_("main_window.menu.restore"))
    
    def import_rename_pairs(self):
        """导入重命名配对"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, _("main_window.menu.import_pairs"), "",
            "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if not filepath:
            return
        
        try:
            imported_count = 0
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # 支持多种分隔符: Tab, |, ->
                    parts = None
                    for sep in ['\t', '|', '->', ',']:
                        if sep in line:
                            parts = line.split(sep, 1)
                            break
                    
                    if parts and len(parts) == 2:
                        old_name = parts[0].strip()
                        new_name = parts[1].strip()
                        
                        # 在表格中查找并设置新名称
                        for row in range(self.file_table.rowCount()):
                            item = self.file_table.item(row, 0)
                            if item and item.text() == old_name:
                                self.file_table.setItem(row, 1, QTableWidgetItem(new_name))
                                imported_count += 1
                                break
            
            QMessageBox.information(
                self, _("main_window.dialogs.undo_complete_title"),
                _("main_window.status.import_success_info").format(count=imported_count)
            )
        except Exception as e:
            QMessageBox.warning(self, _("main_window.dialogs.import_fail_title"), _("main_window.dialogs.read_error").format(error=e))

    # ========== 各模块重置函数 ==========
    
    def reset_regex_group(self):
        """重置正则模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.regex_pattern.clear()
        self.regex_replace.clear()
        self.regex_include_ext.setChecked(False)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.regex.title")))
    
    def reset_replace_group(self):
        """重置替换模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.replace_find.clear()
        self.replace_with.clear()
        self.replace_case_sensitive.setChecked(False)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.replace.title")))
    
    def reset_remove_group(self):
        """重置移除模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.remove_first_n.setValue(0)
        self.remove_last_n.setValue(0)
        self.remove_from.setValue(0)
        self.remove_to.setValue(0)
        self.remove_chars.clear()
        self.remove_words.clear()
        self.remove_crop_mode.setCurrentIndex(0)
        self.remove_crop_text.clear()
        self.remove_digits.setChecked(False)
        self.remove_chinese.setChecked(False)
        self.remove_trim.setChecked(False)
        self.remove_ds.setChecked(False)
        self.remove_accents.setChecked(False)
        self.remove_chars_check.setChecked(False)
        self.remove_symbols.setChecked(False)
        self.remove_lead_dots.setCurrentIndex(0)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.remove.title")))
    
    def reset_add_group(self):
        """重置添加模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.add_prefix.clear()
        self.add_suffix.clear()
        self.add_insert.clear()
        self.add_insert_pos.setValue(0)
        self.add_word_space.setChecked(False)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.add.title")))
    
    def reset_auto_date_group(self):
        """重置自动日期模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.auto_date_type.setCurrentIndex(0)
        self.auto_date_mode.setCurrentIndex(0)
        self.auto_date_format.setCurrentIndex(0)
        self.auto_date_sep.clear()
        self.auto_date_connect.setText("_")
        self.auto_date_custom.clear()
        self.auto_date_center.setChecked(False)
        self.auto_date_distance.setValue(0)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.auto_date.title")))
    
    def reset_numbering_group(self):
        """重置编号模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.numbering_mode.setCurrentIndex(0)
        self.numbering_at.setValue(0)
        self.numbering_start.setValue(1)
        self.numbering_increment.setValue(1)
        self.numbering_padding.setValue(0)
        self.numbering_separator.clear()
        self.numbering_break.setValue(0)
        self.numbering_folder.setChecked(False)
        self.numbering_type.setCurrentIndex(0)
        self.numbering_roman.setCurrentIndex(0)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.number.title")))
    
    def reset_name_group(self):
        """重置文件名模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.name_mode.setCurrentIndex(0)
        self.name_fixed.clear()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.file.title")))
    
    def reset_case_group(self):
        """重置大小写模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.case_mode.setCurrentIndex(0)
        self.case_digits.setChecked(False)
        self.case_symbols.setChecked(False)
        self.case_exception.clear()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.case.title")))
    
    def reset_move_copy_group(self):
        """重置移动/复制模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.move_copy_mode.setCurrentIndex(0)
        self.move_from.setValue(0)
        self.move_target.setCurrentIndex(0)
        self.move_count.setValue(0)
        self.move_separator.clear()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.move_copy.title")))
    
    def reset_folder_name_group(self):
        """重置文件夹名模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.folder_name_mode.setCurrentIndex(0)
        self.folder_name_sep.setText("_")
        self.folder_name_levels.setValue(1)
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.folder.title")))
    
    def reset_extension_group(self):
        """重置扩展名模块 - 只清除输入内容，不取消勾选"""
        self.save_current_input_state()
        self.ext_mode.setCurrentIndex(0)
        self.ext_fixed.clear()
        self.update_preview()
        self.statusBar().showMessage(_("main_window.status.module_cleared").format(module=_("main_window.rules.extension.title")))

    # ========== 恢复功能 ==========
    
    def save_current_input_state(self):
        """保存当前所有模块的输入状态"""
        self.last_rules_state = {
            # 正则模块
            'regex_checked': self.regex_check.isChecked(),
            'regex_pattern': self.regex_pattern.text(),
            'regex_replace': self.regex_replace.text(),
            'regex_include_ext': self.regex_include_ext.isChecked(),
            # 替换模块
            'replace_checked': self.replace_check.isChecked(),
            'replace_find': self.replace_find.text(),
            'replace_with': self.replace_with.text(),
            'replace_case_sensitive': self.replace_case_sensitive.isChecked(),
            # 移除模块
            'remove_checked': self.remove_check.isChecked(),
            'remove_first_n': self.remove_first_n.value(),
            'remove_last_n': self.remove_last_n.value(),
            'remove_from': self.remove_from.value(),
            'remove_to': self.remove_to.value(),
            'remove_chars': self.remove_chars.text(),
            'remove_words': self.remove_words.text(),
            'remove_digits': self.remove_digits.isChecked(),
            'remove_symbols': self.remove_symbols.isChecked(),
            # 添加模块
            'add_checked': self.add_check.isChecked(),
            'add_prefix': self.add_prefix.text(),
            'add_suffix': self.add_suffix.text(),
            'add_insert': self.add_insert.text(),
            'add_insert_pos': self.add_insert_pos.value(),
            'add_word_space': self.add_word_space.isChecked(),
            # 自动日期模块
            'auto_date_checked': self.auto_date_check.isChecked(),
            'auto_date_type': self.auto_date_type.currentIndex(),
            'auto_date_mode': self.auto_date_mode.currentIndex(),
            'auto_date_format': self.auto_date_format.currentText(),
            'auto_date_sep': self.auto_date_sep.text(),
            # 编号模块
            'numbering_checked': self.numbering_check.isChecked(),
            'numbering_mode': self.numbering_mode.currentIndex(),
            'numbering_at': self.numbering_at.value(),
            'numbering_start': self.numbering_start.value(),
            'numbering_increment': self.numbering_increment.value(),
            'numbering_padding': self.numbering_padding.value(),
            'numbering_separator': self.numbering_separator.text(),
            'numbering_break': self.numbering_break.value(),
            'numbering_folder': self.numbering_folder.isChecked(),
            'numbering_type': self.numbering_type.currentIndex(),
            'numbering_roman': self.numbering_roman.currentIndex(),
            # 文件名模块
            'name_checked': self.name_check.isChecked(),
            'name_mode': self.name_mode.currentIndex(),
            'name_fixed': self.name_fixed.text(),
            # 大小写模块
            'case_checked': self.case_check.isChecked(),
            'case_mode': self.case_mode.currentIndex(),
            'case_digits': self.case_digits.isChecked(),
            'case_symbols': self.case_symbols.isChecked(),
            'case_exception': self.case_exception.text(),
            # 移动/复制模块
            'move_checked': self.move_check.isChecked(),
            'move_copy_mode': self.move_copy_mode.currentIndex(),
            'move_from': self.move_from.value(),
            'move_target': self.move_target.currentIndex(),
            'move_count': self.move_count.value(),
            'move_separator': self.move_separator.text(),
            # 文件夹名模块
            'folder_name_checked': self.folder_name_check.isChecked(),
            'folder_name_mode': self.folder_name_mode.currentIndex(),
            'folder_name_sep': self.folder_name_sep.text(),
            'folder_name_levels': self.folder_name_levels.value(),
            # 扩展名模块
            'ext_checked': self.ext_check.isChecked(),
            'ext_mode': self.ext_mode.currentIndex(),
            'ext_fixed': self.ext_fixed.text(),
        }
    
    def restore_last_input(self):
        """恢复上一次的模块输入内容"""
        if self.last_rules_state is None:
            QMessageBox.information(self, _("main_window.dialogs.hint_title"), _("main_window.status.none"))
            return
        
        state = self.last_rules_state
        
        # 恢复正则模块
        self.regex_check.setChecked(state['regex_checked'])
        self.regex_pattern.setText(state['regex_pattern'])
        self.regex_replace.setText(state['regex_replace'])
        self.regex_include_ext.setChecked(state['regex_include_ext'])
        
        # 恢复替换模块
        self.replace_check.setChecked(state['replace_checked'])
        self.replace_find.setText(state['replace_find'])
        self.replace_with.setText(state['replace_with'])
        self.replace_case_sensitive.setChecked(state['replace_case_sensitive'])
        
        # 恢复移除模块
        self.remove_check.setChecked(state['remove_checked'])
        self.remove_first_n.setValue(state['remove_first_n'])
        self.remove_last_n.setValue(state['remove_last_n'])
        self.remove_from.setValue(state['remove_from'])
        self.remove_to.setValue(state['remove_to'])
        self.remove_chars.setText(state['remove_chars'])
        self.remove_words.setText(state['remove_words'])
        self.remove_digits.setChecked(state['remove_digits'])
        self.remove_symbols.setChecked(state['remove_symbols'])
        
        # 恢复添加模块
        self.add_check.setChecked(state['add_checked'])
        self.add_prefix.setText(state['add_prefix'])
        self.add_suffix.setText(state['add_suffix'])
        self.add_insert.setText(state['add_insert'])
        self.add_insert_pos.setValue(state['add_insert_pos'])
        self.add_word_space.setChecked(state['add_word_space'])
        
        # 恢复自动日期模块
        self.auto_date_check.setChecked(state['auto_date_checked'])
        self.auto_date_type.setCurrentIndex(state['auto_date_type'])
        self.auto_date_mode.setCurrentIndex(state['auto_date_mode'])
        self.auto_date_format.setCurrentText(state['auto_date_format'])
        self.auto_date_sep.setText(state['auto_date_sep'])
        
        # 恢复编号模块
        self.numbering_check.setChecked(state['numbering_checked'])
        self.numbering_mode.setCurrentIndex(state['numbering_mode'])
        self.numbering_at.setValue(state['numbering_at'])
        self.numbering_start.setValue(state['numbering_start'])
        self.numbering_increment.setValue(state['numbering_increment'])
        self.numbering_padding.setValue(state['numbering_padding'])
        self.numbering_separator.setText(state['numbering_separator'])
        self.numbering_break.setValue(state['numbering_break'])
        self.numbering_folder.setChecked(state['numbering_folder'])
        self.numbering_type.setCurrentIndex(state['numbering_type'])
        self.numbering_roman.setCurrentIndex(state['numbering_roman'])
        
        # 恢复文件名模块
        self.name_check.setChecked(state['name_checked'])
        self.name_mode.setCurrentIndex(state['name_mode'])
        self.name_fixed.setText(state['name_fixed'])
        
        # 恢复大小写模块
        self.case_check.setChecked(state['case_checked'])
        self.case_mode.setCurrentIndex(state['case_mode'])
        self.case_digits.setChecked(state['case_digits'])
        self.case_symbols.setChecked(state['case_symbols'])
        self.case_exception.setText(state['case_exception'])
        
        # 恢复移动/复制模块
        self.move_check.setChecked(state['move_checked'])
        self.move_copy_mode.setCurrentIndex(state['move_copy_mode'])
        self.move_from.setValue(state['move_from'])
        self.move_target.setCurrentIndex(state['move_target'])
        self.move_count.setValue(state['move_count'])
        self.move_separator.setText(state['move_separator'])
        
        # 恢复文件夹名模块
        self.folder_name_check.setChecked(state['folder_name_checked'])
        self.folder_name_mode.setCurrentIndex(state['folder_name_mode'])
        self.folder_name_sep.setText(state['folder_name_sep'])
        self.folder_name_levels.setValue(state['folder_name_levels'])
        
        # 恢复扩展名模块
        self.ext_check.setChecked(state['ext_checked'])
        self.ext_mode.setCurrentIndex(state['ext_mode'])
        self.ext_fixed.setText(state['ext_fixed'])
        
        self.update_preview()
        self.statusBar().showMessage(_("main_window.menu.restore"))

    # ========== 文件排序功能 ==========
    
    def on_header_clicked(self, column: int):
        """表头点击事件 - 实现排序"""
        # 可排序的列: 2=大小, 3=类型, 4=创建日期, 5=修改日期, 6=长度
        sortable_columns = {
            0: "name",      # 原文件名
            2: "size",      # 大小
            3: "type",      # 类型
            4: "created",   # 创建日期
            5: "modified",  # 修改日期
            6: "length"     # 长度
        }
        
        if column not in sortable_columns:
            return
        
        # 切换排序方向
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        
        # 执行排序
        sort_key = sortable_columns[column]
        self.sort_files_by_column(sort_key, self.sort_ascending)
        
        # 更新表头显示排序指示
        self.update_header_sort_indicator()
    
    def sort_files_by_column(self, sort_key: str, ascending: bool = True):
        """按指定列排序文件"""
        if not self.file_list:
            return
        
        # 显示排序状态
        self.statusBar().showMessage(_("main_window.status.sorting"))
        
        try:
            # 根据排序键获取排序函数
            if sort_key == "name":
                key_func = lambda x: os.path.basename(x).lower()
            elif sort_key == "size":
                key_func = lambda x: os.path.getsize(x) if os.path.exists(x) else 0
            elif sort_key == "type":
                key_func = lambda x: os.path.splitext(x)[1].lower()
            elif sort_key == "created":
                key_func = lambda x: os.path.getctime(x) if os.path.exists(x) else 0
            elif sort_key == "modified":
                key_func = lambda x: os.path.getmtime(x) if os.path.exists(x) else 0
            elif sort_key == "length":
                key_func = lambda x: len(os.path.basename(x))
            else:
                return
            
            # 排序文件列表
            self.file_list.sort(key=key_func, reverse=not ascending)
            
            # 重新填充表格
            self.refresh_file_table()
            
            # 显示排序结果
            direction = _("main_window.status.sort_asc") + " ↑" if ascending else _("main_window.status.sort_desc") + " ↓"
            sort_names = {
                "name": _("main_window.file_table.orig_name"),
                "size": _("main_window.file_table.size"),
                "type": _("main_window.file_table.type"),
                "created": _("main_window.file_table.create_date"),
                "modified": _("main_window.file_table.modify_date"),
                "length": _("main_window.file_table.length")
            }
            self.statusBar().showMessage(_("main_window.status.sorted_by").format(by=sort_names.get(sort_key, sort_key)) + " " + direction)
            
        except Exception as e:
            self.statusBar().showMessage(_("main_window.status.sort_fail").format(error=e))
    
    def refresh_file_table(self):
        """刷新文件表格（保持文件列表顺序）"""
        # 保存当前文件列表
        temp_list = self.file_list[:]
        
        # 清空表格
        self.file_table.setRowCount(0)
        self.file_list.clear()
        
        # 重新添加文件
        for filepath in temp_list:
            self.add_file_to_table(filepath)
        
        # 更新预览
        self.update_preview()
    
    def update_header_sort_indicator(self):
        """更新表头排序指示器"""
        headers = [
            _("main_window.file_table.orig_name"),
            _("main_window.file_table.new_name"),
            _("main_window.file_table.size"),
            _("main_window.file_table.type"),
            _("main_window.file_table.create_date"),
            _("main_window.file_table.modify_date"),
            _("main_window.file_table.length"),
            _("main_window.file_table.status")
        ]
        
        for i, header in enumerate(headers):
            item = self.file_table.horizontalHeaderItem(i)
            if item:
                if i == self.sort_column:
                    arrow = " ↑" if self.sort_ascending else " ↓"
                    item.setText(header + arrow)
                else:
                    item.setText(header)
