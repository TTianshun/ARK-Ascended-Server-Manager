"""
日志管理
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class Logger:
    """日志管理器"""
    
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def setup(cls, log_dir: Path, log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
        """初始化日志系统"""
        if cls._logger is not None:
            return cls._logger
        
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / log_file
        
        logger = logging.getLogger("ark_asa_manager")
        logger.setLevel(level)
        
        # 文件处理器(带轮转)
        fh = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        fh.setLevel(logging.DEBUG)
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        cls._logger = logger
        return logger


def setup_logger(log_dir: Path, log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """设置日志"""
    return Logger.setup(log_dir, log_file, level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name or "ark_asa_manager")
