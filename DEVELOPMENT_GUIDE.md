# BroadenAgentic 开发指南

## 🎯 开发概述

BroadenAgentic是一个模块化的智能Agent框架，设计目标是让开发者能够轻松扩展和定制功能。本指南将详细介绍如何参与开发和扩展框架功能。

## 🏗️ 架构设计原则

### 1. 模块化设计
- 每个模块都有清晰的职责边界
- 模块间通过标准接口通信
- 支持插拔式扩展

### 2. 异步优先
- 所有I/O操作都是异步的
- 支持高并发处理
- 避免阻塞操作

### 3. 类型安全
- 使用Pydantic进行数据验证
- 完整的类型注解
- 运行时类型检查

### 4. 可测试性
- 每个模块都有对应的测试
- 支持单元测试和集成测试
- 提供测试工具和mock

## 🧠 核心模块开发

### 1. LLM模块开发

#### 添加新的LLM实现

1. **继承LLMBase类**
```python
from app.core.llm.base import LLMBase, LLMConfig, GenerationResult

class MyCustomLLM(LLMBase):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # 初始化你的LLM
    
    async def load_model(self) -> bool:
        """加载模型"""
        try:
            # 实现模型加载逻辑
            self._is_loaded = True
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """生成文本"""
        if not self._is_loaded:
            await self.load_model()
        
        # 实现文本生成逻辑
        response = await self._call_model(prompt, **kwargs)
        
        return GenerationResult(
            text=response.text,
            tokens_used=response.tokens,
            finish_reason=response.finish_reason
        )
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 实现健康检查逻辑
            return True
        except Exception:
            return False
```

2. **在工厂中注册**
```python
# 在app/core/llm/factory.py中添加
async def _create_custom_llm(self, llm_config: LLMConfig) -> LLMBase:
    """创建自定义LLM"""
    return MyCustomLLM(llm_config)
```

#### LLM配置扩展

```python
from pydantic import BaseModel, Field

class MyCustomLLMConfig(BaseModel):
    """自定义LLM配置"""
    api_key: str = Field(..., description="API密钥")
    custom_param: str = Field(default="default", description="自定义参数")
```

### 2. Agent模块开发

#### 创建专用Agent

```python
from app.core.agent.base import AgentBase, AgentConfig
from app.core.constraint import InputTypeConstraint, OutputTypeConstraint

class MySpecializedAgent(AgentBase):
    """专用Agent示例"""
    
    def __init__(self, config: AgentConfig, llm):
        super().__init__(config, llm)
        # 初始化专用功能
    
    async def _process_special_task(self, input_data: str) -> str:
        """处理特殊任务"""
        # 实现特殊任务处理逻辑
        return f"处理结果: {input_data}"
    
    async def execute(self, input_data: Any) -> str:
        """执行任务"""
        # 验证输入
        self._validate_input(input_data)
        
        # 处理特殊任务
        result = await self._process_special_task(str(input_data))
        
        # 验证输出
        self._validate_output(result)
        
        return result
```

#### Agent配置示例

```python
# 创建专用Agent配置
specialized_config = AgentConfig(
    name="专用分析Agent",
    description="专门处理特定类型任务",
    input_constraints=[
        InputTypeConstraint(
            name="data",
            data_type="string",
            min_length=1,
            max_length=1000
        )
    ],
    output_constraints=[
        OutputTypeConstraint(
            name="analysis",
            data_type="string"
        )
    ],
    output_criterion=OutputCriterion(
        name="专用标准",
        description="输出应符合专用要求",
        min_score=0.8
    )
)
```

### 3. 约束系统开发

#### 创建自定义约束

