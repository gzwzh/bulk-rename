"""
广告管理器 - 管理广告的加载和显示
"""
from typing import Optional, List, Dict, Any
from .adv_api import AdvAPI


class AdvManager:
    """广告管理器"""
    
    # 默认软件编号（需要根据实际情况修改）
    DEFAULT_SOFT_NUMBER = "10002"
    
    def __init__(self, soft_number: str = DEFAULT_SOFT_NUMBER):
        """
        初始化广告管理器
        
        Args:
            soft_number: 软件编号
        """
        self.soft_number = soft_number
    
    def get_adv(self, adv_position: str) -> Optional[Dict[str, Any]]:
        """
        获取广告
        
        Args:
            adv_position: 广告位置（如 adv_position_01）
            
        Returns:
            广告数据或None
        """
        adv_list = AdvAPI.get_adv(self.soft_number, adv_position)
        
        if adv_list and len(adv_list) > 0:
            return adv_list[0]  # 返回第一个广告
        
        return None
    
    def get_adv_list(self, adv_position: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取广告列表
        
        Args:
            adv_position: 广告位置（如 adv_position_01）
            
        Returns:
            广告列表或None
        """
        return AdvAPI.get_adv(self.soft_number, adv_position)
