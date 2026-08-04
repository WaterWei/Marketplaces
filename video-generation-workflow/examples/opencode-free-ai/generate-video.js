const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const sharp = require("sharp");

const root = __dirname;
const framesDir = path.join(root, "frames");
const pngDir = path.join(root, "png-frames");
const outDir = path.join(root, "out");
fs.rmSync(framesDir, { recursive: true, force: true });
fs.rmSync(pngDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });
fs.mkdirSync(pngDir, { recursive: true });
fs.mkdirSync(outDir, { recursive: true });

const W = 1080;
const H = 1920;
const FPS = 24;
const DURATION = 40;
const TOTAL = FPS * DURATION;

const scenes = [
  { start: 0, end: 4.3, kind: "hook" },
  { start: 4.3, end: 9.4, kind: "fear" },
  { start: 9.4, end: 14.4, kind: "solution" },
  { start: 14.4, end: 20.2, kind: "model" },
  { start: 20.2, end: 26.2, kind: "firstday" },
  { start: 26.2, end: 32.6, kind: "agents" },
  { start: 32.6, end: 40, kind: "tests" },
];

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function clamp(v, min = 0, max = 1) {
  return Math.max(min, Math.min(max, v));
}

function ease(t) {
  t = clamp(t);
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function wrap(text, maxChars) {
  const lines = [];
  let line = "";
  for (const ch of text) {
    const n = /[A-Za-z0-9/._:-]/.test(ch) ? 0.55 : 1;
    const len = [...line].reduce((sum, c) => sum + (/[A-Za-z0-9/._:-]/.test(c) ? 0.55 : 1), 0);
    if (len + n > maxChars && line) {
      lines.push(line);
      line = ch;
    } else {
      line += ch;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function textBlock(text, x, y, size, color, maxChars, opts = {}) {
  const lines = wrap(text, maxChars);
  const weight = opts.weight || 700;
  const anchor = opts.anchor || "start";
  const lh = opts.lineHeight || size * 1.24;
  return lines
    .map((line, i) => {
      const yy = y + i * lh;
      return `<text x="${x}" y="${yy}" text-anchor="${anchor}" font-size="${size}" font-weight="${weight}" fill="${color}">${esc(line)}</text>`;
    })
    .join("\n");
}

function pill(x, y, w, h, label, color = "#e7fff6", stroke = "#70f2bd", text = "#10241d") {
  return `
  <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${h / 2}" fill="${color}" stroke="${stroke}" stroke-width="2"/>
  <text x="${x + w / 2}" y="${y + h / 2 + 12}" text-anchor="middle" font-size="34" font-weight="800" fill="${text}">${esc(label)}</text>`;
}

function card(x, y, w, h, rx = 34, fill = "#ffffff", opacity = 1) {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" opacity="${opacity}" filter="url(#shadow)"/>`;
}

function terminal(x, y, w, h, lines, p = 1) {
  const visible = Math.max(1, Math.floor(lines.length * clamp(p)));
  const body = lines.slice(0, visible).map((line, i) => {
    const color = line.startsWith("$") ? "#b7ffd6" : line.includes("free") ? "#80f4b7" : "#e6ecff";
    return `<text x="${x + 44}" y="${y + 116 + i * 58}" font-size="34" font-weight="650" fill="${color}">${esc(line)}</text>`;
  }).join("\n");
  return `
  <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="30" fill="#10141d" stroke="#2a3347" stroke-width="2" filter="url(#shadow)"/>
  <circle cx="${x + 42}" cy="${y + 42}" r="12" fill="#ff5f57"/>
  <circle cx="${x + 82}" cy="${y + 42}" r="12" fill="#ffbd2e"/>
  <circle cx="${x + 122}" cy="${y + 42}" r="12" fill="#28c840"/>
  ${body}`;
}

function bg(t) {
  const drift = Math.sin(t * 0.7) * 24;
  return `
  <rect width="${W}" height="${H}" fill="#f7f6ef"/>
  <circle cx="${150 + drift}" cy="200" r="260" fill="#c7f4dd" opacity="0.55"/>
  <circle cx="${940 - drift}" cy="520" r="330" fill="#d7d6ff" opacity="0.55"/>
  <circle cx="${250 - drift}" cy="1560" r="330" fill="#ffd6b8" opacity="0.5"/>
  <path d="M0 1450 C220 1370 390 1510 600 1430 C820 1340 940 1330 1080 1400 L1080 1920 L0 1920 Z" fill="#111827" opacity="0.05"/>
  <g opacity="0.12" stroke="#111827" stroke-width="1">
    ${Array.from({ length: 14 }, (_, i) => `<line x1="${i * 90}" y1="0" x2="${i * 90 - 260}" y2="${H}"/>`).join("")}
  </g>`;
}

function defs() {
  return `
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#111827" flood-opacity="0.16"/>
    </filter>
    <style>
      text { font-family: "PingFang SC", "Hiragino Sans GB", "Heiti SC", Arial, sans-serif; }
    </style>
  </defs>`;
}

function sceneFor(t) {
  return scenes.find((s) => t >= s.start && t < s.end) || scenes[scenes.length - 1];
}

function renderScene(kind, p, t) {
  const inY = 70 * (1 - ease(p * 2));
  const fade = ease(p * 2);
  if (kind === "hook") {
    return `
    <g opacity="${fade}" transform="translate(0 ${inY})">
      ${pill(86, 150, 300, 70, "学生党 / 小白")}
      <text x="86" y="360" font-size="78" font-weight="950" fill="#121826">不想每月花钱</text>
      <text x="86" y="458" font-size="78" font-weight="950" fill="#121826">养 AI 工具？</text>
      ${textBlock("先用 OpenCode 搭一个免费的 AI 助手。", 86, 610, 47, "#384152", 14, { weight: 750, lineHeight: 64 })}
      ${terminal(86, 780, 908, 390, ["$ opencode", "选择 free 模型", "开始让 AI 在电脑里干活"], ease((p - 0.28) / 0.5))}
      ${textBlock("这不是程序员专属教程。", 540, 1320, 44, "#121826", 14, { anchor: "middle", weight: 900 })}
      ${textBlock("是给想低成本体验 AI 自动化的人。", 540, 1390, 38, "#546071", 16, { anchor: "middle", weight: 700 })}
    </g>`;
  }
  if (kind === "fear") {
    const items = ["要买 Claude？", "要海外信用卡？", "要会编程？", "要折腾网络？"];
    return `
    <g opacity="${fade}" transform="translate(0 ${inY})">
      ${textBlock("很多人还没开始，先被成本劝退。", 86, 240, 62, "#121826", 13, { weight: 900, lineHeight: 82 })}
      ${items.map((it, i) => {
        const pp = ease((p - i * 0.12) / 0.42);
        const y = 500 + i * 180;
        return `<g opacity="${pp}" transform="translate(${(1 - pp) * 80} 0)">
          ${card(86, y, 908, 122, 34, "#ffffff", 0.96)}
          <text x="136" y="${y + 76}" font-size="43" font-weight="900" fill="#121826">${esc(it)}</text>
          <text x="914" y="${y + 76}" text-anchor="end" font-size="42" font-weight="900" fill="#d13f3f">先不用</text>
        </g>`;
      }).join("")}
      ${textBlock("第一步不是追最贵模型， 是先跑通。", 86, 1320, 58, "#121826", 13, { weight: 900, lineHeight: 78 })}
    </g>`;
  }
  if (kind === "solution") {
    return `
    <g opacity="${fade}" transform="translate(0 ${inY})">
      ${textBlock("OpenCode 可以先理解成：", 86, 250, 48, "#4b5563", 14, { weight: 800 })}
      ${textBlock("电脑里的免费 AI 助手工作台", 86, 350, 74, "#121826", 11, { weight: 950, lineHeight: 92 })}
      ${card(86, 600, 908, 520, 40, "#111827", 1)}
      <text x="138" y="700" font-size="42" font-weight="900" fill="#e8fff2">你直接用中文说：</text>
      <text x="138" y="815" font-size="42" font-weight="800" fill="#ffffff">帮我整理资料</text>
      <text x="138" y="910" font-size="42" font-weight="800" fill="#ffffff">帮我写小红书文案</text>
      <text x="138" y="1005" font-size="42" font-weight="800" fill="#ffffff">帮我做一个网页</text>
      <path d="M146 1210 L934 1210" stroke="#d6d3ff" stroke-width="3" opacity="0.6"/>
      ${textBlock("它会分析、规划、写脚本、改项目。", 86, 1305, 50, "#121826", 14, { weight: 900, lineHeight: 68 })}
    </g>`;
  }
  if (kind === "model") {
    return `
    <g opacity="${fade}" transform="translate(0 ${inY})">
      ${textBlock("重点：先用免费模型。", 86, 245, 68, "#121826", 12, { weight: 950 })}
      ${terminal(86, 430, 908, 660, ["$ /model", "GLM · free", "Kimi · free", "Minimax · low cost", "先选带 free 的"], ease((p - 0.12) / 0.6))}
      ${pill(130, 1190, 260, 72, "不用死记", "#fff", "#111827", "#111827")}
      ${pill(420, 1190, 360, 72, "看到 free 先选", "#111827", "#111827", "#ffffff")}
      ${textBlock("学习、整理资料、写内容、做小工具，第一天够用了。", 86, 1370, 50, "#121826", 14, { weight: 900, lineHeight: 70 })}
    </g>`;
  }
  if (kind === "firstday") {
    return `
    <g opacity="${fade}" transform="translate(0 ${inY})">
      ${textBlock("第一天别急着做大项目。", 86, 230, 66, "#121826", 12, { weight: 950 })}
      ${card(86, 430, 908, 210, 38, "#ffffff", 0.98)}
      <text x="136" y="520" font-size="42" font-weight="950" fill="#111827">01 先选免费模型</text>
      <text x="136" y="585" font-size="34" font-weight="780" fill="#536071">打开 /model，看到 free 先选</text>
      ${card(86, 710, 908, 210, 38, "#ffffff", 0.98)}
      <text x="136" y="800" font-size="42" font-weight="950" fill="#111827">02 先让它规划</text>
      <text x="136" y="865" font-size="34" font-weight="780" fill="#536071">先不要改文件，先说怎么做</text>
      ${card(86, 990, 908, 210, 38, "#ffffff", 0.98)}
      <text x="136" y="1080" font-size="42" font-weight="950" fill="#111827">03 再做小任务</text>
      <text x="136" y="1145" font-size="34" font-weight="780" fill="#536071">整理资料、改文案、写小脚本</text>
      ${textBlock("安装细节放正文，视频只讲行动路径。", 86, 1360, 48, "#121826", 15, { weight: 900, lineHeight: 66 })}
    </g>`;
  }
  if (kind === "agents") {
    const agents = ["规划", "查资料", "读代码", "前端", "调试"];
    return `
    <g opacity="${fade}" transform="translate(0 ${inY})">
      ${textBlock("想更像 AI 工作台？", 86, 230, 68, "#121826", 11, { weight: 950 })}
      ${textBlock("再装 Oh-My-Opencode。", 86, 335, 56, "#384152", 13, { weight: 850 })}
      ${card(86, 520, 908, 470, 42, "#111827", 1)}
      <text x="540" y="640" text-anchor="middle" font-size="48" font-weight="950" fill="#ffffff">一个助手，像带了小团队</text>
      ${agents.map((a, i) => {
        const pp = ease((p - i * 0.09) / 0.45);
        const x = 150 + (i % 2) * 390;
        const y = 740 + Math.floor(i / 2) * 92;
        return `<g opacity="${pp}" transform="translate(0 ${(1 - pp) * 28})">${pill(x, y, 300, 62, a, i % 2 ? "#d7d6ff" : "#c7f4dd", "transparent", "#111827")}</g>`;
      }).join("")}
      ${terminal(86, 1100, 908, 290, ["帮我安装并配置 oh-my-opencode", "没有付费模型也没关系", "优先使用免费模型"], ease((p - 0.38) / 0.48))}
    </g>`;
  }
  return `
  <g opacity="${fade}" transform="translate(0 ${inY})">
    ${textBlock("装好后，先做 3 个小测试。", 86, 220, 62, "#121826", 13, { weight: 950, lineHeight: 78 })}
    ${[
      ["01", "资料整理助手", "先规划分类，不急着移动文件"],
      ["02", "内容助手", "把文章改成小红书风格"],
      ["03", "自动化助手", "写脚本处理重复工作"],
    ].map((it, i) => {
      const pp = ease((p - i * 0.13) / 0.5);
      const y = 480 + i * 250;
      return `<g opacity="${pp}" transform="translate(${(1 - pp) * 70} 0)">
        ${card(86, y, 908, 170, 36, "#ffffff", 0.98)}
        <text x="136" y="${y + 74}" font-size="38" font-weight="950" fill="#7c6cff">${it[0]}</text>
        <text x="235" y="${y + 70}" font-size="43" font-weight="950" fill="#111827">${esc(it[1])}</text>
        <text x="235" y="${y + 124}" font-size="32" font-weight="760" fill="#536071">${esc(it[2])}</text>
      </g>`;
    }).join("")}
    ${textBlock("真正重要的不是最贵的 AI。", 86, 1330, 56, "#121826", 13, { weight: 950 })}
    ${textBlock("而是一个每天都能打开、能练、能帮你干活的助手。", 86, 1410, 44, "#384152", 15, { weight: 800, lineHeight: 62 })}
    <text x="540" y="1690" text-anchor="middle" font-size="42" font-weight="950" fill="#111827">下一篇：Skill 怎么让它更好用</text>
  </g>`;
}

function renderFrame(i) {
  const t = i / FPS;
  const s = sceneFor(t);
  const p = (t - s.start) / (s.end - s.start);
  const progress = t / DURATION;
  const bar = 86 + 908 * progress;
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
${defs()}
${bg(t)}
<rect x="54" y="54" width="972" height="1812" rx="58" fill="none" stroke="#111827" stroke-opacity="0.08" stroke-width="2"/>
${renderScene(s.kind, p, t)}
<rect x="86" y="1782" width="908" height="8" rx="4" fill="#111827" opacity="0.12"/>
<rect x="86" y="1782" width="${bar - 86}" height="8" rx="4" fill="#111827" opacity="0.72"/>
<text x="86" y="1844" font-size="30" font-weight="800" fill="#5b6472">OpenCode 免费 AI 助手入门</text>
</svg>`;
}

async function renderPngFrame(i) {
  const name = `frame_${String(i).padStart(4, "0")}`;
  const svg = renderFrame(i);
  fs.writeFileSync(path.join(framesDir, `${name}.svg`), svg);
  await sharp(Buffer.from(svg)).png().toFile(path.join(pngDir, `${name}.png`));
}

async function main() {
  const concurrency = 8;
  let next = 0;
  const workers = Array.from({ length: concurrency }, async () => {
    while (next < TOTAL) {
      const i = next++;
      await renderPngFrame(i);
      if (i % 120 === 0) console.log(`rendered frame ${i}/${TOTAL}`);
    }
  });
  await Promise.all(workers);

  const output = path.join(outDir, "opencode-free-ai-assistant.mp4");
  execFileSync("ffmpeg", [
    "-y",
    "-hide_banner",
    "-loglevel", "warning",
    "-framerate", String(FPS),
    "-i", path.join(pngDir, "frame_%04d.png"),
    "-f", "lavfi",
    "-i", "sine=frequency=95:duration=40:sample_rate=48000",
    "-f", "lavfi",
    "-i", "sine=frequency=420:duration=40:sample_rate=48000",
    "-filter_complex", "[1:a]volume=0.08[a1];[2:a]volume=0.015,atrim=0:40[a2];[a1][a2]amix=inputs=2:duration=shortest[a]",
    "-map", "0:v",
    "-map", "[a]",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-r", String(FPS),
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    output,
  ], { stdio: "inherit" });

  console.log(output);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
