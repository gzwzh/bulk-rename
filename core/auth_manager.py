"""
认证管理器，负责登录流程、外部浏览器唤起和 token 持久化。
"""
import base64
import hashlib
import hmac
import json
import os
import subprocess
import threading
import time
import uuid
import webbrowser
from typing import Any, Callable, Dict, Optional, Tuple

from .auth_api import AuthAPI


class AuthManager:
    """处理登录流程和 token 管理。"""

    TOKEN_STORAGE_DIR = os.path.join(os.path.expanduser("~"), ".bulk_rename_tool")
    TOKEN_FILE = os.path.join(TOKEN_STORAGE_DIR, "auth_token.json")
    SECRET_KEY = b"7530bfb1ad6c41627b0f0620078fa5ed"

    POLL_INTERVAL = 2
    POLL_TIMEOUT = 300

    def __init__(self):
        os.makedirs(self.TOKEN_STORAGE_DIR, exist_ok=True)
        self._token = None
        self._user_info = None
        self._polling_thread = None
        self._stop_polling = False
        self._last_login_url = None
        self._load_token()

    @staticmethod
    def _debug(message: str):
        """登录调试日志。"""
        print(f"[AUTH] {message}", flush=True)

    def _load_token(self):
        """从本地加载 token。"""
        try:
            if os.path.exists(self.TOKEN_FILE):
                with open(self.TOKEN_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._token = data.get("token")
                self._user_info = data.get("user_info")

                if self._token and not self.verify_token():
                    self._token = None
                    self._user_info = None
        except Exception as e:
            print(f"加载 Token 失败: {e}")
            self._token = None
            self._user_info = None

    def _save_token(self, token: str, user_info: Optional[Dict[str, Any]] = None):
        """保存 token 到本地。"""
        try:
            data = {
                "token": token,
                "user_info": user_info,
                "saved_at": time.time(),
            }
            with open(self.TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._token = token
            self._user_info = user_info
        except Exception as e:
            print(f"保存 Token 失败: {e}")

    def _clear_token(self):
        """清理本地 token。"""
        try:
            if os.path.exists(self.TOKEN_FILE):
                os.remove(self.TOKEN_FILE)
            self._token = None
            self._user_info = None
        except Exception as e:
            print(f"清除 Token 失败: {e}")

    @classmethod
    def _get_secret_key(cls) -> bytes:
        return cls.SECRET_KEY

    @classmethod
    def generate_signed_nonce(cls) -> str:
        """生成带签名的 client_nonce。"""
        nonce = str(uuid.uuid4()).replace("-", "")
        timestamp = int(time.time())
        message = f"{nonce}|{timestamp}".encode("utf-8")
        signature = base64.b64encode(
            hmac.new(cls._get_secret_key(), message, hashlib.sha256).digest()
        ).decode("utf-8")
        signed_nonce = {
            "nonce": nonce,
            "timestamp": timestamp,
            "signature": signature,
        }
        json_str = json.dumps(signed_nonce, separators=(",", ":"))
        url_safe_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        return url_safe_str.replace("+", "-").replace("/", "_").rstrip("=")

    def is_logged_in(self) -> bool:
        return self._token is not None

    def get_token(self) -> Optional[str]:
        return self._token

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        return self._user_info

    def verify_token(self) -> bool:
        if not self._token:
            return False
        return AuthAPI.check_login(self._token)

    def get_last_login_url(self) -> Optional[str]:
        return self._last_login_url

    def build_login_url(self) -> Tuple[Optional[str], Optional[str]]:
        """
        生成完整登录地址，并返回 (url, client_nonce)。
        """
        client_nonce = self.generate_signed_nonce()
        login_url = AuthAPI.get_web_login_url()
        if not login_url:
            return None, None

        separator = "&" if "?" in login_url else "?"
        full_login_url = (
            f"{login_url}{separator}client_type=desktop&client_nonce={client_nonce}"
        )
        self._last_login_url = full_login_url
        self._debug(f"built login url, nonce length={len(client_nonce)}")
        return full_login_url, client_nonce

    def open_external_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        统一通过系统浏览器打开外链。
        """
        try:
            if os.name == "nt":
                self._debug("opening external url via os.startfile")
                os.startfile(url)
                return True, None

            # WSL 下优先用 Windows Explorer 打开完整 URL，避免 cmd 截断查询参数。
            if self._is_wsl():
                self._debug("detected WSL, trying PowerShell encoded command")
                ps_command = self._build_windows_open_url_command(url)
                spawned, spawn_error = self._try_spawn(ps_command, capture_error=True)
                if spawned:
                    self._debug("external browser launched with: powershell encoded command")
                    return True, None
                self._debug(f"launcher failed: powershell encoded command -> {spawn_error}")
                return False, spawn_error or "WSL 环境下无法自动打开浏览器"

            for command in (
                ["xdg-open", url],
                ["gio", "open", url],
                ["sensible-browser", url],
            ):
                if self._try_spawn(command):
                    self._debug(f"external browser launched with: {' '.join(command[:2])}")
                    return True, None

            if webbrowser.open(url):
                self._debug("external browser launched with python webbrowser")
                return True, None

            return False, "未找到可用的系统浏览器启动方式"
        except Exception as e:
            self._debug(f"open external url exception: {e}")
            return False, str(e)

    def start_login_flow(
        self,
        on_success: Callable,
        on_error: Callable,
        on_cancel: Callable,
    ):
        """
        启动登录流程：
        1. 生成登录 URL
        2. 通过系统浏览器打开
        3. 后台轮询 token
        """
        full_login_url, client_nonce = self.build_login_url()
        if not full_login_url or not client_nonce:
            on_error("无法获取登录 URL，请检查网络连接")
            return

        self._debug(f"starting login flow: {full_login_url[:120]}")
        opened, open_error = self.open_external_url(full_login_url)
        self._debug(f"browser open result: opened={opened}, error={open_error}")

        self._stop_polling = False
        self._polling_thread = threading.Thread(
            target=self._poll_token,
            args=(client_nonce, on_success, on_error, on_cancel),
            daemon=True,
        )
        self._polling_thread.start()

        if not opened:
            detail = f": {open_error}" if open_error else ""
            on_error(f"AUTO_OPEN_FAILED:{full_login_url}{detail}")

    def _poll_token(
        self,
        client_nonce: str,
        on_success: Callable,
        on_error: Callable,
        on_cancel: Callable,
    ):
        """轮询服务端是否已经完成网页登录。"""
        start_time = time.time()
        self._debug("polling started")

        while not self._stop_polling:
            if time.time() - start_time > self.POLL_TIMEOUT:
                self._debug("polling timeout")
                on_error(f"登录超时（{self.POLL_TIMEOUT} 秒），请重试")
                return

            try:
                token = AuthAPI.get_token(client_nonce)
                if token:
                    self._debug("token received")
                    user_info = AuthAPI.get_user_info(token)
                    self._save_token(token, user_info)
                    on_success(token, user_info or {})
                    return
                self._debug("poll returned no token")
            except Exception as e:
                self._debug(f"poll token exception: {e}")

            if not self._stop_polling:
                time.sleep(self.POLL_INTERVAL)

        self._debug("polling cancelled")
        on_cancel()

    def cancel_login(self):
        """取消登录轮询。"""
        self._stop_polling = True
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=2)

    def logout(self) -> bool:
        if not self._token:
            return False

        success = AuthAPI.logout(self._token)
        self._clear_token()
        return success

    def refresh_user_info(self) -> bool:
        if not self._token:
            return False

        user_info = AuthAPI.get_user_info(self._token)
        if user_info:
            self._user_info = user_info
            self._save_token(self._token, user_info)
            return True
        return False

    @staticmethod
    def _is_wsl() -> bool:
        """判断当前是否运行在 WSL。"""
        try:
            if os.name == "nt":
                return False
            if "WSL_DISTRO_NAME" in os.environ:
                return True
            if os.path.exists("/proc/version"):
                with open("/proc/version", "r", encoding="utf-8") as f:
                    return "microsoft" in f.read().lower()
        except Exception:
            return False
        return False

    @staticmethod
    def _try_spawn(
        command: list[str],
        capture_error: bool = False,
    ) -> Tuple[bool, Optional[str]] | bool:
        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            if capture_error:
                return True, None
            return True
        except FileNotFoundError:
            if capture_error:
                return False, "command not found"
            return False
        except Exception as e:
            if capture_error:
                return False, str(e)
            return False

    @staticmethod
    def _build_windows_open_url_command(url: str) -> list[str]:
        """
        通过 PowerShell -EncodedCommand 打开 URL，避免 WSL/Windows 多层转义丢参。
        """
        ps_script = f'Start-Process "{url}"'
        encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
        return [
            "/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe",
            "-NoProfile",
            "-EncodedCommand",
            encoded,
        ]
