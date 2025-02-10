# Schema 规范文档

## 概述
本文档定义了PyService中服务配置文件（service.json）中request_schema和response_schema的格式规范。

## Schema 基本结构
每个schema必须是一个JSON对象，包含以下基本属性：
- `type`: 字段类型，必填
- `properties`: 当type为object时的子字段定义
- `description`: 字段描述，建议填写
- `required`: 当type为object时的必填字段列表

## 支持的数据类型

### 1. object类型
用于表示一个JSON对象，必须包含properties属性来定义子字段。

```json
{
    "type": "object",
    "properties": {
        "field1": { "type": "string" },
        "field2": { "type": "number" }
    },
    "required": ["field1"]
}
```

### 2. string类型
用于表示字符串值。

```json
{
    "type": "string",
    "description": "字段描述",
    "enum": ["选项1", "选项2"],  // 可选，定义枚举值
    "default": "默认值"  // 可选，定义默认值
}
```

### 3. number类型
用于表示数值。

```json
{
    "type": "number",
    "description": "字段描述",
    "minimum": 0,  // 可选，最小值
    "maximum": 100,  // 可选，最大值
    "default": 0  // 可选，默认值
}
```

### 4. boolean类型
用于表示布尔值。

```json
{
    "type": "boolean",
    "description": "字段描述",
    "default": false  // 可选，默认值
}
```

### 5. array类型
用于表示数组。

```json
{
    "type": "array",
    "items": {  // 定义数组元素的类型
        "type": "string"
    },
    "description": "字段描述",
    "minItems": 1,  // 可选，最小元素数量
    "maxItems": 10  // 可选，最大元素数量
}
```

## 示例

### 计算器服务的请求schema
```json
{
    "type": "object",
    "properties": {
        "a": {
            "type": "number",
            "description": "第一个操作数"
        },
        "b": {
            "type": "number",
            "description": "第二个操作数"
        },
        "operation": {
            "type": "string",
            "enum": ["+", "-", "*", "/"],
            "description": "运算符"
        }
    },
    "required": ["a", "b", "operation"]
}
```

### 计算器服务的响应schema
```json
{
    "type": "object",
    "properties": {
        "result": {
            "type": "number",
            "description": "计算结果"
        }
    },
    "required": ["result"]
}
```