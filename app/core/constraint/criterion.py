"""
输出标准判断 - 用户用自然语言描述的质量标准
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class CriterionMetric(BaseModel):
    """标准指标"""
    name: str = Field(..., description="指标名称")
    description: str = Field(..., description="指标描述")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="权重")
    threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="阈值")


class OutputCriterion(BaseModel):
    """输出标准判断 - 用户用自然语言描述的质量标准"""
    name: str = Field(..., description="标准名称")
    description: str = Field(..., description="自然语言描述的质量标准")
    criteria: List[CriterionMetric] = Field(default_factory=list, description="具体指标")
    weights: Dict[str, float] = Field(default_factory=dict, description="指标权重")
    min_score: float = Field(default=0.8, ge=0.0, le=1.0, description="最低合格分数")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    
    def __post_init__(self):
        """初始化后处理"""
        # 如果没有具体指标，从描述中提取
        if not self.criteria:
            self.criteria = self._extract_criteria_from_description()
    
    def _extract_criteria_from_description(self) -> List[CriterionMetric]:
        """从描述中提取指标"""
        criteria = []
        
        # 常见的质量指标
        common_metrics = {
            '准确性': '输出内容是否准确无误',
            '完整性': '输出内容是否完整',
            '相关性': '输出内容是否与输入相关',
            '一致性': '输出内容是否一致',
            '清晰度': '输出内容是否清晰易懂',
            '专业性': '输出内容是否专业',
            '创新性': '输出内容是否有创新性',
            '实用性': '输出内容是否实用'
        }
        
        # 根据描述匹配指标
        description_lower = self.description.lower()
        
        for metric_name, metric_desc in common_metrics.items():
            if any(keyword in description_lower for keyword in metric_name.lower().split()):
                criteria.append(CriterionMetric(
                    name=metric_name,
                    description=metric_desc,
                    weight=1.0
                ))
        
        # 如果没有匹配到任何指标，添加默认指标
        if not criteria:
            criteria.append(CriterionMetric(
                name="总体质量",
                description="整体输出质量评估",
                weight=1.0
            ))
        
        return criteria
    
    async def evaluate(self, output: Any, llm=None) -> float:
        """评估输出质量"""
        try:
            if not self.criteria:
                return 0.5  # 默认分数
            
            total_score = 0.0
            total_weight = 0.0
            
            for criterion in self.criteria:
                weight = self.weights.get(criterion.name, criterion.weight)
                score = await self._evaluate_criterion(criterion, output, llm)
                
                total_score += score * weight
                total_weight += weight
            
            final_score = total_score / total_weight if total_weight > 0 else 0.0
            logger.info(f"输出质量评估: {final_score:.3f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            return 0.0
    
    async def _evaluate_criterion(self, criterion: CriterionMetric, output: Any, llm=None) -> float:
        """评估单个标准"""
        try:
            if llm is None:
                # 如果没有LLM，使用简单规则评估
                return self._simple_evaluation(criterion, output)
            
            # 使用LLM评估
            return await self._llm_evaluation(criterion, output, llm)
            
        except Exception as e:
            logger.error(f"标准评估失败 {criterion.name}: {e}")
            return 0.5
    
    def _simple_evaluation(self, criterion: CriterionMetric, output: Any) -> float:
        """简单规则评估"""
        if not isinstance(output, str):
            return 0.5
        
        output_lower = output.lower()
        
        # 根据指标名称进行简单评估
        if '准确性' in criterion.name:
            # 检查是否包含错误信息
            error_keywords = ['错误', '失败', '无效', '不正确']
            if any(keyword in output_lower for keyword in error_keywords):
                return 0.3
            return 0.8
        
        elif '完整性' in criterion.name:
            # 检查长度和内容完整性
            if len(output) < 10:
                return 0.4
            elif len(output) > 100:
                return 0.9
            return 0.7
        
        elif '相关性' in criterion.name:
            # 检查是否包含输入相关内容
            return 0.7
        
        elif '清晰度' in criterion.name:
            # 检查语言清晰度
            if len(output.split()) > 5:
                return 0.8
            return 0.6
        
        else:
            return 0.7
    
    async def _llm_evaluation(self, criterion: CriterionMetric, output: Any, llm) -> float:
        """使用LLM评估"""
        try:
            prompt = f"""
请评估以下输出是否符合标准，评分范围0-1：

标准: {criterion.description}
输出: {output}

请从{self.min_score}到1.0之间给出一个分数，只返回数字：
"""
            
            response = await llm.generate(prompt, max_tokens=10)
            score_text = response.text.strip()
            
            try:
                score = float(score_text)
                # 确保分数在合理范围内
                score = max(0.0, min(1.0, score))
                return score
            except ValueError:
                logger.warning(f"无法解析LLM评估分数: {score_text}")
                return 0.5
                
        except Exception as e:
            logger.error(f"LLM评估失败: {e}")
            return 0.5
    
    def is_satisfied(self, score: float) -> bool:
        """检查是否满足标准"""
        return score >= self.min_score
    
    def get_feedback(self, score: float) -> str:
        """获取评估反馈"""
        if score >= self.min_score:
            return f"输出质量良好 (分数: {score:.3f})"
        elif score >= 0.6:
            return f"输出质量一般，需要改进 (分数: {score:.3f})"
        else:
            return f"输出质量较差，需要重新生成 (分数: {score:.3f})"
    
    def get_improvement_suggestions(self, score: float) -> List[str]:
        """获取改进建议"""
        suggestions = []
        
        if score < self.min_score:
            suggestions.append("输出质量不达标，建议重新生成")
            
            if score < 0.5:
                suggestions.append("检查输入约束和输出要求")
                suggestions.append("优化Prompt模板")
            
            if score < 0.7:
                suggestions.append("增加输出内容的详细程度")
                suggestions.append("确保输出格式正确")
        
        return suggestions


class CriterionEvaluator:
    """标准评估器"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.evaluation_history = []
    
    async def evaluate_output(self, output: Any, criterion: OutputCriterion) -> Dict[str, Any]:
        """评估输出"""
        score = await criterion.evaluate(output, self.llm)
        is_satisfied = criterion.is_satisfied(score)
        feedback = criterion.get_feedback(score)
        suggestions = criterion.get_improvement_suggestions(score)
        
        result = {
            'score': score,
            'is_satisfied': is_satisfied,
            'feedback': feedback,
            'suggestions': suggestions,
            'criterion_name': criterion.name,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        self.evaluation_history.append(result)
        return result
    
    def get_evaluation_history(self) -> List[Dict[str, Any]]:
        """获取评估历史"""
        return self.evaluation_history
    
    def get_average_score(self) -> float:
        """获取平均分数"""
        if not self.evaluation_history:
            return 0.0
        
        scores = [result['score'] for result in self.evaluation_history]
        return sum(scores) / len(scores)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if not self.evaluation_history:
            return 0.0
        
        successful = sum(1 for result in self.evaluation_history if result['is_satisfied'])
        return successful / len(self.evaluation_history) 