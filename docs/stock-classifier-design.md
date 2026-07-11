# 分类器设计方案

## classify(symbol) → { exchange, type }

### 输入处理
- 若输入为 `{纯数字}.{字母}` 形式（如 `518600.SZ`、`07515.HK`）：去掉后缀，提取纯数字部分进行分类
- 否则整体作为股票代码（如 `BRK.A`、`DRAM`）

### 市场判定
| 条件 | 交易所 | 说明 |
|------|--------|------|
| 包含字母 | US | 美股/ETF，含 `BRK.A` 等带点代码 |
| 纯数字, len=6 | CN | 按前缀表细分 stock/fund |
| 纯数字, len<6 | HK | 港股/ETF |
| 其他 | — | type=unknown |

### CN 6位数字前缀规则
**STOCK**: 600/601/603/605/688/900 → SH ; 000/001/002/003/300/301/200 → SZ
**FUND**: 510/511/512/513/515/517/518/520/530/560/588 → SH; 158/159/160-169/184/180-181 → SZ
**UNKNOWN**: 11xxxx/01xxxx/019xxx 等（交给 TuShare 自行处理）

### 集成点
- `stock_classifier.py` — 新独立模块，零依赖
- `stock.py` lookup — 前端不再传 exchange，全权交由分类器
- `TuShareProvider` — 根据 type 走 fund 或 stock 通路
- `YFinanceProvider` — HK 代码 strip 前导零
- 前端添加对话框 — 删除交易所/货币下拉框，仅留代码+名称

### 设计约束
- 分类器不依赖外部数据源（不调 API、不查数据库）
- 分类器不负责 ticker 格式化（前导零处理在 Provider）
- 用户不可手动指定交易所（代码中注释决策理由）
