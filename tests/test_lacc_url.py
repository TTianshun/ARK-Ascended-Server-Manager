"""
LACC URL 保持完整性测试

验证 INIParser 在整个服务器启动流程中能正确保留包含 :// 的 URL。
模拟：_inject_lacc_ini → ensure_required_server_settings → apply_staging_to_server
      → inject_lacc_to_server_config
"""
import logging
import shutil
import pytest
from pathlib import Path
from ark_asa_manager.ini.parser import INIParser
from ark_asa_manager.core.server_ops import inject_lacc_to_server_config


WS_URL_UNQUOTED = "ws://127.0.0.1:8000"
WS_URL_QUOTED = '"ws://127.0.0.1:8000"'
_logger = logging.getLogger(__name__)


class TestINIParserURLPreservation:
    """验证 INIParser 在各种场景下保留 URL 的完整性"""

    def test_parse_url_without_quotes(self, tmp_path: Path):
        """不带引号的 URL 解析后值完整"""
        ini = tmp_path / "test.ini"
        ini.write_text(
            "[LACC]\nURL=ws://127.0.0.1:8000\nToken=abc\nName=Server1\n",
            encoding="utf-8",
        )

        parser = INIParser()
        parser.parse_file(ini)

        assert parser.get("LACC", "URL") == WS_URL_UNQUOTED

    def test_parse_url_with_quotes(self, tmp_path: Path):
        """带双引号的 URL 解析后值完整（含引号）"""
        ini = tmp_path / "test.ini"
        ini.write_text(
            '[LACC]\nURL="ws://127.0.0.1:8000"\nToken=abc\nName=Server1\n',
            encoding="utf-8",
        )

        parser = INIParser()
        parser.parse_file(ini)

        assert parser.get("LACC", "URL") == WS_URL_QUOTED

    def test_roundtrip_url_without_quotes(self, tmp_path: Path):
        """不带引号的 URL 经过 parse → save 后保持不变"""
        ini = tmp_path / "test.ini"
        ini.write_text(
            "[LACC]\nURL=ws://127.0.0.1:8000\nToken=abc\n",
            encoding="utf-8",
        )

        parser = INIParser()
        parser.parse_file(ini)
        parser.save_file(ini)

        content = ini.read_text(encoding="utf-8")
        assert "URL=ws://127.0.0.1:8000" in content

    def test_roundtrip_url_with_quotes(self, tmp_path: Path):
        """带双引号的 URL 经过 parse → save 后保持不变"""
        ini = tmp_path / "test.ini"
        ini.write_text(
            '[LACC]\nURL="ws://127.0.0.1:8000"\nToken=abc\n',
            encoding="utf-8",
        )

        parser = INIParser()
        parser.parse_file(ini)
        parser.save_file(ini)

        content = ini.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in content

    def test_roundtrip_with_extra_set_operations(self, tmp_path: Path):
        """模拟 ensure_required_server_settings：
        解析包含 LACC 的 INI → 设置其他 section 的值 → 保存。
        LACC URL 必须保持不变。
        """
        ini = tmp_path / "test.ini"
        ini.write_text(
            "[ServerSettings]\n"
            "ServerAdminPassword=old\n"
            "\n"
            "[LACC]\n"
            'URL="ws://127.0.0.1:8000"\n'
            "Token=abc\n"
            "Name=Server1\n",
            encoding="utf-8",
        )

        parser = INIParser()
        parser.parse_file(ini)

        # 模拟 ensure_required_server_settings 的操作
        parser.set("ServerSettings", "ServerAdminPassword", "newpw")
        parser.set("ServerSettings", "ServerPassword", "joinpw")
        parser.set("ServerSettings", "RCONEnabled", "True")
        parser.set("ServerSettings", "RCONPort", "27020")
        parser.set("/Script/Engine.GameSession", "SessionName", "MyServer")
        parser.set("/Script/Engine.GameSession", "MaxPlayers", "70")

        parser.save_file(ini)

        content = ini.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in content, (
            f"URL was corrupted after set+save. File content:\n{content}"
        )
        assert "Token=abc" in content
        assert "Name=Server1" in content

    def test_roundtrip_url_unquoted_with_extra_set(self, tmp_path: Path):
        """同上测试，但 URL 不带引号"""
        ini = tmp_path / "test.ini"
        ini.write_text(
            "[ServerSettings]\n"
            "ServerAdminPassword=old\n"
            "\n"
            "[LACC]\n"
            "URL=ws://127.0.0.1:8000\n"
            "Token=abc\n"
            "Name=Server1\n",
            encoding="utf-8",
        )

        parser = INIParser()
        parser.parse_file(ini)

        parser.set("ServerSettings", "ServerAdminPassword", "newpw")
        parser.set("/Script/Engine.GameSession", "SessionName", "MyServer")
        parser.set("/Script/Engine.GameSession", "MaxPlayers", "70")

        parser.save_file(ini)

        content = ini.read_text(encoding="utf-8")
        assert "URL=ws://127.0.0.1:8000" in content, (
            f"URL was corrupted. File content:\n{content}"
        )

    def test_bom_file_preserves_url(self, tmp_path: Path):
        """带 BOM (utf-8-sig) 的文件经过 parse → save 后 URL 不变"""
        ini = tmp_path / "test.ini"
        ini.write_text(
            "[ServerSettings]\n"
            "ServerAdminPassword=old\n"
            "[LACC]\n"
            'URL="ws://127.0.0.1:8000"\n'
            "Token=abc\n",
            encoding="utf-8-sig",  # 写入带 BOM 的文件
        )

        parser = INIParser()
        parser.parse_file(ini)

        # BOM 不应影响 LACC URL 的解析
        assert parser.get("LACC", "URL") == WS_URL_QUOTED

        parser.set("ServerSettings", "ServerAdminPassword", "newpw")
        parser.save_file(ini)

        content = ini.read_text(encoding="utf-8-sig")
        assert 'URL="ws://127.0.0.1:8000"' in content, (
            f"URL was corrupted after BOM file roundtrip. Content:\n{content}"
        )


