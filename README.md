# XFunNote — 小方的万用本

> **XFunNote** = e**X**ploratory **Fun**damental **Note**book  
> 小方的万用本，个人效率与 AI 助手的实验场。

---

## 项目简介

XFunNote 是一个个人知识管理与效率工具，核心目标是：

- 整合**各类碎片信息**为结构化条目，统一存储与管理
- 借助 **AI 自动生成日报/周报**，辅助每日复盘与决策
- 作为技术实验场：Python 工程化 + AI Agent + 快速原型开发

**当前阶段**：准大一暑假 MVP 开发中

---

## 设计哲学

- **数据优先**：所有信息以条目（Entry）为单位存储，统一抽象为 `Notebook`，扩展列按需定义。
- **筛选驱动**：`Condition` + 递归 `Filter` 构成完整的查询 DSL，支持 AND/OR 嵌套、自定义运算符（`JSON_CONTAINS`、`LIKE` 等），全部下推 SQLite。
- **AI 原生**：AI 通过 Function Calling 调用 `query_entries`/`update_entries` 等安全工具，自动应用 `AI_READ_FILTER` 与 `AI_WRITE_FILTER` 行级/列级权限沙箱，杜绝越权操作。
- **记忆即数据**：用户偏好、AI 规则、分类体系均存储为 `accumulation` 本子中的条目，通过 `ai_tags`/`ai_note` 分散索引，通过 `search_memories` 统一检索。
- **本地优先**：单文件 SQLite + WAL 模式，零配置同步（iCloud/OneDrive/WebDAV 即可）。

---

## 技术栈

| 类别         | 选择                                                                    |
| ------------ | ----------------------------------------------------------------------- |
| 语言         | Python 3.10+                                                            |
| 数据库       | SQLite（WAL 模式，读写分离事务）                                        |
| CLI 框架     | Typer                                                                   |
| AI           | OpenAI SDK（兼容层，已对接 DeepSeek API）                              |
| 测试         | pytest + pytest-cov                                                     |
| 后端 API     | FastAPI（规划中）                                                       |
| 前端/界面    | Streamlit（规划中）                                                     |

---

## 功能路线图

### ✅ 已完成

| 模块 | 说明 |
|------|------|
| **数据库引擎** | 基于原生 `sqlite3`，安全参数化查询。支持 `Column` 列定义、`Condition` 筛选条件（内置 =/!=/>/</>=/<=/IN/NOT IN/BETWEEN/LIKE 及自定义运算符扩展）、递归 `Filter` 结构（外层 OR 内层 AND）、读写分离事务（写 IMMEDIATE、读不阻塞） |
| **Notebook 体系** | 抽象基类封装通用 CRUD + 自动建表 + 批量操作，子类只需定义扩展列和自动填充逻辑 |
| **内置本子** | 基于基类扩展的 4 种预置实现 — 计划（字母编号/月分组）、日记（日期维）、单词（复习跟踪/去重）、积累（分类积累）。各子类仅需定义扩展列和自动填充逻辑即可获得完整 CRUD + 批量操作 + 筛选查询，通过注册中心可插拔扩展 |
| **注册中心** | `Registry` 管理所有 Notebook 实例，支持注册/查找/注销/迭代 |
| **CLI 命令行** | 完整的 CRUD 操作：`init/reset/add/list/listid/listcolumns/delete/update`，JSON 格式输入输出 |
| **测试覆盖** | 全面覆盖核心引擎正常路径、边界条件、错误路径及事务回滚 |

### 🗺️ 规划中

按优先级分三个梯队：

**🚀 第一梯队（近期）**
- **AI Tools 层** — `xfun/ai/tools.py` 实现 8 个 Function Calling 工具，`xfun/ai/security.py` 定义 AI 读写沙箱
- **AI 日报闭环** — `xfun/ai/daily.py` 拉取当日数据，调用 DeepSeek 生成结构化摘要，支持 LaTeX 编译
- **视图层** — `xfun/core/view.py` 实现跨本子数据水合查询

**📡 第二梯队（中期）**
- **QQ 机器人推送** — 集成 go-cqhttp HTTP API，定时推送日报
- **FastAPI 后端** — `backend/main.py` 暴露 RESTful 接口
- **工具函数补全** — `file_utils.py`、`string_utils.py`

**🔭 第三梯队（远期）**
- **Streamlit 前端** — `frontend/app.py` 可视化界面
- **单词复习调度** — SM-2 间隔重复算法集成
- **多端同步** — 数据库文件置于 iCloud/OneDrive/WebDAV

---

## 设计路线图

以下路线图按开发顺序排列，每项均可在当前架构上独立增量实现。

