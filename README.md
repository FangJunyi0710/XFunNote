# XFunNote — 小方的万用本

> **XFunNote** = e**X**ploratory **Fun**damental **Note**book  
> 探索性万用笔记本，个人效率与 AI 助手的实验场。

---

## 项目简介

XFunNote 是一个个人知识管理与效率工具，核心目标是：

- 整合**计划、日记、学习记录、单词**等碎片信息，统一存储与管理
- 借助 **AI 自动生成日报/周报**，辅助每日复盘与决策
- 作为技术实验场：Python 工程化 + AI Agent + 快速原型开发

**当前阶段**：准大一暑假 MVP 开发中

---

## 技术栈

| 类别         | 选择                                                                    |
| ------------ | ----------------------------------------------------------------------- |
| 语言         | Python 3.10+                                                            |
| 数据库       | SQLite（WAL 模式，读写分离事务）                                        |
| CLI 框架     | Typer                                                                   |
| AI           | OpenAI SDK → DeepSeek API                                               |
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
| **测试覆盖** | ~89 个测试用例，覆盖核心引擎正常路径、边界条件、错误路径及事务回滚 |

### 🗺️ 规划中

- **AI 日报/周报** — `xfun/ai/` 模块待实现，基于 DeepSeek 聚合数据生成复盘报告
- **FastAPI 后端** — `backend/main.py` 待实现，暴露 RESTful API
- **Streamlit 前端** — `frontend/app.py` 待实现，可视化界面
- **视图层** — `xfun/core/view.py` 待实现，格式化输出（Markdown、颜色控制台）
- **工具函数** — `file_utils.py`、`string_utils.py` 待补齐
- **单词复习调度** — 间隔重复算法（SM-2）集成

---

## 配置

### 1. 环境变量

复制项目根目录的 `.env.example` 为 `.env` 并填写配置。

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

各命令的完整用法和示例见 `cli.py` 底部测试语句块。

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
│   │   └── view.py         #     [待实现] 视图格式化
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

Apache 2.0

---

## 作者

@小_方_
