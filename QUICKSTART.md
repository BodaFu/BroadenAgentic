# BroadenAgentic 快速启动指南

## 🚀 快速开始

### 1. 环境准备

确保你的系统满足以下要求：
- **Python**: 3.9+ (推荐3.11+)
- **硬件**: RTX 3060 GPU, 16GB RAM
- **系统**: Windows 11 (推荐)

### 2. 安装Ollama和Qwen模型

```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取Qwen3-8B模型
ollama pull qwen3:8b

# 验证模型
ollama run qwen3:8b "Hello, world!"
```

### 3. 安装Python依赖

```bash
# 安装基础依赖
pip install fastapi uvicorn pydantic

# 安装完整依赖
pip install -r requirements.txt
```

### 4. 运行系统测试

```bash
# 测试系统是否正常工作
python test_system.py
```

### 5. 启动应用

```bash
# 方式1: 使用启动脚本
python run.py

# 方式2: 直接启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 访问应用

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **根路径**: http://localhost:8000/

## 📖 使用示例

### 基础LLM使用

```python
import asyncio
from app.core.llm import LLMConfig, QwenLLM

async def basic_example():
    # 创建LLM配置
    config = LLMConfig(
        model_name="qwen3:8b",
        temperature=0.7,
        max_tokens=100
    )
    
    # 创建LLM实例
    llm = QwenLLM(config)
    await llm.load_model()
    
    # 生成文本
    result = await llm.generate("请介绍一下人工智能")
    print(result.text)

asyncio.run(basic_example())
```

### 创建Agent

```python
import asyncio
from app.core.llm import LLMConfig, QwenLLM
from app.core.agent import AgentConfig, AgentBase
from app.core.constraint import InputTypeConstraint, OutputTypeConstraint, OutputCriterion

async def agent_example():
    # 创建LLM
    llm_config = LLMConfig(model_name="qwen3:8b")
    llm = QwenLLM(llm_config)
    await llm.load_model()
    
    # 创建约束
    input_constraints = [
        InputTypeConstraint(
            name="text",
            data_type="string",
            min_length=1,
            max_length=1000
        )
    ]
    
    output_constraints = [
        OutputTypeConstraint(
            name="response",
            data_type="string",
            min_length=10,
            max_length=500
        )
    ]
    
    # 创建输出标准
    output_criterion = OutputCriterion(
        name="质量评估",
        description="输出应该准确、完整且有用",
        min_score=0.7
    )
    
    # 创建Agent
    agent_config = AgentConfig(
        name="文本分析Agent",
        description="分析输入的文本并提供见解",
        input_constraints=input_constraints,
        output_constraints=output_constraints,
        output_criterion=output_criterion
    )
    
    agent = AgentBase(agent_config, llm)
    
    # 执行Agent
    result = await agent.execute("人工智能是计算机科学的一个分支")
    print(result)

asyncio.run(agent_example())
```

## 🔧 API使用

### 创建Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agent/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "文本分析Agent",
    "description": "分析输入的文本并提供见解",
    "input_data": "测试输入",
    "input_constraints": [
      {
        "name": "text",
        "data_type": "string",
        "min_length": 1,
        "max_length": 1000
      }
    ],
    "output_constraints": [
      {
        "name": "response",
        "data_type": "string",
        "min_length": 10,
        "max_length": 500
      }
    ],
    "output_criterion": {
      "name": "质量评估",
      "description": "输出应该准确、完整且有用",
      "min_score": 0.7
    }
  }'
```

### 执行Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agent/文本分析Agent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": "人工智能是计算机科学的一个分支"
  }'
```

### 获取Agent状态

```bash
curl -X GET "http://localhost:8000/api/v1/agent/文本分析Agent/status"
```

## 🎯 核心特性

### 1. Prompt工程师友好
- 可视化Prompt调优工具
- A/B测试界面
- 实时Prompt预览
- 自动Prompt优化建议

### 2. 可归因性和可量化性
- 完整的决策过程追踪
- 客观的评估指标
- 透明度报告生成
- 性能监控和成本分析

### 3. 本地化优先
- 基于Qwen3-8B-Int4模型
- 通过Ollama本地部署
- 减少API依赖
- 支持RTX 3060等消费级GPU

### 4. 约束系统
- 输入输出类型约束验证
- 自然语言质量标准
- 自动质量评估和优化
- 智能重试机制

## 🐛 故障排除

### 1. Ollama连接失败
```bash
# 检查Ollama服务是否运行
ollama list

# 重启Ollama服务
ollama serve
```

### 2. 模型加载失败
```bash
# 检查模型是否已下载
ollama list

# 重新下载模型
ollama pull qwen2.5:7b
```

### 3. 内存不足
- 确保有足够的GPU内存
- 考虑使用更小的模型
- 调整batch_size参数

### 4. 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📚 更多资源

- **完整文档**: 查看 `docs/` 目录
- **API文档**: http://localhost:8000/docs
- **示例代码**: 查看 `examples/` 目录
- **测试代码**: 查看 `tests/` 目录

## 🤝 贡献

欢迎贡献代码和提出建议！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。 