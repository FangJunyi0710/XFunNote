# XFunNote — 小方的万用本

> **XFunNote** = e**X**ploratory **Fun**damental **Note**book  
> 小方的万用本，个人效率与 AI 助手的实验场。

---

## 概述

XFunNote 是一个个人知识管理与效率工具，核心目标是整合碎片信息为结构化条目、借助 AI 自动生成日报/周报辅助复盘、以及作为 Python 工程化 + AI Agent 的快速原型实验场。

**设计定位**：XFunNote 不是"一个管理计划的 App"，而是**一个能够容纳个人全部时间、记忆、对话、知识、零散信息的容器**。它以**本地优先 + 手机即服务器**为部署模型——所有数据存储于设备本地 SQLite 文件中，同一 WiFi 下的任何设备均可通过浏览器访问，飞行模式也可用。这种架构保证了数据的永久可访问性和完全的隐私控制，不受第三方平台政策变更的影响。

AI 的"懂你"能力来源于系统内沉淀的多维度数据，当这些数据在同一个系统里积累足够长时间后，AI 能自然地感知时间跨度和感情变化，产生个性化的反馈。

**当前阶段**：准大一暑假 MVP 开发中。Python 核心引擎（xfun/）+ FastAPI 后端已完成，React 前端（页面组件 + 状态管理 + 路由体系）已完成。

### 核心亮点

- **临时层（对话的版本控制）**：最独特的创新。支持回到任意对话节点分支出新路径、编辑历史消息让 AI 重新生成、保存快照随时回退——让 AI 对话从线性指令变成可编排的实验场。
- **多维数据感知**：AI 的"懂你"源于意图、行为、感受、输入等数据在同一系统中长期沉淀，使其能自然感知时间跨度与情感变化。
- **三端统一访问**：手机运行服务，电脑/平板通过 `http://hostname.local` 访问（同一 WiFi），其他设备通过 Tailscale/ZeroTier 安全接入。

---

## 快速开始

```bash
# 1. 一键创建虚拟环境并安装依赖
chmod +x setup.sh && ./setup.sh

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 复制项目根目录的 `.env.example` 为 `.env` 并填写配置（环境变量说明见 `.env.example` 文件头部）。

# 4. 启动后端
chmod +x backend/main.py && ./backend/main.py
# HTTPS 模式（需先运行 ./scripts/gen_cert.sh 并配置 .env）

# 5. 另开终端启动前端
cd frontend
npm install && npm run dev # 若使用低于 1024 端口需改为 sudo npm run dev
```

### 安全性提升：前端使用 HTTPS

使用自签名证书保护前端，若未生成并配置证书，前端会自动回退到 HTTP 模式，行为与之前一致。

前端 HTTPS 模式下自动启动一个 HTTP 重定向服务，将 `http://hostname.local` 的请求 301 重定向到 `https://hostname.local`。这样局域网其他设备访问 `http://hostname.local` 即可自动跳转到 HTTPS 前端。具体端口可在 `./.env` 修改。

**注意**：浏览器会提示自签名证书不安全，这是正常的，选择"继续前往"即可。可将证书加入系统或浏览器的受信任列表以永久消除警告。生产环境应使用受信任的 CA 证书或配置 DNS 泛域名证书。

```bash
# 1. 生成自签名证书到 ./certs/
./scripts/gen_cert.sh

# 2. 编辑 .env 添加 SSL_CERT_PATH, SSL_KEY_PATH

# 3. 之后操作与非 HTTPS 相同
# ...
```

### 便捷性提升：mDNS 局域网访问

局域网中的其他设备可通过 `hostname.local` 域名访问本服务，无需记忆并输入 IP 地址。

**注意**：部分浏览器缺乏对 mDNS 域名的解析功能，需更换浏览器或仍直接访问 `http://[服务器IP]` 或 `https://[服务器IP]`。

```bash
# 安装 Avahi
sudo apt update
sudo apt install avahi-daemon avahi-utils -y

# 启动 Avahi
sudo systemctl enable --now avahi-daemon.service

# 若修改 .env 中的主机名，需手动刷新 Avahi 配置以在局域网中生效
chmod +x ./scripts/update_avahi_hostname.sh
sudo ./scripts/update_avahi_hostname.sh
```

---

## 核心架构

### 设计哲学
- **数据优先与本地闭环**：一切数据以 `Notebook` 条目（Entry）为单位存储；单文件 SQLite（WAL 模式）承载所有数据。
- **AI 原生与安全前置**：AI 通过 Function Calling 调用数据工具，全程受 `_permission` 表约束的行级/列级沙箱钳制，过滤逻辑强制下推 SQL。
- **身份即视角**：以 `(read_view, write_view)` 元组定义"身份"，用户可自由定义创建新身份。

### 数据模型与核心编排
- **Notebook**：数据容器基类，子类定义 `_extra_columns` 即获完整 CRUD。筛选由 `Condition`（支持 `JSON_CONTAINS`/`LIKE`/`TEXT_SEARCH` 等自定义运算符）与递归 `Filter`（外层 OR、内层 AND，支持无限嵌套与取反）构成查询语言。
- **View 与 Permission**：View 描述跨本子的列+行数据子集；Permission 为 `(read_view, write_view)` 元组，写视图强制为读视图子集。Permission 通过双元组精细控制四个 CRUD 操作：

  | 操作 | 控制方式 |
  |------|---------|
  | **Query / Count** | `query_view` 与 `read_view` 取 AND 交集，仅返回读视图允许的列和行 |
  | **Add** | `view_clean_add()` 过滤 entries，仅保留写视图中出现的列；表不在写视图中则拒绝写入 |
  | **Update** | `view_clean_update()` 对写视图中每个 `(列集, 行筛选)` 规格分别取列交集 + 行筛选 AND 组合；不在写视图中的列被静默丢弃 |
  | **Delete** | `view_clean_delete()` 仅当写视图的某规格包含 `id` 列时允许删除，且行筛选被限制在写视图范围内 |
