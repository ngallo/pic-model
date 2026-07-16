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
