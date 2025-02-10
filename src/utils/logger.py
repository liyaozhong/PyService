"""日志工具模块

提供统一的日志记录功能，支持不同级别的日志输出和灵活的配置。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

class Logger:
    """日志工具类
    
    提供统一的日志记录接口，支持输出到控制台和文件。
    """
    
    def __init__(self, name: str, log_file: Optional[str] = None, level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 如果指定了日志文件，添加文件处理器
        if log_file:
            log_dir = Path(log_file).parent
            if not log_dir.exists():
                log_dir.mkdir(parents=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """记录调试级别日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录信息级别日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告级别日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误级别日志"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误级别日志"""
        self.logger.critical(message)

# 创建默认的logger实例
logger = Logger('pyservice')