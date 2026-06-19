# Kimi Work 初始化指令

在Kimi Work中创建新项目后，发送以下消息启动开发：

---

请加载以下两份文档作为项目上下文：

[system_prompt.md 内容]

[requirements.md 内容]

---

现在请开始 Milestone 1 的第一项任务：创建项目骨架。
具体要求：
1. 创建完整的目录结构
2. 编写 docker-compose.yml（backend + postgres）
3. 编写 backend/Dockerfile 和 requirements.txt
4. 编写 backend/app/main.py（FastAPI入口，含健康检查端点 /health）
5. 编写 backend/app/config.py（读取.env配置，使用pydantic-settings）
6. 配置 Alembic（alembic.ini + env.py），使其能连接PostgreSQL
7. 创建第一个迁移：创建 portfolio 表（仅核心字段）

交付物要求：
- 所有代码必须能直接复制到文件中使用
- 提供验证步骤：如何运行docker-compose并验证服务正常
- 提供 .env.example 文件内容

---

## 快速开始清单

| 步骤 | 操作 | 预计时间 |
|------|------|----------|
| 1 | 在Kimi Work中新建项目 | 2分钟 |
| 2 | 粘贴系统提示词 + 需求文档 | 5分钟 |
| 3 | 发送初始化指令 | 1分钟 |
| 4 | 等待Agent生成代码，复制到本地 | 10分钟 |
| 5 | 创建 `.env` 文件并填入你的TuShare Token | 2分钟 |
| 6 | 运行 `docker-compose up --build` | 3分钟 |
| 7 | 访问 `http://localhost:8080/docs` 验证 | 1分钟 |
