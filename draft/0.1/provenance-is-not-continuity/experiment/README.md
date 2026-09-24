# Experimental artifact — "Provenance Is Not Continuity"

Reproducible testbed for Section IX (Experimental Demonstration) and
Appendices A–B of the paper. Everything runs locally; no cloud account.

## What it is

- **Lab** (from the [PIC-X](https://github.com/pic-protocol/pic-x) repository,
  commit `1b485cd`, via `docker-compose.lab.yml`):
  - **Keycloak 26.7.0** — the OAuth 2.0 / OIDC authorization server (RFC 8693
    token exchange, DPoP), realm `acme-idp`, user `alice`.
  - **PIC-X v0.2.2** — the PIC Authority Broker and Exchange Server, built from
    source; realm `acme` maps the token's scopes to invariants and settles
    Profile 0.2 advancements. Protocol crate: `pic-protocol` 0.2.3 (crates.io).
  - **trust-lab** — a laboratory SD-JWT attestation issuer (issues to anyone;
    stands in for attestation infrastructure, per assumption A3).
- **mixer/** — Rust fault-injection harness linked against the same
  `pic-protocol` 0.2.3 crate PIC-X uses. Builds valid candidates and
  deliberately mixed ones (`mix-splice`, `mix-challenge`, `forge-union`),
  runs the ordinary downstream verifier (`verify-settled`), and measures
  in-process verification (`bench-verify`, `bench-jwt`, `bench-dpop`).
- **runner.py** — drives every run: the baseline resource server (a conformant
  RFC 6750 + RFC 9449 validator that logs each check individually), the agent
  with its fault-injection switches, the PIC-X runs, and the performance
  loops. Creates the two down-scoped client scopes and the DPoP-bound client
  in Keycloak through the admin API (idempotent).

## Run

```sh
./run.sh            # everything: pic, baseline, perf (N=100)
./run.sh pic        # PIC-X runs only (P0–P7)
./run.sh baseline   # OAuth 2.0 + DPoP baseline runs only (B0–B2)
./run.sh perf       # performance only (--n to change N)
./run.sh review     # review-response runs (P8, P9, P10, P3b)
```

Requirements: Docker, Rust 1.85+, Python 3.11+ with `cryptography`.

## Outputs

- `results/<run>.json` — one record per run: move, expected, observed
  (verbatim, never edited), per-check transcripts, timestamps.
- `results/machine.json` — CPU, OS, runtime and image versions, PIC-X commit.
- `logs/<run>.log` — human-readable transcript per run.
- `logs/pic-x-server-rejections.jsonl` — PIC-X server-side audit lines for the
  rejected advancements (the failing conjunct is named in `error`).

## Run map (paper ↔ artifact)

| Paper | Artifact | Shows |
|---|---|---|
| B0 | `results/B0-sanity.json` | Sanity: correct pairing accepted |
| B1 | `results/B1-mix.json` | Theorem 1: mix accepted, all 17 checks pass |
| B1b | `results/B1b-accumulator.json` | Reachable interleaving without intent |
| B2 | `results/B2-exec-id.json` | Lemma 2 (receiver-side variant) |
| P0 | `results/P0-setup.json` | Two lineages from one grant; valid continuations |
| P1 | `results/P1-mix-splice.json` | Predecessor-binding rejection |
| P2 | `results/P2-mix-challenge.json` | Challenge-continuity rejection |
| P3 | `results/P3-forge-union.json` | Corollary 1: union rejected (forged checkpoint) |
| P4 | `results/P4-carol-joins.json` | T4 / open continuation, κ satisfied |
| P5 | `results/P5-carol-wrong-department.json` | κ violation rejected |
| P6 | `results/P6-duplicate-delivery.json` | Prop. 3: P holds twice, U absent |
| P7 | `results/P7-revocation.json` | Omission record: revocation not implemented |
| P8 | `results/P8-honest-cross-use.json` | Honest cross-use accepted as X_A (attribution, not prevention) |
| P9 | `results/P9-lineage-lock.json` | Occurrence policy at the receiver; inexpressible under the baseline |
| P10 | `results/P10-single-lineage.json` | Lineage granularity is an origination decision |
| P3b | `results/P3b-bad-bitmap.json` | Settlement-side attenuation validation is live |
| R9 | `results/R9-performance.json` | Latencies, sizes, in-process verification |

## Honesty notes

- Observed outcomes are recorded verbatim from HTTP responses, server logs,
  and verifier outputs; the runner never edits them.
- The duplicate-delivery run redelivers explicitly in-process (documented in
  the paper's threats-to-validity; the delivery contract is what is modeled).
- Revocation and composition are not implemented in PIC-X at this commit; the
  corresponding runs are omitted, not simulated.
