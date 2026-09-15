# Pages dependency trees

## / (Chat)
Entry: `apps/web/app/page.tsx`
Dependencies:
- `apps/web/app/chat.module.css`
- `apps/web/components/app-shell.tsx`
  - `apps/web/components/app-shell.module.css`
  - `apps/web/lib/auth-token.ts`
- `apps/web/components/auth-gate.tsx`
  - `apps/web/lib/auth-token.ts`
- `apps/web/components/ui.module.css`
- `apps/web/lib/api-client.ts`
- `apps/web/styles/tokens.css` (via globals)
- `apps/web/app/globals.css`

## /login
Entry: `apps/web/app/login/page.tsx`
Dependencies:
- `apps/web/app/login/login.module.css`
- `apps/web/components/ui.module.css`
- `apps/web/lib/api-client.ts`
- `apps/web/lib/auth-token.ts`
- `apps/web/styles/tokens.css`

## /kbs
Entry: `apps/web/app/kbs/page.tsx`
Dependencies:
- `apps/web/app/kbs/kbs.module.css`
- `apps/web/components/app-shell.tsx`
  - `apps/web/components/app-shell.module.css`
- `apps/web/components/auth-gate.tsx`
- `apps/web/components/ui.module.css`
- `apps/web/lib/api-client.ts`

## /kbs/[id]
Entry: `apps/web/app/kbs/[id]/page.tsx`
Dependencies:
- `apps/web/app/kbs/kbs.module.css`
- `apps/web/components/app-shell.tsx`
- `apps/web/components/auth-gate.tsx`
- `apps/web/components/status-pill.tsx`
  - `apps/web/components/ui.module.css`
- `apps/web/components/ui.module.css`
- `apps/web/lib/api-base.ts`
- `apps/web/lib/api-client.ts`
- `apps/web/lib/auth-token.ts`

## /jobs
Entry: `apps/web/app/jobs/page.tsx`
Dependencies:
- `apps/web/app/kbs/kbs.module.css`
- `apps/web/components/app-shell.tsx`
- `apps/web/components/auth-gate.tsx`
