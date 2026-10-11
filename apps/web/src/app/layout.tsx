import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentTestHub - 行业领先的下一代多智能体协作式 Agent 评测平台",
  description: "基于多智能体考官动态博弈、美团二元 Rubric 陪审团与阿里 7-Hop 全链路精细化评测平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="antialiased bg-obsidian-950 text-slate-100">{children}</body>
    </html>
  );
}