- **Ops 统一入口**：`query` / `count` / `add` / `update` / `delete` 五个高维函数，内部自动编排 View、Permission 与 Notebook，是 API 和 AI Tools 的唯一数据操作入口。
- **系统支撑表**：

  | 表名 | 用途 |
  |------|------|
  | `_token` | API 鉴权，支持 Shortcut 一次性兑换、过期/停用 |
  | `_view` | 存储命名的 View 定义，通过 `name` 引用 |
  | `_filter` | 存储命名的 Filter 条件，通过 REF 运算符引用复用 |
  | `_permission` | 定义 `(读视图, 写视图)` 身份 |

  四张系统表通过对应管理路由（`/views/*`、`/permissions/*`、`/tokens/*`、`/filters/*`）进行 CRUD。

  ### 权限沙箱
- AI Chat 自动计算 **Token 权限 ∩ AI 模式预设权限** 的交集，遵循最小权限原则。
- 写操作前自动清洗非授权列；删除操作强制"预览 → 确认"两阶段。
- `_TOOL_REGISTRY` 注册 5 个工具工厂，不同 AI 模式可绑定不同工具子集。

### 查询下推引擎
- `Filter.to_sql()` 将嵌套条件无损翻译为单条 SQL WHERE；`View.to_sql()` 将跨本子 UNION ALL + 去重完全下推至 SQLite。
- 优先走索引列压缩数据集，再对少量结果执行 JSON/文本运算。
- 自定义运算符单点注册，消除双引擎不一致风险。

### AI 原生能力
- **三级记忆**：显式记忆（`aimemory`，按 `[事实]/[历史]/[策略]` 前缀分类）、知识积累（`accumulation`）、分散索引（各本子 `ai_tags`/`ai_note`）。
- **Agent 引擎**：`agent_invoke()` 提供 TOKEN/MSG/SYNC 三级流式粒度，配套完整消息序列化基建。
- **工具工厂与 Agent 循环**：AI 工具通过 `make_tools(tool_names, permission)` 工厂模式创建，每个工具在创建时绑定权限闭包，确保仅操作授权数据。`agent_invoke()` 执行"LLM 调用 → 工具执行 → 结果反馈"循环，最大迭代次数由 `max_iterations` 控制。

  ### 核心模块职责

| 模块 | 核心职责 |
|------|---------|
| `db.py` | 数据库连接管理、WAL 模式、事务隔离（写事务 `BEGIN IMMEDIATE` / 读事务 `BEGIN`）、建表/补齐列/建索引、钩子驱动的 CRUD、在线热备份与恢复 |
| `notebook.py` | `Notebook` 基类，定义 9 个通用字段，子类通过 `_extra_columns` 扩展 + `_pre_add`/`_validate`/`_autofill` 三钩子定制行为 |
| `filter.py` | `Condition` + `Filter` 递归筛选 DSL，`filter_to_sql()` 全下推为单条 SQL WHERE |
| `view.py` | `View` 跨表数据子集描述，`view_to_sql()` 生成 UNION ALL + GROUP BY 去重查询，`view_or()`/`view_and()` 布尔组合，`view_clean_*()` 列级写清洗 |
| `ops.py` | `query`/`count`/`add`/`update`/`delete` 五个高维函数，统一编排 View、Permission 与 Notebook，是 API 和 AI Tools 的唯一数据操作入口 |
| `extras.py` | 注册 `JSON_CONTAINS`/`JSON_NOT_CONTAINS`/`TEXT_SEARCH`/`TRUE`/`FALSE` 五个扩展运算符 |
| `errors.py` | `XFunError` 基类 + 7 个子异常 |

### 内置本子一览

| 本子 | 特有字段 | 行为钩子 |
|------|---------|---------|
| `plan` | `no`(自动编号), `seq`(同月自增), `month`(YYMM), `done` | `_autofill`: 自动生成 `no`（如 `2606A`）；`_pre_add`: 同月内自动分配递增 seq |
| `diary` | `date`, `mood`, `weather` | 无 |
| `word` | `word`(唯一), `part_of_speech`, `phonetic`, `example`, `review_count`, `performance`, `next_review`, `last_review`, `related_words` | `_autofill`: 填充 `review_count`/`performance` 默认值 |
| `accumulation` | `source` | 无 |
| `aimemory` | `title`(必填), `source` | 无 |
| `timeline` | `start_time`(必填), `end_time`(可选), `location`(可选) | 无 |
| `schedule` | `start_time`(必填), `end_time`(可选), `location`(可选) | 无 |

所有本子共有 9 个基类字段：`id`, `content`, `created_at`, `updated_at`, `tags`, `note`, `is_ai_gen`, `ai_tags`, `ai_note`。

---

## 技术栈与项目组织

