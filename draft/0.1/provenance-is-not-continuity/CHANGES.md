# CHANGES — pic_provenance_is_not_continuity.tex

Every edit made to the paper relative to the previous draft, and why. Anything
not listed here is unchanged. All numbers, hashes, versions, and log lines come
from the runs recorded in `experiment/results/` and `experiment/logs/` on the
machine described in `experiment/results/machine.json` (Apple M4 Max, macOS
26.6.2, 2026-09-05).

## Section IX — fully replaced

The micro-benchmark section ("Implementation and Preliminary Measurements",
based on pic-prototyping v0.2) is replaced by **"Experimental Demonstration"**:

- **Testbed** (§IX-A): Keycloak 26.7.0 (container), PIC-X v0.2.2 built from
  source at commit `1b485cd`, protocol crate `pic-protocol` 0.2.3 (crates.io),
  trust-lab attestation stub, a Python RFC 6750+9449 resource server that logs
  every check, and a Rust fault-injection harness linked against the same
  protocol crate. One-command reproduction in `experiment/run.sh`. Includes a
  black-and-white TikZ topology figure (fig:testbed).
- **Correspondence to the model**: explicit mapping from the conjuncts of
  Def. 10 (Accept_PIC) to the checks PIC-X implements, and an explicit list of
  what is *not* exercised (request digest — profile-conditional and unused;
  PCA0's binding to ρ(X) is procedural, not a carried digest).
- **Runs** (§IX-B, Table `tab:runs`): B0/B1/B1b/B2 (baseline; Theorem 1,
  reachable interleaving, Lemma 2) and P0–P7 (PIC-X; Theorem 2, Corollary 1,
  T4/κ, Prop. 3, revocation omission). Expected vs Observed, observed verbatim.
- **Log excerpts** (§IX-C): B1's full 17-check pass list (the point: nothing
  failed — "conformant" observed) and P1's rejection naming the failing
  conjunct, client- and server-side.
- **Performance** (§IX-D, Table `tab:perf`): HTTP round trips N=100
  (Keycloak RFC 8693 exchange median 3.9 ms; PIC-X initial 1.2 ms; PIC-X
  advancement 2.0 ms) and in-process receiver-side verification N=2000
  (RS256 JWT verify 10.8 µs; ES256 DPoP verify 27.8 µs; PIC ordinary
  verify_settled 489.1 µs). Both ratios stated without adjectives:
  advancement round trip 0.53× the IdP's own RFC 8693 exchange; receiver-side
  verification 12.7× the baseline's two signature checks. Constant-size settled
  token (1,964 B at position 1, 1,965 B at position 100). This resolves the old
  TODO "measure a baseline JWT verify + DPoP verify and report the ratio" and
  removes the old Table II and the TODO about the mixing-scenario bench row.
- **Threats to validity** (§IX-E): loopback-only, stock-Keycloak/by-construction
  RS conformance, lab attester (A3 assumed), unimplemented features excluded,
  explicit redelivery instead of a broker.

## Definitional edit — flagged for author review

**Def. 8 (Proof of Relationship)**: the previous "reference construction"
sketch (`PCA_{i+1} = Sign_{k_{i+1}}(H(PCA_i), H(q_{i+1}), C_{i+1}, att, t)`;
`PCA_0 = Sign_{k_0}(H(ρ(X)), C_0, att_0)`, citing pic-prototyping v0.2) does
**not** match the normative Profile 0.2 construction (pic-spec Draft 0.2,
commit `5f8703d`) that PIC-X implements. The sketch is replaced with the
faithful one: a signed checkpoint PCA_i carrying (C_i, position, challenge
n_i); a workload-signed transition over (H(PCA_i), n_i, n_{i+1}, attenuation,
attestation), with the request digest H(q) profile-conditional; the successor
PCA signed by the verifier on acceptance; PCA_0 = Sign_AS(C_0, 0, n_0).
Abstract content of the definition (receiver-verifiable evidence that s_{i+1}
continues s_i for q) unchanged.

**Theorem 2, proof of (i)**: consequential edit. The uniqueness argument
previously said the chain resolves to a PCA_0 "committing to H(ρ(X))". In the
Profile 0.2 construction PCA_0 does not carry a digest of ρ(X); it is minted
by the originator from the verified origination request with a fresh lineage
identity and challenge (A4). The proof now derives uniqueness from the chain
of transition digests and challenges down to that PCA_0, with the binding to
ρ(X) discharged by A4. **Finding, not silently fixed**: if the authors intend
the stronger carried-digest binding, the spec/implementation do not provide it
today, and the paper should not claim it.

**Corollary 1**: "an ordinary PCA cannot name both as predecessor" →
"an ordinary *transition* cannot name both as predecessor" (in Profile 0.2 the
predecessor reference lives in the transition, not the PCA).

