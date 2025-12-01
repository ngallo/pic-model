# **PIC Model — Provenance Identity Continuity for Distributed Execution Systems**

**Version:** 0.1 (Draft)
**Date:** 2025-11-29
**Author:** Nicola Gallo — Software Architect  
_All opinions and contributions are my own._  
**GitHub:** https://github.com/ngallo  
**Source:** https://github.com/ngallo/pic-model  
**License:** CC BY 4.0

---

## **Abstract**

The **Executor-First Paradigm** asserts that identity is not an attribute embedded in static credentials or artifacts, but an **emergent property of the execution state** and its **verifiable causal origin**.

The **Provenance Identity Continuity (PIC) Model** defines the invariants that identity **MUST** satisfy across an entire **multi-hop causal execution**, replacing artifact possession with **execution provenance** as the continuity anchor.

Each hop **MUST** be treated as part of a **verifiable distributed transaction**.  
This transaction binds the executor to its causal predecessor, preventing detachment, impersonation, replay, and artifact inheritance failures that plague token-based approaches.

Because continuity derives from provenance, the model supports both **identity-centric flows** and **anonymous capability-based flows**.  
These flows eliminate identity leakage, prevent impersonation via transferable credentials, and reduce cross-domain replay vectors — while maintaining full causal verifiability.

Anonymous capability flows are **inherently privacy-preserving in multi-hop environments**, because they do not expose identity while preserving continuity through **Proof of Continuity**, not **Proof of Possession**.

The model introduces the **Structural Impossibility Claim (NO-GO Result)**:

> **Artifact-centric delegation models — including tokens, certificates, DID documents, or transferable proofs — CANNOT guarantee continuity of Proof of Continuity across multi-hop execution.**

Artifacts may encode identity, authorization, or claims,
but they do **not** prove that the executor performing hop *n*
is the same causally-bound executor that the previous hop *n−1* recognized and attested as its next hop.

Artifacts may demonstrate possession or key ownership,
but they do **not** demonstrate that hop *n* is causally bound to hop *n−1*.

A valid continuation requires that the executor at hop *n*
be verifiably the same executor causally designated by hop *n−1* through attestation.

This limitation is structural, not implementation-dependent,
and cannot be resolved by stronger cryptography, token binding,
session rotation, enclaves, or enriched claims.

---

## **0. Causal Continuity: The Transaction Is the Identity**

Causality in PIC **is not a credential**.  
It is not a token, signature, DID, or certificate.

> **Causality is the distributed transaction itself.**

A PIC Distributed Transaction (τ) carries a verifiable fact:

- **an identity**, or
- **a capability**, or
- **both**, or
- **another contextual attribute**.

What the transaction carries is determined at creation time.  
It becomes the initial causal state.

At each hop, the transaction **MAY reduce its disclosure scope**  
(e.g., drop identity while retaining capability),  
but it **MUST NOT introduce external identity** or import new credentials.

> **Information MAY decrease across hops.  
> Information MUST NOT increase.**

The state that is propagated is the only one that exists.  
If causal continuity is not propagated:

> **The transaction is dead.**

There are no retries, refresh tokens, or secondary inheritance.

Provenance continuity is therefore a structural invariant:

- identity is optional,
- capability is optional,
- **the transaction is mandatory**.

**The system trusts the Distributed Transaction (τ) — its causal provenance — not its artifacts.**

## **1. Introduction**

Distributed execution systems are inherently **multi-hop**.  
Delegation patterns — whether cryptographic or physical — **always** involve:

- **Delegator** — origin of authority  
- **Delegate** — executing agent

In basic paper-based delegation, the artifact **ceases to be meaningful** once the delegate is removed.  
Any party acquiring it can impersonate the delegate.

Therefore:

> **Delegation MUST be expressed as a single causal hop.  
> Delegator and delegate MUST be attested atomically as part of the same continuity step.**

Any mechanism collapsing identity into a transferable artifact  
(e.g., certificates, bearer tokens, DID credentials)  
adds attack surface and weakens continuity guarantees.

---

### **1.1 Proof of Possession vs Proof of Continuity**

Proof of Possession (PoP) demonstrates control over a cryptographic material or artifact at a specific point in time.  
PoP is a claim of **possession**.