### 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | Python 3.10+, FastAPI, Typer | RESTful 接口 + CLI 管理 |
| AI | LangChain + DeepSeek API | 通过 `langchain_anthropic.ChatAnthropic` 兼容封装，支持 thinking blocks 和 tool calling |
| 数据契约 | Pydantic | 数据模型 + JSON Schema 双重校验，供 AI Function Calling 入参约束 |
| 前端 | React 18, TypeScript, Vite 5, Tailwind CSS 3 | 自建组件体系（button/card/dialog/input/select/tabs/switch/badge 等），无第三方 UI 库 |
| 状态管理 | Zustand | 5 个 Store：notebookStore / chatStore / sidebarStore / tokenStore / themeStore |
| 路由 | react-router-dom v6 | 8 个页面组件 |
| 测试 | pytest, pytest-cov | 27 个测试文件覆盖核心引擎、AI 层与后端路由 |
| 数据库 | SQLite（WAL 模式） | 单文件存储 |

### 前端路由结构

| 路径 | 页面组件 | 说明 |
|------|---------|------|
| `/` | Home | 首页 |
| `/notebooks/:type` | Notebook*Page（7 个） | 每个内置本子对应一个页面组件 |
| `/notebooks/:notetype/new` | NotebookEditPage | 新建条目 |
| `/notebooks/:notetype/edit/:id` | NotebookEditPage | 编辑条目 |
| `/notebooks/:notetype/batch-update` | NotebookEditPage | 批量更新 |
| `/notebooks/:notetype/filter` | NotebookFilter | Filter 编辑 |
| `/ai` | AiChat | AI 对话界面 |
| `/management` | Management | 系统管理（视图/权限/Token/数据库 4 个 Tab） |
| `/token-input` | TokenInputPanel | Token 输入面板 |

---

## 路线图

### 阶段零：核心引擎与基础本子
- [x] 数据库引擎、Ops 操作层、Notebook 抽象基类
- [x] 7 个内置本子
- [x] 注册中心
- [x] 400+ 单元测试

### 阶段一：AI Tools 层
- [x] 5 个 Function Calling 工具
- [x] Pydantic 模型及 JSON Schema 双重校验
- [x] 系统提示词、Agent 对话引擎
- [x] CLI 命令行（10 个命令）
- [ ] 计算/分析工具、联网搜索工具、文本搜索工具（tools.py）
- [ ] `replace` 工具管理标签等功能（tools.py）
- [ ] `compile_latex` 工具（tools.py）

### 阶段二：View 层
- [x] `view_to_sql`（跨本子 UNION ALL + 去重下推）
- [x] `view_or`/`view_and`
- [x] `view_clean_*` 安全沙箱
- [x] 序列化/反序列化、ViewModel Pydantic 校验

### 阶段三：FastAPI 后端
- [x] RESTful 路由（notebooks/ai/views/tokens/permissions/filters/db）
- [x] Token 鉴权体系
- [x] 依赖注入与 CORS
- [ ] Filter 编辑器/管理页面
- [x] 批量更新功能
- [x] 深色主题
- [x] 分页器跳转
- [ ] 增加导入导出功能
- [x] HTTPS 增强安全

### 阶段四：前端可视化
- [x] 列表/筛选/增删改
- [ ] 日记时间线等的三级概览视图以及其他精致UI
- [ ] AI 流式对话配置界面
- [ ] 日报查看/导出
- [ ] 实现 filter 编辑器页面
- [ ] 前端实现真正的视图筛选
- [ ] 前端在权限被拒时根据 ops 返回值提示

### 阶段五：AI 日报闭环
- [ ] `generate_daily_report()` 拉取当日数据
- [ ] DeepSeek 生成摘要
- [ ] LaTeX 模板填充 + 迭代编译（最多重试 3 次）
- [ ] 用户反馈学习

### 阶段六：记忆导入与持续学习
- [ ] ChatGPT 对话导出解析
- [ ] Markdown/纯文本批量导入
- [ ] 持续学习模块
- [ ] 命令行聊天界面
- [ ] 记忆导入与持续学习模块

### 远期路线
- [ ] QQ 机器人推送与定时任务
- [ ] 多端同步与扩展
- [ ] 工具函数补全与复习调度
- [ ] 三档 AI 模式：白板模式（零工具）/ 查询模式（仅只读）/ 读写模式（完全 CRUD）
- [ ] 临时层系统
- [ ] 零散信息整合
- [ ] 本地优先部署完善
- [ ] 核心引擎补全（正则运算符、权限安全修复）
- [ ] AI 工具变量机制
- [ ] 正则表达式匹配运算符


