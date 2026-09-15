# Local design direction (Superdesign cloud unavailable)

Superdesign CLI login failed twice (TLS disconnect). Canvas drafts could not be created.
This file records the locked design direction used for implementation.

## Locked choices

- Full site: login, chat, kbs list/detail, jobs, AppShell
- Keep existing teal enterprise palette and Plus Jakarta Sans
- Layout / hierarchy polish only
- Implement with shadcn/ui + Tailwind v4 + lucide-react

## Variation A (selected for implementation)

- Sidebar with stronger brand weight and nav active tint
- Chat: two-pane desktop; citations Sheet on small screens
- Composer as bottom card with Textarea + send Button
- KB create via Dialog; detail via Tabs; status via Badge
- Jobs page as Card list of recent jobs with empty state linking to KBs

## Variation B (not selected)

- Denser dashboard-style KB cards grid instead of table
- Citations always as bottom drawer even on desktop

## Pages in scope

1. Login — centered Card
2. Chat — AppShell + transcript + citations
3. Knowledge bases — Table + Dialog
4. Knowledge base detail — Tabs (documents / connector / jobs)
5. Jobs — list Card with Status Badges
