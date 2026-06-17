#!/usr/bin/env python3
"""Extract Table of Contents from OCR output for all 8 books."""

import os, re, json

BASE = "skills/pdf-to-math-questions/output"

# Book configs: (book_dir, main_pdf_pattern, toc_doc)
BOOKS = [
    ("25秋浙教版数学七年级上册《53 同步》", "A本彩色版", "doc_3.md"),
    ("25秋浙教版数学七年级下册《53 同步》", "七下B本ZJ", "doc_3.md"),
    ("25秋浙教版数学八年级上册《53 同步》", "A本", "doc_3.md"),
    ("25秋人教版数学五年级上册《53天天练》", "5主书", "doc_4.md"),
    ("25秋人教版数学四年级上册《53天天练》", "4主书", "doc_4.md"),
    ("25秋北师版数学四年级上册《53天天练》", "4主书", "doc_4.md"),
    ("25秋苏教版数学二年级上册《53天天练》", "主书", "doc_4.md"),
    ("26春苏教版数学一年级下册《53天天练》", "SJ_1下", "doc_3.md"),
]


def parse_page_number(text):
    """Extract page number from TOC line like '..... A1' or '…… 15'."""
    # Try patterns: A1, B3, 15, etc.
    m = re.search(r'[.…]{1,6}\s*([A-Z]?\d+[A-Z]?)\s*$', text.strip())
    if m:
        return m.group(1)
    # Try: ... page_num at end
    m = re.search(r'(\d+)\s*$', text.strip())
    if m:
        return m.group(1)
    return None


def parse_toc_53tongbu(content):
    """Parse TOC for 53同步 (初中) - doc_3.md format."""
    entries = []
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip non-TOC lines
        if line.startswith("##") and ("目录" in line or "CONTENTS" in line):
            continue
        if line.startswith("<div") or line.startswith("<img"):
            continue

        page = parse_page_number(line)
        # Remove page number from line for parsing
        clean = re.sub(r'[.…]{1,6}\s*[A-Z]?\d+[A-Z]?\s*$', '', line).strip()

        # Level 1: 第N章 ...
        m = re.match(r'^(第\d+章)\s+(.+)', clean)
        if m:
            entries.append({"title": f"{m.group(1)} {m.group(2)}", "level": 1, "page": page})
            continue

        # Level 2: N.M ... or 第N课时 ... or 专项突破... or 练模型
        m = re.match(r'^(\d+\.\d+)\s+(.+)', clean)
        if m:
            entries.append({"title": f"{m.group(1)} {m.group(2)}", "level": 2, "page": page})
            continue

        m = re.match(r'^(第\d+课时)\s+(.+)', clean)
        if m:
            entries.append({"title": f"{m.group(1)} {m.group(2)}", "level": 2, "page": page})
            continue

        m = re.match(r'^(专项突破\d+)\s+(.+)', clean)
        if m:
            entries.append({"title": f"{m.group(1)} {m.group(2)}", "level": 2, "page": page})
            continue

        if clean in ("练模型", "练方法") or clean.startswith("模型") or clean.startswith("方法"):
            entries.append({"title": clean, "level": 3, "page": page})
            continue

        # Level 3: 知识点N ...
        m = re.match(r'^(知识点\s*\d*)\s*(.*)', clean)
        if m:
            title = f"知识点 {m.group(1).replace('知识点', '').strip()} {m.group(2)}".strip()
            if "知识点 " not in title:
                title = f"知识点 {clean.replace('知识点', '').strip()}"
            entries.append({"title": title, "level": 3, "page": page})
            continue

    return entries


def parse_toc_53tiantianlian(content):
    """Parse TOC for 53天天练 (小学) - doc_4.md format."""
    entries = []
    lines = content.split("\n")
    current_unit = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("##") and "目录" in line:
            continue
        if line.startswith("<div") or line.startswith("<img"):
            continue

        page = parse_page_number(line)
        clean = re.sub(r'[.…]{1,6}\s*\d+\s*$', '', line).strip()
        clean = re.sub(r'[.……]+\s*$', '', line).strip()

        # Unit name: ##### or #### with unit name
        m = re.match(r'^#{3,5}\s+(.+)', clean)
        if m:
            current_unit = m.group(1).strip()
            entries.append({"title": current_unit, "level": 1, "page": page})
            continue

        # 第N单元知识梳理 / 第N单元素养练习
        m = re.match(r'^(第[一二三四五六七八九十]+单元)(知识梳理|素养练习)', clean)
        if m:
            entries.append({"title": clean, "level": 2, "page": page})
            continue

        # 第N课时 ...
        m = re.match(r'^(第\d+课时)\s+(.+)', clean)
        if m:
            entries.append({"title": f"{m.group(1)} {m.group(2)}", "level": 2, "page": page})
            continue

        # 整理和复习 / 期末复习 / 回顾与整理
        if clean in ("整理和复习", "期末复习", "回顾与整理", "整理与复习"):
            entries.append({"title": clean, "level": 2, "page": page})
            continue

        # Other entries with page numbers
        if page and clean:
            entries.append({"title": clean, "level": 2, "page": page})

    return entries


