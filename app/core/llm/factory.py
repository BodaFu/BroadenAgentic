"""
LLM工厂类 - 自动选择本地或云端模型
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from .base import LLMBase, LLMConfig
from .qwen import QwenLLM
from .qwen_api import QwenAPILLM, QwenAPIConfig

logger = logging.getLogger(__name__)


class LLMFactoryConfig(BaseModel):
    """LLM工厂配置"""
    preferred_mode: str = Field(default="local", description="首选模式: local/cloud/auto")
    local_model_name: str = Field(default="qwen3:8b", description="本地模型名称")
    cloud_model_name: str = Field(default="qwen-plus", description="云端模型名称")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="API基础URL")
    fallback_to_cloud: bool = Field(default=True, description="本地失败时是否回退到云端")
    health_check_timeout: int = Field(default=10, description="健康检查超时时间")


class LLMFactory:
    """LLM工厂类 - 自动选择本地或云端模型"""
    
    def __init__(self, config: LLMFactoryConfig):
        self.config = config
        self._local_llm = None
        self._cloud_llm = None
        self._current_mode = None
    
    async def create_llm(self, llm_config: Optional[LLMConfig] = None) -> LLMBase:
        """创建LLM实例"""
        if llm_config is None:
            llm_config = LLMConfig(
                model_name=self.config.local_model_name,
                temperature=0.7,
                max_tokens=4096
            )
        
        if self.config.preferred_mode == "local":
            return await self._create_local_llm(llm_config)
        elif self.config.preferred_mode == "cloud":
            return await self._create_cloud_llm(llm_config)
        else:  # auto
            return await self._create_auto_llm(llm_config)
    
    async def _create_local_llm(self, llm_config: LLMConfig) -> LLMBase:
        """创建本地LLM"""
        if self._local_llm is None:
            self._local_llm = QwenLLM(llm_config)
        
        # 检查本地模型是否可用
        if await self._check_local_health():
            self._current_mode = "local"
            logger.info("使用本地Ollama模型")
            return self._local_llm
        else:
            raise Exception("本地模型不可用")
    
    async def _create_cloud_llm(self, llm_config: LLMConfig) -> LLMBase:
        """创建云端LLM"""
        if self._cloud_llm is None:
            if not self.config.api_key:
                raise ValueError("云端模式需要API密钥")
            
            api_config = QwenAPIConfig(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                model_name=self.config.cloud_model_name
            )
            
            # 更新配置以使用云端模型名称
            llm_config.model_name = self.config.cloud_model_name
            self._cloud_llm = QwenAPILLM(llm_config, api_config)
        
        # 检查云端模型是否可用
        if await self._check_cloud_health():
            self._current_mode = "cloud"
            logger.info("使用云端Qwen API模型")
            return self._cloud_llm
        else:
            raise Exception("云端模型不可用")
    
    async def _create_auto_llm(self, llm_config: LLMConfig) -> LLMBase:
        """自动选择LLM"""
        # 首先尝试本地模型
        try:
            local_llm = await self._create_local_llm(llm_config)
            return local_llm
        except Exception as e:
            logger.warning(f"本地模型不可用: {e}")
            
            if self.config.fallback_to_cloud:
                try:
                    cloud_llm = await self._create_cloud_llm(llm_config)
                    return cloud_llm
                except Exception as e2:
                    logger.error(f"云端模型也不可用: {e2}")
                    raise Exception("本地和云端模型都不可用")
            else:
                raise Exception("本地模型不可用且未启用云端回退")
    
    async def _check_local_health(self) -> bool:
        """检查本地模型健康状态"""
        try:
            if self._local_llm is None:
                return False
            
            # 设置超时
            return await asyncio.wait_for(
                self._local_llm.health_check(),
                timeout=self.config.health_check_timeout
            )
        except Exception as e:
            logger.warning(f"本地模型健康检查失败: {e}")
            return False
    
    async def _check_cloud_health(self) -> bool:
        """检查云端模型健康状态"""
        try:
            if self._cloud_llm is None:
                return False
            
            # 设置超时
            return await asyncio.wait_for(
                self._cloud_llm.health_check(),
                timeout=self.config.health_check_timeout
            )
        except Exception as e:
            logger.warning(f"云端模型健康检查失败: {e}")
            return False
    
    def get_current_mode(self) -> Optional[str]:
        """获取当前使用的模式"""
        return self._current_mode
    
    def get_available_modes(self) -> Dict[str, bool]:
        """获取可用模式"""
        return {
            "local": self._local_llm is not None and self._local_llm.is_loaded(),
            "cloud": self._cloud_llm is not None and self._cloud_llm.is_loaded()
        }
    
    async def switch_mode(self, mode: str, llm_config: Optional[LLMConfig] = None) -> LLMBase:
        """切换模式"""
        if llm_config is None:
            if mode == "local":
                llm_config = LLMConfig(
                    model_name=self.config.local_model_name,
                    temperature=0.7,
                    max_tokens=2048
                )
            else:
                llm_config = LLMConfig(
                    model_name=self.config.cloud_model_name,
                    temperature=0.7,
                    max_tokens=2048
                )
        
        if mode == "local":
            return await self._create_local_llm(llm_config)
        elif mode == "cloud":
            return await self._create_cloud_llm(llm_config)
        else:
            raise ValueError(f"不支持的模式: {mode}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "current_mode": self._current_mode,
            "preferred_mode": self.config.preferred_mode,
            "available_modes": self.get_available_modes()
        }
        
        if self._local_llm:
            info["local_model"] = self._local_llm.get_model_info()
        
        if self._cloud_llm:
            info["cloud_model"] = self._cloud_llm.get_model_info()
        
        return info 