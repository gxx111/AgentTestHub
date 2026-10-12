import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentTestHub | Agent 评测工作台",
  description: "多团队 Agent 质量评测、运行追踪与数据集管理工作台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
