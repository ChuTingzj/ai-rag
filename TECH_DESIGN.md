# 技术方案设计：下一代企业知识助手（模块化先进 RAG）

| 字段 | 内容 |
| --- | --- |
| 状态 | Proposed |
| 版本 | 0.4 |
| 日期 | 2026-09-12 |
| 变更 | PGVector；ui-ux-pro-max；uv/pnpm；前端 **Next.js 16.3.5** |
| 对应 PRD | [`PRD.md`](../PRD.md) |
| 对应调研 | [`research.md`](../research.md) |
| 架构路线 | 模块化管道平台 |
| 首期交付 | M1 生产基线；接口预留 M2–M4 |

---

## 1. 设计目标

将 PRD 中的产品能力落到**可本地一键运行、可私有化替换、可分阶段演进**的技术体系：

1. M1 即可演示：上传 + 飞书 Wiki 同步 → Hybrid + Rerank → OpenRouter 带引用问答 + 评测脚本  
2. 核心能力全部接口化：`LLMProvider` / `EmbeddingProvider` / `Connector` / `Retriever` / `Orchestrator`  
3. M2–M4 以**插件式执行器**挂入 Orchestrator，避免推翻 M1 管道  
4. 安全默认：密钥环境变量、审计追加写、ACL 钩子在 M1 预留、M2 强制启用  

---

## 2. 关闭 PRD 开放问题（默认锁定）

| # | PRD 开放问题 | 本方案锁定 | 理由 |
| --- | --- | --- | --- |
| 1 | M1 优先 Wiki | **飞书（Lark）**；Connector 接口同时预留 Notion / Confluence | 中文企业场景优先；飞书开放平台文档成熟 |
| 2 | 向量库与单机基线 | **PostgreSQL 16 + pgvector**（稠密向量）+ **同一库内 tsvector/BM25 词法检索**（元数据/ACL/审计/任务同库） | 单机少依赖、事务一致、私有化简单；Hybrid = pgvector ANN + FTS/BM25 + RRF |
| 3 | 身份 | **M1：本地用户 + JWT**；`AuthProvider` 预留 OIDC | 先跑通；M2 接企业 SSO 不改业务层 |
| 4 | Adaptive 路由 | **M2：规则特征 + 一次 LLM 分类（OpenRouter）**；可降级为纯规则 | 平衡成本与准确；可配置 `ROUTER_MODE=rules\|llm\|hybrid` |
| 5 | 回归门槛 | **M3**：Agent 路径在 golden set 上 answer_faithfulness ≥ M2 single − 0.05；**M4**：关系题子集相对 vector-only 引用命中率 +10% 绝对点 | 实现期用固定 seed 评测集固化 |
| 6 | 前端设计 | 统一 **ui-ux-pro-max**；真相源 `design-system/enterprise-knowledge-assistant/` | Flat + Plus Jakarta Sans + Teal/Orange；Phosphor 图标 |
| 7 | 包管理 | **Python → uv**；**前端 → pnpm** | 全仓库强制，禁止 pip/poetry/npm/yarn 作为主路径 |
| 8 | 前端框架 | **Next.js `16.3.5`**（App Router）+ TypeScript | 精确钉死版本；pnpm 管理；UI 走 design-system；业务 API 仍由 FastAPI 提供 |

**单机资源基线（开发）**：8GB RAM / 4 CPU；Postgres(pgvector) + Redis + API + Worker + Web；首次下载 bge-m3 + reranker 约 2–4GB 磁盘。

---

## 3. 技术栈

### 3.0 包管理（强制）