Proof of Continuity (PoC) demonstrates that the executor performing hop *n*
is verifiably the same causally-bound executor that hop *n−1* attested as its next hop.  
PoC is a claim of **execution continuity**, not artifact possession.

The two are not equivalent.

Artifact-centric models — including bearer tokens, certificates, DID-based credentials, or key-bound proofs — can establish PoP, but **cannot** establish PoC across multi-hop execution.

PoP verifies **who holds an artifact**.  
PoC verifies **who continues the transaction**.

PoP-based delegation collapses at the moment an artifact changes hands, is relayed, replayed, or executed autonomously.  
PoC **must** be tied to the causal origin of execution, not to the material artifact.

> A model that verifies possession of artifacts validates holders.  
> A model that verifies causal continuity validates executors.

No artifact — regardless of cryptographic strength, token binding, DID rotation, enclave guarantees, or MPC — can ensure continuity of control once execution crosses hops or domains.

This limitation is **structural**, not implementation-dependent.

Formally:

- **Proof of Possession (PoP)** belongs to the artifact domain (who holds X).
- **Proof of Continuity (PoC)** belongs to the execution domain (who continues τ).

> **Possession ≠ Provenance.  
> PoP can never substitute PoC in multi-hop execution.**

---

### **1.2. Limits of Artifact-Centric Identity**

Artifact-centric identity appears intuitive but is structurally misaligned with distributed execution.

The failure arises from **binding identity to the artifact holder**, instead of to **execution provenance**.

This produces two incompatible regimes:

- internet security → explicit identity,  
- enterprise security → implicit boundary-based identity.

This is paradoxical:

> The public internet — hostile — uses explicit identity primitives,  
> private networks rely on implicit trust that collapses at multi-hop.

Artifact-centric identity functions only under narrow assumptions:

1. **First-hop coupling**  
   Identity binds to a transport channel (e.g., mTLS).  
   → Identity attaches to the **channel**, not the execution.

2. **Token-based continuity**  
   Continuity carried by bearer artifacts.  
   → Identity becomes **possession**, not provenance.

3. **Network isolation as pseudo-identity**  
   Assumes secure boundaries (VPN, firewalls).  
   → **Identity continuity does not cross isolation.**

With **AI agents and autonomous workloads**, execution moves faster than artifacts can track.

> **Possession is not provenance.**

---

### **1.3. Practical Observation**

In systems such as **Apache Kafka**, static artifacts are fragile:

- Removing a signature turns the token into **plain payload**.  
- Encrypting does not guarantee validation before misuse.  
- Edge cases require ad-hoc patching, increasing:
  - fragmentation,  
  - complexity,  
  - attack surface.

This produces **exceptions**, not an identity model.

---

## **2. Required Reframing**

Artifact-centric models assume continuity is carried by credentials held by workloads.  
PIC rejects this assumption:

> **Identity MUST be formalized around multi-hop execution provenance — not artifact possession.**

Continuity is not a property of a static object.  
It emerges from:

- **the executor**,  
- **its causal origin**,  
- **the verifiable dependency chain across hops**.

Tokens, certificates, DID docs, JWTs are not the anchor.  
The **causal execution path** is.

Any model collapsing provenance into artifacts will **inevitably lose continuity**.

---

## **3. Provenance as the Continuity Primitive**

PIC does not require identity to exist as a first-class primitive.

Distributed execution **MUST** be modeled as a **verifiable causal transaction** spanning all hops.  
Continuity is preserved when each hop is bound to:

1. the initiating executor,  
2. its causal predecessor,  
3. the verifiable provenance of the chain (cryptographic, mathematical, physical, or other formally checkable mechanism).

> **Causality is the invariant. Identity is optional metadata over it.**

Identity **MAY** exist — but is not required.

Anonymous or capability-based delegations enable privacy-preserving flows.

Capabilities **MAY** traverse flows without exposing identity,  
as long as they remain tied to the same transaction.

> **Identity is not the anchor of trust.  
> Provenance is.**

Where identity is required, it **MUST** follow the causal model  
and **MUST NOT** rely on bearer semantics or transferable artifacts.

---

## **4. Terminology and Granularity**

- **Executor (Eᵢ)**  
  The agent that performs the operation at hop *i*.  
  An Executor **is not implicitly trusted or authorized**.  
  Legitimacy is established **only through attestation and continuity verification**.

