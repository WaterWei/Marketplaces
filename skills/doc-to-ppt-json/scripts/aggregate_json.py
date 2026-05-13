#!/usr/bin/env python3
"""
doc-to-ppt-json: JSON Validator & Aggregator

两个子命令:
  --validate  : 逐片验证每个 chunk_NNN.json（语法 + schema），精确报告失败分片
  --aggregate : 按编号合并所有 chunk_NNN.json，重编号 slide ID，输出最终文件

用法:
    python3 aggregate_json.py --validate --chunks-dir ./chunks
    python3 aggregate_json.py --aggregate --chunks-dir ./chunks --output ./output.json
    python3 aggregate_json.py --validate-and-aggregate --chunks-dir ./chunks --output ./output.json

依赖: Python 3.11+ (内置 json 模块)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ──────────────────────────────────────────────
# JSON 文本修复（LLM 输出常见问题）
# ──────────────────────────────────────────────

def repair_json_text(text: str) -> tuple[str, list[str]]:
    """
    修复 LLM 生成的 JSON 文本中的常见问题。
    返回 (修复后的文本, 修复操作列表)。

    修复项：
    1. 字符串内的未转义双引号 " → \\"
    2. 字符串内的换行符 → \\n
    3. 尾部逗号 ,] 或 ,} → ] 或 }
    4. Unicode curly quotes " " → 普通中文引号「」（避免与 JSON 分隔符混淆）
    """
    repairs = []

    # 预处理：替换 curly quotes 为中文书名号，避免与 JSON " 混淆
    # 这些是 Unicode 字符 U+201C / U+201D，不会被 JSON 解析器视为分隔符
    # 但 LLM 有时会混用，统一替换为不会冲突的中文标点
    if "“" in text or "”" in text:
        text = text.replace("“", "「").replace("”", "」")
        repairs.append("curly quotes \"\" → 「」")

    # 尝试直接解析，如果成功就不需要进一步修复
    try:
        json.loads(text)
        if not repairs:
            return text, []
        return text, repairs
    except json.JSONDecodeError:
        pass

    # 状态机解析，修复字符串内的未转义引号和控制字符
    result = []
    i = 0
    in_string = False
    fixed_quotes = 0
    fixed_newlines = 0

    while i < len(text):
        ch = text[i]

        if not in_string:
            result.append(ch)
            if ch == '"':
                in_string = True
        else:
            # 我们在一个 JSON 字符串内部
            if ch == '\\' and i + 1 < len(text):
                # 转义序列，原样保留两个字符
                result.append(ch)
                result.append(text[i + 1])
                i += 2
                continue
            elif ch == '"':
                # 关键判断：这个 " 是字符串结尾，还是内容中未转义的引号？
                # 向前跳过空白，看下一个有意义的字符
                j = i + 1
                while j < len(text) and text[j] in ' \t\r\n':
                    j += 1

                if j >= len(text) or text[j] in ':,}]':
                    # 这是字符串结尾引号
                    result.append(ch)
                    in_string = False
                else:
                    # 这是字符串内容中未转义的引号，需要转义
                    result.append('\\"')
                    fixed_quotes += 1
            elif ch == '\n':
                # JSON 字符串内不能有裸换行
                result.append('\\n')
                fixed_newlines += 1
            elif ch == '\r':
                result.append('\\r')
            elif ch == '\t':
                result.append('\\t')
            else:
                result.append(ch)

        i += 1

    text = ''.join(result)

    if fixed_quotes > 0:
        repairs.append(f"unescaped quotes: {fixed_quotes} 个")
    if fixed_newlines > 0:
        repairs.append(f"bare newlines: {fixed_newlines} 个")

    # 修复尾部逗号: ,] 或 ,} （可能中间有空白）
    cleaned = re.sub(r',\s*([}\]])', r'\1', text)
    if cleaned != text:
        repairs.append("trailing commas removed")
        text = cleaned

    return text, repairs


def repair_chunk_file(filepath: str) -> tuple[bool, list[str]]:
    """
    修复单个 chunk JSON 文件。
    返回 (是否发生了修复, 修复操作列表)。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # 先试能不能直接解析
    try:
        json.loads(raw)
        return False, []
    except json.JSONDecodeError:
        pass

    repaired, repairs = repair_json_text(raw)

    # 验证修复后能解析
    try:
        json.loads(repaired)
    except json.JSONDecodeError as e:
        repairs.append(f"修复后仍有错误: {e}")
        return False, repairs

    # 写回文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(repaired)

    return True, repairs


