#!/bin/sh
set -eu

repositories="$(mktemp)"
trap 'rm -f "$repositories"' EXIT
printf '%s\n' 'https://dl-cdn.alpinelinux.org/alpine/v3.22/main' \
    > "$repositories"

reference() {
    apk --repositories-file "$repositories" --no-cache "$@"
}

apk --version
for package in curl jq zlib; do
    printf '\n=== GRAPH %s ===\n' "$package"
    reference dot "$package"
done
