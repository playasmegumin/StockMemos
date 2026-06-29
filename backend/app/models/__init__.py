"""模型聚合入口"""

from app.models.stock import Stock
from app.models.transaction import Transaction

__all__ = [
    "Stock",
    "Transaction",
]
