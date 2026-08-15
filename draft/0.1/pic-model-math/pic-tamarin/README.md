# PIC Tamarin Verification

A Tamarin symbolic verification of the PIC (Provenance Identity Continuity)
model of **Proof-of-Continuity: A Temporal Model for Authority Propagation in
Distributed Systems and AI Agents** (`pic-model.tex`).

Where the Lean project (`../pic-lean`) proves the model's theorems abstractly,
this theory verifies a minimal **message-level realization** of the continuity
discipline against an **active Dolev-Yao network attacker**: a trusted
continuity checker (the "realm") validates each proposed transition and signs
the next authority checkpoint, workloads are attested by a Proof of
Relationship issuer, and every signed artifact travels on the public network.

All 11 lemmas are verified automatically (`tamarin-prover --prove`, ~13s).

## Paper ↔ Tamarin mapping

| Paper | Tamarin lemma / mechanism | Result |
| --- | --- | --- |
| **Thm (PIC Safety)** — a privilege absent from `C0` is never exercised at any hop; the confused-deputy mismatch is unsatisfiable | `PIC_Safety_Read`, `PIC_Safety_Save` (via the inductive invariants `No_Escalation_Read`, `No_Escalation_Save`) | verified |
| Monotone attenuation `C_{i+1} ⊆ C_i` | `NonExpansion` restriction — the checker's acceptance discipline, per atomic privilege | enforced + verified globally |
| Irreversible drop (`droppedAuthorityIsLost`), per branch | `Branch_Dropped_Read_Stays_Dropped`, `Branch_Dropped_Save_Stays_Dropped` | verified |
| **PoR** as single-hop relation witnessed by evidence — eligibility side | `Only_Attested_Advance`: every accepted advancement used a key attested by the trusted issuer; token possession alone never suffices | verified |
| **PoR** — key-control side (evidence identifies the key; the workload signature proves control) | `Key_Control_Or_Compromise`: acceptance under an uncompromised attested key implies that workload signed for exactly that lineage and position | verified |
| One origin authority context per lineage | `Origin_Unique` | verified |
| Fan-out / open continuation (successor unknown at emission) | `Sanity_Sibling_Branches`: two sibling continuations of the same checkpoint are reachable — branching is a feature, not a validation gap | verified (exists-trace) |
| Walkthrough `{read, save} → {save} → {}` | `Sanity_TwoHop_Walkthrough` — non-vacuity of the whole model | verified (exists-trace) |

## Threat model highlights

- **Every settled token is public** (`Out`): PIC artifacts are signed, not
  encrypted, and no confidentiality of token delivery is assumed. All safety
  lemmas hold although the attacker holds every token and credential.
- **Compromised-but-attested workloads** are modeled (`Workload_Compromise`
  leaks the PoR-bound private key). Even then, accepted authority never
  exceeds the origin authority context.
- **Sibling branches are allowed by construction** (checkpoints are
  persistent facts); every safety result holds in the presence of arbitrary
  branching.
- The checker enforces exactly the paper's assumption: *the adversary cannot
  make a valid continuity checker accept a transition that violates
  monotonicity*. Tamarin verifies the global consequences of that local
  discipline.

## Modeling choices

- Authority contexts carry two atomic privileges (`read`, `save`) as
  `'y'/'n'` flags — the walkthrough example, sufficient to express
  non-expansion, irreversible drop, and origin-bound authority.
- Positions are term-encoded naturals `'zero', s('zero'), …`.
- PoR evidence is an issuer-signed credential binding the workload
  verification key (the SD-JWT abstraction). Evidence supports issuer
  validation and key identification; key control is proven by the workload
  signature on the transition — two separate steps, as in the model.
- Checkpoints carry a fresh internal identifier `~cid`, the stand-in for the
  unique signed-artifact identity (`pca_hash`) of the concrete profile.
- Signature verification uses `verify(...) = true` equality restrictions
  (`Eq`), so no unintended pattern matching occurs.

**Not claimed:** cryptographic soundness of a concrete SD-JWT/issuer
deployment (the paper's bridge assumption); byte-level encodings and
COSE/JOSE typing (the term algebra gives perfect parsing); lineage
origination and executor-owned ambient authority (paper, Section 9).

## Install Tamarin

```bash
brew install tamarin-prover/tap/tamarin-prover   # installs maude too
```

Verified with Tamarin 1.12.0 / Maude 3.5.1.

## Verify

```bash
tamarin-prover --prove PICContinuity.spthy
```

Expected summary: all 11 lemmas `verified`, none `falsified`, none
`analysis incomplete`.

## Files

- `PICContinuity.spthy`: the complete theory — trust roots, PoR issuance,
  workload advancement, checker acceptance rule, restrictions, and the 11
  lemmas.
