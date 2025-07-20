"""
Qwen模型实现 - 基于Ollama的本地部署
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .base import LLMBase, LLMConfig, GenerationResult, ToolCall, ToolResult

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Ollama配置"""
    host: str = "http://localhost:11434"
    model_name: str = "qwen3:8b"
    timeout: int = 30


class QwenLLM(LLMBase):
    """Qwen模型实现 - 基于Ollama"""
    
    def __init__(self, config: LLMConfig, ollama_config: Optional[OllamaConfig] = None):
        super().__init__(config)
        self.ollama_config = ollama_config or OllamaConfig()
        self._client = None
    
    async def _get_client(self):
        """获取Ollama客户端"""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.ollama_config.host)
            except ImportError:
                raise ImportError("请安装ollama: pip install ollama")
        return self._client
    
    async def load_model(self) -> bool:
        """加载Qwen模型"""
        try:
            client = await self._get_client()
            
            # 检查模型是否可用
            models = client.list()
            available_models = [m.get('name', '') for m in models.get('models', [])]
            
            if self.config.model_name not in available_models:
                logger.info(f"正在下载模型: {self.config.model_name}")
                client.pull(self.config.model_name)
                logger.info(f"模型 {self.config.model_name} 下载完成")
            
            self._is_loaded = True
            logger.info(f"模型 {self.config.model_name} 加载成功")
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self._is_loaded = False
            return False
    
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """生成文本"""
        try:
            if not self._is_loaded:
                await self.load_model()
            
            client = await self._get_client()
            
            # 合并配置参数
            options = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'top_k': kwargs.get('top_k', 40),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
                'stop': kwargs.get('stop_sequences', self.config.stop_sequences),
                'repeat_penalty': kwargs.get('frequency_penalty', 1.0),
                'seed': kwargs.get('seed', None)
            }
            
            # 移除None值
            options = {k: v for k, v in options.items() if v is not None}
            
            response = client.generate(
                model=self.config.model_name,
                prompt=prompt,
                options=options,
                stream=False
            )
            
            tokens_used = response.get('eval_count', 0)
            # 更新Token使用统计
            self._update_token_usage(tokens_used)
            
            return GenerationResult(
                text=response['response'],
                tokens_used=tokens_used,
                finish_reason=response.get('done_reason', None),
                metadata={
                    'model': self.config.model_name,
                    'prompt_tokens': response.get('prompt_eval_count', None),
                    'total_duration': response.get('total_duration', None)
                }
            )
            
        except Exception as e:
            logger.error(f"文本生成失败: {e}")
            raise Exception(f"文本生成失败: {e}")
    
    async def generate_with_tools(self, prompt: str, tools: List[Dict], **kwargs) -> Dict[str, Any]:
        """使用工具生成"""
        try:
            # 构建工具调用Prompt
            tool_prompt = self._build_tool_prompt(prompt, tools)
            response = await self.generate(tool_prompt, **kwargs)
            
            # 解析工具调用响应
            tool_calls = self._parse_tool_calls(response.text, tools)
            
            return {
                'response': response.text,
                'tool_calls': tool_calls,
                'metadata': response.metadata
            }
            
        except Exception as e:
            logger.error(f"工具生成失败: {e}")
            raise Exception(f"工具生成失败: {e}")
    
    def _build_tool_prompt(self, prompt: str, tools: List[Dict]) -> str:
        """构建工具调用Prompt"""
        tool_descriptions = []
        
        for i, tool in enumerate(tools, 1):
            name = tool.get('name', f'tool_{i}')
            description = tool.get('description', '')
            parameters = tool.get('parameters', {})
            
            param_desc = ""
            if parameters:
                param_list = []
                for param_name, param_info in parameters.get('properties', {}).items():
                    param_type = param_info.get('type', 'string')
                    param_desc_item = f"{param_name} ({param_type})"
                    if 'description' in param_info:
                        param_desc_item += f": {param_info['description']}"
                    param_list.append(param_desc_item)
                param_desc = f"参数: {', '.join(param_list)}"
            
            tool_desc = f"{i}. {name}: {description}"
            if param_desc:
                tool_desc += f" {param_desc}"
            tool_descriptions.append(tool_desc)
        
        tools_text = "\n".join(tool_descriptions)
        
        return f"""
{prompt}

可用工具:
{tools_text}

请根据需要使用上述工具完成任务。如果需要使用工具，请按以下格式输出：

工具名称: [工具名称]
参数: [JSON格式的参数]

如果不需要使用工具，请直接输出结果。
"""
    
    def _parse_tool_calls(self, response: str, tools: List[Dict]) -> List[ToolCall]:
        """解析工具调用响应"""
        tool_calls = []
        
        # 简单的工具调用解析
        lines = response.strip().split('\n')
        current_tool = None
        current_args = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('工具名称:'):
                if current_tool:
                    tool_calls.append(ToolCall(
                        name=current_tool,
                        arguments=current_args
                    ))
                current_tool = line.replace('工具名称:', '').strip()
                current_args = {}
            elif line.startswith('参数:') and current_tool:
                try:
                    import json
                    args_text = line.replace('参数:', '').strip()
                    current_args = json.loads(args_text)
                except:
                    # 如果JSON解析失败，尝试简单解析
                    args_text = line.replace('参数:', '').strip()
                    if args_text:
                        current_args = {'input': args_text}
        
        # 添加最后一个工具调用
        if current_tool:
            tool_calls.append(ToolCall(
                name=current_tool,
                arguments=current_args
            ))
        
        return tool_calls
    
    async def stream_generate(self, prompt: str, **kwargs):
        """流式生成文本"""
        try:
            if not self._is_loaded:
                await self.load_model()
            
            client = await self._get_client()
            
            options = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
            }
            
            response = client.generate(
                model=self.config.model_name,
                prompt=prompt,
                options=options,
                stream=True
            )
            
            for chunk in response:
                if chunk.get('response'):
                    yield chunk['response']
                    
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            raise Exception(f"流式生成失败: {e}")
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> GenerationResult:
        """聊天模式生成"""
        try:
            if not self._is_loaded:
                await self.load_model()
            
            client = await self._get_client()
            
            options = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'num_predict': kwargs.get('max_tokens', self.config.max_tokens),
            }
            
            response = client.chat(
                model=self.config.model_name,
                messages=messages,
                options=options
            )
            
            return GenerationResult(
                text=response['message']['content'],
                tokens_used=response.get('eval_count', None),
                finish_reason='stop',
                metadata={
                    'model': self.config.model_name,
                    'prompt_tokens': response.get('prompt_eval_count', None),
                    'total_duration': response.get('total_duration', None)
                }
            )
            
        except Exception as e:
            logger.error(f"聊天生成失败: {e}")
            raise Exception(f"聊天生成失败: {e}") 