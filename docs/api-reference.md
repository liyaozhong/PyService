# PyService API参考文档

## 核心API

### BaseService 类
基础服务类，所有服务都应继承此类。

#### 方法

##### __init__(self)
初始化服务实例。

##### validate_input(self, input_data: dict) -> bool
验证输入数据的有效性。
- 参数：input_data - 输入数据字典
- 返回：验证是否通过

##### process(self, input_data: dict) -> dict
处理服务请求。
- 参数：input_data - 输入数据字典
- 返回：处理结果字典

##### initialize(self) -> None
服务初始化。

##### cleanup(self) -> None
服务清理。

### ServiceManager 类
服务管理器，负责服务的注册和生命周期管理。

#### 方法

##### register_service(name: str, service_class: Type[BaseService]) -> None
注册新服务。
- 参数：
  - name - 服务名称
  - service_class - 服务类

##### get_service(name: str) -> BaseService
获取服务实例。
- 参数：name - 服务名称
- 返回：服务实例

## 工具API

### EnvironmentManager 类
环境管理器，处理虚拟环境和依赖。

#### 方法

##### create_environment(service_name: str, python_version: str) -> str
创建虚拟环境。
- 参数：
  - service_name - 服务名称
  - python_version - Python版本要求
- 返回：环境路径

##### install_dependencies(env_path: str, dependencies: List[str]) -> bool
安装依赖包。
- 参数：
  - env_path - 环境路径
  - dependencies - 依赖列表
- 返回：安装是否成功

### ProcessManager 类
进程管理器，处理服务进程的生命周期。

#### 方法

##### start_service(service_name: str) -> int
启动服务进程。
- 参数：service_name - 服务名称
- 返回：进程ID

##### stop_service(service_name: str) -> bool
停止服务进程。
- 参数：service_name - 服务名称
- 返回：操作是否成功

## 工具识别API

### CodeAnalyzer 类
代码分析器，用于识别和分析工具函数。

#### 方法

##### analyze_code(code: str) -> Dict[str, Any]
分析代码并提取工具信息。
- 参数：code - 源代码字符串
- 返回：工具描述字典

##### extract_schema(func: Callable) -> Dict[str, Any]
从函数提取Schema信息。
- 参数：func - 函数对象
- 返回：Schema字典

## 错误处理

### 异常类

#### ServiceError
服务执行错误。

#### ConfigurationError
配置错误。

#### EnvironmentError
环境设置错误。

## 工具编排API

### PlanGenerator 类
执行计划生成器。

#### 方法

##### generate_plan(request: str, tools: List[Dict]) -> Dict[str, Any]
生成工具执行计划。
- 参数：
  - request - 用户请求
  - tools - 可用工具列表
- 返回：执行计划

### Executor 类
计划执行器。

#### 方法

##### execute_plan(plan: Dict[str, Any]) -> Any
执行工具调用计划。
- 参数：plan - 执行计划
- 返回：执行结果

## 配置API

### ConfigManager 类
配置管理器。

#### 方法

##### load_service_config(service_name: str) -> Dict[str, Any]
加载服务配置。
- 参数：service_name - 服务名称
- 返回：配置字典

##### validate_config(config: Dict[str, Any]) -> bool
验证配置有效性。
- 参数：config - 配置字典
- 返回：验证是否通过

## 事件API

### EventEmitter 类
事件发射器。

#### 方法

##### on(event: str, callback: Callable) -> None
注册事件监听器。
- 参数：
  - event - 事件名称
  - callback - 回调函数

##### emit(event: str, data: Any) -> None
触发事件。
- 参数：
  - event - 事件名称
  - data - 事件数据

## 日志API

### Logger 类
日志管理器。

#### 方法

##### setup(service_name: str, level: str) -> None
设置日志配置。
- 参数：
  - service_name - 服务名称
  - level - 日志级别

##### log(level: str, message: str, **kwargs) -> None
记录日志。
- 参数：
  - level - 日志级别
  - message - 日志消息
  - kwargs - 额外参数