# PyService

PyService是一个创新的Python服务管理框架，不仅提供服务发现、环境管理、进程管理等核心功能，还计划通过AI Agent实现工具的自动识别、注册和智能编排执行。该框架旨在帮助开发者更便捷地管理和部署Python服务，并通过AI能力提供智能化的工具集成和任务执行。

## 核心功能

### 1. 服务发现与管理
- 自动扫描和发现服务定义
- 服务状态监控和管理
- 支持动态服务注册

### 2. 环境管理
- 自动创建和管理虚拟环境
- 智能依赖管理（支持requirements.txt、setup.py、pyproject.toml）
- 环境隔离，确保服务运行稳定

### 3. 进程管理
- 服务进程生命周期管理
- 端口管理和冲突处理
- 进程监控和自动恢复

### 4. 服务规范
- 标准化的服务定义格式
- 完整的Schema规范支持
- 统一的接口规范

## 快速开始

### 1. 安装
```bash
pip install pyservice
```

### 2. 创建服务
1. 在repo目录下创建服务目录
2. 添加service.json配置文件
3. 实现服务逻辑

### 3. 服务配置
在service.json中配置服务信息：
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
    }
}
```

## 项目结构
```
├── docs/               # 项目文档
├── repo/               # 服务仓库
├── src/                # 源代码
│   ├── core/           # 核心功能
│   │   ├── discovery.py    # 服务发现
│   │   ├── environment.py  # 环境管理
│   │   ├── metadata.py     # 元数据处理
│   │   └── process.py      # 进程管理
│   ├── services/       # 服务实现
│   ├── ui/            # Web 界面
│   └── utils/         # 工具函数
├── requirements.txt    # 项目依赖
└── start.sh           # 启动脚本
```

## 开发指南

### 1. 服务开发规范
- 继承BaseService类实现服务
- 遵循Schema规范定义接口
- 使用标准化的错误处理

### 2. 最佳实践
- 合理使用环境变量
- 做好服务隔离
- 实现健康检查
- 添加完整的文档

## 许可证
MIT License