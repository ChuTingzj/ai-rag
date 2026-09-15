# Design System — 企业知识助手 (Redesign 2026)

Authenticated enterprise knowledge assistant (RAG Q&A + knowledge bases). Dense productivity UI — not a marketing site.

## Brand & product

- Name: 企业知识助手
- Tone: precise, calm, trustworthy; power-user density without clutter
- Shell: left sidebar + main canvas; login is a standalone centered card

## Visual direction (NEW — replaces teal)

Cool **slate + cobalt** enterprise language. Flat surfaces, 1px borders, restrained elevation.

| Role | Hex | Token |
|------|-----|-------|
| Background | `#F4F6F8` | `--background` |
| Foreground | `#0F172A` | `--foreground` |
| Card | `#FFFFFF` | `--card` |
| Muted surface | `#E8ECF1` | `--muted` |
| Muted text | `#64748B` | `--muted-foreground` |
| Border | `#D5DCE5` | `--border` / `--input` |
| Primary | `#2563EB` | `--primary` |
| On primary | `#FFFFFF` | `--primary-foreground` |
| Secondary | `#EEF2FF` | `--secondary` |
| Accent (rare CTA) | `#F59E0B` | `--accent` |
| Destructive | `#DC2626` | `--destructive` |
| Ring | `#2563EB` | `--ring` |
| Sidebar | `#0B1220` | `--sidebar` |
| Sidebar text | `#E2E8F0` | `--sidebar-foreground` |
| Sidebar active | `#2563EB` | `--sidebar-primary` |
| Sidebar hover | `#1E293B` | `--sidebar-accent` |
| Sidebar border | `#1E293B` | `--sidebar-border` |

Radius: **10px** (`--radius: 0.625rem`). Prefer border over heavy shadow; optional soft shadow `0 1px 2px rgb(15 23 42 / 0.06)` on elevated composer / dialogs only.

## Typography

- Font: **Manrope** (400/500/600/700/800) — geometric, product-grade; never Inter/Roboto/system stacks as the primary face
- Body ~0.9375rem; page titles 1.25–1.5rem weight 700; nav labels 0.875rem weight 500

## Spacing

4 / 8 / 12 / 16 / 24 / 32 / 48 px

## Layout patterns

1. **Sidebar**: dark charcoal rail, brand wordmark, icon+label nav, active = primary fill pill, sign-out at bottom
2. **Chat**: sticky KB toolbar; roomy transcript; citations as persistent right rail (desktop) / Sheet (mobile); composer as elevated bottom strip
3. **KB list**: page header + primary create action; Table with muted header
4. **KB detail**: Tabs + dashed upload zone + status Badges
5. **Jobs**: Card list with status Badges + empty state
6. **Login**: centered Card on soft slate field, full-width primary submit

## Icons

Lucide-style outline icons (stroke 2). No emoji as structural icons.

## Anti-patterns

- Teal/mint palette (legacy), purple AI gradients, glow, glassmorphism stacks
- Marketing hero, cream+terracotta, broadsheet dense columns
- Blank freeze during loading — use skeleton / `aria-busy`
