import requests
import logging
from typing import Optional
from core.version import SOFTWARE_ID

logger = logging.getLogger("BulkRenameTool")

class FeedbackAPI:
    BASE_URL = "https://api-web.kunqiongai.com"
    ENDPOINTS = {
        "get_feedback_url": "/soft_desktop/get_feedback_url"
    }
    TIMEOUT = 10

    @staticmethod
    def get_feedback_url() -> Optional[str]:
        """
        获取问题反馈页面的URL
        """
        try:
            url = FeedbackAPI.BASE_URL + FeedbackAPI.ENDPOINTS["get_feedback_url"]
            # 文档说明请求方式为 POST，Content-Type 为 none
            response = requests.post(url, timeout=FeedbackAPI.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 1 and "data" in data:
                base_url = data["data"].get("url")
                if base_url:
                    # 拼接软件编号
                    return f"{base_url}{SOFTWARE_ID}"
            return None
        except Exception as e:
            logger.error(f"获取问题反馈链接失败: {e}")
            return None
