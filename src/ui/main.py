"""主页面模块

提供服务管理和执行的Web界面。
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any
from src.services.common.registry import ServiceRegistry
from src.core.process import ServiceProcessManager
from src.core.environment import EnvironmentManager
from src.core.discovery import ServiceDiscovery

def init_session_state():
    """初始化会话状态"""
    if 'registry' not in st.session_state:
        st.session_state.registry = ServiceRegistry()
    if 'env_manager' not in st.session_state:
        st.session_state.env_manager = EnvironmentManager(Path.cwd())
    if 'runtime' not in st.session_state:
        st.session_state.runtime = ServiceProcessManager()
    if 'discovery' not in st.session_state:
        st.session_state.discovery = ServiceDiscovery(Path.cwd() / 'repo')
    if 'services_cache' not in st.session_state:
        st.session_state.services_cache = None
    if 'running_services_cache' not in st.session_state:
        st.session_state.running_services_cache = {}
    if 'playground_cache' not in st.session_state:
        st.session_state.playground_cache = {
            'selected_service': None,
            'input_params': {}
        }

def render_service_list():
    """渲染服务列表"""
    st.header('服务列表')
    
    # 使用缓存的服务列表，只在必要时重新扫描
    if st.session_state.services_cache is None:
        st.session_state.services_cache = st.session_state.discovery.scan_services()
    services = st.session_state.services_cache
    
    if not services:
        st.info('当前没有可用的服务')
        return
    
    for service_info in services:
        service_name = service_info['name']
        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader(service_name)
            # 检查环境状态
            env_status = st.session_state.env_manager.check_environment(service_name)
            # 获取服务运行状态
            service_status = st.session_state.runtime.get_service_status(service_name)
            st.session_state.running_services_cache[service_name] = service_status
            
            # 根据环境状态和运行状态设置显示状态
            if not env_status['is_ready']:
                if env_status['venv_exists']:
                    status = '环境已创建，依赖未安装'
                else:
                    status = '已注册，环境未配置'
            else:
                if service_status and service_status.get('running'):
                    status = '运行中'
                else:
                    status = '就绪'
            
            version = service_info.get('version', '未知')
            st.markdown(f"**状态:** {status}")
            st.markdown(f"**版本:** {version}")
        
        with col2:
            # 根据环境状态和运行状态显示不同的操作按钮
            if env_status['is_ready']:
                # 从缓存中获取服务状态
                service_status = st.session_state.runtime.get_service_status(service_name)
                st.session_state.running_services_cache[service_name] = service_status
                
                if service_status and service_status.get('running'):
                    if st.button('停止', key=f'stop_{service_name}'):
                        if st.session_state.runtime.stop_service(service_name):
                            # 更新缓存
                            st.session_state.running_services_cache[service_name] = {
                                'pid': None,
                                'returncode': None,
                                'running': False
                            }
                            # 更新running_services_list缓存
                            if 'running_services_list' in st.session_state:
                                st.session_state.running_services_list = [
                                    s for s in st.session_state.running_services_list
                                    if s[0] != service_name
                                ]
                            st.success('服务已停止')
                            st.rerun()
                        else:
                            st.error('停止服务失败')
                else:
                    if st.button('启动', key=f'start_{service_name}'):
                        if st.session_state.runtime.start_service(service_name, {}):
                            # 更新缓存状态为运行中
                            st.session_state.running_services_cache[service_name] = {
                                'running': True,
                                'port': None,
                                'status': {'is_ready': True, 'error': None}
                            }
                            # 更新running_services_list缓存
                            if 'running_services_list' in st.session_state:
                                service_info = st.session_state.discovery.get_service_info(service_name)
                                if service_info:
                                    st.session_state.running_services_list.append((service_name, service_info))
                            st.success('服务启动成功')
                            st.rerun()
                        else:
                            st.error('服务启动失败')
            else:
                if st.button('配置环境', key=f'setup_{service_name}'):
                    # 创建环境
                    env_path = st.session_state.env_manager.create_environment(service_name)
                    if not env_path:
                        st.error('环境创建失败')
                        return
                    
                    # 安装依赖
                    if st.session_state.env_manager.install_dependencies(service_name):
                        st.success('环境配置成功')
                        # 清除缓存，强制重新扫描服务
                        st.session_state.services_cache = None
                        st.rerun()
                    else:
                        st.error('依赖安装失败')

def render_service_execution():
    """渲染服务执行界面"""
    if 'selected_service' not in st.session_state:
        return
    
    st.header('服务执行')
    service_name = st.session_state.selected_service
    
    # 检查服务是否存在
    service_info = st.session_state.discovery.get_service_info(service_name)
    if not service_info:
        st.error(f'服务 {service_name} 不存在')
        return
    
    # 配置输入参数
    st.subheader('输入参数')
    params: Dict[str, Any] = {}
    # TODO: 根据服务元数据动态生成参数输入界面
    
    if st.button('执行服务'):
        try:
            result = st.session_state.runtime.execute_service(service_name, params)
            # 更新服务状态缓存
            service_status = st.session_state.runtime.get_service_status(service_name)
            if service_status:
                st.session_state.running_services_cache[service_name] = service_status
            st.success('服务执行成功')
            st.json(result)
        except Exception as e:
            st.error(f'服务执行失败: {str(e)}')

def render_playground():
    """渲染Playground界面"""
    st.header('服务Playground')
    
    # 获取所有运行中的服务
    running_services = []
    # 优先使用缓存的运行中服务列表
    if 'running_services_list' not in st.session_state:
        st.session_state.running_services_list = []
        services = st.session_state.services_cache or st.session_state.discovery.scan_services()
        for service_info in services:
            service_name = service_info['name']
            service_status = st.session_state.runtime.get_service_status(service_name)
            if service_status and service_status.get('running'):
                running_services.append((service_name, service_info))
        st.session_state.running_services_list = running_services
    else:
        running_services = st.session_state.running_services_list
    
    if not running_services:
        st.info('没有正在运行的服务')
        # 清除playground缓存
        st.session_state.playground_cache = {
            'selected_service': None,
            'input_params': {}
        }
        return
    
    # 服务选择
    selected_service = st.selectbox(
        '选择服务',
        options=[s[0] for s in running_services],
        format_func=lambda x: x,
        key='playground_service_select'
    )
    
    # 更新选中的服务
    if selected_service != st.session_state.playground_cache['selected_service']:
        st.session_state.playground_cache['selected_service'] = selected_service
        st.session_state.playground_cache['input_params'] = {}
    
    # 获取选中服务的信息
    service_info = next(s[1] for s in running_services if s[0] == selected_service)
    
    # 显示API路由信息
    if 'api_routes' in service_info:
        route = service_info['api_routes'][0]  # 目前假设每个服务只有一个API路由
        st.subheader(f'API: {route["path"]} ({route["method"]})')
        
        # 根据请求schema生成输入表单
        st.markdown('### 请求参数')
        input_params = render_input_form(route.get('request_schema', {}), prefix='playground')
        
        # 更新输入参数缓存
        st.session_state.playground_cache['input_params'] = input_params
        
        # 执行按钮和结果显示
        if st.button('执行', key='execute_service'):
            try:
                result = st.session_state.runtime.execute_service(selected_service, input_params)
                st.success('执行成功')
                st.markdown('### 响应结果')
                render_response_data(route.get('response_schema', {}), result)
            except Exception as e:
                st.error(f'执行失败: {str(e)}')

def render_input_form(schema: dict, prefix: str = '') -> dict:
    """根据schema渲染输入表单
    
    Args:
        schema: 请求参数的JSON Schema
        prefix: 输入字段的前缀，用于区分不同表单的输入
        
    Returns:
        dict: 表单输入的参数
    """
    params = {}
    
    if not schema or not isinstance(schema, dict):
        return params
    
    properties = schema.get('properties', {})
    for field_name, field_info in properties.items():
        field_type = field_info.get('type', 'string')
        field_title = field_info.get('title', field_name)
        field_description = field_info.get('description', '')
        field_key = f'{prefix}_{field_name}' if prefix else field_name
        field_default = field_info.get('default')
        
        if field_type == 'string':
            if 'enum' in field_info:
                # 对于枚举类型，使用selectbox
                params[field_name] = st.selectbox(
                    field_title,
                    options=field_info['enum'],
                    help=field_description,
                    key=field_key,
                    index=field_info['enum'].index(field_default) if field_default in field_info.get('enum', []) else 0
                )
            else:
                params[field_name] = st.text_input(
                    field_title,
                    value=field_default or '',
                    help=field_description,
                    key=field_key
                )
        elif field_type == 'number':
            min_value = field_info.get('minimum', None)
            max_value = field_info.get('maximum', None)
            params[field_name] = st.number_input(
                field_title,
                min_value=min_value,
                max_value=max_value,
                value=float(field_default or 0),
                help=field_description,
                key=field_key
            )
        elif field_type == 'boolean':
            params[field_name] = st.checkbox(
                field_title,
                value=field_default or False,
                help=field_description,
                key=field_key
            )
        elif field_type == 'array':
            min_items = field_info.get('minItems')
            max_items = field_info.get('maxItems')
            help_text = field_description
            if min_items is not None or max_items is not None:
                help_text += f" (数组长度限制: {min_items or '无'} - {max_items or '无'})"
            
            value = st.text_input(
                field_title,
                help=f'{help_text} (用逗号分隔多个值)',
                key=field_key,
                value=','.join(map(str, field_default)) if field_default else ''
            )
            items = [item.strip() for item in value.split(',')] if value else []
            
            # 验证数组长度
            if min_items is not None and len(items) < min_items:
                st.warning(f"{field_title}至少需要{min_items}个元素")
            if max_items is not None and len(items) > max_items:
                st.warning(f"{field_title}最多允许{max_items}个元素")
                items = items[:max_items]
            
            params[field_name] = items
        elif field_type == 'object':
            # 递归处理嵌套对象
            st.markdown(f"**{field_title}**")
            if field_description:
                st.markdown(f"*{field_description}*")
            with st.expander(field_title, expanded=True):
                nested_params = render_input_form(field_info, f"{field_key}_")
                params[field_name] = nested_params
    
    return params

def render_response_data(schema: dict, data: Any) -> None:
    """根据schema渲染响应数据
    
    Args:
        schema: 响应数据的JSON Schema
        data: 响应数据
    """
    if not schema or not isinstance(schema, dict):
        st.json(data)
        return
    
    properties = schema.get('properties', {})
    if not properties:
        st.json(data)
        return
    
    if not isinstance(data, dict):
        st.warning('响应数据格式不符合schema定义')
        st.json(data)
        return
    
    for field_name, field_info in properties.items():
        field_type = field_info.get('type', 'string')
        field_title = field_info.get('title', field_name)
        field_description = field_info.get('description', '')
        
        # 获取字段值
        field_value = data.get(field_name)
        
        # 显示字段标题和描述
        if field_type == 'object' and isinstance(field_value, dict):
            with st.expander(field_title, expanded=True):
                render_response_data(field_info, field_value)
        elif field_type == 'array' and isinstance(field_value, list):
            for i, item in enumerate(field_value):
                st.markdown(f"**项目 {i+1}**")
                if 'items' in field_info and isinstance(item, dict):
                    render_response_data(field_info['items'], item)
                else:
                    st.text_input(
                        f"{field_title} - 项目 {i+1}",
                        value=str(item),
                        disabled=True,
                        help=field_description
                    )
        elif field_type == 'number':
            st.number_input(
                field_title,
                value=float(field_value) if field_value is not None else 0.0,
                disabled=True,
                help=field_description
            )
        elif field_type == 'boolean':
            st.checkbox(
                field_title,
                value=bool(field_value),
                disabled=True,
                help=field_description
            )
        else:
            st.text_input(
                field_title,
                value=str(field_value) if field_value is not None else 'N/A',
                disabled=True,
                help=field_description
            )

def main():
    """主函数"""
    st.set_page_config(
        page_title='PyService管理界面',
        page_icon='🚀',
        layout='wide'
    )
    
    st.title('PyService服务管理系统')
    init_session_state()
    
    def render_service_registry():
        """渲染服务注册界面"""
        st.header('服务注册')
        
        # 显示所有repo目录下的项目
        repo_path = Path.cwd() / 'repo'
        if not repo_path.exists():
            repo_path.mkdir(parents=True)
        
        # 获取所有repo目录下的项目
        repos = [d for d in repo_path.iterdir() if d.is_dir()]
        
        # 显示现有项目列表
        st.subheader('现有项目')
        if not repos:
            st.info('当前没有任何项目')
        else:
            for repo in repos:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{repo.name}**")
                    # 检查是否已注册
                    service_status = st.session_state.registry.get_service_status(repo.name)
                    if service_status['status'] == 'registered':
                        st.success('已注册')
                    elif service_status['status'] == 'invalid':
                        st.error(service_status['message'])
                    else:
                        st.warning('未注册')
                with col2:
                    if service_status['status'] == 'unregistered':
                        if st.button('注册', key=f'register_{repo.name}'):
                            if st.session_state.registry.register_service(repo.name, repo.absolute()):
                                st.success('服务注册成功')
                                # 清除服务缓存，强制重新扫描
                                st.session_state.services_cache = None
                                st.rerun()
                            else:
                                st.error('服务注册失败')
                
        # 添加新项目
        st.subheader('添加新项目')
        with st.form('add_repo_form'):
            github_url = st.text_input('GitHub仓库地址', placeholder='例如：https://github.com/username/repo.git')
            project_name = st.text_input('项目名称', placeholder='如果留空，将使用仓库名称')
            
            if st.form_submit_button('克隆项目'):
                if not github_url:
                    st.error('请输入GitHub仓库地址')
                    return
                
                try:
                    # 从GitHub URL中提取仓库名称
                    if not project_name:
                        project_name = github_url.rstrip('.git').split('/')[-1]
                    
                    # 检查项目名称是否已存在
                    target_path = repo_path / project_name
                    if target_path.exists():
                        st.error(f'项目 {project_name} 已存在')
                        return
                    
                    # 克隆仓库
                    import subprocess
                    result = subprocess.run(
                        ['git', 'clone', github_url, str(target_path)],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        st.success('项目克隆成功')
                        # 清除服务缓存，强制重新扫描
                        st.session_state.services_cache = None
                        st.rerun()
                    else:
                        st.error(f'克隆失败：{result.stderr}')
                except Exception as e:
                    st.error(f'克隆过程中发生错误：{str(e)}')
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(['服务列表', 'Playground', '服务注册'])
    
    # 在不同标签页中渲染相应的内容
    with tab1:
        render_service_list()
    with tab2:
        render_playground()
    with tab3:
        render_service_registry()

if __name__ == '__main__':
    main()