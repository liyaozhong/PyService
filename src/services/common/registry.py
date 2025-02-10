"""服务注册管理模块

负责提供服务注册接口，生成服务模板文件。
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from src.utils.logger import Logger

class ServiceRegistry:
    """服务注册管理器
    
    提供服务注册接口，生成服务模板文件。
    使用单例模式确保全局只有一个实例。
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.logger = Logger(__name__)
        self.implementations_dir = Path.cwd() / 'src' / 'services' / 'implementations'
        self._initialized = True
    
    def register_service(self, service_name: str, repo_path: Path) -> bool:
        """注册新服务
        
        Args:
            service_name: 服务名称
            repo_path: 服务仓库路径
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if not service_name or not repo_path:
                self.logger.error('服务名称或仓库路径不能为空')
                return False
            
            # 创建服务实现目录
            service_dir = self.implementations_dir / service_name
            service_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成service.json
            service_json = {
                'name': service_name,
                'version': '1.0.0',
                'api_routes': [
                    {
                        'path': '/calculate',
                        'method': 'POST',
                        'request_schema': {
                            'type': 'object',
                            'properties': {}
                        },
                        'response_schema': {
                            'type': 'object',
                            'properties': {}
                        }
                    }
                ],
                'dependencies': [],
                'repo_path': str(service_name)
            }
            self._create_service_json(service_dir, service_json)
            
            # 生成service.py
            self._create_service_py(service_dir, service_name)
            
            self.logger.info(f'服务{service_name}注册成功')
            return True
        except Exception as e:
            self.logger.error(f'注册服务{service_name}失败: {str(e)}')
            return False
    
    def _create_service_json(self, service_dir: Path, service_json: Dict) -> None:
        """创建service.json文件"""
        json_path = service_dir / 'service.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(service_json, f, indent=4, ensure_ascii=False)
    
    def _create_service_py(self, service_dir: Path, service_name: str) -> None:
        """创建service.py文件"""
        service_template = ""
        
        py_path = service_dir / 'service.py'
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(service_template)
    
    def get_service_status(self, service_name: str) -> Dict[str, str]:
        """获取服务注册状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict[str, str]: 包含服务注册状态的字典
                - status: 注册状态（'registered'已注册, 'unregistered'未注册, 'invalid'已失效）
                - message: 状态说明
        """
        try:
            self.logger.info(f'开始检查服务 {service_name} 的注册状态')
            
            # 1. 扫描 implementations 目录下所有服务的 service.json
            registered_repos = []
            for service_dir in self.implementations_dir.iterdir():
                if not service_dir.is_dir():
                    continue
                    
                service_json_path = service_dir / 'service.json'
                if not service_json_path.exists():
                    continue
                    
                try:
                    with open(service_json_path, 'r', encoding='utf-8') as f:
                        service_json = json.load(f)
                        repo_path = service_json.get('repo_path', '')
                        if repo_path:
                            registered_repos.append(repo_path)
                except json.JSONDecodeError as e:
                    self.logger.warning(f'服务配置文件 {service_json_path} 格式错误: {str(e)}')
                    continue
            
            # 2. 获取 repo 目录下的所有项目
            repo_dir = Path.cwd() / 'repo'
            if not repo_dir.exists() or not repo_dir.is_dir():
                self.logger.warning('repo目录不存在或无效')
                return {
                    'status': 'invalid',
                    'message': 'repo目录不存在或无效'
                }
            
            # 3. 检查当前服务的状态
            service_repo_dir = repo_dir / service_name
            if not service_repo_dir.exists() or not service_repo_dir.is_dir():
                # 服务目录不存在，检查是否在已注册列表中
                if service_name in registered_repos:
                    self.logger.info(f'服务 {service_name} 已失效（仓库已删除）')
                    return {
                        'status': 'invalid',
                        'message': '服务仓库已删除'
                    }
                else:
                    self.logger.info(f'服务 {service_name} 无效（仓库不存在）')
                    return {
                        'status': 'invalid',
                        'message': '服务仓库不存在'
                    }
            
            # 服务目录存在，检查是否已注册
            if service_name in registered_repos:
                self.logger.info(f'服务 {service_name} 已注册')
                return {
                    'status': 'registered',
                    'message': '服务已注册'
                }
            else:
                self.logger.info(f'服务 {service_name} 未注册')
                return {
                    'status': 'unregistered',
                    'message': '服务未注册'
                }
                
        except Exception as e:
            self.logger.error(f'获取服务{service_name}状态失败: {str(e)}')
            import traceback
            self.logger.error(f'错误堆栈:\n{traceback.format_exc()}')
            return {
                'status': 'invalid',
                'message': f'获取服务状态失败: {str(e)}'
            }
