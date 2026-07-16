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
