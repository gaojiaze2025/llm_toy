# DeepSeek API Agent 使用指南

## 项目概述

这是一个使用 DeepSeek API 的智能计算器 Agent，基于 ReAct (Reasoning + Acting) 框架实现。Agent 能够理解用户指令，进行数学计算，并通过工具调用完成任务。

## 文件结构

```
.
├── agent_demo.py          # 主要的 Agent 实现代码
├── requirements.txt       # Python 依赖包
├── .env.example          # 环境变量配置示例
├── plan.md              # 项目架构设计文档
└── README_DEEPSEEK.md   # 本使用指南
```

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制 `.env.example` 文件为 `.env` 并填写你的 DeepSeek API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

## 运行 Agent

### 基本使用

```bash
python agent_demo.py
```

### 自定义用户输入

修改 [`agent_demo.py`](agent_demo.py:178) 文件中的用户输入：

```python
user_input = "计算 123 加上 456 的结果是多少？"
```

### 自定义系统提示词

修改 [`agent_demo.py`](agent_demo.py:168) 文件中的系统提示词：

```python
SYSTEM_PROMPT = """
你是智能计算器Agent...
"""
```

## 核心功能

### 1. ReAct 框架

Agent 遵循 ReAct 框架：
- **Thought**: 推理和计划
- **Action**: 工具调用（JSON 格式）
- **Observation**: 工具执行结果

### 2. 工具系统

当前支持的工具：
- **add_numbers**: 两个数字的加法运算

### 3. DeepSeek API 集成

- 使用官方 DeepSeek API 端点
- 支持重试机制（指数退避）
- 完善的错误处理

## 代码结构说明

### 主要函数

1. **[`call_llm`](agent_demo.py:32)**: DeepSeek API 调用函数
   - 处理消息格式化
   - 实现重试逻辑
   - 错误处理和日志记录

2. **[`run_agent_loop`](agent_demo.py:98)**: Agent 主循环
   - 管理对话历史
   - 解析 LLM 响应
   - 执行工具调用
   - 控制循环终止条件

3. **[`add_numbers`](agent_demo.py:13)**: 工具函数示例
   - 简单的加法运算
   - 类型注解和文档字符串

### 配置管理

在 [`DEEPSEEK_CONFIG`](agent_demo.py:23) 中配置 API 参数：
- API 密钥和端点
- 模型选择
- 温度和最大 token 数

## 输出格式

### LLM 响应格式要求

Agent 要求 DeepSeek 模型按照特定格式输出：

**工具调用格式：**
```
Thought: 推理过程描述
[ACTION_START]
{"tool": "add_numbers", "args": {"a": 123, "b": 456}}
[ACTION_END]
```

**最终答案格式：**
```
Thought: 完成任务的推理
Final Answer: 最终答案文本
```

## 错误处理

### API 错误
- 网络连接问题自动重试（最多3次）
- API 密钥验证
- 响应格式验证

### 工具执行错误
- JSON 解析错误处理
- 工具未注册错误
- 参数验证错误

## 扩展开发

### 添加新工具

1. 定义工具函数：
```python
def multiply_numbers(a: float, b: float) -> float:
    """对两个数字做乘法运算"""
    return a * b
```

2. 注册到工具表：
```python
AVAILABLE_TOOLS = {
    "add_numbers": add_numbers,
    "multiply_numbers": multiply_numbers,
}
```

3. 更新系统提示词中的工具描述

### 修改 API 配置

在 [`DEEPSEEK_CONFIG`](agent_demo.py:23) 中调整参数：
- `temperature`: 控制创造性（0.1-1.0）
- `max_tokens`: 响应长度限制
- `model`: 切换不同模型

## 故障排除

### 常见问题

1. **API 密钥错误**
   - 检查 `.env` 文件中的 `DEEPSEEK_API_KEY`
   - 确认 API 密钥有效且有余量

2. **网络连接问题**
   - 检查网络连接
   - 确认 API 端点可访问

3. **响应格式错误**
   - 检查系统提示词是否清晰
   - 确认模型理解输出格式要求

### 调试模式

在代码中添加调试信息：
```python
print(f"API Request: {payload}")  # 查看请求数据
print(f"API Response: {result}")  # 查看原始响应
```

## 性能优化建议

1. **缓存机制**: 对重复计算结果进行缓存
2. **批量处理**: 支持多个计算任务批量处理
3. **超时设置**: 根据网络状况调整超时时间
4. **并发处理**: 对多个工具调用实现并发执行

## 安全注意事项

1. **API 密钥安全**: 不要将 `.env` 文件提交到版本控制
2. **输入验证**: 对所有用户输入进行验证
3. **资源限制**: 设置合理的 API 调用频率限制
4. **错误日志**: 记录错误信息但不泄露敏感数据

## 许可证

本项目仅供学习和演示使用。