"""共享 Fixture: FastAPI TestClient + SQLite 内存数据库"""

import os
import tempfile
import sys

# 确保 backend 目录在 sys.path 中
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ── 在导入 app 模块之前重定向日志目录，避免 /app 无权限 ──
import app.logging_config as lc

lc.LOG_DIR = tempfile.mkdtemp(prefix="stockmemos_test_logs_")

# ── 让 PostgreSQL 的 JSONB 也能在 SQLite 上正常工作 ──
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

# ── 在导入 app.main 之前替换数据库引擎为 SQLite ──
TEST_DATABASE_URL = "sqlite:///./test.db"
_test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
_test_session_local = sessionmaker(
    autocommit=False, autoflush=False, bind=_test_engine
)

# 先导入 app.database 并打补丁，确保 app.main 中的 startup_event 使用 SQLite
import app.database as db_mod

db_mod.engine = _test_engine
db_mod.SessionLocal = _test_session_local

# ── 现在再导入 app.main ──
import pytest
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


def override_get_db():
    """测试用依赖：使用 SQLite session"""
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建表"""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_stock(client):
    """创建一个示例股票供其他测试使用"""
    res = client.post(
        "/api/stocks",
        json={
            "exchange": "SH",
            "symbol": "600519",
            "name": "贵州茅台",
            "currency": "CNY",
        },
    )
    return res.json()
