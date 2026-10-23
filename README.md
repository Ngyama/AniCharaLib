# AniCharaLib — ACG 角色数据库 V1

以虚构角色为中心的 ACG 人物数据库。你可以按外貌、服装、性格、身份等属性组合检索角色，查看角色详情和所属作品。

- 前端：React 19 + TypeScript + Vite 7 + Tailwind CSS 4 + shadcn/ui（Radix）+ TanStack Query + React Router 7
- 后端：Python + FastAPI + SQLAlchemy 2 + Alembic + psycopg 3
- 数据库：PostgreSQL 17（Docker Compose）

V1 全部数据均为虚构的演示数据：28 名角色、9 部作品、330 个属性。所有数据都由仓库里的 Seed 文件生成。没有使用任何真实动漫图片，角色图由前端按角色发色生成占位图。

---

## 快速开始（Windows）

### 1. 安装必要软件（每台电脑一次）

| 软件 | 版本 | 安装（任选其一） |
| --- | --- | --- |
| Git | 任意新版 | <https://git-scm.com/> 或 `winget install Git.Git` |
| Docker Desktop | 带 Compose v2 | <https://www.docker.com/products/docker-desktop/> 或 `winget install Docker.DockerDesktop` |
| Python | 3.11 及以上（安装时勾选 *py launcher*） | <https://www.python.org/downloads/> 或 `winget install Python.Python.3.13` |
| Node.js | 20.19 及以上，推荐 22 LTS | <https://nodejs.org/> 或 `winget install OpenJS.NodeJS.LTS` |

Docker Desktop 首次安装后需要按提示启用 WSL 2，可能需要重启电脑。运行项目命令前请先启动 Docker Desktop。

### 2. Clone 并初始化

在 PowerShell 或 cmd 中执行：

```powershell
git clone https://github.com/Ngyama/AniCharaLib.git
cd AniCharaLib
.\dev.cmd setup
```

`setup` 是一键初始化命令，依次执行：

1. 检查 Python、Node.js、Docker 是否可用；
2. `.env` 不存在时从 `.env.example` 复制一份；
3. `docker compose up -d --wait` 启动 PostgreSQL，并等待健康检查通过；
4. 创建 `backend\.venv`，按 `requirements*.txt`（固定版本）安装后端依赖；
5. 等待数据库就绪，必要时自动建库，执行 `alembic upgrade head`，再从 `backend\data\*.yaml` 导入演示数据；
6. 在 `frontend` 下按 `package-lock.json` 执行 `npm ci`。

`setup` 可以重复执行：依赖没有变化时会跳过安装，迁移和 Seed 本身也是幂等的。所以每次 `git pull` 之后都可以直接再运行一次 `.\dev.cmd setup`。

### 3. 日常开发

开两个终端：

```powershell
.\dev.cmd backend     # 先应用未执行的迁移，再启动 FastAPI（自动重载） http://localhost:8000/docs
.\dev.cmd frontend    # Vite 开发服务器（热更新）             http://localhost:5173
```

Docker 只负责运行 PostgreSQL。前端和后端都在本机直接运行，修改代码后自动热更新，不需要重新构建任何镜像。三者也可以分别启动：数据库用 `.\dev.cmd db`，关掉后端不影响前端热更新。

### 命令一览

| 命令 | 作用 |
| --- | --- |
| `.\dev.cmd setup` | 一键初始化或更新环境（安装依赖、启动数据库、迁移、导入演示数据） |
| `.\dev.cmd db` / `db-stop` | 启动或停止 PostgreSQL 容器（数据保留在 Docker Volume 中） |
| `.\dev.cmd backend` | 执行迁移后启动后端 |
| `.\dev.cmd frontend` | 启动前端 |
| `.\dev.cmd migrate` | 执行未应用的迁移 |
| `.\dev.cmd seed` | 按 YAML 重新同步演示数据 |
| `.\dev.cmd status` | 显示数据库连接和迁移版本，落后时提示执行 migrate |
| `.\dev.cmd migration "说明"` | 修改模型后自动生成迁移文件 |
| `.\dev.cmd test` | 运行后端测试和前端类型检查 |
| `.\dev.cmd reset` | 重建演示数据库（需要输入数据库名确认） |

