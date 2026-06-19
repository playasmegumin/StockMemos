"""持仓 CRUD API + 仓位管理 Dashboard

Endpoints:
    POST   /api/portfolio              — 创建持仓
    GET    /api/portfolio              — 持仓列表
    GET    /api/portfolio/dashboard    — 仓位管理 Dashboard
    GET    /api/portfolio/{id}         — 单条持仓
    PUT    /api/portfolio/{id}         — 更新持仓
    DELETE /api/portfolio/{id}         — 删除持仓
    POST   /api/portfolio/{id}/trade   — 记录交易点
    GET    /api/portfolio/{id}/trades  — 交易点列表
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.portfolio import Portfolio
from app.models.trade_point import TradePoint
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioWithPnl,
    PortfolioDashboardSummary,
    PortfolioDashboardResponse,
)
from app.schemas.trade_point import TradePointCreate, TradePointResponse
from app.services.tushare_client import TushareClient

router = APIRouter()

# 全局 TuShare 客户端（单例，启动时自动连接）
tushare_client = TushareClient()


# ────────────────────────────────
# 辅助函数：ORM → Pydantic 响应转换
# ────────────────────────────────

def _to_portfolio_response(item: Portfolio) -> PortfolioResponse:
    """将 Portfolio ORM 对象转换为 Pydantic 响应（处理 Decimal / datetime 类型）"""
    return PortfolioResponse(
        id=item.id,
        stock_code=item.stock_code,
        stock_name=item.stock_name,
        quantity=item.quantity,
        cost_price=float(item.cost_price),
        build_date=item.build_date,
        status=item.status,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


def _to_trade_point_response(item: TradePoint) -> TradePointResponse:
    """将 TradePoint ORM 对象转换为 Pydantic 响应"""
    return TradePointResponse(
        id=item.id,
        portfolio_id=item.portfolio_id,
        type=item.type,
        price=float(item.price) if item.price is not None else None,
        reason=item.reason,
        report_id=item.report_id,
        trade_date=item.trade_date,
        created_at=str(item.created_at) if item.created_at else None,
    )


def _calc_position_pnl(pos: Portfolio) -> PortfolioWithPnl:
    """为单条持仓计算最新盈亏（TuShare 实时价格）"""
    latest_price = tushare_client.get_latest_price(pos.stock_code)
    market_value = latest_price * pos.quantity
    cost_value = float(pos.cost_price) * pos.quantity
    floating_pnl = market_value - cost_value
    pnl_rate = (floating_pnl / cost_value) if cost_value else 0.0

    return PortfolioWithPnl(
        id=pos.id,
        stock_code=pos.stock_code,
        stock_name=pos.stock_name,
        quantity=pos.quantity,
        cost_price=float(pos.cost_price),
        build_date=pos.build_date,
        latest_price=latest_price,
        market_value=market_value,
        floating_pnl=floating_pnl,
        pnl_rate=pnl_rate,
        status=pos.status,
        created_at=str(pos.created_at) if pos.created_at else None,
        updated_at=str(pos.updated_at) if pos.updated_at else None,
    )


# ────────────────────────────────
# 创建持仓
# ────────────────────────────────

@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    """录入新持仓"""
    db_item = Portfolio(
        id=str(uuid4()),
        stock_code=data.stock_code,
        stock_name=data.stock_name,
        quantity=data.quantity,
        cost_price=data.cost_price,
        build_date=data.build_date,
        status=data.status or "holding",
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_portfolio_response(db_item)


# ────────────────────────────────
# 获取持仓列表
# ────────────────────────────────

@router.get("", response_model=List[PortfolioResponse])
def list_portfolio(db: Session = Depends(get_db)):
    """获取所有持仓（不含实时盈亏）"""
    items = db.query(Portfolio).order_by(Portfolio.created_at.desc()).all()
    return [_to_portfolio_response(i) for i in items]


# ────────────────────────────────
# 仓位管理 Dashboard（专用聚合接口）
# ────────────────────────────────

@router.get("/dashboard", response_model=PortfolioDashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    """仓位管理 Dashboard

    返回所有持仓的实时盈亏明细 + 汇总卡片数据。
    - 最新价格通过 TuShare 实时拉取（1 小时缓存）
    - 浮动盈亏 = (最新价 - 成本价) × 数量
    - 盈亏率 = 浮动盈亏 / 总成本
    """
    positions = (
        db.query(Portfolio)
        .filter(Portfolio.status == "holding")
        .order_by(Portfolio.created_at.desc())
        .all()
    )

    enriched: List[PortfolioWithPnl] = []
    total_cost = 0.0
    total_market_value = 0.0

    for pos in positions:
        row = _calc_position_pnl(pos)
        enriched.append(row)
        total_cost += float(pos.cost_price) * pos.quantity
        total_market_value += row.market_value

    total_floating_pnl = total_market_value - total_cost
    total_pnl_rate = (total_floating_pnl / total_cost) if total_cost else 0.0

    return PortfolioDashboardResponse(
        positions=enriched,
        summary=PortfolioDashboardSummary(
            total_cost=total_cost,
            total_market_value=total_market_value,
            total_floating_pnl=total_floating_pnl,
            total_pnl_rate=total_pnl_rate,
            position_count=len(enriched),
        ),
    )


# ────────────────────────────────
# 获取单条持仓
# ────────────────────────────────

@router.get("/{id}", response_model=PortfolioResponse)
def get_portfolio(id: str, db: Session = Depends(get_db)):
    """获取单条持仓详情"""
    item = db.query(Portfolio).filter(Portfolio.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return _to_portfolio_response(item)


# ────────────────────────────────
# 更新持仓
# ────────────────────────────────

@router.put("/{id}", response_model=PortfolioResponse)
def update_portfolio(id: str, data: PortfolioCreate, db: Session = Depends(get_db)):
    """更新持仓（全部字段覆盖）"""
    item = db.query(Portfolio).filter(Portfolio.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="持仓不存在")

    item.stock_code = data.stock_code
    item.stock_name = data.stock_name
    item.quantity = data.quantity
    item.cost_price = data.cost_price
    item.build_date = data.build_date
    item.status = data.status or item.status

    db.commit()
    db.refresh(item)
    return _to_portfolio_response(item)


# ────────────────────────────────
# 删除持仓
# ────────────────────────────────

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(id: str, db: Session = Depends(get_db)):
    """删除持仓（级联删除关联 trade_point）"""
    item = db.query(Portfolio).filter(Portfolio.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="持仓不存在")
    db.delete(item)
    db.commit()
    return None


# ────────────────────────────────
# 记录买卖点
# ────────────────────────────────

@router.post("/{id}/trade", response_model=TradePointResponse, status_code=status.HTTP_201_CREATED)
def create_trade(id: str, data: TradePointCreate, db: Session = Depends(get_db)):
    """为某持仓记录交易点（加仓/减仓/止损/止盈）"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="持仓不存在")

    db_item = TradePoint(
        id=str(uuid4()),
        portfolio_id=id,
        type=data.type,
        price=data.price,
        reason=data.reason,
        report_id=data.report_id,
        trade_date=data.trade_date,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_trade_point_response(db_item)


# ────────────────────────────────
# 获取某持仓的买卖点列表
# ────────────────────────────────

@router.get("/{id}/trades", response_model=List[TradePointResponse])
def list_trades(id: str, db: Session = Depends(get_db)):
    """获取某持仓的所有交易点"""
    portfolio = db.query(Portfolio).filter(Portfolio.id == id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="持仓不存在")
    items = (
        db.query(TradePoint)
        .filter(TradePoint.portfolio_id == id)
        .order_by(TradePoint.created_at.desc())
        .all()
    )
    return [_to_trade_point_response(i) for i in items]
