"""
批量重命名 - 主程序入口
功能对标 Bulk Rename Utility
"""
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir)) # 添加父目录 (pkgs/.. -> root) 以支持 pynsist 结构
sys.path.insert(0, current_dir)

from core.i18n import _
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    try:
        # 启用高DPI支持
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # 确定基础路径
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 设置应用图标
        icon_names = ['inco.ico', '批量重命名工具.png', '文件批量重命名.png', '鲲穹01.ico']
        icon_path = None
        
        # 优先查找 sys._MEIPASS (PyInstaller 临时目录)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
             for name in icon_names:
                temp_path = os.path.join(sys._MEIPASS, name)
                if os.path.exists(temp_path):
                    icon_path = temp_path
                    break
        
        # 如果没找到，查找 base_path (执行目录)
        if not icon_path:
            # 检查 base_path 和 parent_path (应对 pynsist 将 main.py 放在 pkgs 子目录的情况)
            search_paths = [base_path, os.path.dirname(base_path)]
            for path in search_paths:
                if icon_path: break
                for name in icon_names:
                    temp_path = os.path.join(path, name)
                    if os.path.exists(temp_path):
                        icon_path = temp_path
                        break
                    
        if icon_path:
            app.setWindowIcon(QIcon(icon_path))
        
        # 设置应用样式
        app.setStyleSheet("""
            QMainWindow, QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 9pt;
                color: #1a1a1a;
            }
            QGroupBox {
                font-weight: bold;
                color: #000000;
                border: 1px solid #999;
                border-radius: 3px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #000000;
            }
            QLabel {
                color: #1a1a1a;
            }
            QCheckBox {
                color: #1a1a1a;
            }
            QTreeView, QTableView, QListView {
                border: 1px solid #999;
                alternate-background-color: #f5f5f5;
                color: #1a1a1a;
            }
            QPushButton {
                padding: 4px 12px;
                min-height: 20px;
                color: #1a1a1a;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 2px 4px;
                min-height: 18px;
                color: #1a1a1a;
            }
            QMenuBar {
                color: #1a1a1a;
            }
            QMenu {
                color: #1a1a1a;
            }
            QStatusBar {
                color: #1a1a1a;
            }
        """)
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        print(_("main.error").format(error=str(e)))
        traceback.print_exc()
        input(_("main.exit_prompt"))


if __name__ == '__main__':
    main()
