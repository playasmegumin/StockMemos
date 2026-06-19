"""事件节点 + 预测结果 API

Endpoints:
    POST   /api/event-nodes                    — 创建事件节点
    GET    /api/event-nodes                    — 获取事件列表
    GET    /api/event-nodes/{id}               — 获取事件详情
    PUT    /api/event-nodes/{id}               — 更新事件
    DELETE /api/event-nodes/{id}               — 删除事件
    POST   /api/event-nodes/{id}/predictions   — 添加预测结果
    GET    /api/event-nodes/{id}/predictions   — 获取预测列表
    PUT    /api/event-nodes/{id}/predictions/{pid} — 更新预测（标记实际结果）
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event_node import EventNode
from app.models.event_prediction import EventPrediction
from app.schemas.event_node import EventNodeCreate, EventNodeResponse
from app.schemas.event_prediction import EventPredictionCreate, EventPredictionResponse

router = APIRouter()


def _to_event_node_response(item: EventNode) -> EventNodeResponse:
    return EventNodeResponse(
        id=item.id,
        title=item.title,
        category=item.category,
        occurred_at=item.occurred_at,
        description=item.description,
        source_url=item.source_url,
        status=item.status,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


def _to_event_prediction_response(item: EventPrediction) -> EventPredictionResponse:
    return EventPredictionResponse(
        id=item.id,
        event_node_id=item.event_node_id,
        outcome_label=item.outcome_label,
        outcome_description=item.outcome_description,
        probability_estimate=float(item.probability_estimate) if item.probability_estimate is not None else None,
        impact_brief=item.impact_brief,
        is_actual_result=item.is_actual_result,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


@router.post("", response_model=EventNodeResponse, status_code=status.HTTP_201_CREATED)
def create_event_node(data: EventNodeCreate, db: Session = Depends(get_db)):
    """创建事件节点"""
    db_item = EventNode(
        id=str(uuid4()),
        title=data.title,
        category=data.category,
        occurred_at=data.occurred_at,
        description=data.description,
        source_url=data.source_url,
        status=data.status or "pending",
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_event_node_response(db_item)


@router.get("", response_model=List[EventNodeResponse])
def list_event_nodes(db: Session = Depends(get_db)):
    """获取事件列表，按时间倒序"""
    items = db.query(EventNode).order_by(EventNode.created_at.desc()).all()
    return [_to_event_node_response(i) for i in items]


@router.get("/{id}", response_model=EventNodeResponse)
def get_event_node(id: str, db: Session = Depends(get_db)):
    """获取事件详情"""
    item = db.query(EventNode).filter(EventNode.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="事件不存在")
    return _to_event_node_response(item)


@router.put("/{id}", response_model=EventNodeResponse)
def update_event_node(id: str, data: EventNodeCreate, db: Session = Depends(get_db)):
    """更新事件节点"""
    item = db.query(EventNode).filter(EventNode.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="事件不存在")
    item.title = data.title
    item.category = data.category
    item.occurred_at = data.occurred_at
    item.description = data.description
    item.source_url = data.source_url
    item.status = data.status or item.status
    db.commit()
    db.refresh(item)
    return _to_event_node_response(item)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_node(id: str, db: Session = Depends(get_db)):
    """删除事件节点（级联删除预测结果）"""
    item = db.query(EventNode).filter(EventNode.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="事件不存在")
    db.delete(item)
    db.commit()
    return None


@router.post("/{id}/predictions", response_model=EventPredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(id: str, data: EventPredictionCreate, db: Session = Depends(get_db)):
    """为事件添加预测结果"""
    event = db.query(EventNode).filter(EventNode.id == id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    db_item = EventPrediction(
        id=str(uuid4()),
        event_node_id=id,
        outcome_label=data.outcome_label,
        outcome_description=data.outcome_description,
        probability_estimate=data.probability_estimate,
        impact_brief=data.impact_brief,
        is_actual_result=data.is_actual_result or False,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_event_prediction_response(db_item)


@router.get("/{id}/predictions", response_model=List[EventPredictionResponse])
def list_predictions(id: str, db: Session = Depends(get_db)):
    """获取事件的预测结果列表"""
    event = db.query(EventNode).filter(EventNode.id == id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    items = db.query(EventPrediction).filter(EventPrediction.event_node_id == id).all()
    return [_to_event_prediction_response(i) for i in items]


@router.put("/{id}/predictions/{pid}", response_model=EventPredictionResponse)
def update_prediction(id: str, pid: str, data: EventPredictionCreate, db: Session = Depends(get_db)):
    """更新预测结果（标记实际结果等）"""
    item = db.query(EventPrediction).filter(EventPrediction.id == pid, EventPrediction.event_node_id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="预测不存在")
    item.outcome_label = data.outcome_label
    item.outcome_description = data.outcome_description
    item.probability_estimate = data.probability_estimate
    item.impact_brief = data.impact_brief
    item.is_actual_result = data.is_actual_result or item.is_actual_result
    db.commit()
    db.refresh(item)
    return _to_event_prediction_response(item)
