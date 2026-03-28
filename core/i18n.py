import json
import os
import logging

class I18nManager:
    _instance = None
    _translations = {}
    _current_locale = "zh_CN"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._load_translations()
        return cls._instance

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d

    def _get_base_path(self):
        """获取基础路径，处理 PyInstaller 打包情况"""
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _load_translations(self):
        """加载翻译文件"""
        # 获取 locales 目录路径
        base_path = self._get_base_path()
        locales_dir = os.path.join(base_path, "locales")
        locale_path = os.path.join(locales_dir, f"{self._current_locale}.json")
        fallback_path = os.path.join(locales_dir, "zh_CN.json")
        
        # 先加载 zh_CN 作为基础回退
        self._translations = {}
        try:
            if os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as f:
                    self._translations = json.load(f)
        except Exception as e:
            print(f"Failed to load fallback translations: {e}")

        # 如果当前语言不是 zh_CN，则加载并合并
        if self._current_locale != "zh_CN":
            try:
                if os.path.exists(locale_path):
                    with open(locale_path, "r", encoding="utf-8") as f:
                        target_translations = json.load(f)
                        self._deep_update(self._translations, target_translations)
            except Exception as e:
                print(f"Failed to load translations: {e}")

    def get_text(self, key, default=None):
        """获取翻译文本"""
        if not key: return default or ""
        keys = key.split(".")
        val = self._translations
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default if default is not None else key
        return val

    def set_locale(self, locale):
        """切换语言"""
        if self._current_locale == locale:
            return False
        self._current_locale = locale
        self._load_translations()
        return True

    def get_available_locales(self):
        """获取所有可用的语言代码"""
        base_path = self._get_base_path()
        locales_dir = os.path.join(base_path, "locales")
        if not os.path.exists(locales_dir):
            return ["zh_CN"]
        
        locales = []
        for f in os.listdir(locales_dir):
            if f.endswith(".json"):
                locales.append(f[:-5]) # 移除 .json
        return sorted(locales)

    def get_current_locale(self):
        """获取当前语言代码"""
        return self._current_locale

# Global instance
i18n = I18nManager()

def _(key, default=None):
    return i18n.get_text(key, default)