def cmd_repair(chunks_dir: str) -> int:
    """修复所有 chunk JSON 文件中的常见问题。"""
    chunk_files = find_chunk_files(chunks_dir)
    if not chunk_files:
        print(f"ERROR: 在 {chunks_dir} 中没有找到 chunk_NNN.json 文件", file=sys.stderr)
        return 1

    print(f"修复目录: {chunks_dir}")
    print(f"待检查: {len(chunk_files)} 个文件")
    print()

    repaired_count = 0
    failed_count = 0

    for _index, filepath in chunk_files:
        filename = os.path.basename(filepath)
        repaired, repairs = repair_chunk_file(filepath)

        if repaired:
            repaired_count += 1
            print(f"  {filename}: 已修复 — {'; '.join(repairs)}")
        elif repairs:
            # 有修复尝试但未成功
            failed_count += 1
            print(f"  {filename}: 修复失败 — {'; '.join(repairs)}")
        # else: 无需修复，静默跳过

    print()
    if repaired_count == 0 and failed_count == 0:
        print("所有文件格式正确，无需修复。")
    else:
        print(f"修复: {repaired_count} 个, 失败: {failed_count} 个, 无需修复: {len(chunk_files) - repaired_count - failed_count} 个")

    return 1 if failed_count > 0 else 0


# ──────────────────────────────────────────────
# Schema 验证规则
# ──────────────────────────────────────────────

VALID_LAYOUTS = {"cover", "cards", "list", "columns", "code", "table", "comparison", "content"}

LAYOUT_REQUIRED_FIELDS = {
    "cover": ["subtitle"],
    "cards": ["cards"],
    "list": ["items"],
    "columns": ["columns"],
    "code": ["code"],
    "table": ["table"],
    "comparison": ["comparison"],
    # content 没有额外必填字段
}


@dataclass
class ValidationResult:
    chunk_index: int
    filename: str
    passed: bool
    errors: list[str]
    slide_count: int = 0


def validate_slide(slide: dict, slide_idx: int) -> list[str]:
    """验证单个 slide 对象，返回错误列表。"""
    errors = []
    prefix = f"slides[{slide_idx}]"

    # 通用必填字段
    for field in ("id", "layout", "eyebrow", "title"):
        if field not in slide:
            errors.append(f"{prefix}: 缺少必填字段 '{field}'")

    # layout 类型检查
    layout = slide.get("layout", "")
    if layout not in VALID_LAYOUTS:
        errors.append(f"{prefix}: 未知的 layout '{layout}'，有效值: {', '.join(sorted(VALID_LAYOUTS))}")

    # layout 特定字段检查
    if layout in LAYOUT_REQUIRED_FIELDS:
        for req_field in LAYOUT_REQUIRED_FIELDS[layout]:
            if req_field not in slide:
                errors.append(f"{prefix} (layout={layout}): 缺少必填字段 '{req_field}'")

    # cards 内部结构
    if layout == "cards" and "cards" in slide:
        for ci, card in enumerate(slide["cards"]):
            for cf in ("icon", "title", "description"):
                if cf not in card:
                    errors.append(f"{prefix}.cards[{ci}]: 缺少字段 '{cf}'")

    # columns 内部结构
    if layout == "columns" and "columns" in slide:
        for ci, col in enumerate(slide["columns"]):
            for cf in ("title", "items"):
                if cf not in col:
                    errors.append(f"{prefix}.columns[{ci}]: 缺少字段 '{cf}'")

    # comparison 内部结构
    if layout == "comparison" and "comparison" in slide:
        comp = slide["comparison"]
        for side in ("left", "right"):
            if side not in comp:
                errors.append(f"{prefix}.comparison: 缺少 '{side}'")
            else:
                for cf in ("title", "items"):
                    if cf not in comp[side]:
                        errors.append(f"{prefix}.comparison.{side}: 缺少字段 '{cf}'")

    return errors


