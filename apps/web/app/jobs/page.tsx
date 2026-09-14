"use client";

import { AppShell } from "@/components/app-shell";
import { AuthGate } from "@/components/auth-gate";

import styles from "../kbs/kbs.module.css";

export default function JobsPage() {
  return (
    <AuthGate>
      <AppShell>
        <div className={styles.page}>
          <h1 className={styles.title}>任务</h1>
          <p style={{ color: "var(--color-muted-foreground)" }}>
            在知识库详情页的「任务」标签中查看索引与同步进度。
          </p>
        </div>
      </AppShell>
    </AuthGate>
  );
}
