# PIC Verification — Lean 4 Formalization (self-contained reference)

This single document describes the **PIC Lean Verification** project and embeds
its complete Lean source, so it can be read and analyzed on its own — without
cloning or building the repository. It is a faithful, read-only companion to the
Lean code in this folder; the `.lean` files remain canonical.

The project is a Lean 4 formalization of the definitions and theorems in
**Proof-of-Continuity: A Temporal Model for Authority Propagation in Distributed
Systems and AI Agents** (`../pic-model.tex`).

Key facts for an analyst:

- **Lean version:** `leanprover/lean4:v4.32.0` (pinned in `lean-toolchain`).
- **No Mathlib.** Only Lean core is used; there is no external mathematical
  dependency.
- **No `sorry` and no added `axiom`.** Every result is proved from Lean's kernel
  logic. A successful `lake build` means the kernel accepted all proofs.
- **`PoR` is abstract.** As in the paper, the single-hop relationship evidence
  `PoR` (Proof of Relationship) enters as a parameter; its concrete
  (e.g. cryptographic) construction is out of scope, mirroring the paper's
  unforgeability assumption. This project does **not** prove that a concrete
  cryptographic implementation of `PoR` is secure. The one place cryptographic
  soundness is assumed is made explicit as a single hypothesis
  (`concrete_implies_por`) in the refinement module.

## What is proved (paper ↔ Lean)

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
| **Refinement**: concrete Prover/Verifier acceptance ⇒ abstract `PoC` (and origin-bound safety) | `ConcreteChecks`, `ConcreteVerifierAccepts`, `concreteAcceptance_implies_PoC`, `concreteAcceptance_implies_originBound` | `Refinement.lean` |

`Main.lean` instantiates the results on the paper's running examples: the
`C₀ = {(convert, doc)}` chain where `(write, doc)` can never be authorized
(`writeNeverAuthorized`), the impossibility of the confused deputy on that chain
(`demoNoConfusedDeputy`), and the forbidden pair of the projection section — a
possession-based policy provably cannot separate the authorized use from the
confused use (`possessionCannotSeparate`), while any policy that does separate
them is provably not possession-based (`separationRequiresLineage`).

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

## How to build and verify

```bash
# from this folder (pic-lean)
lake build          # a successful build means Lean's kernel accepted all proofs
lake exe pic_verification   # prints the list of verified results (paper → Lean names)
```

Install `elan` (the Lean version manager); the `lean-toolchain` file selects
Lean 4.32.0 automatically.

---

## Source

The library entry point aggregates every module:

### `PICVerification.lean`

```lean
import PICVerification.Basic
import PICVerification.Chain
import PICVerification.Possession
import PICVerification.Projection
import PICVerification.TradeOff
import PICVerification.ConfusedDeputy
import PICVerification.Translation
import PICVerification.Refinement
```

### `PICVerification/Basic.lean`

Privileges, authority contexts, monotone attenuation, and PIC Safety (linear
form).

```lean
/-!
# PIC — Basic definitions and linear safety

Formalizes Section 1 (Model) of the paper:

* privileges `(o, r) ∈ O × R`;
* authority contexts `C ⊆ O × R`;
* monotone attenuation `C_{i+1} ⊆ C_i`;
* **Theorem (PIC Safety)**: no step of a monotone chain can exercise a
  privilege not present at the origin (`authorityBoundedByOrigin`,
  `noPrivilegeEscalation`).
-/

namespace PIC

/-- A privilege is an operation/resource pair `(o, r) ∈ O × R`. -/
structure Privilege (Operation Resource : Type) where
  operation : Operation
  resource : Resource
  deriving Repr, DecidableEq

/-- An authority context `C ⊆ O × R`, represented as a predicate over
privileges. -/
abbrev AuthorityContext (PrivilegeType : Type) := PrivilegeType → Prop

/-- Set-style inclusion, written `A ⊆ₚ B`. -/
def IsSubset {PrivilegeType : Type}
    (A B : AuthorityContext PrivilegeType) : Prop :=
  ∀ privilege, A privilege → B privilege

infix:50 " ⊆ₚ " => IsSubset

/-- Inclusion is reflexive. -/
theorem subsetRefl {PrivilegeType : Type}
    (A : AuthorityContext PrivilegeType) : A ⊆ₚ A :=
  fun _ hp => hp

/-- Inclusion is transitive. -/
theorem subsetTrans
    {PrivilegeType : Type}
    {A B C : AuthorityContext PrivilegeType}
    (hAB : A ⊆ₚ B)
    (hBC : B ⊆ₚ C) :
    A ⊆ₚ C := by
  intro privilege hA
  exact hBC privilege (hAB privilege hA)

/-- A single PIC transition cannot introduce a new privilege. -/
theorem singleStepSafety
    {PrivilegeType : Type}
    (C₀ C₁ : AuthorityContext PrivilegeType)
    (hmono : C₁ ⊆ₚ C₀) :
    ∀ privilege, C₁ privilege → C₀ privilege := by
  exact hmono

/-- Safety for three authority contexts. -/
theorem threeStepSafety
    {PrivilegeType : Type}
    (C₀ C₁ C₂ : AuthorityContext PrivilegeType)
    (h01 : C₁ ⊆ₚ C₀)
    (h12 : C₂ ⊆ₚ C₁) :
    C₂ ⊆ₚ C₀ := by
  exact subsetTrans h12 h01

/-- If a privilege is absent at the origin, it is absent after two hops. -/
theorem absentAtOriginAbsentAtEnd
    {PrivilegeType : Type}
    (C₀ C₁ C₂ : AuthorityContext PrivilegeType)
    (h01 : C₁ ⊆ₚ C₀)
    (h12 : C₂ ⊆ₚ C₁)
    (privilege : PrivilegeType)
    (hAbsent : ¬ C₀ privilege) :
    ¬ C₂ privilege := by
  intro hFinal
  exact hAbsent (h01 privilege (h12 privilege hFinal))

/-- **Theorem (PIC Safety), linear form.** Every authority context in a
monotone chain is bounded by the origin: `C n ⊆ C 0`. -/
theorem authorityBoundedByOrigin
    {PrivilegeType : Type}
    (C : Nat → AuthorityContext PrivilegeType)
    (hmono : ∀ i, C (i + 1) ⊆ₚ C i) :
    ∀ n, C n ⊆ₚ C 0 := by
  intro n
  induction n with
  | zero =>
      intro privilege hp
      exact hp
  | succ n ih =>
      exact subsetTrans (hmono n) ih

/-- PIC prevents privilege escalation along any finite chain: a privilege
absent at the origin is absent at every later hop. -/
theorem noPrivilegeEscalation
    {PrivilegeType : Type}
    (C : Nat → AuthorityContext PrivilegeType)
    (hmono : ∀ i, C (i + 1) ⊆ₚ C i)
    (privilege : PrivilegeType)
    (hAbsent : ¬ C 0 privilege) :
    ∀ n, ¬ C n privilege := by
  intro n hPresent
  have hAtOrigin : C 0 privilege :=
    authorityBoundedByOrigin C hmono n privilege hPresent
  exact hAbsent hAtOrigin

end PIC
```