`dev.cmd` 通过 `-ExecutionPolicy Bypass` 调用 `scripts\dev.ps1`，所以新电脑上不需要修改 PowerShell 执行策略。

---

## 数据库与跨电脑同步

### 什么提交到 Git，什么不提交

| 内容 | 位置 | 是否提交 |
| --- | --- | --- |
| 表结构 | `backend/app/models.py` 和 `backend/alembic/versions/*.py` | 提交 |
| 属性字典与演示数据 | `backend/data/*.yaml` | 提交 |
| 环境变量模板 | `.env.example` | 提交 |
| 本地环境变量和密码 | `.env` | **不提交**（已加入 `.gitignore`） |
| 数据库数据 | Docker Volume `anicharalib_pgdata`（每台电脑各自保存） | **不提交** |
| 依赖目录 | `backend\.venv`、`frontend\node_modules` | **不提交** |

当前阶段没有需要同步的正式数据，任何一台电脑都可以从「迁移 + Seed」完整恢复出同样的数据库。表结构只能由 Alembic 迁移创建，不要手工建表或改表。

### 修改数据库字段的流程

1. 修改 `backend\app\models.py`。
2. `.\dev.cmd migration "add xxx to characters"`：在数据库已是最新版本的前提下，自动生成 `backend\alembic\versions\<日期>_<id>_<说明>.py`。
3. **检查生成的迁移文件**。自动生成并不总是完整的，比如改列名会被识别成「删除 + 新增」，数据迁移也需要手写。
4. `.\dev.cmd migrate` 应用迁移；如果 Seed 文件也要改，再执行 `.\dev.cmd seed`。
5. `.\dev.cmd test`：`tests/test_migrations.py` 会检查模型和迁移是否一致、是否只有一个迁移 head，以及每个迁移能否降级后重新升级。只改模型、忘了写迁移时，测试会失败。
6. 把模型、迁移文件和相关 Seed 修改放在同一个提交里。

在另一台电脑上 `git pull` 之后，执行 `.\dev.cmd setup` 或 `.\dev.cmd migrate` 即可。`.\dev.cmd backend` 启动时也会自动应用未执行的迁移。

注意事项：

- 已经推送的迁移文件不要再修改。需要调整时，新建一个迁移。
- 新建迁移前先 `git pull`。如果两台电脑各自新建了迁移，会出现多个 head，测试会提示。这时执行 `.venv\Scripts\alembic merge heads -m merge`（在 `backend` 目录中）生成合并迁移，并提交。

### 重置开发数据库

```powershell
.\dev.cmd reset            # 删除所有表 → 迁移 → Seed，需要输入数据库名确认
.\dev.cmd reset -Volume    # 删除整个 Docker Volume 并重新创建容器，需要输入 RESET 确认
```

两个重置命令都需要确认后才会执行，并且只允许对本地数据库主机执行。确认输入错误时不会做任何改动。

### 不用 Docker 时

如果本机已经装有 PostgreSQL，可以把 `.env` 中的连接信息改成本机数据库，然后执行 `.\dev.cmd setup -SkipDocker`。数据库不存在时会自动创建。

### 测试数据库

测试会使用 `TEST_DATABASE_URL`（默认是 `<POSTGRES_DB>_test`，不存在时自动创建）。每次运行都会删除并重建它的 schema，所以请不要把它指向需要保留的数据库。

### 不使用脚本的等价命令

```powershell
copy .env.example .env
docker compose up -d --wait db
cd backend
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m app.manage init      # 等待数据库 → 建库 → alembic upgrade head → seed
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
cd ..\frontend
npm ci
npm run dev
```

---

## 目录结构

