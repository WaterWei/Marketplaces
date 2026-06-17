#!/usr/bin/env python3
"""Parse answer PDFs - improved version handling complex formats."""

import os, re, json

BASE = "skills/pdf-to-math-questions/output"

def parse_answer_content(content):
    """Parse answers from answer PDF content. Returns dict {qnum: answer_text}."""
    answers = {}
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("<div") or line.startswith("<img"):
            continue
        if line.startswith("解析") or line.startswith("分析") or line.startswith("答:") or line.startswith("答："):
            continue

        # Pattern 1: "N. answer" where N is question number
        # e.g., "2. 0.368 18.9 2.835 0.493 （竖式略）"
        # e.g., "3. B"
        # e.g., "4. 7.9 × 15.2 = 120.08 km"
        m = re.match(r'^(\d+)\.\s+(.+)$', line)
        if m:
            qnum = int(m.group(1))
            ans = m.group(2).strip()
            # Skip if it looks like a section header or non-answer
            if len(ans) > 200:
                continue
            if qnum not in answers:
                answers[qnum] = ans
            continue

        # Pattern 2: "N. (1) answer (2) answer" multi-part
        m = re.match(r'^(\d+)\.\s*\((\d+)\)\s*(.+)$', line)
        if m:
            qnum = int(m.group(1))
            sub = int(m.group(2))
            ans = m.group(3).strip()
            key = f"{qnum}({sub})"
            if key not in answers:
                answers[key] = ans
            continue

        # Pattern 3: standalone "(N) answer" continuation
        m = re.match(r'^\((\d+)\)\s+(.+)$', line)
        if m:
            sub = int(m.group(1))
            ans = m.group(2).strip()
            # This is a sub-part, needs parent qnum - skip for now
            continue

    return answers


def main():
    all_results = {}

    # Find all answer dirs
    for book_dir in sorted(os.listdir(BASE)):
        book_path = os.path.join(BASE, book_dir)
        if not os.path.isdir(book_path) or book_dir == "chapter-map.json":
            continue

        raw = os.path.join(book_path, "raw_pages")
        if not os.path.isdir(raw):
            continue

        answer_dirs = [d for d in os.listdir(raw)
                      if os.path.isdir(os.path.join(raw, d)) and "答案" in d]

        if not answer_dirs:
            continue

        print(f"\n{'='*60}")
        print(f"Book: {book_dir}")

        all_answers = {}

        for answer_dir in sorted(answer_dirs):
            answer_path = os.path.join(raw, answer_dir)
            docs = sorted([f for f in os.listdir(answer_path)
                          if f.startswith("doc_") and f.endswith(".md")],
                         key=lambda x: int(re.search(r'doc_(\d+)', x).group(1)))

            # Skip first 2 pages (cover + TOC)
            content_docs = docs[2:] if len(docs) > 2 else docs

            combined_answers = {}
            for doc in content_docs:
                doc_path = os.path.join(answer_path, doc)
                with open(doc_path, encoding="utf-8") as f:
                    content = f.read()

                page_answers = parse_answer_content(content)
                for k, v in page_answers.items():
                    if k not in combined_answers:
                        combined_answers[k] = v

            # Separate numeric and key-based answers
            qnum_answers = {k: v for k, v in combined_answers.items() if isinstance(k, int)}
            print(f"  {answer_dir}: {len(qnum_answers)} unique answers")
            all_answers[answer_dir] = qnum_answers

        # Save
        out_dir = os.path.join(book_path, "answers")
        os.makedirs(out_dir, exist_ok=True)

        total = 0
        for answer_dir, answers in all_answers.items():
            out_path = os.path.join(out_dir, f"{answer_dir}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(answers, f, ensure_ascii=False, indent=2, sort_keys=True)
            total += len(answers)

        all_results[book_dir] = total

    print(f"\n{'='*60}")
    print("SUMMARY:")
    for book, count in all_results.items():
        print(f"  {count:3d} answers  {book[:60]}")


if __name__ == "__main__":
    main()
