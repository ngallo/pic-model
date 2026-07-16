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
