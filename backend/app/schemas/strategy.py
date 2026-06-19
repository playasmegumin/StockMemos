"""策略定义请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class StrategyCreate(BaseModel):
    """创建策略请求模型"""
    name: str = Field(..., max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    rules: Dict[str, Any] = Field(..., description="指标组合规则(JSON)")
    is_active: Optional[bool] = Field(True, description="是否启用")


class StrategyResponse(StrategyCreate):
    """策略响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
