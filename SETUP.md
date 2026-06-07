# 배치 자동화 설정 가이드

## 개요
`scripts/batch_reports.py`가 `reports/_queue.json`의 기업을 순서대로 처리해
완성된 HTML 보고서를 `reports/` 폴더에 저장하고 GitHub에 자동 push합니다.

---

## 1회 수동 실행 (테스트)

```bash
cd /path/to/stock-charts
python scripts/batch_reports.py
```

---

## /schedule로 자동 cron 등록 (추천)

Claude Code에서 아래 명령 실행:

```
/schedule
```

설정값:
- **이름**: `기업분석 배치`
- **주기**: `0 */5 * * *` (5시간마다)
- **실행 명령**: `python scripts/batch_reports.py`
- **작업 디렉토리**: `/path/to/stock-charts`

---

## 보고서 티스토리 발행 방법

1. `github.com/kseongbin/stock-charts/tree/main/reports/` 접속
2. `reports/README.md` 열기 → 원하는 기업의 **Raw** 링크 클릭
3. `Ctrl+A` → `Ctrl+C`
4. 티스토리 글쓰기 → **HTML 모드** → `Ctrl+V` → 발행

---

## 큐 관리

새 기업 추가:
```json
// reports/_queue.json 의 "queue" 배열에 추가
{"name": "기업명", "category": "카테고리"}
```

처리 완료 현황: `reports/README.md` 또는 `reports/_index.json` 확인

---

## GitHub push 권한 설정 (최초 1회)

```bash
gh auth login
# 또는
git remote set-url origin https://{TOKEN}@github.com/kseongbin/stock-charts.git
```
