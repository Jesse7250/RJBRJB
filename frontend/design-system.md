# 智慧伴学 EduMate 设计系统

## 1. 产品定位

- **产品类型**：EdTech / AI 个性化学习 Dashboard
- **目标用户**：Python 初学者、编程自学者
- **情绪关键词**：明亮、友好、可信赖、有动力、清晰

## 2. 设计语言

**Bento Grid + Soft Glassmorphism**

- 以卡片（Bento）为信息组织单元，避免文字堆砌。
- 卡片使用大圆角、柔和阴影、半透明玻璃质感。
- 背景使用低饱和渐变 + 细腻网格纹理，营造空间感。

## 3. 色彩系统

| Token | Hex | 用途 |
|-------|-----|------|
| Primary | `#4f46e5` (Indigo-600) | 主按钮、导航激活态、链接 |
| Primary Glow | `#7c3aed` (Violet-600) | 渐变、发光、强调 |
| Accent | `#f59e0b` (Amber-500) | 提示、星光、学习动力 |
| Success | `#10b981` (Emerald-500) | 通过、正确、就绪 |
| Warning | `#f59e0b` | 警告、注意 |
| Error | `#f43f5e` (Rose-500) | 错误、失败 |
| Background | `#f8fafc` + 渐变 | 页面背景 |
| Surface | `rgba(255,255,255,0.85)` | 卡片表面 |
| Text Primary | `#0f172a` (Slate-900) | 标题、正文 |
| Text Secondary | `#64748b` (Slate-500) | 次要文字 |

## 4. 字体系统

- **正文字体**：Inter, system-ui, sans-serif
- **代码字体**：JetBrains Mono, Fira Code, monospace
- **字号层级**：
  - Display: 1.875rem / 30px, font-bold
  - Title: 1.25rem / 20px, font-semibold
  - Body: 0.875rem / 14px, font-normal
  - Caption: 0.75rem / 12px, font-medium

## 5. 阴影与圆角

- 卡片圆角：`rounded-2xl` (16px)
- 按钮圆角：`rounded-xl` (12px)
- 小标签圆角：`rounded-lg` (8px) / `rounded-full`
- 主阴影：`0 8px 32px -4px rgba(79, 70, 229, 0.12)`
- 悬浮阴影：`0 12px 40px -6px rgba(79, 70, 229, 0.18)`

## 6. 动画规范

| 场景 | 时长 | Easing |
|------|------|--------|
| 卡片入场 | 0.4s | cubic-bezier(0.16, 1, 0.3, 1) |
| Hover 缩放 | 0.2s | ease-out |
| Tab 切换 | 0.2s | ease-in-out |
| 消息 stagger | 0.05s 间隔 | ease-out |
| 按钮 press | 0.1s | ease-out |

## 7. 组件模式

- **GlassCard**：白色半透明背景 + backdrop-blur + border + shadow，hover 时轻微上浮。
- **IconBox**：圆角方形彩色渐变背景，承载 Lucide 图标。
- **GradientText**：Indigo → Violet 渐变文字，用于标题强调。
- **Stepper**：资源生成阶段步骤条，每个步骤含图标、标签、完成态。
- **EmptyState**：居中插画 + 标题 + 描述 + 操作按钮。

## 8. 布局原则

- 左侧固定侧边栏（桌面），顶部玻璃导航（移动端）。
- 主内容区使用 Bento Grid：左侧大面板，右侧小部件卡片堆叠。
- 8px 网格倍数间距，留白充足。
- 所有交互元素最小点击区域 44px。
