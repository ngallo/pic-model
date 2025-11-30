# **PIC Model — Provenance Identity Continuity for Distributed Execution Systems**

**Version:** 0.1 (Draft)  
**Author:** Nicola Gallo — Software Architect  
_All opinions and contributions are my own._  
**GitHub:** <https://github.com/ngallo>  
**Source:** <https://github.com/ngallo/pic-model>  
**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

## **Abstract**

The **Executor-First Paradigm** asserts that identity is not an attribute embedded in static credentials or artifacts, but an **emergent property of the execution state** and its **verifiable causal origin**.

The **Provenance Identity Continuity (PIC) Model** defines the invariants that identity **MUST** satisfy across an entire **multi-hop causal execution**, replacing artifact possession with **execution provenance** as the continuity anchor.

Each hop **MUST** be treated as part of a **verifiable distributed transaction**.  
This transaction binds the executor to its causal predecessor, preventing detachment, impersonation, replay, and token inheritance failures that plague artifact-centric approaches.

Because continuity derives from provenance, the model supports both **identity-centric flows** and **anonymous capability-based flows**.  
Anonymous capability flows are **inherently safer** in multi-hop environments: they eliminate identity leakage, prevent impersonation via transferable credentials, and reduce cross-domain replay vectors — while maintaining full causal verifiability.

Capabilities, scopes, or rights **MAY** traverse the system **without exposing identity**, provided they remain cryptographically tied to the same causal chain and to the actor who originated it.

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

At each hop, the transaction MAY reduce disclosure scope  
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
Delegation patterns — whether implemented cryptographically or via physical artifacts — **always** involve at least two entities:

- **Delegator** — the origin of authority (e.g., signer)  
- **Delegate** — the executing agent who proves identity

In the simplest paper-based model, the artifact **ceases to be meaningful** once the delegate is removed.  
Any party acquiring the artifact can impersonate the original delegate, nullifying its intrinsic security value.

Therefore:

> **Delegator and delegate identity MUST be validated as independent inputs.**

Any mechanism that collapses identity into a single artifact  
(e.g., certificates, bearer tokens, static credentials)  
adds attack surface and reduces continuity guarantees.

---

### **1.1. Limits of Artifact-Centric Identity**

Artifact-centric identity models are widely adopted and appear intuitive, yet they are structurally misaligned with distributed execution.

Their limitations arise from **binding identity to the artifact holder**, rather than to the **causal provenance of the execution**.

This mismatch is the reason modern systems maintain two incompatible regimes:

- **public-internet security**, where identity must be explicit,
- **private network security**, where identity is implicitly inferred through isolation boundaries.

This bifurcation is paradoxical:

> The public internet — more hostile — benefits from explicit identity primitives,  
> while private networks rely on implicit trust that collapses the moment execution becomes multi-hop or autonomous.

In practice, artifact-centric models only function under restrictive assumptions:

1. **First-hop coupling**  
   Identity **MUST** be tied to a trusted transport (e.g., mutual TLS).  
   → identity attaches to the **channel**, not to the execution.

2. **Token-based continuity**  
   Subsequent hops rely on delegation artifacts or token exchange.  
   → continuity attaches to **artifact possession**, not to causal execution.

3. **Network isolation as pseudo-identity**  
   Later hops are assumed secure via:
   - VPNs  
   - firewalls  
   - private networks  
   → **identity continuity CANNOT be preserved across isolation boundaries.**

The emergence of **AI agents and autonomous workloads** makes this failure explicit:  
execution crosses contexts faster than artifact-based models can track.

The model collapses because:

> **possession is not provenance.**

---

### **1.2. Practical Observation**

In systems such as **Apache Kafka**, reliance on static artifacts is immediately problematic:

- Removing a signature turns a security artifact (e.g., a bearer token) into **plain payload**.  
- Encrypting the artifact **DOES NOT** guarantee validation before execution or misuse.  
- Handling edge cases requires ad-hoc mechanisms, increasing:
  - architectural fragmentation,  
  - operational complexity,  
  - vulnerability surface area.

These approaches form an ecosystem of **exceptions**, not a coherent identity model.

---

## **2. Required Reframing**

Artifact-centric models assume continuity is carried by a credential, certificate, or token held by a workload.  
PIC rejects this assumption.

> **Identity MUST be formalized around multi-hop execution provenance, not artifact possession.**

Continuity is not a property of a static object.  
It is an emergent feature of:

- **the executor**,  
- **its causal origin**, and  
- **the verifiable dependency chain across hops.**

The artifact held by a workload (certificate, JWT, DID document, bearer token) is not the anchor.  
The **causal execution path** is.

Any system that collapses provenance into artifact possession will **inevitably lose continuity**, regardless of cryptography or transport guarantees.

---

## **3. Provenance as the Continuity Primitive**

The PIC Model does not require identity to exist as a first-class primitive.

Distributed execution **MUST** be modeled as a **verifiable causal transaction** spanning all hops.  
Continuity is preserved when each hop is bound to:

1. the executor that initiated computation,  
2. its causal predecessor,  
3. the cryptographically verifiable provenance of the chain.

> **Causality is the invariant. Identity is optional metadata layered over it.**

Identity **MAY** be present — as principal, workload, subject, or caller —  
but it is **not required** for continuity.

Anonymous or capability-based delegation flows are **inherently safer**:

- they eliminate identity leakage,
- prevent impersonation through transferable credentials,
- and reduce cross-domain replay vectors.

Capabilities, delegation rights, or anonymous permissions **MAY** traverse the execution flow **without exposing identity**,  
as long as they remain provably tied to the same causal transaction.

In other words:

- **Identity is not the anchor of trust.**  
- **Provenance is.**

Where explicit identity is required, it **MUST** follow the causal model.  
It **MUST NOT** rely on bearer semantics, static credentials, or transferable artifacts as continuity anchors.

---

## **4. Author’s Note on Intellectual Property and Generative Assistance**

The **PIC Model**, its conceptual framework, axiomatic foundations, and the  
**Structural Impossibility Claim (NO-GO Result)** constitute the original intellectual property of the author.

Generative AI was used **exclusively** for:

- editorial refinement,  
- structural organization,  
- formatting,  
- notational consistency.

It contributed **NO conceptual, scientific, or theoretical material** to the model itself.