---
## 项目结构
<!-- begin project tree -->
```
XFunNote/
├── backend/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ai.py
│   │   ├── manage_db.py
│   │   ├── manage_filter.py
│   │   ├── manage_permission.py
│   │   ├── manage_token.py
│   │   ├── manage_view.py
│   │   └── notebooks.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── management_service.py
│   │   └── notebook_service.py
│   ├── __init__.py
│   ├── deps.py
│   ├── main.py
│   └── schemas.py
├── data/
│   └── backups/
│       └── .gitkeep
├── frontend/
│   ├── public/
│   │   └── xfun.svg
│   ├── src/
│   │   ├── api/
│   │   │   ├── ai.ts
│   │   │   ├── client.ts
│   │   │   ├── filters.ts
│   │   │   ├── management.ts
│   │   │   ├── notebooks.ts
│   │   │   ├── permissions.ts
│   │   │   ├── tokens.ts
│   │   │   └── views.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Layout.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── notebook/
│   │   │   │   ├── notebookCards/
│   │   │   │   │   ├── index.ts
│   │   │   │   │   ├── NotebookCard.tsx
│   │   │   │   │   └── NotebookCardList.tsx
│   │   │   │   ├── notebookForms/
│   │   │   │   │   ├── defaultForm.tsx
│   │   │   │   │   └── index.ts
│   │   │   │   ├── FilterEditor.tsx
│   │   │   │   ├── NotebookLayout.tsx
│   │   │   │   └── Pagination.tsx
│   │   │   └── ui/
│   │   │       ├── badge.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── checkbox.tsx
│   │   │       ├── ConfirmDialog.tsx
│   │   │       ├── dialog.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── icons.tsx
│   │   │       ├── input.tsx
│   │   │       ├── label.tsx
│   │   │       ├── select.tsx
│   │   │       ├── separator.tsx
│   │   │       ├── switch.tsx
│   │   │       ├── tabs.tsx
│   │   │       ├── textarea.tsx
│   │   │       ├── Timestamp.tsx
│   │   │       ├── Toast.tsx
│   │   │       └── TokenValueDisplay.tsx
│   │   ├── config/
│   │   │   └── notebook.ts
│   │   ├── lib/
│   │   │   ├── error.ts
│   │   │   ├── type-guards.ts
│   │   │   └── utils.ts
│   │   ├── pages/
│   │   │   ├── AiChat.tsx
│   │   │   ├── DatabaseManagement.tsx
│   │   │   ├── Home.tsx
│   │   │   ├── Management.tsx
│   │   │   ├── NotebookAccumulation.tsx
│   │   │   ├── NotebookAimemory.tsx
│   │   │   ├── NotebookDiary.tsx
│   │   │   ├── NotebookEditPage.tsx
│   │   │   ├── NotebookFilter.tsx
│   │   │   ├── NotebookLedger.tsx
│   │   │   ├── NotebookPlan.tsx
│   │   │   ├── NotebookSchedule.tsx
│   │   │   ├── NotebookTimeline.tsx
│   │   │   ├── NotebookWord.tsx
│   │   │   ├── PermissionManagement.tsx
│   │   │   ├── TokenInputPanel.tsx
│   │   │   ├── TokenManagement.tsx
│   │   │   └── ViewManagement.tsx
│   │   ├── stores/
│   │   │   ├── chatStore.ts
│   │   │   ├── notebookStore.ts
│   │   │   ├── sidebarStore.ts
│   │   │   ├── themeStore.ts
│   │   │   └── tokenStore.ts
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── filter.ts
│   │   │   ├── notebook.ts
│   │   │   ├── permission.ts
│   │   │   ├── token.ts
│   │   │   └── view.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── input/
│   └── .gitkeep
├── output/
│   └── .gitkeep
├── scripts/
│   ├── gen_cert.sh
│   ├── project_info.py
│   ├── replace.py
│   ├── update_avahi_hostname.sh
│   └── update_readme.sh
├── tests/
│   ├── backend/
│   │   ├── conftest.py
│   │   ├── test_ai.py
│   │   ├── test_db_management.py
│   │   ├── test_deps.py
│   │   ├── test_filters.py
│   │   ├── test_main.py
│   │   ├── test_notebooks.py
│   │   ├── test_permissions.py
│   │   ├── test_tokens.py
│   │   └── test_views.py
│   ├── xfun/
│   │   ├── conftest.py
│   │   ├── test_accumulation.py
│   │   ├── test_ai_agent.py
│   │   ├── test_ai_prompts.py
│   │   ├── test_ai_schema.py
│   │   ├── test_ai_tools.py
│   │   ├── test_aimemory.py
│   │   ├── test_db.py
│   │   ├── test_diary.py
│   │   ├── test_extras.py
│   │   ├── test_filter.py
│   │   ├── test_notebook.py
│   │   ├── test_ops.py
│   │   ├── test_plan.py
│   │   ├── test_registry.py
│   │   ├── test_schedule.py
│   │   ├── test_time_utils.py
│   │   ├── test_timeline.py
│   │   ├── test_token.py
│   │   ├── test_view.py
│   │   └── test_word.py
│   └── __init__.py
├── xfun/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   ├── schema.py
│   │   └── tools.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── errors.py
│   │   ├── extras.py
│   │   ├── filter.py
│   │   ├── notebook.py
│   │   ├── ops.py
│   │   └── view.py
│   ├── notebooks/
│   │   ├── __init__.py
│   │   ├── accumulation.py
│   │   ├── aimemory.py
│   │   ├── diary.py
│   │   ├── ledger.py
│   │   ├── plan.py
│   │   ├── schedule.py
│   │   ├── timeline.py
│   │   └── word.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py
│   │   ├── time_utils.py
│   │   └── token_utils.py
│   ├── __init__.py
│   ├── config.py
│   └── system_tables.py
├── .env.example
├── .gitattributes
├── .gitignore
├── cli.py
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt
└── setup.sh
```
<!-- end project tree -->

### 依赖关系图

