# Extractable components

## AppShell
- Source: `apps/web/components/app-shell.tsx`
- Category: layout
- Description: Left sidebar app shell with brand, nav links, sign-out, and main canvas
- Extractable props: activeItem (string, default: "chat") — maps to current route segment
- Hardcoded: brand text「企业知识助手」, nav labels 问答/知识库/任务, Phosphor icons, CSS Modules classes

## StatusPill
- Source: `apps/web/components/status-pill.tsx`
- Category: basic
- Description: Status badge for documents and index jobs
- Extractable props: status (string, default: "pending")
- Hardcoded: Chinese labels, pill color classes
