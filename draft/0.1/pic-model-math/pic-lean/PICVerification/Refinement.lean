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
