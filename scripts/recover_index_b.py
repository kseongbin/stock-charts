#!/usr/bin/env python3
"""
reports_b/_index.json 복구 스크립트.

B 루틴 에이전트가 _index.json을 부분 재작성하면서 기존 항목 약 100개가
유실된 사건(커밋 8f47c97)을 되돌린다. 디렉터리의 실제 HTML 파일을 기준으로
인덱스를 재구축한다.

복구 우선순위:
  1. 현재 _index.json 항목 (최신 메타 그대로 유지)
  2. 손상 직전 커밋(15d760f)의 _index.json
  3. git --diff-filter=A 첫 add 커밋 날짜 기반 추정

사용:
  python3 scripts/recover_index_b.py            # dry-run (변경 없음)
  python3 scripts/recover_index_b.py --write    # _index.json 저장
  python3 scripts/recover_index_b.py --write --regenerate-readme
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FOLDER = REPO / "reports_b"
INDEX_PATH = FOLDER / "_index.json"
LAST_GOOD_COMMIT = "15d760f"


def load_index_from_commit(commit: str) -> dict:
    result = subprocess.run(
        ["git", "show", f"{commit}:reports_b/_index.json"],
        cwd=REPO, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"[warn] {commit} 에서 _index.json 을 읽을 수 없음: {result.stderr.strip()}", file=sys.stderr)
        return {}
    return json.loads(result.stdout)


def first_add_date(html_path: Path) -> str:
    rel = html_path.relative_to(REPO).as_posix()
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%ad", "--date=short", "--", rel],
        cwd=REPO, capture_output=True, text=True, check=True,
    )
    dates = [line for line in result.stdout.strip().splitlines() if line]
    return dates[-1] if dates else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="실제로 _index.json 저장")
    parser.add_argument("--regenerate-readme", action="store_true", help="저장 후 regenerate_readme.py 실행")
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(f"[err] {INDEX_PATH} 없음", file=sys.stderr)
        return 1

    current = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    good = load_index_from_commit(LAST_GOOD_COMMIT)

    def normalize(entries: dict) -> dict:
        out = {}
        for k, v in entries.items():
            key = k[:-5] if k.endswith(".html") else k
            if "filename" not in v:
                v["filename"] = f"{key}.html"
            out[key] = v
        return out

    completed: dict = {}
    completed.update(normalize(good.get("completed", {})))
    completed.update(normalize(current.get("completed", {})))

    n_from_good = len(good.get("completed", {}))
    n_from_current = len(current.get("completed", {}))
    n_after_merge = len(completed)

    added_from_git: list[tuple[str, str]] = []
    for html in sorted(FOLDER.glob("*.html")):
        name = html.stem
        if name in completed:
            existing = completed[name]
            if existing.get("filename") != html.name:
                existing["filename"] = html.name
            continue
        date = first_add_date(html) or "2026-06-10"
        completed[name] = {
            "filename": html.name,
            "category": "일반",
            "generated_at": date,
        }
        added_from_git.append((name, date))

    orphans = [
        name for name in completed
        if not (FOLDER / completed[name].get("filename", f"{name}.html")).exists()
    ]

    new_index = {
        "description": current.get("description") or good.get("description") or "B 계정 처리 보고서 인덱스",
        "last_updated": max((v.get("generated_at", "") for v in completed.values()), default=""),
        "completed": completed,
    }

    print(f"현재 _index.json:           {n_from_current}개")
    print(f"직전 정상({LAST_GOOD_COMMIT}): {n_from_good}개")
    print(f"머지 후:                    {n_after_merge}개")
    print(f"git 로그로 복원:            {len(added_from_git)}개")
    if added_from_git:
        for name, date in added_from_git[:15]:
            print(f"  + {name} ({date})")
        if len(added_from_git) > 15:
            print(f"  ... 외 {len(added_from_git) - 15}건")
    if orphans:
        print(f"[warn] HTML 파일 없는 인덱스 항목 {len(orphans)}개: {orphans[:5]}{'...' if len(orphans) > 5 else ''}")
    print(f"최종 인덱스:                {len(completed)}개")
    print(f"디렉터리 HTML 파일:         {len(list(FOLDER.glob('*.html')))}개")

    if not args.write:
        print("\n(dry-run) 저장하려면 --write 옵션 추가")
        return 0

    INDEX_PATH.write_text(
        json.dumps(new_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n저장: {INDEX_PATH}")

    if args.regenerate_readme:
        script = REPO / "scripts" / "regenerate_readme.py"
        print(f"\n실행: python3 {script.relative_to(REPO)} reports_b")
        subprocess.run([sys.executable, str(script), "reports_b"], cwd=REPO, check=True)
    else:
        print("다음 단계: python3 scripts/regenerate_readme.py reports_b")
    return 0


if __name__ == "__main__":
    sys.exit(main())