```
AniCharaLib/
├── dev.cmd                   开发命令入口（调用 scripts\dev.ps1）
├── docker-compose.yml        PostgreSQL（仅绑定 127.0.0.1）
├── .env.example              环境变量模板
├── backend/
│   ├── alembic/versions/     数据库迁移（表结构的唯一来源）
│   ├── app/
│   │   ├── config.py         环境变量配置
│   │   ├── db.py             Engine / Session
│   │   ├── models.py         SQLAlchemy 模型
│   │   ├── schemas.py        Pydantic 响应 Schema（API 契约）
│   │   ├── search.py         角色检索（规则检索，由 PostgreSQL 执行）
│   │   ├── presenters.py     ORM → Schema 转换
│   │   ├── routers/          attributes / characters / works 接口
│   │   ├── seed.py           属性字典与演示数据导入（幂等同步）
│   │   ├── manage.py         wait / init / migrate / status / reset
│   │   └── main.py           FastAPI 应用
│   ├── data/                 attributes.yaml / works.yaml / characters.yaml
│   └── tests/                pytest（使用真实 PostgreSQL）
├── frontend/
│   └── src/
│       ├── api/              API 客户端、类型、React Query hooks
│       ├── components/       布局、角色卡片、属性筛选面板、shadcn/ui 组件
│       ├── hooks/            检索条件 ↔ URL 同步
│       └── pages/            检索 / 角色详情 / 作品列表 / 作品详情 / 属性索引
└── scripts/dev.ps1           Windows 开发任务脚本
```

前端开发服务器会把 `/api` 代理到 `http://localhost:8000`。后端地址不同时，可以设置 `VITE_API_PROXY_TARGET`；前后端分开部署时，可以设置 `VITE_API_BASE_URL`。

---

## 数据库结构

```
attribute_categories ─< attribute_groups ─< attributes ─┐ (parent_id → attributes)
                                                         │
characters ─< character_names                            │
characters ─< character_attributes >──────────────────────┘
characters ─< character_works >─ works
```

| 表 | 说明 |
| --- | --- |
| `characters` | 角色基本资料：`key`（稳定标识）、主要名称、性别、生日（月/日）、年龄（文本）、身高、血型、简介、图片 URL |
| `character_names` | 多语言名称与别名：`language` ∈ zh / ja / en / romaji / other，`name_type` ∈ name / alias；`(character_id, language, name)` 唯一 |
| `works` | 作品：标题、原名、英文名、类型（anime / visual_novel / manga / light_novel / game / novel / other）、年份、简介 |
| `character_works` | 角色 ↔ 作品多对多，带 `role`（main / supporting / minor / cameo）。同一角色出现在原作、改编和联动作品中时，只保留一条角色记录 |
| `attribute_categories` | 一级分类，带 `domain`（appearance / personality / other），决定该分类在角色页中归入「外观 / 性格 / 其他」哪个区块 |
| `attribute_groups` | 二级分类；`featured` 表示该组属性会显示在角色卡片上 |
| `attributes` | 可检索标签：稳定英文 `key`、中 / 日 / 英名称、可选色样 `swatch`、可选父属性、排序 |
| `character_attributes` | 角色拥有的属性，主键 `(character_id, attribute_id)`，另有 `(attribute_id, character_id)` 反向索引 |

索引说明：
- 名称检索使用 `ILIKE '%…%'`，并通过 `pg_trgm` 的 GIN 索引加速（由迁移启用扩展）。
- 属性检索走 `character_attributes` 的两个方向的复合索引。

外观、性格等信息全部以属性行的形式存储，不是 `characters` 表上的固定字段。因此增加分类或标签只需要修改 `attributes.yaml`，不需要修改数据库结构。

## 检索规则

`GET /api/characters?attrs=pink-hair,red-hair,twin-tails,weak-willed&q=…`

