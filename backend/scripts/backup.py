"""CLI 数据备份/恢复脚本

用法:
    docker compose exec backend python -m scripts.backup export --types stocks,transactions,memos,kline --output /tmp/backup.tar.gz
    docker compose exec backend python -m scripts.backup import --file /tmp/backup.tar.gz
"""

import argparse
import json
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def cmd_export(args):
    from app.database import SessionLocal
    from app.routers.backup import _build_stream, VALID_TYPES

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    invalid = set(types) - VALID_TYPES
    if invalid:
        logger.error("无效的 types: %s", invalid)
        sys.exit(1)

    # stocks 始终导出
    all_types = list(set(types) | {"stocks"})

    db = SessionLocal()
    try:
        buf = _build_stream(all_types, db)
        output = args.output or f"./stockmemos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        with open(output, "wb") as f:
            f.write(buf.getvalue())
        logger.info("✅ 已导出到 %s", output)
        logger.info("   包含: %s", ", ".join(all_types))
    finally:
        db.close()


def cmd_import(args):
    from app.database import SessionLocal
    from app.routers.backup import (
        _import_stocks,
        _import_transactions,
        _import_memos,
        _import_kline,
        ImportResponse,
        ImportCounts,
        ImportSkipped,
    )
    import tarfile

    db = SessionLocal()
    try:
        with tarfile.open(args.file, "r:gz") as tar:
            result = ImportResponse(
                imported=ImportCounts(),
                skipped=ImportSkipped(),
            )
            stocks_imported, stocks_skipped = _import_stocks(tar, db)
            result.imported.stocks = stocks_imported
            result.skipped.stocks = stocks_skipped

            result.imported.transactions = _import_transactions(tar, db)
            result.imported.memos = _import_memos(tar, db)
            result.imported.kline_files = _import_kline(tar, db)

        logger.info("✅ 导入完成")
        logger.info("   个股: %d 成功 / %d 跳过", result.imported.stocks, len(result.skipped.stocks))
        logger.info("   交易: %d 成功", result.imported.transactions)
        logger.info("   备忘: %d 成功", result.imported.memos)
        logger.info("   K线文件: %d", result.imported.kline_files)
        if result.skipped.stocks:
            logger.info("   已存在（跳过）: %s", ", ".join(result.skipped.stocks))
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="StockMemos 数据备份工具")
    sub = parser.add_subparsers(dest="command", required=True)

    # export
    export_p = sub.add_parser("export", help="导出数据")
    export_p.add_argument("--types", required=True, help="逗号分隔: stocks,transactions,memos,kline")
    export_p.add_argument("--output", help="输出文件路径（默认: ./stockmemos_export_<timestamp>.tar.gz）")
    export_p.set_defaults(func=cmd_export)

    # import
    import_p = sub.add_parser("import", help="导入数据")
    import_p.add_argument("--file", required=True, help="导入文件路径（tar.gz）")
    import_p.set_defaults(func=cmd_import)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
