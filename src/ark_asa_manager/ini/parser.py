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
        current_section = None
        
        for line in self.lines:
            if line.type == "section":
                current_section = line.section
                result.append(str(line))
            elif line.type == "key":
                if line.section in self.sections and line.key in self.sections[line.section]:
                    new_value = self.sections[line.section][line.key]
                    result.append(f"{line.key}={new_value}")
            else:
                result.append(str(line))
        
        return '\n'.join(result)
    
    def save_file(self, path: Path) -> bool:
        """保存到文件"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.to_string())
            return True
        except Exception as e:
            print(f"保存INI文件失败: {e}")
            return False