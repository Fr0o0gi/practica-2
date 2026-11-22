#!/bin/sh
set -eu

root="$(mktemp -d)"
trap 'rm -rf "$root"' EXIT
mkdir -p "$root/etc/apk" "$root/etc/ssl"
cp -R /etc/apk/keys "$root/etc/apk/keys"
cp -R /etc/ssl/certs "$root/etc/ssl/certs"
printf '%s\n' 'https://dl-cdn.alpinelinux.org/alpine/v3.22/main' \
    > "$root/etc/apk/repositories"

apk --version
apk --root "$root" --arch x86_64 --initdb update
for package in curl jq zlib; do
    printf '\n=== FETCH %s ===\n' "$package"
    apk --root "$root" fetch -R --url "$package"
    printf '\n=== GRAPH %s ===\n' "$package"
    apk --root "$root" dot "$package"
done