def validate_chunk_file(filepath: str, chunk_index: int) -> ValidationResult:
    """验证单个 chunk JSON 文件。"""
    filename = os.path.basename(filepath)
    errors = []

    # 1. JSON 语法验证
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return ValidationResult(
            chunk_index=chunk_index,
            filename=filename,
            passed=False,
            errors=[f"JSON 语法错误: {e}"],
        )
    except Exception as e:
        return ValidationResult(
            chunk_index=chunk_index,
            filename=filename,
            passed=False,
            errors=[f"文件读取错误: {e}"],
        )

    # 2. 顶层结构验证
    if not isinstance(data, dict):
        return ValidationResult(
            chunk_index=chunk_index,
            filename=filename,
            passed=False,
            errors=["顶层必须是 JSON 对象"],
        )

    if "slides" not in data:
        return ValidationResult(
            chunk_index=chunk_index,
            filename=filename,
            passed=False,
            errors=["缺少 'slides' 字段"],
        )

    slides = data["slides"]
    if not isinstance(slides, list):
        return ValidationResult(
            chunk_index=chunk_index,
            filename=filename,
            passed=False,
            errors=["'slides' 必须是数组"],
        )

    if len(slides) == 0:
        return ValidationResult(
            chunk_index=chunk_index,
            filename=filename,
            passed=False,
            errors=["'slides' 数组不能为空"],
        )

    # 3. 逐 slide 验证
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            errors.append(f"slides[{i}]: 必须是对象")
            continue
        errors.extend(validate_slide(slide, i))

    return ValidationResult(
        chunk_index=chunk_index,
        filename=filename,
        passed=len(errors) == 0,
        errors=errors,
        slide_count=len(slides),
    )


def find_chunk_files(chunks_dir: str) -> list[tuple[int, str]]:
    """
    在目录中查找所有 chunk_NNN.json 文件。
    返回 [(index, filepath), ...] 按编号排序。
    """
    pattern = re.compile(r"^chunk_(\d{3})\.json$")
    chunks = []

    for filename in os.listdir(chunks_dir):
        m = pattern.match(filename)
        if m:
            index = int(m.group(1))
            filepath = os.path.join(chunks_dir, filename)
            chunks.append((index, filepath))

    chunks.sort(key=lambda x: x[0])
    return chunks


def check_continuity(chunk_files: list[tuple[int, str]]) -> list[str]:
    """检查分片编号是否连续。"""
    errors = []
    if not chunk_files:
        errors.append("没有找到任何 chunk_NNN.json 文件")
        return errors

    indices = [idx for idx, _ in chunk_files]
    expected = list(range(1, len(chunk_files) + 1))

    if indices != expected:
        missing = set(expected) - set(indices)
        if missing:
            errors.append(f"分片编号不连续，缺少: {sorted(missing)}")
        extra = set(indices) - set(expected)
        if extra:
            errors.append(f"发现多余编号: {sorted(extra)}")

    return errors


def cmd_validate(chunks_dir: str) -> int:
    """逐片验证，返回 0 表示全部通过，1 表示有失败。"""
    print(f"验证目录: {chunks_dir}")
    print()

    chunk_files = find_chunk_files(chunks_dir)
    if not chunk_files:
        print(f"ERROR: 在 {chunks_dir} 中没有找到 chunk_NNN.json 文件", file=sys.stderr)
        return 1

    # 编号连续性检查
    continuity_errors = check_continuity(chunk_files)
    if continuity_errors:
        for err in continuity_errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        return 1

    results: list[ValidationResult] = []
    for index, filepath in chunk_files:
        result = validate_chunk_file(filepath, index)
        results.append(result)

    # 输出报告
    passed_count = sum(1 for r in results if r.passed)
    failed_count = sum(1 for r in results if not r.passed)
    total_slides = sum(r.slide_count for r in results)

    print(f"{'编号':<6} {'文件':<22} {'状态':<8} {'slides':<8} {'错误'}")
    print("-" * 70)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        err_str = "; ".join(r.errors[:3]) if r.errors else ""
        if len(r.errors) > 3:
            err_str += f" (+{len(r.errors)-3} more)"
        print(f"{r.chunk_index:<6} {r.filename:<22} {status:<8} {r.slide_count:<8} {err_str}")

    print("-" * 70)
    print(f"总计: {len(results)} 个分片, {total_slides} 张 slides")
    print(f"通过: {passed_count}, 失败: {failed_count}")

    if failed_count > 0:
        print(f"\n以下分片需要修复:")
        for r in results:
            if not r.passed:
                print(f"  chunk_{r.chunk_index:03d}.json:")
                for err in r.errors:
                    print(f"    - {err}")
        return 1

    print("\n全部验证通过！可以执行聚合。")
    return 0


