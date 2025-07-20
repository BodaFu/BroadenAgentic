"""
BroadenAgentic - 主应用入口
"""

import uvicorn
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging
import asyncio

from .core.llm import LLMConfig, QwenLLM, LLMFactory, LLMFactoryConfig
from .core.agent import AgentConfig, AgentBase
from .core.constraint import InputTypeConstraint, OutputTypeConstraint, OutputCriterion

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="BroadenAgentic",
    description="Prompt工程师友好的Agentic AI框架",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局LLM实例
llm_factory = None
llm_instance = None
agent_instances = {}


class LLMRequest(BaseModel):
    """LLM请求模型"""
    model_name: str = "qwen2.5:7b"
    temperature: float = 0.7
    max_tokens: int = 2048
    prompt: str


class AgentRequest(BaseModel):
    """Agent请求模型"""
    name: str
    description: str
    input_data: Any
    input_constraints: Optional[List[Dict]] = None
    output_constraints: Optional[List[Dict]] = None
    output_criterion: Optional[Dict] = None


class AgentResponse(BaseModel):
    """Agent响应模型"""
    output: Any
    quality_score: float
    execution_time: float
    retry_count: int
    status: str


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global llm_factory, llm_instance
    
    try:
        # 初始化LLM工厂
        factory_config = LLMFactoryConfig(
            preferred_mode="auto",  # 自动选择本地或云端
            local_model_name="qwen3:8b",
            cloud_model_name="qwen-plus",
            api_key=os.getenv("QWEN_API_KEY"),  # 从环境变量获取API密钥
            fallback_to_cloud=True
        )
        
        llm_factory = LLMFactory(factory_config)
        
        # 创建LLM实例
        llm_config = LLMConfig(
            model_name="qwen3:8b",
            temperature=0.7,
            max_tokens=2048
        )
        
        llm_instance = await llm_factory.create_llm(llm_config)
        
        logger.info(f"BroadenAgentic应用启动成功，使用模式: {llm_factory.get_current_mode()}")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to BroadenAgentic",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    global llm_factory, llm_instance
    
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="LLM未初始化")
    
    is_healthy = await llm_instance.health_check()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "llm_loaded": llm_instance.is_loaded(),
        "model_info": llm_instance.get_model_info(),
        "factory_info": llm_factory.get_model_info() if llm_factory else {}
    }


@app.post("/api/v1/llm/generate")
async def generate_text(request: LLMRequest):
    """生成文本"""
    global llm_instance
    
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="LLM未初始化")
    
    try:
        result = await llm_instance.generate(
            request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "text": result.text,
            "tokens_used": result.tokens_used,
            "finish_reason": result.finish_reason,
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"文本生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/create")
async def create_agent(request: AgentRequest):
    """创建Agent"""
    global llm_instance
    
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="LLM未初始化")
    
    try:
        # 构建约束
        input_constraints = []
        if request.input_constraints:
            for constraint_data in request.input_constraints:
                input_constraints.append(InputTypeConstraint(**constraint_data))
        
        output_constraints = []
        if request.output_constraints:
            for constraint_data in request.output_constraints:
                output_constraints.append(OutputTypeConstraint(**constraint_data))
        
        # 构建输出标准
        if request.output_criterion:
            output_criterion = OutputCriterion(**request.output_criterion)
        else:
            output_criterion = OutputCriterion(
                name="默认标准",
                description="输出应该准确、完整且有用"
            )
        
        # 创建Agent配置
        agent_config = AgentConfig(
            name=request.name,
            description=request.description,
            input_constraints=input_constraints,
            output_constraints=output_constraints,
            output_criterion=output_criterion
        )
        
        # 创建Agent实例
        agent = AgentBase(agent_config, llm_instance)
        agent_instances[request.name] = agent
        
        return {
            "message": "Agent创建成功",
            "agent_name": request.name,
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Agent创建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/{agent_name}/execute")
async def execute_agent(agent_name: str, request: Dict[str, Any]):
    """执行Agent"""
    global agent_instances
    
    if agent_name not in agent_instances:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")
    
    try:
        agent = agent_instances[agent_name]
        input_data = request.get("input_data")
        
        start_time = asyncio.get_event_loop().time()
        
        # 执行Agent
        output = await agent.execute(input_data)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # 获取执行状态
        status = agent.get_status()
        
        return AgentResponse(
            output=output,
            quality_score=status['performance_metrics']['average_score'],
            execution_time=execution_time,
            retry_count=status['retry_count'],
            status=status['status']
        )
        
    except Exception as e:
        logger.error(f"Agent执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agent/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """获取Agent状态"""
    global agent_instances
    
    if agent_name not in agent_instances:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")
    
    agent = agent_instances[agent_name]
    return agent.get_status()


@app.get("/api/v1/agent/{agent_name}/history")
async def get_agent_history(agent_name: str, limit: int = 10):
    """获取Agent执行历史"""
    global agent_instances
    
    if agent_name not in agent_instances:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")
    
    agent = agent_instances[agent_name]
    return agent.get_execution_history(limit)


@app.delete("/api/v1/agent/{agent_name}")
async def delete_agent(agent_name: str):
    """删除Agent"""
    global agent_instances
    
    if agent_name not in agent_instances:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 不存在")
    
    del agent_instances[agent_name]
    
    return {
        "message": f"Agent '{agent_name}' 删除成功",
        "status": "deleted"
    }


@app.get("/api/v1/agents")
async def list_agents():
    """列出所有Agent"""
    global agent_instances
    
    agents = []
    for name, agent in agent_instances.items():
        status = agent.get_status()
        agents.append({
            "name": name,
            "status": status['status'],
            "execution_count": status['execution_count'],
            "average_score": status['performance_metrics']['average_score']
        })
    
    return {"agents": agents}


@app.get("/api/v1/llm/info")
async def get_llm_info():
    """获取LLM信息"""
    global llm_factory, llm_instance
    
    if llm_instance is None:
        raise HTTPException(status_code=503, detail="LLM未初始化")
    
    return {
        "current_mode": llm_factory.get_current_mode() if llm_factory else None,
        "available_modes": llm_factory.get_available_modes() if llm_factory else {},
        "model_info": llm_instance.get_model_info(),
        "factory_info": llm_factory.get_model_info() if llm_factory else {}
    }


@app.post("/api/v1/llm/switch")
async def switch_llm_mode(mode: str):
    """切换LLM模式"""
    global llm_factory, llm_instance
    
    if llm_factory is None:
        raise HTTPException(status_code=503, detail="LLM工厂未初始化")
    
    try:
        llm_config = LLMConfig(
            model_name="qwen3:8b" if mode == "local" else "qwen-plus",
            temperature=0.7,
            max_tokens=2048
        )
        
        llm_instance = await llm_factory.switch_mode(mode, llm_config)
        
        return {
            "message": f"成功切换到{mode}模式",
            "current_mode": llm_factory.get_current_mode(),
            "model_info": llm_instance.get_model_info()
        }
        
    except Exception as e:
        logger.error(f"切换LLM模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 