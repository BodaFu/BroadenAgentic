"""
Qwen API云端调用实现 - 基于OpenAI库
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import LLMBase, LLMConfig, GenerationResult, ToolCall, ToolResult

logger = logging.getLogger(__name__)


class QwenAPIConfig(BaseModel):
    """Qwen API配置"""
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="API基础URL")
    model_name: str = Field(default="qwen-plus", description="模型名称")
    timeout: int = Field(default=30, description="超时时间(秒)")


class QwenAPILLM(LLMBase):
    """Qwen API实现 - 基于OpenAI库的云端调用"""
    
    def __init__(self, config: LLMConfig, api_config: Optional[QwenAPIConfig] = None):
        super().__init__(config)
        self.api_config = api_config
        self._client = None
    
    async def _get_client(self):
        """获取OpenAI客户端"""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_config.api_key,
                    base_url=self.api_config.base_url
                )
            except ImportError:
                raise ImportError("请安装openai: pip install openai")
        return self._client
    
    async def load_model(self) -> bool:
        """加载模型（API模式下直接返回True）"""
        try:
            # 测试API连接
            client = await self._get_client()
            
            # 简单的连接测试
            response = await client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            self._is_loaded = True
            logger.info(f"Qwen API连接成功，模型: {self.config.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Qwen API连接失败: {e}")
            self._is_loaded = False
            return False
    
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """生成文本"""
        try:
            if not self._is_loaded:
                await self.load_model()
            
            client = await self._get_client()
            
            # 构建请求参数
            request_params = {
                'model': self.config.model_name,
                'messages': [{"role": "user", "content": prompt}],
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'frequency_penalty': kwargs.get('frequency_penalty', self.config.frequency_penalty),
                'presence_penalty': kwargs.get('presence_penalty', self.config.presence_penalty),
            }
            
            # 添加停止序列
            if self.config.stop_sequences:
                request_params['stop'] = self.config.stop_sequences
            
            response = await client.chat.completions.create(**request_params)
            
            # 解析响应
            message = response.choices[0].message
            usage = response.usage
            
            tokens_used = usage.total_tokens if usage else 0
            # 更新Token使用统计
            self._update_token_usage(tokens_used)
            
            return GenerationResult(
                text=message.content,
                tokens_used=tokens_used,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    'model': self.config.model_name,
                    'prompt_tokens': usage.prompt_tokens if usage else None,
                    'completion_tokens': usage.completion_tokens if usage else None,
                    'total_tokens': usage.total_tokens if usage else None
                }
            )
            
        except Exception as e:
            logger.error(f"Qwen API文本生成失败: {e}")
            raise Exception(f"Qwen API文本生成失败: {e}")
    
    async def generate_with_tools(self, prompt: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """使用工具生成"""
        try:
            client = await self._get_client()
            
            # 构建工具格式
            openai_tools = []
            for tool in tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.get('name', ''),
                        "description": tool.get('description', ''),
                        "parameters": tool.get('parameters', {})
                    }
                }
                openai_tools.append(openai_tool)
            
            # 构建请求
            request_params = {
                'model': self.config.model_name,
                'messages': [{"role": "user", "content": prompt}],
                'tools': openai_tools,
                'tool_choice': 'auto',
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            }
            
            response = await client.chat.completions.create(**request_params)
            
            # 解析工具调用
            tool_calls = []
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append(ToolCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ))
            
            return {
                'response': response.choices[0].message.content,
                'tool_calls': tool_calls,
                'metadata': {
                    'model': self.config.model_name,
                    'usage': response.usage.dict() if response.usage else {}
                }
            }
            
        except Exception as e:
            logger.error(f"Qwen API工具生成失败: {e}")
            raise Exception(f"Qwen API工具生成失败: {e}")
    
    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本"""
        try:
            client = await self._get_client()
            
            request_params = {
                'model': self.config.model_name,
                'messages': [{"role": "user", "content": prompt}],
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'stream': True
            }
            
            response = await client.chat.completions.create(**request_params)
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Qwen API流式生成失败: {e}")
            raise Exception(f"Qwen API流式生成失败: {e}")
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> GenerationResult:
        """聊天模式生成"""
        try:
            client = await self._get_client()
            
            request_params = {
                'model': self.config.model_name,
                'messages': messages,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            }
            
            response = await client.chat.completions.create(**request_params)
            
            message = response.choices[0].message
            usage = response.usage
            
            return GenerationResult(
                text=message.content,
                tokens_used=usage.total_tokens if usage else None,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    'model': self.config.model_name,
                    'prompt_tokens': usage.prompt_tokens if usage else None,
                    'completion_tokens': usage.completion_tokens if usage else None,
                    'total_tokens': usage.total_tokens if usage else None
                }
            )
            
        except Exception as e:
            logger.error(f"Qwen API聊天生成失败: {e}")
            raise Exception(f"Qwen API聊天生成失败: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_name': self.config.model_name,
            'is_loaded': self._is_loaded,
            'api_mode': True,
            'config': self.config.dict(),
            'api_config': self.api_config.dict() if self.api_config else {}
        } 