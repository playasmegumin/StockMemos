# OCR 截图识别模块

同花顺 App 截图 → 结构化 JSON → 对接备份导入系统。

## 安装

```bash
# 满足任一引擎需求即可

# 选项 A：Qwen-VL（推荐，仅需 API Key）
pip install -r requirements.txt
export DASHSCOPE_API_KEY="sk-xxx"

# 选项 B：RapidOCR（本地离线，无需 API）
pip install rapidocr_onnxruntime
```

## 使用

```bash
# 从 backend/ 目录运行

# 交易流水截图（推荐 Qwen-VL 引擎）
python -m app.ocr.cli --image stock.jpg --type trade --engine qwen --stock-code 600118 --exchange SH

# 银证转账截图
python -m app.ocr.cli --image money.jpg --type capital --engine qwen

# 本地 RapidOCR 引擎
python -m app.ocr.cli --image stock.jpg --type trade --engine rapid

# 批量处理
python -m app.ocr.cli --images ./screenshots/*.jpg --type capital --output ./results/
```

## 输出格式

输出 JSON 与备份导入系统兼容，可直接通过设置页「备份导入」写入数据库。

### 交易流水 (`*_transactions.json`)

```json
{
  "version": "1",
  "transactions": [{
    "exchange": "SH",
    "symbol": "600118",
    "action": "buy",
    "traded_at": "2026-01-08",
    "price": 103.16,
    "quantity": -100,
    "gas": 5.18
  }]
}
```

### 银证转账 (`*_capital_flows.json`)

```json
{
  "version": "1",
  "capital_flows": [{
    "type": "deposit",
    "amount": 500.0,
    "currency": "CNY",
    "created_at": "2025-12-12T15:00:00"
  }]
}
```

## 引擎

| 引擎 | `--engine` | 类型 | 优势 | 局限 |
|------|-----------|------|------|------|
| **Qwen-VL API** | `qwen` | 远端 LLM API | 精度最高，自动理解排版 | 需 API Key 和网络 |
| **RapidOCR ONNX** | `rapid`（默认） | 本地 ONNX | 免费离线 | 银证转账记录边界检测薄弱 |

## 参数

| 参数 | 说明 |
|------|------|
| `--image` | 单张截图路径 |
| `--images` | 批量截图路径（glob 模式） |
| `--type` | `trade`（交易流水）、`capital`（银证转账） |
| `--engine` | `qwen`、`rapid`（默认）、`paddle` |
| `--stock-code` | 股票代码，交易流水必填 |
| `--exchange` | 交易所，交易流水必填 |
| `--output` | 输出目录（默认 `./ocr_results`） |
| `--no-dedup` | 跳过交互式去重 |

## 目录结构

```
backend/app/ocr/
├── cli.py               # CLI 入口
├── base.py              # OCRResult + BaseOCREngine
├── qwen_engine.py       # Qwen-VL API 引擎（首选）
├── rapid_engine.py      # RapidOCR ONNX 引擎（备选）
├── paddle_engine.py     # PaddleOCR 引擎（备选）
├── parsers/
│   ├── base.py          # BaseParser 坐标分组
│   ├── huase_trade.py   # 交易流水坐标解析器
│   └── huase_capital.py # 银证转账坐标解析器
├── __init__.py
└── __main__.py
```