- **Executor Characteristic (C₍Eᵢ₎)**  
  A verifiable description of the operational context of the Executor at hop *i*.  
  Characteristics define **what conditions the agent satisfies**, not *who the agent is*.

  Examples of C₍Eᵢ₎ include:
  - organizational role (e.g., *Sales Department*)
  - operational domain (e.g., *Office-Italy network zone*)
  - workload class (e.g., *HR worker*, *inference agent*)
  - capability constraints (e.g., *read-only*, *no-write-finance*)
  - anonymity grade (e.g., *redacted identity*, *pseudonymized agent*)

  Characteristics MAY be proven using **privacy-preserving methods**,  
  such as **zero-knowledge proofs**, **remote attestation**, or **TEE seals**.  
  The proof mechanism does **not** change the characteristic itself —  
  it only determines **how** the characteristic is verified.

- **Provenance (P)**  
  The ordered, verifiable chain of causal steps leading to the current hop.

- **Distributed Transaction (τ)**  
  The primary abstraction of PIC: a causally verifiable execution chain spanning multiple hops.  
  Formally: **τ = ⟨E₀, PCA₀, E₁, PCA₁, …, Eᵢ⟩**.

  The Distributed Transaction **is the continuity substrate**.  
  It does not depend on credentials, tokens, or artifacts —  
  continuity emerges from the ordered PIC Causal Attestations (PCAᵢ).

  In the PIC Model, the following terms are **views of the same object τ**:

  - **Causal Chain** → emphasizes the ordered cause–effect relation between hops.  
  - **Provenance Chain** → emphasizes the verifiable attestation history (PCA sequence).  
  - **Run** → emphasizes a concrete execution instance of τ.

  Unless explicitly distinguished, **“causal chain”, “provenance chain”, “run” all refer to the same Distributed Transaction (τ)** seen from different perspectives.

- **Causal Transaction Authority (CTA)**  
  The component that validates continuity and emits the next attestation.  
  The CTA verifies **Proof of Continuity**, not identity ownership.

  The CTA:
  1. receives the **PoCᵢ** from executor *Eᵢ*,  
  2. verifies that *Eᵢ* is the agent attested by hop *i−1*,  
  3. emits a **PIC Causal Attestation (PCAᵢ)**.

  The CTA **does not mint identity**,  
  **does not assign authority**,  
  **does not extend or escalate capability**.  
  Its only function is **continuity verification**.

- **PIC Causal Attestation (PCAᵢ)**  
  A sealed record generated by the CTA at hop *i* that binds:
  1. the current Executor *Eᵢ*,
  2. the previous attestation *PCAᵢ₋₁*,
  3. the capability / characteristic context at hop *i*.

  A PCA **extends provenance**.  
  It is **not a transferable artifact**.

- **PIC Causal Challenge (PCCᵢ)**  
  A freshness mechanism verifying that hop *i* is live and not replayed.  
  Prevents reuse of past attestations.

- **Proof of Identity (PoIᵢ)**  
  Verifies **who** the executor *Eᵢ* is.  
  MAY be explicit (public key), pseudonymous, or zero-knowledge.

- **Proof of Possession (PoPᵢ)**  
  Verifies that *Eᵢ* controls the cryptographic material associated with its identity.  
  PoP validates **ownership**, not continuity.

- **Proof of Continuity (PoCᵢ)**  
  Verifies that *Eᵢ* is the executor explicitly attested by hop *i−1* as the next hop.  
  PoC validates **continuity**, not ownership.

Identity repetition across hops is permitted, but each hop MUST still produce a valid PoCᵢ and a new PCAᵢ.  
Continuity MUST NEVER be inferred from identity reuse or key reuse alone.

---

## **5. Model and Operational Semantics**

### **5.1 Multi-Hop Execution**

A Distributed Transaction (τ) MUST begin at origin hop 0 with executor **E₀**.
Each subsequent hop *i* MUST be executed by executor **Eᵢ**, forming a strictly
ordered causal lineage:

```text
E₀ → E₁ → E₂ → … → Eᵢ
```

Executors are **hop-local identities**. Even if the same underlying process,
agent, or key performs multiple hops, each pair **(Eᵢ, i)** MUST be treated as a
distinct execution instance in time. Identity reuse MUST NOT imply continuity
reuse. Continuity MUST be established exclusively by a valid **Proof of
Continuity (PoCᵢ)** and the resulting **PIC Causal Attestation (PCAᵢ)**.

