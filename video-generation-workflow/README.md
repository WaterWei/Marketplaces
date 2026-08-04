# Video Generation Workflow Skill

默认语言：中文  
Default language: Chinese

把一句视频需求、一篇实操文章、一个产品介绍，变成可执行的视频生产流程：先问清楚目标和风格，再拆脚本和分镜，再生成视觉预演 prompt，最后用 HyperFrames / Remotion / HTML / React 这类代码驱动方式生成可渲染的视频场景。

这个 skill 的核心不是“写一个视频 prompt”，而是帮 Codex 像一个视频制作项目经理一样工作：边问边定方向，边拆边执行，尽量把审美判断、内容判断、工程实现拆开。

## 适合做什么

- 把实操文章改成教程视频
- 把产品介绍改成产品演示视频
- 把工具教程改成小红书 / 抖音 / YouTube 视频
- 生成分镜表、口播稿、字幕稿、视觉预演图 prompt
- 指导 Codex 用 HyperFrames / Remotion / HTML / React 复刻视觉并导出视频
- 生成多种背景风格方向，形成可复用背景图库
- 给客户先出视频方案，再按客户反馈逐镜头微调

## 默认输出方向

当用户没有指定画幅时，skill 会先让客户选择：

- `16:9 横版`：YouTube、Bilibili、产品演示、课程、客户汇报，默认选择
- `9:16 竖版`：小红书、抖音、TikTok、Reels、Shorts
- `1:1 方版`：信息流、广告预览、跨平台复用

如果用户不选，默认按 `16:9 横版视频` 做。

## 安装

把本仓库复制到 Codex skills 目录：

```bash
git clone https://github.com/NickQi688/video-generation-workflow.git ~/.codex/skills/video-generation-workflow
```

之后在 Codex 里可以这样调用：

```text
用 $video-generation-workflow 把这篇文章做成一个 16:9 横版视频。
```

或者：

```text
用 $video-generation-workflow 帮我把这个产品介绍做成客户演示视频，中途可以问我问题。
```

## 工作流

1. 判断输入类型：短需求、实操文章、产品 brief、已有脚本。
2. 先问关键问题：平台画幅、目标观众、风格参考、旁白方式、可用素材。
3. 生成视频 brief：标题、目标、时长、风格、声音、风险点。
4. 拆分镜：每一镜的时长、画面任务、字幕、构图、动效、声音。
5. 生成口播文案和字幕稿：默认输出完整口播、逐镜头口播、字幕版。
6. 生成视觉预演 prompt：先定视觉，不急着写代码。
7. 预览图确认：客户确认后再进入代码动画，除非明确要求自动推进。
8. 代码复刻场景：文字、数字、UI、图表、动效用代码实现；图片只做参考、背景、人物、产品素材。
9. 单镜头预览和微调：每次只改最关键的问题。
10. 最终装配：检查时长、画幅、字幕可读性、音画同步、导出格式。

## 为什么要先出视觉预演图

只说“高级、科技感、简洁”通常不够，因为 AI 会把这些词理解成很多不同方向。

这个 skill 倾向于先让 Codex 生成每个关键场景的视觉预演 prompt，必要时用图像模型出一张参考图。视觉方向确认后，再把图交给 Codex 复刻成代码动画。

分工原则：

- 图片生成：背景纹理、人物插图、产品 cutout、气氛参考、关键帧参考
- 代码实现：文字、数字、图表、UI、布局、字幕、时间轴、动效

这样做的好处是：视觉判断和工程实现分开，客户也更容易给反馈。

## 预览图要不要确认？

要。默认规则是：关键场景预览图生成后，先让用户或客户确认，再进入代码动画制作。

推荐确认方式：

```text
我已经生成了视觉预览方向，请确认：
1. 通过：继续做代码动画
2. 修改风格：告诉我哪里要改
3. 多出几版：指定要多出哪一镜或哪种风格
```

只有在用户明确说“自动推进”“不用确认”“你直接做完”时，才跳过确认。客户项目默认不跳过。

## 要不要做背景图库？

建议做，但不要一开始塞太多图片。更好的方式是先建立“背景风格库”和 prompt 模板，等某个方向被客户认可后，再沉淀成项目资产。

本仓库提供了背景图库参考：

```text
references/background-library.md
```

建议先准备这些方向：

- 干净产品渐变
- 纸张纹理 / 编辑部风
- 深色数据看板 / 终端风
- 柔和产品棚拍
- 极简网格 / 技术图
- 温暖教学 / 新手教程
- 电影感抽象背景