## Other text edits

- **Abstract**: one clause appended to the last sentence mentioning the
  demonstration (conformant acceptance on Keycloak+DPoP; rejection by PIC-X
  naming the failing conjunct). No adjectives.
- **Contributions**: item 7 added for the experimental demonstration.
- **§IV** (after Theorem 1): one sentence pointing to run B1; after the
  accumulator countermodel: one sentence pointing to run B1b.
- **§V**: Prop. 3 discussion: one sentence pointing to run P6. Incremental
  profile remark: one sentence on its centralized form (A2 concentrated at the
  settlement authority). Composition: TODO resolved by citing the PIC Sandboxed
  Execution Draft 0.2 (`picsandbox`), with the explicit statement that PIC-X
  does not implement it at the evaluated commit — the experiment claims
  propagation only.
- **§VI Tier 1**: one sentence stating that PIC-X is the Tier-1 remedy
  implemented (an RFC 8693 AS become continuity verifier).
- **§VIII points 1–2**: one sentence each noting that PIC-X implements the
  AS-minted PCA0 option and a configured scope→C0 translation that rejects
  unmatched scopes.
- **§XI Related work, "Prior model"**: adds the experimental demonstration to
  the list of what this paper adds.
- **§XII Limitations, "Verification status"**: adds that the experiment is not
  a conformance proof.
- **Table I caption**: TODO replaced by the pinned versions actually consulted
  (Biscuit v3.3; UCAN 1.0.0; UCAN Invocation 1.0.0, optional `cause` field —
  verified against the public repositories on 2026-09-05).

## Appendices added

- **Appendix A**: PIC-X capability inventory at commit `1b485cd`, from source,
  with file references — who mints PCA0 (the realm; A4 at the AS), scope→C0
  translation, no DPoP verification at the exchange, exact successor signing
  content, κ as execution-contract-vs-disclosed-claims, centralized settlement
  profile only, no replay store (U not provided), revocation not implemented,
  composition not implemented, request_digest present in the wire format but
  not required by policy.
- **Appendix B**: verbatim excerpts of the run records (P2, P3, P5, P6,
  audit events) and a pointer to the full artifact. Red TODO for the public
  artifact URL.

## Bibliography

- Removed `picproto` (pic-prototyping v0.2) — superseded by PIC-X as the
  implementation evaluated.
- Added `picx`: PIC-X v0.2.2, commit `1b485cd`,
  github.com/pic-protocol/pic-x + `pic-protocol` 0.2.3 (crates.io).
- `picspec` pinned to commit `5f8703d` and extended with the Prover/Verifier
  Specification (the normative document for the Profile 0.2 checks).
- Added `picsandbox`: PIC Sandboxed Execution Draft 0.2 (same commit).
- `biscuit` pinned: specification v3.3 (eclipse-biscuit/biscuit,
  SPECIFICATIONS.md).
- `ucan` pinned: UCAN spec v1.0.0; UCAN Invocation v1.0.0 (`cause` optional).

## Deviations from the run plan, all stated in the paper

- **R2 (AS-copied exec_id)**: Keycloak 26.7.0 has no conformant mechanism to
  copy a client-chosen execution identifier into an exchanged token; run B2
  exercises the receiver-side variant and the paper says so. Lemma 2 itself is
  about the hypothetical extension and stands on the proof.
- **R7 (revocation)**: omitted; `NoRevocationConfigured` at commit `1b485cd`
  (crates/pic-x-realm/src/checkpoints.rs). Stated in Table tab:runs and
  Appendix A.
- **R8 (two consecutive non-conforming hops)**: not constructible in the
  centralized profile — every hop passes the settlement authority; the caveat
  becomes A2 concentrated there. Stated in §V remark and §IX-A.
- **Broker**: explicit redelivery in-process instead of a message broker,
  documented in Threats to validity (the delivery contract, at-least-once, is
  what is modeled; a broker adds no receiver check).
- **Composition**: not implemented in PIC-X → no run; the paper's composition
  section stays model-level with the spec citation.

## TODOs left red on purpose (not verifiable by the experiment)

- Author(s) / affiliation.
- Which definitions/theorems are new vs. restated relative to arXiv:2607.08906.
- Lean artifact commit hash and covered theorems.
- Public artifact URL for the experiment (must exist before it can be cited).

## Findings for the authors (beyond the flagged Def. 8 edit)

1. **Receiver-side cost asymmetry**: ordinary verification of a settled PIC
   token costs 12.7× the baseline receiver's two signature checks (489 µs vs
   38.6 µs in-process; three nested ES256 signatures vs RS256+ES256). Constant
   in hops, but not "comparable to one token verification". The paper now
   reports the number instead of the sentence.
