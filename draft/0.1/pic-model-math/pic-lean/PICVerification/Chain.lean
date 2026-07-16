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
