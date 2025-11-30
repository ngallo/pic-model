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
Anonymous capability flows are **inherently safer** in multi-hop environments:  
they eliminate identity leakage, prevent impersonation through transferable credentials, and reduce cross-domain replay vectors — while maintaining full causal verifiability.

Capabilities, scopes, or rights **MAY** traverse the system **without exposing identity**, provided they remain cryptographically tied to the same causal chain and to the executor who originated it.

The model introduces the **Structural Impossibility Claim (NO-GO Result)**:  
artifact-based delegation **CANNOT** guarantee identity continuity in distributed systems.  
This claim is structural, not mathematical; formal treatment is deferred to future work.

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

---

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

### **1.1. Limits of Artifact-Centric Identity**

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

### **1.2. Practical Observation**

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
3. the cryptographically verifiable provenance of the chain.

> **Causality is the invariant. Identity is optional metadata over it.**

Identity **MAY** exist — but is not required.

Anonymous or capability-based delegations are safer:

- no identity leakage,
- no credential impersonation,
- reduced replay vectors.

Capabilities **MAY** traverse flows without exposing identity,  
as long as they remain tied to the same transaction.

> **Identity is not the anchor of trust.  
> Provenance is.**

Where identity is required, it **MUST** follow the causal model  
and **MUST NOT** rely on bearer semantics or transferable artifacts.

---

# **4. Architectural Invariants (Normative)**

RFC 2119 terminology applies.

### **4.1 Causal Origin Invariant**
- A PIC transaction **MUST** originate from an executor.  
- The origin **MUST** be cryptographically bound.  
- No new identity or authority **MAY** be injected after origin.

### **4.2 Monotonic Disclosure Invariant**
- Attributes **MAY decrease**.  
- Attributes **MUST NOT increase**.  
- Importing credentials **MUST FAIL**.

### **4.3 Delegation Invariant**
- Delegation **MUST** be capability reduction.  
- Delegation **MUST NOT** produce new identities.  
- Authority **MUST** remain tied to origin.

### **4.4 Continuity Invariant**
- Each hop **MUST** validate provenance before execution.  
- If continuity fails → **transaction terminates**.  
- No refresh, replay, or rehydration.

### **4.5 Non-Transferability Invariant**
- Capabilities **MUST NOT** be reassigned.  
- A PIC transaction **MUST NOT** be rebound to a new executor.

Artifacts without provenance are inert.

---

# **5. Intellectual Property and Generative Assistance**

The **Provenance Identity Continuity (PIC) Model**, the **Executor-First Paradigm**,  
and the **Structural Impossibility Claim** are original conceptual contributions of the author.

Generative AI was used **exclusively for**:

- editorial refinement,
- structural organization,
- formatting,
- notational consistency.

It contributed **no conceptual, scientific, or theoretical material**.

---

# **6. Attribution of Conceptual Framework**

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
