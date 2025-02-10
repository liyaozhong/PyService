"""服务进程和执行管理模块

负责管理服务进程的创建、监控、执行和生命周期管理。
"""

import os
import subprocess
import requests
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from src.core.environment import EnvironmentManager
from src.core.discovery import ServiceDiscovery
from src.core.metadata import ServiceMetadataManager
from src.utils.logger import logger

class ServiceProcessManager:
    """服务进程管理器
    
    负责管理服务进程的创建、监控和生命周期管理。
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
        self.discovery = ServiceDiscovery()
        self.environment_manager = EnvironmentManager()
        services_path = self.discovery.services_path
        if not services_path:
            logger.error('无法获取服务路径')
            raise ValueError('无法获取服务路径')
        self.metadata_manager = ServiceMetadataManager(services_path)
        self.running_services: Dict[str, subprocess.Popen] = {}
        self._initialized = True
    
    def start_service(self, service_name: str, config: dict) -> dict:
        try:
            # 获取服务信息
            service_info = self.discovery.get_service_info(service_name)
            if not service_info:
                logger.error(f'服务 {service_name} 信息不存在')
                return {'success': False, 'error': f'服务 {service_name} 信息不存在'}
            
            logger.info(f'开始启动服务: {service_name}')
            logger.debug(f'服务配置信息: {service_info}')
            
            # 获取服务路径
            service_path = self.metadata_manager.get_service_implementation_path(service_name)
            if not service_path:
                logger.error(f'服务 {service_name} 实现文件不存在')
                return {'success': False, 'error': f'服务 {service_name} 实现文件不存在'}
            
            # 获取服务环境变量
            env_vars = service_info.get('environment', {}).get('env_vars', {})
            if not env_vars:
                logger.error(f'服务 {service_name} 未定义环境变量')
                return {'success': False, 'error': f'服务 {service_name} 未定义环境变量'}
            
            # 获取服务端口
            original_port = int(env_vars.get('PORT', 0))
            if not original_port:
                logger.error(f'服务 {service_name} 未定义端口')
                return {'success': False, 'error': f'服务 {service_name} 未定义端口'}
            
            # 检查端口是否被占用，如果被占用则尝试终止占用进程
            if self.is_port_in_use(original_port):
                logger.info(f'端口 {original_port} 被占用，尝试终止占用进程')
                if not self.kill_process_by_port(original_port):
                    logger.error(f'无法终止占用端口 {original_port} 的进程')
                    return {'success': False, 'error': f'无法终止占用端口 {original_port} 的进程'}
                logger.info(f'成功终止占用端口 {original_port} 的进程')
            
            port = original_port
            
            # 准备环境变量
            env = os.environ.copy()
            for key, value in {**env_vars, **config}.items():
                env[key] = str(value)
            
            # 准备启动命令
            cmd = [
                sys.executable,
                '-m', 'uvicorn',
                f'src.services.implementations.{service_name}.service:app',
                '--host', '0.0.0.0',
                '--port', str(port),
                '--log-level', 'info'
            ]
            
            # 创建日志目录和文件
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f'{service_name}.log'
            
            # 启动服务进程
            logger.info(f'启动服务进程: {" ".join(cmd)}')
            with open(log_file, 'w') as log_fp:
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    cwd=service_path.parent,
                    stdout=log_fp,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            # 等待服务启动
            max_retries = 10
            retry_interval = 0.5
            for i in range(max_retries):
                if process.poll() is not None:
                    # 进程已退出，读取日志文件获取错误信息
                    error_message = ''
                    try:
                        with open(log_file, 'r') as f:
                            error_message = f.read().strip()
                    except Exception as e:
                        logger.error(f'读取日志文件失败: {str(e)}')
                    
                    logger.error(f'服务进程异常退出，退出码: {process.returncode}，错误信息: {error_message}')
                    return {'success': False, 'error': f'服务进程异常退出，退出码: {process.returncode}，错误信息: {error_message}'}
                
                # 检查端口是否被进程占用
                if self.is_port_in_use(port):
                    # 检查进程是否还在运行
                    if process.poll() is None:
                        # 服务启动成功
                        server_status = {'is_ready': True, 'error': None}
                        # 保存服务信息
                        self.running_services[service_name] = {
                            'process': process,
                            'port': port,
                            'status': server_status,
                            'start_time': datetime.now().isoformat()
                        }
                        logger.info(f'服务 {service_name} 启动成功')
                        # 添加初始化请求重试机制
                        init_max_retries = 3
                        init_retry_interval = 0.5
                        init_url = f'http://localhost:{port}/init'
                        
                        for init_retry in range(init_max_retries):
                            try:
                                # 检查服务进程是否仍在运行
                                if process.poll() is not None:
                                    error_message = '服务进程已退出'
                                    logger.error(f'服务 {service_name} 初始化失败: {error_message}')
                                    return {'success': False, 'error': f'服务初始化失败: {error_message}'}
                                
                                response = requests.post(init_url, json=service_info)
                                response.raise_for_status()
                                logger.info(f'服务 {service_name} 初始化成功')
                                return {'success': True, 'port': port, 'status': 'running', 'message': f'服务已启动，监听端口: {port}'}
                            except Exception as e:
                                if init_retry < init_max_retries - 1:
                                    logger.warning(f'服务 {service_name} 初始化重试 ({init_retry + 1}/{init_max_retries}): {str(e)}')
                                    time.sleep(init_retry_interval)
                                else:
                                    logger.error(f'服务 {service_name} 初始化失败: {str(e)}')
                                    # 初始化失败，终止进程
                                    process.terminate()
                                    try:
                                        process.wait(timeout=5)
                                    except subprocess.TimeoutExpired:
                                        process.kill()
                                    return {'success': False, 'error': f'服务初始化失败: {str(e)}'}
                                        
                logger.info(f'等待服务启动 ({i+1}/{max_retries})...')
                time.sleep(retry_interval)
            
            # 启动超时，终止进程
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            logger.error('服务启动超时')
            return {'success': False, 'error': '服务启动超时'}
            
        except Exception as e:
            logger.error(f'启动服务进程失败: {str(e)}')
            import traceback
            logger.error(f'错误堆栈:\n{traceback.format_exc()}')
            return {'success': False, 'error': f'启动服务进程失败: {str(e)}'}
    
    def stop_service(self, service_name: str) -> bool:
        """停止服务进程"""
        try:
            if service_name in self.running_services:
                service_info = self.running_services[service_name]
                process = service_info['process']
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                del self.running_services[service_name]
                logger.info(f'服务 {service_name} 已停止')
                return True
            return False
        except Exception as e:
            logger.error(f'停止服务进程失败: {str(e)}')
            return False
    
    def get_service_status(self, service_name: str) -> Optional[dict]:
        """获取服务进程状态"""
        if service_name not in self.running_services:
            return None
        
        service_info = self.running_services[service_name]
        process = service_info['process']
        return {
            'running': process.poll() is None,
            'port': service_info['port'],
            'status': service_info['status'],
            'process': process
        }
    
    def monitor_service(self, service_name: str) -> Dict[str, Any]:
        """监控服务进程状态"""
        status = self.get_service_status(service_name)
        if not status:
            return {'status': 'not_running'}
        
        return {
            'status': 'running' if status['running'] else 'stopped',
            'process': status['process']
        }
    
    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用
        
        Args:
            port: 要检查的端口号
        
        Returns:
            bool: 端口是否被占用
        """
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return False
        except socket.error:
            return True
            
    def kill_process_by_port(self, port: int) -> bool:
        """终止占用指定端口的进程
        
        Args:
            port: 端口号
            
        Returns:
            bool: 是否成功终止进程
        """
        try:
            if sys.platform.startswith('win'):
                cmd = ['netstat', '-ano', '|', 'findstr', f':{port}']
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                if result.stdout:
                    pid = result.stdout.strip().split()[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
            else:
                cmd = ['lsof', '-ti', f':{port}']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout:
                    pid = result.stdout.strip()
                    subprocess.run(['kill', '-9', pid], capture_output=True)
            return True
        except Exception as e:
            logger.error(f'终止进程失败: {str(e)}')
            return False
            
    def execute_service(self, service_name: str, params: dict) -> Any:
        """执行服务调用
        
        通过HTTP请求调用已启动的服务API接口来执行服务。
        
        Args:
            service_name: 服务名称
            params: 服务执行参数
            
        Returns:
            Any: 服务执行结果
            
        Raises:
            ValueError: 服务不存在或未启动时抛出
        """
        try:
            logger.info(f'开始执行服务: {service_name}, 参数: {params}')
            
            # 检查服务是否存在且已启动
            if service_name not in self.running_services:
                logger.error(f'服务 {service_name} 未启动')
                raise ValueError(f'服务 {service_name} 未启动')
            
            # 获取服务元数据
            service_info = self.discovery.get_service_info(service_name)
            if not service_info or 'api_routes' not in service_info:
                logger.error(f'服务 {service_name} 元数据不完整')
                raise ValueError(f'服务 {service_name} 元数据不完整')
            
            # 获取服务API路由信息
            api_routes = service_info['api_routes']
            if not api_routes or not isinstance(api_routes, list):
                logger.error(f'服务 {service_name} 未定义API路由')
                raise ValueError(f'服务 {service_name} 未定义API路由')
            
            # 查找第一个POST路由作为执行路由
            execute_route = None
            for route in api_routes:
                execute_route = route
                break

            if not execute_route:
                logger.error(f'服务 {service_name} 未定义接口')
                raise ValueError(f'服务 {service_name} 未定义接口')
            
            # 构建请求URL
            base_url = f'http://localhost:{service_info["environment"]["env_vars"]["PORT"]}'
            execute_url = f'{base_url}{execute_route["path"]}'
            
            # 发送HTTP请求
            logger.debug(f'发送请求到服务接口: {execute_url}')
            response = requests.post(execute_url, json=params)
            response.raise_for_status()
            
            # 处理响应
            result = response.json()
            logger.info(f'服务 {service_name} 执行成功')
            return result
        except Exception as e:
            logger.error(f'执行服务失败: {str(e)}')
            raise
    
    def validate_service(self, service_name: str) -> bool:
        """验证服务是否可执行"""
        try:
            # 检查服务信息
            service_info = self.discovery.get_service_info(service_name)
            if not service_info:
                return False
            
            # 检查服务路径
            service_path = self.metadata_manager.get_service_implementation_path(service_name)
            if not service_path:
                return False
            
            return True
        except Exception as e:
            logger.error(f'验证服务失败: {str(e)}')
            return False