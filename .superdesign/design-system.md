# Design System — 企业知识助手

Authenticated enterprise knowledge assistant (RAG Q&A + knowledge bases). Not a marketing site.

## Brand & product

- Name: 企业知识助手
- Tone: clear, trustworthy, dense productivity UI
- Shell: left nav + main canvas; login is standalone centered card

## Color palette (keep — do not rebrand)

| Role | Hex | Legacy CSS | shadcn CSS variable |
|------|-----|------------|---------------------|
| Primary | `#0d9488` | `--color-primary` | `--primary` |
| On primary | `#ffffff` | `--color-on-primary` | `--primary-foreground` |
| Secondary | `#14b8a6` | `--color-secondary` | `--secondary` |
| Accent / rare CTA | `#ea580c` | `--color-accent` | `--accent` (+ `--accent-foreground` `#ffffff`) |
| Background | `#f0fdfa` | `--color-background` | `--background` |
| Foreground | `#134e4a` | `--color-foreground` | `--foreground` |
| Card | `#ffffff` | `--color-card` | `--card` / `--card-foreground` |
| Muted | `#e8f1f4` | `--color-muted` | `--muted` |
| Muted text | `#475569` | `--color-muted-foreground` | `--muted-foreground` |
| Border | `#99f6e4` | `--color-border` | `--border` / `--input` |
| Destructive | `#dc2626` | `--color-destructive` | `--destructive` |
| Ring | `#0d9488` | `--color-ring` | `--ring` |

Flat surfaces: prefer **1px border** over heavy shadows. Radius **8px** (`--radius: 0.5rem`).

## Typography

- Font: Plus Jakarta Sans (400/600/700/800)
- Body ~0.9375rem; page titles ~1.25rem–1.5rem, weight 700–800

## Spacing scale

4 / 8 / 16 / 24 / 32 / 48 px

## Component mapping (shadcn)

| Pattern | Component |
|---------|-----------|
| Primary / secondary actions | `Button` (default / outline / secondary) |
| Forms | `Input`, `Label`, `Textarea`, `Select` |
| Surfaces | `Card` |
| Create KB | `Dialog` |
| KB detail sections | `Tabs` |
| Document / KB lists | `Table` |
| Job / doc status | `Badge` |
| App chrome | Sidebar pattern or nav + `Separator` + `Button` |
| Citations on mobile | `Sheet` |
| Scrollable transcript | `ScrollArea` |

## Layout direction (approved style lock)

Keep teal enterprise language. Improve hierarchy:

1. **Sidebar**: clearer brand block, nav item spacing, active state with primary tint
2. **Chat**: sticky toolbar, roomier message column, citations as persistent right panel (desktop) / Sheet (mobile), composer as elevated card strip
3. **KB list**: page header + Dialog create; Table with muted header row
4. **KB detail**: Tabs + dashed upload zone + status Badges
5. **Jobs**: real list surface (not stub pointer-only), Badge states, empty state copy
6. **Login**: centered Card, primary submit full width

## Icons

Target implementation uses **lucide-react** (shadcn default). Do not use emoji as structural icons.

## Anti-patterns

- Purple AI gradients, heavy glow, marketing hero
- Changing brand name or primary teal/orange accent
- Blank freeze during loading — use skeleton / `aria-busy`