<!-- begin dependence graph -->
```mermaid
graph LR
    subgraph scripts[scripts]
        scripts_project_info(project_info)
        scripts_replace(replace)
    end
    style scripts fill:#d4f0c0,stroke:#333,stroke-width:1px,color:#333
    subgraph tests[tests]
        tests___init__(__init__)
    end
    style tests fill:#e8f4fd,stroke:#333,stroke-width:1px,color:#333
    subgraph backend[backend]
        backend___init__(__init__)
        backend_deps(deps)
        backend_main(main)
        backend_schemas(schemas)
    end
    style backend fill:#ffe0f0,stroke:#333,stroke-width:1px,color:#333
    subgraph backend_routers[backend/routers]
        backend_routers___init__(__init__)
        backend_routers_ai(ai)
        backend_routers_manage_db(manage_db)
        backend_routers_manage_filter(manage_filter)
        backend_routers_manage_permission(manage_permission)
        backend_routers_manage_token(manage_token)
        backend_routers_manage_view(manage_view)
        backend_routers_notebooks(notebooks)
    end
    style backend_routers fill:#f0e6ff,stroke:#333,stroke-width:1px,color:#333
    subgraph backend_services[backend/services]
        backend_services___init__(__init__)
        backend_services_ai_service(ai_service)
        backend_services_management_service(management_service)
        backend_services_notebook_service(notebook_service)
    end
    style backend_services fill:#fff3cd,stroke:#333,stroke-width:1px,color:#333
    subgraph _[.]
        cli(cli)
    end
    style _ fill:#ffe0e0,stroke:#333,stroke-width:1px,color:#333
    subgraph tests_backend[tests/backend]
        tests_backend_conftest(conftest)
        tests_backend_test_ai(test_ai)
        tests_backend_test_db_management(test_db_management)
        tests_backend_test_deps(test_deps)
        tests_backend_test_filters(test_filters)
        tests_backend_test_main(test_main)
        tests_backend_test_notebooks(test_notebooks)
        tests_backend_test_permissions(test_permissions)
        tests_backend_test_tokens(test_tokens)
        tests_backend_test_views(test_views)
    end
    style tests_backend fill:#d5f5e3,stroke:#333,stroke-width:1px,color:#333
    subgraph tests_xfun[tests/xfun]
        tests_xfun_conftest(conftest)
        tests_xfun_test_accumulation(test_accumulation)
        tests_xfun_test_ai_agent(test_ai_agent)
        tests_xfun_test_ai_prompts(test_ai_prompts)
        tests_xfun_test_ai_schema(test_ai_schema)
        tests_xfun_test_ai_tools(test_ai_tools)
        tests_xfun_test_aimemory(test_aimemory)
        tests_xfun_test_db(test_db)
        tests_xfun_test_diary(test_diary)
        tests_xfun_test_extras(test_extras)
        tests_xfun_test_filter(test_filter)
        tests_xfun_test_notebook(test_notebook)
        tests_xfun_test_ops(test_ops)
        tests_xfun_test_plan(test_plan)
        tests_xfun_test_registry(test_registry)
        tests_xfun_test_schedule(test_schedule)
        tests_xfun_test_time_utils(test_time_utils)
        tests_xfun_test_timeline(test_timeline)
        tests_xfun_test_token(test_token)
        tests_xfun_test_view(test_view)
        tests_xfun_test_word(test_word)
    end
    style tests_xfun fill:#fdebd0,stroke:#333,stroke-width:1px,color:#333
    subgraph xfun[xfun]
        xfun___init__(__init__)
        xfun_config(config)
        xfun_system_tables(system_tables)
    end
    style xfun fill:#d6eaf8,stroke:#333,stroke-width:1px,color:#333
    subgraph xfun_ai[xfun/ai]
        xfun_ai___init__(__init__)
        xfun_ai_agent(agent)
        xfun_ai_prompts(prompts)
        xfun_ai_schema(schema)
        xfun_ai_tools(tools)
    end
    style xfun_ai fill:#e8daef,stroke:#333,stroke-width:1px,color:#333
    subgraph xfun_core[xfun/core]
        xfun_core___init__(__init__)
        xfun_core_db(db)
        xfun_core_errors(errors)
        xfun_core_extras(extras)
        xfun_core_filter(filter)
        xfun_core_notebook(notebook)
        xfun_core_ops(ops)
        xfun_core_view(view)
    end
    style xfun_core fill:#d4f0c0,stroke:#333,stroke-width:1px,color:#333
    subgraph xfun_notebooks[xfun/notebooks]
        xfun_notebooks___init__(__init__)
        xfun_notebooks_accumulation(accumulation)
        xfun_notebooks_aimemory(aimemory)
        xfun_notebooks_diary(diary)
        xfun_notebooks_ledger(ledger)
        xfun_notebooks_plan(plan)
        xfun_notebooks_schedule(schedule)
        xfun_notebooks_timeline(timeline)
        xfun_notebooks_word(word)
    end
    style xfun_notebooks fill:#e8f4fd,stroke:#333,stroke-width:1px,color:#333
    subgraph xfun_utils[xfun/utils]
        xfun_utils___init__(__init__)
        xfun_utils_file_utils(file_utils)
        xfun_utils_time_utils(time_utils)
        xfun_utils_token_utils(token_utils)
    end
    style xfun_utils fill:#ffe0f0,stroke:#333,stroke-width:1px,color:#333
    backend_deps --> xfun___init__
    backend_deps --> xfun_config
    backend_deps --> xfun_core___init__
    backend_deps --> xfun_core_db
    backend_deps --> xfun_core_filter
    backend_deps --> xfun_core_ops
    backend_deps --> xfun_core_view
    backend_deps --> xfun_utils_file_utils
    backend_deps --> xfun_utils_time_utils
    backend_main --> backend_routers___init__
    backend_main --> backend_routers_ai
    backend_main --> backend_routers_manage_db
    backend_main --> backend_routers_manage_filter
    backend_main --> backend_routers_manage_permission
    backend_main --> backend_routers_manage_token
    backend_main --> backend_routers_manage_view
    backend_main --> backend_routers_notebooks
    backend_main --> xfun_config
    backend_main --> xfun_core_errors
    backend_routers_ai --> backend_deps
    backend_routers_ai --> backend_services___init__
    backend_routers_ai --> backend_services_ai_service
    backend_routers_ai --> xfun_core_view
    backend_routers_manage_db --> backend_deps
    backend_routers_manage_db --> backend_services___init__
    backend_routers_manage_db --> backend_services_management_service
    backend_routers_manage_db --> xfun_config
    backend_routers_manage_filter --> backend_deps
    backend_routers_manage_filter --> xfun_core___init__
    backend_routers_manage_filter --> xfun_core_filter
    backend_routers_manage_filter --> xfun_core_ops
    backend_routers_manage_permission --> backend_deps
    backend_routers_manage_permission --> xfun_core___init__
    backend_routers_manage_permission --> xfun_core_filter
    backend_routers_manage_permission --> xfun_core_ops
    backend_routers_manage_permission --> xfun_core_view
    backend_routers_manage_token --> backend_deps
    backend_routers_manage_token --> xfun___init__
    backend_routers_manage_token --> xfun_config
    backend_routers_manage_token --> xfun_core___init__
    backend_routers_manage_token --> xfun_core_db
    backend_routers_manage_token --> xfun_core_filter
    backend_routers_manage_token --> xfun_core_ops
    backend_routers_manage_token --> xfun_core_view
    backend_routers_manage_token --> xfun_utils_file_utils
    backend_routers_manage_token --> xfun_utils_time_utils
    backend_routers_manage_view --> backend_deps
    backend_routers_manage_view --> xfun_core___init__
    backend_routers_manage_view --> xfun_core_filter
    backend_routers_manage_view --> xfun_core_ops
    backend_routers_manage_view --> xfun_core_view
    backend_routers_notebooks --> backend_deps
    backend_routers_notebooks --> backend_schemas
    backend_routers_notebooks --> backend_services___init__
    backend_routers_notebooks --> backend_services_notebook_service
    backend_routers_notebooks --> xfun_ai_schema
    backend_services_ai_service --> xfun_ai_agent
    backend_services_ai_service --> xfun_ai_prompts
    backend_services_ai_service --> xfun_ai_tools
    backend_services_ai_service --> xfun_core_view
    backend_services_management_service --> xfun___init__
    backend_services_management_service --> xfun_core_db
    backend_services_notebook_service --> xfun___init__
    backend_services_notebook_service --> xfun_core___init__
    backend_services_notebook_service --> xfun_core_db
    backend_services_notebook_service --> xfun_core_filter
    backend_services_notebook_service --> xfun_core_ops
    backend_services_notebook_service --> xfun_core_view
    cli --> xfun___init__
    cli --> xfun_ai_agent
    cli --> xfun_ai_prompts
    cli --> xfun_ai_tools
    cli --> xfun_core_db
    cli --> xfun_core_filter
    cli --> xfun_core_ops
    cli --> xfun_core_view
    cli --> xfun_system_tables
    cli --> xfun_utils_file_utils
    tests_backend_conftest --> backend_deps
    tests_backend_conftest --> backend_main
    tests_backend_conftest --> backend_routers___init__
    tests_backend_conftest --> backend_routers_manage_db
    tests_backend_conftest --> xfun___init__
    tests_backend_conftest --> xfun_core___init__
    tests_backend_conftest --> xfun_core_db
    tests_backend_conftest --> xfun_core_filter
    tests_backend_conftest --> xfun_core_ops
    tests_backend_conftest --> xfun_core_view
    tests_backend_conftest --> xfun_utils_time_utils
    tests_backend_conftest --> xfun_utils_token_utils
    tests_backend_test_ai --> backend_services_ai_service
    tests_backend_test_ai --> xfun___init__
    tests_backend_test_ai --> xfun_core_view
    tests_backend_test_ai --> xfun_utils_time_utils
    tests_backend_test_deps --> backend___init__
    tests_backend_test_deps --> backend_deps
    tests_backend_test_deps --> xfun_utils_time_utils
    tests_backend_test_main --> backend_main
    tests_backend_test_notebooks --> backend_services_notebook_service
    tests_backend_test_tokens --> backend_deps
    tests_backend_test_tokens --> backend_routers_manage_token
    tests_backend_test_tokens --> xfun___init__
    tests_backend_test_tokens --> xfun_core___init__
    tests_backend_test_tokens --> xfun_core_filter
    tests_backend_test_tokens --> xfun_core_ops
    tests_backend_test_tokens --> xfun_core_view
    tests_backend_test_tokens --> xfun_utils_time_utils
    tests_backend_test_tokens --> xfun_utils_token_utils
    tests_xfun_conftest --> xfun_core_db
    tests_xfun_conftest --> xfun_core_notebook
    tests_xfun_conftest --> xfun_notebooks_accumulation
    tests_xfun_conftest --> xfun_notebooks_aimemory
    tests_xfun_conftest --> xfun_notebooks_diary
    tests_xfun_conftest --> xfun_notebooks_plan
    tests_xfun_conftest --> xfun_notebooks_schedule
    tests_xfun_conftest --> xfun_notebooks_timeline
    tests_xfun_conftest --> xfun_notebooks_word
    tests_xfun_test_accumulation --> xfun_core_filter
    tests_xfun_test_ai_agent --> xfun_ai_agent
    tests_xfun_test_ai_prompts --> xfun_ai___init__
    tests_xfun_test_ai_prompts --> xfun_ai_prompts
    tests_xfun_test_ai_prompts --> xfun_core_errors
    tests_xfun_test_ai_schema --> xfun_ai_schema
    tests_xfun_test_ai_schema --> xfun_core_errors
    tests_xfun_test_ai_tools --> xfun___init__
    tests_xfun_test_ai_tools --> xfun_ai_schema
    tests_xfun_test_ai_tools --> xfun_ai_tools
    tests_xfun_test_ai_tools --> xfun_core___init__
    tests_xfun_test_ai_tools --> xfun_core_db
    tests_xfun_test_ai_tools --> xfun_core_errors
    tests_xfun_test_ai_tools --> xfun_core_filter
    tests_xfun_test_ai_tools --> xfun_core_ops
    tests_xfun_test_ai_tools --> xfun_core_view
    tests_xfun_test_aimemory --> xfun_core_filter
    tests_xfun_test_db --> xfun_core_db
    tests_xfun_test_db --> xfun_core_errors
    tests_xfun_test_diary --> xfun_core_filter
    tests_xfun_test_extras --> xfun_core_filter
    tests_xfun_test_filter --> xfun_core_errors
    tests_xfun_test_filter --> xfun_core_filter
    tests_xfun_test_notebook --> xfun_core_db
    tests_xfun_test_notebook --> xfun_core_errors
    tests_xfun_test_notebook --> xfun_core_filter
    tests_xfun_test_notebook --> xfun_core_notebook
    tests_xfun_test_ops --> xfun_core_filter
    tests_xfun_test_ops --> xfun_core_ops
    tests_xfun_test_ops --> xfun_core_view
    tests_xfun_test_plan --> xfun_core_filter
    tests_xfun_test_plan --> xfun_notebooks_plan
    tests_xfun_test_registry --> xfun___init__
    tests_xfun_test_registry --> xfun_config
    tests_xfun_test_registry --> xfun_utils_time_utils
    tests_xfun_test_schedule --> xfun_core_filter
    tests_xfun_test_time_utils --> xfun_utils_time_utils
    tests_xfun_test_timeline --> xfun_core_filter
    tests_xfun_test_token --> xfun___init__
    tests_xfun_test_token --> xfun_utils_token_utils
    tests_xfun_test_view --> xfun_core_filter
    tests_xfun_test_view --> xfun_core_view
    tests_xfun_test_word --> xfun_core_filter
    xfun___init__ --> xfun_core_db
    xfun___init__ --> xfun_core_notebook
    xfun___init__ --> xfun_notebooks_accumulation
    xfun___init__ --> xfun_notebooks_aimemory
    xfun___init__ --> xfun_notebooks_diary
    xfun___init__ --> xfun_notebooks_ledger
    xfun___init__ --> xfun_notebooks_plan
    xfun___init__ --> xfun_notebooks_schedule
    xfun___init__ --> xfun_notebooks_timeline
    xfun___init__ --> xfun_notebooks_word
    xfun___init__ --> xfun_system_tables
    xfun_ai_agent --> xfun_config
    xfun_ai_agent --> xfun_core_errors
    xfun_ai_prompts --> xfun___init__
    xfun_ai_prompts --> xfun_core_db
    xfun_ai_prompts --> xfun_core_errors
    xfun_ai_prompts --> xfun_core_notebook
    xfun_ai_schema --> xfun_core_errors
    xfun_ai_schema --> xfun_core_filter
    xfun_ai_tools --> xfun___init__
    xfun_ai_tools --> xfun_ai_schema
    xfun_ai_tools --> xfun_core___init__
    xfun_ai_tools --> xfun_core_db
    xfun_ai_tools --> xfun_core_errors
    xfun_ai_tools --> xfun_core_filter
    xfun_ai_tools --> xfun_core_ops
    xfun_ai_tools --> xfun_core_view
    xfun_core_db --> xfun_core_errors
    xfun_core_db --> xfun_core_filter
    xfun_core_db --> xfun_utils_time_utils
    xfun_core_errors --> xfun_core_filter
    xfun_core_extras --> xfun_core_filter
    xfun_core_filter --> xfun_core_db
    xfun_core_filter --> xfun_core_errors
    xfun_core_filter --> xfun_core_extras
    xfun_core_filter --> xfun_core_filter
    xfun_core_notebook --> xfun_core_db
    xfun_core_notebook --> xfun_core_errors
    xfun_core_ops --> xfun_core_db
    xfun_core_ops --> xfun_core_filter
    xfun_core_ops --> xfun_core_view
    xfun_core_view --> xfun_core_db
    xfun_core_view --> xfun_core_errors
    xfun_core_view --> xfun_core_filter
    xfun_notebooks_accumulation --> xfun_core_db
    xfun_notebooks_accumulation --> xfun_core_notebook
    xfun_notebooks_aimemory --> xfun_core_db
    xfun_notebooks_aimemory --> xfun_core_notebook
    xfun_notebooks_diary --> xfun_core_db
    xfun_notebooks_diary --> xfun_core_errors
    xfun_notebooks_diary --> xfun_core_notebook
    xfun_notebooks_diary --> xfun_utils_time_utils
    xfun_notebooks_ledger --> xfun_core_db
    xfun_notebooks_ledger --> xfun_core_errors
    xfun_notebooks_ledger --> xfun_core_notebook
    xfun_notebooks_ledger --> xfun_utils_time_utils
    xfun_notebooks_plan --> xfun_core_db
    xfun_notebooks_plan --> xfun_core_errors
    xfun_notebooks_plan --> xfun_core_notebook
    xfun_notebooks_plan --> xfun_utils_time_utils
    xfun_notebooks_schedule --> xfun_core_db
    xfun_notebooks_schedule --> xfun_core_errors
    xfun_notebooks_schedule --> xfun_core_notebook
    xfun_notebooks_schedule --> xfun_utils_time_utils
    xfun_notebooks_timeline --> xfun_core_db
    xfun_notebooks_timeline --> xfun_core_errors
    xfun_notebooks_timeline --> xfun_core_notebook
    xfun_notebooks_timeline --> xfun_utils_time_utils
    xfun_notebooks_word --> xfun_core_db
    xfun_notebooks_word --> xfun_core_errors
    xfun_notebooks_word --> xfun_core_notebook
    xfun_notebooks_word --> xfun_utils_time_utils
    xfun_system_tables --> xfun_core_db
    xfun_system_tables --> xfun_core_errors
    xfun_system_tables --> xfun_core_filter
    xfun_system_tables --> xfun_core_view
    xfun_system_tables --> xfun_utils_time_utils
    xfun_system_tables --> xfun_utils_token_utils
    xfun_utils_file_utils --> xfun_config
    xfun_utils_file_utils --> xfun_core_errors
```
<!-- end dependence graph -->

