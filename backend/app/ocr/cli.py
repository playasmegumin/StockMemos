import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from .parsers.huase_capital import HuaseCapitalParser
from .parsers.huase_trade import HuaseTradeParser
from .paddle_engine import PaddleOCREngine
from .qwen_engine import QwenVLEngine
from .rapid_engine import RapidOCREngine

PARSER_MAP = {
    "huase-trade": HuaseTradeParser,
    "huase-capital": HuaseCapitalParser,
}


def _interactive_dedup(items: List[Dict]) -> List[Dict]:
    key_to_indices: Dict[tuple, List[int]] = {}
    for i, tx in enumerate(items):
        key = (
            tx.get("traded_at"),
            tx.get("price", 0),
            tx.get("gas", 0),
            abs(tx.get("quantity", 0)),
        )
        key_to_indices.setdefault(key, []).append(i)

    result: List[Dict] = []
    for indices in key_to_indices.values():
        if len(indices) > 1:
            sample = items[indices[0]]
            print(f"\n⚠️ 发现 {len(indices)} 条疑似重复订单：")
            print(
                f"  时间: {sample.get('traded_at')}  "
                f"操作: {sample.get('action', '')}  "
                f"价格: {sample.get('price')}  "
                f"Gas: {sample.get('gas')}  "
                f"数量: {sample.get('quantity')}"
            )
            while True:
                try:
                    n = input(
                        "\n实际存在多少笔独立订单？（不重复则输入 1）: "
                    ).strip()
                    if not n:
                        n = "1"
                    count = int(n)
                    if count < 1:
                        continue
                    keep = min(count, len(indices))
                    result.extend(items[idx] for idx in indices[:keep])
                    if keep < len(indices):
                        print(
                            f"  ✅ 保留 {keep} 笔，忽略 "
                            f"{len(indices) - keep} 笔重复"
                        )
                    break
                except ValueError:
                    print("  请输入数字")
        else:
            result.append(items[indices[0]])

    return result


def main():
    parser = argparse.ArgumentParser(
        description="同花顺截图 OCR 识别工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  从 backend/ 目录运行:
    python -m app.ocr.cli --image stock.jpg --type trade --engine qwen
    python -m app.ocr.cli --image stock.jpg --type trade --engine qwen --stock-code 600118 --exchange SH
    python -m app.ocr.cli --image money.jpg --type capital --engine rapid
    python -m app.ocr.cli --images ./screenshots/*.jpg --type capital --output ./results
        """,
    )
    parser.add_argument("--image", help="单张截图路径")
    parser.add_argument("--images", nargs="+", help="多张截图路径（批量）")
    parser.add_argument(
        "--type",
        choices=["trade", "capital"],
        required=True,
        help="截图类型: trade=交易流水, capital=银证转账",
    )
    parser.add_argument(
        "--output",
        default="./ocr_results",
        help="输出目录（默认 ./ocr_results）",
    )
    parser.add_argument(
        "--engine",
        choices=["rapid", "paddle", "qwen"],
        default="rapid",
        help="OCR 引擎: rapid=RapidOCR（默认），paddle=PaddleOCR（需额外安装），qwen=Qwen-VL API",
    )
    parser.add_argument(
        "--stock-code",
        default="",
        help="股票代码（如 600118），用于交易流水输出的 symbol 字段",
    )
    parser.add_argument(
        "--exchange",
        default="",
        help="交易所代码（如 SH/SZ/HK/US），用于交易流水输出的 exchange 字段",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="跳过交互式去重",
    )

    args = parser.parse_args()

    if not args.image and not args.images:
        parser.error("请指定 --image 或 --images")

    engine = (
        RapidOCREngine()
        if args.engine == "rapid"
        else PaddleOCREngine()
        if args.engine == "paddle"
        else QwenVLEngine()
    )

    image_paths: List[str] = []
    if args.image:
        image_paths = [args.image]
    else:
        for pattern in args.images:
            image_paths.extend(glob.glob(pattern))

    if not image_paths:
        print("错误: 未找到任何截图文件")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    total_items = 0
    for img_path in image_paths:
        print(f"\n🔍 处理: {img_path}")

        if args.engine == "qwen":
            # Qwen-VL: 直接结构化输出（绕过坐标解析器）
            try:
                data = engine.analyze(img_path, args.type,
                                        stock_code=args.stock_code,
                                        exchange=args.exchange)
            except Exception as e:
                print(f"  ❌ Qwen-VL 分析失败: {e}")
                continue
        else:
            # 本地引擎: OCR → 坐标解析器
            results = engine.recognize(img_path)
            if not results:
                print(f"  ⚠️ 未检测到文字")
                continue
            parser_key = f"huase-{args.type}"
            ocr_parser_class = PARSER_MAP.get(parser_key)
            if ocr_parser_class is None:
                print(f"错误: 不支持的截图类型 '{args.type}'")
                sys.exit(1)
            data = ocr_parser_class().parse(results)

        items_key = (
            "transactions" if "transactions" in data else "capital_flows"
        )

        # 本地引擎坐标解析器不含 exchange/symbol，从 CLI 参数注入
        if args.engine != "qwen" and items_key == "transactions" and (args.stock_code or args.exchange):
            for tx in data.get("transactions", []):
                if args.exchange:
                    tx["exchange"] = args.exchange
                if args.stock_code:
                    tx["symbol"] = args.stock_code

        items_key = (
            "transactions" if "transactions" in data else "capital_flows"
        )
        items: List[Dict[str, Any]] = data.get(items_key, [])

        if not items:
            print(f"  ⚠️ 未解析到有效记录")
            continue

        total_items += len(items)

        if items_key == "transactions" and not args.no_dedup:
            items = _interactive_dedup(items)

        data[items_key] = items

        stem = Path(img_path).stem
        output_path = os.path.join(args.output, f"{stem}_{items_key}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"  ✅ 输出: {output_path} ({len(items)} 条)")

    print(
        f"\n📊 处理完成: {len(image_paths)} 张截图, "
        f"共 {total_items} 条记录"
    )


if __name__ == "__main__":
    main()
