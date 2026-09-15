# Theme

## Compact token summary

### Colors (`:root`)

| Token | Value |
|-------|-------|
| `--color-primary` | `#0d9488` |
| `--color-on-primary` | `#ffffff` |
| `--color-secondary` | `#14b8a6` |
| `--color-on-secondary` | `#0f172a` |
| `--color-accent` | `#ea580c` |
| `--color-on-accent` | `#ffffff` |
| `--color-background` | `#f0fdfa` |
| `--color-foreground` | `#134e4a` |
| `--color-card` | `#ffffff` |
| `--color-card-foreground` | `#134e4a` |
| `--color-muted` | `#e8f1f4` |
| `--color-muted-foreground` | `#475569` |
| `--color-border` | `#99f6e4` |
| `--color-destructive` | `#dc2626` |
| `--color-on-destructive` | `#ffffff` |
| `--color-ring` | `#0d9488` |

Light mode only shipped. Flat enterprise: 1px teal-tint borders, minimal shadow.

### Typography

- Font: `"Plus Jakarta Sans", system-ui, sans-serif` (`--font-sans`)
- Weights used: 400 / 600 / 700 / 800

### Spacing

| Token | Value |
|-------|-------|
| `--space-xs` | 4px |
| `--space-sm` | 8px |
| `--space-md` | 16px |
| `--space-lg` | 24px |
| `--space-xl` | 32px |
| `--space-2xl` | 48px |

### Radius / motion

- `--radius-md`: 8px
- `--transition-fast`: 150ms ease
- `--transition-base`: 200ms ease
- Breakpoint: nav collapses labels at `max-width: 767px`

### shadcn semantic mapping (target)

| shadcn | Source |
|--------|--------|
| `--primary` | `#0d9488` |
| `--primary-foreground` | `#ffffff` |
| `--secondary` | `#14b8a6` / muted teal |
| `--accent` | `#ea580c` |
| `--background` | `#f0fdfa` |
| `--foreground` | `#134e4a` |
| `--card` | `#ffffff` |
| `--muted` | `#e8f1f4` |
| `--muted-foreground` | `#475569` |
| `--border` / `--input` | `#99f6e4` |
| `--destructive` | `#dc2626` |
| `--ring` | `#0d9488` |
| `--radius` | `0.5rem` (8px) |

## Raw source dumps

### `apps/web/styles/tokens.css`

```css
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap");

:root {
  --color-primary: #0d9488;
  --color-on-primary: #ffffff;
  --color-secondary: #14b8a6;
  --color-on-secondary: #0f172a;
  --color-accent: #ea580c;
  --color-on-accent: #ffffff;
  --color-background: #f0fdfa;
  --color-foreground: #134e4a;
  --color-card: #ffffff;
  --color-card-foreground: #134e4a;
  --color-muted: #e8f1f4;
  --color-muted-foreground: #475569;
  --color-border: #99f6e4;
  --color-destructive: #dc2626;
  --color-on-destructive: #ffffff;
  --color-ring: #0d9488;

  --font-sans: "Plus Jakarta Sans", system-ui, sans-serif;

  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  --radius-md: 8px;
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
}
```

### `apps/web/app/globals.css`

```css
@import "../styles/tokens.css";

*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  min-height: 100%;
  font-family: var(--font-sans);
  color: var(--color-foreground);
  background: var(--color-background);
}

button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible {
  outline: 2px solid var(--color-ring);
  outline-offset: 2px;
}
```

### Tailwind

- Tailwind v4 via `@tailwindcss/postcss` in `apps/web/postcss.config.mjs`
- Not yet used in components (CSS Modules only); shadcn init will wire theme utilities