背景只负责氛围和层次，不负责承载重要文字。重要文字、数字、UI 和图表仍然应该用代码渲染。

## 要不要生成口播文案？

要。默认应该一起生成，因为视频交付不只是画面，还包括“怎么说”。

默认交付三种文本：

- 完整口播稿：适合配音或真人录制
- 逐镜头口播稿：和分镜时间轴对应
- 字幕稿：更短，更适合直接上屏

如果用户明确说“无旁白”“纯字幕”“只要画面”，再改成只生成字幕稿。

## 案例：把 OpenCode 实操文章做成视频

示例目录：

```text
examples/opencode-free-ai/
```

案例来源是一篇面向学生和小白的 OpenCode 教程文章。文章很长，包含工具定位、免费模型、Mac / Windows 安装、Oh-My-Opencode、三个小测试等内容。

实际视频没有硬塞完整教程，而是提炼成一条更适合信息流的主线：

> 新手不需要一开始追最贵、最复杂的 AI 工具。先用 OpenCode + 免费模型跑通一个每天能打开、能练、能干活的 AI 助手。

案例成片：

```text
examples/opencode-free-ai/out/opencode-free-ai-assistant.mp4
```

抽帧预览：

```text
examples/opencode-free-ai/out/contact-sheet.jpg
```

重新生成案例视频：

```bash
cd examples/opencode-free-ai
npm install
npm run render
```

这个案例当前是 `9:16` 竖版，用来演示短视频平台版本。正式给客户做时，可以让客户先选 `16:9`、`9:16` 或 `1:1`，不指定时默认按 `16:9` 横版方案输出。

## 示例请求

```text
用 $video-generation-workflow 把下面这篇文章做成 16:9 横版视频。
目标观众是刚接触 AI 工具的大学生。
视频不要太像安装教程，更像一个工具启蒙短片。
中途如果风格不确定，可以问我问题。
```

```text
用 $video-generation-workflow 帮我做一个产品演示视频。
先给客户 3 个风格方向选择，再拆分镜和视觉预演 prompt。
默认横版 16:9，控制在 60 秒内。
```

```text
用 $video-generation-workflow 把这篇小红书图文改成竖版视频。
保留爆点，但不要照搬全文。
先给我分镜表，我确认后再生成代码动画。
```

## 文件结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── prompt-patterns.md
│   └── background-library.md
└── examples/
    └── opencode-free-ai/
        ├── generate-video.js
        ├── package.json
        ├── production-notes.md
        └── out/
            ├── contact-sheet.jpg
            └── opencode-free-ai-assistant.mp4
```

## 注意

- 不要把重要文字直接做进 AI 生成图里，后期不可控。
- 视频脚本不要照搬长文章，要转成“观众能看懂的行动路径”。
- 每次反馈尽量具体，例如“标题缩小 10%”“卡片延后 0.5 秒出现”“改成 16:9 横版产品演示风格”。
- 如果需要安装视频渲染依赖，先让 Codex 说明方案，再执行。

---

# English Overview

Default language for this skill is Chinese, but it can work with Chinese or English requests.

Video Generation Workflow turns a vague video request, a practical article, or a product brief into an executable AI video production workflow. It helps Codex clarify the creative direction, extract the story, build a scene-by-scene storyboard, generate visual preview prompts, and implement code-driven animated scenes with tools such as HyperFrames, Remotion, HTML, React, or similar renderable stacks.

The point of this skill is not to write one generic video prompt. It is designed to make Codex behave more like a video production lead: ask the right questions, separate taste decisions from implementation, lock the visual direction before coding, and iterate scene by scene.

## What It Is For

- Turn how-to articles into tutorial videos
- Turn product descriptions into product demo videos
- Turn tool guides into Xiaohongshu, Douyin, TikTok, YouTube, or Bilibili videos
- Generate storyboards, voiceover scripts, subtitle scripts, and image-generation prompts
- Guide Codex to recreate approved visuals as code-driven animated scenes
- Generate multiple reusable background style directions and background-library prompts
- Prepare client-facing video concepts, then revise by scene based on feedback

## Default Format

When the target platform or aspect ratio is unclear, the skill should ask the client to choose:

- `16:9 horizontal`: YouTube, Bilibili, product demos, courses, client presentations. This is the default.
- `9:16 vertical`: Xiaohongshu, Douyin, TikTok, Reels, Shorts.
- `1:1 square`: feed posts, ads, and cross-platform previews.

If the user does not choose, the default output is a `16:9 horizontal video`.

## Installation

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/NickQi688/video-generation-workflow.git ~/.codex/skills/video-generation-workflow
```

