---
name: video-generation-workflow
description: "Turn vague video requests, product ideas, or practical how-to articles into a complete AI video production workflow: clarify the desired style through iterative questions, extract story and scenes, draft scripts and storyboards, generate visual preview prompts for image models, implement code-driven animated scenes with HyperFrames/Remotion-style HTML/React, add sound direction, preview, critique, and iterate. Use when Codex is asked to make a video, convert an article into a video, create social/product/demo/tutorial video assets, generate video prompts, plan AI video production, or guide a user through Codex + image generation + HyperFrames video creation."
---

# Video Generation Workflow

## Operating Principle

Separate taste decisions from production work. First clarify the intended viewer, promise, style, and scene logic; then create visual previews; then recreate text, layout, numbers, UI, and animation in code. Use generated images for references, textures, product cutouts, people, or backgrounds, but keep readable text and timing in code.

The user explicitly allows iterative questioning. Ask questions whenever style, audience, content accuracy, assets, or platform constraints are under-specified. Keep each question round small: ask the 1-3 highest-leverage questions, then continue with the best current assumptions.

## Workflow

### 1. Classify the Input

Identify the source type:

- **Short request**: infer the concept, ask for audience/platform/style if missing.
- **Practical article or notes**: extract the core transformation, steps, proof points, examples, and teachable moments.
- **Product/demo brief**: identify product, user pain, before/after, core UI states, and proof.
- **Existing script**: preserve intent, improve visual structure and pacing.

If the input is an article, do not merely summarize it. Convert it into a video argument: hook, tension, method, proof, payoff.

### 2. Ask the First Clarifying Round

Ask only what materially changes the output. Prefer these questions:

1. Target platform and aspect ratio: 9:16, 16:9, 1:1, or custom.
2. Target viewer and desired action after watching.
3. Reference style: product launch, dark analytics dashboard, documentary, tutorial screen recording, cinematic, editorial, minimal tech, etc.
4. Voice: narrated, text-only, talking-head support, or silent with captions.
5. Assets available: screenshots, logos, product images, screen recordings, data, brand colors, music.

If the user says "you decide", choose a strong default and state it briefly.

### 3. Build a Video Brief

Produce a concise brief before implementation:

- Title or working concept
- Target audience
- Platform, aspect ratio, target duration
- Core promise in one sentence
- Visual style and pacing
- Sound direction
- Voiceover mode and narration style
- Required assets and missing assets
- Risk list: unclear claims, unavailable assets, text too dense, too many scenes, weak hook

For short social videos, prefer 15-45 seconds. For tutorials, allow longer only when each step needs screen time.

### 4. Extract Story Into Scenes

Create a scene table. Each scene must have:

- Scene number and duration
- Viewer job: what this scene must make the viewer understand or feel
- Voiceover script
- On-screen text
- Visual composition
- Motion/timing
- Assets needed
- Sound cues

Use few scenes with clear transitions. A strong 30-second video often has 4-6 scenes.

Also produce a voiceover package unless the user explicitly asks for a silent video:

- Full voiceover script
- Per-scene voiceover script
- On-screen subtitle version
- Optional shorter cut for fast-paced short videos

### 5. Generate Visual Preview Prompts

Before coding visually complex scenes, create still-image prompts to lock layout, mood, and hierarchy. Read [references/prompt-patterns.md](references/prompt-patterns.md) for reusable prompt patterns.

Generate one prompt per scene or per key frame. After preview images are generated, pause and ask the user to approve or revise the direction before turning the scene into code, unless the user explicitly asked for fully automatic execution.

Use this confirmation format:

```text
I have the visual previews. Please confirm one:
1. Approved - continue to code-driven animation.
2. Revise style - tell me what to change.
3. Generate more options - specify which scene or style.
```

For low-risk internal drafts, Codex may continue after stating assumptions. For client work, always confirm the preview images before implementation.

Important split:

- Use image generation for: background texture, product cutouts, editorial characters, cinematic plates, rough visual references.
- Use code for: text, numbers, UI labels, charts, cards, cursor movement, transitions, animation timing.

