# 资金管理 — 设计备忘

> 2026-07-10 / 2026-07-11 讨论记录，待后续实现

本文档包含两个独立但相关的功能设计：

1. **现金流水** — 记录资金存入/取出，计算总投入金额和可用现金
2. **投资备忘** — 个人非个股绑定的投资笔记

---

## 第一部分：现金流水

### 需求

维护一个"总投入金额"（从收入中划入投资的资金，不会轻易取出），用于计算：
- **现金** = 总投入金额 − 总持仓金额（CNY）
- **收益率** = 总盈亏 / 总投入金额（后续可扩展）

### 设计决策

#### 存储
| 项目 | 决策 |
|------|------|
| 存储方式 | 后端数据库 `capital_flow` 表 |
| 表结构 | `id`, `amount`(正=存入/负=取出), `note`, `created_at` |
| 总额计算 | `SELECT SUM(amount) FROM capital_flow` |
| 后续优化 | 如果性能需要，可加缓存字段 |

#### 前端
| 项目 | 决策 |
|------|------|
| 展示位置 | 持仓总览页 KPI 卡片"现金"区域 |
| "现金"公式 | 总投入金额 − 总持仓金额（CNY） |
| 添加方式 | 类似交易记录表单（金额 + 备注），每次提交追加一条 `capital_flow` |

#### API
- `GET /api/capital-flows` — 获取流水列表
- `POST /api/capital-flows` — 添加一条记录（body: `{ amount, note }`）
- `DELETE /api/capital-flows/{id}` — 删除一条记录

---

## 第二部分：投资备忘

### 需求

记录不绑定特定个股的个人投资笔记，例如：
- 市场观察和判断
- 交易计划
- 经验反思
- 知识整理

### 设计决策

#### 存储
| 项目 | 决策 |
|------|------|
| 存储方式 | 后端数据库 `investment_memo` 表 |
| 与现有 `report` 表的区别 | `report` 绑定 Stock，`investment_memo` 完全独立 |
| 表结构 | `id`, `title`(可选), `content`(Markdown), `type`(分类), `created_at`, `updated_at` |

`investment_memo` 表字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID PK | 主键 |
| `title` | varchar(200), nullable | 标题（可选，不填则以 content 首行截取） |
| `content` | text | 正文，支持 Markdown |
| `type` | varchar(50), default="general" | 分类：`general`(一般) / `plan`(计划) / `review`(复盘) / `idea`(想法) |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

#### 前端
| 项目 | 决策 |
|------|------|
| 入口 | 侧边栏新增「投资备忘」菜单项 |
| 页面 | 独立页面 `/memos` |
| 列表样式 | 时间线逆序排列，卡片展示 |
| 编辑器 | 简单 Markdown 文本域 + 预览切换 |
| 与现金流量关系 | 完全独立，无关联 |

#### API
- `GET /api/investment-memos` — 获取备忘列表（分页，按 `created_at` 降序）
- `GET /api/investment-memos/{id}` — 获取单条
- `POST /api/investment-memos` — 创建（body: `{ title?, content, type? }`）
- `PUT /api/investment-memos/{id}` — 更新
- `DELETE /api/investment-memos/{id}` — 删除

#### 侧边栏变更

```diff
  <t-menu-item value="dashboard">持仓总览</t-menu-item>
+ <t-menu-item value="memos">投资备忘</t-menu-item>
  <t-menu-item value="agent" disabled>Agent 分析</t-menu-item>
  <t-menu-item value="settings" disabled>设置</t-menu-item>
```

#### 路由变更

```diff
  { path: '/',                 component: PortfolioDashboard },
  { path: '/stock/:id',        component: StockDetail },
+ { path: '/memos',            component: InvestmentMemos },
```

---

## 实现顺序

建议分两次 Change 实现：

1. **第一次 Change：现金流水** — `capital_flow` 表 + API + KPI 卡片联动
2. **第二次 Change：投资备忘** — `investment_memo` 表 + API + 独立页面 + 侧边栏

两个功能完全独立，无依赖关系，也可按需交换顺序。