```python
from app.core.constraint.input import InputTypeConstraint

class CustomInputConstraint(InputTypeConstraint):
    """自定义输入约束"""
    
    def validate(self, data: Any) -> bool:
        """自定义验证逻辑"""
        # 调用父类验证
        if not super().validate(data):
            return False
        
        # 添加自定义验证逻辑
        if isinstance(data, str):
            # 检查是否包含特定关键词
            if "敏感词" in data:
                return False
        
        return True
    
    def get_error_message(self, data: Any) -> Optional[str]:
        """自定义错误消息"""
        if not self.validate(data):
            return "数据包含敏感内容"
        return None
```

#### 创建自定义输出标准

```python
from app.core.constraint.criterion import OutputCriterion

class CustomOutputCriterion(OutputCriterion):
    """自定义输出标准"""
    
    async def evaluate(self, output: str, llm) -> Dict[str, Any]:
        """自定义评估逻辑"""
        # 实现自定义评估逻辑
        score = await self._custom_evaluation(output, llm)
        
        return {
            "score": score,
            "feedback": "自定义反馈",
            "suggestions": ["改进建议1", "改进建议2"]
        }
    
    async def _custom_evaluation(self, output: str, llm) -> float:
        """自定义评估方法"""
        # 实现具体的评估逻辑
        return 0.85
```

## 🔧 工具和工具Agent开发

### 1. 创建工具

```python
from typing import Any, Dict
import requests

class WebSearchTool:
    """网络搜索工具"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search(self, query: str) -> Dict[str, Any]:
        """执行搜索"""
        try:
            # 实现搜索逻辑
            response = requests.get(
                f"https://api.search.com/search?q={query}&key={self.api_key}"
            )
            return {
                "results": response.json(),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
```

### 2. 创建工具Agent

```python
from app.core.agent.tool import ToolAgent

class WebSearchAgent(ToolAgent):
    """网络搜索Agent"""
    
    def __init__(self, config: AgentConfig, llm, search_tool: WebSearchTool):
        super().__init__(config, llm)
        self.search_tool = search_tool
    
    async def execute(self, input_data: str) -> str:
        """执行搜索任务"""
        # 验证输入
        self._validate_input(input_data)
        
        # 执行搜索
        search_results = await self.search_tool.search(input_data)
        
        # 使用LLM处理结果
        prompt = f"基于以下搜索结果，回答问题: {input_data}\n\n搜索结果: {search_results}"
        result = await self.llm.generate(prompt)
        
        # 验证输出
        self._validate_output(result.text)
        
        return result.text
```

## 🧪 测试开发

### 1. 单元测试

```python
import pytest
from unittest.mock import Mock, AsyncMock
from app.core.llm import LLMConfig, QwenLLM

class TestQwenLLM:
    """QwenLLM测试类"""
    
    @pytest.fixture
    def llm_config(self):
        """LLM配置fixture"""
        return LLMConfig(
            model_name="qwen3:8b",
            temperature=0.7,
            max_tokens=100
        )
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Mock Ollama客户端"""
        client = Mock()
        client.generate = AsyncMock(return_value={
            "response": "测试响应",
            "done": True
        })
        return client
    
    @pytest.mark.asyncio
    async def test_generate_text(self, llm_config, mock_ollama_client):
        """测试文本生成"""
        llm = QwenLLM(llm_config)
        llm._client = mock_ollama_client
        
        result = await llm.generate("测试提示")
        
        assert result.text == "测试响应"
        assert result.tokens_used is not None
```

### 2. 集成测试

```python
import pytest
from app.core.agent import AgentConfig, AgentBase
from app.core.constraint import InputTypeConstraint, OutputTypeConstraint

class TestAgentIntegration:
    """Agent集成测试"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        llm = Mock()
        llm.generate = AsyncMock(return_value=Mock(
            text="测试输出",
            tokens_used=10
        ))
        return llm
    
    @pytest.mark.asyncio
    async def test_agent_execution(self, mock_llm):
        """测试Agent执行"""
        config = AgentConfig(
            name="测试Agent",
            description="测试用Agent",
            input_constraints=[
                InputTypeConstraint(
                    name="input",
                    data_type="string",
                    min_length=1
                )
            ],
            output_constraints=[
                OutputTypeConstraint(
                    name="output",
                    data_type="string"
                )
            ]
        )
        
        agent = AgentBase(config, mock_llm)
        result = await agent.execute("测试输入")
        
        assert result == "测试输出"
```

