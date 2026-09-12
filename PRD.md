# PRD：下一代企业知识助手（模块化先进 RAG 平台）

| 字段 | 内容 |
| --- | --- |
| 状态 | Draft（PRD 已评审；技术方案见 TECH_DESIGN.md） |
| 版本 | 0.2 |
| 日期 | 2026-09-12 |
| 依据 | [`research.md`](./research.md) 调研结论 |
| 产品形态 | 企业内部知识助手 |
| 架构路线 | 模块化管道平台（方案 1） |
| 交付策略 | 全量愿景 + M1→M4 分阶段可演示上线 |
| LLM | 经 OpenRouter 接入 |
| Embedding | 可插拔 Provider（默认推荐本地 bge-m3） |

---

## 1. 背景与问题

### 1.1 背景

调研（见 `research.md`）表明：Naive RAG（切块 → 纯向量 Top-K → Prompt）在 2026 年已不具备生产竞争力。瓶颈从「生成能力」转向**检索精度、证据编排、权限与评测**。行业生产基线为 Hybrid + Rerank；Adaptive / Agentic / GraphRAG 是复杂场景的扩展层。长上下文不会消灭 RAG，二者需按任务路由。

### 1.2 要解决的问题

企业内部知识分散在上传文档与 Wiki（Notion / Confluence / 飞书等）中，员工难以快速获得**可信、可追溯、不越权**的答案。现有 Demo 级 RAG 通常存在：

- 检索漏检/误检，专有名词与编号召回差  
- 切块失联，答案无法可靠引用  
- 权限只做在前端，检索层可越权  
- 无评测与审计，无法规模化上线  
- 复杂多跳与关系型问题单次向量检索不够  

### 1.3 产品一句话

员工在权限范围内，对上传文档与协作 Wiki 提问，获得**带引用、可审计**的答案；系统按问题复杂度自动选择检索深度，并分阶段具备 Agent 多跳与 Graph 关系推理能力。

---

## 2. 目标与非目标

### 2.1 目标

1. 打造**下一代模块化先进 RAG**：索引 / 检索 / 精排 / 路由 / Agent / Graph 可插拔、可编排。  
2. **本地/单机可跑通**，架构预留私有化（替换存储与网关，不绑死公有云）。  
3. 企业硬门槛：**检索层 ACL、强制引用、审计日志**。  
4. 质量可量化：内置评测，相对 Naive RAG 有可复现提升。  
5. 按 M1–M4 交付全量能力愿景，每阶段可独立演示与验收。

### 2.2 非目标（首年版不做）

- 多租户公有 SaaS 计费与插件市场  
- 以音视频为主的端到端多模态 RAG（PDF 内基础表格/文本优先）  
- 取代企业全站搜索的全网爬虫  
- 自动企业主数据 / 本体工程平台（M4 不做 MDM）  
- 对外部业务系统的写入类操作（Agent 以只读工具为主）

### 2.3 成功标准（可验收）

| # | 标准 |
| --- | --- |
| S1 | 单机一键（或 docker-compose）启动后，上传文档即可带引用问答 |
| S2 | 关键断言可追溯至 chunk/文档；无法支撑时明确「资料不足」 |
| S3 | 无权限文档永不进入模型上下文（检索层强制） |
| S4 | M1–M4 各有验收清单与演示脚本 |
| S5 | 评测集可回归；管道指标可对比 Naive 基线 |

---

## 3. 用户与场景

### 3.1 角色

| 角色 | 诉求 |
| --- | --- |
| 普通员工 | 查制度/项目/Wiki，答案可信、能打开原文 |
| 知识管理员 | 建库、上传、同步 Wiki、查看索引健康度 |
| 安全/合规 | 不越权、可审计、可私有化部署 |
| 平台管理员 | 配置 OpenRouter、模型、Embedding、连接器、评测 |

### 3.2 核心场景

1. **制度/FAQ 问答**：单次 Hybrid 检索即可。  
2. **跨文档对比/汇总**：需多步或 Graph。  
3. **调研型多跳**：「A 政策如何影响 B 项目」→ Agent 规划多步检索。  
4. **权限隔离问答**：同题不同用户，答案证据集不同。  
5. **知识运营**：同步失败告警、重建索引、评测回归。

---

## 4. 方案概述

采用**模块化管道平台**：

- 统一 **Orchestrator** 按策略路由：`none | single | multi | agent | graph`  
- **LLM** 仅经 OpenRouter；**Embedding** 经可插拔 Provider（默认本地 bge-m3）  
- 知识源：**本地上传** + **Wiki 只读同步**（Notion / Confluence / 飞书，M1 至少落地一种，接口预留其余）  
- 失败降级：Agent/Graph → Adaptive 单次 → 明确错误，禁止静默编造  

