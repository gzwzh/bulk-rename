"""
广告组件 - 显示广告
"""
from core.i18n import _
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import requests
from typing import Callable, Optional, Dict, Any


class AdvLoader(QThread):
    """广告加载线程"""
    
    loaded = pyqtSignal(dict)  # 广告数据
    error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, adv_data: Dict[str, Any]):
        super().__init__()
        self.adv_data = adv_data
    
    def run(self):
        """加载广告"""
        try:
            adv_url = self.adv_data.get("adv_url")
            if not adv_url:
                self.error.emit(_("adv_widget.error_empty"))
                return
            
            # 下载广告图片
            response = requests.get(adv_url, timeout=10)
            if response.status_code == 200:
                self.adv_data["image_data"] = response.content
                self.loaded.emit(self.adv_data)
            else:
                self.error.emit(_("adv_widget.error_download").format(code=response.status_code))
        except Exception as e:
            self.error.emit(_("adv_widget.error_load").format(error=str(e)))


class AdvWidget(QWidget):
    """广告组件"""
    
    # 广告最大宽度和高度（适应操作栏）
    MAX_WIDTH = 120
    MAX_HEIGHT = 30
    
    def __init__(self, parent=None, open_url_callback: Optional[Callable[[str], tuple[bool, Optional[str]]]] = None):
        super().__init__(parent)
        self.adv_data = None
        self.loader = None
        self.open_url_callback = open_url_callback
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 广告标签
        self.adv_label = QLabel()
        self.adv_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.adv_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
        
        # 设置固定大小
        self.adv_label.setFixedSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        
        # 显示占位符
        self.adv_label.setText(_("adv_widget.placeholder"))
        placeholder_font = QFont()
        placeholder_font.setPointSize(8)
        self.adv_label.setFont(placeholder_font)
        self.adv_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: #999;
            }
        """)
        
        layout.addWidget(self.adv_label)
    
    def set_adv(self, adv_data: Dict[str, Any]):
        """
        设置广告
        
        Args:
            adv_data: 广告数据字典
        """
        if not adv_data:
            # 如果没有广告数据，显示占位符
            self.adv_label.setText(_("adv_widget.placeholder"))
            return
        
        self.adv_data = adv_data
        
        # 启动加载线程
        self.loader = AdvLoader(adv_data)
        self.loader.loaded.connect(self._on_adv_loaded)
        self.loader.error.connect(self._on_adv_error)
        self.loader.start()
    
    def _on_adv_loaded(self, adv_data: Dict[str, Any]):
        """广告加载完成"""
        try:
            image_data = adv_data.get("image_data")
            if image_data:
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                
                # 缩放图片到最大尺寸，保持宽高比
                scaled_pixmap = pixmap.scaledToWidth(
                    self.MAX_WIDTH,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # 如果高度超过最大高度，再按高度缩放
                if scaled_pixmap.height() > self.MAX_HEIGHT:
                    scaled_pixmap = pixmap.scaledToHeight(
                        self.MAX_HEIGHT,
                        Qt.TransformationMode.SmoothTransformation
                    )
                
                # 创建圆角图片
                rounded_pixmap = self._create_rounded_pixmap(scaled_pixmap, 5)
                
                self.adv_label.setPixmap(rounded_pixmap)
                
                # 连接点击事件
                self.adv_label.mousePressEvent = self._on_adv_clicked
        except Exception as e:
            print(_("adv_widget.error_display").format(error=str(e)))
    
    def _create_rounded_pixmap(self, pixmap: QPixmap, radius: int) -> QPixmap:
        """
        创建圆角图片
        
        Args:
            pixmap: 原始图片
            radius: 圆角半径
            
        Returns:
            圆角图片
        """
        from PyQt6.QtGui import QPainter, QBrush, QPainterPath
        from PyQt6.QtCore import QRect
        
        # 创建新的透明图片
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)
        
        # 绘制圆角
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
        
        # 设置裁剪路径
        painter.setClipPath(path)
        
        # 绘制图片
        painter.drawPixmap(0, 0, pixmap)
        
        painter.end()
        
        return rounded
    
    def _on_adv_error(self, error_message: str):
        """广告加载错误"""
        print(error_message)
        # 显示占位符
        self.adv_label.setText(_("adv_widget.placeholder"))
        self.adv_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: #999;
            }
        """)
    
    def _on_adv_clicked(self, event):
        """广告被点击"""
        if self.adv_data:
            target_url = self.adv_data.get("target_url")
            if target_url:
                if self.open_url_callback:
                    self.open_url_callback(target_url)
    
    def clear(self):
        """清除广告"""
        self.adv_label.clear()
        self.adv_data = None
