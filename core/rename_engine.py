"""
重命名引擎 - 核心处理逻辑
"""
from core.i18n import _
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class CaseMode(Enum):
    NONE = 0
    LOWER = 1
    UPPER = 2
    TITLE = 3
    SENTENCE = 4
    INVERT = 5


@dataclass
class RenameRules:
    """重命名规则配置"""
    # 正则(1) - RegEx
    regex_enabled: bool = False
    regex_pattern: str = ""
    regex_replace: str = ""
    regex_case_insensitive: bool = False
    
    # 替换(3) - Replace
    replace_enabled: bool = False
    replace_find: str = ""
    replace_with: str = ""
    replace_case_sensitive: bool = False
    
    # 移除(5) - Remove
    remove_enabled: bool = False
    remove_first_n: int = 0
    remove_last_n: int = 0
    remove_from: int = 0
    remove_to: int = 0
    remove_chars: str = ""
    remove_words: str = ""
    remove_crop_mode: int = 0  # 0=无, 1=在前, 2=在后, 3=特殊
    remove_crop_text: str = ""
    remove_digits: bool = False
    remove_chinese: bool = False
    remove_trim: bool = False  # 修饰（移除首尾空格）
    remove_ds: bool = False  # D/S（移除双空格）
    remove_accents: bool = False  # 重音符
    remove_chars_check: bool = False  # 字符（移除特殊字符）
    remove_symbols: bool = False  # 符号
    remove_lead_dots: int = 0  # 前导点号: 0=无, 1=移除, 2=保留一个
    
    # 添加(7) - Add
    add_enabled: bool = False
    add_prefix: str = ""
    add_suffix: str = ""
    add_insert: str = ""
    add_insert_pos: int = 0
    add_word_space: bool = False
    
    # 自动日期(8) - Auto Date
    auto_date_enabled: bool = False
    # 0=创建时间(当前), 1=创建时间(新建), 2=修改时间(当前), 3=修改时间(新建),
    # 4=访问时间(当前), 5=访问时间(新建), 6=发生时间, 7=当前时间
    auto_date_mode: int = 0
    auto_date_format: str = "YMD"  # DMY, MDY, YMD等格式
    auto_date_pos: int = 0  # 0=无, 1=前缀, 2=后缀, 3=固定
    auto_date_sep: str = ""  # 分隔符（日期各部分之间）
    auto_date_connect: str = "_"  # 连接符（日期与文件名之间）
    auto_date_custom: str = ""  # 定制格式
    auto_date_center: bool = False  # 中心
    auto_date_distance: int = 0  # 距离
    
    # 编号(10) - Numbering
    numbering_enabled: bool = False
    numbering_mode: int = 0  # 0=无, 1=前缀, 2=后缀, 3=两者, 4=插入
    numbering_start: int = 1
    numbering_increment: int = 1
    numbering_padding: int = 0
    numbering_separator: str = ""
    numbering_insert_pos: int = 0
    numbering_break: int = 0  # 打断：每N个文件重置计数
    numbering_type: int = 0  # 0=十进制, 1=十六进制, 2=字母
    numbering_roman: int = 0  # 0=无, 1=大写罗马, 2=小写罗马
    
    # 文件(2) - Name
    name_enabled: bool = False
    name_mode: int = 0  # 0=保持, 1=移除, 2=固定, 3=反转
    name_fixed: str = ""
    
    # 大小写(4) - Case
    case_enabled: bool = False
    case_mode: CaseMode = CaseMode.NONE
    case_exception: str = ""
    
    # 移动/复制(6) - Move/Copy
    move_enabled: bool = False
    move_copy_mode: int = 0  # 0=无, 1=复制开始, 2=复制最后, 3=移动开始, 4=移动最后
    move_copy_from: int = 0  # 从位置（起始位置）或字符数
    move_copy_target: int = 0  # 目标位置: 0=无, 1=到开头, 2=到结尾, 3=到位置
    move_copy_count: int = 0  # 字符数/目标位置
    move_copy_separator: str = ""
    
    # 扩展名(11) - Extension
    ext_enabled: bool = False
    ext_mode: int = 0  # 0=相同, 1=小写, 2=大写, 3=标题, 4=固定, 5=额外, 6=移除
    ext_fixed: str = ""
    
    # 附加文件夹名(9) - Append Folder Name
    folder_name_enabled: bool = False
    folder_name_pos: int = 0  # 0=前缀, 1=后缀
    folder_name_separator: str = ""
    folder_name_levels: int = 1


