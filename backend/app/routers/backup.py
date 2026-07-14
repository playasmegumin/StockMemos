"""Backup — 数据导出/导入

Endpoints:
    POST  /api/backup/export  — 导出 ZIP（可选 stocks/transactions/memos/kline）
    POST  /api/backup/import  — 导入 ZIP，返回统计

数据格式规范见 docs/backup-format-design.md
"""

import csv
import io
import json
import logging
import os
import zipfile
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    CapitalFlow,
    InvestmentMemo,
    KlineDaily,
    Stock,
    StockAnalyze,
    StockTag,
    Transaction,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── 请求/响应 Schema ────────────────────────────


class ExportRequest(BaseModel):
    types: List[str]  # stocks, transactions, memos, kline, capital_flows


class ImportCounts(BaseModel):
    stocks: int = 0
    transactions: int = 0
    memos: int = 0
    capital_flows: int = 0
    kline_files: int = 0


class ImportSkipped(BaseModel):
    stocks: List[str] = []
    transactions: int = 0
    memos: int = 0
    capital_flows: int = 0


class ImportResponse(BaseModel):
    imported: ImportCounts
    skipped: ImportSkipped


# ─── 常量 ────────────────────────────────────────

VALID_TYPES = {"stocks", "transactions", "memos", "kline", "capital_flows"}
TS = datetime.now().strftime("%Y%m%d_%H%M%S")


# ═══════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════


def _build_stream(types: List[str], db: Session):
    """在内存中构建 ZIP 并流式返回"""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if "stocks" in types:
            _add_stocks_to_archive(zf, db)
        if "transactions" in types:
            _add_transactions_to_archive(zf, db)
        if "memos" in types:
            _add_memos_to_archive(zf, db)
        if "capital_flows" in types:
            _add_capital_flows_to_archive(zf, db)
        if "kline" in types:
            _add_kline_to_archive(zf, db)

    buf.seek(0)
    return buf


def _add_stocks_to_archive(zf: zipfile.ZipFile, db: Session):
    """导出 Stock + Tag → stocks.json"""
    stocks = db.query(Stock).order_by(Stock.created_at).all()
    result = []
    for s in stocks:
        analyze = db.query(StockAnalyze).filter(
            StockAnalyze.stock_id == s.id
        ).first()
        tags_list = []
        if analyze:
            tags = db.query(StockTag.tag).filter(
                StockTag.stock_analyze_id == analyze.id
            ).order_by(StockTag.created_at).all()
            tags_list = [t.tag for t in tags]
        result.append({
            "exchange": s.exchange,
            "symbol": s.symbol,
            "name": s.name or s.symbol,
            "tags": tags_list,
        })

    content = json.dumps({
        "version": "1",
        "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stocks": result,
    }, ensure_ascii=False, indent=2)

    zf.writestr("stocks.json", content.encode("utf-8"))


def _add_transactions_to_archive(zf: zipfile.ZipFile, db: Session):
    """导出 Transaction → transactions.json"""
    txs = db.query(Transaction).order_by(Transaction.traded_at).all()
    rows = []
    for tx in txs:
        stock = db.query(Stock).filter(Stock.id == tx.stock_id).first()
        if not stock:
            continue
        rows.append({
            "exchange": stock.exchange,
            "symbol": stock.symbol,
            "quantity": float(tx.quantity),
            "price": float(tx.price),
            "gas": float(tx.gas),
            "traded_at": tx.traded_at.isoformat(),
        })

    content = json.dumps({
        "version": "1",
        "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transactions": rows,
    }, ensure_ascii=False, indent=2)

    zf.writestr("transactions.json", content.encode("utf-8"))


def _add_memos_to_archive(zf: zipfile.ZipFile, db: Session):
    """导出 InvestmentMemo → memos.json"""
    memos = db.query(InvestmentMemo).order_by(InvestmentMemo.created_at).all()
    rows = []
    for m in memos:
        stock = db.query(Stock).filter(Stock.id == m.stock_id).first() if m.stock_id else None
        rows.append({
            "title": m.title,
            "content": m.content,
            "stock_exchange": stock.exchange if stock else None,
            "stock_symbol": stock.symbol if stock else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        })

    content = json.dumps({
        "version": "1",
        "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "memos": rows,
    }, ensure_ascii=False, indent=2)

    zf.writestr("memos.json", content.encode("utf-8"))


def _add_capital_flows_to_archive(zf: zipfile.ZipFile, db: Session):
    """导出 CapitalFlow → capital_flows.json"""
    flows = db.query(CapitalFlow).order_by(CapitalFlow.created_at).all()
    rows = []
    for f in flows:
        rows.append({
            "type": f.type,
            "amount": float(f.amount),
            "currency": f.currency,
            "note": f.note,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })

    content = json.dumps({
        "version": "1",
        "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "capital_flows": rows,
    }, ensure_ascii=False, indent=2)

    zf.writestr("capital_flows.json", content.encode("utf-8"))


