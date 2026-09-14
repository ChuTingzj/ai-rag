import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "企业知识助手",
  description: "Enterprise knowledge assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
