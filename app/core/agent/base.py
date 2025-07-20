"""
Agent基类 - 在LLM基类上的包装层，提供质量控制
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ..llm.base import LLMBase, GenerationResult
from ..constraint.input import InputTypeConstraint, InputConstraintSet
from ..constraint.output import OutputTypeConstraint, OutputConstraintSet
from ..constraint.criterion import OutputCriterion

logger = logging.getLogger(__name__)


class AgentStatus(str):
    """Agent状态"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class AgentConfig(BaseModel):
    """Agent配置"""
    name: str = Field(..., description="Agent名称")
    description: str = Field(..., description="Agent描述")
    input_constraints: List[InputTypeConstraint] = Field(default_factory=list, description="输入约束")
    output_constraints: List[OutputTypeConstraint] = Field(default_factory=list, description="输出约束")
    output_criterion: OutputCriterion = Field(..., description="输出标准")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    timeout: int = Field(default=30, gt=0, description="超时时间(秒)")
    enable_auto_optimization: bool = Field(default=True, description="启用自动优化")


class AgentBase:
    """Agent基类 - 在LLM基类上的包装层"""
    
    def __init__(self, config: AgentConfig, llm: LLMBase):
        self.config = config
        self.llm = llm
        self.status = AgentStatus.IDLE
        self.retry_count = 0
        self.execution_history = []
        self.performance_metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'average_score': 0.0,
            'average_response_time': 0.0
        }
    
    async def execute(self, input_data: Any, **kwargs) -> Any:
        """执行任务"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.status = AgentStatus.BUSY
            self.performance_metrics['total_executions'] += 1
            
            # 验证输入约束
            self._validate_input(input_data)
            
            # 生成输出
            output = await self._generate_output(input_data, **kwargs)
            
            # 验证输出约束
            self._validate_output(output)
            
            # 评估输出质量
            quality_score = await self._evaluate_quality(output)
            
            # 获取Token使用统计
            llm_token_usage = self.llm.get_token_usage()
            tokens_used = llm_token_usage.get('total_tokens_used', 0)
            
            # 记录执行历史
            execution_record = {
                'timestamp': datetime.utcnow(),
                'input': input_data,
                'output': output,
                'quality_score': quality_score,
                'response_time': asyncio.get_event_loop().time() - start_time,
                'retry_count': self.retry_count,
                'tokens_used': tokens_used
            }
            self.execution_history.append(execution_record)
            
            # 如果质量不达标，尝试优化
            if quality_score < self.config.output_criterion.min_score and self.retry_count < self.config.max_retries:
                self.retry_count += 1
                logger.info(f"输出质量不达标 ({quality_score:.3f})，尝试优化 (重试 {self.retry_count}/{self.config.max_retries})")
                return await self._optimize_and_retry(input_data, output, quality_score, **kwargs)
            
            # 更新性能指标
            self._update_performance_metrics(quality_score, execution_record['response_time'], tokens_used)
            
            self.status = AgentStatus.IDLE
            self.retry_count = 0
            
            return output
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent执行失败: {e}")
            raise
    
    def _validate_input(self, input_data: Any):
        """验证输入约束"""
        if not self.config.input_constraints:
            return
        
        constraint_set = InputConstraintSet(constraints=self.config.input_constraints)
        
        # 将输入数据转换为字典格式进行验证
        if isinstance(input_data, dict):
            input_dict = input_data
        else:
            # 为每个约束创建输入数据
            input_dict = {}
            for constraint in self.config.input_constraints:
                input_dict[constraint.name] = input_data
        
        if not constraint_set.is_valid(input_dict):
            errors = constraint_set.get_all_errors(input_dict)
            raise ValueError(f"输入验证失败: {'; '.join(errors)}")
    
    def _validate_output(self, output: Any):
        """验证输出约束"""
        if not self.config.output_constraints:
            return
        
        constraint_set = OutputConstraintSet(constraints=self.config.output_constraints)
        
        # 将输出数据转换为字典格式进行验证
        if isinstance(output, dict):
            output_dict = output
        else:
            # 为每个约束创建输出数据
            output_dict = {}
            for constraint in self.config.output_constraints:
                output_dict[constraint.name] = output
        
        if not constraint_set.is_valid(output_dict):
            errors = constraint_set.get_all_errors(output_dict)
            raise ValueError(f"输出验证失败: {'; '.join(errors)}")
    
    async def _evaluate_quality(self, output: Any) -> float:
        """评估输出质量"""
        try:
            return await self.config.output_criterion.evaluate(output, self.llm)
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            return 0.5  # 默认分数
    
    async def _generate_output(self, input_data: Any, **kwargs) -> Any:
        """生成输出"""
        prompt = self._build_prompt(input_data)
        
        try:
            result = await self.llm.generate_with_retry(prompt, **kwargs)
            return result.text
        except Exception as e:
            logger.error(f"输出生成失败: {e}")
            raise
    
    def _build_prompt(self, input_data: Any) -> str:
        """构建Prompt"""
        # 基础Prompt模板
        base_prompt = f"""
