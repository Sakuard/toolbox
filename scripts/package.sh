#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:-$(git branch --show-current)}"
[[ "$tag" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || {
  echo 'Expected a version branch/tag: vX.Y.Z (or pass it as the first argument)' >&2
  exit 1
}
bash scripts/check.sh
version="${tag#v}"
mkdir -p dist
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/toolbox-$version"
cp -R bin commands lib LICENSE README.md "$stage/toolbox-$version/"
printf '%s\n' "$version" > "$stage/toolbox-$version/VERSION"
tar -czf "dist/toolbox-$version.tar.gz" -C "$stage" "toolbox-$version"
(cd dist && shasum -a 256 "toolbox-$version.tar.gz" > SHA256SUMS)
mkdir -p "$stage/install" "$stage/bin"
tar -xzf "dist/toolbox-$version.tar.gz" -C "$stage/install"
ln -s "$stage/install/toolbox-$version/bin/tbx" "$stage/bin/tbx"
[[ "$("$stage/bin/tbx" --version)" == "tbx $version" ]]
[[ -x "$stage/install/toolbox-$version/commands/kube/logs" ]]
echo "Package verified: dist/toolbox-$version.tar.gz"