---

## 使用指南

### API 文档

FastAPI 后端运行后访问 `http://localhost:8000/docs` 查看自动生成的 Swagger UI。

**路由概览**：

| 方法 | 路径 |
|------|------|
| GET | `/api/v0/notebooks` |
| GET | `/api/v0/notebooks/{name}/schema` |
| GET | `/api/v0/notebooks/{name}/entries?view=...` |
| POST | `/api/v0/notebooks/{name}/entries` |
| PUT | `/api/v0/notebooks/{name}/entries` |
| DELETE | `/api/v0/notebooks/{name}/entries` |
| POST | `/api/v0/ai/chat` |
| GET | `/api/v0/ai/permission` |
| GET/PUT/DELETE | `/api/v0/filters/{name}` |
| GET/POST/PUT/DELETE | `/api/v0/tokens[/{id}]` |
| GET/POST/PUT/DELETE | `/api/v0/permissions[/{id}]` |
| GET/PUT/DELETE | `/api/v0/views/{name}` |
| POST | `/api/v0/db/{init\|backup\|restore\|reset}` |
| GET | `/api/v0/db/backups` |
| GET | `/api/v0/tokens/info` |
| POST | `/api/v0/tokens/exchange` |

### CLI 命令行

基于 Typer 的完整 CLI，所有命令参数为 JSON 格式，输出统一为 JSON。