- 同一二级分类内的多个属性为 **OR**（粉发 或 红发）。
- 不同二级分类之间为 **AND**（发色 且 发型 且 性格特征）。
- 严格检索：只有已经标注了对应属性的角色才会进入结果。属性缺失不等于「确认不具有」，但同样不算匹配。
- 字典里不存在的属性 key 会放入响应的 `unknown_attributes`，此时结果为空。字典里存在但没有角色标注的属性，结果同样为空，但不会出现在 `unknown_attributes` 里。
- 名称检索覆盖主要名称以及所有语言的名称和别名，不区分大小写；`%` 和 `_` 按字面字符匹配。名称条件与属性条件之间为 AND。
- 父属性（如 猫耳 → 兽耳）只是信息性的层级，检索时不会自动展开到子属性。
- 分页参数：`page`（≥1）、`page_size`（1–100，默认 24）。排序参数 `sort` 可选 `relevance`、`name`、`newest`、`most_tagged`。
- 另有 `gender` 和 `work_id` 两个过滤条件。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/attributes` | 完整属性字典（分类 → 分组 → 属性），含每个属性的角色数 |
| GET | `/api/characters` | 角色列表 / 名称检索 / 属性检索（分页） |
| GET | `/api/characters/{id}` | 角色详情：多语言名称、作品、按分类分组的属性 |
| GET | `/api/works` | 作品列表（`q`、`work_type`、分页） |
| GET | `/api/works/{id}` | 作品详情与登场角色 |
| GET | `/api/health` | 健康检查 |

响应结构见 `backend/app/schemas.py`，前端对应的类型在 `frontend/src/api/types.ts`。

## 维护数据

1. 编辑 `backend/data/attributes.yaml`、`works.yaml` 或 `characters.yaml`。
2. 运行 `python -m app.seed`。

Seed 按 `key` 同步数据：新增的记录会被创建，已有记录会就地更新，文件中删除的记录也会从数据库删除。重复执行的结果不变。导入前会先做校验，未知属性、未知作品、重复 key、非法性别或生日等问题都会报错，并且不写入任何数据。

前端的分类导航、筛选面板、角色页属性区块和属性索引都由 `/api/attributes` 动态生成，新增分类或标签不需要修改前端组件。前端只维护固定枚举的显示文字（性别、作品类型、角色定位、三个属性区块的名称），这些在 `frontend/src/lib/labels.ts`。

## 页面

- **角色检索**（`/`）：姓名搜索、属性筛选面板、已选条件（按分组显示「或 / 且」关系，可单独移除）、性别、排序、结果数、分页。检索条件保存在 URL 中，可以直接分享。
- **属性筛选面板**：左侧是一级分类导航（按外观 / 性格 / 其他分组），右侧是二级分类和标签。支持跨分类搜索属性名（中 / 日 / 英），底部显示已选属性、清空按钮，以及实时的「显示 N 名角色」。
- **角色详情**（`/characters/:id`）：基本资料、多语言名称与别名、外观 / 性格 / 其他属性、所属作品。属性标签可以点击，跳转到对应的检索结果。
- **作品**（`/works`、`/works/:id`）：按类型筛选和标题搜索；作品详情页列出登场角色及其定位。
- **属性索引**（`/attributes`）：整个字典的一览，每个标签都可以点击检索。
- 布局：底层背景加悬浮圆角内容面板（Inset App Shell），支持深色模式和移动端（导航收进抽屉，筛选面板全屏显示）。

## 未完成与已知限制

- 按 V1 范围，以下功能未实现：外部数据导入（Bangumi / VNDB / EGS）、AI、用户系统、社区功能、排行榜、后台管理、版本管理、属性来源与审核。
- 没有真实角色图片，`image_url` 均为空，前端显示生成的占位图。字段已经预留，填入 URL 后会直接显示。
- 作品详情接口一次返回该作品的全部角色，没有分页。V1 的数据量下没有问题，作品角色很多时应改用 `/api/characters?work_id=` 分页获取。
- 前端没有自动化测试，前端的验证方式是类型检查加手动浏览器测试。
- 前端打包产物是单个约 500 kB 的 JS chunk，暂未做路由级代码分割。
- `傲沉` 等少数标签没有可靠的日文和英文对应译名，因此留空。