### 阶段零：核心收尾（已完成，待合并）
- [x] `Condition` 自定义运算符注册机制（`JSON_CONTAINS`、`LIKE`、`BETWEEN` 等）
- [x] `Filter` 递归 `to_sql()`，支持无限嵌套 OR/AND + `negate`
- [x] `Notebook` 基类抽象 + 4 个本子（`plan`、`word`、`diary`、`accumulation`）
- [x] CLI 完整 CRUD（`add/list/listid/update/delete/reset/listcolumns`）
- [x] 单元测试 94 个，覆盖率 100%

### 阶段一：AI Tools 层（当前进行中）
- [ ] 在 `xfun/ai/tools.py` 中实现：
  - `query_entries`（只读，自动合并 `AI_READ_FILTER`）
  - `update_entries`（可写，自动合并 `AI_WRITE_FILTER` + 列白名单）
  - `add_entries`（自动注入 `is_ai_gen=1`）
  - `delete_entries`（强制安全条件 + 预览拦截）
  - `manage_tags`（追加/替换 `tags` 或 `ai_tags`）
  - `add_ai_note`（追加 `ai_note`，保留历史）
  - `search_memories`（同时检索所有本子的 `ai_tags` 与 `ai_note`）
  - `save_memory`（写入 `accumulation` 本子，`category="AI记忆"`）
- [ ] 在 `xfun/ai/security.py` 中定义：
  - `AI_READ_FILTER`（行级读权限）
  - `AI_WRITE_FILTER`（行级写权限）
  - `AI_WRITABLE_COLUMNS`（列白名单）
- [ ] 在 `xfun/ai/client.py` 中封装 DeepSeek API 调用，注入上述 Tools

### 阶段二：View 层（数据水合与跨本子查询）
- [ ] 实现 `xfun/core/view.py`：
  - `View.query(notetype, filter_groups, fields, limit, offset)` — 跨单/多本子查询，返回完整条目列表
  - 自动合并 `AI_READ_FILTER`（安全沙箱）
  - 支持 `fields` 限定列，减少 Token 消耗
  - 将 `Filter` 递归 `to_sql()` 翻译为 SQL，下推数据库
- [ ] 在 CLI 中接入 `view` 调试命令（可选）

### 阶段三：AI 日报闭环（核心 AI 功能）
- [ ] 实现 `xfun/ai/daily.py`：
  - `generate_daily_report()` — 拉取当日计划/单词/积累，调用 DeepSeek 生成结构化摘要
  - 支持 **LaTeX 模板填充** + **迭代编译**（`pdflatex`，最多重试 3 次，失败回退纯文本）
- [ ] 实现 `xfun/ai/latex.py`：
  - `compile_latex(content: str) -> (pdf_path, error_log)` — 临时目录编译，超时保护
- [ ] 实现用户反馈学习：
  - 用户在 QQ 中反馈意见 → AI 调用 `save_memory` 存储偏好
  - 下次生成日报时，AI 先查询 `accumulation` 中 `category="AI记忆"` 且 `tags` 含 `日报` 的记忆，自动调整模板
- [ ] CLI 命令 `./cli.py daily` 生成当日日报（输出文本或 PDF）

### 阶段四：推送与定时任务
- [ ] 集成 QQ 机器人（HTTP API 客户端）：
  - 通过 `go-cqhttp` 或 `mirai` 接收推送
  - 在 `config.py` 中配置 `QQ_GROUP_ID` / `QQ_USER_ID`
- [ ] CLI 命令 `./cli.py push`：
  - 调用 `daily` 生成 PDF
  - 通过 QQ API 发送文件/消息
- [ ] 配置 Cron 定时任务：
  ```bash
  0 20 * * * cd ~/XFunNote && source .venv/bin/activate && python cli.py push
  ```

### 阶段五：FastAPI 后端（对外接口）
- [ ] 实现 `backend/main.py`：
  - 路由：`/api/v1/notebooks/{name}/entries`（`GET`/`POST`/`PUT`/`DELETE`）
  - 路由：`/api/v1/ai/daily`（日报生成）
  - 路由：`/api/v1/ai/memory`（记忆查询与保存）
- [ ] 依赖注入 + CORS 配置
- [ ] Pydantic Schemas 映射（`ConditionSchema` ↔ `Condition`）
- [ ] 启动：`uvicorn backend.main:app --reload`

### 阶段六：前端可视化（可选）
- [ ] Streamlit 界面 `frontend/app.py`：
  - 计划列表/筛选/增删改
  - 日记时间线
  - 日报查看/导出
- [ ] 调用 FastAPI 后端（而非直接操作数据库）

