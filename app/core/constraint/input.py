"""
输入约束 - 验证输入数据的类型和格式
"""

import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class InputTypeConstraint(BaseModel):
    """输入类型约束"""
    name: str = Field(..., description="约束名称")
    data_type: str = Field(..., description="数据类型")
    required: bool = Field(default=True, description="是否必需")
    min_length: Optional[int] = Field(default=None, ge=0, description="最小长度")
    max_length: Optional[int] = Field(default=None, gt=0, description="最大长度")
    pattern: Optional[str] = Field(default=None, description="正则表达式模式")
    allowed_values: Optional[List[Any]] = Field(default=None, description="允许的值列表")
    min_value: Optional[Union[int, float]] = Field(default=None, description="最小值")
    max_value: Optional[Union[int, float]] = Field(default=None, description="最大值")
    custom_validator: Optional[str] = Field(default=None, description="自定义验证函数")
    
    @validator('data_type')
    def validate_data_type(cls, v):
        """验证数据类型"""
        valid_types = {
            'string', 'integer', 'float', 'boolean', 'array', 'object',
            'image', 'audio', 'video', 'file', 'url', 'email', 'phone'
        }
        if v not in valid_types:
            raise ValueError(f"不支持的数据类型: {v}")
        return v
    
    def validate(self, data: Any) -> bool:
        """验证输入数据"""
        try:
            # 检查必需性
            if self.required and data is None:
                logger.warning(f"约束 {self.name}: 数据为None但为必需")
                return False
            
            if data is None:
                return True
            
            # 类型检查
            if not self._check_type(data):
                logger.warning(f"约束 {self.name}: 数据类型不匹配，期望 {self.data_type}")
                return False
            
            # 长度检查
            if not self._check_length(data):
                return False
            
            # 模式检查
            if not self._check_pattern(data):
                return False
            
            # 值范围检查
            if not self._check_value_range(data):
                return False
            
            # 允许值检查
            if not self._check_allowed_values(data):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"约束验证失败 {self.name}: {e}")
            return False
    
    def _check_type(self, data: Any) -> bool:
        """检查数据类型"""
        type_map = {
            'string': str,
            'integer': int,
            'float': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
            'image': str,  # 简化处理，实际可能需要更复杂的检查
            'audio': str,
            'video': str,
            'file': str,
            'url': str,
            'email': str,
            'phone': str
        }
        
        expected_type = type_map.get(self.data_type)
        if expected_type is None:
            return True  # 未知类型，跳过检查
        
        if isinstance(expected_type, tuple):
            return isinstance(data, expected_type)
        else:
            return isinstance(data, expected_type)
    
    def _check_length(self, data: Any) -> bool:
        """检查长度"""
        if not hasattr(data, '__len__'):
            return True
        
        length = len(data)
        
        if self.min_length is not None and length < self.min_length:
            logger.warning(f"约束 {self.name}: 长度 {length} 小于最小值 {self.min_length}")
            return False
        
        if self.max_length is not None and length > self.max_length:
            logger.warning(f"约束 {self.name}: 长度 {length} 大于最大值 {self.max_length}")
            return False
        
        return True
    
    def _check_pattern(self, data: Any) -> bool:
        """检查正则表达式模式"""
        if not self.pattern or not isinstance(data, str):
            return True
        
        try:
            if not re.match(self.pattern, data):
                logger.warning(f"约束 {self.name}: 数据不匹配模式 {self.pattern}")
                return False
        except re.error as e:
            logger.error(f"约束 {self.name}: 正则表达式错误 {e}")
            return False
        
        return True
    
    def _check_value_range(self, data: Any) -> bool:
        """检查数值范围"""
        if not isinstance(data, (int, float)):
            return True
        
        if self.min_value is not None and data < self.min_value:
            logger.warning(f"约束 {self.name}: 值 {data} 小于最小值 {self.min_value}")
            return False
        
        if self.max_value is not None and data > self.max_value:
            logger.warning(f"约束 {self.name}: 值 {data} 大于最大值 {self.max_value}")
            return False
        
        return True
    
    def _check_allowed_values(self, data: Any) -> bool:
        """检查允许的值"""
        if not self.allowed_values:
            return True
        
        if data not in self.allowed_values:
            logger.warning(f"约束 {self.name}: 值 {data} 不在允许列表中 {self.allowed_values}")
            return False
        
        return True
    
    def get_error_message(self, data: Any) -> Optional[str]:
        """获取验证错误消息"""
        if self.validate(data):
            return None
        
        if self.required and data is None:
            return f"字段 {self.name} 是必需的"
        
        if not self._check_type(data):
            return f"字段 {self.name} 类型错误，期望 {self.data_type}"
        
        if not self._check_length(data):
            if self.min_length and self.max_length:
                return f"字段 {self.name} 长度应在 {self.min_length}-{self.max_length} 之间"
            elif self.min_length:
                return f"字段 {self.name} 长度应不少于 {self.min_length}"
            elif self.max_length:
                return f"字段 {self.name} 长度应不超过 {self.max_length}"
        
        if not self._check_pattern(data):
            return f"字段 {self.name} 格式不正确"
        
        if not self._check_value_range(data):
            if self.min_value and self.max_value:
                return f"字段 {self.name} 值应在 {self.min_value}-{self.max_value} 之间"
            elif self.min_value:
                return f"字段 {self.name} 值应不少于 {self.min_value}"
            elif self.max_value:
                return f"字段 {self.name} 值应不超过 {self.max_value}"
        
        if not self._check_allowed_values(data):
            return f"字段 {self.name} 值应为: {', '.join(map(str, self.allowed_values))}"
        
        return f"字段 {self.name} 验证失败"


class InputConstraintSet(BaseModel):
    """输入约束集合"""
    constraints: List[InputTypeConstraint] = Field(default_factory=list, description="约束列表")
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """验证所有约束"""
        results = {}
        
        for constraint in self.constraints:
            field_data = data.get(constraint.name)
            results[constraint.name] = constraint.validate(field_data)
        
        return results
    
    def get_all_errors(self, data: Dict[str, Any]) -> List[str]:
        """获取所有验证错误"""
        errors = []
        
        for constraint in self.constraints:
            field_data = data.get(constraint.name)
            error_msg = constraint.get_error_message(field_data)
            if error_msg:
                errors.append(error_msg)
        
        return errors
    
    def is_valid(self, data: Dict[str, Any]) -> bool:
        """检查是否所有约束都通过"""
        return all(self.validate(data).values()) 