| 命令 | 说明 |
|------|------|
| `xfun list [--all]` | 列出笔记本名称 |
| `xfun schema TABLE` | 查看表字段结构 |
| `xfun query TABLE VIEW_JSON [--order-by] [--limit] [--offset]` | 通用查询 |
| `xfun add TABLE ENTRIES_JSON` | 通用添加 |
| `xfun update TABLE FILTER_JSON VALUES_JSON` | 通用更新 |
| `xfun delete TABLE FILTER_JSON` | 通用删除 |
| `xfun ai sync --messages JSON` | AI 同步模式（stdout JSON） |
| `xfun ai chat` | AI 交互模式（stderr 流式，stdout JSON） |
| `xfun view full` / `xfun view no` | 输出 full_view / no_view 定义 |
| `xfun init` | 初始化数据库 |
| `xfun backup` | 在线热备份数据库 |
| `xfun restore BACKUP_PATH [--list] [--no-backup]` | 从备份文件恢复（--list 列出备份，--no-backup 恢复前不备份） |
| `xfun reset [--no-backup]` | 重置数据库（--no-backup 重置前不备份） |

---

## 测试

```bash
# 安装测试依赖后
pytest tests/ -v
# 带覆盖率报告
pytest --cov=xfun --cov-report=term-missing
```

