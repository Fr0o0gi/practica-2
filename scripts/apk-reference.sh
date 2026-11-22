#!/bin/sh
set -eu

work="$(mktemp -d)"
repositories="$work/repositories"
trap 'rm -rf "$work"' EXIT
printf '%s\n' 'https://dl-cdn.alpinelinux.org/alpine/v3.22/main' \
    > "$repositories"

reference() {
    apk --repositories-file "$repositories" --no-cache "$@"
}

apk --version
for package in curl jq zlib; do
    printf '\n=== FETCH %s ===\n' "$package"
    mkdir "$work/$package"
    reference fetch -R --url -o "$work/$package" "$package"
    printf '\n=== GRAPH %s ===\n' "$package"
    reference dot "$package"
done
