# PIC Lean Verification

A Lean 4 formalization of the definitions and theorems in
**Proof-of-Continuity: A Temporal Model for Authority Propagation in Distributed Systems and AI Agents** (`pic-model.tex`).

The project intentionally uses only Lean core and has no Mathlib dependency.
It contains no `sorry` and no added axioms: every result below is fully proved
from Lean's kernel logic. As in the paper, the single-hop relationship
evidence `PoR` is abstract (its concrete, e.g. cryptographic, construction is
out of scope), so it enters as a parameter, mirroring the paper's
unforgeability assumption. This project does not prove that a concrete
cryptographic implementation of `PoR` is secure.

## Paper ↔ Lean mapping

| Paper | Lean declaration | File |
| --- | --- | --- |
| Privilege `(o, r) ∈ O × R` | `Privilege` | `Basic.lean` |
| Authority context `C ⊆ O × R` | `AuthorityContext`, `⊆ₚ` | `Basic.lean` |
| **Thm (PIC Safety)** | `authorityBoundedByOrigin`, `noPrivilegeEscalation` (linear form); `picSafety` (chain form) | `Basic.lean`, `Chain.lean` |
| **Def (Proof of Relationship)** | parameter `PoR : Step → Step → Prop`; transitive composition `CausalReach` | `Chain.lean` |
| **Def (Valid transition)** | `ValidTransition` | `Chain.lean` |
| **Def (Proof of Continuity)** | `PoC` | `Chain.lean` |
| **Lem (Continuity implies origin binding)** | `continuityOriginBinding` | `Chain.lean` |
| Authorization rule `⋂ᵢ Cᵢ = C_n` | `authorizationRule`; monotone-decreasing chain `ctxAntitone`; irreversible drop `droppedAuthorityIsLost` | `Chain.lean` |
| PoP semantics, selection function `σ` | `PopAuthorized` | `Possession.lean` |
| **Thm (PoP admits authority mixing)** | `popAdmitsAuthorityMixing` | `Possession.lean` |
| Event `e = (o, r, ℓ) ∈ O × R × 𝓛`, projection `p` | `Event`, `Event.project` | `Projection.lean` |
| **Def (Possession policy)** | `PossessionBased` | `Projection.lean` |
| **Thm (Lineage-invariant policies cannot individuate occurrences)** | `cannotIndividuate` | `Projection.lean` |
| **Thm (Any resolution reintroduces continuity)** | `anyResolutionReintroducesContinuity`, `lineageDiscriminatorExists` | `Projection.lean` |
| **Def (Lineage-invariant authorization)** | `LineageInvariant` (+ equivalence with `PossessionBased`) | `TradeOff.lean` |
| **Thm (Possession–delegation–safety trade-off)** | `possessionDelegationSafetyTradeOff` | `TradeOff.lean` |
| **Cor (Continuity restores confused-deputy safety)** | `continuityRestoresSafety` | `TradeOff.lean` |
| **Def (Origin-bounded authority)** | `OriginBounded`, `poc_originBounded` | `ConfusedDeputy.lean` |
| **Def (Open passthrough)** | `OpenPassthrough`, `openPassthroughImpossible` | `ConfusedDeputy.lean` |
| **Def 1 (Confused deputy)** | `ConfusedDeputy` (restated inside a lineage) | `ConfusedDeputy.lean` |
| **Thm (Confused deputy is impossible under PIC)** | `confusedDeputyImpossible` | `ConfusedDeputy.lean` |
| Heterogeneous operation spaces, `𝒯_{i→i+1}` | `Translation`, `MonotoneTranslation`, `composedTranslation`, `heterogeneousSafety` | `Translation.lean` |

`Main.lean` instantiates the results on the paper's running examples: the
`C₀ = {(convert, doc)}` chain where `(write, doc)` can never be authorized
(`writeNeverAuthorized`), the impossibility of the confused deputy on that
chain (`demoNoConfusedDeputy`), and the forbidden pair of the projection
section — a possession-based policy provably cannot separate the authorized
use from the confused use (`possessionCannotSeparate`), while any policy that
does separate them is provably not possession-based
(`separationRequiresLineage`).

## Modeling choices

- Authority contexts are predicates (`P → Prop`), i.e. sets of atomic
  privileges — the set-valued case `⊆` used throughout the paper's formal
  examples. The general attenuation order `≼` specializes to `⊆ₚ` here.
- A chain is `Chain` with `length` transitions and functions `step`/`ctx`
  indexed by hop; indices beyond `length` are ignored.
- "Exercising a privilege at hop `k`" is modeled as membership in the carried
  context `C k`, which is what the authorization rule requires.
- Policies in the projection results are `Event → Bool`, matching the paper's
  `A : E → {0,1}`.

## Install Lean

Install `elan`, the Lean version manager, following the official Lean setup.
Then open a terminal in this folder. The `lean-toolchain` file selects Lean
4.32.0 automatically.

## Build and verify

```bash
lake build
```

A successful build means Lean's kernel accepted all proofs.

## Run the demonstration executable

```bash
lake exe pic_verification
```

It prints the list of verified results (paper → Lean names).

## Files

- `PICVerification/Basic.lean`: privileges, authority contexts, monotone attenuation, PIC Safety.
- `PICVerification/Chain.lean`: execution chains, `PoR`, `PoC`, origin binding, authorization rule.
- `PICVerification/Possession.lean`: PoP semantics and authority mixing.
- `PICVerification/Projection.lean`: events, lineage, projection theorems.
- `PICVerification/TradeOff.lean`: possession–delegation–safety trade-off.
- `PICVerification/ConfusedDeputy.lean`: open passthrough, confused deputy impossibility.
- `PICVerification/Translation.lean`: heterogeneous vocabularies and policy translations.
- `Main.lean`: concrete examples and executable.
- `lakefile.toml`: Lake project configuration.
- `lean-toolchain`: pinned Lean version.
