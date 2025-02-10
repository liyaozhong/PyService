"""基础服务类

定义服务的基本接口和行为，所有具体服务都应继承此类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import sys
import json
import subprocess
from pathlib import Path
from src.core.environment import EnvironmentManager

class BaseService(ABC):
    # 配置日志输出
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    def __init__(self):
        self.is_running = False
        # 初始化环境管理器
        self.env_manager = EnvironmentManager(Path(self._get_root_path()))
    
    def config(self, config: Dict[str, Any]):
        self.config = config or {}
        # 从配置中获取服务名称
        if not self.config.get('repo_path'):
            raise ValueError('配置中缺少服务名称(repo_path)字段')
        self.service_name = self.config['repo_path']
        self.logger.info(f"初始化服务，服务名称: {self.service_name}")
        self.logger.debug(f"服务配置信息: {self.config}")

    def _get_root_path(self) -> str:
        """获取项目根目录路径"""
        return str(Path(__file__).parent.parent.parent.parent)
    
    def get_repo_path(self) -> str:
        """获取repo目录的绝对路径"""
        return str(Path(self._get_root_path()) / 'repo' / self.service_name)
    
    async def start(self) -> bool:
        """启动服务"""
        try:
            self.is_running = True
            return True
        except Exception:
            return False
    
    async def stop(self) -> bool:
        """停止服务"""
        try:
            self.is_running = False
            return True
        except Exception:
            return False
    
    def execute_script(self, script: str) -> Any:
        """在独立的Python进程中执行脚本
        
        Args:
            script: 要执行的Python脚本内容
            env_name: 环境名称
            
        Returns:
            执行结果
            
        Raises:
            HTTPException: 执行失败时抛出
        """
        try:
            # 获取服务自己的虚拟环境路径
            env_path = Path(self.get_repo_path()) / '.venv'
            if not env_path.exists():
                self.logger.error("服务虚拟环境不存在")
                raise ValueError('服务虚拟环境不存在')
            self.logger.debug(f"使用Python解释器路径: {env_path}")
            
            python_path = env_path / 'bin' / 'python' if sys.platform != 'win32' else env_path / 'Scripts' / 'python.exe'
            
            # 在独立的Python进程中执行脚本
            result = subprocess.run(
                [str(python_path), '-c', script],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析输出结果
            try:
                output = json.loads(result.stdout)
                self.logger.info(f"服务执行结果: {output}")
                if 'error' in output:
                    self.logger.error(f"脚本执行发生错误: {output['error']}")
                    raise ValueError(output['error'])
                return output.get('result')
            except json.JSONDecodeError:
                self.logger.error("无法解析脚本执行结果的JSON输出")
                raise Exception(status_code=500, detail="无法解析脚本执行结果")
                
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip() if e.stderr else "无错误输出"
            self.logger.error(f"脚本执行失败: {e}\n错误输出: {error_output}")
            import traceback
            self.logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            raise Exception(status_code=500, detail=f"脚本执行失败: {e}\n错误输出: {error_output}")
        except Exception as e:
            self.logger.error(f"服务发生未预期的错误: {e}")
            raise Exception(status_code=500, detail=str(e))
    
    @abstractmethod
    def get_script(self, params: Dict) -> str:
        """生成要执行的脚本内容
        
        Args:
            params: 服务调用参数
            
        Returns:
            生成的Python脚本内容
        """
        pass
    
    async def execute(self, params: Dict[str, Any]) -> Any:
        """执行服务调用
        
        Args:
            params: 服务调用参数
            
        Returns:
            服务执行结果
        """
        self.logger.info(f"接收到服务请求，参数: {params}")
        script = self.get_script(params)
        self.logger.debug(f"服务执行脚本: {script}")
        return self.execute_script(script)