### 阶段七：多端同步与扩展（远期）
- [ ] `import/export` 命令：JSON 导入导出（已有 `add` 支持 JSON，`dump` 只需 `SELECT *` + `json.dump`）
- [ ] 多账户支持：`--user` 参数切换数据库文件
- [ ] 多端同步：数据库文件置于 iCloud/OneDrive/WebDAV（由用户自行配置）
- [ ] 移动端网页：Streamlit 部署至公网（或 Tailscale 内网穿透）

---

## 开发蓝图 — 核心架构决策

以下决策是 XFunNote 区别于普通"计划管理工具"的根本所在，也是后续开发的行动纲领。

### 1. 查询引擎：纯 SQL 下推，绝不内存过滤
- `Filter` 递归结构（外层 OR、内层 AND）通过 `to_sql()` 无损展开为一条 SQL。
- 所有自定义运算符（`JSON_CONTAINS`、`TEXT_SEARCH` 等）只注册一次 SQL 生成逻辑，永不重复实现 Python 等价逻辑。
- SQLite 优先走索引列（如 `month`、`done`）压缩数据量，再对少量数据执行 JSON/文本运算，性能充足。

### 2. AI 安全沙箱：零信任行级/列级权限
- `AI_READ_FILTER`：强制行级读权限（例如 `is_ai_gen=1`）。
- `AI_WRITE_FILTER`：强制行级写权限（防止 AI 修改用户手工数据）。
- `AI_WRITABLE_COLUMNS`：列白名单（禁止 AI 触碰 `id`、`created_at`、`seq` 等系统列）。
- 删除操作必须经过"预览 → 确认"流程，禁止无条件删除。

### 3. 记忆系统：显式记忆库 + 分散痕迹的统一检索
- 显式记忆存储在 `accumulation` 本子（`category="AI记忆"`），由 `save_memory` / `search_memories` 管理。
- 分散痕迹存储在各类条目的 `ai_tags` 和 `ai_note` 中，通过 `JSON_CONTAINS` / `TEXT_SEARCH` 运算符检索。
- `search_memories` 工具统一跨源检索，对外呈现为单一记忆接口。

### 4. AI 日报闭环：从生成到交付的自动化
- AI 填充 LaTeX 模板 → 后端 `pdflatex` 编译（最多 3 次迭代纠错）→ 输出 PDF。
- 用户通过 QQ 反馈 → AI 调用 `save_memory` 固化偏好 → 次日日报自动适配。
- `cron` 定时触发 `cli.py push`，通过 QQ 机器人推送 PDF。

### 5. 开发优先级
| 优先级 | 阶段 | 产出 |
| :--- | :--- | :--- |
| 🔴 当前 | AI Tools 层 | `xfun/ai/security.py` + `xfun/ai/tools.py`（8 个工具） |
| 🟡 后续 | View 层 | `xfun/core/view.py`（跨本子数据水合） |
| 🟢 核心 | AI 日报闭环 | `daily.py` + `latex.py` + `push` + QQ 集成 |
| 🔵 按需 | FastAPI 后端 | `backend/main.py` RESTful API |
| ⚪ 远期 | 前端可视化 | `frontend/app.py` Streamlit 界面 |

---

## 配置

### 1. 环境变量

复制项目根目录的 `.env.example` 为 `.env` 并填写配置。

| 变量 | 说明 |
|------|------|
| `XFUN_USER` | 数据库用户名，拼接为 `data/{用户名}.db`。若未设置，默认回退为 `data/default.db` |
| `AI_API_KEY` | DeepSeek API Key，用于 AI 功能 |
| `AI_BASE_URL` | DeepSeek API 端点，默认为 `https://api.deepseek.com` |
| `AI_MODEL` | 默认模型，建议 `deepseek-v4-flash` |
| `QQ_BOT_HTTP_URL` | QQ 机器人 HTTP API 地址（推送日报用） |

### 2. 数据库路径

数据库默认路径为 `data/{用户名}.db`，通过 `XFUN_USER` 自动拼接。  
SQLite 以 **WAL 模式**运行，支持并发读写不阻塞。

---

## 快速开始

```bash
# 1. 一键创建虚拟环境并安装依赖
chmod +x setup.sh && ./setup.sh

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 初始化数据库（自动建表）
./cli.py init

# 4. 添加一条计划
./cli.py add plan '{"month": "2607", "content": "学习 Python 基础"}'

# 5. 列出所有计划
./cli.py list plan

# 6. 查看列定义
./cli.py listcolumns plan
```

---

## CLI 参考

CLI 依托 Typer 构建，所有子命令以 `notename` 为第一个位置参数，从注册中心动态查找对应的 Notebook 实例，因此对任意已注册的本子通用。

### 设计要点

