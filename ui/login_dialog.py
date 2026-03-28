"""
登录弹窗，负责展示登录状态并提供手动打开浏览器的兜底操作。
"""
from core.i18n import _
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from core.auth_manager import AuthManager


class LoginWorker(QThread):
    """后台启动登录流程和轮询。"""

    success = pyqtSignal(str, dict)
    error = pyqtSignal(str)
    cancel = pyqtSignal()

    def __init__(self, auth_manager: AuthManager):
        super().__init__()
        self.auth_manager = auth_manager

    def run(self):
        self.auth_manager.start_login_flow(
            on_success=self._on_success,
            on_error=self._on_error,
            on_cancel=self._on_cancel,
        )

    def _on_success(self, token: str, user_info: dict):
        self.success.emit(token, user_info)

    def _on_error(self, error_message: str):
        self.error.emit(error_message)

    def _on_cancel(self):
        self.cancel.emit()

    def stop(self):
        self.auth_manager.cancel_login()


class LoginDialog(QDialog):
    """登录对话框。"""

    login_success = pyqtSignal(str, dict)

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(_("login_dialog.title"))
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(_("login_dialog.account_login"))
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        info_label = QLabel(_("login_dialog.info"))
        info_label.setStyleSheet("color: #666; line-height: 1.5;")
        layout.addWidget(info_label)

        self.open_browser_btn = QPushButton(_("login_dialog.click_to_open"))
        self.open_browser_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            """
        )
        self.open_browser_btn.clicked.connect(self._manual_open_browser)
        layout.addWidget(self.open_browser_btn)

        self.copy_url_btn = QPushButton(
            _("login_dialog.copy_url", "Copy Login Link")
        )
        self.copy_url_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f5f5f5;
                color: #333;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            """
        )
        self.copy_url_btn.clicked.connect(self._copy_login_url)
        layout.addWidget(self.copy_url_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                height: 8px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            """
        )
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel(_("login_dialog.starting"))
        self.status_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton(_("login_dialog.cancel"))
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.clicked.connect(self.cancel_login)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setStyleSheet("QDialog { background-color: #fff; }")

    def _manual_open_browser(self):
        url = self.auth_manager.get_last_login_url()
        if not url:
            return

        opened, error_message = self.auth_manager.open_external_url(url)
        if opened:
            self.status_label.setText(_("login_dialog.waiting"))
            return

        self._copy_login_url()
        if error_message:
            self.status_label.setText(
                _("login_dialog.error").format(error=error_message)
            )

    def start_login(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(1000)

        self.worker = LoginWorker(self.auth_manager)
        self.worker.success.connect(self._on_login_success)
        self.worker.error.connect(self._on_login_error)
        self.worker.cancel.connect(self._on_login_cancel)
        self.worker.start()
        self.status_label.setText(_("login_dialog.waiting"))

    def _on_login_success(self, token: str, user_info: dict):
        self.status_label.setText(_("login_dialog.success"))
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        QTimer.singleShot(1000, lambda: self._close_dialog(True, token, user_info))

    def _on_login_error(self, error_message: str):
        if error_message.startswith("AUTO_OPEN_FAILED:"):
            if hasattr(self, "open_browser_btn"):
                self.open_browser_btn.show()
            self._copy_login_url(silent=True)
            self.status_label.setText(_("login_dialog.auto_open_failed"))
            return

        self.status_label.setText(_("login_dialog.error").format(error=error_message))
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.cancel_btn.setText(_("login_dialog.close"))

    def _on_login_cancel(self):
        self.status_label.setText(_("login_dialog.cancelled"))
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.cancel_btn.setText(_("login_dialog.close"))

    def cancel_login(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(1000)
        self.reject()

    def _copy_login_url(self, silent: bool = False):
        url = self.auth_manager.get_last_login_url()
        if url:
            QGuiApplication.clipboard().setText(url)
            if not silent:
                QMessageBox.information(
                    self,
                    _("login_dialog.success"),
                    _(
                        "login_dialog.url_copied",
                        "Login URL copied! Please paste it in your browser.",
                    ),
                )

    def _close_dialog(
        self,
        success: bool,
        token: str | None = None,
        user_info: dict | None = None,
    ):
        if success:
            self.login_success.emit(token or "", user_info or {})
            self.accept()
        else:
            self.reject()
