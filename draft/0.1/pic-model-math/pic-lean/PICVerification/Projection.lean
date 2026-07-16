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
