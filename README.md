# BroadenAgentic - Prompt工程师友好的Agentic AI框架

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Qwen](https://img.shields.io/badge/Qwen-2.5+-orange.svg)](https://github.com/QwenLM/Qwen)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个专为Prompt工程师设计的Agentic AI框架，重点关注LLM输出的可归因性、可量化性和可控性。基于本地Qwen系列模型，提供可视化Prompt调优工具和完整的质量控制系统。

## 🚀 特性

- **🎯 Prompt工程师友好**: 可视化Prompt调优工具和A/B测试
- **🔍 可归因性**: 完整的决策过程追踪和透明度报告
- **📊 可量化性**: 客观的评估指标和性能监控
- **🏠 本地化优先**: 基于Qwen系列模型，支持本地部署
- **🔄 输出质量控制**: 自动评估和优化LLM输出
- **🛠️ 多模态支持**: 文本、图像、音频、视频处理
- **⚡ 高性能**: 异步处理，支持本地推理优化
- **🔧 模块化设计**: 易于扩展和维护的约束系统

## 📋 目录

- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [核心概念](#核心概念)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🚀 快速开始

### 环境要求

- **系统**: Windows 11 (推荐)
- **硬件**: RTX 3060 GPU, 16GB RAM
- **软件**: Python 3.9+, CUDA 11.8+
- **模型**: Qwen3-8B-Int4 (通过Ollama)
- **数据库**: PostgreSQL 13+, Redis 6+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/broadenagentic.git
cd broadenagentic
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

3. **安装Ollama和Qwen模型**
```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取Qwen3-8B-Int4模型
ollama pull qwen2.5:7b
```

4. **安装依赖**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

5. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，配置必要的环境变量
```

6. **启动应用**
```bash
python app/main.py
```

6. **访问应用**
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### Docker部署

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

## 📁 项目结构

```
broadenagentic/
├── app/                    # 主应用目录
│   ├── core/              # 核心模块
│   │   ├── agent.py       # 智能体核心
│   │   ├── planner.py     # 任务规划器
│   │   ├── memory.py      # 记忆系统
│   │   └── tools.py       # 工具管理
│   ├── communication/     # 通信模块
│   │   ├── messaging.py   # 消息系统
│   │   ├── events.py      # 事件系统
│   │   └── routing.py     # 路由系统
│   ├── security/          # 安全模块
│   │   ├── auth.py        # 认证授权
│   │   ├── filtering.py   # 内容过滤
│   │   └── audit.py       # 审计日志
│   ├── api/               # API接口
│   │   ├── routes/        # 路由定义
│   │   ├── models/        # 数据模型
│   │   └── middleware/    # 中间件
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── docs/                  # 文档
├── examples/              # 示例代码
├── scripts/               # 脚本文件
└── requirements.txt       # Python依赖
```

## 🧠 核心概念

### LLM基类 (LLM Base)

封装与大模型对话的接口，支持本地Qwen模型：

- **模型管理**: 自动加载和切换模型
- **对话接口**: 标准化的生成接口
- **多模态支持**: 文本、图像、音频处理
- **性能优化**: 本地推理加速

```python
from app.core.llm.qwen import QwenLLM
from app.core.llm.base import LLMConfig

# 配置Qwen模型
config = LLMConfig(
    model_name="qwen2.5:7b",
    temperature=0.7,
    max_tokens=2048
)

# 创建LLM实例
llm = QwenLLM(config)
await llm.load_model()
```

### Agent基类 (Agent Base)

在LLM基类上的包装层，提供质量控制：

- **约束检查**: 输入输出类型约束验证
- **标准判断**: 输出质量自动评估
- **自动调优**: 基于反馈的Prompt优化
- **重试机制**: 智能重试和错误恢复

```python
from app.core.agent.base import AgentBase, AgentConfig
from app.core.constraint import InputTypeConstraint, OutputTypeConstraint

# 配置Agent
config = AgentConfig(
    name="TextProcessor",
    description="处理文本任务",
    input_constraints=[InputTypeConstraint(data_type="string")],
    output_constraints=[OutputTypeConstraint(data_type="string")],
    output_criterion=OutputCriterion(description="输出应该准确且完整")
)

# 创建Agent
agent = AgentBase(config, llm)
result = await agent.execute("分析这段文本")
```

### 任务分配Agent (Task Allocation Agent)

将用户需求分解为具体任务：

- **需求分析**: 理解用户输入的真实意图
- **任务分解**: 将复杂需求分解为简单任务
- **依赖分析**: 识别任务间的依赖关系
- **资源分配**: 为每个任务分配合适的Agent和工具

### 约束系统 (Constraint System)

确保输出质量和一致性：

- **输入约束**: 验证输入数据的类型和格式
- **输出约束**: 确保输出符合预期格式
- **质量标准**: 用自然语言描述的输出评判标准
- **自动验证**: 实时验证输出质量

### 质量控制系统 (Quality Control System)

自动评估和优化输出：

- **质量评估**: 多维度质量评分
- **Prompt优化**: 基于反馈自动调优
- **A/B测试**: 多版本效果对比
- **性能监控**: 实时性能指标跟踪

## 📚 API文档

### 智能体管理

#### 创建智能体
```http
POST /api/v1/agents/
Content-Type: application/json

{
    "name": "Assistant",
    "role": "general",
    "capabilities": ["text_processing", "web_search"]
}
```

#### 获取智能体列表
```http
GET /api/v1/agents/
```

#### 获取智能体详情
```http
GET /api/v1/agents/{agent_id}
```

#### 更新智能体状态
```http
PUT /api/v1/agents/{agent_id}/status
Content-Type: application/json

{
    "status": "busy"
}
```

### 任务管理

#### 创建任务
```http
POST /api/v1/tasks/
Content-Type: application/json

{
    "title": "数据分析任务",
    "description": "分析用户行为数据",
    "agent_id": "agent_id",
    "priority": 1
}
```

#### 获取任务列表
```http
GET /api/v1/tasks/
```

### 工具管理

#### 注册工具
```http
POST /api/v1/tools/
Content-Type: application/json

{
    "name": "web_search",
    "description": "网络搜索工具",
    "endpoint": "https://api.example.com/search",
    "parameters": {
        "query": "string"
    }
}
```

## 🛠️ 开发指南

### 环境设置

1. **安装开发依赖**
```bash
pip install -r requirements-dev.txt
```

2. **设置预提交钩子**
```bash
pre-commit install
```

3. **运行代码格式化**
```bash
black app tests
isort app tests
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/test_core/test_agent.py
```

### 代码质量检查

```bash
# 类型检查
mypy app

# 代码风格检查
flake8 app tests

# 安全检查
bandit -r app
```

## 🚀 部署指南

### 生产环境部署

1. **使用Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

2. **使用Kubernetes**
```bash
kubectl apply -f k8s/
```

3. **使用云服务**
- AWS ECS/EKS
- Google Cloud Run/GKE
- Azure Container Instances/AKS

### 监控和日志

- **应用监控**: Prometheus + Grafana
- **日志管理**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **错误追踪**: Sentry
- **性能分析**: APM工具

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式

1. **报告Bug**: 在GitHub Issues中报告问题
2. **功能请求**: 提出新功能建议
3. **代码贡献**: 提交Pull Request
4. **文档改进**: 完善文档和示例
5. **社区支持**: 回答问题和帮助其他用户

### 开发流程

1. **Fork项目**
2. **创建功能分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建Pull Request**

### 代码规范

- 遵循PEP 8代码风格
- 使用类型提示
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目的支持：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [LangChain](https://langchain.com/) - LLM应用开发框架
- [OpenAI](https://openai.com/) - 强大的AI模型
- [PostgreSQL](https://www.postgresql.org/) - 可靠的关系型数据库
- [Redis](https://redis.io/) - 高性能缓存和消息队列

## 📞 联系我们

- **项目主页**: https://github.com/yourusername/myagentic
- **问题反馈**: https://github.com/yourusername/myagentic/issues
- **讨论区**: https://github.com/yourusername/myagentic/discussions
- **邮箱**: your.email@example.com

---

**MyAgentic** - 让AI更智能，让开发更简单 🚀 