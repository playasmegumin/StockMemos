"""create portfolio table

Revision ID: 001
Revises: 
Create Date: 2024-06-13 02:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 portfolio 表"""
    op.create_table(
        'portfolio',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stock_code', sa.String(20), nullable=False, comment='股票代码，如 000001.SZ'),
        sa.Column('stock_name', sa.String(100), nullable=True, comment='股票名称'),
        sa.Column('quantity', sa.Integer(), nullable=False, comment='持股数量'),
        sa.Column('cost_price', sa.Numeric(10, 4), nullable=False, comment='成本价'),
        sa.Column('build_date', sa.Date(), nullable=False, comment='建仓日期'),
        sa.Column('status', sa.String(20), nullable=False, server_default='holding', comment='状态：holding/closed'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), comment='更新时间'),
    )


def downgrade() -> None:
    """删除 portfolio 表"""
    op.drop_table('portfolio')