Never bake important text into generated images unless the user explicitly wants a non-editable poster frame.

### 5.5. Use Or Build A Background Library

For repeated video work, maintain a small background library instead of regenerating every background from scratch. Read [references/background-library.md](references/background-library.md) when the user asks for multiple styles, brand variants, reusable assets, or client-facing options.

Recommended background library categories:

- Clean product gradient
- Paper grain / editorial
- Dark analytics / terminal
- Soft studio product
- Minimal grid / technical
- Warm education / tutorial
- Cinematic abstract

Generate 3-6 background directions when the style is uncertain. Ask the user to pick one direction before applying it across scenes. Backgrounds should stay low-distraction because text, charts, and UI will be rendered in code.

### 6. Implement Code-Driven Scenes

If HyperFrames is available, use it for HTML/code-driven video creation. If Remotion or a local video stack already exists in the repo, follow the existing stack. If no stack exists, create a minimal implementation plan first and ask before installing dependencies.

For each scene:

1. Analyze visual hierarchy before writing code.
2. Implement static layout first.
3. Add animation in the specified order.
4. Add real audio tracks or renderable audio assets where possible; do not rely on browser-only live sound for final export.
5. Preview and compare against the approved visual direction.

When asking Codex or another agent to implement a scene from a preview image, use this structure:

```text
Strictly recreate the uploaded preview image as a code-driven animated scene.

First do three things:
1. Analyze layout structure and visual hierarchy.
2. List the main components.
3. Confirm the animation order.

Then implement:
- Static layout first: colors, typography, spacing, radius, hierarchy.
- Animation second: [specific timing and sequence].
- Text, numbers, charts, labels, and UI must be code-rendered.
- Image assets are only for backgrounds, product cutouts, people, or textures.
- Keep this scoped to this scene.
```

### 7. Review and Iterate

Review one scene at a time. Give concrete feedback:

- Good: "Delay the annotation card until the chart fade-in completes."
- Good: "Change donut chart red to #b44040."
- Good: "The title is too large for mobile 9:16; reduce it and move the subtitle below."
- Weak: "Make it more premium."

If feedback is vague, convert it into testable visual changes and confirm.

### 8. Final Assembly

Before final delivery, check:

- All scene durations add up to target length.
- Text is readable at target platform size.
- No important text is baked into generated images.
- Audio cues match visual timing.
- Export settings match platform: aspect ratio, resolution, frame rate, format.
- Claims from the source article are preserved or clearly reframed.

Deliver both the final video artifact path and the production package when available: script, scene table, image prompts, asset list, implementation notes, and open questions.

The production package should include:

- Video brief
- Scene table
- Full voiceover script
- Subtitle script
- Visual preview prompts
- Background style choice or background library notes
- Asset list
- Implementation notes

## Interaction Style

Keep the user inside the creative loop without stalling production:

- Ask before major taste commitments.
- Continue after small uncertainties with explicit assumptions.
- Offer 2-3 style directions when the user has no reference.
- Use screenshots or still frames for feedback when available.
- Do not overfit to generic "AI tech" aesthetics; derive the style from audience, product, and message.

## Defaults

Offer the user a format choice when the target platform is unclear. If the user does not choose, use these defaults:

- Platform: 16:9 horizontal video
- Duration: 45 seconds
- Structure: hook -> problem -> workflow/proof -> result -> call to action
- Visual style: precise product/editorial, clean contrast, restrained motion
- Audio: instrumental background plus subtle UI/click/typing cues
- Captions: concise on-screen text, no paragraph blocks
- Voiceover: generate a clear default voiceover script unless the user requests text-only

Common format choices:

- 16:9 horizontal: YouTube, Bilibili, product demos, course clips, client presentations.
- 9:16 vertical: Xiaohongshu, Douyin, TikTok, Reels, Shorts.
- 1:1 square: feed posts, ads, cross-platform previews.

## Resources

- [references/prompt-patterns.md](references/prompt-patterns.md): image prompt templates, scene prompt structure, and implementation prompt snippets.
- [references/background-library.md](references/background-library.md): reusable background style categories and generation prompts.