任务描述: {self.config.description}

输入数据: {input_data}

输出要求: {self.config.output_criterion.description}

请根据任务描述和输入数据生成符合要求的输出。
"""
        
        # 添加约束信息
        if self.config.input_constraints:
            constraint_info = "\n输入约束:\n"
            for constraint in self.config.input_constraints:
                constraint_info += f"- {constraint.name}: {constraint.data_type}"
                if hasattr(constraint, 'description') and constraint.description:
                    constraint_info += f" ({constraint.description})"
                constraint_info += "\n"
            base_prompt += constraint_info
        
        if self.config.output_constraints:
            constraint_info = "\n输出约束:\n"
            for constraint in self.config.output_constraints:
                constraint_info += f"- {constraint.name}: {constraint.data_type}"
                if hasattr(constraint, 'description') and constraint.description:
                    constraint_info += f" ({constraint.description})"
                constraint_info += "\n"
            base_prompt += constraint_info
        
        return base_prompt
    
    async def _optimize_and_retry(self, input_data: Any, previous_output: Any, 
                                quality_score: float, **kwargs) -> Any:
        """优化并重试"""
        try:
            # 基于质量评估结果优化Prompt
            optimized_prompt = await self._optimize_prompt(input_data, previous_output, quality_score)
            
            # 使用优化后的Prompt重新生成
            result = await self.llm.generate_with_retry(optimized_prompt, **kwargs)
            return result.text
            
        except Exception as e:
            logger.error(f"优化重试失败: {e}")
            raise
    
    async def _optimize_prompt(self, input_data: Any, previous_output: Any, 
                              quality_score: float) -> str:
        """优化Prompt"""
        if not self.config.enable_auto_optimization:
            return self._build_prompt(input_data)
        
        optimization_prompt = f"""
原始任务描述: {self.config.description}

输入数据: {input_data}

上次输出: {previous_output}

质量评分: {quality_score:.3f}

输出标准: {self.config.output_criterion.description}

请分析问题并提供改进的任务描述，要求：
1. 保持原有意图
2. 提高输出质量
3. 更清晰的指令
4. 更好的约束条件

改进后的任务描述:
"""
        
        try:
            result = await self.llm.generate(optimization_prompt, max_tokens=200)
            optimized_description = result.text.strip()
            
            # 使用优化后的描述构建新的Prompt
            return f"""
任务描述: {optimized_description}

输入数据: {input_data}

输出要求: {self.config.output_criterion.description}

请根据任务描述和输入数据生成符合要求的输出。
"""
            
        except Exception as e:
            logger.error(f"Prompt优化失败: {e}")
            return self._build_prompt(input_data)
    
    def _update_performance_metrics(self, quality_score: float, response_time: float, tokens_used: int):
        """更新性能指标"""
        if quality_score >= self.config.output_criterion.min_score:
            self.performance_metrics['successful_executions'] += 1
        
        # 更新平均分数
        total_executions = self.performance_metrics['total_executions']
        current_avg = self.performance_metrics['average_score']
        self.performance_metrics['average_score'] = (current_avg * (total_executions - 1) + quality_score) / total_executions
        
        # 更新平均响应时间
        current_avg_time = self.performance_metrics['average_response_time']
        self.performance_metrics['average_response_time'] = (current_avg_time * (total_executions - 1) + response_time) / total_executions
        
        # 更新Token使用统计
        self.performance_metrics['total_tokens_used'] += tokens_used
        self.performance_metrics['average_tokens_per_execution'] = self.performance_metrics['total_tokens_used'] / total_executions
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            'name': self.config.name,
            'status': self.status,
            'retry_count': self.retry_count,
            'performance_metrics': self.performance_metrics.copy(),
            'execution_count': len(self.execution_history)
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history[-limit:]
    
    def reset_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'average_score': 0.0,
            'average_response_time': 0.0,
            'total_tokens_used': 0,
            'average_tokens_per_execution': 0.0
        }
        self.execution_history = []
        # 重置LLM的Token统计
        self.llm.reset_token_usage()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return await self.llm.health_check()
        except Exception as e:
            logger.error(f"Agent健康检查失败: {e}")
            return False 