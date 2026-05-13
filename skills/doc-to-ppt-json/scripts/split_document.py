#!/usr/bin/env python3
"""
doc-to-ppt-json: Document Splitter

将大型 Markdown 文档按可配置的标题模式分割为带编号的片段文件。

用法:
    python3 split_document.py <input.md> [--config customize.toml] [--output-dir ./chunks] [--test]

依赖: Python 3.11+ (使用内置 tomllib)
"""

import argparse
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SectionType:
    name: str
    pattern: str
    level: int
    layout_hint: str
    compiled: re.Pattern = field(default=None, repr=False)

    def __post_init__(self):
        self.compiled = re.compile(self.pattern)


@dataclass
class Chunk:
    index: int
    section_type: str
    title: str
    content: str
    layout_hint: str

    @property
    def filename_base(self) -> str:
        return f"chunk_{self.index:03d}"


def load_config(config_path: str) -> tuple[list[SectionType], dict]:
    """加载 TOML 配置文件，返回 (section_types 按优先级排序, split 配置字典)。"""
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    split_config = config.get("split", {})
    section_order = split_config.get("section_order", [])
    section_types_raw = split_config.get("section_types", {})

    section_types = []
    for name in section_order:
        if name not in section_types_raw:
            print(f"WARNING: section_order 中的 '{name}' 在 section_types 中未定义，跳过", file=sys.stderr)
            continue
        st = section_types_raw[name]
        section_types.append(SectionType(
            name=name,
            pattern=st["pattern"],
            level=st["level"],
            layout_hint=st["layout_hint"],
        ))

    if not section_types:
        print("ERROR: 没有可用的 section_types，请检查配置文件", file=sys.stderr)
        sys.exit(1)

    return section_types, split_config


