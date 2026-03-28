from core.i18n import _
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextBrowser, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class UpdateDialog(QDialog):
    def __init__(self, parent, version, update_log, download_url, on_confirm):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.download_url = download_url
        self.setWindowTitle(_("update_dialog.title"))
        self.setFixedSize(500, 400)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel#TitleLabel {
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
            }
            QLabel#VersionLabel {
                font-family: "Microsoft YaHei";
                font-size: 14px;
                color: #666666;
                margin-bottom: 5px;
            }
            QTextBrowser {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f9f9f9;
                padding: 10px;
                font-family: "Microsoft YaHei";
                font-size: 13px;
                color: #333333;
            }
            QPushButton {
                font-family: "Microsoft YaHei";
                font-size: 14px;
                border-radius: 4px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton#ConfirmButton {
                background-color: #007bff;
                color: white;
                border: none;
            }
            QPushButton#ConfirmButton:hover {
                background-color: #0069d9;
            }
            QPushButton#CancelButton {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #dcdcdc;
            }
            QPushButton#CancelButton:hover {
                background-color: #e6e6e6;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题区域
        title_label = QLabel(_("update_dialog.title"))
        title_label.setObjectName("TitleLabel")
        layout.addWidget(title_label)

        # 版本信息
        version_label = QLabel(_("update_dialog.latest_version").format(version=version))
        version_label.setObjectName("VersionLabel")
        layout.addWidget(version_label)

        # 更新日志
        log_label = QLabel(_("update_dialog.update_content"))
        log_label.setStyleSheet("font-weight: bold; color: #333333;")
        layout.addWidget(log_label)

        self.log_browser = QTextBrowser()
        self.log_browser.setHtml(update_log.replace('\n', '<br>'))
        layout.addWidget(self.log_browser)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton(_("update_dialog.remind_later"))
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton(_("update_dialog.update_now"))
        self.confirm_btn.setObjectName("ConfirmButton")
        self.confirm_btn.clicked.connect(self.accept_update)
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)

    def accept_update(self):
        self.accept()
        if self.on_confirm:
            self.on_confirm()
