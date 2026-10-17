# 07 · 前端架构与重构方案

> 版本：1.0  
> 更新：2026-10-17  
> 状态：有效  
> 负责人：前端 / 设计

---

## 1. 重构目标

1. **全部重写**旧前端页面与组件，不复用旧布局、旧 CSS、旧演示数据。
2. 以"证据优先、发布门禁"为信息架构，而不是"竞技场/大屏"。
3. 建立可维护的设计系统与组件层，消灭巨型 `page.tsx` 和内联组件。
4. 只依赖真实后端能力；未实现的能力明确标注"实验性/规划中"。
5. 支持桌面与移动端，具备空状态、加载、错误、权限处理。

### 1.1 非目标

- 不在本次重构中实现新的后端能力（异步任务、SSE、在线评估等）。
- 不重写评测引擎。
- 不引入重型 UI 框架；使用 Tailwind + 轻量自建组件。

---

## 2. 信息架构

```text
登录 / 注册
└── 应用外壳（侧边栏 + 顶栏 + 内容区）
    ├── 概览
    ├── 评测实验
    │   ├── 实验详情 / 运行报告
    │   └── 运行历史
    ├── Agent 资产
    ├── 数据集
    ├── 评测团队
    └── 工作区设置
```

### 2.1 导航

| 分组 | 页面 | 路由 |
|---|---|---|
| 工作台 | 概览 | `/overview` |
| 工作台 | 评测实验 | `/evaluations` |
| 资产 | Agent 资产 | `/agents` |
| 资产 | 数据集 | `/datasets` |
| 资产 | 评测团队 | `/teams` |
| 治理 | 工作区设置 | `/settings` |

- 登录页：`/login`
- 根路径 `/`：根据登录状态重定向。
- 实验详情：`/evaluations/experiments/[id]`
- 运行详情：`/evaluations/runs/[id]`

---

## 3. 设计系统

### 3.1 视觉方向

- **企业、克制、可信**：浅色内容区 + 深色侧边栏。
- 主色：蓝色（操作/链接），绿色（通过），琥珀（警告），红色（失败）。
- 不使用霓虹、发光、渐变堆叠、夸张动画。
- 数据密度适中；表格和证据优先于装饰。

### 3.2 Tokens

```css
--bg: #f6f7f9;
--surface: #ffffff;
--surface-subtle: #f9fafb;
--border: #e5e7eb;
--border-strong: #d1d5db;
--text: #0f172a;
--muted: #64748b;
--primary: #2563eb;
--primary-hover: #1d4ed8;
--success: #15803d;
--warning: #b45309;
--danger: #b91c1c;
--sidebar: #0b1220;
--sidebar-muted: #94a3b8;
--radius: 10px;
```

- 字体：系统 UI + Inter 回退；ID/代码用 `ui-monospace`。
- 间距：4/8/12/16/24/32。
- 卡片：白底、1px 边框、10px 圆角、无重阴影。
- 表格：行高 44px，表头 12px muted，hover 浅灰。

### 3.3 组件清单

| 组件 | 文件 | 说明 |
|---|---|---|
| Button | `components/ui/button.tsx` | primary/secondary/ghost/danger，loading |
| Input/Textarea/Select | `components/ui/field.tsx` | label、hint、error |
| Modal | `components/ui/modal.tsx` | 可关闭、ESC、滚动 |
| Badge | `components/ui/badge.tsx` | 状态/类型 |
| Card | `components/ui/card.tsx` | 容器 |
| EmptyState | `components/ui/empty-state.tsx` | 空状态 + CTA |
| Spinner | `components/ui/spinner.tsx` | 加载 |
| Toast | `components/ui/toast.tsx` | 全局提示 |
| PageHeader | `components/ui/page-header.tsx` | 标题/描述/操作 |
| StatCard | `components/ui/stat-card.tsx` | 指标卡 |
| Tabs | `components/ui/tabs.tsx` | 页内切换 |
| Sidebar | `components/layout/sidebar.tsx` | 导航/工作区/用户 |
| Topbar | `components/layout/topbar.tsx` | 面包屑/状态 |
| AppShell | `components/layout/app-shell.tsx` | 组合布局 |
| TraceViewer | `components/evaluations/trace-viewer.tsx` | 事件时间线 |
| ExperimentReport | `components/evaluations/experiment-report.tsx` | 报告主体 |

---

## 4. 代码结构

```text
apps/web/src/
├── app/
│   ├── layout.tsx                 # 根布局/metadata
│   ├── globals.css                # tokens + 基础样式
│   ├── page.tsx                   # 重定向
│   ├── login/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx             # Auth + AppShell
│       ├── overview/page.tsx
│       ├── agents/page.tsx
│       ├── datasets/page.tsx
│       ├── evaluations/page.tsx
│       ├── evaluations/experiments/[id]/page.tsx
│       ├── evaluations/runs/[id]/page.tsx
│       ├── teams/page.tsx
│       └── settings/page.tsx
├── components/
│   ├── ui/                        # 设计系统
│   ├── layout/                    # 外壳
│   ├── agents/                    # Agent 表单/卡片
│   ├── datasets/                  # 数据集/用例表单
│   ├── evaluations/               # 启动面板/报告/Trace
│   └── teams/                     # 团队表单
├── lib/
│   ├── api.ts                     # API client
│   ├── auth.tsx                   # AuthProvider/useAuth
│   ├── types.ts                   # API 类型
│   ├── format.ts                  # 格式化
│   └── utils.ts                   # cn 等
└── hooks/
    └── use-resource.ts            # 数据获取 hook
```

