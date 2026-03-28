"""
用户信息面板 - 显示用户信息和登出选项
"""
from core.i18n import _
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtNetwork import QNetworkAccessManager
from PyQt6.QtCore import QEventLoop, QTimer
import requests
from typing import Optional, Dict, Any


class UserPanel(QWidget):
    """用户信息面板"""
    
    # 信号
    logout_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_info = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet("""
            QWidget {
                background-color: #fff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fff;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #f5f5f5;
            }
            QScrollBar::handle:vertical {
                background-color: #ccc;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #999;
            }
        """)
        
        # 内容容器
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(12)
        
        # 用户信息容器
        self.info_container = QFrame()
        self.info_container.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(10)
        
        # 头像和昵称
        avatar_name_layout = QHBoxLayout()
        avatar_name_layout.setSpacing(12)
        
        # 头像
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(60, 60)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 30px;
                background-color: #e0e0e0;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_name_layout.addWidget(self.avatar_label)
        
        # 昵称和账户信息
        info_text_layout = QVBoxLayout()
        info_text_layout.setSpacing(4)
        
        self.nickname_label = QLabel(_("user_panel.not_logged_in"))
        nickname_font = QFont()
        nickname_font.setPointSize(11)
        nickname_font.setBold(True)
        self.nickname_label.setFont(nickname_font)
        self.nickname_label.setStyleSheet("color: #333;")
        info_text_layout.addWidget(self.nickname_label)
        
        self.account_label = QLabel(_("user_panel.account"))
        account_font = QFont()
        account_font.setPointSize(9)
        self.account_label.setFont(account_font)
        self.account_label.setStyleSheet("color: #999;")
        info_text_layout.addWidget(self.account_label)
        
        info_text_layout.addStretch()
        avatar_name_layout.addLayout(info_text_layout)
        
        info_layout.addLayout(avatar_name_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #e0e0e0;")
        info_layout.addWidget(separator)
        
        # 账户信息详情
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)
        
        # 登录状态
        status_layout = QHBoxLayout()
        status_label = QLabel(_("user_panel.login_status"))
        status_label.setStyleSheet("color: #666; font-weight: bold;")
        self.status_value = QLabel(_("user_panel.logged_in"))
        self.status_value.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_value)
        status_layout.addStretch()
        details_layout.addLayout(status_layout)
        
        info_layout.addLayout(details_layout)
        
        content_layout.addWidget(self.info_container)
        
        # 操作按钮
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        
        # 刷新信息按钮
        self.refresh_btn = QPushButton(_("user_panel.refresh_info"))
        self.refresh_btn.setMinimumHeight(32)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        button_layout.addWidget(self.refresh_btn)
        
        # 退出登录按钮
        self.logout_btn = QPushButton(_("user_panel.logout"))
        self.logout_btn.setMinimumHeight(32)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #ba0000;
            }
        """)
        self.logout_btn.clicked.connect(self.logout_clicked.emit)
        button_layout.addWidget(self.logout_btn)
        
        content_layout.addLayout(button_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def set_user_info(self, user_info: Optional[Dict[str, Any]]):
        """
        设置用户信息
        
        Args:
            user_info: 用户信息字典，包含 avatar 和 nickname
        """
        self.user_info = user_info
        
        if not user_info:
            self.nickname_label.setText(_("user_panel.not_logged_in"))
            self.account_label.setText(_("user_panel.account"))
            self.avatar_label.setPixmap(QPixmap())
            return
        
        # 设置昵称
        nickname = user_info.get("nickname", _("user_panel.unknown_user"))
        self.nickname_label.setText(nickname)
        self.account_label.setText(_("user_panel.account_with_name").format(name=nickname))
        
        # 加载头像
        avatar_url = user_info.get("avatar")
        if avatar_url:
            self._load_avatar(avatar_url)
    
    def _load_avatar(self, url: str):
        """
        加载头像
        
        Args:
            url: 头像URL
        """
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                # 缩放到60x60
                scaled_pixmap = pixmap.scaledToWidth(
                    60,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 创建圆形头像
                circular_pixmap = QPixmap(60, 60)
                circular_pixmap.fill(Qt.GlobalColor.transparent)
                
                from PyQt6.QtGui import QPainter, QBrush
                painter = QPainter(circular_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QBrush(scaled_pixmap))
                painter.drawEllipse(0, 0, 60, 60)
                painter.end()
                
                self.avatar_label.setPixmap(circular_pixmap)
        except Exception as e:
            print(f"加载头像失败: {e}")
    
    def clear(self):
        """清除用户信息"""
        self.set_user_info(None)
