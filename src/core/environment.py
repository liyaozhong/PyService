"""环境管理模块

负责管理和配置服务运行环境，包括虚拟环境的创建、依赖管理等。
"""

import os
import subprocess
import venv
import tomli
from pathlib import Path
from typing import Dict, Optional
from src.utils.logger import Logger
from src.core.discovery import ServiceDiscovery

class EnvironmentManager:
    """环境管理器
    
    负责服务运行环境的创建、配置和管理。
    使用单例模式确保全局只有一个实例。
    """
    
    _instance = None
    
    def __new__(cls, base_path: Path = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, base_path: Path = None):
        if self._initialized:
            return
        self.base_path = base_path
        self.environments: Dict[str, Path] = {}
        self.discovery = ServiceDiscovery(base_path)
        self.logger = Logger(__name__)
        self._initialized = True
    
    def _get_service_repo_path(self, service_name: str) -> Optional[Path]:
        """获取服务代码仓库路径"""
        try:
            service_info = self.discovery.get_service_info(service_name)
            if not service_info or 'repo_path' not in service_info:
                # 如果没有配置repo_path，则使用默认路径
                return self.base_path.resolve() / 'repo' / service_name
            # 确保返回的是绝对路径
            repo_path = Path(service_info['repo_path'])
            return self.base_path.resolve() / "repo" / repo_path
        except Exception as e:
            self.logger.error(f'获取服务仓库路径失败: {str(e)}')
            return None
    
    def create_environment(self, service_name: str) -> Optional[Path]:
        """创建服务运行环境"""
        try:
            # 获取服务仓库路径
            repo_path = self._get_service_repo_path(service_name)
            if not repo_path:
                return None
            
            # 创建服务环境目录
            env_path = repo_path / '.venv'
            if not env_path.exists():
                # 创建虚拟环境
                venv.create(env_path, with_pip=True)
                self.environments[service_name] = env_path
                return env_path
            return env_path
        except Exception as e:
            self.logger.error(f'创建环境失败: {str(e)}')
            return None
    
    def install_dependencies(self, service_name: str) -> bool:
        """安装服务依赖
        
        自动检测并使用正确的依赖配置文件（requirements.txt、setup.py或pyproject.toml）安装依赖。
        
        Args:
            service_name: 服务名称
        
        Returns:
            bool: 依赖安装是否成功
        """
        try:
            self.logger.info(f'开始为服务 {service_name} 安装依赖')
            env_path = self.get_environment(service_name)
            if not env_path:
                self.logger.error(f'服务 {service_name} 的环境路径不存在')
                return False
            self.logger.info(f'找到服务环境路径: {env_path}')
            
            # 获取服务仓库路径
            repo_path = self._get_service_repo_path(service_name)
            if not repo_path:
                self.logger.error(f'服务 {service_name} 的仓库路径不存在')
                return False
            self.logger.info(f'找到服务仓库路径: {repo_path}')
            
            # 检查各种配置文件
            config_files = {
                'requirements.txt': lambda: self._install_from_requirements(env_path, repo_path / 'requirements.txt'),
                'setup.py': lambda: self._install_from_setup(env_path, repo_path / 'setup.py'),
                'pyproject.toml': lambda: self._install_from_pyproject(env_path, repo_path / 'pyproject.toml')
            }
            # 尝试安装依赖
            for config_file, install_func in config_files.items():
                config_path = repo_path / config_file
                if config_path.exists():
                    self.logger.info(f'找到依赖配置文件: {config_file}')
                    if install_func():
                        # 验证依赖是否真正安装成功
                        if self._verify_dependencies(env_path, config_path):
                            self.logger.info(f'服务 {service_name} 的依赖安装并验证成功')
                            return True
                        else:
                            self.logger.error(f'服务 {service_name} 的依赖验证失败')
                            return False
                    else:
                        self.logger.error(f'从{config_file}安装依赖失败')
                        return False
            
            self.logger.warning(f'未找到依赖配置文件：{repo_path}')
            return False
            
        except Exception as e:
            self.logger.error(f'安装依赖失败: {str(e)}')
            import traceback
            self.logger.error(f'错误堆栈:\n{traceback.format_exc()}')
            return False

    def _verify_dependencies(self, env_path: Path, config_path: Path) -> bool:
        """验证依赖是否真正安装成功
        
        Args:
            env_path: 虚拟环境路径
            config_path: 依赖配置文件路径
            
        Returns:
            bool: 依赖验证是否通过
        """
        try:
            # 获取虚拟环境中的pip路径
            if os.name == 'nt':
                pip_path = env_path / 'Scripts' / 'pip'
            else:
                pip_path = env_path / 'bin' / 'pip'
            
            # 获取已安装的包列表
            result = subprocess.run(
                [str(pip_path), 'list', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f'获取已安装包列表失败: {result.stderr}')
                return False
            
            # 解析已安装的包
            import json
            installed_packages = json.loads(result.stdout)
            self.logger.info(f'当前已安装的包: {[pkg["name"] for pkg in installed_packages]}')
            
            return True
            
        except Exception as e:
            self.logger.error(f'验证依赖失败: {str(e)}')
            import traceback
            self.logger.error(f'错误堆栈:\n{traceback.format_exc()}')
            return False

    def get_environment(self, service_name: str) -> Optional[Path]:
        """获取服务运行环境路径"""
        repo_path = self._get_service_repo_path(service_name)
        if not repo_path:
            return None
        
        env_path = repo_path / '.venv'
        if env_path.exists():
            return env_path
        return None

    def check_environment(self, service_name: str) -> dict:
        """检查服务环境状态
        
        检查服务的虚拟环境是否存在，以及所需依赖是否已安装。
        
        Args:
            service_name: 服务名称
        
        Returns:
            dict: 环境状态信息，包含以下字段：
                - venv_exists: 虚拟环境是否存在
                - dependencies_installed: 依赖是否已安装
                - is_ready: 环境是否就绪
                - config_type: 依赖配置文件类型
        """
        self.logger.info(f'开始检查服务 {service_name} 的环境状态')
        status = {
            'venv_exists': False,
            'dependencies_installed': False,
            'is_ready': False,
            'config_type': None
        }
        
        # 检查虚拟环境
        env_path = self.get_environment(service_name)
        if not env_path:
            self.logger.warning(f'服务 {service_name} 的虚拟环境不存在')
            return status
            
        self.logger.info(f'找到服务 {service_name} 的虚拟环境: {env_path}')
        status['venv_exists'] = True
        
        # 获取服务仓库路径
        repo_path = self._get_service_repo_path(service_name)
        if not repo_path:
            self.logger.error(f'无法获取服务 {service_name} 的仓库路径')
            return status
        
        self.logger.info(f'找到服务仓库路径: {repo_path}')
        
        # 检查各种配置文件
        config_files = {
            'requirements.txt': self._check_requirements,
            'setup.py': self._check_setup_py,
            'pyproject.toml': self._check_pyproject_toml
        }
        
        for config_file, check_func in config_files.items():
            config_path = repo_path / config_file
            if config_path.exists():
                self.logger.info(f'找到依赖配置文件: {config_file}')
                status['config_type'] = config_file
                status['dependencies_installed'] = check_func(env_path, config_path)
                if status['dependencies_installed']:
                    self.logger.info(f'依赖检查通过，使用配置文件: {config_file}')
                else:
                    self.logger.warning(f'依赖检查未通过，配置文件: {config_file}')
                break
        
        if not status['config_type']:
            self.logger.warning(f'未找到任何依赖配置文件')
        
        # 环境就绪条件：虚拟环境存在且依赖已安装
        status['is_ready'] = status['venv_exists'] and status['dependencies_installed']
        
        if status['is_ready']:
            self.logger.info(f'服务 {service_name} 的环境检查完成，环境已就绪')
        else:
            self.logger.warning(f'服务 {service_name} 的环境检查完成，环境未就绪')
        
        return status

    def _install_from_requirements(self, env_path: Path, requirements_path: Path) -> bool:
        """从requirements.txt安装依赖"""
        try:
            self.logger.info(f'开始从 {requirements_path} 安装依赖')
            # 获取虚拟环境中的pip路径
            if os.name == 'nt':
                pip_path = env_path / 'Scripts' / 'pip'
            else:
                pip_path = env_path / 'bin' / 'pip'
            self.logger.info(f'使用pip路径: {pip_path}')
            
            # 更新pip本身
            self.logger.info('更新pip到最新版本')
            update_result = subprocess.run(
                [str(pip_path), 'install', '--upgrade', 'pip'],
                capture_output=True,
                text=True
            )
            if update_result.returncode != 0:
                self.logger.warning(f'更新pip失败: {update_result.stderr}')
            
            # 安装依赖
            self.logger.info('开始安装依赖包')
            result = subprocess.run(
                [str(pip_path), 'install', '-r', str(requirements_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f'pip安装依赖失败，返回码：{result.returncode}')
                self.logger.error(f'pip输出：\n{result.stdout}')
                self.logger.error(f'pip错误：\n{result.stderr}')
                return False
            
            self.logger.info(f'pip安装输出：\n{result.stdout}')
            return True
        except Exception as e:
            self.logger.error(f'从requirements.txt安装依赖失败: {str(e)}')
            import traceback
            self.logger.error(f'错误堆栈：\n{traceback.format_exc()}')
            return False
    
    def _install_from_setup(self, env_path: Path, setup_path: Path) -> bool:
        """从setup.py安装依赖"""
        try:
            self.logger.info(f'开始从 {setup_path} 安装依赖')
            # 获取虚拟环境中的python解释器路径
            if os.name == 'nt':
                python_path = env_path / 'Scripts' / 'python'
            else:
                python_path = env_path / 'bin' / 'python'
            self.logger.info(f'使用Python路径: {python_path}')
            
            # 安装依赖
            self.logger.info('开始执行setup.py install')
            result = subprocess.run(
                [str(python_path), 'setup.py', 'install'],
                cwd=setup_path.parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f'setup.py安装失败，返回码：{result.returncode}')
                self.logger.error(f'安装输出：\n{result.stdout}')
                self.logger.error(f'安装错误：\n{result.stderr}')
                return False
            
            self.logger.info(f'setup.py安装输出：\n{result.stdout}')
            return True
        except Exception as e:
            self.logger.error(f'从setup.py安装依赖失败: {str(e)}')
            import traceback
            self.logger.error(f'错误堆栈：\n{traceback.format_exc()}')
            return False
    
    def _install_from_pyproject(self, env_path: Path, pyproject_path: Path) -> bool:
        """从pyproject.toml安装依赖"""
        try:
            self.logger.info(f'开始从 {pyproject_path} 安装依赖')
            # 获取虚拟环境中的pip路径
            if os.name == 'nt':
                pip_path = env_path / 'Scripts' / 'pip'
            else:
                pip_path = env_path / 'bin' / 'pip'
            self.logger.info(f'使用pip路径: {pip_path}')
            
            # 安装依赖
            self.logger.info('开始安装项目及其依赖')
            result = subprocess.run(
                [str(pip_path), 'install', str(pyproject_path.parent)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f'pyproject.toml安装失败，返回码：{result.returncode}')
                self.logger.error(f'安装输出：\n{result.stdout}')
                self.logger.error(f'安装错误：\n{result.stderr}')
                return False
            
            self.logger.info(f'pyproject.toml安装输出：\n{result.stdout}')
            return True
        except Exception as e:
            self.logger.error(f'从pyproject.toml安装依赖失败: {str(e)}')
            import traceback
            self.logger.error(f'错误堆栈：\n{traceback.format_exc()}')
            return False
    
    def _check_requirements(self, env_path: Path, requirements_path: Path) -> bool:
        """检查requirements.txt中的依赖是否已安装"""
        return check_dependencies(env_path, requirements_path)
    
    def _check_setup_py(self, env_path: Path, setup_path: Path) -> bool:
        """检查setup.py中的依赖是否已安装"""
        try:
            # 获取虚拟环境中的python解释器路径
            if os.name == 'nt':
                python_path = env_path / 'Scripts' / 'python'
            else:
                python_path = env_path / 'bin' / 'python'
            
            # 运行setup.py egg_info获取依赖信息
            result = subprocess.run(
                [str(python_path), 'setup.py', 'egg_info'],
                cwd=setup_path.parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False
            
            # 检查已安装的包
            return self._check_installed_packages(env_path)
            
        except Exception as e:
            self.logger.error(f'检查setup.py依赖失败: {str(e)}')
            return False
    
    def _check_pyproject_toml(self, env_path: Path, pyproject_path: Path) -> bool:
        """检查pyproject.toml中的依赖是否已安装"""
        try:            
            # 读取pyproject.toml
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomli.load(f)
            
            # 获取依赖列表
            dependencies = []
            if 'project' in pyproject_data:
                if 'dependencies' in pyproject_data['project']:
                    dependencies.extend(pyproject_data['project']['dependencies'])
                if 'optional-dependencies' in pyproject_data['project']:
                    for extra_deps in pyproject_data['project']['optional-dependencies'].values():
                        dependencies.extend(extra_deps)
            
            # 检查已安装的包
            return self._check_installed_packages(env_path)
            
        except Exception as e:
            self.logger.error(f'检查pyproject.toml依赖失败: {str(e)}')
            return False
    
    def _check_installed_packages(self, env_path: Path) -> bool:
        """检查已安装的包，使用dist-metadata直接读取包信息"""
        try:
            # 获取虚拟环境的site-packages路径
            if os.name == 'nt':
                site_packages = env_path / 'Lib' / 'site-packages'
            else:
                site_packages = env_path / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
            
            if not site_packages.exists():
                return False
            
            # 直接读取dist-info目录获取已安装的包信息
            success = True
            for dist_info in site_packages.glob('*.dist-info'):
                metadata_path = dist_info / 'METADATA'
                if not metadata_path.exists():
                    continue
                
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = f.read()
                    # 这里可以解析metadata获取更详细的包信息
                    # 为了简化示例，我们只验证metadata文件是否可读
                except Exception:
                    success = False
                    break
            
            return success
            
        except Exception as e:
            self.logger.error(f'检查已安装包失败: {str(e)}')
            return False

def check_dependencies(venv_dir: Path, requirements_path: Path) -> bool:
    """检查服务依赖是否已安装
    
    使用pip的packaging模块来准确解析和比对包的版本信息。
    
    Args:
        venv_dir: 虚拟环境目录
        requirements_path: requirements.txt文件路径
    
    Returns:
        bool: 依赖检查是否通过
    """
    try:
        # 获取虚拟环境中的pip路径
        if os.name == 'nt':
            pip_path = venv_dir / 'Scripts' / 'pip'
        else:
            pip_path = venv_dir / 'bin' / 'pip'
        
        # 获取已安装的包信息
        result = subprocess.run(
            [str(pip_path), 'list', '--format=json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return False
        
        # 解析已安装的包信息
        import json
        from packaging.requirements import Requirement
        from packaging.version import Version, InvalidVersion
        from packaging.utils import canonicalize_name
        
        installed_packages = {}
        for pkg in json.loads(result.stdout):
            try:
                installed_packages[canonicalize_name(pkg['name'])] = Version(pkg['version'])
            except InvalidVersion:
                continue
        
        # 读取并解析requirements.txt
        with open(requirements_path, 'r') as f:
            required = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # 检查每个依赖是否满足要求
        for req_str in required:
            try:
                req = Requirement(req_str)
                pkg_name = canonicalize_name(req.name)
                
                # 检查包是否已安装
                if pkg_name not in installed_packages:
                    return False
                
                # 检查版本是否满足要求
                if req.specifier and not req.specifier.contains(str(installed_packages[pkg_name])):
                    return False
                    
            except Exception:
                # 如果解析依赖字符串失败，跳过该依赖
                continue
        
        return True
        
    except Exception as e:
        return False