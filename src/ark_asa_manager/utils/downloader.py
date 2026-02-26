"""
文件下载管理
"""
import os
from pathlib import Path
from typing import Callable, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError
import time


class Downloader:
    """文件下载器"""
    
    def __init__(self, timeout: int = 180):
        self.timeout = timeout
    
    def download(
        self,
        url: str,
        destination: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        下载文件
        
        Args:
            url: 下载URL
            destination: 保存路径
            progress_callback: 进度回调 (downloaded_bytes, total_bytes)
        
        Returns:
            成功返回True
        """
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            req = Request(url)
            with urlopen(req, timeout=self.timeout) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                with open(destination, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)
            
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False
