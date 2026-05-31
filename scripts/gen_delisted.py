"""
상장폐지 종목 HTML 생성 스크립트

Phase 2에서 yfinance 데이터 없음(no_data)으로 실패한 종목들에 대해
'상장폐지 종목' 안내 HTML 파일을 생성하고 GitHub에 push한 뒤
batch_state.json에서 charts_done으로 이동시킵니다.

사용법:
  python3 scripts/gen_delisted.py
  python3 scripts/gen_delisted.py --dry-run   # 파일 생성 없이 목록만 출력
"""

import os, json, re, subprocess, argparse, datetime

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS    = os.path.join(BASE, 'scripts')
STATE_FILE = os.path.join(SCRIPTS, 'batch_state.json')
LOG_FILE   = os.path.join(SCRIPTS, 'batch_log.txt')
CHART_SCRIPT = os.path.join(SCRIPTS, 'update_chart.py')
PUSH_EVERY = 100


def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def load_state():
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_code_to_info():
    """update_chart.py STOCKS에서 code → {name, filename} 매핑"""
    with open(CHART_SCRIPT, 'r', encoding='utf-8') as f:
        content = f.read()
    entries = re.findall(
        r'"ticker":\s*"([^"]+)",\s*"name":\s*"([^"]+)",\s*"code":\s*"([^"]+)",\s*"filename":\s*"([^"]+)"',
        content
    )
    return {code: {'ticker': ticker, 'name': name, 'filename': fname}
            for ticker, name, code, fname in entries}


def make_delisted_html(name, code, ticker):
    return f"""<html>
<head><meta charset="utf-8" /></head>
<body>
<p style="text-align:center;padding:60px 20px;font-family:sans-serif;color:#888;font-size:15px;">
  {name} ({code}) — 상장폐지 종목 (거래 데이터 없음)
</p>
</body>
</html>
"""


def git_commit_push(msg):
    subprocess.run(['git', 'add', '.'], cwd=BASE)
    r = subprocess.run(['git', 'commit', '-m', msg], cwd=BASE,
                       capture_output=True, text=True)
    if 'nothing to commit' in r.stdout + r.stderr:
        log("  (커밋할 내용 없음)")
        return
    result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE)
    if result.returncode == 0:
        _cleanup_local_html()
        log("  ✅ push 완료")
    else:
        log("  ⚠️  push 실패")


def _cleanup_local_html():
    r = subprocess.run(['git', 'ls-files', '*.html'], cwd=BASE,
                       capture_output=True, text=True)
    html_files = [f for f in r.stdout.splitlines() if f]
    if not html_files:
        return
    subprocess.run(['git', 'update-index', '--skip-worktree'] + html_files, cwd=BASE)
    removed = 0
    for f in html_files:
        path = os.path.join(BASE, f)
        if os.path.exists(path):
            os.remove(path)
            removed += 1
    if removed:
        log(f"  로컬 HTML {removed}개 삭제 (GitHub에는 유지)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='파일 생성 없이 목록만 출력')
    args = parser.parse_args()

    state = load_state()
    failed_chart = state.get('failed_chart', {})
    charts_done  = set(state.get('charts_done', []))

    # no_data 실패 종목만 대상
    targets = {code: err for code, err in failed_chart.items()
               if err == 'no_data' and code not in charts_done}

    code_to_info = get_code_to_info()

    log(f"상장폐지 HTML 생성 대상: {len(targets):,}개")

    if args.dry_run:
        for code in list(targets.keys())[:20]:
            info = code_to_info.get(code, {})
            print(f"  {code} | {info.get('name','?')} | {info.get('filename','?')}")
        print(f"  ... 총 {len(targets)}개")
        return

    ok = skip = 0
    codes_done_this_run = []

    for i, (code, _) in enumerate(targets.items(), 1):
        info = code_to_info.get(code)
        if not info:
            log(f"  [{i}] ⚠️  {code}: STOCKS에 없음, 스킵")
            skip += 1
            continue

        name     = info['name']
        filename = info['filename']
        ticker   = info['ticker']
        out_path = os.path.join(BASE, filename)

        html = make_delisted_html(name, code, ticker)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # batch_state: failed_chart → charts_done
        del state['failed_chart'][code]
        state['charts_done'].append(code)
        charts_done.add(code)
        codes_done_this_run.append(code)
        ok += 1

        if i % 50 == 0:
            log(f"  진행 {i}/{len(targets)} (✅{ok} ⏭️{skip})")

        if i % PUSH_EVERY == 0:
            save_state(state)
            git_commit_push(f'Batch delisted HTML {ok} done (gen_delisted)')

    save_state(state)
    git_commit_push(f'Batch delisted HTML complete: {ok} done, {skip} skipped')
    log(f"완료: ✅ {ok}개 생성, ⏭️ {skip}개 스킵")


if __name__ == '__main__':
    main()
