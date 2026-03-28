"""
日志模块 - 鲲穹AI批量重命名操作日志系统
"""
from core.i18n import _
import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Optional, List, Dict


class RenameOperation:
    """重命名操作记录"""
    def __init__(self, old_path: str, new_path: str, success: bool, message: str = ""):
        self.timestamp = datetime.now()
        self.old_path = old_path
        self.new_path = new_path
        self.old_name = os.path.basename(old_path)
        self.new_name = os.path.basename(new_path) if new_path else ""
        self.success = success
        self.message = message
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "old_path": self.old_path,
            "new_path": self.new_path,
            "old_name": self.old_name,
            "new_name": self.new_name,
            "success": self.success,
            "message": self.message
        }
    
    def to_log_line(self) -> str:
        status = _("main_window.status.rename_success") if self.success else _("main_window.status.rename_fail").format(error="")
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {status} | {self.old_name} → {self.new_name} | {self.message}"


class RenameToolLogger:
    """鲲穹AI批量重命名日志记录器"""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        
        os.makedirs(log_dir, exist_ok=True)
        
        self.log_dir = log_dir
        self.error_log_file = os.path.join(log_dir, f"error_{datetime.now().strftime('%Y%m%d')}.log")
        self.operation_log_file = os.path.join(log_dir, f"operations_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 操作历史记录（内存中）
        self.operation_history: List[RenameOperation] = []
        
        # 配置错误日志记录器
        self.logger = logging.getLogger("BulkRenameTool")
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(self.error_log_file, encoding='utf-8')
        file_handler.setLevel(logging.ERROR)
        
        # 自定义格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
    
    def log_rename_operation(self, old_path: str, new_path: str, success: bool, message: str = ""):
        """记录重命名操作"""
        operation = RenameOperation(old_path, new_path, success, message)
        self.operation_history.append(operation)
        
        # 同时写入文件
        try:
            with open(self.operation_log_file, 'a', encoding='utf-8') as f:
                f.write(operation.to_log_line() + "\n")
        except Exception:
            pass
        
        return operation
    
    def log_batch_start(self, file_count: int):
        """记录批量操作开始"""
        try:
            with open(self.operation_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {_('main_window.dialogs.confirm_rename_title')} - 共 {file_count} 个文件\n")
                f.write(f"{'='*60}\n")
        except Exception:
            pass
    
    def log_batch_end(self, success_count: int, fail_count: int):
        """记录批量操作结束"""
        try:
            with open(self.operation_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{'='*60}\n")
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {_('main_window.status.rename_complete').format(success=success_count, error=fail_count)}\n")
                f.write(f"{'='*60}\n\n")
        except Exception:
            pass
    
    def get_operation_history(self) -> List[RenameOperation]:
        """获取操作历史"""
        return self.operation_history
    
    def clear_history(self):
        """清除内存中的历史记录"""
        self.operation_history.clear()
    
    def get_log_content(self) -> str:
        """获取日志文件内容"""
        content = ""
        if os.path.exists(self.operation_log_file):
            try:
                with open(self.operation_log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                content = _("main_window.menu.log") + " " + _("logger.fail")
        else:
            content = _("logger.no_log")
        return content
    
    def export_log(self, export_path: str) -> bool:
        """导出日志到指定路径"""
        try:
            content = self.get_log_content()
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def log_error(self, exception: Exception, context: str = "", script_file: str = None):
        """记录错误日志"""
        if script_file is None:
            script_file = self._get_caller_file()
        
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        
        log_entry = f"""
================================================================================
{_("logger.source_script")} {script_file}
{_("logger.error_type")} {error_type}
{_("logger.error_message")} {error_message}
{_("logger.context")} {context if context else _("logger.none")}
{_("logger.stack_trace")}
{stack_trace}
================================================================================
"""
        self.logger.error(log_entry)
        return self.error_log_file
    
    def _get_caller_file(self) -> str:
        """获取调用者的文件名"""
        try:
            frame = sys._getframe(2)
            return frame.f_code.co_filename
        except:
            return "unknown"
    
    def get_log_file_path(self) -> str:
        """获取日志文件路径"""
        return self.operation_log_file


# 全局日志实例
_logger_instance: Optional[RenameToolLogger] = None


def get_logger() -> RenameToolLogger:
    """获取全局日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = RenameToolLogger()
    return _logger_instance


def log_error(exception: Exception, context: str = "", script_file: str = None) -> str:
    """便捷函数：记录错误"""
    return get_logger().log_error(exception, context, script_file)


def log_rename(old_path: str, new_path: str, success: bool, message: str = ""):
    """便捷函数：记录重命名操作"""
    return get_logger().log_rename_operation(old_path, new_path, success, message)