### `PICVerification/Chain.lean`

Execution chains, Proof of Relationship (abstract), Proof of Continuity, origin
binding, and the authorization rule.

```lean
import PICVerification.Basic

/-!
# PIC — Execution chains, Proof of Relationship, Proof of Continuity

Formalizes Section 5 (Proof-of-Continuity) of the paper:

* **Definition (Proof of Relationship)** — abstract single-hop causal
  predicate `PoR : Step → Step → Prop`. As in the paper, its concrete
  (e.g. cryptographic) construction is out of scope: we take it as a
  parameter and, like capability and token models assume their credentials
  unforgeable, we assume the relationship evidence unforgeable.
* **Definition (Valid transition)** — `PoR` plus non-expansiveness.
* **Definition (Proof of Continuity)** — every adjacent transition of the
  chain is valid.
* **Lemma (Continuity implies origin binding)** — `s_n` is causally linked
  to `s_0` through the composed relational chain and `C n ⊆ C 0`.
* **Authorization rule** — on a valid continuity chain,
  `⋂ᵢ Cᵢ = C_n` (`authorizationRule`).
-/


namespace PIC

/-- **Definition (Valid transition).** A transition is valid iff it is both
causally related (`PoR`) and non-expansive (`C₁ ⊆ C₀`). -/
def ValidTransition {Step PrivilegeType : Type}
    (PoR : Step → Step → Prop)
    (s₀ s₁ : Step)
    (C₀ C₁ : AuthorityContext PrivilegeType) : Prop :=
  PoR s₀ s₁ ∧ C₁ ⊆ₚ C₀

/-- An execution chain `π = ⟨(s_0, C_0), …, (s_n, C_n)⟩`: `length` is the
number of transitions `n`; `step i` is the execution step at hop `i` and
`ctx i` the authority context it carries (indices beyond `length` are
ignored). -/
structure Chain (Step PrivilegeType : Type) where
  length : Nat
  step : Nat → Step
  ctx : Nat → AuthorityContext PrivilegeType

/-- **Definition (Proof of Continuity).** `PoC` holds for a chain iff every
adjacent transition is valid: causally related via `PoR` and non-expansive. -/
def PoC {Step PrivilegeType : Type}
    (PoR : Step → Step → Prop)
    (π : Chain Step PrivilegeType) : Prop :=
  ∀ i, i < π.length →
    ValidTransition PoR (π.step i) (π.step (i + 1)) (π.ctx i) (π.ctx (i + 1))

/-- Causal reachability: the reflexive–transitive composition of single-hop
`PoR` relationships. Continuity is the transitive composition of
relationships: `PoR` proves a single link, this closure carries the reach
back to the origin. -/
inductive CausalReach {Step : Type} (PoR : Step → Step → Prop) :
    Step → Step → Prop where
  | refl (s : Step) : CausalReach PoR s s
  | tail {s t u : Step} :
      CausalReach PoR s t → PoR t u → CausalReach PoR s u

/-- A single `PoR` link yields causal reachability. -/
theorem CausalReach.single {Step : Type} {PoR : Step → Step → Prop}
    {s t : Step} (h : PoR s t) : CausalReach PoR s t :=
  CausalReach.tail (CausalReach.refl s) h

/-- Authority contexts are antitone along a valid continuity chain:
for `i ≤ j ≤ n`, `C j ⊆ C i`. This is the monotone-decreasing property
`C_n ⊆ C_{n-1} ⊆ … ⊆ C_0` of the authorization rule. -/
theorem ctxAntitone {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π) :
    ∀ j, j ≤ π.length → ∀ i, i ≤ j → π.ctx j ⊆ₚ π.ctx i := by
  intro j
  induction j with
  | zero =>
      intro _ i hi
      have hz : i = 0 := by omega
      subst hz
      exact subsetRefl _
  | succ j ih =>
      intro hj i hi
      by_cases hcase : i = j + 1
      · subst hcase
        exact subsetRefl _
      · have hij : i ≤ j := by omega
        have hjlt : j < π.length := by omega
        exact subsetTrans (h j hjlt).2 (ih (by omega) i hij)

/-- **Lemma (Continuity implies origin binding).** If `PoC` holds, then every
step `s_n` of the chain is causally linked to `s_0` through a verifiable
relational chain — the composition of the single-hop `PoR` links — and
`C n ⊆ C 0`. -/
theorem continuityOriginBinding {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π) :
    ∀ n, n ≤ π.length →
      CausalReach PoR (π.step 0) (π.step n) ∧ π.ctx n ⊆ₚ π.ctx 0 := by
  intro n
  induction n with
  | zero =>
      intro _
      exact ⟨CausalReach.refl _, subsetRefl _⟩
  | succ n ih =>
      intro hle
      have hlt : n < π.length := by omega
      have prev := ih (by omega)
      have htr := h n hlt
      exact ⟨CausalReach.tail prev.1 htr.1, subsetTrans htr.2 prev.2⟩

/-- **Theorem (PIC Safety), chain form.** On a valid continuity chain, no hop
can exercise a privilege absent from the origin authority context. -/
theorem picSafety {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π)
    (privilege : PrivilegeType)
    (hAbsent : ¬ π.ctx 0 privilege) :
    ∀ k, k ≤ π.length → ¬ π.ctx k privilege := by
  intro k hk hExercised
  exact hAbsent (ctxAntitone h k hk 0 (Nat.zero_le _) privilege hExercised)

/-- **Authorization rule.** On a valid continuity chain the intersection of
all carried contexts collapses to the final one: a privilege is held at every
hop iff it is held at the last hop — `⋂ᵢ Cᵢ = C_n`. -/
theorem authorizationRule {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π)
    (privilege : PrivilegeType) :
    (∀ i, i ≤ π.length → π.ctx i privilege) ↔ π.ctx π.length privilege := by
  constructor
  · intro hall
    exact hall π.length (Nat.le_refl _)
  · intro hend i hi
    exact ctxAntitone h π.length (Nat.le_refl _) i hi privilege hend

/-- Authority dropped at some hop `j` is lost irreversibly: by monotonicity it
cannot reappear at any later hop `k ≥ j`. -/
theorem droppedAuthorityIsLost {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π)
    (privilege : PrivilegeType)
    (j : Nat)
    (hDropped : ¬ π.ctx j privilege) :
    ∀ k, j ≤ k → k ≤ π.length → ¬ π.ctx k privilege := by
  intro k hjk hk hPresent
  exact hDropped (ctxAntitone h k hk j hjk privilege hPresent)

end PIC
```

