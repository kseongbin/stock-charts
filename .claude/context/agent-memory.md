# 기업분석 에이전트 운영 노하우

## 데이터 수집 패턴

### DART 접근
- dart.fss.or.kr 직접 URL 패치는 신뢰할 수 없음 → 웹검색 우회 사용
- 효과적인 검색 패턴: `{기업명} {종목코드} 사업보고서 {연도} 매출실적`
- 특정 rcpNo URL 패치는 유효함
- majorPrdtSalesRvnu.json API 절대 사용 금지 (존재하지 않음)

### 재무 데이터 aggregator (신뢰도 높음)
- FnGuide: `comp.fnguide.com/SVO2/ASP/SVD_Main.asp?gicode=A{종목코드}`
- Butler Works: butler.works
- WiseReport: comp.wisereport.co.kr
- Saramin: saramin.co.kr
- Naver Finance: finance.naver.com/item/coinfo.naver?code={종목코드}
- Goinsider

### PDF 리포트 (고품질 데이터)
- Naver 투자정보 CDN: `ssl.pstatic.net/imgstock/upload/research/company/`
- Alpha Square (유진투자증권 등)
- 패치 시 `web_fetch_pdf_extract_text: True`, token limit ~6,000
- 매출구성, 주주현황, 연혁 데이터 효율적으로 추출 가능

### 검색 언어
- 한국 기업: 한국어 검색이 영어보다 효과적
- 해외 기업(글로벌 경쟁사): 현지 언어 검색 후 한국어 요약

### 경쟁사 조사
- 경쟁사별 개별 검색이 통합 검색보다 정확한 수치 확보

## 매출구성 처리
- 공시 원본 숫자 우선 (추정치 금지)
- DART에서 직접 확인 불가 시: aggregator 데이터 활용 후 각주 추가
  → "※ 위 수치는 [출처]에서 인용. 정확한 수치는 DART rcpNo {번호} 원문 확인 권장"

## 파일명 vs 종목코드 불일치 주의
- AGENT_MAPPING.md에 alias가 있는 경우: iframe URL에는 alias 파일명 사용
- Naver Finance 링크에는 실제 종목코드 사용
- 예: 자화전자 → mapping alias 006260 (iframe), Naver 033240 (링크)

## 상장 여부 확인
- KOSPI/KOSDAQ/KRX 미상장 기업 → 보고서 생성 불가, 조기 종료 후 안내

## 섹션 8 처리
- available.txt에서 종목코드 검색 → 없으면 섹션 8 완전 생략 (h4 포함)
- 있으면 확인된 번호만 img 태그 출력
