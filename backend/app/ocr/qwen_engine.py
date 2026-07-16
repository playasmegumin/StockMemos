"""Qwen-VL 视觉引擎 — 支持两种模式：
- recognize(): 逐行文字 + Y 坐标（用于坐标解析器）
- analyze():  直接结构化 JSON 输出（更可靠，无需坐标解析）
"""

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import BaseOCREngine, OCRResult

logger = logging.getLogger(__name__)

DASHSCOPE_URL = (
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
)

# engine=rapid 的坐标解析器保持原有 prompt
LINE_EXTRACT_PROMPT = (
    "Extract ALL visible text from this image. "
    "For each line of text, output the text content "
    "and its approximate vertical Y-coordinate (row number). "
    "Format: TEXT | Y_POSITION. "
    "Include ALL text including headers, data rows, numbers, "
    "and labels. Do not summarize."
)

TRADE_PROMPT = (
    "这张截图是股票交易流水。提取所有交易记录。\n"
    "1. 截图的页面标题（如果有）会显示股票名称，可能也会显示股票代码和交易所。提取 stock_name、stock_code（纯数字代码，如 600118）、exchange（如 SH/SZ）。\n"
    "2. 提取每一笔交易记录。\n"
    "只输出 JSON，不要其他文字。\n"
    '格式: {"stock_name": "...", "stock_code": "...", "exchange": "...", "transactions": [{"date": "YYYY-MM-DD", "action": "buy/sell", "quantity": 正=买入/建仓 负=卖出/清仓, "price": 数字, "fee": 数字, "amount": 数字}, ...]}'
)

CAPITAL_PROMPT = (
    "这张截图是银证转账/资金流水记录。提取所有转账记录，输出为 JSON 数组。"
    "只输出 JSON，不要其他文字。"
    "每个条目包含: type(deposit/withdraw), amount(数字), date(YYYY-MM-DDThh:mm:ss格式)"
)


class QwenVLEngine(BaseOCREngine):
    def __init__(self, api_key: str = "", model: str = "qwen3-vl-plus"):
        self._api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        self._model = model
        if not self._api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY 未设置。请设置环境变量 DASHSCOPE_API_KEY"
            )

    def _encode_image(self, image_path: str) -> tuple:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                     "png": "image/png", "webp": "image/webp"}
        mime = mime_map.get(ext, f"image/{ext}")
        return data, mime

    def _call_api(self, prompt: str, image_data: str,
                  mime: str) -> str:
        payload = json.dumps({
            "model": self._model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{image_data}"}},
                    {"type": "text", "text": prompt},
                ]
            }],
            "max_tokens": 4096,
        }).encode("utf-8")

        req = urllib.request.Request(
            DASHSCOPE_URL, data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"DashScope API 错误 ({e.code}): {err}")
        except Exception as e:
            raise RuntimeError(f"Qwen-VL API 调用失败: {e}")

    # --- 文本级 OCR（供坐标解析器使用）---

    def recognize(self, image_path: str) -> List[OCRResult]:
        image_data, mime = self._encode_image(image_path)
        text = self._call_api(LINE_EXTRACT_PROMPT, image_data, mime)
        results: List[OCRResult] = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if " | " in line:
                parts = line.rsplit(" | ", 1)
                content = parts[0]
                try:
                    y = float(parts[1])
                except ValueError:
                    y = 0.0
            else:
                content = line
                y = 0.0
            if content:
                results.append(
                    OCRResult(text=content, bbox=[0, y, 0, y], confidence=0.9)
                )
        logger.info("Qwen-VL 文字提取 %s: %d 条", image_path, len(results))
        return results

    # --- 结构化 JSON 输出（首选方式，绕过坐标解析器）---

    def analyze(self, image_path: str, type_: str,
                stock_code: str = "", exchange: str = "") -> Dict[str, Any]:
        """端到端结构化提取，直接返回可导入的 JSON 字典
        stock_code/exchange: CLI 参数，优先级高于 Qwen-VL 从截图提取的值
        """
        if type_ == "trade":
            prompt = TRADE_PROMPT
        elif type_ == "capital":
            prompt = CAPITAL_PROMPT
        else:
            raise ValueError(f"不支持的分析类型: {type_}")

        image_data, mime = self._encode_image(image_path)
        text = self._call_api(prompt, image_data, mime)

        texts_to_try = [text]
        # 尝试移除可能的 markdown 代码块标记
        text_clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
        if text_clean != text:
            texts_to_try.insert(0, text_clean)

        parsed = None
        records = None
        for t in texts_to_try:
            # 尝试匹配 JSON 对象 { ... }
            m = re.search(r"\{.*\}", t, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group())
                    records = parsed.get("transactions", [])
                    break
                except json.JSONDecodeError:
                    pass
            # 尝试匹配 JSON 数组 [ ... ]
            m = re.search(r"\[.*\]", t, re.DOTALL)
            if m:
                try:
                    records = json.loads(m.group())
                    break
                except json.JSONDecodeError:
                    pass

        if records is None:
            raise RuntimeError(f"Qwen-VL 未返回有效 JSON: {text[:200]}")

        if type_ == "trade":
            # Qwen-VL 从截图标题提取的股票信息（可能为空）
            stock_code_from_vl = (parsed or {}).get("stock_code", "") or ""
            exchange_from_vl = (parsed or {}).get("exchange", "") or ""
            stock_name_from_vl = (parsed or {}).get("stock_name", "") or ""
            # 优先 CLI 参数，其次 Qwen-VL 提取
            final_code = stock_code or stock_code_from_vl
            final_exchange = exchange or exchange_from_vl
            return {
                "version": "1",
                "exported_at": datetime.now(timezone.utc)
                    .isoformat().replace("+00:00", "Z"),
                "stock_code": final_code,
                "exchange": final_exchange,
                "stock_name": stock_name_from_vl,
                "transactions": [{
                    "action": rec.get("action", ""),
                    "traded_at": rec.get("date", ""),
                    "price": float(rec["price"]) if "price" in rec else 0,
                    "quantity": int(rec["quantity"]) if "quantity" in rec else 0,
                    "gas": float(rec.get("fee", 0)),
                    "exchange": final_exchange,
                    "symbol": final_code,
                } for rec in records if "date" in rec],
            }
        else:
            return {
                "version": "1",
                "exported_at": datetime.now(timezone.utc)
                    .isoformat().replace("+00:00", "Z"),
                "capital_flows": [{
                    "type": r["type"],
                    "amount": abs(float(r["amount"])),
                    "currency": "CNY",
                    "created_at": r["date"],
                } for r in records if "date" in r],
            }