不采用「一切皆 Agent」作为首发基线（成本与权限难控）；不采用「纯搜索薄生成」作为终态（无法覆盖先进 RAG 愿景）。

---

## 5. 系统架构

```
[Connectors] 上传 / Notion | Confluence | 飞书
      ↓
[Ingest] 解析 → 切块(语义/父子) → 语境 enrichment → Embed + BM25
      ↓
[Stores] Vector · Sparse · Doc Meta · (M4) Graph · ACL · Audit
      ↓
[Orchestrator] 路由: none | single | multi(M2) | agent(M3) | graph(M4)
      ↓
[Retrieve] Hybrid(RRF) → Rerank → ACL filter → Context pack
      ↓
[Generate] OpenRouter → 引用对齐 / 不足则拒答
      ↓
[Eval & Observe] 评测集 · 轨迹 · 延迟/成本
```

### 5.1 模块职责

| 模块 | 职责 | 主要依赖 |
| --- | --- | --- |
| Connector Hub | 拉取/增量同步；统一文档模型 | 外部 Wiki API |
| Ingest Pipeline | 解析、切块、元数据、可选 Contextual 前缀 | Embedding Provider |
| Index Manager | 向量/稀疏索引生命周期、版本、重建 | Vector / Sparse store |
| Retriever | Hybrid + RRF + Rerank；产出候选证据 | Indexes |
| ACL Gateway | 证据进入上下文前过滤 | 身份、ACL 存储 |
| Orchestrator | 策略路由、预算、超时、降级 | 各执行器 |
| Generator | Prompt 组装、OpenRouter、引用强制 | OpenRouter |
| Agent Runtime | 规划、工具注册、轨迹（M3） | Orchestrator + Tools |
| Graph Engine | 构图、社区摘要、图检索（M4） | Doc store |
| Eval Service | Golden set、忠实度/引用指标、回归 | 全链路 |
| Admin & Chat UI | 知识库、同步、问答、审计、评测 | API |

### 5.2 设计原则

1. 业务代码只依赖 `LLMProvider` / `EmbeddingProvider` 接口，不直连具体 SDK 细节散落各处。  
2. ACL 在检索层执行，禁止「先检索再靠 Prompt 保密」。  
3. 所有生成路径支持证据 ID 绑定与拒答。  
4. Store / 网关可替换，服务本地优先与后续私有化。  

---

## 6. 功能需求

### 6.1 需求列表

| ID | 需求 | 优先级 | 阶段 |
| --- | --- | --- | --- |
| FR-01 | 知识库 CRUD；文档上传（PDF / Word / Markdown / TXT） | P0 | M1 |
| FR-02 | Wiki 只读同步（Notion / Confluence / 飞书至少一种；连接器接口预留其余） | P0 | M1 |
| FR-03 | Hybrid 检索（Dense + BM25 + RRF）+ Cross-Encoder 重排 | P0 | M1 |
| FR-04 | 语义切块 + 父子文档索引；答案强制引用；资料不足明示 | P0 | M1 |
| FR-05 | OpenRouter 多模型配置；Embedding Provider 可插拔（默认 bge-m3） | P0 | M1 |
| FR-06 | 索引任务状态（排队/运行/成功/失败）、可重建 | P0 | M1 |
| FR-07 | 最小评测脚本：Naive vs Hybrid+Rerank 可对比 | P0 | M1 |
| FR-08 | Adaptive 路由：不检索 / 单次 / 多步 | P0 | M2 |
| FR-09 | 用户与角色；知识库级 + 文档级 ACL；检索层强制过滤 | P0 | M2 |
| FR-10 | 审计日志（问答、所用证据、路由、模型；追加写） | P0 | M2 |
| FR-11 | Contextual Retrieval 或等价块级语境增强 | P1 | M2 |
| FR-12 | 评测看板 v1（忠实度、引用对齐、延迟） | P1 | M2 |
| FR-13 | Agentic：规划 → 工具 → 中途再检索 → 综合；步数/Token 预算；可审计轨迹 | P0 | M3 |
| FR-14 | Agent 失败降级到 M2 单次管道 | P0 | M3 |
| FR-15 | GraphRAG：实体关系抽取、社区/层级摘要、图+向量混合检索 | P0 | M4 |
| FR-16 | 关系型/全局汇总类查询路由到 Graph；图谱重建与质量抽检 | P1 | M4 |

