# Knowledge Base Page Overrides

> Overrides `MASTER.md` for `/kbs` and `/kbs/:id`.  
> **Density dial:** 8/10 (denser tables/actions).

## Layout

- List page: page title + primary「新建知识库」+ table/cards of KBs
- Detail: header (name, sync/rebuild actions) + tabs or sections: Documents / Connector / Jobs
- Upload zone: dashed border using `--color-border`; `UploadSimple` icon + text

## Components

- Status pills: pending / indexing / ready / failed — color + text (not color alone)
- Job rows: compact; show error message inline when failed
- Feishu bind: secondary button; destructive only for delete

## Motion

- Document list: light stagger OK; **no** overshoot easing on table rows
- Indexing: persistent progress/skeleton until ready