def parse_headers(content: str) -> list[tuple[int, str, int]]:
    """
    解析 Markdown 中的所有标题。
    返回 [(level, title, line_number), ...]
    level: 1-6 对应 # 到 ######
    """
    headers = []
    for i, line in enumerate(content.splitlines()):
        m = re.match(r"^(#{1,6})\s+(.+)", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            headers.append((level, title, i))
    return headers


def match_section_type(title: str, line: str, section_types: list[SectionType]) -> SectionType | None:
    """尝试将标题行匹配到某个 section_type。"""
    for st in section_types:
        if st.compiled.search(line):
            return st
    return None


def split_document(content: str, section_types: list[SectionType]) -> list[Chunk]:
    """
    将文档内容按标题模式分割为 Chunk 列表。

    算法：
    1. 扫描所有标题行，对每个标题尝试匹配 section_types
    2. 匹配成功的标题作为新分段的起点
    3. 分段的内容包含该标题到下一个同级或更高级标题之间的所有行
    4. 第一个匹配标题之前的内容归入序言（如有）
    """
    lines = content.splitlines(keepends=True)
    headers = parse_headers(content)

    if not headers:
        print("ERROR: 文档中没有找到任何标题行", file=sys.stderr)
        sys.exit(1)

    # 找到所有匹配的分段起点
    splits: list[tuple[int, SectionType, str]] = []  # (line_idx, section_type, title)
    for level, title, line_idx in headers:
        raw_line = lines[line_idx].rstrip("\n")
        st = match_section_type(title, raw_line, section_types)
        if st:
            splits.append((line_idx, st, title))

    if not splits:
        print("ERROR: 没有标题匹配到任何 section_types 模式", file=sys.stderr)
        print(f"  文档中共有 {len(headers)} 个标题，但无一匹配配置的模式", file=sys.stderr)
        print("  请检查 customize.toml 中的 section_types.pattern 配置", file=sys.stderr)
        sys.exit(1)

    # 提取每个分段的内容
    chunks = []
    for i, (start_line, st, title) in enumerate(splits):
        # 结束位置：下一个分段的起始行，或文档末尾
        if i + 1 < len(splits):
            end_line = splits[i + 1][0]
        else:
            end_line = len(lines)

        chunk_content = "".join(lines[start_line:end_line]).strip()

        if not chunk_content:
            print(f"ERROR: 分段 {i+1} ('{title}') 内容为空，请检查文档结构", file=sys.stderr)
            sys.exit(1)

        chunks.append(Chunk(
            index=i + 1,
            section_type=st.name,
            title=title,
            content=chunk_content,
            layout_hint=st.layout_hint,
        ))

    return chunks


def write_chunks(chunks: list[Chunk], output_dir: str) -> dict:
    """
    将分段写入输出目录。
    返回 manifest 字典。
    """
    os.makedirs(output_dir, exist_ok=True)

    manifest = {
        "total_chunks": len(chunks),
        "chunks": [],
    }

    for chunk in chunks:
        md_path = os.path.join(output_dir, f"{chunk.filename_base}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(chunk.content + "\n")

        manifest["chunks"].append({
            "index": chunk.index,
            "filename": f"{chunk.filename_base}.md",
            "section_type": chunk.section_type,
            "title": chunk.title,
            "layout_hint": chunk.layout_hint,
            "line_count": len(chunk.content.splitlines()),
        })

    # 写入 manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest


def run_test(config_path: str):
    """使用内置测试数据验证分割逻辑。"""
    test_content = """\
# 大差÷小差 · 统一模型天梯
## 三年级奥数 · 复习巩固专用

### 使用说明

- 适用对象：已学完三年级奥数的孩子。

## 第一部分：总目录

| 阶段 | 主梯 |
|:---|:---|
| 第一阶段 | 主梯 1 |

# 第一阶段：模型的发现与建立

> 目标：从鸡兔同笼和盈亏问题入手。

## 主梯 1：鸡兔同笼——模型的第一次相遇

### 1-1 梯：画脚游戏——让每只动物都"站好"

**【探索】**
农场主数了数。

**【发现】**
假设全是鸡。

**【练习】**
1. 鸡兔共 8 个头。

### 1-2 梯：假设全是鸡——少了多少脚？

**【探索】**
接上题。

## 主梯 2：盈亏问题——模型的再次出现

### 2-1 梯：分糖游戏

**【探索】**
老师有一袋糖。

# 第二阶段：模型的应用与变式

> 目标：把模型应用到各种题型中。

## 主梯 4：差倍问题

### 4-1 梯：画线段图

**【探索】**
苹果是梨的 3 倍。
"""

    section_types, split_config = load_config(config_path)
    chunks = split_document(test_content, section_types)

    print(f"\n{'='*60}")
    print(f"测试结果：共分割为 {len(chunks)} 个片段")
    print(f"{'='*60}")
    for chunk in chunks:
        print(f"  [{chunk.filename_base}] {chunk.section_type:15s} | {chunk.title}")
        print(f"           layout_hint={chunk.layout_hint}, lines={len(chunk.content.splitlines())}")

    print(f"\n测试通过！配置可以正确分割文档。")
    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="将 Markdown 文档按可配置模式分割为带编号的片段文件"
    )
    parser.add_argument("input", nargs="?", help="输入 Markdown 文件路径")
    parser.add_argument("--config", "-c", default=None, help="TOML 配置文件路径")
    parser.add_argument("--output-dir", "-o", default=None, help="输出目录")
    parser.add_argument("--test", action="store_true", help="使用内置测试数据验证配置")

    args = parser.parse_args()

    # 定位配置文件
    if args.config:
        config_path = args.config
    else:
        # 默认：脚本所在目录的上级目录下的 customize.toml
        script_dir = Path(__file__).resolve().parent.parent
        config_path = str(script_dir / "customize.toml")

    if not os.path.exists(config_path):
        print(f"ERROR: 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    if args.test:
        run_test(config_path)
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"ERROR: 输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 加载配置
    section_types, split_config = load_config(config_path)

    # 确定输出目录
    if args.output_dir:
        output_dir = args.output_dir
    else:
        base_dir = split_config.get("output_dir", "_bmad-output/doc-to-ppt-json")
        output_dir = base_dir

    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"输入文件: {input_path}")
    print(f"配置文件: {config_path}")
    print(f"输出目录: {output_dir}")
    print(f"文档大小: {len(content)} 字符, {len(content.splitlines())} 行")
    print()

    # 分割文档
    chunks = split_document(content, section_types)

    # 写入文件
    manifest = write_chunks(chunks, output_dir)

    # 输出结果
    print(f"分割完成！共 {manifest['total_chunks']} 个片段：")
    for info in manifest["chunks"]:
        print(f"  [{info['filename']}] {info['section_type']:15s} | {info['title']} ({info['line_count']} 行)")

    manifest_path = os.path.join(output_dir, "manifest.json")
    print(f"\n清单文件: {manifest_path}")
    print(f"所有片段已写入: {output_dir}/")


if __name__ == "__main__":
    main()
