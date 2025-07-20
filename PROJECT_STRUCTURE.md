# BroadenAgentic 项目结构详解

## 📁 项目整体架构

```
broadenagentic/
├── app/                          # 主应用目录
│   ├── __init__.py              # 应用初始化
│   ├── main.py                  # FastAPI主应用入口
│   └── core/                    # 核心模块
│       ├── __init__.py          # 核心模块初始化
│       ├── llm/                 # 大语言模型模块
│       │   ├── __init__.py      # LLM模块初始化
│       │   ├── base.py          # LLM基类定义
│       │   ├── qwen.py          # Qwen本地模型实现
│       │   ├── qwen_api.py      # Qwen API云端实现
│       │   └── factory.py       # LLM工厂类
│       ├── agent/               # Agent模块
│       │   ├── __init__.py      # Agent模块初始化
│       │   ├── base.py          # Agent基类
│       │   ├── task.py          # 任务Agent
│       │   ├── tool.py          # 工具Agent
│       │   └── allocator.py     # 任务分配Agent
│       └── constraint/          # 约束系统
│           ├── __init__.py      # 约束模块初始化
│           ├── input.py         # 输入约束
│           ├── output.py        # 输出约束
│           └── criterion.py     # 输出标准
├── tests/                       # 测试代码
│   ├── __init__.py
│   ├── test_core/              # 核心模块测试
│   │   ├── __init__.py
│   │   └── test_llm.py         # LLM测试
│   └── conftest.py             # 测试配置
├── examples/                    # 示例代码
│   ├── __init__.py
│   └── basic_usage.py          # 基础使用示例
├── docs/                       # 文档目录
├── scripts/                    # 脚本文件
├── data/                       # 数据目录
├── requirements.txt             # 生产环境依赖
├── requirements-dev.txt         # 开发环境依赖
├── run.py                      # 应用启动脚本
├── demo_framework.py           # 框架演示脚本
├── USAGE.md                    # 使用说明
├── QUICKSTART.md               # 快速开始指南
├── README.md                   # 项目主文档
├── PROJECT_STRUCTURE.md        # 项目结构文档（本文件）
└── env.example                 # 环境变量示例
```

## 🧠 核心模块详解

### 1. LLM模块 (`app/core/llm/`)

#### 1.1 LLM基类 (`base.py`)
**功能**: 定义所有LLM实现的通用接口

**核心类**:
- `LLMBase`: 抽象基类，定义LLM标准接口
- `LLMConfig`: LLM配置类
- `GenerationResult`: 生成结果类
- `ToolCall`: 工具调用类
- `ToolResult`: 工具结果类

**主要方法**:
```python
class LLMBase:
    async def load_model(self) -> bool          # 加载模型
    async def generate(self, prompt: str)       # 文本生成
    async def generate_with_tools(self, prompt, tools)  # 工具调用
    async def stream_generate(self, prompt)     # 流式生成
    async def chat(self, messages)              # 聊天模式
    async def health_check(self) -> bool        # 健康检查
    def get_model_info(self) -> Dict           # 获取模型信息
```

#### 1.2 Qwen本地模型 (`qwen.py`)
**功能**: 基于Ollama的本地Qwen模型实现

**核心类**:
- `QwenLLM`: 继承自LLMBase的Qwen本地实现
- `OllamaConfig`: Ollama配置类

**特性**:
- 支持qwen3:8b, qwen3:14b等模型
- 本地推理，隐私性好
- 响应时间较长（~70秒）

#### 1.3 Qwen API云端模型 (`qwen_api.py`)
**功能**: 基于OpenAI库的Qwen API云端实现

**核心类**:
- `QwenAPILLM`: 继承自LLMBase的Qwen API实现
- `QwenAPIConfig`: Qwen API配置类

**特性**:
- 支持qwen-plus, qwen-turbo, qwen-max等模型
- 云端推理，速度快（~14秒）
- 需要API密钥

#### 1.4 LLM工厂 (`factory.py`)
**功能**: 统一管理本地和云端模型，支持自动切换

**核心类**:
- `LLMFactory`: LLM工厂类
- `LLMFactoryConfig`: 工厂配置类

**支持模式**:
- `local`: 仅使用本地模型
- `cloud`: 仅使用云端模型
- `auto`: 自动选择（优先本地，失败时回退到云端）

**主要方法**:
```python
class LLMFactory:
    async def create_llm(self) -> LLMBase        # 创建LLM实例
    async def switch_mode(self, mode) -> LLMBase # 切换模式
    def get_current_mode(self) -> str            # 获取当前模式
    def get_available_modes(self) -> Dict        # 获取可用模式
```

### 2. Agent模块 (`app/core/agent/`)

#### 2.1 Agent基类 (`base.py`)
**功能**: 在LLM基础上的智能体包装层

