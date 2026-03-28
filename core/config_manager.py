"""
配置管理器 - 保存和加载重命名规则
"""
import json
import os
from dataclasses import asdict
from typing import Optional
from .rename_engine import RenameRules, CaseMode


class ConfigManager:
    """配置管理器"""
    
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".bulk_rename_tool")
    
    def __init__(self):
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
    
    def save_rules(self, rules: RenameRules, filepath: str) -> bool:
        """保存规则到文件"""
        try:
            data = asdict(rules)
            # 转换枚举为值
            data['case_mode'] = rules.case_mode.value
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_rules(self, filepath: str) -> Optional[RenameRules]:
        """从文件加载规则"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换枚举
            if 'case_mode' in data:
                data['case_mode'] = CaseMode(data['case_mode'])
            
            return RenameRules(**data)
        except Exception as e:
            print(f"加载配置失败: {e}")
            return None
    
    def get_recent_configs(self) -> list:
        """获取最近使用的配置列表"""
        recent_file = os.path.join(self.CONFIG_DIR, "recent.json")
        try:
            if os.path.exists(recent_file):
                with open(recent_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def add_recent_config(self, filepath: str):
        """添加到最近使用列表"""
        recent = self.get_recent_configs()
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        recent = recent[:10]  # 保留最近10个
        
        recent_file = os.path.join(self.CONFIG_DIR, "recent.json")
        try:
            with open(recent_file, 'w', encoding='utf-8') as f:
                json.dump(recent, f)
        except:
            pass
