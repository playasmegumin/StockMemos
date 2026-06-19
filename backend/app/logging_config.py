"""日志配置模块

职责：
- 配置应用日志输出到控制台（Docker log，中文提示）
- 配置 SQL 日志持久化到文件（/app/logs/sql.log）
- 过滤 health 检查请求，避免日志噪音
- 应用日志持久化到文件（/app/logs/app.log）
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "/app/logs"


class _HealthFilter(logging.Filter):
    """过滤健康检查相关日志"""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        if "GET /health" in msg or "health" in msg.lower():
            return False
        return True


class _SQLLogFilter(logging.Filter):
    """只接收 SQLAlchemy 日志"""

    def filter(self, record: logging.LogRecord) -> bool:
        return "sqlalchemy" in record.name.lower()


class _AppLogFilter(logging.Filter):
    """只接收应用日志（排除 SQLAlchemy 和 health）"""

    def filter(self, record: logging.LogRecord) -> bool:
        if "sqlalchemy" in record.name.lower():
            return False
        msg = str(record.getMessage())
        if "GET /health" in msg or "health" in msg.lower():
            return False
        return True


def setup_logging() -> None:
    """初始化日志配置"""
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 清除已有处理器（避免重复）
    for h in root.handlers[:]:
        root.removeHandler(h)

    # 1. 控制台处理器：INFO 级别，中文应用日志，过滤 health 和 SQL
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    console.addFilter(_AppLogFilter())
    root.addHandler(console)

    # 2. SQL 日志文件：DEBUG 级别，RotatingFileHandler
    sql_handler = RotatingFileHandler(
        f"{LOG_DIR}/sql.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    sql_handler.setLevel(logging.DEBUG)
    sql_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s\n%(message)s\n",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    sql_handler.addFilter(_SQLLogFilter())
    root.addHandler(sql_handler)

    # 3. 应用日志文件：INFO 级别
    app_handler = RotatingFileHandler(
        f"{LOG_DIR}/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    app_handler.addFilter(_AppLogFilter())
    root.addHandler(app_handler)

    # 5. 配置 SQLAlchemy 引擎日志级别，使 SQL 语句通过 logging 输出到文件
    sqlalchemy_engine = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_engine.setLevel(logging.INFO)
    # 确保传播到 root（被 sql_handler 捕获）
    sqlalchemy_engine.propagate = True
    # 清除 SQLAlchemy 自带的处理器
    sqlalchemy_engine.handlers = []

    # 6. 关闭 uvicorn.access 的默认日志（避免重复英文 access log）
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []
    uvicorn_access.propagate = False  # 不传播到 root
    uvicorn_access.addHandler(logging.NullHandler())
