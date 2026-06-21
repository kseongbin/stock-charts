#!/bin/sh
# 보고서 검증 git pre-commit 훅 설치.
# 한 번만 실행하면 끝. 이후 모든 커밋이 자동 검증됨.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK_SRC="$REPO_ROOT/scripts/git-hooks/pre-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"

if [ ! -f "$HOOK_SRC" ]; then
    echo "ERROR: $HOOK_SRC 없음" >&2
    exit 1
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "✓ pre-commit 훅 설치 완료: $HOOK_DST"
echo "  → 이후 reports_b/*.html 커밋 시 자동 검증됩니다."
echo "  → 우회가 필요하면 'git commit --no-verify' (위급할 때만)."
