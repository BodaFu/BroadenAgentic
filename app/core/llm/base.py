"""
LLM基类 - 封装与大模型对话的接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import asyncio
import logging

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """LLM配置"""
    model_name: str = Field(..., description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, gt=0, description="最大token数")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p参数")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    stop_sequences: Optional[List[str]] = Field(default=None, description="停止序列")
    timeout: int = Field(default=30, gt=0, description="超时时间(秒)")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")


class GenerationResult(BaseModel):
    """生成结果"""
    text: str = Field(..., description="生成的文本")
    tokens_used: Optional[int] = Field(default=None, description="使用的token数")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ToolCall(BaseModel):
    """工具调用"""
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="工具参数")


class ToolResult(BaseModel):
    """工具结果"""
    tool_call: ToolCall = Field(..., description="工具调用")
    result: Any = Field(..., description="工具执行结果")


class LLMBase(ABC):
    """LLM基类 - 封装与大模型对话的接口"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = None
        self._is_loaded = False
        self._retry_count = 0
        self._total_tokens_used = 0
        self._total_requests = 0
    
    @abstractmethod
    async def load_model(self) -> bool:
        """加载模型"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """生成文本"""
        pass
    
    @abstractmethod
    async def generate_with_tools(self, prompt: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """使用工具生成"""
        pass
    
    async def generate_with_retry(self, prompt: str, **kwargs) -> GenerationResult:
        """带重试的文本生成"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await self.generate(prompt, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"生成失败，尝试 {attempt + 1}/{self.config.max_retries + 1}: {e}")
                
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                
        raise last_exception or Exception("生成失败")
    
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._is_loaded
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self._is_loaded:
                await self.load_model()
            
            # 简单的健康检查
            result = await self.generate("Hello", max_tokens=5)
            return bool(result.text.strip())
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.config.model_name,
            "is_loaded": self._is_loaded,
            "config": self.config.dict()
        }
    
    def get_token_usage(self) -> Dict[str, Any]:
        """获取Token使用统计"""
        return {
            "total_tokens_used": self._total_tokens_used,
            "total_requests": self._total_requests,
            "average_tokens_per_request": self._total_tokens_used / self._total_requests if self._total_requests > 0 else 0
        }
    
    def reset_token_usage(self) -> None:
        """重置Token使用统计"""
        self._total_tokens_used = 0
        self._total_requests = 0
    
    def _update_token_usage(self, tokens_used: int) -> None:
        """更新Token使用统计"""
        self._total_tokens_used += tokens_used
        self._total_requests += 1 