"""服务发现模块

负责自动发现和加载服务定义，包括服务代码扫描、状态管理等功能。
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.logger import Logger
from src.core.metadata import ServiceMetadataManager

class ServiceDiscovery:
    """服务发现器
    
    负责扫描目录，发现服务并管理其状态。
    使用单例模式确保全局只有一个实例。
    """
    
    _instance = None
    
    def __new__(cls, repo_path: Path = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, repo_path: Path = None):
        if self._initialized:
            return
            
        self.services_path = Path(__file__).parent.parent / 'services' / 'implementations'
        self.services: Dict[str, Dict] = {}  # 服务信息字典
        self.logger = Logger(__name__)
        self._initialized = True
    
    def scan_services(self) -> List[Dict]:
        """扫描服务目录并返回服务基本信息列表
        
        返回的信息包含服务名称、路径和服务定义（如果存在）。
        服务状态检查应在调用此方法的地方进行处理。
        """
        try:
            self.logger.info(f'开始扫描服务目录: {self.services_path}')
            services_info = []
            # 扫描services目录下的所有子目录
            for item in os.scandir(self.services_path):
                if item.is_dir():
                    service_path = Path(item.path)
                    service_name = item.name
                    
                    # 获取服务定义信息
                    service_info = self.parse_service(service_path)
                    if service_info:
                        service_info['name'] = service_name
                        service_info['path'] = str(service_path)
                        self.services[service_name] = service_info
                        services_info.append(service_info)
                        self.logger.info(f'成功加载服务: {service_name}, 版本: {service_info.get("version", "未知")}')
                    else:
                        self.logger.warning(f'目录 {service_name} 不包含有效的服务定义')
            
            self.logger.info(f'服务扫描完成，共发现 {len(services_info)} 个有效服务')
            return services_info
        except Exception as e:
            self.logger.error(f'扫描服务失败: {str(e)}')
            return []
    
    def parse_service(self, service_path: Path) -> Optional[dict]:
        """解析服务定义"""
        metadata_manager = ServiceMetadataManager(service_path)
        return metadata_manager.parse_service_metadata(service_path)
    
    def get_service_info(self, service_name: str) -> Optional[dict]:
        """获取服务信息"""
        if service_name not in self.services:
            return None
        
        return self.services[service_name]