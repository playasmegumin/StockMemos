"""事件预测结果请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional


class EventPredictionCreate(BaseModel):
    """创建预测结果请求"""
    event_node_id: str = Field(..., description="关联事件节点ID")
    outcome_label: str = Field(..., max_length=200, description="结果标签，如加息25bp")
    outcome_description: Optional[str] = Field(None, description="结果描述")
    probability_estimate: Optional[float] = Field(None, ge=0.0, le=1.0, description="概率0.00-1.00")
    impact_brief: Optional[str] = Field(None, description="若此结果发生，后续影响简要解析")
    is_actual_result: Optional[bool] = Field(False, description="是否为实际发生结果")


class EventPredictionResponse(BaseModel):
    """预测结果响应"""
    id: str
    event_node_id: str
    outcome_label: str
    outcome_description: Optional[str] = None
    probability_estimate: Optional[float] = None
    impact_brief: Optional[str] = None
    is_actual_result: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
