"""add remaining tables

Revision ID: 002
Revises: 001
Create Date: 2024-06-13 03:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建剩余7张数据表"""
    # 1. event（全局事件库）
    op.create_table(
        'event',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, comment='事件名称'),
        sa.Column('category', sa.String(50), nullable=True, comment='事件类型：monetary_policy/geopolitical/macro_data/company_event'),
        sa.Column('expected_date', sa.Date(), nullable=True, comment='预期发生日期'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='状态：pending/occurred/materialized'),
        sa.Column('source_url', sa.Text(), nullable=True, comment='信息来源链接'),
        sa.Column('description', sa.Text(), nullable=True, comment='事件描述'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )

    # 2. analysis_report（分析报告）
    op.create_table(
        'analysis_report',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stock_code', sa.String(20), nullable=False, comment='股票代码'),
        sa.Column('trigger_type', sa.String(20), nullable=True, comment='触发类型：manual/scheduled'),
        sa.Column('final_rating', sa.String(20), nullable=True, comment='最终评级：strong_buy/buy/accumulate/neutral/reduce/sell'),
        sa.Column('summary', sa.Text(), nullable=True, comment='报告摘要'),
        sa.Column('valuation_status', sa.String(20), nullable=True, comment='估值状态：overvalued/fair/undervalued'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )

    # 3. strategy（策略定义）
    op.create_table(
        'strategy',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, comment='策略名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='策略描述'),
        sa.Column('rules', postgresql.JSONB(), nullable=False, comment='指标组合规则(JSON)'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )

    # 4. trade_point（买卖点）
    op.create_table(
        'trade_point',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('portfolio_id', sa.String(36), sa.ForeignKey('portfolio.id'), nullable=False, comment='关联持仓ID'),
        sa.Column('type', sa.String(20), nullable=False, comment='操作类型：add_position/reduce_position/stop_loss/take_profit'),
        sa.Column('price', sa.Numeric(10, 4), nullable=True, comment='交易价格'),
        sa.Column('reason', sa.Text(), nullable=True, comment='交易理由'),
        sa.Column('report_id', sa.String(36), sa.ForeignKey('analysis_report.id'), nullable=True, comment='关联分析报告ID'),
        sa.Column('trade_date', sa.Date(), nullable=True, comment='交易日期'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )

    # 5. event_impact（事件-个股影响）
    op.create_table(
        'event_impact',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_id', sa.String(36), sa.ForeignKey('event.id'), nullable=False, comment='关联事件ID'),
        sa.Column('stock_code', sa.String(20), nullable=False, comment='股票代码'),
        sa.Column('direction', sa.String(20), nullable=True, comment='影响方向：bullish/bearish/neutral'),
        sa.Column('magnitude', sa.Integer(), nullable=True, comment='影响程度：1-5'),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True, comment='置信度：0.00-1.00'),
        sa.Column('time_window', sa.String(50), nullable=True, comment='时间窗口，如 1-3个月'),
        sa.Column('agent_reasoning', sa.Text(), nullable=True, comment='Agent推理过程'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )

    # 6. agent_log（Agent思考过程）
    op.create_table(
        'agent_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('report_id', sa.String(36), sa.ForeignKey('analysis_report.id'), nullable=False, comment='关联报告ID'),
        sa.Column('agent_name', sa.String(50), nullable=False, comment='Agent名称，如 bull_agent'),
        sa.Column('agent_role', sa.String(50), nullable=True, comment='角色：intelligence/event_analysis/bull/bear/referee/valuation/reporter'),
        sa.Column('reasoning', sa.Text(), nullable=True, comment='完整思考文本'),
        sa.Column('conclusion', sa.Text(), nullable=True, comment='结论摘要'),
        sa.Column('meta_data', postgresql.JSONB(), nullable=True, comment='结构化输出(JSON)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )

    # 7. strategy_signal（策略信号记录）
    op.create_table(
        'strategy_signal',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategy.id'), nullable=False, comment='关联策略ID'),
        sa.Column('stock_code', sa.String(20), nullable=False, comment='股票代码'),
        sa.Column('signal_date', sa.Date(), nullable=False, comment='信号日期'),
        sa.Column('signal_type', sa.String(20), nullable=True, comment='信号类型：buy/sell/hold/overvalued/undervalued'),
        sa.Column('raw_data', postgresql.JSONB(), nullable=True, comment='当日指标原始值(JSON)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='创建时间'),
    )


def downgrade() -> None:
    """删除全部新表（注意顺序：先删外键引用端，再删被引用端）"""
    op.drop_table('strategy_signal')
    op.drop_table('agent_log')
    op.drop_table('event_impact')
    op.drop_table('trade_point')
    op.drop_table('strategy')
    op.drop_table('analysis_report')
    op.drop_table('event')
