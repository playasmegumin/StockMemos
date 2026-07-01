"""add event_node and event_prediction

Revision ID: 004
Revises: 003
Create Date: 2024-06-19 04:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 event_node 和 event_prediction 表"""
    op.create_table(
        'event_node',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(300), nullable=False, comment='事件标题'),
        sa.Column('category', sa.String(50), nullable=True, comment='分类'),
        sa.Column('occurred_at', sa.Date(), nullable=True, comment='已发生节点日期'),
        sa.Column('description', sa.Text(), nullable=True, comment='事件描述'),
        sa.Column('source_url', sa.Text(), nullable=True, comment='信息来源'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='状态'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), comment='更新时间'),
    )

    op.create_table(
        'event_prediction',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_node_id', sa.String(36), sa.ForeignKey('event_node.id'), nullable=False, comment='关联事件节点'),
        sa.Column('outcome_label', sa.String(200), nullable=False, comment='结果标签'),
        sa.Column('outcome_description', sa.Text(), nullable=True, comment='结果描述'),
        sa.Column('probability_estimate', sa.Numeric(3, 2), nullable=True, comment='概率0.00-1.00'),
        sa.Column('impact_brief', sa.Text(), nullable=True, comment='后续影响简要解析'),
        sa.Column('is_actual_result', sa.Boolean(), nullable=True, server_default='false', comment='是否为实际结果'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), comment='更新时间'),
    )


def downgrade() -> None:
    op.drop_table('event_prediction')
    op.drop_table('event_node')
