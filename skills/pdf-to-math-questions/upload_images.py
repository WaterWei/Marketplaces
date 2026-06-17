#!/usr/bin/env python3
"""Upload images to 飞书 Base for all books."""

import json, os, re, subprocess, time

BASE = "skills/pdf-to-math-questions/output"

BOOKS = [
    ("25秋人教版数学五年级上册《53天天练》", "KpM1bqk2Fa50Oys24CHcZ61Ynbc", "tblboaC6DyaAPRkL"),
    ("25秋人教版数学四年级上册《53天天练》", "E4IEbAwBQaV5aosEc36cPeHunzd", "tblnWkSFNBHRSX4G"),
    ("25秋北师版数学四年级上册《53天天练》", "GQK5buwKyag2ZDsTcfyciYNonBh", "tbl5opy4DI94DoMx"),
    ("25秋浙教版数学七年级上册《53 同步》", "AbmKbMJQfacDwcsPDdhcqNiBnge", "tblAYAEuJui7aOOG"),
    ("25秋浙教版数学七年级下册《53 同步》", "EMLubgR18a5USNsJI3scVARknql", "tblDTrrebTVDin2U"),
    ("25秋浙教版数学八年级上册《53 同步》", "AxKmb4Fs6aP9uCsy1qPcdBMYntP", "tblE7cYJ7L7PBA7W"),
    ("25秋苏教版数学二年级上册《53天天练》", "LtHRbpcOtaO5KMs4jaVcuJpTntd", "tblk42IYi365hGvD"),
    ("26春苏教版数学一年级下册《53天天练》", "ZExGbTSPNabLUXsMqaEcw7Imnjf", "tblqAJov4ap0Ockj"),
]


def extract_image_paths(question):
    """Extract image paths from question (images field or img tags in text)."""
    paths = question.get("images", [])
    if not paths:
        paths = re.findall(r'<img\s+src="(imgs/[^"]+)"', question.get("question_text", ""))
    return paths


def download_image(url, local_path):
    result = subprocess.run(
        ["curl", "-s", "-o", local_path, "-w", "%{http_code}", url],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout == "200"


def upload_attachment(token, table_id, record_id, file_path):
    result = subprocess.run(
        ["lark-cli", "base", "+record-upload-attachment",
         "--base-token", token, "--table-id", table_id,
         "--record-id", record_id, "--field-id", "题目图片",
         "--file", file_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        return json.loads(result.stdout).get("ok", False)
    return False


def get_record_ids(token, table_id):
    all_ids = []
    offset = 0
    while True:
        result = subprocess.run(
            ["lark-cli", "base", "+record-list",
             "--base-token", token, "--table-id", table_id,
             "--limit", "200", "--offset", str(offset), "--field-id", "ID"],
            capture_output=True, text=True
        )
        ids = []
        for line in result.stdout.split("\n"):
            if line.startswith("| rec"):
                rid = line.split("|")[1].strip()
                if rid.startswith("rec"):
                    ids.append(rid)
        all_ids.extend(ids)
        if len(ids) < 200 or "has_more=false" in result.stdout:
            break
        offset += 200
    return all_ids


def process_book(book_dir, token, table_id):
    print(f"\n{'='*50}")
    print(f"Processing: {book_dir}")

    # Load image URL mapping
    map_path = os.path.join(BASE, book_dir, "image_urls.json")
    if not os.path.exists(map_path):
        print(f"  No image_urls.json, skipping")
        return 0
    with open(map_path, encoding="utf-8") as f:
        all_image_urls = json.load(f)
    print(f"  Image URLs: {len(all_image_urls)}")

    # Read parsed questions
    parsed_path = os.path.join(BASE, book_dir, "batches", "parsed_2.json")
    if not os.path.exists(parsed_path):
        print(f"  No parsed_2.json, skipping")
        return 0
    with open(parsed_path, encoding="utf-8") as f:
        questions = json.load(f)

    # Find questions with images
    questions_with_images = []
    for q in questions:
        img_paths = extract_image_paths(q)
        if img_paths:
            questions_with_images.append({"id": q["id"], "images": img_paths})

    print(f"  Questions with images: {len(questions_with_images)}")
    if not questions_with_images:
        return 0

    # Get record IDs
    record_ids = get_record_ids(token, table_id)
    print(f"  Records in Base: {len(record_ids)}")

    if len(record_ids) != len(questions):
        print(f"  WARNING: count mismatch")

    # Download and upload
    tmp_dir = os.path.join("skills/pdf-to-math-questions/tmp_images", book_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    uploaded = 0
    for qi in questions_with_images:
        # Find record by ID match
        q_idx = None
        for i, q in enumerate(questions):
            if q["id"] == qi["id"]:
                q_idx = i
                break
        if q_idx is None or q_idx >= len(record_ids):
            continue

        record_id = record_ids[q_idx]
        for img_path in qi["images"]:
            url = all_image_urls.get(img_path)
            if not url:
                continue
            local_path = os.path.join(tmp_dir, os.path.basename(img_path))
            if download_image(url, local_path):
                if upload_attachment(token, table_id, record_id, local_path):
                    uploaded += 1
            time.sleep(0.05)

    print(f"  Uploaded: {uploaded} images")
    return uploaded


def main():
    total = 0
    for book_dir, token, table_id in BOOKS:
        total += process_book(book_dir, token, table_id)
    print(f"\n{'='*50}")
    print(f"Total images uploaded: {total}")


if __name__ == "__main__":
    main()
