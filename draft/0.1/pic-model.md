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

Anonymous capability flows are **inherently privacy-preserving in multi-hop environments**, because they do not expose identity while preserving continuity through **Proof of Control**, not **Proof of Possession**.

The model introduces the **Structural Impossibility Claim (NO-GO Result)**:

> **Artifact-centric delegation models — including tokens, certificates, DID documents, or transferable proofs — CANNOT guarantee continuity of Proof of Control across multi-hop execution.**

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

A PIC transaction carries a verifiable fact:

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

**The system trusts the causal chain, not its artifacts.**

## **1. Introduction**

Distributed execution systems are inherently **multi-hop**.  
Delegation patterns — whether cryptographic or physical — **always** involve:

- **Delegator** — origin of authority  
- **Delegate** — executing agent

In basic paper-based delegation, the artifact **ceases to be meaningful** once the delegate is removed.  
Any party acquiring it can impersonate the delegate.

Therefore:

> **Delegator and delegate identity MUST be validated as independent inputs.**

Any mechanism collapsing identity into a transferable artifact  
(e.g., certificates, bearer tokens, DID credentials)  
adds attack surface and weakens continuity guarantees.

---

### **1.1 Proof of Possession vs Proof of Control**

Proof of Possession (PoP) demonstrates control over a cryptographic material or artifact at a specific point in time.  
PoP is a claim of **possession**.

Proof of Control (PoC) demonstrates that the executor performing hop *n*
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
  A causally verifiable execution chain spanning multiple hops.  
  **τ = ⟨E₀, PCA₀, E₁, PCA₁, …, Eᵢ⟩**  

  The Distributed Transaction **is the continuity substrate**.  
  It does not depend on credentials, tokens, or artifacts —  
  continuity emerges from the ordered causal attestations.

- **Causal Transaction Authority (CTA)**  
  The component that validates continuity and emits the next attestation.  
  The CTA verifies **Proof of Control**, not identity ownership.

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

- **Proof of Control (PoCᵢ)**  
  Verifies that *Eᵢ* is the executor explicitly attested by hop *i−1* as the next hop.  
  PoC validates **continuity**, not ownership.

---

## **5. Model and Operational Semantics**

**WORK IN PROGRESS**

---

## **6. Fundamental Axioms**

**WORK IN PROGRESS**

---

## **7. Architectural Invariants (Normative)**

**RFC 2119 terminology applies.**  
These invariants define the **minimum structural guarantees** required for Provenance Identity Continuity (PIC).  
They do not prescribe algorithms, cryptographic curves, or protocol formats — only **causality rules**.

---

### **7.1 PIC Causal Attestation Primitive**

A **Distributed Transaction (τ)** evolves hop-by-hop through a sequence of **PIC Causal Attestations (PCAᵢ)**.

- The first attestation is the **Origin PCA**.
- Each subsequent hop *i* produces a **new PCAᵢ** derived from **PCAᵢ₋₁**.
- The ordered chain of attestations **IS** the transaction provenance.

Each **PCAᵢ** **MUST** bind, atomically and verifiably:

1. **Executor Eᵢ**,  
2. **Previous attestation PCAᵢ₋₁**,  
3. **Hop context C₍Eᵢ₎** (identity or characteristic-based capability).

A PIC Causal Attestation **MUST** embed:

- A **link to PCAᵢ₋₁** (hash, commitment, accumulator, Merkle, etc.),  
- A **Proof of Identity (PoIᵢ)** *or* **Executor Characteristic proof**,  
- A **Proof of Possession (PoPᵢ)** *only if identity is disclosed*,  
- A **Proof of Control (PoCᵢ)** proving Eᵢ is the designated successor of hop *i−1*,  
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

**Proof of Control ≠ Proof of Possession**  
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

## **8. Structural Impossibility Claim (Security Argument)**

**WORK IN PROGRESS**

---

## **9. Relationships and Considerations**

**WORK IN PROGRESS**

---

## **10. Intellectual Property and Generative Assistance**

The **Provenance Identity Continuity (PIC) Model**, the **Executor-First Paradigm**,  
and the **Structural Impossibility Claim** are original conceptual contributions of the author.

Generative AI was used **exclusively for**:

- editorial refinement,
- structural organization,
- formatting,
- notational consistency.

It contributed **no conceptual, scientific, or theoretical material**.

---

## **11. Attribution of Conceptual Framework**

The PIC Model establishes:

- identity as an emergent property of execution provenance,  
- continuity as a causal invariant across multi-hop transactions,
- capabilities as non-transferable causal artifacts,
- the impossibility of artifact possession to guarantee continuity.

These are **architectural principles**, not terminology.  
Renaming primitives or rephrasing components **does not cqhange the model**.

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