A Distributed Transaction MUST remain a single τ ONLY if each hop produces
exactly one successor attested by **PCAᵢ₋₁**. No mechanism other than **PoCᵢ**
MAY create or extend lineage. External continuity primitives such as
consensus, locks, token refresh, shared sessions, or identity re-assertion
MUST NOT substitute provenance, as they collapse continuity into artifact
semantics.

When a hop emits multiple successors, each successor MUST produce its own
**PCAᵢ**. This MUST be treated as a fork event. Forking creates multiple
Distributed Transactions, each inheriting the degraded capability state and
constraints already attested at fork time:

```text
E₀ → E₁a → E₂a → …
E₀ → E₁b → E₂b → …
```

A fork duplicates lineage, not authority. Forks MUST NOT reintroduce identity,
expand capability, escalate privilege, import external credentials, or share
attestations. A **PCA** MUST NOT be forwarded, cloned, replayed, multiplexed,
or reused across branches.

Forking is logical divergence, not concurrency. Concurrency implies competing
or simultaneous claims over the same τ and is forbidden; parallelism refers to
independent τ instances and is permitted.

In PIC, multi-hop execution IS the security primitive. Continuity MUST be
expressed by provenance, not artifact transfer, inheritance, or coordination.

---

### **5.2 Causal Transition Function**

A distributed execution MUST advance hop-by-hop. The transition from hop *i*
to hop *i+1* MUST be defined exclusively by the attested continuity of the
Distributed Transaction (τ).

```text
τᵢ + PCAᵢ → τᵢ₊₁
```

τᵢ MUST include the complete ordered provenance of all previous hops.
**PCAᵢ MUST bind, atomically and verifiably:**

1. the current executor **Eᵢ**,  
2. the previous attestation **PCAᵢ₋₁**,  
3. the hop context **C(Eᵢ)** (identity or capability scope).

**The transition τᵢ → τᵢ₊₁ MUST be valid only if PoCᵢ holds.**  
PoCᵢ MUST attest that **Eᵢ is the exact successor designated by hop i−1**.
No external signal, token, certificate, credential, or enclave MAY substitute PoCᵢ.

If PoCᵢ fails, τᵢ MUST have no successor.  
No replay, refresh, reminting, token regeneration, session inheritance,
or late authorization MAY reattach continuity to τᵢ.

A failed transition MUST NOT produce τᵢ₊₁, MUST NOT emit a PCAᵢ₊₁, and MUST NOT
propagate capability or identity beyond hop i.  
Continuity dies causally; the transaction does not degrade into exceptions.

---

## **6. Fundamental Axioms (Required Set of Invariants)**

These axioms define the **minimum structural guarantees** required to maintain  
**Provenance Identity Continuity (PIC)** in distributed execution.

They govern:

- **causality**,  
- **continuity**,  
- **non-transferability**,  
- **execution provenance**,  

—not cryptographic curves, protocol formats, or implementation details.

---

### **Axiom F1 — Causal Identity Substrate**

Identity in PIC is established by **Executor + Provenance**.

An executor is legitimate only when it is **causally bound to a transaction**.

Identity may take multiple forms:

- explicit identity (e.g., key or certificate)
- pseudonymous identity
- privacy-preserving identity (ZK)
- executor characteristics (contextual attributes)

> **Identity is whatever the previous hop attested as the next valid executor.**

---

### **Axiom F2 — Possession ≠ Execution**

Owning an artifact (token, signature, credential)
**does not prove who is executing the next hop**.

Artifacts demonstrate **ownership**, not **continuity**.

- **PoP = Proof of Possession** → shows control of material  
- **PoC = Proof of Continuity** → shows continuity of execution

**Only PoC establishes continuity.**

#### **Formal Lemma — Possession is not Provenance**

Let:
- **PoP** denote any artifact-bound claim of ownership,
- **PoC** denote a causality-bound claim of continuity.

Then:

**Possession ≠ Provenance**  
**PoP ∉ {Continuity Invariants}**  
**PoC ∈ {Continuity Invariants}**

A model that treats possession as continuity collapses once an artifact changes holder,  
is replayed, proxied, or reissued.  
**Continuity MUST emerge from causality, not from transferable artifacts.**

---

### **Axiom F3 — Reminting ≠ Delegation**