def parse_toc_generic(content):
    """Generic TOC parser for books without clear structure."""
    entries = []
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("##") and ("目录" in line or "CONTENTS" in line):
            continue
        if line.startswith("<div") or line.startswith("<img"):
            continue

        page = parse_page_number(line)
        clean = re.sub(r'[.…]{1,6}\s*\d+\s*$', '', line).strip()
        clean = re.sub(r'[.……]+\s*$', '', line).strip()

        if not clean:
            continue

        # Determine level by heading markers
        if line.startswith("#"):
            level = line.count("#")
            clean = re.sub(r'^#+\s*', '', line).strip()
        elif re.match(r'^第[一二三四五六七八九十\d]+[章节单元课]', clean):
            if "章" in clean or "单元" in clean:
                level = 1
            else:
                level = 2
        elif re.match(r'^\d+\.\d+', clean):
            level = 2
        elif re.match(r'^知识点', clean):
            level = 3
        else:
            level = 2

        entries.append({"title": clean, "level": level, "page": page})

    return entries


def find_main_pdf(book_dir):
    """Find the main content PDF directory."""
    raw = os.path.join(BASE, book_dir, "raw_pages")
    if not os.path.isdir(raw):
        return None

    pdfs = [d for d in os.listdir(raw)
            if os.path.isdir(os.path.join(raw, d))
            and "答案" not in d and "answer" not in d.lower()]

    if not pdfs:
        return None

    # Find PDF with most pages
    best = max(pdfs, key=lambda p: len([f for f in os.listdir(os.path.join(raw, p))
                                         if f.startswith("doc_") and f.endswith(".md")]))
    return best


def main():
    results = {}

    for book_dir, pdf_pattern, toc_doc in BOOKS:
        print(f"\n{'='*60}")
        print(f"Processing: {book_dir}")

        main_pdf = find_main_pdf(book_dir)
        if not main_pdf:
            print(f"  ERROR: No main PDF found")
            continue

        print(f"  Main PDF: {main_pdf}")

        # Find TOC doc
        raw_dir = os.path.join(BASE, book_dir, "raw_pages", main_pdf)

        # Try specified doc first, then fallback
        toc_path = None
        for doc_name in [toc_doc, "doc_3.md", "doc_4.md", "doc_5.md"]:
            p = os.path.join(raw_dir, doc_name)
            if os.path.exists(p):
                toc_path = p
                break

        if not toc_path:
            print(f"  ERROR: No TOC doc found")
            continue

        # Some books have TOC spanning multiple pages
        # Only concatenate if next page also starts with TOC markers (headings + page numbers)
        # Stop if page contains numbered questions (1. 2. 3.) or <img> blocks
        content = ""
        toc_num = int(os.path.basename(toc_path).replace("doc_", "").replace(".md", ""))
        for offset in range(3):
            doc_name = f"doc_{toc_num + offset}.md"
            p = os.path.join(raw_dir, doc_name)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    page_content = f.read()
                # First page always included
                if offset == 0:
                    content += page_content + "\n"
                    continue
                # Check if page is TOC continuation (not content page)
                has_numbered_questions = bool(re.search(r'^\d+\.\s', page_content, re.MULTILINE))
                has_answer_markers = bool(re.search(r'答案|解析|DA本|DB本', page_content))
                has_img_blocks = page_content.count('<img') > 3
                if has_numbered_questions or has_answer_markers or has_img_blocks:
                    break
                content += page_content + "\n"

        last_doc = toc_num + offset
        print(f"  TOC source: doc_{toc_num}.md through doc_{last_doc}.md ({len(content)} chars)")

        # Choose parser based on book type
        if "53 同步" in book_dir or "53同步" in book_dir:
            entries = parse_toc_53tongbu(content)
        elif "53天天练" in book_dir:
            entries = parse_toc_53tiantianlian(content)
        else:
            entries = parse_toc_generic(content)

        # Deduplicate by title
        seen = set()
        unique = []
        for e in entries:
            if e["title"] not in seen:
                seen.add(e["title"])
                unique.append(e)
        entries = unique

        # For 53同步 (初中), keep only L1+L2 (chapters + sections)
        # Level 3 (知识点) entries are too granular and cause noise
        if "53 同步" in book_dir or "53同步" in book_dir:
            entries = [e for e in entries if e["level"] <= 2]

        # Clean up artifacts
        entries = [e for e in entries if e["title"] not in ("O", "")]

        print(f"  Extracted {len(entries)} TOC entries")
        if entries:
            for e in entries[:5]:
                indent = "  " * (e["level"] - 1)
                print(f"    {indent}[L{e['level']}] {e['title']} ... {e['page']}")
            if len(entries) > 5:
                print(f"    ... ({len(entries) - 5} more)")

        # Save to chapter-map.json
        out_path = os.path.join(BASE, book_dir, "chapter-map.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {out_path}")

        results[book_dir] = len(entries)

    print(f"\n{'='*60}")
    print("SUMMARY:")
    for book, count in results.items():
        print(f"  {book}: {count} entries")


if __name__ == "__main__":
    main()
