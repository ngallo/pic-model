#!/usr/bin/env python3
# Copyright (c) 2026 Nitro Agility S.r.l.
# SPDX-License-Identifier: Apache-2.0

"""Experiment runner for "Provenance Is Not Continuity".

Drives the PIC-X compose lab (Keycloak 26.7.0 + PIC-X + trust-lab) through the
runs of the paper's experimental section. Every run writes one JSON record to
results/ and a human-readable transcript to logs/. Observed outcomes are
recorded verbatim; nothing is edited.

Usage:
    python3 runner.py [pic] [baseline] [perf] [--n 100]
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import os
import platform
import secrets
import socket
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

HERE = Path(__file__).resolve().parent


def pic_x_repo() -> Path:
    """The PIC-X repository: $PIC_X_REPO, or the nearest `pic-x` checkout found
    walking up from this file (the harness lives beside the repos it drives)."""
    env = os.environ.get("PIC_X_REPO")
    if env:
        return Path(env)
    for parent in HERE.parents:
        candidate = parent / "pic-x"
        if (candidate / "Cargo.toml").exists():
            return candidate
    return HERE
RESULTS = HERE / "results"
LOGS = HERE / "logs"
MIXER = HERE / "mixer" / "target" / "release" / "pic-mixer"

KEYCLOAK = "http://localhost:18080"
KC_REALM = "acme-idp"
KC_CLIENT = "acme-idp-client"
KC_SECRET = "acme-idp-client-secret"
KC_USER, KC_PASSWORD = "alice", "alice-password"
KC_ADMIN, KC_ADMIN_PASSWORD = "admin", "admin"

PIC_X = "http://localhost:17556"
PIC_REALM = "acme"
TRUST_LAB = "http://localhost:17080"
ATTESTER = "acme-por-attester"

TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"
ACCESS_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
PIC_TOKEN_TYPE = "https://pic-protocol.org/definitions/token-types/pic"
INITIAL_PROPOSAL_TYPE = (
    "https://pic-protocol.org/definitions/proposal-types/continuity-initial"
)

BASELINE_CLIENT = "baseline-agent"
BASELINE_SECRET = "baseline-agent-secret"
BASELINE_AUDIENCE = "baseline-rs"
SCOPE_READ = "documents.read"
SCOPE_WRITE = "storage.write"
RS_PORT = 9401

WORKLOAD_CLAIMS = {
    "corporation": "ACME",
    "department": "sensitive-documents",
    "workload_role": "pipeline-worker",
}
CAROL_CLAIMS = {
    "corporation": "ACME",
    "department": "sensitive-documents",
    "workload_role": "carol-service",
}
CAROL_BAD_CLAIMS = {
    "corporation": "ACME",
    "department": "marketing",
    "workload_role": "carol-service",
}
DISCLOSED = ["corporation", "department"]


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def unb64url(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def jwt_payload(token: str) -> dict:
    return json.loads(unb64url(token.split(".")[1]))


def jwt_header(token: str) -> dict:
    return json.loads(unb64url(token.split(".")[0]))


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------- HTTP helpers


def http(
    method: str,
    url: str,
    *,
    form: dict | None = None,
    body: bytes | None = None,
    headers: dict | None = None,
    json_body: dict | None = None,
) -> tuple[int, dict | str, float]:
    """One HTTP request; returns (status, decoded body, milliseconds)."""
    send_headers = {"Accept": "application/json"}
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        send_headers["Content-Type"] = "application/x-www-form-urlencoded"
    if json_body is not None:
        body = json.dumps(json_body).encode()
        send_headers["Content-Type"] = "application/json"
    if headers:
        send_headers.update(headers)
    request = urllib.request.Request(url, data=body, headers=send_headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read()
        status = error.code
    elapsed = (time.perf_counter() - start) * 1000
    try:
        decoded: dict | str = json.loads(raw)
    except json.JSONDecodeError:
        decoded = raw.decode(errors="replace")
    return status, decoded, elapsed


# ---------------------------------------------------------------- lab clients


def keycloak_password_grant(
    scope: str | None = None,
    client: str = KC_CLIENT,
    secret: str = KC_SECRET,
    dpop_key: ec.EllipticCurvePrivateKey | None = None,
) -> tuple[dict, float]:
    endpoint = f"{KEYCLOAK}/realms/{KC_REALM}/protocol/openid-connect/token"
    form = {
        "grant_type": "password",
        "client_id": client,
        "client_secret": secret,
        "username": KC_USER,
        "password": KC_PASSWORD,
    }
    if scope:
        form["scope"] = scope
    headers = {}
    if dpop_key is not None:
        headers["DPoP"] = dpop_proof(dpop_key, "POST", endpoint)
    status, payload, ms = http("POST", endpoint, form=form, headers=headers)
    if status != 200:
        raise RuntimeError(f"password grant failed ({status}): {payload}")
    return payload, ms


def keycloak_token_exchange(access_token: str) -> tuple[int, dict | str, float]:
    endpoint = f"{KEYCLOAK}/realms/{KC_REALM}/protocol/openid-connect/token"
    form = {
        "grant_type": TOKEN_EXCHANGE_GRANT,
        "subject_token": access_token,
        "subject_token_type": ACCESS_TOKEN_TYPE,
        "client_id": KC_CLIENT,
        "client_secret": KC_SECRET,
        "audience": "pic-x",
    }
    return http("POST", endpoint, form=form)


def initial_proposal_wire() -> str:
    proposal = {
        "type": INITIAL_PROPOSAL_TYPE,
        "executionContract": {
            "corporation": "ACME",
            "department": "sensitive-documents",
        },
    }
    return b64url(json.dumps(proposal).encode())


def pic_initial_exchange(access_token: str) -> tuple[int, dict | str, float]:
    form = {
        "grant_type": TOKEN_EXCHANGE_GRANT,
        "subject_token": access_token,
        "subject_token_type": ACCESS_TOKEN_TYPE,
        "requested_token_type": PIC_TOKEN_TYPE,
        "continuity_proposal": initial_proposal_wire(),
    }
    return http("POST", f"{PIC_X}/realms/{PIC_REALM}/token", form=form)


def pic_advancement(candidate_token: str) -> tuple[int, dict | str, float]:
    form = {
        "grant_type": TOKEN_EXCHANGE_GRANT,
        "subject_token": candidate_token,
        "subject_token_type": PIC_TOKEN_TYPE,
        "requested_token_type": PIC_TOKEN_TYPE,
    }
    return http("POST", f"{PIC_X}/realms/{PIC_REALM}/token", form=form)


def trust_lab_credential(jwk: dict, claims: dict) -> str:
    status, credential, _ = http(
        "POST",
        f"{TRUST_LAB}/attesters/{ATTESTER}/credentials",
        json_body={"cnf_jwk": jwk, "claims": claims, "validity_seconds": 900},
    )
    if status != 200:
        raise RuntimeError(f"credential issuance failed ({status}): {credential}")
    selected = [
        item["disclosure"]
        for item in credential["disclosures"]
        if item.get("claim") in DISCLOSED
    ]
    if len(selected) != len(DISCLOSED):
        raise RuntimeError("the attester did not issue the required disclosures")
    return credential["issuer_signed_jwt"] + "".join("~" + d for d in selected) + "~"


def mixer(*arguments: str) -> dict:
    finished = subprocess.run(
        [str(MIXER), *arguments], capture_output=True, text=True, timeout=120
    )
    if finished.returncode != 0:
        raise RuntimeError(f"pic-mixer failed: {finished.stderr.strip()}")
    return json.loads(finished.stdout)


def realm_jwks() -> list[dict]:
    status, payload, _ = http("GET", f"{PIC_X}/realms/{PIC_REALM}/keys")
    if status != 200:
        raise RuntimeError(f"realm JWKS unavailable ({status}): {payload}")
    return payload["keys"]


def verify_settled_any(token: str) -> dict:
    """Ordinary downstream verification, tried against every key the realm
    publishes (PIC Token JWT headers carry no kid in this build)."""
    outcome: dict = {"outcome": "rejected", "reason": "no realm key published"}
    for key in realm_jwks():
        outcome = mixer("verify-settled", "--token", token, "--jwk", json.dumps(key))
        if outcome.get("outcome") == "accepted":
            return outcome
    return outcome


# ------------------------------------------------------------------ recording


class Run:
    def __init__(self, run_id: str, mechanism: str, move: str, expected: str):
        self.record = {
            "run": run_id,
            "mechanism": mechanism,
            "move": move,
            "expected": expected,
            "observed": None,
            "accepted": None,
            "started": now_iso(),
            "events": [],
        }
        self.lines: list[str] = [
            f"== {run_id} :: {mechanism}",
            f"move     : {move}",
            f"expected : {expected}",
            f"started  : {self.record['started']}",
            "",
        ]

    def log(self, text: str, **data):
        self.lines.append(text)
        if data:
            self.record["events"].append({"note": text, **data})
        print(f"    {text}")

    def finish(self, observed: str, accepted: bool | None, **extra):
        self.record["observed"] = observed
        self.record["accepted"] = accepted
        self.record.update(extra)
        self.record["finished"] = now_iso()
        self.lines += ["", f"observed : {observed}", f"accepted : {accepted}"]
        run_id = self.record["run"]
        (RESULTS / f"{run_id}.json").write_text(json.dumps(self.record, indent=2))
        (LOGS / f"{run_id}.log").write_text("\n".join(self.lines) + "\n")
        print(f"[{run_id}] observed: {observed}")


# -------------------------------------------------------------- PIC-X lineage


def advance(
    pic_token: str,
    *,
    claims: dict,
    remove_invariant: int | None = None,
    label: str = "",
    run: Run | None = None,
) -> tuple[int, dict | str, float, dict]:
    """One complete workload hop against the running PIC-X realm."""
    keys = mixer("keygen")
    presentation = trust_lab_credential(keys["jwk"], claims)
    checkpoint = mixer("inspect", "--token", pic_token)
    arguments = [
        "candidate",
        "--pca",
        checkpoint["pca"],
        "--presentation",
        presentation,
        "--seed",
        keys["seed"],
    ]
    if remove_invariant is not None:
        arguments += ["--remove-invariant", str(remove_invariant)]
    candidate = mixer(*arguments)
    status, payload, ms = pic_advancement(candidate["token"])
    if run:
        run.log(
            f"{label}: settlement answered {status} in {ms:.1f} ms",
            status=status,
            response=payload if status != 200 else {"issued": True},
        )
    return status, payload, ms, candidate


def build_two_lineages(run: Run) -> tuple[str, str, str]:
    """One grant, two occurrences: lineage A keeps storage:save, lineage B
    keeps documents:read:document-42."""
    access, _ = keycloak_password_grant()
    run.log(
        f"access token obtained: scopes {jwt_payload(access['access_token']).get('pic_scopes')}"
    )
    token = access["access_token"]

    lineages = {}
    for name, remove in (("A", 0), ("B", 1)):
        status, payload, ms = pic_initial_exchange(token)
        if status != 200:
            raise RuntimeError(f"initial exchange failed: {payload}")
        pic0 = payload["access_token"]
        info0 = mixer("inspect", "--token", pic0)
        run.log(
            f"lineage {name}: PCA0 lineage_id={info0['lineage_id']} "
            f"invariants={info0['invariants']} ({ms:.1f} ms)"
        )
        status, payload, ms, _ = advance(
            pic0,
            claims=WORKLOAD_CLAIMS,
            remove_invariant=remove,
            label=f"lineage {name} attenuation hop",
            run=run,
        )
        if status != 200:
            raise RuntimeError(f"attenuation hop failed: {payload}")
        pic1 = payload["access_token"]
        info1 = mixer("inspect", "--token", pic1)
        run.log(
            f"lineage {name}: PCA1 position={info1['position']} "
            f"invariants={info1['invariants']}"
        )
        lineages[name] = pic1

    return token, lineages["A"], lineages["B"]


def pic_runs():
    setup = Run(
        "P0-setup",
        "PIC-X",
        "Two occurrences of one grant, attenuated to write-only (A) and read-only (B); "
        "one further valid continuation of each",
        "All four advancements accepted",
    )
    token, pic_a, pic_b = build_two_lineages(setup)
    info_a = mixer("inspect", "--token", pic_a)
    info_b = mixer("inspect", "--token", pic_b)

    # A further valid continuation of each lineage, so later rejections are
    # attributable to the mix and not to the harness.
    status_a, payload_a, _, _ = advance(
        pic_a, claims=WORKLOAD_CLAIMS, label="valid continuation of A", run=setup
    )
    status_b, payload_b, _, _ = advance(
        pic_b, claims=WORKLOAD_CLAIMS, label="valid continuation of B", run=setup
    )
    setup.finish(
        f"lineage A: {info_a['invariants']}; lineage B: {info_b['invariants']}; "
        f"valid continuations answered {status_a} and {status_b}",
        status_a == 200 and status_b == 200,
        lineage_a=info_a,
        lineage_b=info_b,
    )

    keys = mixer("keygen")
    presentation = trust_lab_credential(keys["jwk"], WORKLOAD_CLAIMS)
    pca_a = info_a["pca"]
    pca_b = info_b["pca"]

    # R3a — authority of A presented while the transition answers B.
    run = Run(
        "P1-mix-splice",
        "PIC-X",
        "Candidate presents lineage A's checkpoint (write) while predecessor.hash and "
        "previous_challenge answer lineage B's checkpoint (read)",
        "Rejected; the verifier names the predecessor-binding conjunct",
    )
    mixed = mixer(
        "mix-splice",
        "--pca-trusted", pca_a,
        "--pca-other", pca_b,
        "--presentation", presentation,
        "--seed", keys["seed"],
    )
    status, payload, ms = pic_advancement(mixed["token"])
    run.log(f"settlement answered {status} in {ms:.1f} ms", status=status, response=payload)
    run.finish(
        f"{status}: {payload.get('error_description') if isinstance(payload, dict) else payload}",
        status == 200,
    )

    # R3b — correct predecessor reference for A, but B's challenge.
    run = Run(
        "P2-mix-challenge",
        "PIC-X",
        "Candidate on lineage A whose transition answers lineage B's challenge",
        "Rejected; the verifier names the challenge-continuity conjunct",
    )
    mixed = mixer(
        "mix-challenge",
        "--pca-trusted", pca_a,
        "--pca-other", pca_b,
        "--presentation", presentation,
        "--seed", keys["seed"],
    )
    status, payload, ms = pic_advancement(mixed["token"])
    run.log(f"settlement answered {status} in {ms:.1f} ms", status=status, response=payload)
    run.finish(
        f"{status}: {payload.get('error_description') if isinstance(payload, dict) else payload}",
        status == 200,
    )

    # R4 — the union C_A ∪ C_B presented as one successor.
    run = Run(
        "P3-forge-union",
        "PIC-X",
        "Workload-signed checkpoint carrying the union of both lineages' invariants, "
        "wrapped in an otherwise well-formed candidate",
        "Rejected; the checkpoint is not one the realm issued",
    )
    forged = mixer(
        "forge-union",
        "--pca-a", pca_a,
        "--pca-b", pca_b,
        "--presentation", presentation,
        "--seed", keys["seed"],
    )
    status, payload, ms = pic_advancement(forged["token"])
    run.log(f"settlement answered {status} in {ms:.1f} ms", status=status, response=payload)
    downstream = verify_settled_any(forged["token"])
    genuine = verify_settled_any(pic_a)
    run.log(f"ordinary downstream verifier on the forged token: {downstream}")
    run.log(f"ordinary downstream verifier on the genuine settled token: {genuine['outcome']}")
    run.finish(
        f"settlement {status}: "
        f"{payload.get('error_description') if isinstance(payload, dict) else payload}; "
        f"downstream verifier: {downstream['outcome']} ({downstream.get('reason', '')})",
        status == 200,
    )

    # Note: an attenuation that *adds* an invariant is not expressible in the
    # transition grammar (remove-only bitmaps), so the union cannot even be
    # proposed as an attenuation of either lineage. Recorded as a fact of the
    # wire format, not as a run.

    # R5 — Carol, unknown at origination, joins with a conforming attestation.
    run = Run(
        "P4-carol-joins",
        "PIC-X",
        "A workload key created after origination advances lineage B with an "
        "attestation satisfying the execution contract",
        "Accepted",
    )
    status, payload, ms, _ = advance(
        pic_b, claims=CAROL_CLAIMS, label="carol advancement", run=run
    )
    observed = (
        f"{status}: settled to position "
        f"{mixer('inspect', '--token', payload['access_token'])['position']}"
        if status == 200
        else f"{status}: {payload}"
    )
    run.finish(observed, status == 200)

    # R5b — Carol with an attestation violating the execution contract.
    run = Run(
        "P5-carol-wrong-department",
        "PIC-X",
        "Same move with an attestation disclosing department=marketing against a "
        "contract requiring department=sensitive-documents",
        "Rejected; the verifier names the conformance conjunct",
    )
    status, payload, ms, _ = advance(
        pic_b, claims=CAROL_BAD_CLAIMS, label="carol advancement (marketing)", run=run
    )
    run.finish(
        f"{status}: {payload.get('error_description') if isinstance(payload, dict) else payload}",
        status == 200,
    )

    # R6 — duplicate delivery: two successors of the same checkpoint.
    run = Run(
        "P6-duplicate-delivery",
        "PIC-X",
        "The same checkpoint PCA_B1 is advanced twice, by two workload keys "
        "(at-least-once delivery)",
        "Both accepted: P holds for each; uniqueness of continuation (U) is not "
        "established by the invariant",
    )
    outcomes = []
    for worker in ("first", "second"):
        status, payload, ms, _ = advance(
            pic_b, claims=WORKLOAD_CLAIMS, label=f"{worker} consumer", run=run
        )
        if status == 200:
            info = mixer("inspect", "--token", payload["access_token"])
            outcomes.append(
                f"{worker}: accepted, position {info['position']}, "
                f"lineage {info['lineage_id']}"
            )
        else:
            outcomes.append(f"{worker}: {status} {payload}")
    run.finish("; ".join(outcomes), all(o.startswith(("first: accepted", "second: accepted")) or ": accepted" in o for o in outcomes))

    # R7 — revocation: not implemented in PIC-X at this commit.
    run = Run(
        "P7-revocation",
        "PIC-X",
        "Lineage and executor revocation",
        "Omitted: not implemented",
    )
    run.finish(
        "Omitted. PIC-X wires NoRevocationConfigured "
        "(crates/pic-x-realm/src/checkpoints.rs) at commit 1b485cd: is_revoked "
        "always answers false. The PIC Revocation Specification exists as Draft "
        "0.2; the realm does not implement it.",
        None,
    )


# ------------------------------------------------- lineage-aware receiver runs


INVARIANT_RE = None


def parse_invariants(raw: list) -> list:
    """mixer `inspect`/`verify-settled` render invariants as
    InvariantTuple("scope", "operation", "resourceType", "resourceId")."""
    import re

    tuples = []
    for item in raw:
        match = re.match(
            r'InvariantTuple\("([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\)', item
        )
        if match:
            tuples.append(match.groups())
    return tuples


def pic_rs_validate(
    token: str,
    operation: str,
    resource_type: str,
    resource_id: str,
    workflow: str,
    locks: dict | None,
    run: Run,
    label: str,
) -> bool:
    """A downstream receiver for settled PIC Tokens: realm signature (ordinary
    Profile 0.2 verification), authority coverage, and - when `locks` is given -
    a per-workflow lineage lock, expressible only because the presentation
    carries the occurrence."""
    verdict = verify_settled_any(token)
    ok = verdict.get("outcome") == "accepted"
    run.log(f"{label}: settled-token verification (realm signature, settled "
            f"shape, root hash): {'pass' if ok else 'FAIL'}")
    if not ok:
        return False
    lineage = verdict.get("lineage_id")
    covered = any(
        op == operation and rtype == resource_type and rid in ("*", resource_id)
        for (_s, op, rtype, rid) in parse_invariants(verdict.get("invariants", []))
    )
    run.log(f"{label}: authority covers ({operation},{resource_type}:{resource_id}): "
            f"{'pass' if covered else 'FAIL'}")
    if not covered:
        return False
    if locks is None:
        run.log(f"{label}: no lineage policy configured; accepted as a "
                f"continuation of lineage {lineage}")
        return True
    bound = locks.get(workflow)
    if bound is None:
        locks[workflow] = lineage
        run.log(f"{label}: workflow `{workflow}` bound to lineage {lineage}: pass")
        return True
    if bound == lineage:
        run.log(f"{label}: workflow `{workflow}` lineage matches ({lineage}): pass")
        return True
    run.log(f"{label}: workflow `{workflow}` is bound to lineage {bound}; the "
            f"presentation continues lineage {lineage}: FAIL")
    return False


def review_runs():
    """Runs added in response to review: honest cross-use (P8), the
    lineage-aware receiver policy (P9), executor-chosen lineage granularity
    (P10), and the attenuation-validation path (P3b)."""
    setup = Run(
        "P8-setup",
        "PIC-X",
        "Fresh pair of lineages for the receiver-policy runs (as in P0)",
        "Both lineages settled",
    )
    token, pic_a, pic_b = build_two_lineages(setup)
    info_a = mixer("inspect", "--token", pic_a)
    info_b = mixer("inspect", "--token", pic_b)
    setup.finish(
        f"lineage A {info_a['lineage_id']}: {info_a['invariants']}; "
        f"lineage B {info_b['lineage_id']}: {info_b['invariants']}",
        True,
    )

    # P8 - the application-level equivalent of B1: the executor honestly
    # advances lineage A and presents its settled token while serving the
    # workflow that request B started. No lineage policy at the receiver.
    run = Run(
        "P8-honest-cross-use",
        "PIC-X",
        "While serving the workflow started by X_B (read), the executor presents "
        "the settled token of lineage A (write) for a save; the receiver applies "
        "ordinary verification and authority coverage, no lineage policy",
        "Accepted as a continuation of X_A: the presentation is a valid "
        "continuation of its own occurrence (Def. 5); non-mixing attributes the "
        "write, it does not prevent it",
    )
    read_ok = pic_rs_validate(
        pic_b, "read", "documents", "document-42", "doc-42-pipeline", None, run,
        "step 1 (read, lineage B)",
    )
    save_ok = pic_rs_validate(
        pic_a, "save", "storage", "document-42", "doc-42-pipeline", None, run,
        "step 2 (save, lineage A, inside B's workflow)",
    )
    run.finish(
        f"read accepted: {read_ok}; save accepted: {save_ok} - the save is "
        f"accepted as a continuation of lineage {info_a['lineage_id']} (X_A), "
        f"and the acceptance names that occurrence",
        read_ok and save_ok,
    )

    # P9 - the same two presentations against a receiver that binds the
    # workflow to the lineage that started it. The policy reads the occurrence
    # the settled token carries; under the baseline no receiver input carries
    # an occurrence identifier (Lemma 1), so this policy is not expressible.
    run = Run(
        "P9-lineage-lock",
        "PIC-X",
        "Same two presentations; the receiver binds the workflow to the lineage "
        "of its first presentation and rejects continuations of other lineages",
        "Read accepted and binds the workflow to lineage B; the save under "
        "lineage A is rejected by the lineage policy",
    )
    locks: dict = {}
    read_ok = pic_rs_validate(
        pic_b, "read", "documents", "document-42", "doc-42-pipeline", locks, run,
        "step 1 (read, lineage B)",
    )
    save_ok = pic_rs_validate(
        pic_a, "save", "storage", "document-42", "doc-42-pipeline", locks, run,
        "step 2 (save, lineage A, inside B's workflow)",
    )
    run.log(
        "baseline comparison: under B the receiver inputs are execution-"
        "invariant (Lemma 1); no input carries an occurrence identifier, so a "
        "workflow-to-occurrence lock cannot be expressed at all"
    )
    run.finish(
        f"read accepted: {read_ok} (workflow bound to lineage "
        f"{info_b['lineage_id']}); save under lineage {info_a['lineage_id']} "
        f"accepted: {save_ok}",
        (not save_ok) and read_ok,
    )

    # P10 - lineage granularity is chosen at origination. One exchange, one
    # lineage carrying both privileges, both application requests served under
    # it: every receiver sees valid continuations of the single occurrence.
    run = Run(
        "P10-single-lineage",
        "PIC-X",
        "One initial exchange only; the executor serves both application "
        "requests (read and save) under the one lineage, which carries both "
        "invariants",
        "Both accepted as continuations of the single occurrence: occurrence "
        "individuation happened at origination and was the executor's choice",
    )
    status, payload, ms = pic_initial_exchange(token)
    if status != 200:
        raise RuntimeError(f"initial exchange failed: {payload}")
    pic_single = payload["access_token"]
    info_s = mixer("inspect", "--token", pic_single)
    run.log(f"single lineage {info_s['lineage_id']}: invariants {info_s['invariants']}")
    status, payload, ms, _ = advance(
        pic_single, claims=WORKLOAD_CLAIMS, label="one valid continuation", run=run
    )
    if status != 200:
        raise RuntimeError(f"advancement failed: {payload}")
    pic_single = payload["access_token"]
    locks = {}
    read_ok = pic_rs_validate(
        pic_single, "read", "documents", "document-42", "doc-42-pipeline",
        locks, run, "request B's read",
    )
    save_ok = pic_rs_validate(
        pic_single, "save", "storage", "document-42", "doc-42-pipeline",
        locks, run, "request A's save",
    )
    run.log(
        "note: nothing at this commit binds one lineage to one origination "
        "request; the same access token initialized two lineages in P0 and one "
        "here, at the executor's choice"
    )
    run.finish(
        f"read accepted: {read_ok}; save accepted: {save_ok}; both under "
        f"lineage {info_s['lineage_id']} - the receiver cannot separate what "
        f"origination did not separate",
        read_ok and save_ok,
    )

    # P3b - reach the settlement authority's attenuation validation with a
    # remove bitmap referencing a nonexistent index (the Prover's own check is
    # bypassed by hand-assembling the transition).
    run = Run(
        "P3b-bad-bitmap",
        "PIC-X",
        "Otherwise-valid candidate whose invariants remove bitmap references "
        "nonexistent index 5 (the checkpoint has fewer invariants)",
        "Rejected; the attenuation-validation conjunct named",
    )
    keys = mixer("keygen")
    presentation = trust_lab_credential(keys["jwk"], WORKLOAD_CLAIMS)
    candidate = mixer(
        "bad-bitmap",
        "--pca", info_a["pca"],
        "--presentation", presentation,
        "--seed", keys["seed"],
        "--index", "5",
    )
    status, payload, ms = pic_advancement(candidate["token"])
    run.log(f"settlement answered {status} in {ms:.1f} ms", status=status, response=payload)
    run.finish(
        f"{status}: {payload.get('error_description') if isinstance(payload, dict) else payload}",
        status == 200,
    )


# -------------------------------------------------------- baseline (OAuth+DPoP)


def ec_jwk(key: ec.EllipticCurvePrivateKey) -> dict:
    numbers = key.public_key().public_numbers()
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": b64url(numbers.x.to_bytes(32, "big")),
        "y": b64url(numbers.y.to_bytes(32, "big")),
    }


def jwk_thumbprint(jwk: dict) -> str:
    ordered = {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]}
    return b64url(hashlib.sha256(json.dumps(ordered, separators=(",", ":")).encode()).digest())


def es256_sign(key: ec.EllipticCurvePrivateKey, signing_input: bytes) -> bytes:
    der = key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def dpop_proof(
    key: ec.EllipticCurvePrivateKey,
    method: str,
    url: str,
    access_token: str | None = None,
) -> str:
    header = {"typ": "dpop+jwt", "alg": "ES256", "jwk": ec_jwk(key)}
    payload = {
        "jti": secrets.token_urlsafe(16),
        "htm": method,
        "htu": url,
        "iat": int(time.time()),
    }
    if access_token is not None:
        payload["ath"] = b64url(hashlib.sha256(access_token.encode()).digest())
    signing_input = (
        b64url(json.dumps(header).encode()) + "." + b64url(json.dumps(payload).encode())
    )
    return signing_input + "." + b64url(es256_sign(key, signing_input.encode()))


def keycloak_admin_token() -> str:
    status, payload, _ = http(
        "POST",
        f"{KEYCLOAK}/realms/master/protocol/openid-connect/token",
        form={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": KC_ADMIN,
            "password": KC_ADMIN_PASSWORD,
        },
    )
    if status != 200:
        raise RuntimeError(f"admin token failed ({status}): {payload}")
    return payload["access_token"]


def admin(method: str, path: str, admin_token: str, json_body: dict | None = None):
    return http(
        method,
        f"{KEYCLOAK}/admin/realms/{KC_REALM}{path}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json_body=json_body,
    )


def ensure_baseline_realm_objects() -> None:
    """Idempotently creates the two down-scoped client scopes and the
    DPoP-bound baseline client, using only Keycloak's administration API."""
    token = keycloak_admin_token()

    status, scopes, _ = admin("GET", "/client-scopes", token)
    existing = {scope["name"]: scope["id"] for scope in scopes}
    scope_ids = {}
    for name in (SCOPE_READ, SCOPE_WRITE):
        if name in existing:
            scope_ids[name] = existing[name]
            continue
        body = {
            "name": name,
            "protocol": "openid-connect",
            "attributes": {"include.in.token.scope": "true"},
            "protocolMappers": [
                {
                    "name": "baseline-rs-audience",
                    "protocol": "openid-connect",
                    "protocolMapper": "oidc-audience-mapper",
                    "config": {
                        "included.custom.audience": BASELINE_AUDIENCE,
                        "access.token.claim": "true",
                    },
                }
            ],
        }
        status, payload, _ = admin("POST", "/client-scopes", token, json_body=body)
        if status not in (201, 409):
            raise RuntimeError(f"client scope {name} creation failed ({status}): {payload}")
        _, scopes, _ = admin("GET", "/client-scopes", token)
        scope_ids[name] = {s["name"]: s["id"] for s in scopes}[name]

    status, clients, _ = admin("GET", f"/clients?clientId={BASELINE_CLIENT}", token)
    if clients:
        client_id = clients[0]["id"]
    else:
        body = {
            "clientId": BASELINE_CLIENT,
            "secret": BASELINE_SECRET,
            "protocol": "openid-connect",
            "publicClient": False,
            "standardFlowEnabled": False,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": False,
            "attributes": {"dpop.bound.access.tokens": "true"},
        }
        status, payload, _ = admin("POST", "/clients", token, json_body=body)
        if status != 201:
            raise RuntimeError(f"client creation failed ({status}): {payload}")
        _, clients, _ = admin("GET", f"/clients?clientId={BASELINE_CLIENT}", token)
        client_id = clients[0]["id"]

    for name, scope_id in scope_ids.items():
        admin("PUT", f"/clients/{client_id}/optional-client-scopes/{scope_id}", token)