def cmd_aggregate(chunks_dir: str, output_path: str, title: str, author: str, date: str) -> int:
    """合并所有 chunk JSON，重编号 ID，输出最终文件。"""
    print(f"分片目录: {chunks_dir}")
    print(f"输出文件: {output_path}")
    print()

    chunk_files = find_chunk_files(chunks_dir)
    if not chunk_files:
        print(f"ERROR: 没有找到 chunk_NNN.json 文件", file=sys.stderr)
        return 1

    # 编号连续性检查
    continuity_errors = check_continuity(chunk_files)
    if continuity_errors:
        for err in continuity_errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        return 1

    # 合并 slides
    all_slides = []
    for index, filepath in chunk_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"ERROR: 读取 chunk_{index:03d}.json 失败: {e}", file=sys.stderr)
            print(f"聚合中断，请先修复该分片。", file=sys.stderr)
            return 1

        if "slides" not in data or not isinstance(data["slides"], list):
            print(f"ERROR: chunk_{index:03d}.json 缺少有效的 'slides' 数组", file=sys.stderr)
            print(f"聚合中断，请先修复该分片。", file=sys.stderr)
            return 1

        if len(data["slides"]) == 0:
            print(f"ERROR: chunk_{index:03d}.json 的 slides 数组为空", file=sys.stderr)
            print(f"聚合中断，请先修复该分片。", file=sys.stderr)
            return 1

        all_slides.extend(data["slides"])

    # 全局重编号
    for i, slide in enumerate(all_slides):
        slide["id"] = i + 1

    # 构建最终 JSON
    final_json = {
        "title": title,
        "slides": all_slides,
    }
    if author:
        final_json["author"] = author
    if date:
        final_json["date"] = date

    # 写入文件
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)

    print(f"聚合完成！")
    print(f"  分片数: {len(chunk_files)}")
    print(f"  总 slides: {len(all_slides)}")
    print(f"  输出文件: {output_path}")

    # 最终验证
    print(f"\n执行最终验证...")
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            verify_data = json.load(f)
        assert "slides" in verify_data
        assert len(verify_data["slides"]) == len(all_slides)
        assert verify_data["slides"][0]["id"] == 1
        assert verify_data["slides"][-1]["id"] == len(all_slides)
        print("最终验证通过！")
    except Exception as e:
        print(f"最终验证失败: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_validate_and_aggregate(chunks_dir: str, output_path: str, title: str, author: str, date: str) -> int:
    """先验证再聚合。"""
    ret = cmd_validate(chunks_dir)
    if ret != 0:
        print("\n验证未通过，聚合已取消。请先修复失败的分片。", file=sys.stderr)
        return ret

    print()
    return cmd_aggregate(chunks_dir, output_path, title, author, date)


def main():
    parser = argparse.ArgumentParser(
        description="doc-to-ppt-json: JSON 逐片验证与聚合工具"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repair", action="store_true", help="修复 JSON 文件中的常见问题（未转义引号、尾部逗号等）")
    group.add_argument("--validate", action="store_true", help="逐片验证所有 chunk_NNN.json")
    group.add_argument("--aggregate", action="store_true", help="合并重编号输出最终 JSON")
    group.add_argument("--validate-and-aggregate", action="store_true", help="先修复 → 验证 → 聚合")

    parser.add_argument("--chunks-dir", "-d", required=True, help="分片 JSON 文件目录")
    parser.add_argument("--output", "-o", default=None, help="最终输出 JSON 文件路径")
    parser.add_argument("--title", "-t", default="演示文稿", help="PPT 标题")
    parser.add_argument("--author", "-a", default="", help="作者")
    parser.add_argument("--date", default="", help="日期")

    args = parser.parse_args()

    if args.aggregate or args.validate_and_aggregate:
        if not args.output:
            print("ERROR: --aggregate 和 --validate-and-aggregate 需要 --output 参数", file=sys.stderr)
            sys.exit(1)

    if args.repair:
        ret = cmd_repair(args.chunks_dir)
    elif args.validate:
        ret = cmd_validate(args.chunks_dir)
    elif args.aggregate:
        ret = cmd_aggregate(args.chunks_dir, args.output, args.title, args.author, args.date)
    else:
        ret = cmd_repair(args.chunks_dir)
        print()
        ret = cmd_validate_and_aggregate(args.chunks_dir, args.output, args.title, args.author, args.date)

    sys.exit(ret)


if __name__ == "__main__":
    main()
