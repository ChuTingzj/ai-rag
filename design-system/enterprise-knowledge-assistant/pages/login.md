# Login Page Overrides

> Overrides `MASTER.md` for `/login`.

## Layout

- Centered single card (max-width 400px) on `--color-background`
- Product name as strongest text in viewport (brand-first); one short supporting line; form; primary CTA
- No hero image, no marketing sections

## Forms

- Email + password with visible `<label>`
- Validate on blur; on submit show button loading then inline error summary if failed
- Focus first invalid field after failed submit

## Motion

- Card: optional 300ms fade; reduced-motion → instant