### `PICVerification/Possession.lean`

Proof-of-Possession semantics and the theorem that PoP admits authority mixing.

```lean
import PICVerification.Basic

/-!
# PIC — Proof-of-Possession semantics and authority mixing

Formalizes Section 4 (Proof-of-Possession) of the paper:

* **PoP semantics** — possession implies usability: an executor holding a
  family of authority sources `{A_j}` may exercise any privilege granted by
  some source (`PopAuthorized`). The paper's *selection function* `σ` chooses
  such a source independently of the request lineage; here its existence is
  the existential in `PopAuthorized`.
* **Theorem (PoP admits authority mixing)** — if the deputy holds a source
  granting `(o, r)` while the request-derived origin context lacks it, then
  PoP authorizes the exercise even though the confused-deputy mismatch of
  Definition 1 is present. As in the paper, the proof is definitional
  unpacking: possession-based authorization simply does not read the lineage.
-/


namespace PIC

/-- **PoP semantics (possession implies usability).** An executor holding the
family of authority sources `held : ι → AuthorityContext P` — ambient
privileges, delegated tokens, bound or sender-constrained artifacts — is
authorized for a privilege iff *some* held source grants it. The witnessing
index is the choice made by the paper's selection function `σ`, made
independently of the request lineage. -/
def PopAuthorized {PrivilegeType ι : Type}
    (held : ι → AuthorityContext PrivilegeType)
    (privilege : PrivilegeType) : Prop :=
  ∃ j, held j privilege

/-- **Theorem (PoP admits authority mixing).** Let a request originate from an
authority context `C₀` that does not contain `(o, r)`, and let the executor
hold another authority source that does contain it. Then PoP authorizes the
exercise of `(o, r)` while `(o, r)` is absent from the request authority
context — the authority/causality mismatch of the confused deputy
(Definition 1) is admissible in the model. -/
theorem popAdmitsAuthorityMixing {PrivilegeType ι : Type}
    (held : ι → AuthorityContext PrivilegeType)
    (C₀ : AuthorityContext PrivilegeType)
    (privilege : PrivilegeType)
    (j : ι)
    (hHeld : held j privilege)
    (hNotOrigin : ¬ C₀ privilege) :
    PopAuthorized held privilege ∧ ¬ C₀ privilege :=
  ⟨⟨j, hHeld⟩, hNotOrigin⟩

end PIC
```

### `PICVerification/Projection.lean`

The projection theorems: lineage-invariant possession cannot individuate
occurrences, and any resolution reintroduces continuity.

