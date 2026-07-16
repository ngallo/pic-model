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
