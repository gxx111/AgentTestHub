import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AgentTestHub · Agent 发布门禁",
  description:
    "用可复现的仿真环境、带证据的轨迹裁决和 CI 集成，在发布前回答这个 Agent 版本能不能上线。",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