### 6.2 引用与权限硬规则

1. **无出处不断言**：事实性输出须绑定 `evidence_id`；无法绑定则拒答或标明不确定。  
2. **ACL 先于上下文打包**：过滤后无证据 → 返回「无权限或无资料」，不进行猜测型生成。  
3. **引用可导航**：至少回到文档；优先支持 chunk 定位。  
4. **越权必测**：用户 A 询问仅用户 B 可见内容时，零泄漏。  

### 6.3 关键用户流程

**F1 建库灌数**：创建知识库 → 配置可见性 → 上传 / 绑定 Wiki → 观察同步与索引 → 可重建。  

**F2 权限问答**：登录 → 选择知识库或「有权全部」→ 提问 → 答案 + 引用 → 打开原文。  

**F3 复杂问题（M2+）**：展示策略（单次/多步/Agent）与可选轨迹；超预算降级并提示。  

**F4 审计评测**：按用户/时间查轨迹；跑评测集；对比管道版本。  

---

## 7. 里程碑与范围

| 里程碑 | 主题 | In | Out |
| --- | --- | --- | --- |
| **M1** | 生产基线 Hybrid RAG | FR-01–07；本地可跑；至少一种 Wiki | Adaptive、细粒度 ACL、Agent、Graph |
| **M2** | 企业硬门槛 | FR-08–12；越权测试通过 | 多 Agent、完整 GraphRAG |
| **M3** | Agentic | FR-13–14；轨迹与预算 | 业务系统写入、插件市场 |
| **M4** | GraphRAG | FR-15–16；关系/汇总增益可演示 | 自动本体/MDM 平台 |

**跨阶段约束**

- LLM 经 OpenRouter；Embedding 可插拔  
- 架构支持私有化扩展  
- 每阶段交付：演示脚本 + 验收用例 + 已知限制说明  

---

## 8. 数据模型（逻辑）

| 对象 | 关键字段 | 说明 |
| --- | --- | --- |
| User / Role | id, roles[] | 先本地账号，预留 SSO |
| KnowledgeBase | id, name, acl | 权限主容器 |
| Document | id, kb_id, source, uri, acl, status, version | source = upload \| notion \| confluence \| feishu \| … |
| Chunk | id, doc_id, parent_id?, text, context_prefix?, embedding_ref | 支持父子 |
| IndexJob | id, kb_id, state, error, stats | 同步/重建 |
| QueryTrace | id, user_id, route, steps[], evidence_ids[], model, cost | 审计与 Agent |
| ACLPolicy | principal, resource, action | 检索层执行 |
| EvalCase / EvalRun | question, expected, metrics | 回归 |
| GraphNode / Edge | entity, type, relations, community | M4 |

---

## 9. 非功能需求

| 类别 | 要求 |
| --- | --- |
| 可部署性 | 本地单机可启动；配置环境变量化（OpenRouter Key、模型名、嵌入模型路径等） |
| 安全性 | 密钥不入库明文；日志默认脱敏；检索层 ACL；审计追加写 |
| 可观测性 | 记录路由、证据 ID、延迟、Token/费用估算；M3+ 记录 Agent 步骤 |
| 性能 | M1 单次管道 P95 可测量可配置；具体 SLA 在私有化项目中再签 |
| 可替换性 | Vector DB、Sparse 索引、LLM/Embedding Provider 均接口化 |
| 降级 | 上游失败时明确错误或降级管道，禁止无证据生成 |

---

## 10. 技术约束与集成

| 项 | 决策 |
| --- | --- |
| LLM | **OpenRouter** 统一接入，支持配置切换模型 |
| Embedding | **可插拔**；默认推荐 **本地 bge-m3**；可扩展 OpenRouter 或其他 |
| 向量库 | **PostgreSQL + pgvector**；词法检索 tsvector/BM25；无独立 Qdrant |
| 前端 | **Next.js 16.3.5**（App Router）+ **ui-ux-pro-max**（`design-system/enterprise-knowledge-assistant/`） |
| 包管理 | **Python：uv**；**前端：pnpm**（强制，含 lockfile；`next` 钉死 `16.3.5`） |
| 知识源 M1 | 文件上传 + 飞书 Wiki 只读同步 |
| 部署 | 先本地/单机；预留私有化（VPC/专有云） |
| 评测 | 自建领域 golden set + 忠实度/引用对齐；可参考 RAGAS 等方法论 |

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 范围过大导致长期不可用 | 高 | 严格 M1–M4 验收门禁 |
| Wiki API 变更/配额 | 中 | 连接器隔离、增量同步、失败重试与告警 |
| OpenRouter 限流/不可用 | 中 | 多模型配置、超时重试、明确错误提示 |
| Graph 成本高、质量不稳 | 中 | M4 可开关；小库试点；重建与抽检 |
| Agent 成本失控 | 高 | 硬性步数/Token 预算；默认降级单次 |
| 权限漏洞 | 高 | M2 越权用例强制通过；ACL 单测+集成测 |

