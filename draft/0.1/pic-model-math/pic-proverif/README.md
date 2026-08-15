# PIC ProVerif Verification

A ProVerif symbolic verification of the PIC (Provenance Identity Continuity)
model of **Proof-of-Continuity: A Temporal Model for Authority Propagation in
Distributed Systems and AI Agents** (`pic-model.tex`) — the companion of the
Tamarin theory in `../pic-tamarin` and of the Lean formalization in
`../pic-lean`.

The protocol modeled here is the same minimal centralized-checker realization
verified in Tamarin: a trusted continuity checker validates each proposed
transition and signs the next authority checkpoint; workloads are attested by
a Proof of Relationship issuer; every signed artifact is public.

## Division of labor across the three projects

| Layer | Project | What it proves |
| --- | --- | --- |
| Abstract model (arbitrary privilege sets, arbitrary chain length) | `../pic-lean` | All paper theorems, kernel-checked, no axioms |
| Message level vs active attacker — stateful/inductive properties | `../pic-tamarin` | Origin-bound authority (PIC Safety), branch-local irreversible drop, plus the authentication core |
| Message level vs active attacker — authentication core, second opinion | this project | PoR eligibility, key control/agreement, non-vacuity |

The origin-bound non-expansion theorem is an invariant over **unbounded
checkpoint chains**; proving it needs induction over the chain, which is
outside what ProVerif's Horn-clause abstraction establishes automatically for
this model (the saturation keeps recursive checkpoint hypotheses unresolved).
It is therefore proved in Tamarin — whose trace induction is designed for
stateful invariants — and abstractly in Lean. ProVerif independently verifies
the authentication core, giving a second tool's confirmation of the PoR
results.

## Paper ↔ ProVerif mapping

| Paper | ProVerif query | Expected result |
| --- | --- | --- |
| **PoR** — eligibility: only attested workloads advance; possession of tokens alone never suffices (the attacker holds every token) | `event(AcceptedT(k,l,p)) ==> event(Issued(k))` | `true` |
| **PoR** — key control: evidence identifies the key, the workload signature proves control | `event(AcceptedT(k,l,p)) ==> event(WSignT(k,l,p)) \|\| event(KeyReveal(k))` | `true` |
| Walkthrough `{read, save} → {save} → {}` reachable (non-vacuity) | `event(Settled(l, s(s(zero)), no, no))` | `false` (i.e. reachable) |

## Threat model highlights

- Signatures are message-revealing (`getmess`): PIC artifacts are signed,
  not encrypted; every settled checkpoint is public. No confidentiality of
  token delivery is assumed.
- Compromised-but-attested workloads are modeled (`KeyReveal` leaks the
  PoR-bound private key).
- Checkpoint artifacts are never consumed: sibling branches (fan-out) are
  possible by construction and the results hold in their presence.
- The checker validates the predecessor checkpoint by verifying the realm
  signature on the presented checkpoint artifact — the artifact carries the
  trusted state, as in the concrete profile where the candidate embeds the
  signed predecessor checkpoint.

**Not claimed:** cryptographic soundness of a concrete SD-JWT/issuer
deployment (the paper's bridge assumption); byte-level encodings and
COSE/JOSE typing; lineage origination and executor-owned ambient authority
(paper, Section 9).

## Install ProVerif

Via opam (`opam install proverif`) or from source:

```bash
brew install ocaml ocaml-findlib
curl -sL -o proverif.tar.gz \
  https://bblanche.gitlabpages.inria.fr/proverif/proverif2.05.tar.gz
tar xzf proverif.tar.gz && cd proverif2.05 && ./build
cp proverif /opt/homebrew/bin/
```

Verified with ProVerif 2.05.

## Verify

```bash
proverif pic_continuity.pv
```

Expected `RESULT` lines:

```text
RESULT event(AcceptedT(k,l_1,p_1)) ==> event(Issued(k)) is true.
RESULT event(AcceptedT(k,l_1,p_1)) ==> event(WSignT(k,l_1,p_1)) || event(KeyReveal(k)) is true.
RESULT not event(Settled(l_1,s(s(zero)),no,no)) is false.
```

(The last line being `false` means the walkthrough end state IS reachable —
the sanity check that the model is not vacuous.)

## Files

- `pic_continuity.pv`: the complete model — types and cryptography,
  attenuation destructors, events, queries, lineage initialization, workload
  attestation/advancement/compromise, and the checker acceptance process.