2. **Exchange-side cost**: a PIC-X advancement round trip (2.0 ms median)
   measured *below* Keycloak's own RFC 8693 exchange (3.9 ms) on the same
   machine. Reported as an observation about these two codebases, not as a
   protocol claim.
3. **P3 rejection path**: the forged union fails first on the trust conjunct
   ("root.pca is not the currently trusted checkpoint"), not on ⊆ — the
   predicate is a conjunction and the first failing conjunct is reported; the
   ⊆ branch of Corollary 1 is enforced structurally by the removal-only wire
   format. The paper states this explicitly rather than implying a ⊆ log line.

---

# Review response (second pass, 2026-09-05)

Edits made in response to the hostile review (M1–M3, mediums, minors). Four
new runs were executed on the same testbed and machine; observed outcomes
verbatim in `experiment/results/` and `experiment/logs/`.

## M1 — attribution, not prevention

- **New run P8 (honest cross-use)**: the executor honestly advances lineage A
  and presents its settled token while serving the workflow request B started.
  **Accepted** — as a continuation of X_A, per Def. 4/5. Declared in the table,
  in §IX-B, and in the intro. The paper no longer lets "rejects the same move"
  stand: P1–P3 are framed as artifact-level misattribution (conjunct-liveness
  tests), P8 is the application-level equivalent of B1.
- **New run P9 (lineage lock)**: a downstream receiver binds the workflow to
  the lineage of its first presentation (B's read) and **rejects** lineage A's
  save: "workflow is bound to lineage B; the presentation continues lineage A".
  The run also records that the same policy is not expressible under the
  baseline (Lemma 1: no receiver input carries an occurrence). Framed as
  [arXiv:2607.08906, Thm. 4] enforced at a receiving boundary.
- **Intro rewritten**: new paragraph stating precisely what P buys in the
  opening scenario (union unrepresentable; misattribution rejected;
  occurrence-scoped receiver policy) and what it does not (the write under its
  true lineage still happens; semantic intent out of scope). Abstract,
  contribution 7, conclusion, and §VII "What PIC does not prevent" (new item
  (d)) aligned.

## M2 — lineage granularity chosen by the untrusted executor

- **New run P10 (single lineage)**: one initial exchange, both application
  requests served under the one lineage → both accepted; "the receiver cannot
  separate what origination did not separate". Honest outcome recorded,
  including the note that nothing at this commit binds one lineage to one ρ
  (P0 initialized two lineages from the same token).
- **Paper**: new §VIII point 6 ("One lineage per occurrence"): discharging A4
  includes minting exactly one lineage per origination request and refusing
  re-initialization on the same ρ (carried digest of ρ or single-use subject
  tokens); the evaluated commit enforces neither. New Limitations paragraph
  "Origination granularity". The reviewer's stronger fix (ρ signed
  principal-side, H(ρ) carried in PCA0, AS dedup) is stated as the discharge
  condition — it is not implemented in PIC-X at `1b485cd`, so the paper
  requires it rather than claims it.

## M3 — experiment narrower than the theorem

- **(a) Holder binding at the seam**: §VIII point 4 and Appendix A now state
  that the exchange accepts bearer subject tokens (no cnf/DPoP check) and that
  at that seam the deployed PIC path is weaker than the DPoP-verifying baseline
  receiver against subject-token theft. Also added to Threats to validity.
  (Not fixable by the artifact without changing PIC-X; stated, not patched.)
- **(b) Downstream trusts V**: §V incremental-profile remark extended —
  downstream boundaries discharge the predicate by verifying the settlement
  authority's signature (A2 instantiated at V); that authority is a required
  mediator for advancement in this realization, the model requires none (T2),
  and the decentralized profiles are not what §IX tests. Same statement in
  §IX-A "Correspondence to the model". Theorem 2 itself unchanged (abstract,
  per-boundary A2); the realization-specific scope is now explicit next to it.
- **(c) Request binding**: abstract now reads "and, where the profile requires
  it, to the signed request"; a sentence after Def. 10 states the request
  conjunct is profile-conditional and that P rests on the predecessor binding.

## Mediums

- **Cor. 1 evidence**: new run **P3b** reaches the settlement-side attenuation
  validation with a hand-assembled candidate (remove bitmap referencing
  nonexistent index 5): rejected "remove bitmap references a nonexistent index
  in section invariants". §IX-B rewritten: non-expansion holds by construction
  (removal-only materialization), is re-checked under the attenuation order,
  and the validation path is live — not dead code.
- **B2 wording** softened: "we found no supported configuration of Keycloak
  26.7.0", replacing the categorical "offers no conformant mechanism".