---

## 12. 验收标准

### 12.1 M1

- [ ] 上传 PDF/Word/MD/TXT 后可问答，答案含可点击引用  
- [ ] 至少一种 Wiki 同步成功并进入检索  
- [ ] Hybrid + Rerank 可启用；与 Naive 开关对比评测脚本跑通  
- [ ] OpenRouter 与默认 Embedding 配置生效  
- [ ] 本地一键启动文档齐全  

### 12.2 M2

- [ ] Adaptive 路由结果可观测（日志/UI）  
- [ ] 越权用例 100% 不泄漏  
- [ ] 审计可按用户/时间检索问答与证据  
- [ ] 无证据时拒答文案符合规范  
- [ ] Contextual（或等价）策略可配置  

### 12.3 M3

- [ ] 多跳题产生完整可审计轨迹  
- [ ] 超预算触发降级，不无限循环  
- [ ] 回归集上不低于约定的 M2 基线门槛（具体阈值实现计划中锁定）  

### 12.4 M4

- [ ] 图谱可构建与重建  
- [ ] 关系/汇总题相对「仅向量」有可展示增益  
- [ ] Graph 路径可关闭，不影响 M1–M3  

---

## 13. 度量指标（产品/质量）

| 指标 | 用途 |
| --- | --- |
| 检索 Recall@k / nDCG | 检索质量 |
| 引用对齐率 / 忠实度 | 降低幻觉与错引 |
| 拒答正确率 | 「该拒则拒」 |
| 越权泄漏次数 | 安全门禁（目标 0） |
| P95 端到端延迟 | 体验 |
| 单次请求费用估算 | 成本（尤其 M3） |
| 索引滞后时间 | Wiki 新鲜度 |

---

## 14. 开放问题（已在技术方案中锁定）

详见 [`TECH_DESIGN.md`](./TECH_DESIGN.md) §2。摘要：

1. **Wiki M1**：飞书；Notion/Confluence 仅 stub。  
2. **存储**：**PostgreSQL 16 + pgvector**（稠密）+ tsvector/BM25（词法）；开发机约 8GB RAM；无独立 Qdrant。  
3. **身份**：M1 本地用户 + JWT；预留 OIDC。  
4. **Adaptive**：M2 规则 + 可选 LLM 分类（`ROUTER_MODE`）。  
5. **回归门槛**：M3 faithfulness ≥ M2 − 0.05；M4 关系题引用命中 +10pp。  
6. **前端设计**：统一 **ui-ux-pro-max**（`design-system/enterprise-knowledge-assistant/`）。  
7. **包管理**：**uv**（Python）+ **pnpm**（前端）。  
8. **前端框架**：**Next.js 16.3.5**（App Router）。  

---

## 15. 文档关系与下一步

| 文档 | 作用 |
| --- | --- |
| [`research.md`](./research.md) | 行业现状、痛点、趋势依据 |
| 本文 `PRD.md` | 产品需求与分阶段范围 |
| [`TECH_DESIGN.md`](./TECH_DESIGN.md) | 技术选型、架构、接口、数据与部署 |
| [`docs/superpowers/plans/2026-09-12-m1-hybrid-rag.md`](./docs/superpowers/plans/2026-09-12-m1-hybrid-rag.md) | M1 任务级实现计划 |

**下一步**：评审技术方案 → 按 M1 计划开工（Subagent-Driven 或 Inline Execution）。

---

## 附录 A：与调研结论的映射

| 调研结论 | PRD 落点 |
| --- | --- |
| Hybrid + Rerank 为生产基线 | M1 FR-03 |
| 切块与 Contextual 影响召回 | M1 FR-04、M2 FR-11 |
| 检索层 ACL / 审计为企业基线 | M2 FR-09/10 |
| Adaptive 控制噪声与成本 | M2 FR-08 |
| Agentic 适合多跳，需预算 | M3 FR-13/14 |
| GraphRAG 补关系/汇总 | M4 FR-15/16 |
| 长上下文与 RAG 互补 | Orchestrator 保留 `none` 路由 |
| 评测不足是普遍痛点 | FR-07/12 + 第 13 节指标 |
