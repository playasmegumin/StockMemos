"""资金流水 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CapitalFlowCreate(BaseModel):
    """创建资金流水请求"""
    type: str = Field(..., pattern="^(deposit|withdraw|fee)$",
                      description="操作类型")
    amount: float = Field(..., gt=0, description="金额（用户填正数，后端转符号）")
    currency: Optional[str] = Field("CNY", max_length=10, description="币种")
    note: Optional[str] = Field(None, max_length=500, description="备注")


class CapitalFlowResponse(BaseModel):
    """资金流水响应"""
    id: str
    type: str
    amount: float
    currency: str
    note: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CapitalSummaryResponse(BaseModel):
    """资金汇总响应"""
    total_invested_cny: float = Field(0.0, description="总投入金额(CNY)")
    total_historical_pnl_cny: float = Field(0.0, description="历史总盈亏(CNY)")
    total_position_value_cny: float = Field(0.0, description="总持仓金额(CNY)")
    total_adjustment_cny: float = Field(0.0, description="历史盈亏调整偏移值(CNY)")
