"""
示例测试文件 - 可根据需要扩展
"""
import pytest
from pathlib import Path
from ark_asa_manager.ini import INIParser
from ark_asa_manager.models import ServerConfig, RCONConfig


class TestINIParser:
    """INI解析器测试"""
    
    def test_parse_basic(self, tmp_path):
        \"\"\"测试基本解析\"\"\"
        ini_file = tmp_path / "test.ini"
        ini_file.write_text("[Section1]\nKey1=Value1\n")
        
        parser = INIParser()
        assert parser.parse_file(ini_file) is True
        assert parser.get("Section1", "Key1") == "Value1"


class TestServerConfig:
    \"\"\"服务器配置测试\"\"\"
    
    def test_create_config(self, tmp_path):
        \"\"\"测试创建配置\"\"\"
        config = ServerConfig(
            name="test_server",
            server_dir=tmp_path,
        )
        assert config.name == "test_server"
        assert config.port == 7777


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