Reissuing or regenerating artifacts breaks continuity.

Examples:
- issuing a new token
- re-minting a credential
- DID or key rotation

These actions produce a **new origin**, not a continuation.

**Delegation MUST preserve causal binding — not recreate it.**

---

### **Axiom F4 — Immutability of the Distributed Transaction**

Every hop in the Distributed Transaction (τ) MUST bind itself to its predecessor.

A **PIC Causal Attestation (PCA)** MUST include:

1. The executor of the hop  
2. The previous attestation  
3. The hop context

No hop MAY:

- skip an ancestor
- rewrite the history of τ
- splice a branch back into τ once separated

---

### **Axiom F5 — Atomic Attestation**

All proofs REQUIRED for a hop MUST be bound into **one attestation (PCA)**.

These include:
- continuity (PoC)
- executor identity or characteristics
- freshness challenge
- context constraints

No staged validation, no multi-message negotiation.

> **Continuity is asserted atomically.**

---

### **Axiom F6 — Causal Authorization**

Authorization MUST originate from the **causal chain**.

It CANNOT be injected mid-transaction by:
- external grants,
- new tokens,
- imported certificates.

If different authority is needed, a **new transaction MUST begin at origin**.

---

### **Axiom F7 — Network Isolation ≠ Identity**

Executor identity MUST NOT be inferred from:

- network zone  
- VPN location  
- mTLS session  
- perimeter routing

Infrastructure **does not provide causal continuity.**

---

### **Axiom F8 — Attestation ≠ Continuity**

Attestation proves **what or who** the executor is.  
Continuity proves **that the executor is the one previously selected**.

These must remain distinct:

- Attestation = verification of properties
- Continuity = verification of causality

> **Identity ≠ causal binding.**

---

### **Axiom F9 — Forks Create New Transactions**

Distributed execution MAY fan-out or branch.

Each branch MUST form an **independent Distributed Transaction (τ₁, τ₂, …)**  
with its own PCA chain.

A PCA MUST NOT be:

- forwarded
- cloned
- replayed
- multiplexed across branches

> **Forking creates new lineage (new τ), not parallel executors of the same τ.**  
> **Forking is logical, not concurrent: it represents divergent causal succession, not simultaneous execution of the same successor.**

**Parallelism ≠ Concurrency**

> Parallelism refers to independent Distributed Transactions (τ₁, τ₂, …),
> each with its own PCA lineage.
> Concurrency refers to simultaneous claims over the same τ.
> PIC allows parallelism and forbids concurrency.

---

### **Axiom F10 — Delegation Is Irreversible**

Delegation MUST only **reduce capability**, never expand it.

Permitted:

- narrowing scope
- removing identity
- increasing anonymity
- lowering permissions

Forbidden:

- minting new identities
- expanding rights
- importing external credentials

Delegated power remains causally tied to the origin.

---

### **Axiom F11 — Identity Can Be Abstract**

Identity in PIC MAY be **non-personal and non-cryptographic**.

It may consist of contextual operational attributes:

- role
- function
- workload category
- capability constraints
- privacy grade

What matters is that **the prior hop attested them**.

---

### **Axiom F12 — Continuity Over Ownership**

Only **Proof of Continuity (PoC)** establishes continuity.

Ownership of keys, artifacts, or credentials:

- MAY assist identity proofs
- CANNOT substitute causality

> **Execution continuity is causal, not material.**

---

### **Axiom F13 — Non-Transferability of Capabilities**

Capabilities MUST NOT move between executors  
unless causally linked through the PCA chain.

Artifacts without PCA provenance are **inert**:

- They MUST NOT imply identity,
- MUST NOT imply authority,
- MUST NOT imply continuity.

---

### **Axiom F14 — Irreversible Pending (Structural End State)**

A Distributed Transaction (τ) may reach a state where **no future executor can ever produce a valid PoC**, 
because every possible hop is formally invalid under the attested constraints of τ.

This state is **Irreversible Pending**.

Irreversible Pending **is not a failure**:
- it produces **no runtime error**,  
- it consumes **no resources**,  
- it blocks **no agents**,  
- it incurs **no operational cost**,
- it creates **no security risk**.

It is simply the point where **continuity is no longer possible** under the rules of τ.

A τ in Irreversible Pending:

- remains **perfectly verifiable**,  
- remains **immutable**,  
- remains **audit-safe**,  
- but **cannot progress**.

This condition may arise from:

- causal constraints (depth, quorum, attestation scope),
- model constraints (capability reduction, disclosure monotonicity),
- CTA policy (validated against τ’s own metadata),
- external signals MAY influence execution ONLY when attested as constraints of τ,
  and MUST NOT introduce new authority, identity, or capability.
- time-based or contextual constraints explicitly attested in any PCA (expiry, deadline, epoch) that permanently invalidate all future successors.

**One executor’s inability to generate PoC is irrelevant.**  
τ ends structurally only when **no admissible executor can ever generate a valid next PCA**.

Restarting after Irreversible Pending always creates **a new τ₀**,
with a fresh origin and **no inheritance of PCA state**.

> **Termination in PIC means the structure forbids continuity,
> not that an agent failed or a system crashed.**

---

## **7. Architectural Invariants (Normative)**

**RFC 2119 terminology applies.**  
These invariants define the **minimum structural guarantees** required for Provenance Identity Continuity (PIC).  
They do not prescribe algorithms, cryptographic curves, or protocol formats — only **causality rules**.

---

### **7.1 PIC Causal Attestation Primitive**

A **Distributed Transaction (τ)** evolves hop-by-hop through a sequence of **PIC Causal Attestations (PCAᵢ)**.

- The first attestation is the **Origin PCA**.
- Each subsequent hop *i* is executed by an executor **Eᵢ**. Eᵢ MAY be identical to a previous executor, but continuity MUST be re-attested at each hop.
- The ordered chain of attestations **IS** the transaction provenance.

Each **PCAᵢ** **MUST** bind, atomically and verifiably:

1. **Executor Eᵢ**,  
2. **Previous attestation PCAᵢ₋₁**,  
3. **Hop context C₍Eᵢ₎** (identity or characteristic-based capability).

A PIC Causal Attestation **MUST** embed:

- A **link to PCAᵢ₋₁** (hash, commitment, accumulator, Merkle, etc.),  
- A **Proof of Identity (PoIᵢ)** *or* **Executor Characteristic proof**,  
- A **Proof of Possession (PoPᵢ)** *only if identity is disclosed*,  
- A **Proof of Continuity (PoCᵢ)** proving Eᵢ is the designated successor of hop *i−1*,  
- A **freshness primitive (PCCᵢ)** preventing replay at hop *i*.

> **The PCA is the continuity substrate.  
> It is not a transferable credential, token, or entitlement.**

The **Causal Transaction Authority (CTA)**:

- **MUST** verify PoCᵢ before generating PCAᵢ,
- **MUST NOT** inject identity, issue authority, or upgrade capability,
- **MUST ONLY** validate continuity.

If continuity verification fails → **the transaction MUST terminate**.

---

### **7.2 Causal Origin Invariant**

- A Distributed Transaction **MUST** originate from an executor E₀.
- The Origin PCA **MUST** bind E₀ to its initial context.
- No new executor identity or capability **MAY** be inserted after origin.

> Origin is not a login event — it is the **first causal attestation**.

---

### **7.3 Monotonic Disclosure Invariant**

- Context **MAY decrease** hop-by-hop (redaction, narrowing, anonymization).
- Context **MUST NOT increase** (no identity injection, no imported claims).
- Introduction of external artifacts **MUST FAIL**.

Once a transaction τ has begun, its **available disclosure surface must shrink** or remain stable — never expand.

---

### **7.4 Delegation Invariant**

- Delegation **MUST** be an irreversible reduction of capability.
- Delegation **MUST NOT** mint new identities.
- Delegated capability **MUST** remain tied to the origin executor E₀.

> Delegation is continuity-preserving degradation,  
> not authority creation.

---

### **7.5 Continuity Invariant**

- Each hop **MUST** be causally bound to the previous hop via **PoCᵢ**.
- If causality breaks → **the transaction MUST terminate**.
- No refresh, replay, or rehydration **MAY** re-attach continuity.

**Proof of Continuity ≠ Proof of Possession**  
Continuity refers exclusively to **the executor causally selected by the prior hop**,  
not to key ownership or credential possession.

Any continuity model based on artifacts is **structurally non-verifiable** in multi-hop execution.

---

### **7.6 Non-Transferability Invariant**

