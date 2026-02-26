"""
Steam相关操作
"""
from pathlib import Path
from typing import Optional
from ..utils.downloader import Downloader


class SteamManager:
    """Steam管理器"""
    
    def __init__(self, steamcmd_dir: Path):
        self.steamcmd_dir = steamcmd_dir
        self.steamcmd_exe = steamcmd_dir / "steamcmd.exe"
    
    def is_installed(self) -> bool:
        """检查SteamCMD是否已安装"""
        return self.steamcmd_exe.exists()
    
    def install(self, url: str) -> bool:
        """安装SteamCMD"""
        try:
            from zipfile import ZipFile
            
            # 下载
            temp_zip = self.steamcmd_dir / "steamcmd_tmp.zip"
            downloader = Downloader()
            if not downloader.download(url, temp_zip):
                return False
            
            # 解压
            with ZipFile(temp_zip, 'r') as zf:
                zf.extractall(self.steamcmd_dir)
            
            temp_zip.unlink()
            return self.is_installed()
        except Exception as e:
            print(f"安装SteamCMD失败: {e}")
            return False
    
    def update_app(self, app_id: int, install_dir: Path) -> bool:
        """更新应用"""
        try:
            import subprocess
            
            args = [
                str(self.steamcmd_exe),
                "+force_install_dir",
                str(install_dir),
                "+login",
                "anonymous",
                "+app_update",
                str(app_id),
                "validate",
                "+quit",
            ]
            
            subprocess.run(args, check=True)
            return True
        except Exception as e:
            print(f"更新应用失败: {e}")
            return False