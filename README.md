# diet-agent 饮食推荐助手

基于 **Spring Boot 3 + AgentScope** 的多轮对话饮食推荐 Agent。用户用自然语言说出想吃什么，系统识别意图、追问缺失槽位、检索餐食库并生成推荐理由；同时内置了完整的 **Trace 链路追踪 + 离线评估** 能力。

## 功能特性

- **多轮对话推荐**：意图识别 → 槽位抽取 → 信息不足自动追问 → 检索重排 → 生成推荐理由。
- **6 类意图路由**：`MEAL_RECOMMENDATION`（推荐）、`CLARIFY_NEEDED`（追问）、`MEAL_ADJUST`（换一批）、`MEAL_PLAN`（多餐规划）、`HEALTH_RISK`（健康风险拦截）、`OTHER`（无关内容）。
- **双模型分工**：主模型负责推荐理由与最终应答，轻量模型负责意图识别与澄清追问，降低延迟与成本。
- **健康风险护栏**：涉及医疗诊断、极端节食等内容时按风险等级拦截。
- **个人 / 公共餐食库**：个人餐食可增删改查，公共餐食按 24 个菜系覆盖。
- **可视化前端**：聊天推荐、个人餐食、公共餐食、Trace 查看、评估报告页面（纯静态，随应用一起启动）。
- **Request Trace 与离线评估**：每次请求落库 trace，支持人工标注与批量自动评估打分。

## 技术栈

| 层 | 技术 |
|---|---|
| 运行时 | JDK 21、Spring Boot 3.3 |
| Agent 框架 | AgentScope（`agentscope-spring-boot-starter`） |
| 模型接入 | 任意 OpenAI 兼容网关（本地自建 / DashScope 兼容模式 / 其它厂商） |
| 持久层 | MyBatis + MySQL 8 |
| 工具库 | Hutool、Lombok |
| 前端 | 原生 HTML / CSS / JS（无构建步骤） |
| 部署 | Docker / Docker Compose（多阶段构建） |

## 架构与请求流程

```
前端 (#/diet/chat)
      │  POST /api/v1/diet/chat
      ▼
DietOrchestratorService（状态机）
      │
      ├─ IntentAgent          → 意图识别 + 槽位抽取
      ├─ ClarifyRuleService   → 槽位不足则追问
      ├─ RiskGuardService     → 健康风险拦截
      ├─ MealSearch/MealRank  → 按槽位检索并重排候选餐食
      └─ Recommend/Plan Agent → 生成推荐理由与最终应答
      │
      ▼
MySQL（会话 / 消息 / trace / 反馈 / 餐食库 / 槽位字典）
```

## 快速开始（Docker，推荐）

前置条件：安装 Docker 与 Docker Compose，并准备一个 **OpenAI 兼容的 LLM 网关**（本地或云端均可）。

```bash
git clone <repo-url> diet-agent
cd diet-agent

# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，至少填写 DIET_LLM_API_KEY 与 DIET_LLM_BASE_URL

# 2. 一键启动（自动建库、建表、导入种子数据）
docker compose up -d --build

# 3. 打开页面
#    http://localhost:8080/#/diet/chat
```

首次启动 MySQL 会自动执行 `01-schema.sql`、`02-seed-v2.sql`、`03-seed-v4.sql`。**若修改了初始化 SQL，需要先 `docker compose down -v` 删除数据卷再重建。**

查看日志 / 停止：

```bash
docker compose logs -f app
docker compose down          # 停止，保留数据卷
docker compose down -v       # 停止并清空数据库
```

> **容器如何访问宿主机上的网关？**
> Compose 里默认用 `host.docker.internal` 指向宿主机（已通过 `extra_hosts` 兼容 Linux）。
> 如果你的网关在别的机器上，直接把 `DIET_LLM_BASE_URL` 改成它的公网地址即可。

## 本地开发（不使用 Docker）

前置条件：JDK 21、Maven 3.9+、MySQL 8（数据库名 `diet_db`）。

```bash
# 1. 初始化数据库
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS diet_db DEFAULT CHARACTER SET utf8mb4;"
mysql -uroot -p diet_db < src/main/resources/db/diet_db.sql
mysql -uroot -p diet_db < scripts/v2-seed-meals.sql
mysql -uroot -p diet_db < scripts/v4-seed-meals.sql

# 2. 打包
mvn clean package -DskipTests

# 3. 启动（通过环境变量注入配置）
export DIET_LLM_BASE_URL=http://localhost:7863/v1
export DIET_LLM_API_KEY=sk-your-key
export DIET_LLM_MAIN_MODEL=qwen-max
export DIET_LLM_LIGHT_MODEL=qwen-turbo
java -jar target/diet-agent-1.0-SNAPSHOT.jar
```

Windows 下把 `export` 换成 `set`（CMD）或 `$env:X = "..."`（PowerShell）。

## 配置项