def _add_kline_to_archive(zf: zipfile.ZipFile, db: Session):
    """导出 KlineDaily → kline/{symbol}_{exchange}.csv"""
    rows = db.execute(
        text("SELECT DISTINCT stock_id FROM kline_daily")
    ).fetchall()

    for (stock_id,) in rows:
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            continue

        klines = db.query(KlineDaily).filter(
            KlineDaily.stock_id == stock_id
        ).order_by(KlineDaily.trade_date).all()

        if not klines:
            continue

        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["date", "open", "high", "low", "close", "volume", "amount"])
        for k in klines:
            writer.writerow([
                k.trade_date.isoformat(),
                float(k.open),
                float(k.high),
                float(k.low),
                float(k.close),
                int(k.volume),
                float(k.amount) if k.amount else "",
            ])

        filename = f"kline/{stock.symbol}_{stock.exchange}.csv"
        zf.writestr(filename, csv_buf.getvalue().encode("utf-8"))


@router.post("/backup/export")
def export_backup(req: ExportRequest, db: Session = Depends(get_db)):
    """导出数据为 ZIP"""
    if not req.types:
        raise HTTPException(422, "types 不能为空")
    invalid = set(req.types) - VALID_TYPES
    if invalid:
        raise HTTPException(422, f"无效的 types: {invalid}")

    buf = _build_stream(req.types, db)
    filename = f"stockmemos_export_{TS}.zip"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ═══════════════════════════════════════════════════
# 导入
# ═══════════════════════════════════════════════════


def _extract_file(zf: zipfile.ZipFile, name: str) -> Optional[str]:
    """从 ZIP 中提取文本文件内容（支持嵌套目录）"""
    try:
        return zf.read(name).decode("utf-8")
    except KeyError:
        pass
    # 嵌套路径兜底：*/name
    for n in zf.namelist():
        if n.endswith("/" + name):
            return zf.read(n).decode("utf-8")
    return None


def _import_stocks(zf: zipfile.ZipFile, db: Session) -> tuple:  # (imported, skipped)
    """导入 stocks.json（已存在则跳过）"""
    raw = _extract_file(zf, "stocks.json")
    if raw is None:
        return 0, []

    data = json.loads(raw)
    imported = 0
    skipped = []

    for item in data.get("stocks", []):
        exchange = item["exchange"]
        symbol = item["symbol"]
        name = item.get("name", symbol)
        tags = item.get("tags", [])

        # 检查是否已存在
        existing = db.query(Stock).filter(
            Stock.exchange == exchange,
            Stock.symbol == symbol,
        ).first()
        if existing:
            skipped.append(f"{exchange}/{symbol}")
            continue

        stock = Stock(
            exchange=exchange,
            symbol=symbol,
            name=name,
            currency="CNY",  # 默认；导入后刷新自动修正
            position=0,
            historical_pnl=0.0,
        )
        db.add(stock)
        db.flush()  # 获取 id

        # 创建标签（tags 存在 StockAnalyze 上，需同时创建）
        if tags:
            # 创建或查找 StockAnalyze
            analyze = db.query(StockAnalyze).filter(
                StockAnalyze.stock_id == stock.id
            ).first()
            if not analyze:
                analyze = StockAnalyze(stock_id=stock.id)
                db.add(analyze)
                db.flush()
            for i, tag_name in enumerate(tags):
                tag = StockTag(
                    stock_analyze_id=analyze.id,
                    tag=tag_name,
                    created_at=datetime.utcnow(),
                )
                db.add(tag)

        imported += 1

    db.commit()
    return imported, skipped


def _import_transactions(zf: zipfile.ZipFile, db: Session) -> int:
    """导入 transactions.json（同一批次内存去重 + DB 判重）"""
    raw = _extract_file(zf, "transactions.json")
    if raw is None:
        return 0

    data = json.loads(raw)
    imported = 0
    seen_keys: set = set()  # 同一批次内去重（db.commit 在循环外）
    refreshed_stock_ids: set = set()  # 需要刷新 position/pnl 的 stock

    for item in data.get("transactions", []):
        exchange = item["exchange"]
        symbol = item["symbol"]

        # 内存去重
        key = (exchange, symbol, item["quantity"], item["price"], item["gas"], item["traded_at"])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        stock = db.query(Stock).filter(
            Stock.exchange == exchange,
            Stock.symbol == symbol,
        ).first()
        if not stock:
            continue

        # DB 去重
        dup = db.query(Transaction).filter(
            Transaction.stock_id == stock.id,
            Transaction.quantity == item["quantity"],
            Transaction.price == item["price"],
            Transaction.gas == item["gas"],
            Transaction.traded_at == date.fromisoformat(item["traded_at"]),
        ).first()
        if dup:
            continue

        tx = Transaction(
            stock_id=stock.id,
            quantity=item["quantity"],
            price=item["price"],
            gas=item["gas"],
            traded_at=date.fromisoformat(item["traded_at"]),
        )
        db.add(tx)
        imported += 1
        refreshed_stock_ids.add(str(stock.id))

    db.commit()

    # 刷新导入过交易记录的个股 position / historical_pnl
    if refreshed_stock_ids:
        from app.routers.transaction import _recalc_stock
        for sid in refreshed_stock_ids:
            _recalc_stock(sid, db)

    return imported