27 个测试文件覆盖以下范围：

| 覆盖范围 | 文件数 | 包含模块 |
|---------|--------|---------|
| 核心引擎 | 7 | db, filter, notebook, ops, view, extras, registry |
| 内置本子 | 7 | 每个内置本子对应一个测试文件 |
| AI 层 | 4 | agent, prompts, schema, tools |
| 工具函数 | 2 | time_utils, token_utils |
| 后端路由 | 7 | ai, db_management, filters, notebooks, permissions, tokens, views |

**测试架构**：分立的 `tests/xfun/conftest.py`（核心引擎测试）和 `tests/backend/conftest.py`（后端路由测试），各管理独立的临时数据库。function 级隔离（每个测试前 `DELETE FROM` 所有表）、`populated_db` 夹具预填样本数据。

---

## FAQ 与关于

### FAQ

**数据库在哪里？**
`data/{XFUN_USER}.db`，默认 `data/default.db`。备份文件在 `data/backups/`。

**如何重置数据库？**
CLI：`xfun reset`（自动备份后重置）。API：`POST /api/v0/db/reset`（需 ROOT_TOKEN）。

**如何创建第一个 API Token？**
在 `.env` 中设置 `ROOT_TOKEN`，启动后端后以 `ROOT_TOKEN` 作为 `Token` 调用 `POST /api/v0/tokens`，或通过前端 `/token-input` 页面输入 ROOT_TOKEN 后创建。

**如何切换用户/数据库？**
设置环境变量 `XFUN_USER=username`，数据库路径变为 `data/username.db`。

**前端报 CORS 错误怎么办？**
确保后端正在运行，前端通过 Vite proxy 转发请求（默认 `http://localhost:8000`）。

**模块导入时自动建库？**
`import xfun` 会自动初始化数据库（建表/补齐列/建索引），无需手动调用 `xfun init`。

**如何手动生成 API Token？**
```bash
echo "sk-$(openssl rand -base64 24 | tr '+/' '-_' | tr -d '=')"
```

### 关于

- **许可证**：Apache 2.0 © 2026 FangJunyi0710
- **作者**：FangJunyi0710（@小_方_）