class TestFullLACCFlow:
    """模拟完整的 LACC 配置 + 服务器启动流程"""

    def _simulate_inject_lacc_ini(
        self, ini_path: Path, ws_url: str, token: str, map_name: str
    ):
        """模拟 _inject_lacc_ini 的行为"""
        lacc_section = (
            f"\n[LACC]\n"
            f'URL="{ws_url}"\n'
            f"Token={token}\n"
            f'Name="{map_name}"\n'
        )

        if ini_path.exists():
            content = ini_path.read_text(encoding="utf-8-sig")
        else:
            content = ""

        import re

        if "[LACC]" in content:
            content = re.sub(
                r"\[LACC\][^\[]*",
                lacc_section.lstrip("\n") + "\n",
                content,
                count=1,
            )
        else:
            content = content.rstrip() + "\n" + lacc_section

        ini_path.parent.mkdir(parents=True, exist_ok=True)
        ini_path.write_text(content, encoding="utf-8")

    def _simulate_ensure_required_settings(self, ini_path: Path):
        """模拟 ensure_required_server_settings 的行为"""
        parser = INIParser()
        parser.parse_file(ini_path)

        parser.set("ServerSettings", "ServerAdminPassword", "admin123")
        parser.set("ServerSettings", "ServerPassword", "join456")
        parser.set("ServerSettings", "RCONEnabled", "True")
        parser.set("ServerSettings", "RCONPort", "27020")
        parser.set("/Script/Engine.GameSession", "SessionName", "TestServer")
        parser.set("/Script/Engine.GameSession", "MaxPlayers", "70")

        parser.save_file(ini_path)

    def test_full_flow_empty_staging(self, tmp_path: Path):
        """完整流程：staging 文件不存在 → inject → ensure → copy → 验证"""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        server_dir = tmp_path / "server" / "ShooterGame" / "Saved" / "Config" / "WindowsServer"
        server_dir.mkdir(parents=True)

        staging_gus = staging_dir / "GameUserSettings.ini"
        server_gus = server_dir / "GameUserSettings.ini"

        # Step 1: inject LACC (模拟自动配置)
        self._simulate_inject_lacc_ini(
            staging_gus, "ws://127.0.0.1:8000", "mytoken", "TheIsland"
        )

        staging_after_inject = staging_gus.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in staging_after_inject, (
            f"inject 后 staging 文件不正确:\n{staging_after_inject}"
        )

        # Step 2: ensure_required_server_settings (模拟服务器启动)
        self._simulate_ensure_required_settings(staging_gus)

        staging_after_ensure = staging_gus.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in staging_after_ensure, (
            f"ensure 后 staging URL 被截断:\n{staging_after_ensure}"
        )

        # Step 3: apply_staging_to_server (模拟复制到服务器目录)
        shutil.copy2(staging_gus, server_gus)

        server_content = server_gus.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in server_content, (
            f"服务器配置中 URL 被截断:\n{server_content}"
        )

    def test_full_flow_existing_staging(self, tmp_path: Path):
        """完整流程：staging 已有内容 → inject → ensure → copy → 验证"""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        server_dir = tmp_path / "server"
        server_dir.mkdir()

        staging_gus = staging_dir / "GameUserSettings.ini"
        server_gus = server_dir / "GameUserSettings.ini"

        # 预先写入 staging 内容（模拟之前的配置）
        staging_gus.write_text(
            "[ServerSettings]\n"
            "ServerAdminPassword=old\n"
            "ServerPassword=\n"
            "\n"
            "[/Script/Engine.GameSession]\n"
            "MaxPlayers=50\n",
            encoding="utf-8",
        )

        # Step 1: inject LACC
        self._simulate_inject_lacc_ini(
            staging_gus, "ws://127.0.0.1:8000", "secret", "Fjordur"
        )

        # Step 2: ensure_required_server_settings
        self._simulate_ensure_required_settings(staging_gus)

        staging_content = staging_gus.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in staging_content, (
            f"ensure 后 URL 被截断:\n{staging_content}"
        )

        # Step 3: copy to server
        shutil.copy2(staging_gus, server_gus)

        server_content = server_gus.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:8000"' in server_content, (
            f"服务器配置中 URL 被截断:\n{server_content}"
        )

    def test_full_flow_reinject_after_previous_run(self, tmp_path: Path):
        """完整流程：第一次运行后再次 inject → ensure → 验证（URL 不重复引号）"""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        staging_gus = staging_dir / "GameUserSettings.ini"

        # 第一次注入
        self._simulate_inject_lacc_ini(
            staging_gus, "ws://127.0.0.1:8000", "tok", "Map1"
        )
        self._simulate_ensure_required_settings(staging_gus)

        # 第二次注入（模拟用户再次点击自动配置）
        self._simulate_inject_lacc_ini(
            staging_gus, "ws://127.0.0.1:9000", "tok2", "Map2"
        )
        self._simulate_ensure_required_settings(staging_gus)

        content = staging_gus.read_text(encoding="utf-8")
        assert 'URL="ws://127.0.0.1:9000"' in content, (
            f"第二次注入后 URL 不正确:\n{content}"
        )
        # 确保没有双重引号
        assert 'URL=""ws' not in content
        assert "Token=tok2" in content
        assert 'Name="Map2"' in content

    def test_url_with_different_ports(self, tmp_path: Path):
        """验证不同端口的 URL 都能正确保留"""
        staging_gus = tmp_path / "GameUserSettings.ini"

        for port in [8000, 8080, 9999, 443, 80]:
            url = f"ws://127.0.0.1:{port}"
            self._simulate_inject_lacc_ini(staging_gus, url, "t", "S")
            self._simulate_ensure_required_settings(staging_gus)

            content = staging_gus.read_text(encoding="utf-8")
            expected = f'URL="{url}"'
            assert expected in content, (
                f"Port {port}: URL 被截断。期望 {expected}，文件内容:\n{content}"
            )