class RenameEngine:
    """重命名引擎"""
    
    def __init__(self):
        self.rules = RenameRules()
        self._counter = 0
    
    def reset_counter(self):
        """重置计数器"""
        self._counter = 0
    
    def preview_rename(self, filepath: str, index: int = 0) -> str:
        """预览重命名结果"""
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        
        # 分离文件名和扩展名
        if '.' in filename and not filename.startswith('.'):
            name, ext = os.path.splitext(filename)
        else:
            name, ext = filename, ""
        
        # 应用各种规则
        new_name = self._apply_rules(name, filepath, index)
        new_ext = self._apply_ext_rules(ext)
        
        return new_name + new_ext

    def _apply_rules(self, name: str, filepath: str, index: int) -> str:
        """应用所有重命名规则"""
        result = name
        
        # 1. 正则替换
        if self.rules.regex_enabled and self.rules.regex_pattern:
            try:
                flags = re.IGNORECASE if self.rules.regex_case_insensitive else 0
                result = re.sub(self.rules.regex_pattern, self.rules.regex_replace, result, flags=flags)
            except re.error:
                pass
        
        # 2. 文件名模式
        if self.rules.name_enabled:
            if self.rules.name_mode == 1:  # 移除
                result = ""
            elif self.rules.name_mode == 2:  # 固定
                result = self.rules.name_fixed
            elif self.rules.name_mode == 3:  # 反转
                result = result[::-1]
        
        # 3. 替换
        if self.rules.replace_enabled and self.rules.replace_find:
            if self.rules.replace_case_sensitive:
                result = result.replace(self.rules.replace_find, self.rules.replace_with)
            else:
                pattern = re.compile(re.escape(self.rules.replace_find), re.IGNORECASE)
                result = pattern.sub(self.rules.replace_with, result)
        
        # 4. 大小写转换
        if self.rules.case_enabled:
            result = self._apply_case(result)
        
        # 5. 移除
        if self.rules.remove_enabled:
            result = self._apply_remove(result)
        
        # 6. 移动/复制
        if self.rules.move_enabled:
            result = self._apply_move_copy(result)
        
        # 7. 添加
        if self.rules.add_enabled:
            result = self._apply_add(result)
        
        # 8. 自动日期
        if self.rules.auto_date_enabled:
            result = self._apply_auto_date(result, filepath)
        
        # 9. 附加文件夹名
        if self.rules.folder_name_enabled:
            result = self._apply_folder_name(result, filepath)
        
        # 10. 编号
        if self.rules.numbering_enabled:
            result = self._apply_numbering(result, index)
        
        return result
    
    def _apply_case(self, name: str) -> str:
        """应用大小写转换"""
        mode = self.rules.case_mode
        if mode == CaseMode.LOWER:
            return name.lower()
        elif mode == CaseMode.UPPER:
            return name.upper()
        elif mode == CaseMode.TITLE:
            return name.title()
        elif mode == CaseMode.SENTENCE:
            return name.capitalize()
        elif mode == CaseMode.INVERT:
            return name.swapcase()
        return name
    
    def _apply_remove(self, name: str) -> str:
        """应用移除规则"""
        result = name
        
        # 移除前N个字符（最初）
        if self.rules.remove_first_n > 0:
            result = result[self.rules.remove_first_n:]
        
        # 移除后N个字符（最后）
        if self.rules.remove_last_n > 0:
            result = result[:-self.rules.remove_last_n] if self.rules.remove_last_n < len(result) else ""
        
        # 移除指定位置范围（从...到）
        if self.rules.remove_from > 0 and self.rules.remove_to >= self.rules.remove_from:
            start = self.rules.remove_from - 1
            end = self.rules.remove_to
            result = result[:start] + result[end:]
        
        # 移除指定字符
        if self.rules.remove_chars:
            for char in self.rules.remove_chars:
                result = result.replace(char, "")
        
        # 移除指定词（单词）
        if self.rules.remove_words:
            for word in self.rules.remove_words.split():
                result = result.replace(word, "")
        
        # 裁切功能
        if self.rules.remove_crop_mode > 0 and self.rules.remove_crop_text:
            crop_text = self.rules.remove_crop_text
            if self.rules.remove_crop_mode == 1:  # 在前 - 移除裁切文本之前的内容
                idx = result.find(crop_text)
                if idx >= 0:
                    result = result[idx + len(crop_text):]
            elif self.rules.remove_crop_mode == 2:  # 在后 - 移除裁切文本之后的内容
                idx = result.find(crop_text)
                if idx >= 0:
                    result = result[:idx]
            elif self.rules.remove_crop_mode == 3:  # 特殊 - 移除裁切文本本身
                result = result.replace(crop_text, "")
        
        # 移除数字
        if self.rules.remove_digits:
            result = re.sub(r'\d', '', result)
        
        # 移除汉字
        if self.rules.remove_chinese:
            result = re.sub(r'[\u4e00-\u9fff]', '', result)
        
        # 移除重音符
        if self.rules.remove_accents:
            import unicodedata
            result = ''.join(
                c for c in unicodedata.normalize('NFD', result)
                if unicodedata.category(c) != 'Mn'
            )
        
        # 移除特殊字符（字符复选框）
        if self.rules.remove_chars_check:
            result = re.sub(r'[^\w\s\-_.]', '', result)
        
        # 移除符号
        if self.rules.remove_symbols:
            result = re.sub(r'[!@#$%^&*()+=\[\]{};:\'",.<>?/\\|`~]', '', result)
        
        # 前导点号处理
        if self.rules.remove_lead_dots > 0:
            if self.rules.remove_lead_dots == 1:  # 移除所有前导点号
                result = result.lstrip('.')
            elif self.rules.remove_lead_dots == 2:  # 保留一个前导点号
                stripped = result.lstrip('.')
                if result.startswith('.'):
                    result = '.' + stripped
                else:
                    result = stripped
        
        # 修饰 - 去除首尾空格
        if self.rules.remove_trim:
            result = result.strip()
        
        # D/S - 移除双空格
        if self.rules.remove_ds:
            while '  ' in result:
                result = result.replace('  ', ' ')
        
        return result
    
    def _apply_add(self, name: str) -> str:
        """应用添加规则"""
        result = name
        
        # 插入文本
        if self.rules.add_insert and self.rules.add_insert_pos >= 0:
            pos = min(self.rules.add_insert_pos, len(result))
            result = result[:pos] + self.rules.add_insert + result[pos:]
        
        # 添加前缀
        if self.rules.add_prefix:
            result = self.rules.add_prefix + result
        
        # 添加后缀
        if self.rules.add_suffix:
            result = result + self.rules.add_suffix
        
        return result

    def _apply_auto_date(self, name: str, filepath: str) -> str:
        """应用自动日期"""
        import datetime
        try:
            stat = os.stat(filepath)
            mode = self.rules.auto_date_mode
            
            # 获取时间戳
            # UI下拉框: 0=创建时间(当前), 1=修改时间(当前), 2=访问时间(当前), 3=当前时间
            if mode == 0:  # 创建时间(当前)
                dt = datetime.datetime.fromtimestamp(stat.st_ctime)
            elif mode == 1:  # 修改时间(当前)
                dt = datetime.datetime.fromtimestamp(stat.st_mtime)
            elif mode == 2:  # 访问时间(当前)
                dt = datetime.datetime.fromtimestamp(stat.st_atime)
            elif mode == 3:  # 当前时间（当天日期）
                dt = datetime.datetime.now()
            else:
                dt = datetime.datetime.fromtimestamp(stat.st_ctime)
            
            # 格式化日期
            date_str = self._format_date(dt)
            
            # 如果方式为"无"，不添加日期
            if self.rules.auto_date_pos == 0:
                return name
            
            # 连接符
            connect = self.rules.auto_date_connect
            
            # 根据方式添加日期
            if self.rules.auto_date_center:
                # 中心模式：在指定距离位置插入
                pos = self.rules.auto_date_distance
                if pos >= len(name):
                    return name + connect + date_str
                else:
                    return name[:pos] + connect + date_str + connect + name[pos:]
            elif self.rules.auto_date_pos == 1:  # 前缀
                return date_str + connect + name
            elif self.rules.auto_date_pos == 2:  # 后缀
                return name + connect + date_str
            elif self.rules.auto_date_pos == 3:  # 固定（替换文件名）
                return date_str
            
            return name
        except Exception:
            return name
    
    def _format_date(self, dt) -> str:
        """根据格式设置格式化日期"""
        import datetime
        
        # 如果有定制格式，优先使用
        if self.rules.auto_date_custom:
            try:
                return dt.strftime(self.rules.auto_date_custom)
            except Exception:
                pass
        
        # 分隔符
        sep = self.rules.auto_date_sep
        
        # 预定义格式映射（支持中文和英文格式）
        format_map = {
            # 英文格式（兼容旧版）
            "DMY": f"%d{sep}%m{sep}%Y",
            "MDY": f"%m{sep}%d{sep}%Y",
            "YMD": f"%Y{sep}%m{sep}%d",
            "YDM": f"%Y{sep}%d{sep}%m",
            "DYM": f"%d{sep}%Y{sep}%m",
            "MYD": f"%m{sep}%Y{sep}%d",
            "DMYHMS": f"%d{sep}%m{sep}%Y{sep}%H{sep}%M{sep}%S",
            "MDYHMS": f"%m{sep}%d{sep}%Y{sep}%H{sep}%M{sep}%S",
            "YMDHMS": f"%Y{sep}%m{sep}%d{sep}%H{sep}%M{sep}%S",
            "Y": "%Y",
            "M": "%m",
            "D": "%d",
            "YM": f"%Y{sep}%m",
            "MD": f"%m{sep}%d",
            "HMS": f"%H{sep}%M{sep}%S",
            "HM": f"%H{sep}%M",
            "H": "%H",
            # 使用翻译后的格式作为键
            _("main_window.rules.auto_date.formats")[0]: f"%Y{sep}%m{sep}%d",
            _("main_window.rules.auto_date.formats")[1]: f"%d{sep}%m{sep}%Y",
            _("main_window.rules.auto_date.formats")[2]: f"%m{sep}%d{sep}%Y",
        }
        
        fmt = self.rules.auto_date_format
        if fmt in format_map:
            return dt.strftime(format_map[fmt])
        else:
            # 尝试直接作为strftime格式使用
            try:
                return dt.strftime(fmt)
            except Exception:
                return dt.strftime("%Y%m%d")
    
    def _get_exif_date(self, filepath: str):
        """从图片EXIF获取拍摄时间"""
        import datetime
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            img = Image.open(filepath)
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal":
                        return datetime.datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
        return None
    
    def _apply_folder_name(self, name: str, filepath: str) -> str:
        """应用附加文件夹名
        folder_name_pos: 0=无, 1=前缀, 2=后缀
        UI下拉框索引: 0=无, 1=前缀, 2=后缀
        """
        try:
            # 如果位置为"无"，不添加文件夹名
            if self.rules.folder_name_pos == 0:
                return name
            
            directory = os.path.dirname(filepath)
            parts = []
            for _ in range(self.rules.folder_name_levels):
                folder = os.path.basename(directory)
                if folder:
                    parts.insert(0, folder)
                directory = os.path.dirname(directory)
            
            folder_str = self.rules.folder_name_separator.join(parts)
            sep = self.rules.folder_name_separator
            
            # 修复：正确映射前缀和后缀
            # folder_name_pos: 1=前缀, 2=后缀
            if self.rules.folder_name_pos == 1:  # 前缀 - 文件夹名在前
                if sep:
                    return folder_str + sep + name
                else:
                    return folder_str + name
            elif self.rules.folder_name_pos == 2:  # 后缀 - 文件夹名在后
                if sep:
                    return name + sep + folder_str
                else:
                    return name + folder_str
            
            return name
        except:
            return name
    
    def _apply_numbering(self, name: str, index: int) -> str:
        """应用编号"""
        # 计算实际编号（考虑打断功能）
        if self.rules.numbering_break > 0:
            # 打断：每N个文件重置计数
            local_index = index % self.rules.numbering_break
            num = self.rules.numbering_start + local_index * self.rules.numbering_increment
        else:
            num = self.rules.numbering_start + index * self.rules.numbering_increment
        
        # 根据类型和罗马数设置生成编号字符串
        num_str = self._format_number(num)
        sep = self.rules.numbering_separator
        
        mode = self.rules.numbering_mode
        if mode == 0:  # 无
            return name
        elif mode == 1:  # 前缀
            return num_str + sep + name
        elif mode == 2:  # 后缀
            return name + sep + num_str
        elif mode == 3:  # 两者
            return num_str + sep + name + sep + num_str
        elif mode == 4:  # 插入
            pos = min(self.rules.numbering_insert_pos, len(name))
            return name[:pos] + num_str + name[pos:]
        return name
    
    def _format_number(self, num: int) -> str:
        """根据类型格式化编号"""
        # 优先检查罗马数字
        if self.rules.numbering_roman == 1:  # 大写罗马
            return self._to_roman(num).upper()
        elif self.rules.numbering_roman == 2:  # 小写罗马
            return self._to_roman(num).lower()
        
        # 根据进制类型格式化
        # 类型索引: 0=Base2, 1=Base3, ..., 8=Base10, ..., 14=Base16, 15=A-Z, 16=a-z
        num_type = self.rules.numbering_type
        
        if num_type == 15:  # A-Z (大写字母)
            num_str = self._to_base26(num).upper()
        elif num_type == 16:  # a-z (小写字母)
            num_str = self._to_base26(num).lower()
        elif 0 <= num_type <= 14:
            # Base 2 到 Base 16
            base = num_type + 2  # 索引0对应Base2，索引14对应Base16
            num_str = self._to_base_n(num, base)
        else:
            num_str = str(num)
        
        # 应用对齐（补零）
        if self.rules.numbering_padding > 0:
            num_str = num_str.zfill(self.rules.numbering_padding)
        
        return num_str
    
    def _to_roman(self, num: int) -> str:
        """转换为罗马数字"""
        if num <= 0 or num > 3999:
            return str(num)
        
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
        
        result = ''
        for i, v in enumerate(val):
            while num >= v:
                result += syms[i]
                num -= v
        return result
    
    def _to_base26(self, num: int) -> str:
        """转换为26进制字母 (A=1, B=2, ..., Z=26, AA=27...)"""
        if num <= 0:
            return 'A'
        
        result = ''
        while num > 0:
            num -= 1
            result = chr(65 + (num % 26)) + result
            num //= 26
        return result
    
    def _to_base_n(self, num: int, base: int) -> str:
        """转换为任意进制 (2-16)"""
        if num == 0:
            return '0'
        if base < 2 or base > 16:
            return str(num)
        
        digits = '0123456789ABCDEF'
        result = ''
        while num > 0:
            result = digits[num % base] + result
            num //= base
        return result if result else '0'
    
    def _apply_move_copy(self, name: str) -> str:
        """应用移动/复制
        模式: 0=无, 1=复制开始, 2=复制最后, 3=移动开始, 4=移动最后
        目标: 0=无, 1=到开头, 2=到结尾, 3=到位置
        """
        if len(name) == 0:
            return name
        
        mode = self.rules.move_copy_mode
        target = self.rules.move_copy_target
        
        if mode == 0 or target == 0:  # 无操作
            return name
        
        from_pos = self.rules.move_copy_from  # 从位置或字符数
        count = self.rules.move_copy_count  # 字符数或目标位置
        sep = self.rules.move_copy_separator
        
        # 根据模式确定是从开始还是从最后提取，以及是复制还是移动
        is_copy = mode in [1, 2]  # 1=复制开始, 2=复制最后
        from_start = mode in [1, 3]  # 1=复制开始, 3=移动开始
        
        # 计算要提取的字符段
        if from_start:
            # 从开始位置提取
            start_pos = from_pos
            end_pos = from_pos + count if count > 0 else len(name)
            if start_pos >= len(name):
                return name
            end_pos = min(end_pos, len(name))
            segment = name[start_pos:end_pos]
        else:
            # 从最后位置提取
            # from_pos 表示从末尾往前数的位置，count 表示字符数
            if from_pos >= len(name):
                return name
            start_pos = len(name) - from_pos - count if count > 0 else 0
            start_pos = max(0, start_pos)
            end_pos = len(name) - from_pos
            segment = name[start_pos:end_pos]
        
        if not segment:
            return name
        
        # 根据是复制还是移动决定剩余部分
        if is_copy:
            remaining = name  # 复制时保留原文
        else:
            remaining = name[:start_pos] + name[end_pos:]  # 移动时删除原位置的字符
        
        # 根据目标位置插入
        if target == 1:  # 到开头
            if sep:
                return segment + sep + remaining
            else:
                return segment + remaining
        elif target == 2:  # 到结尾
            if sep:
                return remaining + sep + segment
            else:
                return remaining + segment
        elif target == 3:  # 到位置
            target_pos = min(count, len(remaining))
            return remaining[:target_pos] + segment + remaining[target_pos:]
        
        return name
    
    def _apply_ext_rules(self, ext: str) -> str:
        """应用扩展名规则
        模式: 0=相同, 1=小写, 2=大写, 3=标题, 4=固定, 5=额外, 6=移除
        """
        if not self.rules.ext_enabled:
            return ext
        
        mode = self.rules.ext_mode
        if mode == 0:  # 相同（保持不变）
            return ext
        elif mode == 1:  # 小写
            return ext.lower()
        elif mode == 2:  # 大写
            return ext.upper()
        elif mode == 3:  # 标题（首字母大写）
            # 扩展名通常以.开头，所以需要特殊处理
            if ext.startswith('.'):
                return '.' + ext[1:].capitalize()
            return ext.capitalize()
        elif mode == 4:  # 固定（替换为指定扩展名）
            if self.rules.ext_fixed:
                new_ext = self.rules.ext_fixed
                if not new_ext.startswith('.'):
                    new_ext = '.' + new_ext
                return new_ext
            return ext
        elif mode == 5:  # 额外（在原扩展名后添加）
            if self.rules.ext_fixed:
                new_ext = self.rules.ext_fixed
                if not new_ext.startswith('.'):
                    new_ext = '.' + new_ext
                return ext + new_ext
            return ext
        elif mode == 6:  # 移除
            return ""
        
        return ext
        return ext
    
    def execute_rename(self, files: List[str]) -> List[tuple]:
        """执行重命名操作"""
        results = []
        self.reset_counter()
        
        for index, filepath in enumerate(files):
            try:
                directory = os.path.dirname(filepath)
                new_name = self.preview_rename(filepath, index)
                new_path = os.path.join(directory, new_name)
                
                if filepath != new_path:
                    # 检查目标文件是否存在
                    if os.path.exists(new_path):
                        results.append((filepath, new_path, False, _("rename_engine.file_exists")))
                    else:
                        os.rename(filepath, new_path)
                        results.append((filepath, new_path, True, _("rename_engine.success")))
                else:
                    results.append((filepath, new_path, True, _("rename_engine.no_change")))
            except Exception as e:
                results.append((filepath, "", False, str(e)))
        
        return results
