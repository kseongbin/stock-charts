"""
특정 기업들을 배치 처리 우선순위 앞으로 이동시키는 스크립트.
batch_state.json의 registered 리스트에서 대상 기업을 앞으로 재배치.
"""

import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE, 'scripts', 'batch_state.json')

TARGET_NAMES = [
    # 전력기기/송전
    "효성중공업", "LS ELECTRIC", "일진전기", "제룡전기", "세명전기", "제룡산업",
    "보성파워텍", "지투파워", "한전산업", "키스트론", "그리드위즈", "산일전기",
    # 전선/소재
    "대한전선", "가온전선", "대원전선", "LS", "LS마린솔루션", "풍산", "대창",
    "이구산업", "티씨머티리얼즈",
    # 에너지/발전
    "지엔씨에너지",
    # 통신장비
    "케이엠더블유", "에이스테크", "쏠리드", "서진시스템", "RFHIC", "오이솔루션",
    "기가레인", "우리넷", "유비쿼스", "에프알텍", "옵티코어", "라이콤",
    "센서뷰", "대한광통신",
    # 광통신/양자
    "빛과전자", "이노인스트루먼트", "옵티시스", "드림시큐리티", "엑스게이트",
    "한국첨단소재",
    # 반도체/장비
    "SK하이닉스", "삼성전자", "네패스아크", "인텍플러스", "에스에이엠티",
    "피델릭스", "심텍홀딩스", "피엠티", "주성엔지니어링", "미래산업",
    # MLCC/전자부품
    "코스텍시스템", "삼화콘덴서공업", "삼화전기", "삼성전기", "코칩", "서울전자통신",
    # 유리기판
    "제이앤티씨", "기가비스", "SKC",
    # AI S/W
    "오픈베이스", "링네트", "모아데이타", "파이오링크", "오브젠",
    "플리토", "씨이랩", "포톤",
    # 대기업 SI
    "현대오토에버", "삼성에스디에스", "롯데이노베이트", "LG씨엔에스",
    # 2차전지
    "LG에너지솔루션", "더블유씨피", "삼성SDI", "대주전자재료", "메가터치",
    "에이프로", "나노팀", "테이팩스", "리튬포어스", "하이드로리튬", "강원에너지",
    # 자동차 부품
    "현대모비스", "한온시스템", "현대자동차", "현대위아", "에스엘",
    # 로봇
    "마키나락스", "라온로보틱스", "한국피아이엠", "코스모로보틱스",
    "제닉스로보틱스", "아이로보틱스",
    # 조선/우주항공
    "한화오션", "HD현대중공업", "HD한국조선해양", "켄코아에어로스페이스",
    "에이치브이엠", "AP위성", "베셀",
    # LG그룹
    "LG전자", "LG이노텍", "LG", "LG디스플레이",
    # 제약/바이오
    "디앤디파마텍", "코아스템켐온", "네이처셀", "지아이이노베이션", "현대바이오",
    "피플바이오", "엑셀세라퓨틱스", "한올바이오파마",
    # 진단키트/치매
    "메이슨캐피탈", "삼진제약", "차백신연구소", "녹십자엠에스", "수젠텍",
    "랩지노믹스", "진원생명과학",
    # 핀테크/플랫폼
    "코나아이", "나이스정보통신", "웹케시", "에스아이리소스", "나노캠텍",
    "조이웍스앤코", "한성크린텍", "코이즈", "성문전자", "티웨이홀딩스",
]

def main():
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # 이름 → 코드 매핑 (all_companies 기준)
    name_to_code = {}
    for c in state['all_companies']:
        name_to_code[c['name']] = c['code']

    # 대상 코드 집합 찾기
    target_codes = set()
    not_found = []
    for name in TARGET_NAMES:
        if name in name_to_code:
            target_codes.add(name_to_code[name])
        else:
            not_found.append(name)

    if not_found:
        print(f"⚠️  배치 목록에 없는 기업 ({len(not_found)}개):")
        for n in not_found:
            print(f"   - {n}")

    # 이미 완료/실패된 종목 제외 (재배치할 의미 없음)
    fin_done = set(state['financials_done'])
    fin_fail = set(state['failed_financial'].keys())

    pending_targets = [c for c in target_codes if c not in fin_done and c not in fin_fail]
    already_done   = [c for c in target_codes if c in fin_done]
    already_failed = [c for c in target_codes if c in fin_fail]

    print(f"\n대상 기업 총 {len(target_codes)}개:")
    print(f"  재무 완료: {len(already_done)}개")
    print(f"  재무 실패: {len(already_failed)}개")
    print(f"  재무 미완료 (우선 처리 대상): {len(pending_targets)}개")

    if not pending_targets:
        print("\n✅ 모든 대상 기업이 이미 처리 완료됨. 재배치 불필요.")
        return

    # registered 리스트 재배치: target_pending → 나머지 순
    target_set = set(pending_targets)
    others = [c for c in state['registered'] if c not in target_set]
    # target은 TARGET_NAMES 순서 유지
    ordered_targets = []
    seen = set()
    for name in TARGET_NAMES:
        code = name_to_code.get(name)
        if code and code in target_set and code not in seen:
            ordered_targets.append(code)
            seen.add(code)

    state['registered'] = ordered_targets + others

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"\n✅ batch_state.json 재배치 완료: {len(ordered_targets)}개 우선 처리 대상을 맨 앞으로 이동")
    print(f"   다음 배치 실행 시 이 기업들부터 처리됩니다.")

    # 이름 → 코드 매핑 출력 (확인용)
    code_to_name = {c['code']: c['name'] for c in state['all_companies']}
    print(f"\n우선 처리될 기업 목록:")
    for i, code in enumerate(ordered_targets, 1):
        status = ""
        if code in fin_done:
            status = " [완료]"
        print(f"  {i:3d}. [{code}] {code_to_name.get(code, '?')}{status}")

if __name__ == '__main__':
    main()
