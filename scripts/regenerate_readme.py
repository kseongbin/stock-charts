#!/usr/bin/env python3
"""
README.md 를 _index.json 기준으로 자동 재생성.

사용법:
  python3 scripts/regenerate_readme.py reports
  python3 scripts/regenerate_readme.py reports_b
"""
import json
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def regenerate(folder: str) -> None:
    base = REPO / folder
    idx_path = base / "_index.json"
    readme_path = base / "README.md"

    with idx_path.open(encoding="utf-8") as f:
        idx = json.load(f)

    items = sorted(idx["completed"].items(), key=lambda x: x[1].get("generated_at", ""))

    is_b = folder == "reports_b"
    title = "기업분석 보고서 인덱스 (B 계정)" if is_b else "기업분석 보고서 인덱스"
    footer_note = (
        "*이 파일은 B 루틴이 보고서 생성 시 자동으로 갱신합니다.*"
        if is_b
        else "*이 파일은 batch_reports.py가 보고서 생성 시 자동으로 갱신합니다.*"
    )

    rows = []
    for i, (name, info) in enumerate(items, 1):
        filename = info.get("filename", f"{name}.html")
        encoded = urllib.parse.quote(filename)
        url = f"https://raw.githubusercontent.com/kseongbin/stock-charts/main/{folder}/{encoded}"
        rows.append(
            f'| {i} | {name} | {info.get("category", "일반")} | [Raw]({url}) | {info.get("generated_at", "")} |'
        )

    body = (
        f"# {title}\n\n"
        "자동 생성된 보고서 목록입니다. Raw 링크를 클릭해 HTML을 복사한 뒤 티스토리에 붙여넣으세요.\n\n"
        "## 사용 방법\n"
        "1. 아래 표에서 원하는 기업의 **Raw** 링크 클릭\n"
        "2. `Ctrl+A` → `Ctrl+C` (전체 복사)\n"
        "3. 티스토리 글쓰기 → **HTML 모드** 전환 → `Ctrl+V` 붙여넣기 → 발행\n\n"
        "---\n\n"
        "## 생성된 보고서\n\n"
        "| # | 기업명 | 카테고리 | Raw 링크 | 생성일 |\n"
        "|---:|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n---\n\n"
        + footer_note
        + "\n"
    )

    readme_path.write_text(body, encoding="utf-8")
    print(f"{readme_path}: {len(items)} entries")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"reports", "reports_b"}:
        print("Usage: python3 scripts/regenerate_readme.py [reports|reports_b]", file=sys.stderr)
        sys.exit(1)
    regenerate(sys.argv[1])
