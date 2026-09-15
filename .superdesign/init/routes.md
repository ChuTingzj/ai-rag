# Routes

App Router under `apps/web/app/`. No nested layouts beyond root. Authenticated pages wrap with `AuthGate` + `AppShell` (except `/login`).

| URL | File | Layout | Summary |
|-----|------|--------|---------|
| `/` | `apps/web/app/page.tsx` | AuthGate + AppShell | RAG chat: KB select, messages, composer, citations panel / Sheet |
| `/login` | `apps/web/app/login/page.tsx` | none | Email/password login card |
| `/kbs` | `apps/web/app/kbs/page.tsx` | AuthGate + AppShell | KB table + create Dialog |
| `/kbs/[id]` | `apps/web/app/kbs/[id]/page.tsx` | AuthGate + AppShell | Tabs: documents / Feishu connector / jobs |
| `/jobs` | `apps/web/app/jobs/page.tsx` | AuthGate + AppShell | KB list gateway into per-KB jobs tab |
