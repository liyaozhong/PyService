# PyService 服务开发指南

## 概述
本指南详细说明了如何在PyService框架下开发和部署服务，包括服务定义、实现和最佳实践。

## 服务开发流程

### 1. 创建服务目录
在repo目录下创建新的服务目录：
```bash
mkdir repo/your_service
cd repo/your_service
```

### 2. 定义服务配置
创建service.json文件：
```json
{
    "name": "your_service",
    "version": "1.0.0",
    "description": "服务描述",
    "repo_path": "your_service",
    "dependencies": [
        "package1>=1.0.0",
        "package2>=2.0.0"
    ],
    "environment": {
        "python_version": ">=3.8",
        "env_vars": {
            "PORT": "8000"
        }
    },
    "request_schema": {
        "type": "object",
        "properties": {
            "input_field": {
                "type": "string",
                "description": "输入字段描述"
            }
        }
    },
    "response_schema": {
        "type": "object",
        "properties": {
            "output_field": {
                "type": "string",
                "description": "输出字段描述"
            }
        }
    }
}
```

### 3. 实现服务逻辑
创建service.py文件：
```python
from pyservice.core import BaseService

class YourService(BaseService):
    def __init__(self):
        super().__init__()
        # 初始化服务

    def validate_input(self, input_data):
        # 输入验证
        return True

    def process(self, input_data):
        # 服务核心逻辑
        result = self.do_something(input_data)
        return {"output_field": result}

    def do_something(self, data):
        # 具体业务逻辑实现
        return processed_data
```

## 服务规范

### 1. 目录结构
```
your_service/
├── service.json     # 服务配置
├── service.py       # 服务实现
├── requirements.txt # 依赖声明
├── tests/           # 测试用例
└── docs/           # 服务文档
```

### 2. 配置规范
- 必填字段完整性
- Schema定义清晰
- 版本号规范（语义化版本）
- 依赖版本明确

### 3. 代码规范
- 类型注解
- 文档字符串
- 错误处理
- 日志记录

## 最佳实践

### 1. 输入验证
```python
def validate_input(self, input_data):
    if not isinstance(input_data.get('input_field'), str):
        raise ValueError("input_field must be string")
    if len(input_data['input_field']) > 100:
        raise ValueError("input_field too long")
    return True
```

### 2. 错误处理
```python
from pyservice.utils.errors import ServiceError

class YourService(BaseService):
    def process(self, input_data):
        try:
            result = self.do_something(input_data)
            return {"output_field": result}
        except Exception as e:
            raise ServiceError(f"处理失败: {str(e)}")
```

### 3. 资源管理
```python
class YourService(BaseService):
    def __init__(self):
        super().__init__()
        self.resource = None

    def initialize(self):
        self.resource = self.setup_resource()

    def cleanup(self):
        if self.resource:
            self.resource.close()
```

### 4. 性能优化
```python
from functools import lru_cache

class YourService(BaseService):
    @lru_cache(maxsize=100)
    def expensive_operation(self, input_data):
        # 耗时操作的缓存处理
        return result
```

## 测试指南

### 1. 单元测试
```python
import unittest

class TestYourService(unittest.TestCase):
    def setUp(self):
        self.service = YourService()

    def test_process(self):
        input_data = {"input_field": "test"}
        result = self.service.process(input_data)
        self.assertEqual(result["output_field"], "expected")
```

### 2. 集成测试
```python
class TestYourServiceIntegration(unittest.TestCase):
    def test_end_to_end(self):
        # 完整流程测试
        service = YourService()
        service.initialize()
        try:
            result = service.process({"input_field": "test"})
            self.assertTrue(result["success"])
        finally:
            service.cleanup()
```

## 部署注意事项

### 1. 环境准备
- 确保Python版本兼容
- 安装所有依赖
- 配置环境变量

### 2. 健康检查
- 实现健康检查接口
- 监控关键指标
- 设置告警阈值

### 3. 日志配置
- 使用结构化日志
- 设置适当的日志级别
- 实现日志轮转

## 常见问题

### 1. 依赖冲突
- 使用虚拟环境
- 明确依赖版本
- 定期更新依赖

### 2. 性能问题
- 使用性能分析工具
- 实现缓存机制
- 优化算法逻辑

### 3. 内存泄漏
- 及时释放资源
- 使用上下文管理器
- 定期检查内存使用