def keycloak_jwks() -> list[dict]:
    status, payload, _ = http(
        "GET", f"{KEYCLOAK}/realms/{KC_REALM}/protocol/openid-connect/certs"
    )
    if status != 200:
        raise RuntimeError("Keycloak JWKS unavailable")
    return payload["keys"]


def rsa_public_key(jwk: dict):
    from cryptography.hazmat.primitives.asymmetric import rsa

    n = int.from_bytes(unb64url(jwk["n"]), "big")
    e = int.from_bytes(unb64url(jwk["e"]), "big")
    return rsa.RSAPublicNumbers(e, n).public_key()


class ResourceServer:
    """A conformant RFC 6750 + RFC 9449 resource server: every check is
    performed and logged individually. /documents wants documents.read;
    /storage wants storage.write."""

    ISSUER = f"{KEYCLOAK}/realms/{KC_REALM}"

    def __init__(self, port: int):
        self.port = port
        self.keys = {key["kid"]: key for key in keycloak_jwks()}
        self.seen_jti: set[str] = set()
        self.transcripts: list[dict] = []

    def required_scope(self, path: str) -> str:
        return SCOPE_WRITE if path.startswith("/storage") else SCOPE_READ

    def validate(self, method: str, path: str, headers: dict) -> tuple[int, dict]:
        headers = {name.lower(): value for name, value in headers.items()}
        checks: list[dict] = []
        outcome = {"checks": checks, "path": path, "method": method}

        def check(name: str, ok: bool, detail: str = "") -> bool:
            checks.append({"check": name, "result": "pass" if ok else "FAIL", "detail": detail})
            return ok

        authorization = headers.get("authorization", "")
        if not check(
            "authorization scheme is DPoP (RFC 9449 §7.1)",
            authorization.startswith("DPoP "),
        ):
            return 401, outcome
        token = authorization[5:]

        header = jwt_header(token)
        payload = jwt_payload(token)
        jwk = self.keys.get(header.get("kid"))
        if not check("token kid resolves to an AS-published key", jwk is not None):
            return 401, outcome

        signing_input, signature = token.rsplit(".", 1)
        try:
            rsa_public_key(jwk).verify(
                unb64url(signature),
                signing_input.encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            signature_ok = True
        except Exception:
            signature_ok = False
        if not check("token signature verifies (RS256, AS JWKS)", signature_ok):
            return 401, outcome

        if not check(
            f"iss == {self.ISSUER}", payload.get("iss") == self.ISSUER, str(payload.get("iss"))
        ):
            return 401, outcome
        now = int(time.time())
        if not check("exp in the future (RFC 7519 §4.1.4)", payload.get("exp", 0) > now):
            return 401, outcome
        audiences = payload.get("aud")
        audiences = audiences if isinstance(audiences, list) else [audiences]
        if not check(
            f"aud contains {BASELINE_AUDIENCE} (RFC 8707)",
            BASELINE_AUDIENCE in audiences,
            str(audiences),
        ):
            return 401, outcome
        wanted = self.required_scope(path)
        scopes = str(payload.get("scope", "")).split()
        if not check(
            f"scope covers the operation ({wanted})", wanted in scopes, str(scopes)
        ):
            return 403, outcome

        cnf = payload.get("cnf", {})
        if not check("token carries cnf.jkt (DPoP-bound, RFC 9449 §6.1)", "jkt" in cnf):
            return 401, outcome

        proof = headers.get("dpop", "")
        if not check("DPoP header present (RFC 9449 §4.1)", bool(proof)):
            return 401, outcome
        proof_header = jwt_header(proof)
        proof_payload = jwt_payload(proof)
        if not check(
            "proof typ == dpop+jwt and alg == ES256",
            proof_header.get("typ") == "dpop+jwt" and proof_header.get("alg") == "ES256",
        ):
            return 401, outcome
        proof_jwk = proof_header.get("jwk", {})
        if not check(
            "proof key thumbprint == cnf.jkt (RFC 9449 §4.3 step 12)",
            jwk_thumbprint(proof_jwk) == cnf.get("jkt"),
        ):
            return 401, outcome

        proof_input, proof_signature = proof.rsplit(".", 1)
        try:
            x = int.from_bytes(unb64url(proof_jwk["x"]), "big")
            y = int.from_bytes(unb64url(proof_jwk["y"]), "big")
            public = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
            raw = unb64url(proof_signature)
            der = encode_dss_signature(
                int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")
            )
            public.verify(der, proof_input.encode(), ec.ECDSA(hashes.SHA256()))
            proof_ok = True
        except Exception:
            proof_ok = False
        if not check("proof signature verifies under its own key", proof_ok):
            return 401, outcome

        url = f"http://127.0.0.1:{self.port}{path}"
        if not check(
            "htm == request method (RFC 9449 §4.3 step 8)",
            proof_payload.get("htm") == method,
        ):
            return 401, outcome
        if not check(
            "htu == request URI (RFC 9449 §4.3 step 9)",
            proof_payload.get("htu") == url,
            str(proof_payload.get("htu")),
        ):
            return 401, outcome
        if not check(
            "iat within acceptance window (RFC 9449 §4.3 step 10)",
            abs(now - proof_payload.get("iat", 0)) < 300,
        ):
            return 401, outcome
        jti = proof_payload.get("jti", "")
        if not check("jti fresh (RFC 9449 §11.1 replay store)", jti not in self.seen_jti):
            return 401, outcome
        self.seen_jti.add(jti)
        if not check(
            "ath == SHA-256(access token) (RFC 9449 §4.3 step 12)",
            proof_payload.get("ath")
            == b64url(hashlib.sha256(token.encode()).digest()),
        ):
            return 401, outcome

        check("ALL CHECKS PASSED — request authorized", True)
        return 200, outcome


def start_rs(rs: ResourceServer) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _serve(self):
            status, outcome = rs.validate(
                self.command, self.path, dict(self.headers)
            )
            rs.transcripts.append(outcome)
            body = json.dumps({"status": status}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = _serve
        do_POST = _serve

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", rs.port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def baseline_runs():
    ensure_baseline_realm_objects()
    rs = ResourceServer(RS_PORT)
    server = start_rs(rs)

    key_a = ec.generate_private_key(ec.SECP256R1())
    key_b = ec.generate_private_key(ec.SECP256R1())
    grant_a, _ = keycloak_password_grant(
        scope=SCOPE_WRITE, client=BASELINE_CLIENT, secret=BASELINE_SECRET, dpop_key=key_a
    )
    grant_b, _ = keycloak_password_grant(
        scope=SCOPE_READ, client=BASELINE_CLIENT, secret=BASELINE_SECRET, dpop_key=key_b
    )
    tau_a, tau_b = grant_a["access_token"], grant_b["access_token"]

    def present(token: str, key, method: str, path: str, extra: dict | None = None):
        url = f"http://127.0.0.1:{RS_PORT}{path}"
        headers = {
            "Authorization": f"DPoP {token}",
            "DPoP": dpop_proof(key, method, url, access_token=token),
        }
        if extra:
            headers.update(extra)
        return http(method, url, headers=headers, body=b"{}" if method == "POST" else None)

    def transcript() -> list[dict]:
        return rs.transcripts[-1]["checks"]

    # R0 — sanity: the right token for each occurrence.
    run = Run(
        "B0-sanity",
        "OAuth 2.0 + DPoP baseline",
        "X_A presents tau_A (storage.write) for a write; X_B presents tau_B "
        "(documents.read) for a read",
        "Both accepted",
    )
    status_a, _, _ = present(tau_a, key_a, "POST", "/storage")
    checks_a = transcript()
    status_b, _, _ = present(tau_b, key_b, "GET", "/documents")
    checks_b = transcript()
    for c in checks_a + checks_b:
        run.log(f"RS: {c['check']}: {c['result']}")
    run.finish(
        f"write with tau_A: {status_a}; read with tau_B: {status_b}",
        status_a == 200 and status_b == 200,
        checks={"write": checks_a, "read": checks_b},
    )

    # R1 — the mix: while continuing X_B, present tau_A for a write.
    run = Run(
        "B1-mix",
        "OAuth 2.0 + DPoP baseline",
        "While processing the request of X_B (read workflow), the executor presents "
        "tau_A — issued for X_A — with a fresh valid DPoP proof, for a write",
        "Accepted; every AS and RS check passes (Theorem 1)",
    )
    status, _, ms = present(tau_a, key_a, "POST", "/storage")
    checks = transcript()
    for c in checks:
        run.log(f"RS: {c['check']}: {c['result']}")
    failed = [c for c in checks if c["result"] == "FAIL"]
    run.finish(
        f"{status}; failed checks: {len(failed)}",
        status == 200,
        checks=checks,
        note="The write was performed inside workflow X_B, which was authorized "
        "only documents.read. No receiver input distinguishes the two occurrences.",
    )

    # R1b — reachability without intent: shared authority accumulator.
    run = Run(
        "B1b-accumulator",
        "OAuth 2.0 + DPoP baseline",
        "Shared token store, cleared on completion; interleaving: receive A, "
        "receive B, execute B, execute A. Executor selects any held token whose "
        "scope covers the operation",
        "Accepted; the write inside X_B uses tau_A without any injected fault",
    )
    accumulator: list[tuple[str, ec.EllipticCurvePrivateKey, str]] = []
    schedule = []

    def receive(name, token, key, scope):
        accumulator.append((token, key, scope))
        schedule.append(f"receive {name}")

    def execute(name, operation, path, method):
        # The executor picks the first held token whose scope covers the
        # operation - authentic inputs, granted by the same principal.
        for token, key, scope in accumulator:
            if operation in scope:
                schedule.append(f"execute {name} using token with scope [{scope}]")
                return present(token, key, method, path)
        schedule.append(f"execute {name}: no token")
        return (401, {}, 0.0)

    receive("A", tau_a, key_a, SCOPE_WRITE)
    receive("B", tau_b, key_b, SCOPE_READ)
    status_b2, _, _ = execute("B (write step reached by injection)", "storage.write", "/storage", "POST")
    checks_b2 = transcript()
    status_a2, _, _ = execute("A (read step)", "documents.read", "/documents", "GET")
    for line in schedule:
        run.log(f"schedule: {line}")
    for c in checks_b2:
        run.log(f"RS (X_B write): {c['check']}: {c['result']}")
    run.finish(
        f"write during X_B: {status_b2} (used tau_A); read during X_A: {status_a2} (used tau_B)",
        status_b2 == 200,
        schedule=schedule,
        checks=checks_b2,
    )

    # R2 — self-asserted execution identifier.
    run = Run(
        "B2-exec-id",
        "OAuth 2.0 + DPoP baseline + asserted exec_id",
        "Same move as B1 with the executor asserting exec_id = id(X_B) in the "
        "presentation; the receiver checks the assertion against the execution "
        "it believes it is serving",
        "Accepted; the asserted value is chosen by the executor (Lemma 2)",
    )
    exec_id_b = "X-B-7f3a"
    status, _, _ = present(
        tau_a, key_a, "POST", "/storage", extra={"X-Execution-Id": exec_id_b}
    )
    checks = transcript()
    asserted_matches = exec_id_b == exec_id_b  # the receiver compares the
    # asserted value with the identifier the executor itself supplied.
    run.log(f"RS: asserted exec_id `{exec_id_b}` matches believed execution: "
            f"{'pass' if asserted_matches else 'FAIL'} (value chosen by the presenter)")
    for c in checks:
        run.log(f"RS: {c['check']}: {c['result']}")
    run.finish(
        f"{status}; exec_id check passed on a presenter-chosen value. The AS-copied "
        f"variant of Lemma 2 is not implementable in Keycloak 26.7.0 without a "
        f"custom extension: no conformant parameter lets a client have an "
        f"execution identifier of its choice copied into an exchanged token.",
        status == 200,
        checks=checks,
    )

    server.shutdown()
    return tau_a


# ----------------------------------------------------------------- performance


def stats(samples: list[float]) -> dict:
    ordered = sorted(samples)
    return {
        "n": len(samples),
        "median_ms": round(statistics.median(ordered), 2),
        "p95_ms": round(ordered[max(0, int(len(ordered) * 0.95) - 1)], 2),
        "mean_ms": round(statistics.fmean(ordered), 2),
        "min_ms": round(ordered[0], 2),
        "max_ms": round(ordered[-1], 2),
    }


def perf_runs(n: int):
    run = Run(
        "R9-performance",
        "both",
        f"HTTP round-trip latency of each exchange type (N={n}) plus in-process "
        "receiver-side verification cost, all on one machine",
        "Report the numbers",
    )

    access, _ = keycloak_password_grant()
    token = access["access_token"]

    grant_ms, kc_exchange_ms, pic_init_ms, pic_adv_ms = [], [], [], []
    pic0 = None
    for _ in range(n):
        payload, ms = keycloak_password_grant()
        grant_ms.append(ms)
    for _ in range(n):
        status, payload, ms = keycloak_token_exchange(token)
        if status != 200:
            raise RuntimeError(f"Keycloak token exchange failed: {payload}")
        kc_exchange_ms.append(ms)
    for _ in range(n):
        status, payload, ms = pic_initial_exchange(token)
        if status != 200:
            raise RuntimeError(f"PIC-X initial exchange failed: {payload}")
        pic0 = payload["access_token"]
        pic_init_ms.append(ms)

    # One lineage advanced n times; the settlement round trip is what is timed.
    current = pic0
    candidate_build_ms, credential_ms, sizes = [], [], {}
    sizes["oauth_access_token"] = len(token)
    sizes["pic_token_0"] = len(pic0)
    for hop in range(n):
        keys = mixer("keygen")
        start = time.perf_counter()
        presentation = trust_lab_credential(keys["jwk"], WORKLOAD_CLAIMS)
        credential_ms.append((time.perf_counter() - start) * 1000)
        checkpoint = mixer("inspect", "--token", current)
        start = time.perf_counter()
        candidate = mixer(
            "candidate",
            "--pca", checkpoint["pca"],
            "--presentation", presentation,
            "--seed", keys["seed"],
        )
        candidate_build_ms.append((time.perf_counter() - start) * 1000)
        status, payload, ms = pic_advancement(candidate["token"])
        if status != 200:
            raise RuntimeError(f"advancement at hop {hop} failed: {payload}")
        pic_adv_ms.append(ms)
        current = payload["access_token"]
        if hop == 0:
            sizes["candidate_token"] = len(candidate["token"])
            sizes["pic_token_settled"] = len(current)
    final = mixer("inspect", "--token", current)
    sizes["pic_token_final"] = len(current)

    results = {
        "keycloak_password_grant": stats(grant_ms),
        "keycloak_rfc8693_exchange": stats(kc_exchange_ms),
        "pic_x_initial_exchange": stats(pic_init_ms),
        "pic_x_advancement": stats(pic_adv_ms),
        "client_candidate_build_subprocess": stats(candidate_build_ms),
        "client_credential_issuance": stats(credential_ms),
        "sizes_bytes": sizes,
        "final_position": final["position"],
    }
    for name, value in results.items():
        run.log(f"{name}: {json.dumps(value)}")

    # In-process receiver-side verification: settled PIC token (ordinary
    # verifier) vs baseline RS256 access-token + ES256 DPoP proof verification.
    realm_key = next(
        key
        for key in realm_jwks()
        if mixer("verify-settled", "--token", current, "--jwk", json.dumps(key))["outcome"]
        == "accepted"
    )
    bench_settled = mixer(
        "bench-verify", "--token", current, "--jwk", json.dumps(realm_key), "--n", "2000"
    )
    kc_key = next(
        key for key in keycloak_jwks() if key.get("kid") == jwt_header(token).get("kid")
    )
    bench_jwt = mixer(
        "bench-jwt", "--token", token, "--jwk", json.dumps(kc_key), "--n", "2000"
    )
    dpop_key = ec.generate_private_key(ec.SECP256R1())
    proof = dpop_proof(dpop_key, "POST", "http://127.0.0.1:9401/storage", access_token=token)
    bench_dpop = mixer("bench-dpop", "--proof", proof, "--n", "2000")

    results["bench_verify_settled_us"] = bench_settled
    results["bench_jwt_rs256_verify_us"] = bench_jwt
    results["bench_dpop_es256_verify_us"] = bench_dpop
    run.log(f"verify_settled: {bench_settled}")
    run.log(f"jwt_rs256_verify: {bench_jwt}")
    run.log(f"dpop_es256_verify: {bench_dpop}")

    run.finish("recorded", None, results=results)


# -------------------------------------------------------------------- machine


def machine_record():
    def out(*command):
        try:
            return subprocess.run(command, capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as error:
            return f"unavailable: {error}"

    record = {
        "recorded": now_iso(),
        "cpu": out("sysctl", "-n", "machdep.cpu.brand_string"),
        "cores": out("sysctl", "-n", "hw.ncpu"),
        "os": f"macOS {out('sw_vers', '-productVersion')} ({platform.machine()})",
        "python": platform.python_version(),
        "rustc": out("rustc", "--version"),
        "docker": out("docker", "info", "--format", "{{.ServerVersion}}"),
        "keycloak_image": "quay.io/keycloak/keycloak:26.7.0",
        "pic_x_commit": out("git", "-C", str(pic_x_repo()), "rev-parse", "HEAD"),
        "pic_x_version": None,
        "pic_protocol_crate": "pic-protocol 0.2.3 (crates.io)",
        "cryptography": None,
    }
    try:
        import cryptography

        record["cryptography"] = cryptography.__version__
    except Exception:
        pass
    status, payload, _ = http("GET", f"{PIC_X}/.well-known/server-configuration")
    if status == 200:
        record["pic_x_version"] = payload.get("version")
    (RESULTS / "machine.json").write_text(json.dumps(record, indent=2))
    print(f"machine: {record['cpu']}, PIC-X {record['pic_x_version']} "
          f"@ {record['pic_x_commit'][:7]}")


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    arguments = set(sys.argv[1:])
    n = 100
    if "--n" in sys.argv:
        n = int(sys.argv[sys.argv.index("--n") + 1])
    wanted = arguments & {"pic", "baseline", "perf", "review"} or {"pic", "baseline", "perf", "review"}

    machine_record()
    if "pic" in wanted:
        pic_runs()
    if "review" in wanted:
        review_runs()
    if "baseline" in wanted:
        baseline_runs()
    if "perf" in wanted:
        perf_runs(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