所有配置都可用环境变量覆盖（Spring Boot 占位符语法 `${ENV:默认值}`）。

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `DIET_DB_URL` | `jdbc:mysql://localhost:3306/diet_db?...` | 数据库连接串 |
| `DIET_DB_USERNAME` | `root` | 数据库用户名 |
| `DIET_DB_PASSWORD` | `123456` | 数据库密码 |
| `SERVER_PORT` | `8080` | 应用端口 |
| `DIET_LLM_BASE_URL` | `http://localhost:7863/v1` | OpenAI 兼容网关地址（需含 `/v1`） |
| `DIET_LLM_API_KEY` | 空 | 网关 API Key |
| `DIET_LLM_MAIN_MODEL` | `qwen-max` | 主模型（推荐理由 / 最终应答） |
| `DIET_LLM_LIGHT_MODEL` | `qwen-turbo` | 轻量模型（意图识别 / 澄清追问） |
| `DIET_SESSION_MAX_HISTORY_TURNS` | `10` | 会话保留的历史轮数 |
| `DIET_EVAL_CONCURRENCY` | `4` | 批量评估并发度 |
| `DIET_EVAL_TASK_TIMEOUT_MS` | `60000` | 单条 trace 评估超时（毫秒） |
| `DIET_LOG_LEVEL` | `INFO` | `com.diet` 包日志级别 |

Docker Compose 额外支持 `.env` 中的 `MYSQL_ROOT_PASSWORD`、`MYSQL_DATABASE`、`MYSQL_PORT`、`APP_PORT`。

> 请勿把真实 API Key 写进 `application.yml`。本地开发建议用环境变量，或新建一个已被 `.gitignore` 忽略的 `application-local.yml`。

## API 接口

除特别说明外，均需请求头 `X-User-Id: <userId>`（默认 `1`）。

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/v1/diet/sessions` | 创建会话 |
| `POST` | `/api/v1/diet/chat` | 发送一条消息（核心对话入口） |
| `GET` | `/api/v1/diet/meals/personal` | 查询个人餐食 |
| `POST` | `/api/v1/diet/meals/personal` | 新增个人餐食 |
| `PUT` | `/api/v1/diet/meals/personal/{mealId}` | 修改个人餐食 |
| `DELETE` | `/api/v1/diet/meals/personal/{mealId}` | 删除个人餐食 |
| `GET` | `/api/v1/diet/meals/public` | 查询公共餐食 |
| `GET` | `/api/v1/diet/slot-options` | 查询槽位字典 |
| `POST` | `/api/v1/diet/feedback` | 提交推荐反馈 |
| `GET` | `/api/v1/diet/debug/traces/{traceId}` | 查看单条 trace |
| `GET` | `/api/v1/diet/debug/sessions/{sessionId}/traces` | 查看会话下全部 trace |
| `GET` | `/api/v1/diet/debug/traces` | 按条件查询 trace |
| `PUT` | `/api/v1/diet/debug/traces/{traceId}/label` | 人工标注 trace |
| `POST` | `/api/v1/diet/evaluations` | 批量评估并生成报告 |

对话示例：

```bash
# 1. 创建会话
curl -X POST http://localhost:8080/api/v1/diet/sessions -H 'X-User-Id: 1'

# 2. 发消息
curl -X POST http://localhost:8080/api/v1/diet/chat \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: 1' \
  -d '{"sessionId":"<上一步返回的 sessionId>","message":"今天中午想吃点清淡减脂高蛋白的","sourceMode":"PUBLIC"}'
```

## 评测与数据集

- `scripts/dataset.json`：黄金数据集，覆盖 6 类意图，槽位值全部取自 `diet_slot_option` 字典。
- `scripts/gen-dataset.py`：在现有数据集上追加用例。
- `scripts/run-baseline.ps1`：跑数据集 → 产生 trace → 自动标注 → 批量评估 → 落盘报告。

```bash
powershell -ExecutionPolicy Bypass -File scripts/run-baseline.ps1 -IncludeJudge
```

## 目录结构

```
├── Dockerfile                 # 多阶段构建
├── docker-compose.yml         # app + MySQL 一键部署
├── .env.example               # 环境变量模板
├── pom.xml
├── src/main/java/com/diet/
│   ├── agent/                 # Agent 构建器、工厂、Prompt 加载
│   ├── config/                # AgentScope 模型配置
│   ├── controller/            # REST 接口
│   ├── enums/                 # 意图、风险等级、会话阶段等枚举
│   ├── mapper/                # MyBatis Mapper
│   ├── model/                 # 请求 / 响应 / 领域模型
│   └── service/               # 编排、意图、澄清、检索、规划、评估等服务
├── src/main/resources/
│   ├── application.yml        # 配置（不含密钥）
│   ├── db/diet_db.sql         # 建表 + 槽位字典 + 基础餐食
│   ├── diet/prompts/          # 各 Agent 的 Prompt
│   ├── mapper/                # MyBatis XML
│   └── static/                # 前端页面（原生 HTML/CSS/JS）
└── scripts/                   # 数据集、评测脚本、种子数据
```

## License

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE)：

- ✅ 允许个人学习、研究、实验、爱好项目等**非商业用途**，可以自由使用、修改、分发；
- ✅ 允许慈善机构、教育机构、公共研究/安全/卫生机构、环保组织、政府机构使用；
- ❌ **禁止任何商业用途**（含任何预期商业应用）。

> 注意：这不是 OSI 认可的开源协议，而是"源码公开 + 非商业授权"。商业授权请联系作者。
