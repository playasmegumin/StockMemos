# Agent 股票交易决策系统 — 局域网部署指南

## 环境要求

- **操作系统**: Windows 10/11 或 macOS 或 Linux
- **Docker Desktop**: 最新版（含 Docker Compose）
- **WSL2** (Windows 用户): 必须启用，Docker 运行在 WSL2 后端
- **内存**: 至少 4GB 可用内存（Docker 分配）
- **网络**: 同一局域网内设备可互相访问

## 快速启动（首次）

### 1. 准备环境变量

```bash
# 复制模板
cp .env.example .env

# 编辑 .env，填入以下必填项：
# - TUSHARE_TOKEN（从 https://tushare.pro/register 获取）
# - DEEPSEEK_API_KEY（从 https://platform.deepseek.com/ 获取）
# - 可选：SMTP 配置（用于邮件推送日报）
```

### 2. 构建并启动

```bash
docker compose up --build -d
```

### 3. 验证服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:8501 | Streamlit Dashboard |
| 后端 API | http://localhost:8080 | FastAPI + 自动文档 |
| API 文档 | http://localhost:8080/docs | Swagger UI |
| 数据库 | localhost:5432 | PostgreSQL（内部使用） |

### 4. 查看日志

```bash
docker compose logs -f backend   # 后端日志
docker compose logs -f frontend  # 前端日志
docker compose logs -f db        # 数据库日志
```

## 局域网访问配置

默认情况下，服务仅监听 `localhost`。要在局域网内其他设备访问，需要修改 Docker Compose 端口绑定。

### 修改 `docker-compose.yml`

将端口绑定从 `127.0.0.1:端口` 改为 `0.0.0.0:端口`（或保持默认，Docker 默认就是 0.0.0.0）：

```yaml
services:
  backend:
    ports:
      - "8080:8080"  # 所有接口可访问
  frontend:
    ports:
      - "8501:8501"
```

### 获取本机 IP

```bash
# Windows (PowerShell)
ipconfig | findstr "IPv4"

# macOS / Linux
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### 其他设备访问

假设服务器 IP 为 `192.168.1.100`：

- 前端: `http://192.168.1.100:8501`
- 后端: `http://192.168.1.100:8080`

## 日常操作

```bash
# 启动
docker compose up -d

# 停止
docker compose down

# 停止并清空数据（重置数据库）
docker compose down -v

# 重新构建后端（代码更新后）
docker compose build backend

# 进入后端容器执行命令
docker exec -it trading-backend bash

# 数据库迁移
docker exec -it trading-backend alembic upgrade head
```

## 故障排查

### 后端 500 错误

```bash
docker logs trading-backend --tail 50
```

常见原因：
- `.env` 未配置 `TUSHARE_TOKEN` 或 `DEEPSEEK_API_KEY`
- Alembic 迁移未执行：`docker exec trading-backend alembic upgrade head`

### 前端页面空白

```bash
docker restart trading-frontend
```

### 数据库连接失败

```bash
# 检查数据库状态
docker ps | grep trading-db

# 检查数据库是否健康
docker exec trading-db pg_isready -U trading
```

### 端口冲突

如果 8080/8501/5432 被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8081:8080"  # 本地 8081 映射到容器 8080
```

## 数据备份

```bash
# 备份数据库
docker exec trading-db pg_dump -U trading agent_trading > backup.sql

# 恢复数据库
docker exec -i trading-db psql -U trading agent_trading < backup.sql
```

## 安全提示

1. **不要提交 `.env` 到 Git** — 已配置 `.gitignore`
2. **局域网暴露风险** — 仅在可信网络内开放端口
3. **SMTP 密码** — 使用应用专用密码（如 Gmail App Password），不要暴露主密码

## 更新升级

```bash
# 拉取最新代码后
git pull  # 或手动更新代码

# 重新构建并启动
docker compose down -v && docker compose up --build -d
```

## 联系与支持

- 项目文档: `PROJECT.md`
- API 文档: `http://localhost:8080/docs`
- 问题排查: 查看 `docker compose logs`
