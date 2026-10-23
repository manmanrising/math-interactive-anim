# math-interactive-anim

> 一个通用 `SKILL.md` 技能：把一道数学题，变成「手指拖动就能看懂」的单个 HTML 动图。零依赖、可离线、手机直接打开。WorkBuddy / Claude Code / Cursor 等支持 SKILL.md 的工具都能用。

**🎬 在线演示（手机直接开，无需安装）**：https://manmanrising.github.io/math-interactive-anim/

## 📸 截图这张卡，发给你的 AI，它自己装好并用起来

<img src="share/ai-card.png" alt="截图这一页，交给你的 AI 助手" width="560">

不用懂命令行。把上面这张图整张发给任意 AI（Claude Code / WorkBuddy / Cursor / 豆包…），它就能自己下载、放进技能目录、按 `SKILL.md` 的流程帮你出图。

## 这是什么

给它一道题（文字或截图），它产出**一个零外部依赖的 HTML 文件**：拖动滑块实时看动点 / 图形 / 数值变化，一键跳到关键答案时刻，并附完整文字解题过程。面向初中、高中数学。

## 特性

- **零依赖**：不引任何 CDN / 字体 / 库，`file://` 双击即开，绝不白屏
- **移动端友好**：`viewport` 自适应 + 原生滑块 / 按钮，手机浏览器直接拖
- **离线可用**：纯 SVG + 原生 JS，断网也能用
- **答案可跳转**：动图比死图强的核心，点按钮直达答案时刻
- **读数实时刷新**：参数一变，关键量同步更新

## 覆盖题型

一维数轴动点 · 单参数平面动点 · 图形性质验证 · 折叠与对称 · 动点最值 · 轨迹 · 函数与面积 · 旋转位似

## 安装

技能遵循通用 `SKILL.md` 规范，各平台动作一致：下载解压 → 放进技能目录 → 新开对话。

| 平台 | 技能目录 |
|---|---|
| Claude Code | `~/.claude/skills/math-interactive-anim/` |
| WorkBuddy | `~/.workbuddy/skills/math-interactive-anim/` |
| 其他支持 SKILL.md 的工具 | 该工具自己的 skills 目录 |
| 网页版 / 手机版 AI | 无技能目录，直接让它读 `SKILL.md` 按流程执行 |

装好后新开对话，发一道题，例如："把这道题做成动图：……"

技能会生成 HTML 并交付（WorkBuddy 走 `present_files`，其他环境直接保存文件给你），双击 HTML 打开，或在手机浏览器打开。

## 动图怎么用 / 分享

- **电脑**：双击 HTML 文件
- **手机**：通过微信 / 网盘传到手机，用浏览器打开（微信内需「用其他应用打开」）
- **永久链接**：已开 GitHub Pages，手机浏览器 / 微信直接打开 <https://manmanrising.github.io/math-interactive-anim/>，扫码即看

## 目录结构

```
math-interactive-anim/
├── SKILL.md                        # 技能定义（WorkBuddy 读取）
├── assets/
│   ├── template.html               # 通用模板，复制后只改 A/B 两区
│   ├── example-numberline.html     # 一维数轴动点完整范例
│   └── example-parabola.html       # 二维抛物线面积完整范例
├── references/
│   ├── patterns.md                 # 八类题型建模对照
│   └── pitfalls.md                 # 渲染 / 测试坑与解法
├── scripts/
│   └── check_anim.py               # 一键自检（语法 / 运行时 / 结构 / 读数）
├── LICENSE
└── README.md
```

## 自检

写完动图后运行：

```bash
python scripts/check_anim.py 你的文件.html
```

全绿（无 ❌）即可交付。

## 许可证

[MIT](LICENSE) © 2026 大壮 (DaZhuang)

## ⭐ 欢迎 Star

如果这个技能帮你把题讲清楚了，点个 Star，让更多人发现它。