class TestInjectLACCToServerConfig:
    """验证 inject_lacc_to_server_config 直接写入正确 URL"""

    GUS_REL = "ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini"

    def _make_server_gus(self, server_dir: Path, content: str = "") -> Path:
        gus = server_dir / self.GUS_REL
        gus.parent.mkdir(parents=True, exist_ok=True)
        gus.write_text(content, encoding="utf-8")
        return gus

    def test_inject_creates_lacc_section(self, tmp_path: Path):
        """对没有 LACC 的文件注入后包含完整 URL"""
        server_dir = tmp_path / "server"
        gus = self._make_server_gus(
            server_dir,
            "[ServerSettings]\nServerAdminPassword=pw\n",
        )

        inject_lacc_to_server_config(
            server_dir, WS_URL_UNQUOTED, "tok", "Map1", _logger
        )

        content = gus.read_text(encoding="utf-8")
        assert "[LACC]" in content
        assert f'URL="{WS_URL_UNQUOTED}"' in content
        assert "Token=tok" in content
        assert 'Name="Map1"' in content

    def test_inject_preserves_url_with_double_slashes(self, tmp_path: Path):
        """直接注入的 URL 必须保留 ://"""
        server_dir = tmp_path / "server"
        gus = self._make_server_gus(server_dir, "[ServerSettings]\nKey=Val\n")

        inject_lacc_to_server_config(
            server_dir, "ws://192.168.1.100:9999", "t", "S", _logger
        )

        content = gus.read_text(encoding="utf-8")
        assert 'URL="ws://192.168.1.100:9999"' in content

    def test_inject_replaces_truncated_url(self, tmp_path: Path):
        """模拟 UE5 截断后重新注入：URL=ws: → URL=ws://127.0.0.1:8000"""
        server_dir = tmp_path / "server"
        gus = self._make_server_gus(
            server_dir,
            "[ServerSettings]\nServerAdminPassword=pw\n\n"
            "[LACC]\nURL=ws:\nToken=old\nName=OldMap\n",
        )

        inject_lacc_to_server_config(
            server_dir, WS_URL_UNQUOTED, "newtok", "NewMap", _logger
        )

        content = gus.read_text(encoding="utf-8")
        assert f'URL="{WS_URL_UNQUOTED}"' in content
        assert "Token=newtok" in content
        assert 'Name="NewMap"' in content

    def test_inject_does_not_duplicate_sections(self, tmp_path: Path):
        """多次注入不会产生重复的 [LACC] 段"""
        server_dir = tmp_path / "server"
        gus = self._make_server_gus(server_dir, "[ServerSettings]\nKey=Val\n")

        for port in [8000, 8001, 8002]:
            inject_lacc_to_server_config(
                server_dir, f"ws://127.0.0.1:{port}", "t", "S", _logger
            )

        content = gus.read_text(encoding="utf-8")
        assert content.count("[LACC]") == 1
        assert 'URL="ws://127.0.0.1:8002"' in content


