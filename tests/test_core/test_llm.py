"""
LLM模块测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.core.llm import LLMConfig, QwenLLM, GenerationResult


class TestLLMConfig:
    """测试LLM配置"""
    
    def test_llm_config_creation(self):
        """测试LLM配置创建"""
        config = LLMConfig(
            model_name="qwen2.5:7b",
            temperature=0.7,
            max_tokens=2048
        )
        
        assert config.model_name == "qwen2.5:7b"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
    
    def test_llm_config_defaults(self):
        """测试LLM配置默认值"""
        config = LLMConfig(model_name="test")
        
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.top_p == 0.9


class TestQwenLLM:
    """测试Qwen LLM"""
    
    @pytest.fixture
    def llm_config(self):
        """LLM配置fixture"""
        return LLMConfig(
            model_name="qwen2.5:7b",
            temperature=0.7,
            max_tokens=100
        )
    
    @pytest.fixture
    def mock_ollama_client(self):
        """模拟Ollama客户端"""
        mock_client = Mock()
        mock_client.list.return_value = {
            'models': [{'name': 'qwen2.5:7b'}]
        }
        mock_client.generate.return_value = {
            'response': 'Hello, world!',
            'eval_count': 10,
            'done_reason': 'stop'
        }
        return mock_client
    
    @pytest.mark.asyncio
    async def test_qwen_llm_creation(self, llm_config):
        """测试Qwen LLM创建"""
        with patch('app.core.llm.qwen.ollama') as mock_ollama:
            mock_client = Mock()
            mock_ollama.Client.return_value = mock_client
            mock_client.list.return_value = {'models': [{'name': 'qwen2.5:7b'}]}
            
            llm = QwenLLM(llm_config)
            assert llm.config == llm_config
            assert llm._is_loaded == False
    
    @pytest.mark.asyncio
    async def test_load_model_success(self, llm_config, mock_ollama_client):
        """测试模型加载成功"""
        with patch('app.core.llm.qwen.ollama') as mock_ollama:
            mock_ollama.Client.return_value = mock_ollama_client
            
            llm = QwenLLM(llm_config)
            result = await llm.load_model()
            
            assert result == True
            assert llm._is_loaded == True
    
    @pytest.mark.asyncio
    async def test_load_model_failure(self, llm_config):
        """测试模型加载失败"""
        with patch('app.core.llm.qwen.ollama') as mock_ollama:
            mock_client = Mock()
            mock_client.list.side_effect = Exception("Connection failed")
            mock_ollama.Client.return_value = mock_client
            
            llm = QwenLLM(llm_config)
            result = await llm.load_model()
            
            assert result == False
            assert llm._is_loaded == False
    
    @pytest.mark.asyncio
    async def test_generate_text(self, llm_config, mock_ollama_client):
        """测试文本生成"""
        with patch('app.core.llm.qwen.ollama') as mock_ollama:
            mock_ollama.Client.return_value = mock_ollama_client
            
            llm = QwenLLM(llm_config)
            llm._is_loaded = True
            
            result = await llm.generate("Hello")
            
            assert isinstance(result, GenerationResult)
            assert result.text == "Hello, world!"
            assert result.tokens_used == 10
            assert result.finish_reason == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_with_retry(self, llm_config, mock_ollama_client):
        """测试带重试的文本生成"""
        with patch('app.core.llm.qwen.ollama') as mock_ollama:
            mock_ollama.Client.return_value = mock_ollama_client
            
            llm = QwenLLM(llm_config)
            llm._is_loaded = True
            
            result = await llm.generate_with_retry("Hello")
            
            assert isinstance(result, GenerationResult)
            assert result.text == "Hello, world!"
    
    def test_is_loaded(self, llm_config):
        """测试模型加载状态检查"""
        llm = QwenLLM(llm_config)
        assert llm.is_loaded() == False
        
        llm._is_loaded = True
        assert llm.is_loaded() == True
    
    def test_get_model_info(self, llm_config):
        """测试获取模型信息"""
        llm = QwenLLM(llm_config)
        info = llm.get_model_info()
        
        assert info['model_name'] == "qwen2.5:7b"
        assert info['is_loaded'] == False
        assert 'config' in info


class TestGenerationResult:
    """测试生成结果"""
    
    def test_generation_result_creation(self):
        """测试生成结果创建"""
        result = GenerationResult(
            text="Hello, world!",
            tokens_used=10,
            finish_reason="stop",
            metadata={"model": "qwen2.5:7b"}
        )
        
        assert result.text == "Hello, world!"
        assert result.tokens_used == 10
        assert result.finish_reason == "stop"
        assert result.metadata["model"] == "qwen2.5:7b"
    
    def test_generation_result_defaults(self):
        """测试生成结果默认值"""
        result = GenerationResult(text="Hello")
        
        assert result.text == "Hello"
        assert result.tokens_used is None
        assert result.finish_reason is None
        assert result.metadata == {}


if __name__ == "__main__":
    pytest.main([__file__]) 