- **Performance**: the 0.53× cross-codebase ratio removed from the text; the
  exchange rows are now explicitly context ("no ratio between them is a
  statement about the protocols"); the only claimed ratio is the receiver-side
  in-process one (12.7×), same process/machine/language.
- **Threats combination**: added the compound sentence — open continuation +
  no U + no revocation + promiscuous attester ⇒ in this deployment as tested,
  anyone who observes a checkpoint and can obtain a lab attestation can
  continue the lineage until it expires; production closes it with real
  attestation, revocation, and a U supply, none demonstrated here.
- **P4/P5 scope**: new paragraph — the runs establish that κ is enforced
  against attester-signed claims, not that the attestation is trustworthy
  (A3 assumed). Also noted in the Appendix A κ row.
- **Vocabularies**: testbed now states documents.read/storage.write vs
  documents:read/storage:save are each path's own translation T at hop 0,
  deliberately not unified.

## Minors

- arXiv reference completed with DOI 10.48550/arXiv.2607.08906.
- Biscuit v3.3 and UCAN/Invocation 1.0.0: both were verified against the
  public repositories on 2026-09-05 (eclipse-biscuit README feature table;
  ucan-wg/spec and ucan-wg/invocation READMEs); "Accessed 2026-09-05" added to
  both bibliography entries.
- Keycloak 26.7.0 / Rust 1.98.0 / macOS 26.6.2 are recorded from the running
  system in `experiment/results/machine.json`.
- Still red: authors/affiliation; delta vs arXiv; Lean artifact; public
  artifact URL.

## New artifact pieces

- `mixer` subcommand `bad-bitmap` (hand-assembled invalid attenuation).
- `runner.py review` runs: P8-setup, P8-honest-cross-use, P9-lineage-lock,
  P10-single-lineage, P3b-bad-bitmap; the lineage-aware receiver
  (`pic_rs_validate`) logs settled-token verification, authority coverage, and
  the per-workflow lineage lock individually.

## Artifact reference (2026-09-05, after the move into pic-model)

- The paper and the experimental artifact now live in the public repository
  `https://github.com/ngallo/pic-model`, directory
  `draft/0.1/provenance-is-not-continuity` (local remote verified:
  `git@github.com:ngallo/pic-model.git`; repository confirmed public).
- Added bibliography entry `picartifact` and cited it in §IX (intro and
  testbed) and Appendix B; the red "public artifact URL" TODO is resolved.
- Note: the directory is committed by the author; after the push, the artifact
  reference can optionally be pinned to a commit hash like the pic-x and
  pic-spec entries.
- `run.sh` and `runner.py` now locate the pic-x checkout by walking up the
  directory tree (override with `PIC_X_REPO`), so the artifact works from its
  new location and from any checkout layout that keeps `pic-x` beside or above
  it.

## Remaining TODOs resolved with verified facts (2026-09-05)

- **Delta vs arXiv:2607.08906**: resolved. The full definition/theorem
  inventory of the arXiv paper was retrieved from the published HTML version
  (Defs. 1–13, Thms. 1–6, Lemma 1, Cor. 1) and the intro TODO replaced with a
  precise new-vs-restated statement: new — occurrence/provenance/receiver-input
  separation, P over receiver inputs, Lemma 1 (field-level invariance),
  Theorem 1's conformance claim, Lemma 2, the complement equation, U,
  composition proposition, three tiers, experiment; restated/specialized —
  Def. 6 generalizes [Defs. 7–8], Defs. 8–9 restate [Defs. 4–6] in the
  Profile 0.2 construction, Theorem 2 is the concrete counterpart of
  [Thm. 1, Lem. 1, Thm. 6], Cor. 1 of [Thm. 6], Lemma 2 strengthens [Thm. 4].
  Also corrected the §III citation from [Def. 7] to [Defs. 7–8].
- **Lean artifact**: resolved. The Lean 4 formalization lives in the same
  public repository (ngallo/pic-model, `draft/0.1/pic-model-math/pic-lean`,
  last touched at commit `c02c7db`, Lean v4.32.0, Lean core only, no extra
  axioms, no `sorry`). **Verified by building it on this machine**: `lake
  build` completed successfully (22/22 jobs — the kernel accepted all proofs)
  and `lake exe pic_verification` printed the verified statements. Its own
  paper↔Lean map covers Thms. 1–6, Lemma 1, Cor. 1 of the arXiv paper plus an
  abstract-to-concrete refinement whose single explicit hypothesis
  (`concrete_implies_por`) is exactly where A5 enters; the A5 TODO now cites
  it (`picmodellean` bib entry) and says precisely that.
- **Artifact URL**: resolved earlier the same day (`picartifact` →
  github.com/ngallo/pic-model, `draft/0.1/provenance-is-not-continuity`).
- **Still red (author-only)**: Author(s) and Affiliation.
