"""服务元数据管理模块

负责管理服务的元数据信息，包括服务配置、版本等。
"""

from typing import Dict, Optional, Any
from pathlib import Path
import json
from src.utils.logger import logger

class ServiceMetadataManager:
    """服务元数据管理器
    
    负责管理服务的元数据信息，提供元数据的读取和更新功能。
    """
    
    def __init__(self, repo_path: Path):
        if not repo_path:
            raise ValueError("repo_path不能为空")
        self.repo_path = repo_path.resolve()
        self.metadata_cache: Dict[str, dict] = {}
    
    def get_service_metadata(self, service_name: str) -> Optional[dict]:
        """获取服务元数据"""
        if service_name in self.metadata_cache:
            return self.metadata_cache[service_name]
        
        service_dir = self.repo_path / service_name
        metadata_path = service_dir / 'service.json'
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.metadata_cache[service_name] = metadata
                return metadata
        except Exception as e:
            logger.error(f'读取服务元数据失败: {str(e)}')
            return None
    
    def get_service_implementation_path(self, service_name: str) -> Optional[Path]:
        """获取服务实现文件路径
        
        Args:
            service_name: 服务名称
            
        Returns:
            Optional[Path]: 服务实现文件路径，如果不存在则返回None
        """
        service_dir = self.repo_path / service_name
        service_path = service_dir / 'service.py'
        return service_path if service_path.exists() else None
    
    def get_service_config_path(self, service_name: str) -> Optional[Path]:
        """获取服务配置文件路径
        
        Args:
            service_name: 服务名称
            
        Returns:
            Optional[Path]: 服务配置文件路径，如果不存在则返回None
        """
        service_dir = self.repo_path / service_name
        config_path = service_dir / 'service.json'
        return config_path if config_path.exists() else None
    
    def get_service_dir(self, service_name: str) -> Optional[Path]:
        """获取服务目录路径
        
        Args:
            service_name: 服务名称
            
        Returns:
            Optional[Path]: 服务目录路径，如果不存在则返回None
        """
        service_dir = self.repo_path / service_name
        return service_dir if service_dir.exists() else None
    
    def update_service_metadata(self, service_name: str, metadata: dict) -> bool:
        """更新服务元数据"""
        try:
            service_dir = self.repo_path / service_name
            metadata_path = service_dir / 'service.json'
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            
            self.metadata_cache[service_name] = metadata
            return True
        except Exception as e:
            logger.error(f'更新服务元数据失败: {str(e)}')
            return False
    
    def clear_metadata_cache(self, service_name: Optional[str] = None) -> None:
        """清除元数据缓存"""
        if service_name:
            self.metadata_cache.pop(service_name, None)
        else:
            self.metadata_cache.clear()
            
    def parse_service_metadata(self, service_path: Path) -> Optional[dict]:
        """解析服务定义文件
        
        Args:
            service_path: 服务目录路径
            
        Returns:
            Optional[dict]: 服务元数据信息，如果解析失败则返回None
        """
        try:
            metadata_path = service_path / 'service.json'
            if not metadata_path.exists():
                logger.warning(f'服务定义文件不存在: {metadata_path}')
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            if self._validate_metadata(metadata):
                return metadata
            return None
        except Exception as e:
            logger.error(f'解析服务定义失败: {str(e)}')
            return None
            
    def _validate_metadata(self, metadata: dict) -> bool:
        """验证服务元数据"""
        required_fields = ['name', 'version', 'api_routes', 'dependencies']
        for field in required_fields:
            if field not in metadata:
                logger.warning(f'服务定义缺少必需字段: {field}')
                return False
        return True