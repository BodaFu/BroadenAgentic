"""
任务Agent - 根据具体任务要求构建的专用Agent
"""

from typing import Any, Dict, List, Optional
from .base import AgentBase, AgentConfig


class TaskAgent(AgentBase):
    """任务Agent - 根据具体任务要求构建的专用Agent"""
    
    def __init__(self, config: AgentConfig, llm):
        super().__init__(config, llm)
        self.task_type = getattr(config, 'task_type', 'general')
        self.required_tools = getattr(config, 'required_tools', [])
    
    async def execute_with_tools(self, input_data: Any, tools: List[Dict] = None, **kwargs) -> Any:
        """使用工具执行任务"""
        # 这里可以添加工具调用逻辑
        return await self.execute(input_data, **kwargs)
    
    def get_task_info(self) -> Dict[str, Any]:
        """获取任务信息"""
        return {
            'task_type': self.task_type,
            'required_tools': self.required_tools,
            'status': self.get_status()
        } 