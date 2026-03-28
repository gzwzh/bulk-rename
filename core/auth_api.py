"""
认证API模块 - 处理与服务器的通信
"""
import requests
import json
from typing import Optional, Dict, Any
from urllib.parse import urlencode


class AuthAPI:
    """认证API客户端"""
    
    BASE_URL = "https://api-web.kunqiongai.com"
    
    # API端点
    ENDPOINTS = {
        "get_web_login_url": "/soft_desktop/get_web_login_url",
        "get_token": "/user/desktop_get_token",
        "check_login": "/user/check_login",
        "get_user_info": "/soft_desktop/get_user_info",
        "logout": "/logout",
        "get_custom_url": "/soft_desktop/get_custom_url",
    }
    
    # 超时设置
    TIMEOUT = 10

    @staticmethod
    def _debug(message: str):
        print(f"[AUTH_API] {message}", flush=True)
    
    @staticmethod
    def get_web_login_url() -> Optional[str]:
        """
        获取网页端登录地址
        
        Returns:
            登录URL或None
        """
        try:
            url = AuthAPI.BASE_URL + AuthAPI.ENDPOINTS["get_web_login_url"]
            AuthAPI._debug(f"request login url: {url}")
            response = requests.post(url, timeout=AuthAPI.TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            AuthAPI._debug(f"login url response code={data.get('code')}")
            if data.get("code") == 1 and "data" in data:
                return data["data"].get("login_url")
            return None
        except Exception as e:
            AuthAPI._debug(f"get_web_login_url failed: {e}")
            return None
    
    @staticmethod
    def get_custom_url() -> Optional[str]:
        """
        获取需求定制页面链接
        
        Returns:
            需求定制页面URL或None
        """
        try:
            url = AuthAPI.BASE_URL + AuthAPI.ENDPOINTS["get_custom_url"]
            response = requests.post(url, timeout=AuthAPI.TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 1 and "data" in data:
                return data["data"].get("url")
            return None
        except Exception as e:
            print(f"获取需求定制页面链接失败: {e}")
            return None
    
    @staticmethod
    def get_token(client_nonce: str) -> Optional[str]:
        """
        获取登录令牌
        
        Args:
            client_nonce: 临时会话ID
            
        Returns:
            Token或None
        """
        try:
            url = AuthAPI.BASE_URL + AuthAPI.ENDPOINTS["get_token"]
            AuthAPI._debug(f"poll token: nonce length={len(client_nonce)}")
            payload = {
                "client_type": "desktop",
                "client_nonce": client_nonce,
            }
            
            response = requests.post(
                url,
                data=urlencode(payload),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=AuthAPI.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            payload_data = data.get("data") or {}
            token = payload_data.get("token")
            AuthAPI._debug(
                f"poll token response code={data.get('code')}, "
                f"data_type={type(data.get('data')).__name__}, has_token={bool(token)}"
            )
            if data.get("code") == 1 and token:
                return token
            return None
        except Exception as e:
            AuthAPI._debug(f"get_token failed: {e}")
            return None
    
    @staticmethod
    def check_login(token: str) -> bool:
        """
        检查是否已登录
        
        Args:
            token: 登录令牌
            
        Returns:
            是否已登录
        """
        try:
            url = AuthAPI.BASE_URL + AuthAPI.ENDPOINTS["check_login"]
            payload = {"token": token}
            
            response = requests.post(
                url,
                data=urlencode(payload),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=AuthAPI.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("code") == 1
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False
    
    @staticmethod
    def get_user_info(token: str) -> Optional[Dict[str, Any]]:
        """
        获取用户基本信息
        
        Args:
            token: 登录令牌
            
        Returns:
            用户信息字典或None
        """
        try:
            url = AuthAPI.BASE_URL + AuthAPI.ENDPOINTS["get_user_info"]
            AuthAPI._debug("request user info")
            
            response = requests.post(
                url,
                headers={
                    "token": token,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=AuthAPI.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            AuthAPI._debug(f"user info response code={data.get('code')}")
            if data.get("code") == 1 and "data" in data:
                return data["data"].get("user_info")
            return None
        except Exception as e:
            AuthAPI._debug(f"get_user_info failed: {e}")
            return None
    
    @staticmethod
    def logout(token: str) -> bool:
        """
        退出登录
        
        Args:
            token: 登录令牌
            
        Returns:
            是否成功
        """
        try:
            url = AuthAPI.BASE_URL + AuthAPI.ENDPOINTS["logout"]
            
            response = requests.post(
                url,
                headers={
                    "token": token,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=AuthAPI.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("code") == 1
        except Exception as e:
            print(f"退出登录失败: {e}")
            return False
