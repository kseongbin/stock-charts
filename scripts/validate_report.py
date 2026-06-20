#!/usr/bin/env python3
"""
보고서 HTML 구조 검증.

사용:
    python3 scripts/validate_report.py reports_b/우리엔터프라이즈.html
    python3 scripts/validate_report.py --all                  # reports_b 전체
    python3 scripts/validate_report.py --all reports          # reports 전체
    python3 scripts/validate_report.py --list-broken          # 깨진 목록만 출력 (CI/스크립트용)

규칙은 .claude/agents/company-analyst.md (v24) 의 풀 템플릿을 따른다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 필수 섹션. 각 패턴은 풀 텍스트(태그 제거 후)에 대해 검색.
# 핵심: 섹션 번호+키워드 매칭. nbsp/공백/마침표 변형은 허용.
REQUIRED_SECTIONS: list[tuple[str, str]] = [
    ("1. 주가 흐름",        r"\b1[\.\s]+주가\s*흐름"),
    ("2. 기업 개요",        r"\b2[\.\s]+기업\s*개요"),
    ("3. 주요 연혁",        r"\b3[\.\s]+주요\s*연혁"),
    ("4. 사업개요",         r"\b4[\.\s]+사업\s*개요"),
    ("5. 주요 제품 매출 구성", r"\b5[\.\s]+주요\s*제품\s*매출\s*구성"),
    # 6번은 (6-1 연간 + 6-2 분기) 둘 다 OR 단일 (6. 연간 재무) 둘 중 하나
    # → validate() 안에서 별도 처리
    ("7. 주주 정보",        r"\b7[\.\s]+주주\s*정보"),
    ("9-1 관련 기사",       r"\b9-1[\.\s]+관련\s*기사"),
    ("9-2 관련 기사",       r"\b9-2[\.\s]+관련\s*기사"),
    ("9-3 관련 기사",       r"\b9-3[\.\s]+관련\s*기사"),
    ("9-4 관련 기사",       r"\b9-4[\.\s]+관련\s*기사"),
    ("9-5 관련 기사",       r"\b9-5[\.\s]+관련\s*기사"),
    ("10. 사업 검토",       r"\b10[\.\s]+사업\s*검토"),
]

# 재무 섹션 (6번) — KR/US 패턴 OR JP/CN/HK 패턴 중 하나면 OK
FIN_KR_US = (r"\b6-1[\.\s]+연간\s*재무", r"\b6-2[\.\s]+분기\s*재무")
FIN_JP_CN_HK = (r"\b6[\.\s]+연간\s*재무",)

# 에이전트 툴호출 XML이 HTML에 새어 들어간 흔적. 발견 즉시 실패.
# 2026-06-20 우림피티에스/우신시스템 사고: 본문 끝에 </content></invoke> 누출.
TOOLCALL_LEAK_PATTERNS = [
    r"</?content>",
    r"</?invoke\b",
    r"</?function_calls>",
    r"</?parameter\b",
    r"\bantml:",
]


def _strip_html(text: str) -> str:
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def validate(path: Path) -> list[str]:
    """누락 섹션/누출 흔적 목록 반환. 빈 리스트면 통과."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = _strip_html(raw)
    missing: list[str] = []
    for label, pat in REQUIRED_SECTIONS:
        if not re.search(pat, text):
            missing.append(label)
    # 6번 재무 섹션: KR/US 풀 OR JP/CN/HK 단일
    has_kr_us = all(re.search(p, text) for p in FIN_KR_US)
    has_jp_cn_hk = all(re.search(p, text) for p in FIN_JP_CN_HK)
    if not has_kr_us and not has_jp_cn_hk:
        missing.append("6. 재무 (6-1 연간 + 6-2 분기, 또는 단일 6. 연간 재무)")
    # 툴호출 XML 누출 검사 (원본 텍스트 대상)
    for pat in TOOLCALL_LEAK_PATTERNS:
        m = re.search(pat, raw)
        if m:
            missing.append(f"툴호출 XML 누출: {m.group(0)!r}")
    return missing


def report_one(path: Path) -> bool:
    missing = validate(path)
    if missing:
        print(f"FAIL {path.relative_to(REPO_ROOT)}")
        for m in missing:
            print(f"  - missing: {m}")
        return False
    print(f"OK   {path.relative_to(REPO_ROOT)}")
    return True


def scan_dir(dir_name: str, list_broken_only: bool = False) -> int:
    base = REPO_ROOT / dir_name
    files = sorted(base.glob("*.html"))
    fail = 0
    for f in files:
        missing = validate(f)
        if missing:
            fail += 1
            if list_broken_only:
                print(f.relative_to(REPO_ROOT))
            else:
                print(f"FAIL {f.relative_to(REPO_ROOT)}  (missing {len(missing)})")
    if not list_broken_only:
        print(f"---\n{dir_name}: {len(files)}개 중 {fail}개 실패")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="검사할 HTML 파일 경로")
    ap.add_argument("--all", action="store_true", help="reports_b 전체 검사 (또는 인자로 디렉토리 지정)")
    ap.add_argument("--list-broken", action="store_true", help="깨진 파일 경로만 한 줄씩 출력")
    args = ap.parse_args()

    if args.all:
        targets = args.paths if args.paths else ["reports_b"]
        total_fail = 0
        for d in targets:
            total_fail += scan_dir(d, list_broken_only=args.list_broken)
        return 1 if total_fail else 0

    if not args.paths:
        ap.print_help()
        return 2

    fail = 0
    for p in args.paths:
        path = Path(p)
        if not path.is_absolute():
            path = REPO_ROOT / path
        if not path.exists():
            print(f"NOT FOUND: {p}", file=sys.stderr)
            fail += 1
            continue
        if not report_one(path):
            fail += 1
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