| 侧 | 工具 | 规范 |
| --- | --- | --- |
| Python（根 monorepo / `packages/*` / `apps/api`） | **[uv](https://github.com/astral-sh/uv)** | 用 `pyproject.toml` + `uv.lock`；工作区可用 uv workspace；安装 `uv sync`；运行 `uv run …`；新增依赖 `uv add`；**禁止**以 `pip install` / Poetry / conda 作为项目主流程 |
| 前端（`apps/web`） | **[pnpm](https://pnpm.io)** | `package.json` + `pnpm-lock.yaml`；安装 `pnpm install`；脚本 `pnpm <script>`；新增依赖 `pnpm add`；**禁止** npm / yarn 作为主流程 |
| Docker | 同上 | 镜像构建阶段：Python 用 `uv sync --frozen`；前端用 `pnpm install --frozen-lockfile` + `pnpm build` |

**提交物必须包含：** `uv.lock`、`pnpm-lock.yaml`（有前端时）。

### 3.1 总览

| 层 | 选型 | 备注 |
| --- | --- | --- |
| 包管理 | **uv**（Python）+ **pnpm**（前端） | 见 §3.0 |
| 语言 | Python 3.12（`requires-python` 由 uv/pyproject 锁定） | RAG/嵌入生态成熟 |
| API | FastAPI + Pydantic v2 | OpenAPI 自动生成 |
| 异步任务 | arq + Redis | 索引/同步/构图 |
| 元数据 + 向量 DB | **PostgreSQL 16 + pgvector**（镜像 `pgvector/pgvector:pg16`）+ SQLAlchemy 2 + Alembic | 单库承载元数据与向量 |
| 词法检索 | `tsvector` + GIN（中文可用分词预处理）；必要时旁路 `bm25s` | 与 dense 经 RRF 融合 |
| LLM | OpenRouter（OpenAI 兼容 HTTP） | 唯一生成出口 |
| Embedding | `BAAI/bge-m3` via `sentence-transformers` | 默认真值本地；可换 OpenRouter embeddings |
| Rerank | `BAAI/bge-reranker-v2-m3` 本地 Cross-Encoder | 可配置关闭以加速 Demo |
| 解析 | pymupdf / python-docx / 纯文本 | M1；表格增强后续 |
| 切块 | 自研 semantic + parent-child | 不绑死 LangChain 核心路径 |
| 前端 | **Next.js 16.3.5** + TypeScript + **ui-ux-pro-max** | App Router；`@phosphor-icons/react`；pnpm；CSS 变量来自 MASTER |
| 部署 | Docker Compose | api / worker / web / **postgres(pgvector)** / redis |
| 观测 | structlog + 可选 OpenTelemetry | QueryTrace 落库 |
| 评测 | 自研脚本 + ragas 指标可选依赖 | M1 最小对比脚本 |

### 3.2 明确不采用（M1）

- 不以 LangChain/LlamaIndex 作为核心运行时（避免黑盒与升级地狱）；可参考其算法，自研薄编排  
- 不以多租户 SaaS 中间件为默认  
- Graph 不用一上来上 Neo4j；M4 默认 **Postgres 存边 + 内存/磁盘 NetworkX 或 Graphology 算法**；规模不够再换 Neo4j  
- **不以 pip/Poetry/npm/yarn 管理本仓库依赖**（统一 uv / pnpm）  
- **不以 Vite SPA 作为前端骨架**（统一 Next.js 16.3.5 App Router）  
- M1 不以 Next.js Route Handlers 替代 FastAPI 核心 RAG API（BFF 仅可做薄代理，可选）  

---

## 4. 逻辑架构

```
                    ┌──────────── Web (Next.js 16.3.5) ────────────┐
                    │  Chat · KB Admin · Jobs · Eval · Audit         │
                    └───────────────┬───────────────────────────────┘
                                    │ /api/v1 rewrite → Nest Gateway
                    ┌───────────────▼─────────────────────┐
                    │     Gateway (NestJS :8080)           │
                    │  CORS · JWT · routing · request-id   │
                    └───┬─────────────┬─────────────┬─────┘
                        │             │             │
              ┌─────────▼──┐  ┌───────▼──────┐  ┌──▼──────────┐
              │ Auth Nest  │  │ Connectors   │  │ RAG FastAPI │
              │ register   │  │ Feishu bind  │  │ KB Docs     │
              │ login /me  │  │ sync trigger │  │ Query Jobs  │
              └─────┬──────┘  └──────┬───────┘  └──┬──────────┘
                    │                │             │
                    └────────┬───────┴─────────────┘
                             │
              ┌──────────────▼──────────────────────┐
              │ PostgreSQL 16 + pgvector             │
              │ users, kb, docs, chunks, connectors  │
              └─────────────────────────────────────┘

Worker (arq): parse → chunk → embed → UPSERT chunks(+vector,+tsv)
              feishu sync → ingest
```

### 4.1 运行时进程

| 进程 | 职责 |
| --- | --- |
| `gateway` | 对外 HTTP 入口：CORS、JWT 校验、按路径转发、request-id |
| `auth` | 注册 / 登录 / `GET /me`、签发 JWT、`users` 表 |
| `connectors` | 飞书 connector 绑定与 sync 触发；enqueue 走 RAG internal API |
| `api` | RAG HTTP：KB/Docs/Jobs/Query；`/internal/v1/enqueue/*` |
| `worker` | 异步：解析、嵌入、PGVector 写入、Wiki 同步、重建 |
| `web` | Next.js 16.3.5（standalone）；严格遵循 design-system |
| `postgres`（pgvector） / `redis` | 基础设施 |

Identity：Gateway 校验 Bearer JWT 后向下游转发 `X-User-Id` + `X-Internal-Token`；下游不直接信任客户端 JWT。

---

## 5. 仓库与模块结构

```
ai-rag/
├── PRD.md
├── research.md
├── TECH_DESIGN.md                 # 本文
├── design-system/enterprise-knowledge-assistant/  # ui-ux-pro-max
│   ├── MASTER.md
│   └── pages/{login,chat,knowledge-base}.md
├── docker-compose.yml
├── .env.example
├── pyproject.toml                 # uv workspace root
├── uv.lock
├── apps/
│   ├── gateway/                   # NestJS API gateway (:8080)
│   ├── auth/                      # NestJS auth microservice (:8081)
│   ├── connectors/                # NestJS connectors microservice (:8082)
│   ├── api/                       # FastAPI RAG-only (:8000)
│   │   └── app/
│   │       ├── main.py
│   │       ├── api/               # KB, docs, jobs, query + internal enqueue
│   │       ├── core/              # config, gateway principal deps
│   │       └── workers/           # arq ingest/sync
│   └── web/                       # Next.js 16.3.5（pnpm + App Router + design-system）
│       ├── package.json           # "next": "16.3.5"
│       ├── app/                   # App Router routes
│       ├── components/
│       └── styles/tokens.css
├── packages/
│   ├── nest-common/               # JWT + internal-token helpers
│   └── rag/                       # 可独立测试的领域库
│       ├── providers/             # llm, embedding, rerank
│       ├── connectors/            # upload, feishu, (notion, confluence stubs)
│       ├── ingest/                # parse, chunk, contextual, index_jobs
│       ├── retrieve/              # hybrid (pgvector+fts), rrf, rerank, pack
│       ├── generate/              # prompts, cite, refuse
│       ├── orchestrator/          # routes, budgets, degrade
│       ├── acl/                   # policy engine (M2)
│       ├── agent/                 # M3
│       ├── graph/                 # M4
│       ├── eval/                  # harness
│       └── domain/                # pydantic models / protocols
├── migrations/                    # Alembic（含 vector extension）
├── tests/
├── evals/                         # golden sets + scripts
└── docs/superpowers/
```

**边界原则**：`packages/rag` 不依赖 FastAPI；API 只做适配。便于单测与私有化嵌入。

---

## 6. 核心接口（Protocol）

```python
# packages/rag/domain/protocols.py

class LLMProvider(Protocol):
    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResult: ...

class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...
    @property
    def dim(self) -> int: ...

class RerankProvider(Protocol):
    async def rerank(
        self, query: str, documents: list[str], top_n: int
    ) -> list[RerankHit]: ...

class Connector(Protocol):
    id: str  # "upload" | "feishu" | ...
    async def list_changes(self, cursor: str | None) -> ChangePage: ...
    async def fetch_document(self, external_id: str) -> RawDocument: ...

class Retriever(Protocol):
    async def retrieve(
        self, query: QueryContext, *, top_k: int
    ) -> list[Evidence]: ...

class Orchestrator(Protocol):
    async def run(self, request: QueryRequest) -> QueryResponse: ...
```

### 6.1 OpenRouter LLM

- Base URL: `https://openrouter.ai/api/v1`  
- 使用官方 OpenAI-compatible `chat/completions`  
- Header：`Authorization: Bearer $OPENROUTER_API_KEY`，可选 `HTTP-Referer` / `X-Title`  
- 配置项：`OPENROUTER_MODEL`（如 `openai/gpt-4.1-mini`）、超时、最大重试 2  

### 6.2 Embedding Provider 注册表

| name | 实现 | 默认 |
| --- | --- | --- |
| `local_bge_m3` | sentence-transformers | **是** |
| `openrouter` | OpenRouter embeddings API | 否 |

`EMBEDDING_PROVIDER=local_bge_m3`

---

## 7. 数据设计

### 7.1 PostgreSQL 主要表

```sql
-- 简化逻辑 DDL（实现以 Alembic 为准）

users (
  id UUID PK,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  roles TEXT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ
)

knowledge_bases (
  id UUID PK,
  name TEXT NOT NULL,
  description TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ
)

documents (
  id UUID PK,
  kb_id UUID REFERENCES knowledge_bases(id),
  source TEXT NOT NULL,           -- upload | feishu | ...
  external_id TEXT,              -- wiki page id
  title TEXT,
  uri TEXT,
  mime_type TEXT,
  status TEXT NOT NULL,          -- pending|indexing|ready|failed
  version INT NOT NULL DEFAULT 1,
  checksum TEXT,
  raw_path TEXT,                 -- object storage / local fs
  created_at, updated_at TIMESTAMPTZ,
  UNIQUE(kb_id, source, external_id)
)

chunks (
  id UUID PK,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  kb_id UUID NOT NULL,            -- 冗余便于按库过滤/建索引
  parent_chunk_id UUID NULL,
  ordinal INT NOT NULL,
  text TEXT NOT NULL,
  context_prefix TEXT,           -- M2 contextual
  token_count INT,
  embedding VECTOR(EMBEDDING_DIM) NOT NULL,  -- pgvector；DIM 来自配置（bge-m3 实测写入）
  tsv TSVECTOR,                  -- 词法检索；中文经分词后再 to_tsvector('simple', ...)
  meta JSONB                     -- title, uri, acl_version 等
)
-- INDEX: HNSW on embedding (vector_cosine_ops)
-- INDEX: GIN on tsv
-- INDEX: (kb_id) for tenant/kb scoping

index_jobs (
  id UUID PK,
  kb_id UUID,
  document_id UUID NULL,
  job_type TEXT,                 -- ingest|sync|rebuild|graph_build
  state TEXT,                    -- queued|running|success|failed
  error TEXT,
  stats JSONB,
  created_at, started_at, finished_at
)

connectors (
  id UUID PK,
  kb_id UUID,
  type TEXT,                     -- feishu
  config_encrypted BYTEA,        -- token 等
  cursor TEXT,
  enabled BOOL
)

-- M2
acl_policies (
  id UUID PK,
  principal_type TEXT,           -- user|role
  principal_id TEXT,
  resource_type TEXT,            -- kb|document
  resource_id UUID,
  action TEXT                    -- read
)

query_traces (
  id UUID PK,
  user_id UUID,
  kb_ids UUID[],
  question TEXT,
  route TEXT,
  answer TEXT,
  evidence_ids UUID[],
  model TEXT,
  steps JSONB,
  latency_ms INT,
  cost_usd NUMERIC,
  created_at TIMESTAMPTZ
)

-- M4
graph_nodes / graph_edges / graph_communities ...
```

### 7.2 PGVector + 词法检索（Hybrid）

- **扩展**：`CREATE EXTENSION IF NOT EXISTS vector;`  
- **稠密列**：`chunks.embedding vector(N)`，`N = EMBEDDING_DIM`（启动时校验与 EmbeddingProvider.dim 一致）  
- **ANN 索引**：`CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)`（小数据可用 IVFFlat，默认 HNSW）  
- **词法列**：`chunks.tsv tsvector` + `GIN(tsv)`；写入前对中文做分词（jieba 等）后 `to_tsvector('simple', tokens)`  
- **检索 SQL 形态（示意）**：

```sql
-- dense: ORDER BY embedding <=> :query_vec LIMIT 50  (cosine distance)
-- lexical: WHERE tsv @@ plainto_tsquery('simple', :q) ORDER BY ts_rank_cd(tsv, ...) LIMIT 50
```

**M1 Hybrid 落地策略（锁定）**：

1. **Dense**：pgvector 余弦距离 Top-50（按 `kb_id` 过滤）  
2. **Lexical**：`tsvector` Top-50；若中文召回不足，同进程 **bm25s** 作为可选第二稀疏源（配置 `LEXICAL_BACKEND=tsv|bm25s|both`）  
3. **RRF**：`k=60`，融合后 Top-100 进 rerank  
4. **Rerank**：Cross-Encoder → Top 6–8 进生成  

按 KB 删除/重建：`DELETE FROM chunks WHERE kb_id = :id`（与元数据同事务，无跨库一致性问题）。

### 7.3 父子切块

- **Child**：~200–400 tokens，用于检索（写入 `embedding` + `tsv`）  
- **Parent**：章节/页级，生成时用 parent 文本（或 child + 左右窗口）  
- 检索命中 child → `ContextPacker` 升级为 parent，去重后打包  

---

## 8. 关键流水线

### 8.1 摄入（Ingest）

```
RawDocument
  → Parser (pdf/docx/md/txt)
  → Normalizer (去噪、标题层级)
  → Chunker (semantic boundaries + parent/child)
  → [M2] ContextualPrefix (LLM 短前缀，可关)
  → EmbeddingProvider.embed_documents
  → UPSERT chunks (embedding + tsv) in PostgreSQL
  → documents.status=ready
```

失败：`status=failed`，`index_jobs.error` 记录，支持重试。

### 8.2 飞书同步（M1）

- 使用飞书开放平台：tenant_access_token + 云文档/知识库 API（具体 scope 写在 `.env.example`）  
- 增量：`connectors.cursor` 保存 `page_token` / `edit_time`  
- Worker 定时或手动触发 `sync_feishu(kb_id)`  
- 每个 page → `RawDocument` → 同一 Ingest 管道  
- 删除：远端消失则软删文档并 `DELETE` 对应 chunks（含向量）  

### 8.3 查询（M1 single 路径）

```
QueryRequest(user, question, kb_ids)
  → (M1) route := single
  → Retriever.hybrid(question)
  → ACL.filter(evidence)          # M1: allow-all if no policies
  → if empty: refuse(NO_EVIDENCE)
  → ContextPacker(parents, max_tokens)
  → Generator(prompt with [E1]..[En], force citations)
  → validate citations ⊆ evidence_ids
  → QueryTrace persist (M1 可写精简 trace)
  → QueryResponse(answer, citations[], route, trace_id)
```

### 8.4 生成与引用协议

Prompt 约定：

- 证据块标记为 `[E{n}]` + 标题 + 正文  
- 要求模型在句末使用 `[E{n}]`；禁止无引用事实句  
- 后处理：解析引用；若存在无引用段落 → 剥离或整答降级为「资料不足」  
- `refuse_reasons`: `NO_EVIDENCE` | `UNGROUNDED` | `NO_PERMISSION`（M2）  

### 8.5 Orchestrator 路由演进

| route | 阶段 | 行为 |
| --- | --- | --- |
| `none` | M2+ | 不检索，仅通用闲聊或拒答（可关） |
| `single` | M1 | 一次 Hybrid+Rerank+生成 |
| `multi` | M2 | 查询改写/分解 2–3 次检索再融合 |
| `agent` | M3 | 规划循环，工具：retrieve / list_docs / get_chunk |
| `graph` | M4 | 图检索 + 向量补充 |

降级链：`agent|graph` → `multi|single` → `refuse`。

---

## 9. API 设计（M1 为主）

Base: `/api/v1`  
Auth: `Authorization: Bearer <jwt>`

| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/auth/register` | 本地注册（可关） |
| POST | `/auth/login` | 返回 JWT |
| GET | `/me` | 当前用户 |
| GET/POST | `/knowledge-bases` | 列表/创建 |
| GET/PATCH/DELETE | `/knowledge-bases/{id}` | |
| POST | `/knowledge-bases/{id}/documents` | multipart 上传 |
| GET | `/knowledge-bases/{id}/documents` | |
| POST | `/knowledge-bases/{id}/connectors/feishu` | 绑定飞书 |
| POST | `/knowledge-bases/{id}/sync` | 触发同步 |
| POST | `/knowledge-bases/{id}/rebuild` | 重建索引 |
| GET | `/jobs/{id}` | 任务状态 |
| POST | `/query` | 问答 |
| GET | `/query/traces/{id}` | 轨迹 |
| POST | `/eval/run` | 触发评测（admin） |

### 9.1 `POST /query` 请求/响应

```json
// request
{
  "question": "差旅报销上限是多少？",
  "kb_ids": ["uuid"],
  "route_hint": null
}

// response
{
  "answer": "根据差旅制度，国内机票经济舱限额为…[E1]",
  "citations": [
    {
      "evidence_id": "chunk-uuid",
      "document_id": "doc-uuid",
      "title": "差旅报销制度",
      "uri": "/files/...",
      "snippet": "...",
      "score": 0.82
    }
  ],
  "route": "single",
  "refuse_reason": null,
  "trace_id": "uuid"
}
```

---

## 10. 前端设计（强制 ui-ux-pro-max）

### 10.1 设计真相源

| 路径 | 作用 |
| --- | --- |
| [`design-system/enterprise-knowledge-assistant/MASTER.md`](./design-system/enterprise-knowledge-assistant/MASTER.md) | 全局色板、字体、间距、组件规范 |
| `design-system/.../pages/login.md` | 登录页覆盖 |
| `design-system/.../pages/chat.md` | 问答页覆盖 |
| `design-system/.../pages/knowledge-base.md` | 知识库管理覆盖 |

**实现约定**：任意前端页面开发前，先读 MASTER，再读对应 `pages/*.md`（有则覆盖）。禁止另起一套色板/字体。

### 10.2 视觉与交互锁定

| 项 | 决策 |
| --- | --- |
| 风格 | Flat Design（少阴影、清晰边框分层；卡片用 border 而非重阴影） |
| 主色 | Teal `#0D9488`；CTA Accent `#EA580C` |
| 字体 | **Plus Jakarta Sans**（标题/正文） |
| 图标 | **Phosphor** `@phosphor-icons/react`（`regular` weight）；禁止 emoji 作图标 |
| 动效 | 150–200ms ease；列表 stagger 可用；表格禁用 back.out 过冲；尊重 `prefers-reduced-motion` |
| 无障碍 | 正文对比度 ≥4.5:1；可见 focus ring（`--color-ring`）；表单必须有 label；异步操作 `aria-busy` + skeleton |

### 10.3 信息架构与页面

| 路由 | design-system 规范 | Next.js 实现 | 功能 |
| --- | --- | --- | --- |
| `/login` | `pages/login.md` | `app/login/page.tsx` | 登录；提交反馈 Loading→Success/Error |
| `/` | `pages/chat.md` | `app/page.tsx` | 问答：选 KB、回答区、引用侧栏；skeleton |
| `/kbs` `/kbs/[id]` | `pages/knowledge-base.md` | `app/kbs/...` | 知识库/文档/上传/飞书同步/任务 |
| `/jobs` | MASTER | `app/jobs/page.tsx` | 全局任务 |
| `/eval` | MASTER | `app/eval/page.tsx` | 评测简表 |
| `/audit` | MASTER（M2） | `app/audit/page.tsx` | 审计 |

路由使用 **Next.js App Router**；动态段用 `[id]`。

### 10.4 前端工程

- **框架：Next.js `16.3.5`（精确版本钉死）+ TypeScript + App Router**  
- **包管理：仅 pnpm**（`pnpm install` / `pnpm dev` / `pnpm build`）  
- 与后端：浏览器经 `NEXT_PUBLIC_API_BASE_URL` 调用 FastAPI；本地可用 `rewrites` 代理 `/api/*` → FastAPI（可选）  
- 部署：推荐 `output: 'standalone'` 便于 Docker  
- CSS：全局 CSS variables 映射 MASTER token（`--color-*` / `--space-*`）  
- 组件：自研薄组件（Button/Input/Table/Skeleton），不引入与色板冲突的默认主题包  
- React 规范：props/事件类型完整；不做无依据的全面 `memo`；遵守 React 19 / Next 16 安全基线  
- RSC：默认 Server Components；交互页（Chat/上传）使用 Client Components  

M1 UI 目标：完成 F1/F2 演示，且**视觉上已是统一设计系统**，而非「能用就行」的无样式页面。

---

## 11. 安全设计

| 项 | M1 | M2+ |
| --- | --- | --- |
| 密钥 | `.env`；不进 git；不进日志 | KMS/密封配置可选 |
| 传输 | 本地 HTTP；私有化建议 TLS 终止 | |
| 认证 | JWT（HS256，`JWT_SECRET`） | OIDC |
| ACL | Gateway 接口 + allow-all 实现 | 强制策略 |
| 飞书 token |  Fernet 加密存 `connectors.config_encrypted` | |
| Prompt injection | 系统提示隔离用户问题与证据；证据只读 | 加强过滤器 |
| 审计 | 写 `query_traces` | 不可变导出 |

---

## 12. 评测技术方案

### 12.1 M1

目录：`evals/m1/`

- `golden.jsonl`：≥20 条 `{id, question, kb, must_include_doc_ids[], forbidden_doc_ids[]}`  
- 脚本：`uv run python -m rag.eval.run --pipeline naive|hybrid`  
- 指标：  
  - `retrieval_hit_rate`：must_include 是否出现在 top_k  
  - `citation_precision`：生成引用 ∈ 检索集  
  - `refuse_on_empty` 手工用例  

### 12.2 M2+

- 增加 faithfulness（LLM-as-judge 或 ragas）  
- 越权套件：`evals/security/acl_leak.jsonl`  

---

## 13. 部署

### 13.1 `docker-compose` 服务

`postgres`（**镜像 `pgvector/pgvector:pg16`**）、`redis`、`api`、`worker`、`web`  
（**不再包含独立 Qdrant 服务**）

### 13.2 关键环境变量

```bash
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4.1-mini
EMBEDDING_PROVIDER=local_bge_m3
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIM=1024
RERANK_MODEL=BAAI/bge-reranker-v2-m3
LEXICAL_BACKEND=tsv
DATABASE_URL=postgresql+asyncpg://rag:rag@postgres:5432/rag
REDIS_URL=redis://redis:6379
JWT_SECRET=
FEISHU_APP_ID=
FEISHU_APP_SECRET=
DATA_DIR=/data
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 13.3 私有化替换点

| 组件 | 替换方式 |
| --- | --- |
| OpenRouter | 实现 `LLMProvider` 指向内网 vLLM / 其他网关 |
| Embedding | 换 Provider 名 |
| PGVector | 升级 Postgres 规格；超大规模时可再引入专用向量引擎（经 `VectorStore` Protocol） |
| 飞书 | 新 Connector |
| Auth | OIDC AuthProvider |

---

## 14. M2–M4 技术演进（摘要）

### M2 Adaptive + ACL + Contextual + Audit

- `acl.filter(user, evidences)` 在 pack 前强制执行  
- Router：特征（疑问词、多实体、对比词）+ 可选 LLM JSON 分类  
- Contextual：摄入时对每个 child 调 LLM 生成 ≤100 token 前缀再嵌入（可关，控成本）  
- Audit API + UI  

### M3 Agent

- `AgentRuntime`：ReAct 风格，最大 `max_steps=6`，`max_tokens_budget`  
- Tools：`hybrid_retrieve`, `get_document`, `get_chunk`  
- 每步写入 `query_traces.steps`  
- 超限 → `single` 降级  

### M4 GraphRAG

- 离线：LLM 抽取实体关系 → `graph_nodes/edges` → Leiden/Louvain 社区 → 社区摘要文本再索引  
- 在线：entity linking → 子图扩展 → 与向量结果 RRF  
- Feature flag：`GRAPH_ENABLED=false` 默认  

---

## 15. 测试策略

| 类型 | 范围 |
| --- | --- |
| 单元 | Chunker、RRF、引用解析、ACL 匹配 |
| 合约 | LLMProvider mock、Connector mock |
| 集成 | docker compose：上传 → 索引 → query |
| 安全 | M2 越权套件 CI 必过 |
| 回归 | `evals/` 每里程碑门槛 |

---

## 16. 里程碑技术交付物

| 里程碑 | 技术交付物 |
| --- | --- |
| M1 | Compose 可起；上传+飞书；Hybrid+Rerank；引用问答；评测脚本；本文接口落地 |
| M2 | ACL/Audit/Adaptive/Contextual；越权 CI |
| M3 | AgentRuntime + 预算降级 |
| M4 | Graph build/query + flag |

---

## 17. 风险与技术缓解

| 风险 | 缓解 |
| --- | --- |
| bge-m3 本机过重 | 提供 `EMBEDDING_PROVIDER=openrouter` 旁路；或量化/更小模型配置项 |
| 飞书权限申请慢 | M1 可用「上传」独立验收；飞书作为并行路径 |
| 中文 FTS 召回偏弱 | 启用 `LEXICAL_BACKEND=both`（tsv + bm25s） |
| pgvector 维数不一致 | 启动校验 `EMBEDDING_DIM` 与模型 dim；迁移脚本绑定维度 |
| OpenRouter 延迟 | 超时与模型切换；UI 明确加载态 |
| 引用后处理过严导致拒答过多 | 可配置 `CITATION_STRICTNESS=strict|moderate` |

---

## 18. 文档与实现顺序建议

1. 本文 `TECH_DESIGN.md` 评审锁定  
2. **仅 M1** 编写详细实现计划（任务级）→ 编码  
3. M2/M3/M4 各自独立实现计划（避免一份巨无霸计划）  

对应实现计划路径（M1）：`docs/superpowers/plans/2026-09-12-m1-hybrid-rag.md`
