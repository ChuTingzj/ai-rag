# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/enterprise-knowledge-assistant/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Enterprise Knowledge Assistant  
**Generated:** 2026-09-12 (ui-ux-pro-max)  
**Updated:** 2026-09-12 — product app overrides (not marketing landing)  
**Category:** Productivity / Enterprise Internal Tool  
**Design Dials:** Variance 4/10 | Motion 4/10 | Density 7/10  

---

## Product framing (override landing pattern)

This is an **authenticated app shell**, not a marketing site:

- Layout: left nav (Chat / Knowledge Bases / Jobs / Eval) + main canvas  
- No hero / product-video / pricing sections  
- Priority: clarity, citation trust, loading feedback, keyboard access  

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#0D9488` | `--color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` |
| Secondary | `#14B8A6` | `--color-secondary` |
| On Secondary | `#0F172A` | `--color-on-secondary` |
| Accent/CTA | `#EA580C` | `--color-accent` |
| On Accent/CTA | `#FFFFFF` | `--color-on-accent` |
| Background | `#F0FDFA` | `--color-background` |
| Foreground | `#134E4A` | `--color-foreground` |
| Card | `#FFFFFF` | `--color-card` |
| Card Foreground | `#134E4A` | `--color-card-foreground` |
| Muted | `#E8F1F4` | `--color-muted` |
| Muted Foreground | `#475569` | `--color-muted-foreground` |
| Border | `#99F6E4` | `--color-border` |
| Destructive | `#DC2626` | `--color-destructive` |
| On Destructive | `#FFFFFF` | `--color-on-destructive` |
| Ring | `#0D9488` | `--color-ring` |

**Notes:** Teal primary + orange accent. On-primary/on-accent set to white for button contrast (project override). Flat surfaces: prefer **1px border** over heavy shadows.

### Typography

- **Heading / Body:** Plus Jakarta Sans (400/600/700/800)
- **Google Fonts:** `https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap`

```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap');

:root {
  --font-sans: "Plus Jakarta Sans", system-ui, sans-serif;
}
```

### Spacing

| Token | Value |
|------|------|
| `--space-xs` | 4px |
| `--space-sm` | 8px |
| `--space-md` | 16px |
| `--space-lg` | 24px |
| `--space-xl` | 32px |
| `--space-2xl` | 48px |

### Style

- **Name:** Flat Design  
- Light + Dark supported (M1 ship light; dark tokens reserved)  
- Transitions: 150–200ms ease  
- Hover: color/opacity/background shift; `cursor: pointer` on clickable controls  
- Focus: `outline: 2px solid var(--color-ring); outline-offset: 2px`  

### Icons

- Library: **Phosphor** `@phosphor-icons/react`, weight `regular`  
- Common: `MagnifyingGlass`, `Folder`, `FolderOpen`, `FileText`, `UploadSimple`, `ChatCircle`, `ShieldCheck`, `ListChecks`  
- Never use emoji as structural icons  
- Decorative icons beside text: `aria-hidden="true"`  

### Motion

- List enter: subtle fade/translate (≤400ms); honor `prefers-reduced-motion: reduce`  
- Do **not** use `back.out` overshoot on dense tables or citation lists  
- Query loading: skeleton + `aria-busy="true"` (no blank freeze)  

### App shell components

| Component | Spec |
|-----------|------|
| Primary button | bg `--color-primary`, text `--color-on-primary`, radius 8px |
| Accent button | bg `--color-accent` (destructive/sync rare CTAs) |
| Input | white card surface, border `--color-border`, labeled |
| Card / panel | white + 1px teal-tint border; no multi-layer shadow |
| Nav item | muted idle; primary tint when active |
| Citation chip | muted bg; click focuses source snippet |

### Anti-patterns

- Complex onboarding wizards  
- Purple-gradient AI cliché themes  
- Placeholder-only inputs  
- Frozen UI during retrieval/generation  

### Pre-delivery checklist

- [ ] No emoji icons  
- [ ] cursor-pointer on clickable elements  
- [ ] Hover 150–300ms  
- [ ] Text contrast ≥4.5:1  
- [ ] Visible focus rings  
- [ ] prefers-reduced-motion respected  
- [ ] Responsive 375 / 768 / 1024 / 1440  