- **JSON 输入/输出** — `add` / `update` 接收 JSON 条目，`list` / `listid` / `listcolumns` 输出 JSON，便于管道组合与脚本集成
- **批量操作** — `add` / `list` / `delete` / `update` 均支持单条或批量，统一使用 JSON 标记
- **筛选引擎** — `listid --filter` 采用 OR-of-ANDs 筛选结构，支持单条件、多条件与组合（AND）以及多组或（OR of ANDs），`op` 可扩展至 `IN` / `BETWEEN` / `LIKE` 等运算符，`negate` 可反转条件
- **排序分页** — `--order-by` 支持多列排序（如 `month ASC, no`），`--limit` / `--offset` 控制分页

### 子命令一览

| 命令 | 作用 | 关键参数 |
|------|------|----------|
| `init` | 初始化数据库和所有已注册本子 | 无 |
| `reset` | 清空 data 目录并重新初始化 | 无 |
| `add` | 添加条目（单条或批量） | `notename`, `entry`(JSON) |
| `list` | 按 ID 查询条目 | `notename`, `entry_ids`(JSON) |
| `listid` | 按条件筛选 ID 列表 | `notename`, `--filter`, `--order-by`, `--limit`, `--offset` |
| `update` | 批量更新字段 | `notename`, `entry_ids`(JSON), `entry`(JSON) |
| `delete` | 批量删除 | `notename`, `entry_ids`(JSON) |
| `listcolumns` | 查看本子的列定义 schema | `notename` |

### 常用示例

```bash
# 筛选 2607 月未完成的计划
./cli.py listid plan --filter '{"column":"month","value":"2607","op":"="}' --limit 10

# 批量添加两条计划
./cli.py add plan '[{"month":"2607","content":"任务A"},{"month":"2607","content":"任务B"}]'

# 标记为已完成
./cli.py update plan '["plan-2607-001"]' '{"done":1}'
```

---

## 核心概念

| 概念 | 说明 |
|------|------|
| **Notebook** | 数据容器基类，子类定义 `_extra_columns` 即可获得完整 CRUD + 筛选能力 |
| **Condition** | 单个筛选条件（`column op value`），支持 `JSON_CONTAINS`、`TEXT_SEARCH` 等自定义运算符注册 |
| **Filter** | 递归结构：外层 `OR`，内层 `AND`，支持无限嵌套与整体取反，最终由 `to_sql()` 展开为 SQL WHERE |
| **View** | `query_view(notetype, filter, fields)` 跨本子数据水合，是 AI 与前端的数据唯一入口 |
| **AI Tools** | `query_entries`、`update_entries`、`add_entries`、`delete_entries`、`manage_tags`、`add_ai_note`、`search_memories`、`save_memory` 共 8 个工具 |
| **记忆系统** | `accumulation` 本子存储结构化记忆（标题 + 内容 + 标签）+ 各本子 `ai_tags`/`ai_note` 分散索引，由 `search_memories` 统一检索 |

---

## 项目结构

```
XFunNote/
├── cli.py                  # 命令行入口
├── setup.sh                # 环境构建脚本
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板（复制为 .env 后填写）
│
├── xfun/                   # 核心库包
│   ├── core/               #   核心引擎
│   │   ├── db.py           #     数据库层（Column/Condition/DB/Filter）
│   │   ├── notebook.py     #     Notebook 抽象基类
│   │   ├── registry.py     #     注册中心
│   │   ├── errors.py       #     异常体系
│   │   └── view.py         #     [待实现] 跨本子数据水合与查询
│   ├── notebooks/          #   具体 Notebook 实现
│   │   ├── plan.py         #     计划本
│   │   ├── diary.py        #     日记本
│   │   ├── word.py         #     单词本
│   │   └── accumulation.py #     积累本
│   ├── ai/                 #   [待实现] AI 模块
│   ├── utils/              #   工具函数
│   │   ├── time_utils.py   #     时间日期工具
│   │   ├── file_utils.py   #     [待实现] 文件工具
│   │   └── string_utils.py #     [待实现] 字符串工具
│   ├── config.py           #   配置读取
│   └── __init__.py         #   模块入口，注册内置 Notebook
│
├── backend/
│   └── main.py             # [待实现] FastAPI 后端
├── frontend/
│   └── app.py              # [待实现] Streamlit 前端
├── scripts/
│   └── testai.py           # AI 连接测试脚本
├── tests/                  # 测试套件
├── data/                   # SQLite 数据库
├── input/                  # AI 记忆 / 计划文件
└── output/                 # AI 输出目录
```

---

## API 文档

FastAPI 后端尚在规划中，上线后将暴露与 CLI 对等的 RESTful 接口。

---

## 测试

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=xfun --cov-report=term-missing

# 运行特定文件
pytest tests/test_db.py
```

---

## 许可证

Apache 2.0 © 2026 fangjunyi0710

---

## 作者

FangJunyi0710（小_方_）
