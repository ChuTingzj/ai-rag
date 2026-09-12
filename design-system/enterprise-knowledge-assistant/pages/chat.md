# Chat Page Overrides

> Overrides `MASTER.md` for `/` (问答页).

## Layout

- Full-height app shell: **left nav** + **center transcript** + **right citation panel** (≥320px on desktop)
- On <768px: citation panel becomes bottom sheet / drawer; primary CTA remains send

## Interaction

- Empty state: short prompt examples (not a marketing hero)
- While querying: message skeleton + `aria-busy` on answer region
- Citations: list with `FileText` icon; click scrolls/highlights snippet
- Route badge (M2+): muted chip showing `single` / `multi` / `agent` — do not use emoji

## Components

- Composer: labeled textarea + primary send button; disable send while in-flight
- KB selector: accessible listbox/select with visible label「知识库」

## Motion

- New messages: 200ms fade-in only; no bounce on citation list