class TestEndToEndWithReinject:
    """端到端测试：inject_lacc_ini → ensure → apply → reinject"""

    GUS_REL = "ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini"

    def _simulate_inject_lacc_ini(
        self, ini_path: Path, ws_url: str, token: str, map_name: str
    ):
        import re

        lacc_section = (
            f"\n[LACC]\n"
            f'URL="{ws_url}"\n'
            f"Token={token}\n"
            f'Name="{map_name}"\n'
        )

        if ini_path.exists():
            content = ini_path.read_text(encoding="utf-8-sig")
        else:
            content = ""

        if "[LACC]" in content:
            content = re.sub(
                r"\[LACC\][^\[]*",
                lacc_section.lstrip("\n") + "\n",
                content,
                count=1,
            )
        else:
            content = content.rstrip() + "\n" + lacc_section

        ini_path.parent.mkdir(parents=True, exist_ok=True)
        ini_path.write_text(content, encoding="utf-8")

    def _simulate_ensure(self, ini_path: Path):
        parser = INIParser()
        parser.parse_file(ini_path)
        parser.set("ServerSettings", "ServerAdminPassword", "admin")
        parser.set("ServerSettings", "RCONEnabled", "True")
        parser.set("ServerSettings", "RCONPort", "27020")
        parser.set("/Script/Engine.GameSession", "MaxPlayers", "70")
        parser.save_file(ini_path)

    def _simulate_ue5_truncation(self, ini_path: Path):
        """模拟 UE5 引擎将 // 视为注释并截断 URL"""
        content = ini_path.read_text(encoding="utf-8")
        truncated = []
        for line in content.splitlines():
            idx = line.find("//")
            if idx >= 0:
                line = line[:idx].rstrip()
            truncated.append(line)
        ini_path.write_text("\n".join(truncated), encoding="utf-8")

    def test_full_pipeline_survives_ue5_truncation(self, tmp_path: Path):
        """完整流程：inject → ensure → copy → UE5 截断 → reinject → URL 正确"""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        server_dir = tmp_path / "server"
        server_gus_dir = server_dir / self.GUS_REL
        server_gus_dir.parent.mkdir(parents=True, exist_ok=True)

        staging_gus = staging_dir / "GameUserSettings.ini"
        server_gus = server_gus_dir  # 就是 GameUserSettings.ini 文件路径

        ws_url = "ws://127.0.0.1:8000"
        token = "secret"
        name = "TheIsland"

        # Step 1: 自动配置写入 staging
        self._simulate_inject_lacc_ini(staging_gus, ws_url, token, name)
        assert 'URL="ws://127.0.0.1:8000"' in staging_gus.read_text()

        # Step 2: ensure_required_server_settings 处理 staging（INIParser 保留 URL）
        self._simulate_ensure(staging_gus)
        assert 'URL="ws://127.0.0.1:8000"' in staging_gus.read_text()

        # Step 3: apply_staging_to_server 复制到服务器目录
        shutil.copy2(staging_gus, server_gus)
        assert 'URL="ws://127.0.0.1:8000"' in server_gus.read_text()

        # Step 4: 模拟 UE5 引擎截断 // 注释
        self._simulate_ue5_truncation(server_gus)
        truncated_content = server_gus.read_text()
        assert "ws://127.0.0.1:8000" not in truncated_content, \
            "UE5 模拟截断应该已移除 //"

        # Step 5: reinject 修复截断（核心修复步骤）
        inject_lacc_to_server_config(server_dir, ws_url, token, name, _logger)

        final_content = server_gus.read_text()
        assert f'URL="{ws_url}"' in final_content, (
            f"reinject 后 URL 应该完整。实际内容:\n{final_content}"
        )
        assert f"Token={token}" in final_content
        assert f'Name="{name}"' in final_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
