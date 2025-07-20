# BroadenAgentic框架使用说明

## 概述

BroadenAgentic是一个支持本地Ollama和云端Qwen API的智能Agent框架，提供灵活的模型选择和完整的约束验证功能。

## 快速开始

### 1. 环境准备

确保已安装以下依赖：
```bash
pip install -r requirements.txt
```

### 2. 配置Ollama（本地模型）

安装并启动Ollama：
```bash
# 下载并安装Ollama
# 启动Ollama服务
ollama serve

# 拉取Qwen模型
ollama pull qwen3:8b
```

### 3. 配置Qwen API（云端模型）

设置API密钥：
```bash
export QWEN_API_KEY="sk-9b6f66d94dd249dfb7a7416cc270ce4d"
```

或在Windows PowerShell中：
```powershell
$env:QWEN_API_KEY="sk-9b6f66d94dd249dfb7a7416cc270ce4d"
```

### 4. 运行演示

```bash
python demo_framework.py
```

## 核心功能

### 1. LLM工厂

支持三种模式：
- **本地模式**：使用Ollama本地模型
- **云端模式**：使用Qwen API云端模型
- **自动模式**：优先本地，失败时回退到云端

```python
from app.core.llm import LLMFactory, LLMFactoryConfig

# 本地模式
config = LLMFactoryConfig(preferred_mode="local")
factory = LLMFactory(config)
llm = await factory.create_llm()

# 云端模式
config = LLMFactoryConfig(
    preferred_mode="cloud",
    api_key="your-api-key"
)
factory = LLMFactory(config)
llm = await factory.create_llm()

# 自动模式
config = LLMFactoryConfig(
    preferred_mode="auto",
    api_key="your-api-key",
    fallback_to_cloud=True
)
factory = LLMFactory(config)
llm = await factory.create_llm()
```

### 2. Agent框架

创建带约束的Agent：

```python
from app.core.agent import AgentConfig, AgentBase
from app.core.constraint import InputTypeConstraint, OutputTypeConstraint, OutputCriterion

# 创建约束
input_constraints = [
    InputTypeConstraint(
        name="topic",
        data_type="string",
        min_length=1,
        max_length=200
    )
]

output_constraints = [
    OutputTypeConstraint(
        name="analysis",
        data_type="string"
    )
]

output_criterion = OutputCriterion(
    name="质量评估",
    description="输出应该准确、完整且有用",
    min_score=0.7
)

# 创建Agent
agent_config = AgentConfig(
    name="智能分析Agent",
    description="分析给定主题并提供专业见解",
    input_constraints=input_constraints,
    output_constraints=output_constraints,
    output_criterion=output_criterion
)

agent = AgentBase(agent_config, llm)

# 执行Agent
result = await agent.execute("人工智能在医疗领域的应用")
```

### 3. 约束验证

框架提供完整的输入输出约束验证：

- **输入约束**：验证输入数据的类型、长度、格式等
- **输出约束**：验证输出数据的质量和结构
- **质量评估**：使用LLM评估输出质量

### 4. 性能监控

框架内置性能监控功能：

```python
# 获取Agent状态
status = agent.get_status()
print(f"执行次数: {status['execution_count']}")
print(f"平均分数: {status['performance_metrics']['average_score']}")

# 获取LLM信息
info = llm.get_model_info()
print(f"模型名称: {info['model_name']}")
print(f"是否加载: {info['is_loaded']}")
```

## API使用

### 启动API服务

```bash
python run.py
```

### API端点

- `GET /health` - 健康检查
- `GET /api/v1/llm/info` - 获取LLM信息
- `POST /api/v1/llm/switch` - 切换LLM模式
- `POST /api/v1/generate` - 文本生成
- `POST /api/v1/agents` - 创建Agent
- `POST /api/v1/agents/{name}/execute` - 执行Agent
- `GET /api/v1/agents` - 列出所有Agent

## 性能对比

根据测试结果：

| 模式 | 响应时间 | Token数 | 特点 |
|------|----------|---------|------|
| 本地模式 | ~70秒 | ~1200 | 免费，隐私性好 |
| 云端模式 | ~14秒 | ~700 | 速度快，质量高 |

## 配置说明

### 环境变量

```bash
# Ollama配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Qwen API配置
QWEN_API_KEY=sk-9b6f66d94dd249dfb7a7416cc270ce4d
```

### 模型配置

- **本地模型**：qwen3:8b, qwen3:14b
- **云端模型**：qwen-plus, qwen-turbo, qwen-max

## 故障排除

### 常见问题

1. **本地模型连接失败**
   - 检查Ollama服务是否启动
   - 确认模型是否已下载

2. **云端API连接失败**
   - 检查API密钥是否正确
   - 确认网络连接正常

3. **约束验证失败**
   - 检查输入数据格式
   - 调整约束参数

### 日志查看

框架使用Python标准logging模块，可通过环境变量设置日志级别：

```bash
export LOG_LEVEL=DEBUG
```

## 开发指南

### 添加新模型

1. 继承`LLMBase`类
2. 实现必要的方法
3. 在工厂中注册

### 扩展约束

1. 继承`InputTypeConstraint`或`OutputTypeConstraint`
2. 实现自定义验证逻辑
3. 在Agent配置中使用

## 许可证

本项目采用MIT许可证。 