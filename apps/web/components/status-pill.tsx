import ui from "./ui.module.css";

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  pending: { label: "待处理", className: ui.statusPending },
  indexing: { label: "索引中", className: ui.statusIndexing },
  ready: { label: "就绪", className: ui.statusReady },
  failed: { label: "失败", className: ui.statusFailed },
  completed: { label: "完成", className: ui.statusReady },
  running: { label: "运行中", className: ui.statusIndexing },
};

type StatusPillProps = {
  status: string;
};

export function StatusPill({ status }: StatusPillProps) {
  const key = status.toLowerCase();
  const mapped = STATUS_MAP[key] ?? {
    label: status,
    className: ui.statusPending,
  };
  return (
    <span className={`${ui.statusPill} ${mapped.className}`}>
      {mapped.label}
    </span>
  );
}
