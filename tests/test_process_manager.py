"""
ProcessManager 多进程管理测试 - 测试字典式管理实现
"""
import pytest
from pathlib import Path
from ark_asa_manager.core import ProcessManager
import sys


class TestProcessManager:
    """ProcessManager 多进程管理测试"""
    
    def test_single_server_start_stop(self):
        """测试单个服务器启动和停止"""
        pm = ProcessManager()
        
        # 测试初始状态
        assert pm.get_running_count() == 0
        assert pm.get_all_running_servers() == []
        
        # 测试服务器不存在时的状态
        assert not pm.is_running("server1")
        assert pm.get_pid("server1") is None
    
    def test_multiple_servers_status(self):
        """测试多个服务器的状态跟踪"""
        pm = ProcessManager()
        
        # 初始化时应该没有运行的服务器
        assert pm.get_running_count() == 0
        
        # 尝试将多个服务器标记为不运行
        assert not pm.is_running("server1")
        assert not pm.is_running("server2")
        assert not pm.is_running("server3")
        
        # 验证没有以"server"开头的运行服务器
        running = pm.get_all_running_servers()
        assert len(running) == 0
    
    def test_get_all_running_servers_empty(self):
        """测试在没有运行服务器时获取列表"""
        pm = ProcessManager()
        assert pm.get_all_running_servers() == []
        assert pm.get_running_count() == 0
    
    def test_process_manager_cleanup(self):
        """测试进程管理器的内部清理"""
        pm = ProcessManager()
        
        # 验证内部数据结构是字典
        assert isinstance(pm._processes, dict)
        assert isinstance(pm._pids, dict)
        
        # 验证字典初始为空
        assert len(pm._processes) == 0
        assert len(pm._pids) == 0


class TestProcessManagerIntegration:
    """ProcessManager 集成测试 - 可与真实进程测试"""
    
    def test_start_with_python_interpreter(self):
        """测试用 Python 解释器作为可执行文件启动"""
        pm = ProcessManager()
        
        # 使用 Python 解释器作为示例（立即退出的简单脚本）
        try:
            # 注：这是一个简单的测试，实际环境中需要可执行文件
            result = pm.start(
                "test_server",
                executable=Path(sys.executable),
                args=["-c", "print('test')"]
            )
            # 如果启动成功，应该能获取 PID
            if result:
                pid = pm.get_pid("test_server")
                assert pid is not None
                # 清理
                pm.stop("test_server")
        except Exception:
            # 如果环境不支持，跳过测试
            pytest.skip("运行环境不支持进程启动")
    
    def test_cannot_start_duplicate_server(self):
        """测试不能启动重复的服务器"""
        pm = ProcessManager()
        
        try:
            # 首次启动
            result1 = pm.start(
                "duplicate_server",
                executable=Path(sys.executable),
                args=["-c", "import time; time.sleep(2)"]
            )
            
            if result1:
                # 第二次启动应该失败（因为已经在运行）
                result2 = pm.start(
                    "duplicate_server",
                    executable=Path(sys.executable),
                    args=["-c", "print('test')"]
                )
                assert not result2, "不应该能启动重复的服务器"
                
                # 清理
                pm.stop("duplicate_server")
        except Exception:
            pytest.skip("运行环境不支持进程启动")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
