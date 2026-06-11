#!/usr/bin/env python3
"""
보고서 HTML 의 v24 마크업을 강제로 정규화.

LLM 에이전트가 자기 마음대로 단순화한 마크업
(예: `<b>▶&nbsp;X</b>&nbsp;:`)을 v24 템플릿 형식
(예: `<b>▶<span>&nbsp;</span>X</b><span>&nbsp;</span>:`)로 일관 변환.

사용법:
  단일 파일:   python3 scripts/normalize_html.py reports/FSN.html
  폴더 일괄:   python3 scripts/normalize_html.py reports/
  여러 파일:   python3 scripts/normalize_html.py reports/A.html reports/B.html
"""
import re
import sys
from pathlib import Path

# 공백류: 공백, &nbsp;, <span>...</span> 류
WS = r"(?:\s|&nbsp;|<span[^>]*>(?:\s|&nbsp;)*</span>)+"


def normalize(html: str) -> str:
    # 1. 섹션 2 [주요 사업] 글머리: data-path-to-node="1"
    #    <b>▶ X </b> :  →  <b>▶<span>&nbsp;</span>X</b><span>&nbsp;</span>:
    def sec2_bullet(m: re.Match) -> str:
        prefix, name, close = m.group(1), m.group(2).strip(), m.group(3)
        return f"{prefix}<span>&nbsp;</span>{name}{close}<span>&nbsp;</span>:"

    html = re.sub(
        r'(<p [^>]*data-path-to-node="1"[^>]*><b>▶)'
        + WS
        + r"(.*?)"
        + r"(</b>)"
        + WS
        + r":",
        sec2_bullet,
        html,
        flags=re.DOTALL,
    )

    # 2. 섹션 3 [최근 시장 관심 이유] 글머리: data-path-to-node="3"
    #    + 헤딩이 [최근 시장 관심 이유] 이후의 글머리만 해당 (사업개요 섹션과 구분)
    #    <b>▶ X </b> :  →  <b>▶<span> X</span></b><span>&nbsp;</span>:
    def sec3_bullet(m: re.Match) -> str:
        prefix, title, close = m.group(1), m.group(2).strip(), m.group(3)
        return f"{prefix}<span> {title}</span>{close}<span>&nbsp;</span>:"

    # 섹션 3 글머리는 [최근 시장 관심 이유] 블록과 사업개요(4) 블록 둘 다에서 사용됨
    # 우선 단순 패턴 (span 으로 텍스트 감싸지 않은 형태)만 변환
    html = re.sub(
        r'(<p [^>]*data-path-to-node="3"[^>]*><b>▶)'
        + r"(?!<span>)"  # 이미 <span> 으로 감싸진 정상 패턴은 건너뜀
        + WS
        + r"([^<]*?)"  # 제목 (HTML 태그 없는 단순 텍스트)
        + r"(</b>)"
        + WS
        + r":",
        sec3_bullet,
        html,
    )

    # 3. 핵심 사업 / 핵심 기술 / 신규 사업 글머리 (size16, path 3)
    #    <b>▶<span>&nbsp;</span>X</b><span>&nbsp;</span>: 가 v24 형식
    #    이미 위 #2 에서 처리됨

    # 4. iframe 도메인 강제: raw.githack.com → kseongbin.github.io/stock-charts
    html = re.sub(
        r"https?://raw\.githack\.com/kseongbin/stock-charts/main/",
        "https://kseongbin.github.io/stock-charts/",
        html,
    )

    # 5. HTML 주석 제거 (티스토리 fragment 에 불필요)
    html = re.sub(r"<!--.*?-->\s*", "", html, flags=re.DOTALL)

    return html


def process(path: Path) -> bool:
    """파일 정규화. 변경 있으면 True, 없으면 False."""
    original = path.read_text(encoding="utf-8")
    normalized = normalize(original)
    if original == normalized:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    targets: list[Path] = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            targets.extend(sorted(p.glob("*.html")))
        elif p.is_file():
            targets.append(p)
        else:
            print(f"skip (not found): {arg}", file=sys.stderr)

    changed = 0
    for p in targets:
        if process(p):
            print(f"normalized: {p}")
            changed += 1
    print(f"\n총 {len(targets)}개 검사 / {changed}개 정규화")


if __name__ == "__main__":
    main()
