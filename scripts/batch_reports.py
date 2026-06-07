#!/usr/bin/env python3
"""
기업분석 보고서 배치 생성 스크립트
- reports/_queue.json에서 기업 순서대로 처리
- claude CLI로 company-analyst 에이전트 호출
- 결과 HTML을 reports/ 에 저장
- README.md 자동 갱신
- git commit & push
- 사용량 한도 도달 시 큐 보존 후 종료
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUEUE_FILE = ROOT / "reports" / "_queue.json"
INDEX_FILE = ROOT / "reports" / "_index.json"
README_FILE = ROOT / "reports" / "README.md"
REPORTS_DIR = ROOT / "reports"

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/kseongbin/stock-charts/main/reports"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_html(output: str) -> str:
    """claude 출력에서 HTML 블록 추출"""
    # ```html ... ``` 형식
    match = re.search(r"```html\s*(.*?)\s*```", output, re.DOTALL)
    if match:
        return match.group(1).strip()
    # <h3 으로 시작하는 블록
    match = re.search(r"(<h3\s.*?)</div>\s*$", output, re.DOTALL)
    if match:
        return match.group(0).strip()
    return ""


def sanitize_filename(name: str) -> str:
    """파일명에 사용할 수 없는 문자 제거"""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def run_claude(company_name: str) -> tuple[bool, str]:
    """claude CLI로 에이전트 호출, (성공여부, HTML or 에러메시지) 반환"""
    prompt = f"{company_name}"
    cmd = [
        "claude",
        "--model", "claude-sonnet-4-6",
        "--agent", "company-analyst",
        "--print",
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(ROOT),
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if any(x in stderr.lower() for x in ["rate limit", "quota", "usage limit", "overloaded"]):
                return False, "RATE_LIMIT"
            return False, f"ERROR: {stderr[:200]}"
        html = extract_html(result.stdout)
        if not html:
            return False, f"HTML_NOT_FOUND: {result.stdout[:200]}"
        return True, html
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except FileNotFoundError:
        return False, "CLAUDE_NOT_FOUND"


def update_readme(index_data: dict):
    """README.md 보고서 테이블 갱신"""
    completed = index_data.get("completed", {})
    rows = []
    for i, (name, info) in enumerate(sorted(completed.items(), key=lambda x: x[1].get("generated_at", ""), reverse=True), 1):
        filename = info.get("filename", "")
        raw_url = f"{GITHUB_RAW_BASE}/{filename}"
        category = info.get("category", "")
        generated_at = info.get("generated_at", "")
        rows.append(f"| {i} | {name} | {category} | [Raw]({raw_url}) | {generated_at} |")

    table_header = "| # | 기업명 | 카테고리 | Raw 링크 | 생성일 |\n|---:|---|---|---|---|"
    table_body = "\n".join(rows) if rows else "*(아직 생성된 보고서 없음)*"

    content = f"""# 기업분석 보고서 인덱스

자동 생성된 보고서 목록입니다. Raw 링크를 클릭해 HTML을 복사한 뒤 티스토리에 붙여넣으세요.

## 사용 방법
1. 아래 표에서 원하는 기업의 **Raw** 링크 클릭
2. `Ctrl+A` → `Ctrl+C` (전체 복사)
3. 티스토리 글쓰기 → **HTML 모드** 전환 → `Ctrl+V` 붙여넣기 → 발행

---

## 생성된 보고서 ({len(completed)}개)

{table_header}
{table_body}

---

*이 파일은 batch_reports.py가 보고서 생성 시 자동으로 갱신합니다.*
*마지막 갱신: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def git_commit_push(company_name: str, filename: str):
    """생성된 파일 commit & push"""
    try:
        subprocess.run(["git", "add", f"reports/{filename}", "reports/README.md", "reports/_index.json", "reports/_queue.json"],
                       cwd=str(ROOT), check=True, capture_output=True)
        msg = f"Add report: {company_name}"
        subprocess.run(["git", "commit", "-m", msg],
                       cwd=str(ROOT), check=True, capture_output=True)
        subprocess.run(["git", "push"],
                       cwd=str(ROOT), check=True, capture_output=True)
        print(f"  ✅ push 완료: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  git 오류: {e.stderr.decode()[:100] if e.stderr else str(e)}")


def main():
    if not QUEUE_FILE.exists():
        print("❌ reports/_queue.json 없음")
        sys.exit(1)

    queue_data = load_json(QUEUE_FILE)
    index_data = load_json(INDEX_FILE) if INDEX_FILE.exists() else {"completed": {}}
    queue = queue_data.get("queue", [])

    if not queue:
        print("✅ 큐가 비었습니다. 처리할 기업이 없습니다.")
        sys.exit(0)

    print(f"📋 처리 대기: {len(queue)}개")
    processed = 0

    while queue:
        item = queue[0]
        company_name = item["name"]
        category = item.get("category", "")

        print(f"\n🔍 [{processed + 1}] {company_name} ({category}) 처리 중...")

        success, result = run_claude(company_name)

        if result == "RATE_LIMIT":
            print(f"  ⚠️  사용량 한도 도달. 큐 보존 후 종료. (남은 {len(queue)}개)")
            queue_data["queue"] = queue
            save_json(QUEUE_FILE, queue_data)
            sys.exit(0)

        if not success:
            print(f"  ❌ 실패: {result}")
            # 실패한 항목은 큐 끝으로 이동 (재시도 방지를 위해 별도 기록)
            item["last_error"] = result
            item["error_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            queue.pop(0)
            queue_data["queue"] = queue
            save_json(QUEUE_FILE, queue_data)
            continue

        # 파일 저장
        safe_name = sanitize_filename(company_name)
        filename = f"{safe_name}.html"
        filepath = REPORTS_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result)

        # 인덱스 갱신
        index_data.setdefault("completed", {})[company_name] = {
            "filename": filename,
            "category": category,
            "generated_at": datetime.now().strftime("%Y-%m-%d"),
        }
        index_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_json(INDEX_FILE, index_data)

        # 큐에서 제거
        queue.pop(0)
        queue_data["queue"] = queue
        save_json(QUEUE_FILE, queue_data)

        # README 갱신
        update_readme(index_data)

        # git commit & push
        git_commit_push(company_name, filename)

        processed += 1
        print(f"  ✅ 완료: {filename}")

    print(f"\n🎉 배치 완료: {processed}개 처리, 큐 소진")


if __name__ == "__main__":
    main()
