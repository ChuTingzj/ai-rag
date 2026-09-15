import { Badge } from "@/components/ui/badge";

const STATUS_MAP: Record<
  string,
  { label: string; variant: "secondary" | "warning" | "success" | "destructive" }
> = {
  pending: { label: "待处理", variant: "secondary" },
  indexing: { label: "索引中", variant: "warning" },
  ready: { label: "就绪", variant: "success" },
  failed: { label: "失败", variant: "destructive" },
  completed: { label: "完成", variant: "success" },
  running: { label: "运行中", variant: "warning" },
};

type StatusPillProps = {
  status: string;
};

export function StatusPill({ status }: StatusPillProps) {
  const key = status.toLowerCase();
  const mapped = STATUS_MAP[key] ?? {
    label: status,
    variant: "secondary" as const,
  };
  return <Badge variant={mapped.variant}>{mapped.label}</Badge>;
}
