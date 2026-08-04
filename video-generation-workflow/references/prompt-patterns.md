# Prompt Patterns

## Scene Table Template

```markdown
| # | Duration | Viewer job | On-screen text | Visual composition | Motion | Assets | Sound |
|---|---:|---|---|---|---|---|---|
| 1 | 0-4s | Hook the viewer | ... | ... | ... | ... | ... |
```

## Scene Table With Voiceover

```markdown
| # | Time | Viewer job | Voiceover | On-screen subtitle | Visual composition | Motion | Assets | Sound |
|---|---:|---|---|---|---|---|---|---|
| 1 | 0-4s | Hook the viewer | ... | ... | ... | ... | ... | ... |
```

## Voiceover Package Template

```markdown
## Full Voiceover

[Natural spoken script. Avoid sounding like a written article.]

## Per-Scene Voiceover

| # | Time | Voiceover | Subtitle |
|---|---:|---|---|
| 1 | 0-4s | ... | ... |

## Short Subtitle Cut

[Shorter text for on-screen captions, optimized for readability.]
```

Default to generating this package unless the user asks for a silent or text-only video.

## Visual Preview Prompt: UI Or Dashboard Scene

```text
A [interface type] in [aspect ratio] format, [tone and palette].
[Primary layout: left/right/top/bottom, hierarchy, chart/UI elements, exact numbers, colors]
Floating annotation card · [position] · semi-transparent dark background
+ white border · large: "[main label]" / small: "[supporting label]"
Minimal visual noise, no decorative elements.
Overall tone: [emotional direction].
```

Use for data dashboards, product UI, tool demos, and software explanation scenes. Keep all important text short because the final text should be recreated in code.

## Visual Preview Prompt: Product Demo Hero

```text
A premium product demo frame in [aspect ratio], [brand/product category].
Center: [main product/UI state], sharp and readable.
Background: [simple environment or texture], low distraction.
Foreground annotations: [1-3 callouts], clean hierarchy.
Lighting/color: [specific palette].
Overall tone: [credible, fast, calm, high-energy, clinical, etc.].
No fake logos, no unreadable dense text.
```

## Visual Preview Prompt: Editorial Character

```text
A [halftone / editorial / clean vector-like] character, [posture and expression].
Transparent background preferred.
No background objects, no text, no UI elements.
Minimum 1024px tall.
Style: product editorial illustration, not photo-realistic.
Avoid: dark muddy tones, heavy shadows, generic corporate clipart.
```

Use characters as overlay assets. Do not ask the image model to create the whole scene when code needs to control text and timing.

## Visual Preview Prompt: Background Texture

```text
A [aspect ratio] subtle background texture, [warm ivory / cool white / deep charcoal / paper grain / soft studio].
Extremely subtle; this will sit behind UI layers.
No patterns, no icons, no text, no focal point.
[target resolution].
Zero distracting elements.
```

## Background Style Choice Prompt

```text
Generate [3-6] background style directions for a [video type] in [aspect ratio].
The backgrounds must be low-distraction and contain no text, no logos, no icons, no UI, and no focal objects.
Provide options across these directions:
1. Clean product gradient
2. Paper grain editorial
3. Dark analytics / terminal
4. Soft studio product
5. Minimal grid / technical
6. Warm education / tutorial

For each option, describe:
- Best use case
- Palette
- Mood
- Why it fits the target viewer
- Image-generation prompt
```

After background previews are generated, ask the user to choose one direction before applying it across scenes.

## HyperFrames Opening Prompt Pattern

```text
Use HyperFrames to create a [video type] opening animation, [aspect ratio], under [duration].
Goal: [what the viewer should understand].
Start from [initial scene].
Animate [specific action] with [timing].
Then transition to [next scene].
Required elements: [text, icons, product, UI, data, assets].
Style: [visual references and constraints].
Sound: [music, typing, clicks, whooshes, narration]; use renderable audio tracks for final output.
Ensure it can render reliably to MP4.
```

## Scene Implementation Prompt Pattern

```text
Strictly follow this scene brief and any approved preview image.

First:
1. Analyze layout and visual hierarchy.
2. List components.
3. Confirm animation order.

Then implement:
- Static layout first.
- Animation second.
- Text, numbers, charts, labels, and UI are code-rendered.
- Image assets are only for backgrounds, product cutouts, people, or textures.
- Keep changes scoped to this scene.
```

## Feedback Translation

Turn vague feedback into concrete changes:

- "More premium" -> reduce clutter, increase spacing, simplify palette, sharpen typography, slow easing slightly.
- "More energetic" -> shorter scene durations, stronger cuts, snappier scale/slide motion, more percussion.
- "More trustworthy" -> less decoration, clearer data labels, calmer palette, fewer exaggerated claims.
- "More like a tutorial" -> cursor path, highlighted click targets, step counters, readable captions.
- "More cinematic" -> fewer UI labels, stronger camera movement, deeper contrast, sound swell, slower reveal.
