#!/bin/sh
# Copyright (c) 2026 Nitro Agility S.r.l.
# SPDX-License-Identifier: Apache-2.0
#
# One-command runner for the experimental section of
# "Provenance Is Not Continuity".
#
#   ./run.sh            start the lab, build the harness, run every run
#   ./run.sh pic        only the PIC-X runs
#   ./run.sh baseline   only the OAuth 2.0 + DPoP baseline runs
#   ./run.sh perf       only the performance runs
#
# Requirements: Docker, Rust 1.85+, Python 3.11+ with `cryptography`.

set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
if [ -z "${PIC_X_REPO:-}" ]; then
    dir="$HERE"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/pic-x/Cargo.toml" ]; then PIC_X_REPO="$dir/pic-x"; break; fi
        dir=$(dirname "$dir")
    done
fi
if [ -z "${PIC_X_REPO:-}" ] || [ ! -f "$PIC_X_REPO/docker-compose.lab.yml" ]; then
    echo "pic-x repository not found; set PIC_X_REPO" >&2
    exit 1
fi

echo "== starting the PIC-X compose lab (Keycloak 26.7.0 + PIC-X + trust-lab)"
docker compose -f "$PIC_X_REPO/docker-compose.lab.yml" up -d --build

echo "== building the fault-injection harness (pic-protocol 0.2.3)"
cargo build --release --manifest-path "$HERE/mixer/Cargo.toml"

echo "== waiting for the lab services"
for url in \
    "http://localhost:18080/realms/acme-idp/.well-known/openid-configuration" \
    "http://localhost:17556/.well-known/server-configuration" \
    "http://localhost:17080/"; do
    until curl -fsS -m 2 "$url" >/dev/null 2>&1; do sleep 2; done
done

echo "== running"
python3 "$HERE/runner.py" "$@"

echo "== done; see results/*.json and logs/*.log"
