"""
认证集成模块 - 将登录功能集成到主窗口
"""
from core.i18n import _, i18n
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QMenu, QMessageBox, QToolBar, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
import os
from core.auth_manager import AuthManager
from core.adv_manager import AdvManager
from core.auth_api import AuthAPI
from .login_dialog import LoginDialog
from .user_panel import UserPanel
from .adv_widget import AdvWidget


class UserButton(QPushButton):
    """用户按钮 - 显示登录/用户信息"""
    
    # 信号
    login_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    
    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.user_panel = None
        self.panel_popup = None
        
        self.setMinimumWidth(100)
        self.setMinimumHeight(32)
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 9pt;
                color: #333;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        
        self.clicked.connect(self._on_button_clicked)
        self.update_ui()
    
    def update_ui(self):
        """更新按钮UI"""
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            if user_info:
                nickname = user_info.get("nickname", _("auth_integration.user"))
                self.setText(f"{nickname}")
            else:
                self.setText(_("auth_integration.logged_in"))
        else:
            self.setText(_("auth_integration.login"))
    def _on_button_clicked(self):
        """按钮点击事件"""
        if self.auth_manager.is_logged_in():
            self._show_user_panel()
        else:
            self.login_clicked.emit()
    
    def _show_user_panel(self):
        """显示用户信息面板"""
        if not self.user_panel:
            self.user_panel = UserPanel()
            self.user_panel.logout_clicked.connect(self._on_logout)
            self.user_panel.refresh_btn.clicked.connect(self._on_refresh_user_info)
        
        # 更新用户信息
        user_info = self.auth_manager.get_user_info()
        self.user_panel.set_user_info(user_info)
        
        # 创建弹出窗口
        if not self.panel_popup:
            self.panel_popup = QWidget()
            self.panel_popup.setWindowFlags(
                Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
            )
            self.panel_popup.setMinimumSize(300, 350)
            layout = QHBoxLayout(self.panel_popup)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.user_panel)
        
        # 计算弹出位置
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self.panel_popup.move(pos.x() - self.panel_popup.width() + self.width(), pos.y())
        self.panel_popup.show()
    
    def _on_logout(self):
        """退出登录"""
        reply = QMessageBox.question(
            self,
            _("auth_integration.confirm_logout"),
            _("auth_integration.confirm_logout_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.auth_manager.logout():
                QMessageBox.information(self, _("auth_integration.logout_success"), _("auth_integration.logout_success"))
                self.update_ui()
                self.logout_clicked.emit()
                if self.panel_popup:
                    self.panel_popup.hide()
            else:
                QMessageBox.warning(self, _("auth_integration.error"), _("auth_integration.logout_fail"))
    
    def _on_refresh_user_info(self):
        """刷新用户信息"""
        if self.auth_manager.refresh_user_info():
            user_info = self.auth_manager.get_user_info()
            self.user_panel.set_user_info(user_info)
            QMessageBox.information(self, _("auth_integration.logout_success"), _("auth_integration.refresh_success"))
        else:
            QMessageBox.warning(self, _("auth_integration.error"), _("auth_integration.refresh_fail"))


class AuthIntegration:
    """认证集成 - 将登录功能集成到主窗口"""
    
    def __init__(self, main_window):
        """
        初始化认证集成
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
        self.auth_manager = AuthManager()
        self.adv_manager = AdvManager()
        self.user_button = None
        self.adv_widget = None
        self.login_dialog = None
    
    def setup_ui(self):
        """设置UI - 保留用于兼容性"""
        pass
    
    def setup_ui_in_action_bar(self, action_bar: QWidget, layout: QHBoxLayout):
        """在操作栏中设置UI - 添加登录按钮和广告到操作栏右侧"""
        # 语言显示映射
        lang_names = {
            "ar": "Arabic (العربية)",
            "bn": "Bengali (বাংলা)",
            "de": "German (Deutsch)",
            "en": "English",
            "es": "Spanish (Español)",
            "fa": "Farsi (فارسی)",
            "fr": "French (Français)",
            "he": "Hebrew (עברית)",
            "hi": "Hindi (हिन्दी)",
            "id": "Indonesian (Bahasa Indonesia)",
            "it": "Italian (Italiano)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
            "ms": "Malay (Bahasa Melayu)",
            "nl": "Dutch (Nederlands)",
            "pl": "Polish (Polski)",
            "pt": "Portuguese (Português)",
            "pt_BR": "Brazilian Portuguese",
            "ru": "Russian (Русский)",
            "sw": "Swahili (Kiswahili)",
            "ta": "Tamil (தமிழ்)",
            "th": "Thai (ไทย)",
            "tl": "Tagalog",
            "tr": "Turkish (Türkçe)",
            "uk": "Ukrainian (Українська)",
            "ur": "Urdu (اردو)",
            "vi": "Vietnamese (Tiếng Việt)",
            "zh_CN": "简体中文",
            "zh_TW": "繁體中文"
        }

        # 创建语言切换下拉框
        lang_combo = QComboBox()
        lang_combo.setMinimumWidth(120)
        lang_combo.setMinimumHeight(32)
        lang_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 2px 10px;
                font-size: 9pt;
                color: #333;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666;
                margin-right: 8px;
            }
        """)
        
        # 添加可用语言
        available_locales = i18n.get_available_locales()
        current_locale = i18n.get_current_locale()
        
        # 在添加项目前先断开信号，防止初始化时触发刷新导致崩溃
        lang_combo.blockSignals(True)
        for code in available_locales:
            name = lang_names.get(code, code)
            lang_combo.addItem(name, code)
            if code == current_locale:
                lang_combo.setCurrentIndex(lang_combo.count() - 1)
        lang_combo.blockSignals(False)
        
        # 绑定切换事件
        def on_lang_changed(index):
            code = lang_combo.itemData(index)
            if i18n.set_locale(code):
                # 实时刷新主窗口UI
                self.main_window.retranslate_ui()
                
                # 更新自身按钮文本
                self.user_button.update_ui()
                contact_btn.setText(_("auth_integration.contact_us"))
                
                # 状态栏提示
                self.main_window.statusBar().showMessage(_("main_window.status_ready"), 3000)
        
        lang_combo.currentIndexChanged.connect(on_lang_changed)

        # 创建用户按钮
        self.user_button = UserButton(self.auth_manager, self.main_window)
        self.user_button.login_clicked.connect(self._on_login_clicked)
        self.user_button.logout_clicked.connect(self._on_logout_clicked)
        
        # 创建广告组件
        self.adv_widget = AdvWidget(
            open_url_callback=self.auth_manager.open_external_url
        )
        
        # 创建"软件定制，联系我们"按钮
        contact_btn = QPushButton(_("auth_integration.contact_us"))
        contact_btn.setMinimumWidth(150)
        contact_btn.setMinimumHeight(32)
        contact_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #3B82F6, stop:1 #06B6D4);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 12px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #2563EB, stop:1 #0891B2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #1D4ED8, stop:1 #0E7490);
            }
        """)
        contact_btn.clicked.connect(self._on_contact_clicked)
        
        # 添加弹簧，使所有按钮右对齐
        layout.addStretch()
        
        # 添加语言切换下拉框 (放在定制按钮旁边)
        layout.addWidget(lang_combo)
        
        # 添加"联系我们"按钮
        layout.addWidget(contact_btn)
        
        # 添加广告组件
        layout.addWidget(self.adv_widget)
        
        # 添加用户按钮到操作栏右侧
        layout.addWidget(self.user_button)
        
        # 加载广告
        self._load_adv()
    
    def _on_login_clicked(self):
        """登录按钮点击事件"""
        if not self.login_dialog:
            self.login_dialog = LoginDialog(self.auth_manager, self.main_window)
            self.login_dialog.login_success.connect(self._on_login_success)
        
        self.login_dialog.start_login()
        self.login_dialog.exec()
    
    def _on_login_success(self, token: str, user_info: dict):
        """登录成功"""
        self.user_button.update_ui()
        QMessageBox.information(
            self.main_window,
            _("auth_integration.login_success_title"),
            _("auth_integration.welcome_msg").format(name=user_info.get('nickname', _("auth_integration.user")))
        )
    
    def _on_logout_clicked(self):
        """退出登录"""
        self.user_button.update_ui()
    
    def _load_adv(self):
        """加载广告"""
        try:
            adv_data = self.adv_manager.get_adv("adv_position_01")
            if adv_data and self.adv_widget:
                self.adv_widget.set_adv(adv_data)
        except Exception as e:
            print(f"加载广告失败: {e}")
    
    def _on_contact_clicked(self):
        """联系我们按钮点击事件"""
        try:
            # 获取需求定制页面链接
            custom_url = AuthAPI.get_custom_url()
            if custom_url:
                opened, _ = self.auth_manager.open_external_url(custom_url)
                if not opened:
                    QMessageBox.warning(
                        self.main_window,
                        _("auth_integration.error"),
                        _("auth_integration.custom_software_error")
                    )
            else:
                # 如果获取链接失败，显示默认联系信息
                QMessageBox.information(
                    self.main_window,
                    _("auth_integration.custom_software"),
                    _("auth_integration.custom_software_info")
                )
        except Exception as e:
            print(f"打开需求定制页面失败: {e}")
            QMessageBox.warning(
                self.main_window,
                _("auth_integration.error"),
                _("auth_integration.custom_software_error")
            )
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.auth_manager.is_logged_in()
    
    def get_token(self) -> str:
        """获取Token"""
        return self.auth_manager.get_token()
    
    def get_user_info(self) -> dict:
        """获取用户信息"""
        return self.auth_manager.get_user_info()
