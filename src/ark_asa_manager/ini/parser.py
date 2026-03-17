"""
INI文件解析和处理
"""
import re
from typing import List, Optional, Tuple
from pathlib import Path


class INILine:
    """表示INI文件中的一行"""
    
    def __init__(self, line: str, line_type: str = "comment"):
        self.original = line
        self.type = line_type  # "section", "key", "comment", "blank"
        self.section = ""
        self.key = ""
        self.value = ""
        self._parse()
    
    def _parse(self) -> None:
        """解析行内容"""
        stripped = self.original.strip()
        
        if not stripped:
            self.type = "blank"
        elif stripped.startswith('[') and stripped.endswith(']'):
            self.type = "section"
            self.section = stripped[1:-1]
        elif '=' in stripped and not stripped.startswith(';'):
            self.type = "key"
            key_part, value_part = stripped.split('=', 1)
            self.key = key_part.strip()
            self.value = value_part.strip()
        else:
            self.type = "comment"
    
    def __repr__(self) -> str:
        if self.type == "section":
            return f"[{self.section}]"
        elif self.type == "key":
            return f"{self.key}={self.value}"
        else:
            return self.original


class INIParser:
    """INI文件解析器"""
    
    def __init__(self):
        self.lines: List[INILine] = []
        self.sections: dict = {}
    
    def parse_file(self, path: Path) -> bool:
        """解析INI文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.lines = []
            current_section = None
            
            for line in content.splitlines():
                ini_line = INILine(line)
                self.lines.append(ini_line)
                
                if ini_line.type == "section":
                    current_section = ini_line.section
                    if current_section not in self.sections:
                        self.sections[current_section] = {}
                elif ini_line.type == "key" and current_section:
                    self.sections[current_section][ini_line.key] = ini_line.value
            
            return True
        except Exception as e:
            print(f"解析INI文件失败: {e}")
            return False
    
    def get(self, section: str, key: str) -> Optional[str]:
        """获取配置值"""
        if section in self.sections and key in self.sections[section]:
            return self.sections[section][key]
        return None
    
    def set(self, section: str, key: str, value: str) -> None:
        """设置配置值"""
        if section not in self.sections:
            self.sections[section] = {}
        self.sections[section][key] = value
    
    def delete(self, section: str, key: str) -> bool:
        """删除配置值"""
        if section in self.sections and key in self.sections[section]:
            del self.sections[section][key]
            return True
        return False
    
    def to_string(self) -> str:
        """转换为字符串"""
        result = []
        current_section: Optional[str] = None
        # 跟踪每个 section 中已写出的 key，用于补充新增的 key
        written_keys: dict = {}

        for line in self.lines:
            if line.type == "section":
                # 切换 section 前，先补充当前 section 中新增的 key
                if current_section is not None:
                    self._append_new_keys(result, current_section, written_keys.get(current_section, set()))
                current_section = line.section
                written_keys[current_section] = set()
                result.append(str(line))
            elif line.type == "key" and current_section is not None:
                # 用 current_section（而非 line.section）查找最新值
                if current_section in self.sections and line.key in self.sections[current_section]:
                    new_value = self.sections[current_section][line.key]
                    result.append(f"{line.key}={new_value}")
                    written_keys[current_section].add(line.key)
                # key 已被 delete() 删除时直接跳过，不输出该行
            else:
                result.append(str(line))

        # 补充最后一个 section 中新增的 key
        if current_section is not None:
            self._append_new_keys(result, current_section, written_keys.get(current_section, set()))

        # 输出完全新增的 section（原文件中不存在的）
        existing_sections = {l.section for l in self.lines if l.type == "section"}
        for section, keys in self.sections.items():
            if section not in existing_sections:
                result.append(f"[{section}]")
                for k, v in keys.items():
                    result.append(f"{k}={v}")

        return '\n'.join(result)

    def _append_new_keys(self, result: list, section: str, written: set) -> None:
        """将 section 中通过 set() 新增但原文件中不存在的 key 追加到输出"""
        if section not in self.sections:
            return
        for key, value in self.sections[section].items():
            if key not in written:
                result.append(f"{key}={value}")
    
    def save_file(self, path: Path) -> bool:
        """保存到文件"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.to_string())
            return True
        except Exception as e:
            print(f"保存INI文件失败: {e}")
            return False