```lean
import PICVerification.Basic

/-!
# PIC — Projection: lineage-invariant possession cannot individuate occurrences

Formalizes Section 5.3 (Projection) of the paper:

* an **event** is an occurrence of a privilege within a lineage,
  `e = (o, r, ℓ) ∈ E := O × R × 𝓛`;
* `p : E → O × R` is the projection that forgets the lineage;
* **Definition (Possession policy)** — a policy is possession-based iff it
  factors through `p` (`PossessionBased`);
* **Theorem (Lineage-invariant policies cannot individuate occurrences)** —
  two events sharing the privilege but differing in lineage receive the same
  verdict (`cannotIndividuate`);
* **Theorem (Any resolution reintroduces continuity)** — a policy separating
  such a forbidden pair is not lineage-invariant
  (`anyResolutionReintroducesContinuity`) and must read some function
  `g : 𝓛 → Bool` of the lineage that distinguishes the two
  (`lineageDiscriminatorExists`). Such a `g` is exactly a continuity
  mechanism — a proof-of-relationship extract of the lineage.
-/


namespace PIC

/-- An event is an occurrence of a privilege within a lineage:
`e = (o, r, ℓ) ∈ E := O × R × 𝓛`. The `privilege` field is the spatial
component; `lineage` is the temporal component. -/
structure Event (PrivilegeType Lineage : Type) where
  privilege : PrivilegeType
  lineage : Lineage

/-- The projection `p : E → O × R` that forgets the lineage coordinate.
Possession is the projection onto `O × R` that forgets the lineage axis. -/
def Event.project {PrivilegeType Lineage : Type}
    (e : Event PrivilegeType Lineage) : PrivilegeType :=
  e.privilege

/-- An authorization policy `A : E → {0,1}` assigns a verdict to every
event. -/
abbrev Policy (PrivilegeType Lineage : Type) :=
  Event PrivilegeType Lineage → Bool

/-- **Definition (Possession policy).** A policy is possession-based iff it is
invariant under lineage: it factors through the projection `p`, i.e. there
exists `Ā : O × R → {0,1}` with `A = Ā ∘ p`. -/
def PossessionBased {PrivilegeType Lineage : Type}
    (A : Policy PrivilegeType Lineage) : Prop :=
  ∃ Abar : PrivilegeType → Bool, ∀ e, A e = Abar e.privilege

/-- **Theorem (Lineage-invariant policies cannot individuate occurrences).**
Let `e` and `e'` be two events with the same privilege but (possibly) distinct
lineage. Then every possession-based policy satisfies `A e = A e'`. -/
theorem cannotIndividuate {PrivilegeType Lineage : Type}
    (A : Policy PrivilegeType Lineage)
    (hA : PossessionBased A)
    (e e' : Event PrivilegeType Lineage)
    (hproj : e.privilege = e'.privilege) :
    A e = A e' := by
  cases hA with
  | intro Abar hfac =>
      rw [hfac e, hfac e', hproj]

/-- **Theorem (Any resolution reintroduces continuity).** A policy that
authorizes `e` and denies `e'`, with `p e = p e'`, cannot be
possession-based: it must depend on the lineage coordinate. -/
theorem anyResolutionReintroducesContinuity {PrivilegeType Lineage : Type}
    (A : Policy PrivilegeType Lineage)
    (e e' : Event PrivilegeType Lineage)
    (hproj : e.privilege = e'.privilege)
    (hAuth : A e = true)
    (hDeny : A e' = false) :
    ¬ PossessionBased A := by
  intro hA
  have hsame := cannotIndividuate A hA e e' hproj
  rw [hAuth, hDeny] at hsame
  exact Bool.noConfusion hsame

/-- The positive half of the reintroduction theorem: a policy separating the
forbidden pair reads some function `g : 𝓛 → Bool` of the lineage with
`g ℓ ≠ g ℓ'`. Such a `g` is exactly a continuity mechanism — a
proof-of-relationship extract of the lineage. -/
theorem lineageDiscriminatorExists {PrivilegeType Lineage : Type}
    (A : Policy PrivilegeType Lineage)
    (e e' : Event PrivilegeType Lineage)
    (hproj : e.privilege = e'.privilege)
    (hAuth : A e = true)
    (hDeny : A e' = false) :
    ∃ g : Lineage → Bool, g e.lineage ≠ g e'.lineage := by
  refine ⟨fun ℓ => A ⟨e.privilege, ℓ⟩, ?_⟩
  intro heq
  have heq' : A ⟨e.privilege, e.lineage⟩ = A ⟨e.privilege, e'.lineage⟩ := heq
  have h1 : A ⟨e.privilege, e.lineage⟩ = true := hAuth
  have h2 : A ⟨e.privilege, e'.lineage⟩ = false := by
    rw [hproj]
    exact hDeny
  rw [h1, h2] at heq'
  exact Bool.noConfusion heq'

end PIC
```

### `PICVerification/TradeOff.lean`

The possession–delegation–safety trade-off and the corollary that continuity
restores safety.

```lean
import PICVerification.Basic
import PICVerification.Projection

/-!
# PIC — The possession–delegation–safety trade-off

Formalizes Section 5.4 (A Trade-off Theorem for Authority Propagation):

* **Definition (Lineage-invariant authorization)** — the verdict depends only
  on the privilege, not on the lineage that caused the event
  (`LineageInvariant`), and its equivalence with possession-based policies;
* **Theorem (Possession–delegation–safety trade-off)** — no policy can
  simultaneously be lineage-invariant, authorize the deputy's legitimate use
  of an independently held privilege (authority-mixing-capable delegation),
  and deny the same privilege in a request lineage whose origin lacks it
  (confused-deputy safety). The three hypotheses yield `False`.
* **Corollary (Continuity restores confused-deputy safety)** — relinquishing
  lineage-invariance regains safety: under non-expansive propagation a
  privilege absent at the origin cannot appear at any later hop.
-/


namespace PIC

/-- **Definition (Lineage-invariant authorization).** Authorization of an
event `(o, r, ℓ)` depends only on the possessed authority for `(o, r)`, not on
the lineage `ℓ` that caused the event. -/
def LineageInvariant {PrivilegeType Lineage : Type}
    (A : Policy PrivilegeType Lineage) : Prop :=
  ∀ (privilege : PrivilegeType) (ℓ ℓ' : Lineage),
    A ⟨privilege, ℓ⟩ = A ⟨privilege, ℓ'⟩

/-- A possession-based policy is lineage-invariant. -/
theorem lineageInvariant_of_possessionBased
    {PrivilegeType Lineage : Type}
    {A : Policy PrivilegeType Lineage}
    (h : PossessionBased A) :
    LineageInvariant A := by
  cases h with
  | intro Abar hfac =>
      intro privilege ℓ ℓ'
      rw [hfac ⟨privilege, ℓ⟩, hfac ⟨privilege, ℓ'⟩]

/-- Conversely, when lineages exist, a lineage-invariant policy factors
through the projection: the two notions coincide. -/
theorem possessionBased_of_lineageInvariant
    {PrivilegeType Lineage : Type} [Inhabited Lineage]
    {A : Policy PrivilegeType Lineage}
    (h : LineageInvariant A) :
    PossessionBased A :=
  ⟨fun privilege => A ⟨privilege, default⟩,
   fun e => h e.privilege e.lineage default⟩

/-- **Theorem (Possession–delegation–safety trade-off).** No
authority-propagation system can simultaneously satisfy:

1. *lineage-invariant authorization* (`hInvariant`);
2. *authority-mixing-capable delegation* — the deputy holds an independent
   source granting the privilege, so its legitimate self-originated use, in
   its own lineage `ℓown`, is authorized (`hMixing`);
3. *confused-deputy safety* — the same privilege must be denied in the
   request lineage `ℓreq` whose origin context lacks it (`hSafety`).

The three hypotheses are jointly contradictory. -/
theorem possessionDelegationSafetyTradeOff
    {PrivilegeType Lineage : Type}
    (A : Policy PrivilegeType Lineage)
    (privilege : PrivilegeType)
    (ℓreq ℓown : Lineage)
    (hInvariant : LineageInvariant A)
    (hMixing : A ⟨privilege, ℓown⟩ = true)
    (hSafety : A ⟨privilege, ℓreq⟩ = false) :
    False := by
  have h := hInvariant privilege ℓown ℓreq
  rw [hMixing, hSafety] at h
  exact Bool.noConfusion h

/-- **Corollary (Continuity restores confused-deputy safety).** Relinquishing
lineage-invariance regains safety: under non-expansive propagation
`C (i+1) ⊆ C i`, an `(o, r) ∉ C 0` cannot appear at any later hop. -/
theorem continuityRestoresSafety {PrivilegeType : Type}
    (C : Nat → AuthorityContext PrivilegeType)
    (hmono : ∀ i, C (i + 1) ⊆ₚ C i)
    (privilege : PrivilegeType)
    (hAbsent : ¬ C 0 privilege) :
    ∀ k, ¬ C k privilege :=
  noPrivilegeEscalation C hmono privilege hAbsent

end PIC
```

### `PICVerification/ConfusedDeputy.lean`

Origin-bounded authority, open passthrough, and the impossibility of the
confused deputy under PIC.

```lean
import PICVerification.Basic
import PICVerification.Chain

/-!
# PIC — Impossibility of the confused deputy

Formalizes Sections 3 (Confused Deputy), 6 (Safety Property) and 7
(Impossibility of the Confused Deputy):

* **Definition (Origin-bounded authority)** — every executable privilege at
  any hop was granted at hop 0 (`OriginBounded`);
* **Definition (Open passthrough)** — as a consequence of a request, a
  privilege absent from the origin context is exercised within the request's
  lineage (`OpenPassthrough`); this is exactly the confused deputy;
* **Definition (Confused deputy, Def. 1)** — restated inside a lineage: the
  four conditions become (1) `(o,r) ∉ Priv(U)`, (2) `(o,r) ∈ Priv(D)`,
  (3)+(4) the exercise occurs at some hop of the lineage rooted at `U`'s
  request, i.e. `(o,r) ∈ C k`. Exercising a privilege at hop `k` requires its
  presence in the carried context `C k` (the authorization rule);
* **Theorem (Confused deputy is impossible under PIC)** — in any valid PIC
  execution the conditions cannot be jointly satisfied
  (`confusedDeputyImpossible`).
-/


namespace PIC

/-- **Definition (Origin-bounded authority).** A chain has origin-bounded
authority if every context carried at any hop is contained in the origin
context. -/
def OriginBounded {Step PrivilegeType : Type}
    (π : Chain Step PrivilegeType) : Prop :=
  ∀ k, k ≤ π.length → π.ctx k ⊆ₚ π.ctx 0

/-- Every valid PIC execution enforces origin-bounded authority. -/
theorem poc_originBounded {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π) :
    OriginBounded π :=
  fun k hk => ctxAntitone h k hk 0 (Nat.zero_le _)

/-- **Definition (Open passthrough).** As a consequence of a request, a
privilege absent from the origin authority context is exercised at some hop of
the request's lineage: `(o,r) ∉ C 0` yet `(o,r) ∈ C k`. This is exactly the
confused deputy, separated from legitimate delegation (which realizes an
authority *in* `C 0`) and from the deputy's own housekeeping (which is rooted
in a distinct origin and does not belong to this lineage). -/
def OpenPassthrough {Step PrivilegeType : Type}
    (π : Chain Step PrivilegeType) : Prop :=
  ∃ (privilege : PrivilegeType) (hop : Nat),
    hop ≤ π.length ∧
    ¬ π.ctx 0 privilege ∧
    π.ctx hop privilege

/-- No valid PIC execution contains an open passthrough. -/
theorem openPassthroughImpossible {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    (h : PoC PoR π) :
    ¬ OpenPassthrough π := by
  intro hop
  match hop with
  | ⟨privilege, k, hk, hAbsent, hExercised⟩ =>
      exact hAbsent (poc_originBounded h k hk privilege hExercised)

/-- **Definition (Confused deputy, Def. 1), inside a lineage.** There exist a
privilege `(o,r)` and a hop `k` of the lineage rooted at the user's request
such that `(o,r) ∉ Priv(U)`, `(o,r) ∈ Priv(D)`, and `(o,r)` is exercised at
hop `k` as a consequence of the request — which, under the authorization rule,
requires `(o,r) ∈ C k`. -/
def ConfusedDeputy {Step PrivilegeType : Type}
    (π : Chain Step PrivilegeType)
    (PrivU PrivD : AuthorityContext PrivilegeType) : Prop :=
  ∃ (privilege : PrivilegeType) (hop : Nat),
    hop ≤ π.length ∧
    ¬ PrivU privilege ∧
    PrivD privilege ∧
    π.ctx hop privilege

/-- **Theorem (Confused deputy is impossible under PIC).** In any valid PIC
execution — one whose adjacent transitions satisfy `PoR` and monotonicity, so
that authority is origin-bounded — with the origin context selected from the
user's privileges (`C 0 ⊆ Priv(U)`), the confused deputy conditions cannot be
jointly satisfied as valid behavior within the model. The deputy's own
possession `(o,r) ∈ Priv(D)` is irrelevant: it cannot enter the lineage. -/
theorem confusedDeputyImpossible {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {π : Chain Step PrivilegeType}
    {PrivU PrivD : AuthorityContext PrivilegeType}
    (hpoc : PoC PoR π)
    (hOrigin : π.ctx 0 ⊆ₚ PrivU) :
    ¬ ConfusedDeputy π PrivU PrivD := by
  intro hcd
  match hcd with
  | ⟨privilege, hop, hk, hNotU, _hInD, hExercised⟩ =>
      have hAtOrigin : π.ctx 0 privilege :=
        poc_originBounded hpoc hop hk privilege hExercised
      exact hNotU (hOrigin privilege hAtOrigin)

end PIC
```

### `PICVerification/Translation.lean`

Heterogeneous operation spaces and policy translations, with safety relative to
the translations.

```lean
import PICVerification.Basic

/-!
# PIC — Heterogeneous operation spaces and policy translations

Formalizes the *Heterogeneous operation spaces* paragraph of Section 5:
different hops may use different privilege vocabularies `Oᵢ × Rᵢ`; a
transition is governed by a policy translation
`𝒯_{i→i+1} : 𝒫(Oᵢ × Rᵢ) → 𝒫(O_{i+1} × R_{i+1})` and monotonicity becomes
`C (i+1) ⊆ 𝒯 (C i)`.

The safety theorem is *relative* to the translations, as the paper states:
if every `𝒯ᵢ` is monotone, the final authority is bounded by the composed
translation of the origin context (`heterogeneousSafety`). An overly
permissive translation is a policy error, not a violation of the continuity
invariant.
-/


namespace PIC

/-- A policy translation between two local privilege vocabularies. -/
def Translation (P₁ P₂ : Type) :=
  AuthorityContext P₁ → AuthorityContext P₂

/-- A translation is monotone if it preserves inclusion of authority
contexts. -/
def MonotoneTranslation {P₁ P₂ : Type} (T : Translation P₁ P₂) : Prop :=
  ∀ A B : AuthorityContext P₁, A ⊆ₚ B → T A ⊆ₚ T B

/-- The composite translation `𝒯_{0→n}` from the origin vocabulary to the
vocabulary at hop `n`. -/
def composedTranslation {P : Nat → Type}
    (T : ∀ i, Translation (P i) (P (i + 1))) :
    (n : Nat) → Translation (P 0) (P n)
  | 0 => fun C => C
  | n + 1 => fun C => T n (composedTranslation T n C)

/-- **Heterogeneous safety (relative to `𝒯`).** If every hop satisfies the
translated monotonicity condition `C (i+1) ⊆ 𝒯ᵢ (C i)` and every translation
is monotone, then the authority at hop `n` is bounded by the composed
translation of the origin: `C n ⊆ 𝒯_{0→n} (C 0)`. Safety is therefore
relative to the soundness of the chosen policy translations. -/
theorem heterogeneousSafety {P : Nat → Type}
    (T : ∀ i, Translation (P i) (P (i + 1)))
    (hT : ∀ i, MonotoneTranslation (T i))
    (C : ∀ i, AuthorityContext (P i))
    (hchain : ∀ i, C (i + 1) ⊆ₚ T i (C i)) :
    ∀ n, C n ⊆ₚ composedTranslation T n (C 0) := by
  intro n
  induction n with
  | zero =>
      exact subsetRefl _
  | succ n ih =>
      show C (n + 1) ⊆ₚ T n (composedTranslation T n (C 0))
      exact subsetTrans (hchain n) (hT n _ _ ih)

end PIC
```

### `PICVerification/Refinement.lean`

The refinement bridge: concrete Prover/Verifier acceptance implies the abstract
`PoC` (and origin-bound safety), with cryptographic soundness isolated as one
explicit assumption.

```lean
import PICVerification.Basic
import PICVerification.Chain

/-!
# PIC — Refinement: concrete verifier acceptance implies abstract PoC

This module bridges the abstract PIC model (`Basic`, `Chain`) to the concrete
Prover/Verifier profile of the *PIC Prover and Verifier Specification*.

The concrete per-hop checks of that specification (Section 3.3) — signature
integrity, predecessor-hash link, continuation-challenge response, attestation
validity, and executor conformance — are modeled here as **abstract
predicates**. Their cryptographic realization is out of scope, exactly as `PoR`
is abstract in the model. Their soundness enters through a single, explicit
refinement hypothesis, `concrete_implies_por`: a hop that passes the concrete
relationship checks witnesses the abstract single-hop relation `PoR`.

Given that hypothesis, we prove that a chain accepted by the concrete verifier
satisfies the abstract `PoC`, and therefore inherits the existing safety
theorem `picSafety`: no privilege absent from the origin can appear downstream.

No cryptographic primitive is claimed to be proven secure here. What is
certified is the **logical composition** of the protocol: concrete acceptance,
under the stated crypto assumption, implies the abstract PIC invariants.
-/

namespace PIC

/-- Abstract stand-ins for the concrete verifier checks of the specification
(Section 3.3). Each is a per-hop predicate indexed by the hop; their concrete
(e.g. cryptographic) realization is out of scope, as `PoR` is in the model. -/
structure ConcreteChecks (Step : Type) where
  /-- The outer signature verifies over the whole document (integrity). -/
  signatureValid : Nat → Prop
  /-- `previousPcaHash` equals the hash of the predecessor PCA. -/
  predecessorLinked : Nat → Prop
  /-- The continuation-challenge response matches the predecessor challenge. -/
  challengeValid : Nat → Prop
  /-- The embedded executor attestation is valid. -/
  attestationValid : Nat → Prop
  /-- The attested attributes satisfy the predecessor execution contract. -/
  conforms : Nat → Prop

/-- A hop passes all of the concrete relationship checks. -/
def ConcreteHopChecks {Step : Type} (c : ConcreteChecks Step) (i : Nat) : Prop :=
  c.signatureValid i ∧ c.predecessorLinked i ∧ c.challengeValid i ∧
    c.attestationValid i ∧ c.conforms i

/-- **Concrete verifier acceptance.** The verifier accepts a chain iff every
hop passes the concrete checks *and* carries a non-expansive authority context
(`C_{i+1} ⊆ C_i`). This mirrors Section 3.3: the crypto/conformance checks plus
the explicit non-expansion check. -/
def ConcreteVerifierAccepts {Step PrivilegeType : Type}
    (c : ConcreteChecks Step)
    (π : Chain Step PrivilegeType) : Prop :=
  ∀ i, i < π.length →
    ConcreteHopChecks c i ∧ π.ctx (i + 1) ⊆ₚ π.ctx i

/-- **Refinement theorem.** Under the external assumption that the concrete
relationship checks at a hop witness the abstract single-hop relation `PoR`
(`concrete_implies_por` — this is where cryptographic soundness is assumed), a
chain accepted by the concrete verifier satisfies the abstract `PoC`. -/
theorem concreteAcceptance_implies_PoC {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {c : ConcreteChecks Step}
    {π : Chain Step PrivilegeType}
    (concrete_implies_por :
      ∀ i, i < π.length → ConcreteHopChecks c i →
        PoR (π.step i) (π.step (i + 1)))
    (h : ConcreteVerifierAccepts c π) :
    PoC PoR π := by
  intro i hi
  obtain ⟨hchecks, hmono⟩ := h i hi
  exact ⟨concrete_implies_por i hi hchecks, hmono⟩

/-- **Concrete safety.** A chain accepted by the concrete verifier is
origin-bounded: a privilege absent from the origin authority context appears at
no hop. This reuses the abstract `picSafety` theorem through the refinement,
without reproving anything about the model itself. -/
theorem concreteAcceptance_implies_originBound {Step PrivilegeType : Type}
    {PoR : Step → Step → Prop}
    {c : ConcreteChecks Step}
    {π : Chain Step PrivilegeType}
    (concrete_implies_por :
      ∀ i, i < π.length → ConcreteHopChecks c i →
        PoR (π.step i) (π.step (i + 1)))
    (h : ConcreteVerifierAccepts c π)
    (privilege : PrivilegeType)
    (hAbsent : ¬ π.ctx 0 privilege) :
    ∀ k, k ≤ π.length → ¬ π.ctx k privilege :=
  picSafety (concreteAcceptance_implies_PoC concrete_implies_por h)
    privilege hAbsent

end PIC
```

### `Main.lean`

The demonstration executable: instantiates the abstract results on the paper's
running examples and prints the list of verified declarations.

```lean
import PICVerification

/-!
# Demo instantiation of the PIC verification library

Instantiates the paper's running examples with concrete types:

* the Section 6 example — with `C₀ = {(convert, doc)}`, `(write, doc)` can
  never be authorized within the same execution chain;
* the confused deputy of Definition 1 — impossible on a valid PIC chain;
* the projection of Section 5.3 — a possession-based policy gives the same
  verdict to the authorized use and the confused use, while any policy
  separating them is provably not possession-based.

All theorems below are checked by Lean when this file compiles.
-/


open PIC

inductive Operation where
  | read
  | convert
  | write
  deriving Repr, DecidableEq

inductive Resource where
  | document
  | secret
  deriving Repr, DecidableEq

abbrev DemoPrivilege := Privilege Operation Resource

def convertDoc : DemoPrivilege := ⟨Operation.convert, Resource.document⟩
def writeDoc : DemoPrivilege := ⟨Operation.write, Resource.document⟩

/-! ## A two-transition execution chain carrying only `(convert, document)` -/

inductive DemoStep where
  | origin
  | serviceA
  | serviceB
  deriving Repr, DecidableEq

def demoStep : Nat → DemoStep
  | 0 => DemoStep.origin
  | 1 => DemoStep.serviceA
  | _ => DemoStep.serviceB

def demoCtx : Nat → AuthorityContext DemoPrivilege :=
  fun _ p => p = convertDoc

/-- The abstract single-hop relationship evidence; trivial for the demo. -/
def demoPoR : DemoStep → DemoStep → Prop := fun _ _ => True

def demoChain : Chain DemoStep DemoPrivilege :=
  { length := 2, step := demoStep, ctx := demoCtx }

theorem demoPoC : PoC demoPoR demoChain :=
  fun _ _ => ⟨True.intro, fun _ hp => hp⟩

theorem writeNeConvert : writeDoc ≠ convertDoc := by decide

theorem writeAbsentAtOrigin : ¬ demoChain.ctx 0 writeDoc :=
  fun h => writeNeConvert h

/-- Paper, Section 6: if `C₀ = {(convert, doc)}`, then `(write, doc)` can
never be authorized at any hop of the same execution chain. -/
theorem writeNeverAuthorized :
    ∀ k, k ≤ demoChain.length → ¬ demoChain.ctx k writeDoc :=
  picSafety demoPoC writeDoc writeAbsentAtOrigin

/-! ## Confused deputy (Definition 1) is impossible on this chain -/

def userPriv : AuthorityContext DemoPrivilege :=
  fun p => p = convertDoc

def deputyPriv : AuthorityContext DemoPrivilege :=
  fun p => p = convertDoc ∨ p = writeDoc

theorem demoNoConfusedDeputy :
    ¬ ConfusedDeputy demoChain userPriv deputyPriv :=
  confusedDeputyImpossible demoPoC (fun _ hp => hp)

theorem demoNoOpenPassthrough : ¬ OpenPassthrough demoChain :=
  openPassthroughImpossible demoPoC

/-! ## Projection: possession cannot separate the forbidden pair -/

inductive DemoLineage where
  | userRequest
  | attackerRequest
  deriving Repr, DecidableEq

/-- `(write, doc)` exercised as a continuation of the authorizing request. -/
def authorizedUse : Event DemoPrivilege DemoLineage :=
  ⟨writeDoc, DemoLineage.userRequest⟩

/-- The same privilege exercised outside the lineage that granted it. -/
def confusedUse : Event DemoPrivilege DemoLineage :=
  ⟨writeDoc, DemoLineage.attackerRequest⟩

/-- A possession-based policy: reads only the privilege coordinate. -/
def possessionPolicy : Policy DemoPrivilege DemoLineage :=
  fun e => decide (e.privilege = writeDoc)

theorem possessionPolicyIsPossessionBased :
    PossessionBased possessionPolicy :=
  ⟨fun privilege => decide (privilege = writeDoc), fun _ => rfl⟩

/-- The projection theorem, instantiated: possession gives the same verdict to
the authorized occurrence and the confused one. -/
theorem possessionCannotSeparate :
    possessionPolicy authorizedUse = possessionPolicy confusedUse :=
  cannotIndividuate possessionPolicy possessionPolicyIsPossessionBased
    authorizedUse confusedUse rfl

/-- A lineage-sensitive policy separating the forbidden pair. -/
def lineageSensitivePolicy : Policy DemoPrivilege DemoLineage :=
  fun e =>
    decide (e.privilege = writeDoc ∧ e.lineage = DemoLineage.userRequest)

theorem policySeparates :
    lineageSensitivePolicy authorizedUse = true ∧
    lineageSensitivePolicy confusedUse = false := by
  decide

/-- The reintroduction theorem, instantiated: any policy that separates the
two occurrences is not possession-based — it is continuity-aware. -/
theorem separationRequiresLineage :
    ¬ PossessionBased lineageSensitivePolicy :=
  anyResolutionReintroducesContinuity lineageSensitivePolicy
    authorizedUse confusedUse rfl policySeparates.1 policySeparates.2

/-! ## Verified declarations -/

#check @picSafety
#check @continuityOriginBinding
#check @authorizationRule
#check @popAdmitsAuthorityMixing
#check @cannotIndividuate
#check @anyResolutionReintroducesContinuity
#check @lineageDiscriminatorExists
#check @possessionDelegationSafetyTradeOff
#check @continuityRestoresSafety
#check @openPassthroughImpossible
#check @confusedDeputyImpossible
#check @heterogeneousSafety
#check @concreteAcceptance_implies_PoC
#check @concreteAcceptance_implies_originBound

def main : IO Unit := do
  IO.println "PIC Lean verification project"
  IO.println "The project compiled: Lean accepted the PIC proofs."
  IO.println ""
  IO.println "Verified results (paper → Lean):"
  IO.println "  Thm  PIC Safety                      → picSafety, authorityBoundedByOrigin"
  IO.println "  Lem  Continuity implies origin bind. → continuityOriginBinding"
  IO.println "  Rule ⋂ᵢ Cᵢ = C_n                     → authorizationRule"
  IO.println "  Thm  PoP admits authority mixing     → popAdmitsAuthorityMixing"
  IO.println "  Thm  Lineage-invariant policies      → cannotIndividuate"
  IO.println "       cannot individuate occurrences"
  IO.println "  Thm  Any resolution reintroduces     → anyResolutionReintroducesContinuity,"
  IO.println "       continuity                        lineageDiscriminatorExists"
  IO.println "  Thm  Possession–delegation–safety    → possessionDelegationSafetyTradeOff"
  IO.println "       trade-off"
  IO.println "  Cor  Continuity restores safety      → continuityRestoresSafety"
  IO.println "  Def  Open passthrough                → openPassthroughImpossible"
  IO.println "  Thm  Confused deputy impossible      → confusedDeputyImpossible"
  IO.println "  Par  Heterogeneous operation spaces  → heterogeneousSafety"
  IO.println "  Ref  Concrete acceptance ⇒ PoC       → concreteAcceptance_implies_PoC,"
  IO.println "       (spec Prover/Verifier profile)     concreteAcceptance_implies_originBound"
```

## Project configuration

### `lakefile.toml`

```toml
name = "pic-lean-verification"
version = "0.1.0"
defaultTargets = ["pic_verification"]

[[lean_lib]]
name = "PICVerification"

[[lean_exe]]
name = "pic_verification"
root = "Main"
```

### `lean-toolchain`

```text
leanprover/lean4:v4.32.0
```