### 3. 性能测试

```python
import asyncio
import time
from app.core.llm import LLMFactory, LLMFactoryConfig

class TestPerformance:
    """性能测试类"""
    
    @pytest.mark.asyncio
    async def test_llm_performance(self):
        """测试LLM性能"""
        config = LLMFactoryConfig(
            preferred_mode="local",
            local_model_name="qwen3:8b"
        )
        
        factory = LLMFactory(config)
        llm = await factory.create_llm()
        
        # 测试响应时间
        start_time = time.time()
        result = await llm.generate("性能测试")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 120  # 2分钟内完成
        assert result.text is not None
```

## 🔍 调试和日志

### 1. 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('broadenagentic.log'),
        logging.StreamHandler()
    ]
)

# 模块级日志
logger = logging.getLogger(__name__)
```

### 2. 调试工具

```python
# 启用详细日志
import logging
logging.getLogger('app').setLevel(logging.DEBUG)

# 使用pdb调试
import pdb
pdb.set_trace()

# 使用ipdb调试（推荐）
import ipdb
ipdb.set_trace()
```

### 3. 性能分析

```python
import cProfile
import pstats

def profile_function():
    """性能分析装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()
            
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(10)
            
            return result
        return wrapper
    return decorator

# 使用示例
@profile_function()
async def my_function():
    # 你的代码
    pass
```

## 📦 打包和部署

### 1. 创建setup.py

```python
from setuptools import setup, find_packages

setup(
    name="broadenagentic",
    version="1.0.0",
    description="Prompt工程师友好的Agentic AI框架",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.0.0",
        "ollama>=0.5.0",
        "openai>=1.0.0",
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ]
    },
    python_requires=">=3.9",
)
```

### 2. 创建Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# 复制项目文件
COPY requirements.txt .
COPY app/ ./app/
COPY run.py .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 拉取模型
RUN ollama pull qwen3:8b

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run.py"]
```

### 3. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - QWEN_API_KEY=${QWEN_API_KEY}
    depends_on:
      - ollama
    volumes:
      - ./data:/app/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

## 🤝 贡献指南

### 1. 开发流程

1. **Fork项目**
2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **编写代码和测试**
4. **运行测试**
   ```bash
   pytest
   ```
5. **提交代码**
   ```bash
   git commit -m "feat: add your feature"
   ```
6. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **创建Pull Request**

### 2. 代码规范

- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用mypy进行类型检查
- 遵循PEP 8规范

```bash
# 格式化代码
black app/ tests/

# 排序导入
isort app/ tests/

# 类型检查
mypy app/
```

### 3. 测试要求

- 新功能必须有对应的测试
- 测试覆盖率不低于80%
- 所有测试必须通过

```bash
# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 📚 学习资源

### 1. 相关文档
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Pydantic文档](https://pydantic-docs.helpmanual.io/)
- [Ollama文档](https://ollama.ai/docs)
- [Qwen文档](https://github.com/QwenLM/Qwen)

### 2. 设计模式
- 工厂模式：LLM工厂
- 策略模式：不同的LLM实现
- 装饰器模式：约束验证
- 观察者模式：事件系统

### 3. 最佳实践
- 异步编程
- 错误处理
- 日志记录
- 性能优化
- 安全考虑

## 🔮 未来规划

### 1. 短期目标
- 添加更多LLM支持
- 完善约束系统
- 优化性能
- 增强测试覆盖

### 2. 中期目标
- 添加Web界面
- 支持多模态输入
- 实现分布式部署
- 添加监控和告警

### 3. 长期目标
- 构建生态系统
- 支持插件系统
- 实现自动优化
- 支持企业级部署 