"""健康检查路由"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health_check():
    """健康检查端点"""
    return {"status": "ok"}