**核心类**:
- `AgentBase`: Agent基类
- `AgentConfig`: Agent配置类
- `AgentStatus`: Agent状态枚举

**主要功能**:
- 输入输出约束验证
- 输出质量评估
- 自动重试机制
- 性能监控

**主要方法**:
```python
class AgentBase:
    async def execute(self, input_data) -> str   # 执行任务
    def get_status(self) -> Dict                # 获取状态
    def get_history(self) -> List               # 获取历史
    def reset(self) -> None                     # 重置状态
```

#### 2.2 任务Agent (`task.py`)
**功能**: 专门处理特定任务的Agent

**核心类**:
- `TaskAgent`: 继承自AgentBase的任务Agent

**特性**:
- 针对特定任务优化
- 可配置的任务处理流程
- 支持任务链式调用

#### 2.3 工具Agent (`tool.py`)
**功能**: 提供工具调用能力的Agent

**核心类**:
- `ToolAgent`: 继承自AgentBase的工具Agent

**特性**:
- 支持外部工具调用
- 工具参数验证
- 工具结果处理

#### 2.4 任务分配Agent (`allocator.py`)
**功能**: 将复杂需求分解为具体任务

**核心类**:
- `TaskAllocationAgent`: 继承自AgentBase的任务分配Agent

**特性**:
- 需求分析和理解
- 任务分解和规划
- 资源分配和调度

### 3. 约束系统 (`app/core/constraint/`)

#### 3.1 输入约束 (`input.py`)
**功能**: 验证输入数据的格式和内容

**核心类**:
- `InputTypeConstraint`: 输入类型约束
- `InputConstraintSet`: 输入约束集合

**支持验证**:
- 数据类型检查
- 长度限制
- 正则表达式匹配
- 数值范围检查
- 允许值列表

#### 3.2 输出约束 (`output.py`)
**功能**: 验证输出数据的格式和质量

**核心类**:
- `OutputTypeConstraint`: 输出类型约束
- `OutputConstraintSet`: 输出约束集合

**支持验证**:
- 数据类型检查
- 结构验证
- 质量指标检查
- 自定义验证器

#### 3.3 输出标准 (`criterion.py`)
**功能**: 使用自然语言描述的输出质量评估标准

**核心类**:
- `OutputCriterion`: 输出标准类
- `CriterionEvaluator`: 标准评估器

**特性**:
- 自然语言描述标准
- LLM自动评估
- 反馈和改进建议
- 评估历史记录

## 🔧 配置系统

### 环境变量配置

**Ollama配置**:
```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

**Qwen API配置**:
```bash
QWEN_API_KEY=sk-9b6f66d94dd249dfb7a7416cc270ce4d
```

**应用配置**:
```bash
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

### LLM配置示例

**本地模式**:
```python
config = LLMFactoryConfig(
    preferred_mode="local",
    local_model_name="qwen3:8b"
)
```

**云端模式**:
```python
config = LLMFactoryConfig(
    preferred_mode="cloud",
    cloud_model_name="qwen-plus",
    api_key="your-api-key"
)
```

**自动模式**:
```python
config = LLMFactoryConfig(
    preferred_mode="auto",
    local_model_name="qwen3:8b",
    cloud_model_name="qwen-plus",
    api_key="your-api-key",
    fallback_to_cloud=True
)
```

## 🧪 测试系统

### 测试结构
```
tests/
├── test_core/              # 核心模块测试
│   ├── test_llm.py         # LLM测试
│   ├── test_agent.py       # Agent测试
│   └── test_constraint.py  # 约束测试
├── test_integration/       # 集成测试
└── conftest.py             # 测试配置
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_core/test_llm.py

# 运行带覆盖率测试
pytest --cov=app
```

## 📚 示例和文档

### 示例代码
- `examples/basic_usage.py`: 基础使用示例
- `demo_framework.py`: 完整框架演示

### 文档
- `README.md`: 项目主文档
- `USAGE.md`: 使用说明
- `QUICKSTART.md`: 快速开始指南
- `PROJECT_STRUCTURE.md`: 项目结构文档（本文件）

## 🚀 开发指南

### 添加新模型
1. 继承`LLMBase`类
2. 实现必要的方法
3. 在工厂中注册

### 扩展约束
1. 继承`InputTypeConstraint`或`OutputTypeConstraint`
2. 实现自定义验证逻辑
3. 在Agent配置中使用

### 创建新Agent
1. 继承`AgentBase`类
2. 实现特定任务逻辑
3. 配置相应的约束和标准

## 🔍 调试和监控

### 日志系统
- 使用Python标准logging模块
- 支持不同级别的日志输出
- 可配置日志格式和输出位置

### 性能监控
- Agent执行次数统计
- 平均响应时间
- 成功率统计
- 错误率统计

### 健康检查
- LLM连接状态检查
- 模型加载状态检查
- API服务状态检查 