def _import_memos(zf: zipfile.ZipFile, db: Session) -> int:
    """导入 memos.json"""
    raw = _extract_file(zf, "memos.json")
    if raw is None:
        return 0

    data = json.loads(raw)
    imported = 0

    for item in data.get("memos", []):
        title = item["title"]
        content = item["content"]

        # 判重：same title + close created_at
        created = item.get("created_at")
        if created:
            created_dt = datetime.fromisoformat(created)
            dup = db.query(InvestmentMemo).filter(
                InvestmentMemo.title == title,
                InvestmentMemo.created_at >= created_dt,
            ).first()
            if dup:
                continue

        # 关联股票
        stock_id = None
        if item.get("stock_symbol"):
            stock = db.query(Stock).filter(
                Stock.exchange == item.get("stock_exchange"),
                Stock.symbol == item["stock_symbol"],
            ).first()
            if stock:
                stock_id = stock.id

        memo = InvestmentMemo(
            title=title,
            content=content,
            stock_id=stock_id,
            created_at=datetime.fromisoformat(created) if created else datetime.utcnow(),
            updated_at=datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else datetime.utcnow(),
        )
        db.add(memo)
        imported += 1

    db.commit()
    return imported


def _import_capital_flows(zf: zipfile.ZipFile, db: Session) -> int:
    """导入 capital_flows.json"""
    raw = _extract_file(zf, "capital_flows.json")
    if raw is None:
        return 0

    data = json.loads(raw)
    imported = 0

    for item in data.get("capital_flows", []):
        flow = CapitalFlow(
            type=item["type"],
            amount=item["amount"],
            currency=item.get("currency", "CNY"),
            note=item.get("note"),
            created_at=datetime.fromisoformat(item["created_at"]) if item.get("created_at") else datetime.utcnow(),
        )
        db.add(flow)
        imported += 1

    db.commit()
    return imported


def _import_kline(zf: zipfile.ZipFile, db: Session) -> int:
    """导入 kline/*.csv（UPSERT，支持嵌套目录）"""
    file_count = 0

    for name in zf.namelist():
        if not name.endswith(".csv"):
            continue
        normalized = name.replace("\\", "/")
        if "kline/" not in normalized:
            continue

        # 从 basename 提取 exchange 和 symbol
        basename = normalized.split("/")[-1].replace(".csv", "")
        parts = basename.split("_")
        if len(parts) < 2:
            continue
        exchange = parts[-1]
        symbol = "_".join(parts[:-1])

        stock = db.query(Stock).filter(
            Stock.exchange == exchange,
            Stock.symbol == symbol,
        ).first()
        if not stock:
            logger.warning("[backup] kline: stock not found for %s/%s", exchange, symbol)
            continue

        content = zf.read(name).decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        imported = 0
        for row in reader:
            try:
                trade_date = date.fromisoformat(row["date"])
                existing = db.query(KlineDaily).filter(
                    KlineDaily.stock_id == stock.id,
                    KlineDaily.trade_date == trade_date,
                ).first()

                kwargs = {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                    "amount": float(row["amount"]) if row.get("amount", "").strip() else 0.0,
                }

                if existing:
                    for k, v in kwargs.items():
                        setattr(existing, k, v)
                else:
                    kline = KlineDaily(
                        stock_id=stock.id,
                        trade_date=trade_date,
                        **kwargs,
                    )
                    db.add(kline)
                    imported += 1
            except (ValueError, KeyError) as e:
                logger.warning("[backup] kline: skip row %s: %s", row.get("date"), e)
                continue

        db.commit()
        file_count += 1

    return file_count


@router.post("/backup/import")
def import_backup(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """导入 ZIP 并返回统计"""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "仅支持 .zip 文件")

    content = file.file.read()
    buf = io.BytesIO(content)

    result = ImportResponse(
        imported=ImportCounts(),
        skipped=ImportSkipped(),
    )

    try:
        with zipfile.ZipFile(buf, "r") as zf:
            stocks_imported, stocks_skipped = _import_stocks(zf, db)
            result.imported.stocks = stocks_imported
            result.skipped.stocks = stocks_skipped

            result.imported.transactions = _import_transactions(zf, db)
            result.imported.memos = _import_memos(zf, db)
            result.imported.capital_flows = _import_capital_flows(zf, db)
            result.imported.kline_files = _import_kline(zf, db)
    except (zipfile.BadZipFile, json.JSONDecodeError) as e:
        raise HTTPException(400, f"无法解析备份文件: {e}")

    return result
