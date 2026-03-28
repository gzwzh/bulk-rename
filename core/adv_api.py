"""
广告API模块 - 处理与服务器的广告通信
"""
import requests
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode


class AdvAPI:
    """广告API客户端"""
    
    BASE_URL = "https://api-web.kunqiongai.com"
    
    # API端点
    ENDPOINTS = {
        "get_adv": "/soft_desktop/get_adv",
    }
    
    # 超时设置
    TIMEOUT = 10
    
    @staticmethod
    def get_adv(soft_number: str, adv_position: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取广告
        
        Args:
            soft_number: 软件编号
            adv_position: 广告位置（如 adv_position_01）
            
        Returns:
            广告列表或None
        """
        try:
            url = AdvAPI.BASE_URL + AdvAPI.ENDPOINTS["get_adv"]
            payload = {
                "soft_number": soft_number,
                "adv_position": adv_position,
            }
            
            response = requests.post(
                url,
                data=urlencode(payload),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=AdvAPI.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 1 and "data" in data:
                return data["data"]
            return None
        except Exception as e:
            print(f"获取广告失败: {e}")
            return None