- Capabilities **MUST NOT** be reassigned between independent executors.
- A Distributed Transaction **MUST NOT** be rebound to an executor not present in the PCA chain.

Artifacts without PCA provenance are **inert**:
they **MUST NOT** encode identity, authority, or continuity.

---

## 8 Structural Impossibility (NO-GO Result)

The PIC Model states a fundamental limit:

> **Artifact-based delegation CANNOT provide Proof of Continuity (PoC) across multi-hop execution.**

This is structural, not cryptographic.

---

### 8.1 Definitions

```
PoP = Proof of Possession (control of an artifact or key)
PoI = Proof of Identity (who the executor claims to be)
PoC = Proof of Continuity (continuity from previous attested executor)
τ   = Distributed Transaction (causal execution chain)
PCA = PIC Causal Attestation
```

- **PoP** = ownership.
- **PoC** = causal succession.
- **PoP ≠ PoC.**

---

### 8.2 Structural Impossibility

Artifact models validate **what is held** (PoP),
not **who continues τ** (PoC).

Artifacts can be:
- copied,
- forwarded,
- replayed,
- proxied.

All remain **cryptographically valid**, but causally ambiguous.

> Transferability breaks continuity by definition.

---

### 8.2.1 Informal Reduction (Non-Normative)

If an artifact A were sufficient to guarantee PoC across hops,
then A must encode:

1. executor identity of hop i,
2. causal binding to hop i−1,
3. non-transferability.

1 and 2 imply A must embed lineage.
3 implies A cannot be transferable.

Therefore A is no longer an artifact but a PCA instance,
which is bound by continuity, not possession.

Hence, any transferable artifact cannot guarantee PoC by construction.

---

### 8.3 Replay does not fix continuity

Nonces, timestamps, TLS binding, enclaves, DID rotation
only restrict **reuse** of artifacts.

They do **not** prove:
- that the executor at hop *i* is the one attested by hop *i−1*.

Replay-hardening ≠ PoC.

---

### 8.4 Stronger cryptography does not help

Better signatures, MPC, threshold keys, zk-proofs
only strengthen **ownership proofs**.

They cannot express:

```
"I am the next attested executor of τ."
```

Cryptography can validate artifacts,  
**not lineage**.

---

### 8.5 Execution vs Artifact domain

Artifacts describe **objects** (“who holds X”).  
Continuity describes **execution** (“who continues τ”).

They are different domains.  
You cannot infer the latter from the former.

---

### 8.6 Consequence

At **hop 2 and beyond**, artifact-based continuity collapses:

```
Hop0 → Hop1: PoP valid
Hop1 → Hop2: artifact transferable
           → executor unknown
           → PoC broken
           → τ terminated
```

Once PoC fails:
- no replay,
- no refresh,
- no rebinding.

A restart is **a new origin**, not a continuation.

---

### 8.7 Implication

Continuity must be **proven hop-by-hop**.

> **Only provenance + executor attestation (PCA + PoC) guarantees continuity.  
> Artifact possession never does.**

---

## **9. Intellectual Property and Generative Assistance**

The **Provenance Identity Continuity (PIC) Model**, the **Executor-First Paradigm**,  
and the **Structural Impossibility Claim** are original conceptual contributions of the author.

Generative AI was used **exclusively for**:

- editorial refinement,
- structural organization,
- formatting,
- notational consistency.

It contributed **no conceptual, scientific, or theoretical material**.

---

## **10. Attribution of Conceptual Framework**

The PIC Model establishes:

- identity as an emergent property of execution provenance,  
- continuity as a causal invariant across multi-hop transactions,
- capabilities as non-transferable causal artifacts,
- the impossibility of artifact possession to guarantee continuity.

These are **architectural principles**, not terminology.  
Renaming primitives or rephrasing components **does not change the model**.

Implementations, extensions, or derivative frameworks  
that apply these principles **MUST preserve attribution**:

> **Provenance Identity Continuity (PIC) Model — Nicola Gallo**

Attribution maintains conceptual traceability  
while enabling open research, critique, and evolution.

---

## **Summary**

- The PIC Model is open for use, extension, and implementation.  
- You may modify, improve, or generalize it.  
- Attribution is required to acknowledge conceptual origin.  
- The goal is collaboration and progress — not restriction.

---

> **Provenance Identity Continuity (PIC) Model — Nicola Gallo**
> 