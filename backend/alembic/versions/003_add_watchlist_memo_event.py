"""add watchlist, investment_memo, memo_event

Revision ID: 003
Revises: 002
Create Date: 2024-06-19 03:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建自选股、投资备忘录、备忘录事件表"""
    # 1. investment_memo（投资备忘录，先创建，因为 watchlist 外键引用它）
    op.create_table(
        'investment_memo',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stock_code', sa.String(20), nullable=False, comment='股票代码'),
        sa.Column('target_price', sa.Numeric(10, 4), nullable=True, comment='目标股价（估值）'),
        sa.Column('valuation_method', sa.String(50), nullable=True, comment='估值方法：PE/DCF/可比公司'),
        sa.Column('business_scope', sa.Text(), nullable=True, comment='业务范围/供需关系/产业链生态位'),
        sa.Column('short_trend', sa.String(20), nullable=True, comment='短线趋势：up/down/sideways'),
        sa.Column('mid_trend', sa.String(20), nullable=True, comment='中线趋势：up/down/sideways'),
        sa.Column('long_trend', sa.String(20), nullable=True, comment='长期趋势：up/down/sideways'),
        sa.Column('trend_logic', sa.Text(), nullable=True, comment='趋势预测核心逻辑'),
        sa.Column('notes', sa.Text(), nullable=True, comment='用户自定义备注'),
        sa.Column('last_updated_by', sa.String(50), nullable=True, comment='最后更新来源'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), comment='更新时间'),
    )

    # 2. watchlist（自选股）
    op.create_table(
        'watchlist',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stock_code', sa.String(20), nullable=False, unique=True, comment='股票代码'),
        sa.Column('stock_name', sa.String(100), nullable=True, comment='股票名称'),
        sa.Column('sector', sa.String(50), nullable=True, comment='所属板块/行业'),
        sa.Column('market', sa.String(20), nullable=True, comment='交易所：SH/SZ/HK/US'),
        sa.Column('is_watched', sa.Boolean(), nullable=True, server_default='true', comment='是否在关注'),
        sa.Column('memo_id', sa.String(36), sa.ForeignKey('investment_memo.id'), nullable=True, comment='关联投资备忘录ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), comment='更新时间'),
    )

    # 3. memo_event（备忘录关联事件）
    op.create_table(
        'memo_event',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('memo_id', sa.String(36), sa.ForeignKey('investment_memo.id'), nullable=False, comment='关联备忘录ID'),
        sa.Column('event_name', sa.String(200), nullable=False, comment='事件名称'),
        sa.Column('event_type', sa.String(20), nullable=True, comment='类型：earnings/order/geopolitical/policy/other'),
        sa.Column('impact_tag', sa.String(20), nullable=True, comment='影响标签：bullish/bearish/neutral'),
        sa.Column('expected_date', sa.Date(), nullable=True, comment='预期发生日期'),
        sa.Column('actual_date', sa.Date(), nullable=True, comment='实际发生日期'),
        sa.Column('result_status', sa.String(20), nullable=False, server_default='pending', comment='pending/occurred/expired/cancelled'),
        sa.Column('result_summary', sa.Text(), nullable=True, comment='事件结果摘要'),
        sa.Column('source_url', sa.Text(), nullable=True, comment='信息来源'),
        sa.Column('agent_analysis', sa.Text(), nullable=True, comment='Agent分析摘要'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), comment='更新时间'),
    )


def downgrade() -> None:
    """删除新增表（注意顺序：先删外键引用端）"""
    op.drop_table('memo_event')
    op.drop_table('watchlist')
    op.drop_table('investment_memo')
