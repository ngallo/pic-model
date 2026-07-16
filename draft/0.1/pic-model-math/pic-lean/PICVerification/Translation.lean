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
