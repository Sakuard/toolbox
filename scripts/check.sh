#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
while IFS= read -r script; do
  bash -n "$script"
  [[ -x "$script" ]] || { echo "Not executable: $script" >&2; exit 1; }
done < <(find bin commands -type f)
[[ "$(bin/tbx --version)" == "tbx dev" ]]
[[ "$(bin/tbx -v)" == "tbx dev" ]]
if bin/tbx does-not-exist 2>/dev/null; then
  echo 'Unknown command should fail' >&2
  exit 1
fi
echo "Checks passed"