### 4.1 约束

- 页面文件只做组合，不写复杂表单/表格逻辑。
- 所有 API 调用走 `lib/api.ts`，组件不直接 `fetch`。
- 所有类型来自 `lib/types.ts`，禁止 `any`（必要时 `unknown` + 收窄）。
- 所有日期/百分比/耗时走 `lib/format.ts`。
- 组件默认 client（需要数据/交互），静态展示可为 server。

---

## 5. 数据与状态

### 5.1 Auth

- `AuthProvider` 读取 `localStorage` 的 `ath_token` / `ath_workspace`。
- 启动时调用 `/auth/me` 校验；失败则清空并跳转 `/login`。
- 登录/注册成功后保存 token、workspace，跳转 `/overview`。
- 多工作区：侧边栏切换，更新 `ath_workspace` 并刷新页面。

### 5.2 数据获取

- `useResource(key, fetcher)`：返回 `data/loading/error/refresh`。
- 页面级刷新；写操作成功后调用 `refresh`。
- 不做全局缓存（后续可引入 TanStack Query）。
- 请求失败显示错误 + 重试；不静默吞错。

### 5.3 长任务

- `universal-run` 当前是同步接口。前端：
  - 提交后显示"运行中"与计时器。
  - 并行轮询 `/evaluations/streams/{stream_id}` 展示事件计数/最新事件。
  - 完成后刷新实验列表并跳转详情。
  - 明确提示"请勿关闭页面；后续版本将改为后台任务"。

---

## 6. 页面规格

### 6.1 登录

- 左侧品牌/定位/三条价值点；右侧登录/注册 tabs。
- 字段：邮箱、密码、姓名（注册）。
- 错误：401/409/422 显示可读信息。
- 成功后跳转。

### 6.2 概览

- 4 个指标：Agent 数、数据集数、实验数、最近实验通过率。
- 最近实验表：状态、Agent/数据集、通过率、重复数、时间。
- 右侧：发布门禁摘要、快速开始。
- 空状态：引导创建 Agent/数据集/团队。

### 6.3 Agent 资产

- 卡片列表：名称、类型、模型、描述、密钥状态。
- 操作：编辑、删除、测试连接。
- 新建/编辑：类型、模型、API Base、API Key、Webhook、描述、System Prompt、工具 JSON（高级）。
- `mas_team` 标注"实验性，暂不可执行"。

### 6.4 数据集

- 左列表 + 右详情。
- 数据集：名称、领域、描述、init_sql、用例数。
- 用例：标题、类别、prompt、预期状态、Rubric。
- 新建/编辑：JSON 文本域（带校验与模板）。
- 支持从数据集跳转评测。

### 6.5 评测实验

- 启动面板：Agent、数据集、策略、评测团队、重复次数、单用例。
- 运行状态：计时、事件数、最新事件、取消提示（当前后端不支持取消，标注）。
- 实验列表：状态、通过率、平均分、重复、flaky、时间。
- 运行历史：单次运行列表。
- 详情：摘要、case stability、失败证据、Trace。

### 6.6 评测团队

- 团队列表：成员角色、模型、最大轮次/超时/调用预算。
- 新建/编辑：4 个必选角色 + 1 个可选红队；模型/API Base/Key；启用开关。
- 说明：真实 LLM 调用、预算与超时、密钥加密。

### 6.7 设置

- 工作区信息、成员列表、邀请成员（邮箱/角色）。
- 当前用户、API 地址、退出登录。
- 文档链接。

---

## 7. 可访问性与响应式

- 所有交互可键盘操作；Modal 焦点管理 + ESC。
- 颜色对比度满足 WCAG AA；状态不只靠颜色，配合文字/图标。
- 移动端：侧边栏抽屉；表格横向滚动；按钮触达 ≥ 40px。
- 空状态、错误、加载均有明确文案。

---

## 8. 性能

- 首屏 JS 目标 < 150KB（gzip）。
- 列表超过 50 条时分页/虚拟化（当前数据量小，先分页）。
- 图片/图标使用 lucide，避免大图。
- 不在客户端引入大型图表库；概览用 CSS 柱状图。

---

## 9. 旧前端清理

删除：

- `app/page.tsx` 旧单页应用。
- `components/arena`、`components/comparison`、`components/datasets`、`components/matrix`、`components/runs`、`components/studio`、`components/teams`、`components/trace`、`components/layout/Header.tsx`。
- 旧 `globals.css` 的 cyber/obsidian 样式。
- 硬编码演示数据组件与假报告。

保留：

- `package.json` 依赖（后续再裁剪 `@xyflow/react`）。
- 后端 API、`run_dev` 脚本。

---

## 10. 验收标准

- [ ] 旧页面/组件全部移除，无引用。
- [ ] 7 个页面路由可用，登录守卫生效。
- [ ] 所有列表/表单对接真实 API。
- [ ] 无硬编码演示数据。
- [ ] `npm run build` 通过，TypeScript strict 无错误。
- [ ] 桌面/移动端基本可用。
- [ ] 空/错/加载状态完整。
- [ ] 文档更新（本文件 + README）。
