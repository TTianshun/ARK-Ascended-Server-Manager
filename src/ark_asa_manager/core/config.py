"""
配置管理
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置文件管理"""
    
    def __init__(self, config_dir: Path, config_name: str = "global.json"):
        self.config_dir = config_dir
        self.config_path = config_dir / config_name
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                return {}
        return {}
    
    def save(self) -> bool:
        """保存配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value
    
    def update(self, data: Dict[str, Any]) -> None:
        """更新配置"""
        self._config.update(data)
