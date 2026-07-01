"""个股分析 CRUD API

Endpoints:
    GET    /api/stock-analyze/stock/{stock_id}              — 获取个股分析（不存在则自动创建）
    PUT    /api/stock-analyze/{id}                          — 更新基本面数据
    DELETE /api/stock-analyze/{id}                          — 删除个股分析（级联删子表）

    # Reports（分析报告）
    GET    /api/stock-analyze/{id}/reports                  — 获取报告列表
    POST   /api/stock-analyze/{id}/reports                  — 创建报告
    GET    /api/stock-analyze/{id}/reports/{rid}            — 获取单条报告
    PUT    /api/stock-analyze/{id}/reports/{rid}            — 更新报告
    DELETE /api/stock-analyze/{id}/reports/{rid}            — 删除报告

    # TpSlPoints（止盈止损点）
    GET    /api/stock-analyze/{id}/tp-sl-points             — 获取止盈止损点列表
    POST   /api/stock-analyze/{id}/tp-sl-points             — 创建止盈止损点
    PUT    /api/stock-analyze/{id}/tp-sl-points/{pid}       — 更新止盈止损点
    DELETE /api/stock-analyze/{id}/tp-sl-points/{pid}       — 删除止盈止损点

    # StockTags（个股标签）
    GET    /api/stock-analyze/{id}/stock-tags               — 获取标签列表
    POST   /api/stock-analyze/{id}/stock-tags               — 创建标签
    DELETE /api/stock-analyze/{id}/stock-tags/{tid}         — 删除标签
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock import Stock
from app.models.stock_analyze import StockAnalyze
from app.models.report import Report
from app.models.tp_sl_point import TpSlPoint
from app.models.stock_tag import StockTag
from app.schemas.stock_analyze import StockAnalyzeCreate, StockAnalyzeResponse
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse
from app.schemas.tp_sl_point import TpSlPointCreate, TpSlPointUpdate, TpSlPointResponse
from app.schemas.stock_tag import StockTagCreate, StockTagUpdate, StockTagResponse

router = APIRouter()


# ═══════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════

def _get_analyze_or_404(id: str, db: Session) -> StockAnalyze:
    item = db.query(StockAnalyze).filter(StockAnalyze.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股分析不存在")
    return item


def _to_analyze_response(item: StockAnalyze) -> StockAnalyzeResponse:
    return StockAnalyzeResponse(
        id=item.id,
        stock_id=item.stock_id,
        fundamentals_data=item.fundamentals_data,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


def _to_report_response(item: Report) -> ReportResponse:
    return ReportResponse(
        id=item.id,
        stock_analyze_id=item.stock_analyze_id,
        generated_at=str(item.generated_at) if item.generated_at else None,
        title=item.title,
        content=item.content,
        created_at=str(item.created_at) if item.created_at else None,
    )


def _to_tp_sl_response(item: TpSlPoint) -> TpSlPointResponse:
    return TpSlPointResponse(
        id=item.id,
        stock_analyze_id=item.stock_analyze_id,
        price=float(item.price),
        label=item.label,
        notes=item.notes,
        created_at=str(item.created_at) if item.created_at else None,
    )


def _to_tag_response(item: StockTag) -> StockTagResponse:
    return StockTagResponse(
        id=item.id,
        stock_analyze_id=item.stock_analyze_id,
        tag=item.tag,
        created_at=str(item.created_at) if item.created_at else None,
    )


# ═══════════════════════════════════════
# StockAnalyze 主体
# ═══════════════════════════════════════

@router.get("/stock/{stock_id}", response_model=StockAnalyzeResponse)
def get_or_create_analyze(stock_id: str, db: Session = Depends(get_db)):
    """获取个股分析（不存在则自动创建空记录）"""
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="个股不存在")

    item = db.query(StockAnalyze).filter(StockAnalyze.stock_id == stock_id).first()
    if item:
        return _to_analyze_response(item)

    # 自动创建
    new_item = StockAnalyze(
        id=str(uuid4()),
        stock_id=stock_id,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return _to_analyze_response(new_item)


@router.put("/{id}", response_model=StockAnalyzeResponse)
def update_analyze(id: str, data: StockAnalyzeCreate, db: Session = Depends(get_db)):
    """更新个股基本面数据"""
    item = _get_analyze_or_404(id, db)
    if data.fundamentals_data is not None:
        item.fundamentals_data = data.fundamentals_data
    db.commit()
    db.refresh(item)
    return _to_analyze_response(item)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analyze(id: str, db: Session = Depends(get_db)):
    """删除个股分析（级联删除子表数据）"""
    item = _get_analyze_or_404(id, db)
    db.delete(item)
    db.commit()
    return None


# ═══════════════════════════════════════
# Reports
# ═══════════════════════════════════════

@router.get("/{id}/reports", response_model=List[ReportResponse])
def list_reports(id: str, db: Session = Depends(get_db)):
    """获取分析报告列表"""
    _get_analyze_or_404(id, db)
    items = (
        db.query(Report)
        .filter(Report.stock_analyze_id == id)
        .order_by(Report.generated_at.desc())
        .all()
    )
    return [_to_report_response(i) for i in items]


@router.post("/{id}/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(id: str, data: ReportCreate, db: Session = Depends(get_db)):
    """创建分析报告"""
    _get_analyze_or_404(id, db)
    item = Report(
        id=str(uuid4()),
        stock_analyze_id=id,
        generated_at=data.generated_at,
        title=data.title,
        content=data.content,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_report_response(item)


@router.get("/{id}/reports/{rid}", response_model=ReportResponse)
def get_report(id: str, rid: str, db: Session = Depends(get_db)):
    """获取单条分析报告"""
    _get_analyze_or_404(id, db)
    item = db.query(Report).filter(Report.id == rid, Report.stock_analyze_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="分析报告不存在")
    return _to_report_response(item)


@router.put("/{id}/reports/{rid}", response_model=ReportResponse)
def update_report(id: str, rid: str, data: ReportUpdate, db: Session = Depends(get_db)):
    """更新分析报告"""
    _get_analyze_or_404(id, db)
    item = db.query(Report).filter(Report.id == rid, Report.stock_analyze_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="分析报告不存在")

    if data.generated_at is not None:
        item.generated_at = data.generated_at
    if data.title is not None:
        item.title = data.title
    if data.content is not None:
        item.content = data.content

    db.commit()
    db.refresh(item)
    return _to_report_response(item)


@router.delete("/{id}/reports/{rid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(id: str, rid: str, db: Session = Depends(get_db)):
    """删除分析报告"""
    _get_analyze_or_404(id, db)
    item = db.query(Report).filter(Report.id == rid, Report.stock_analyze_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="分析报告不存在")
    db.delete(item)
    db.commit()
    return None


# ═══════════════════════════════════════
# TP/SL Points
# ═══════════════════════════════════════

@router.get("/{id}/tp-sl-points", response_model=List[TpSlPointResponse])
def list_tp_sl_points(id: str, db: Session = Depends(get_db)):
    """获取止盈止损点列表"""
    _get_analyze_or_404(id, db)
    items = (
        db.query(TpSlPoint)
        .filter(TpSlPoint.stock_analyze_id == id)
        .order_by(TpSlPoint.created_at.asc())
        .all()
    )
    return [_to_tp_sl_response(i) for i in items]


@router.post("/{id}/tp-sl-points", response_model=TpSlPointResponse, status_code=status.HTTP_201_CREATED)
def create_tp_sl_point(id: str, data: TpSlPointCreate, db: Session = Depends(get_db)):
    """创建止盈止损点"""
    _get_analyze_or_404(id, db)
    item = TpSlPoint(
        id=str(uuid4()),
        stock_analyze_id=id,
        price=data.price,
        label=data.label,
        notes=data.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_tp_sl_response(item)


@router.put("/{id}/tp-sl-points/{pid}", response_model=TpSlPointResponse)
def update_tp_sl_point(id: str, pid: str, data: TpSlPointUpdate, db: Session = Depends(get_db)):
    """更新止盈止损点"""
    _get_analyze_or_404(id, db)
    item = db.query(TpSlPoint).filter(TpSlPoint.id == pid, TpSlPoint.stock_analyze_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="止盈止损点不存在")

    if data.price is not None:
        item.price = data.price
    if data.label is not None:
        item.label = data.label
    if data.notes is not None:
        item.notes = data.notes

    db.commit()
    db.refresh(item)
    return _to_tp_sl_response(item)


@router.delete("/{id}/tp-sl-points/{pid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tp_sl_point(id: str, pid: str, db: Session = Depends(get_db)):
    """删除止盈止损点"""
    _get_analyze_or_404(id, db)
    item = db.query(TpSlPoint).filter(TpSlPoint.id == pid, TpSlPoint.stock_analyze_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="止盈止损点不存在")
    db.delete(item)
    db.commit()
    return None


# ═══════════════════════════════════════
# Stock Tags
# ═══════════════════════════════════════

@router.get("/{id}/stock-tags", response_model=List[StockTagResponse])
def list_stock_tags(id: str, db: Session = Depends(get_db)):
    """获取个股标签列表"""
    _get_analyze_or_404(id, db)
    items = (
        db.query(StockTag)
        .filter(StockTag.stock_analyze_id == id)
        .order_by(StockTag.created_at.asc())
        .all()
    )
    return [_to_tag_response(i) for i in items]


@router.post("/{id}/stock-tags", response_model=StockTagResponse, status_code=status.HTTP_201_CREATED)
def create_stock_tag(id: str, data: StockTagCreate, db: Session = Depends(get_db)):
    """创建个股标签"""
    _get_analyze_or_404(id, db)
    item = StockTag(
        id=str(uuid4()),
        stock_analyze_id=id,
        tag=data.tag,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_tag_response(item)


@router.delete("/{id}/stock-tags/{tid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock_tag(id: str, tid: str, db: Session = Depends(get_db)):
    """删除个股标签"""
    _get_analyze_or_404(id, db)
    item = db.query(StockTag).filter(StockTag.id == tid, StockTag.stock_analyze_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股标签不存在")
    db.delete(item)
    db.commit()
    return None