Example invocation:

```text
Use $video-generation-workflow to turn this article into a 16:9 horizontal video.
```

Or:

```text
Use $video-generation-workflow to create a client-facing product demo video. Ask me questions whenever the style is unclear.
```

## Workflow

1. Classify the input: short request, practical article, product brief, or existing script.
2. Ask only the highest-impact questions: format, audience, style reference, voiceover mode, and available assets.
3. Create a video brief: title, target viewer, duration, visual style, sound direction, required assets, and risks.
4. Build a scene table: duration, viewer job, on-screen text, composition, motion, assets, and sound cues.
5. Generate the voiceover script and subtitle script by default.
6. Generate visual preview prompts before writing code.
7. Ask for approval after preview images are generated, unless the user explicitly requested automatic execution.
8. Recreate the approved scene in code: text, data, UI, charts, timing, and animation should be code-rendered.
9. Review and revise one scene at a time.
10. Assemble the final video and verify duration, aspect ratio, readability, audio sync, and export settings.

## Why Visual Previews Come First

Words like “premium”, “techy”, or “minimal” are too vague. The skill encourages Codex to generate still-frame visual preview prompts first. Once the visual direction is approved, Codex can recreate the layout and animation in code.

Recommended division of labor:

- Image generation: background textures, editorial characters, product cutouts, atmospheric references, keyframe previews.
- Code rendering: text, numbers, charts, UI, layout, subtitles, timeline, and animation.

This keeps creative approval and technical implementation separate, which makes client feedback easier to handle.

## Should Visual Previews Be Confirmed?

Yes. The default rule is to pause after key visual previews are generated and ask the user or client to approve them before building code-driven animation.

Only skip this step when the user explicitly says to continue automatically. For client work, do not skip it by default.

## Should There Be A Background Library?

Yes, but start with a lightweight style library rather than a huge asset dump.

This repository includes:

```text
references/background-library.md
```

Recommended directions:

- Clean product gradient
- Paper grain / editorial
- Dark analytics / terminal
- Soft studio product
- Minimal grid / technical
- Warm education / tutorial
- Cinematic abstract

Backgrounds should provide atmosphere and depth only. Important text, numbers, UI, and charts should remain code-rendered.

## Should Voiceover Scripts Be Generated?

Yes. By default, the skill should generate:

- Full voiceover script
- Per-scene voiceover script
- Short subtitle script

If the user requests a silent or text-only video, generate subtitles only.

## Example: OpenCode Article To Video

Example folder:

```text
examples/opencode-free-ai/
```

The source was a long OpenCode tutorial for students and beginners. Instead of squeezing the whole tutorial into one video, the case study extracted one clear message:

> Beginners do not need the most expensive or complex AI toolchain first. Start with OpenCode plus free models, and build a daily AI assistant that can actually help with work.

Rendered example video:

```text
examples/opencode-free-ai/out/opencode-free-ai-assistant.mp4
```

Contact sheet:

```text
examples/opencode-free-ai/out/contact-sheet.jpg
```

Re-render the example:

```bash
cd examples/opencode-free-ai
npm install
npm run render
```

This example is currently a `9:16` vertical short video. For client work, the skill should offer `16:9`, `9:16`, and `1:1`; if the user does not choose, it defaults to `16:9`.

## Example Prompts

```text
Use $video-generation-workflow to turn the article below into a 16:9 horizontal video.
The audience is college students who are new to AI tools.
Do not make it feel like a dry installation tutorial. Make it feel like a tool discovery video.
Ask me questions whenever the style is unclear.
```

```text
Use $video-generation-workflow to create a product demo video.
Give the client 3 style directions first, then build the storyboard and visual preview prompts.
Default to 16:9 horizontal and keep it under 60 seconds.
```

## Notes

- Do not bake important text into generated images; keep text editable and code-rendered.
- Do not copy long articles directly into video scripts; convert them into a clear viewer journey.
- Make feedback specific: “reduce the title size by 10%”, “delay the card by 0.5s”, or “switch this to a 16:9 product demo style”.
- If rendering dependencies are needed, have Codex explain the implementation plan before installing them.
