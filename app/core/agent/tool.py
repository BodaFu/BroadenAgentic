"""
工具Agent - 基本工具Agent，高频复用的功能Agent
"""

from typing import Any, Dict, List, Optional
from .base import AgentBase, AgentConfig


class ToolAgent(AgentBase):
    """工具Agent - 基本工具Agent，高频复用的功能Agent"""
    
    def __init__(self, config: AgentConfig, llm):
        super().__init__(config, llm)
        self.tool_type = getattr(config, 'tool_type', 'general')
        self.capabilities = getattr(config, 'capabilities', [])
    
    async def execute_tool(self, tool_name: str, tool_args: Dict[str, Any], **kwargs) -> Any:
        """执行特定工具"""
        # 这里可以添加具体的工具执行逻辑
        input_data = {
            'tool_name': tool_name,
            'tool_args': tool_args
        }
        return await self.execute(input_data, **kwargs)
    
    def get_tool_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            'tool_type': self.tool_type,
            'capabilities': self.capabilities,
            'status': self.get_status()
        } 