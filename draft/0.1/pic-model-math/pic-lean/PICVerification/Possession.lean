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
