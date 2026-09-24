// Copyright (c) 2026 Nitro Agility S.r.l.
// SPDX-License-Identifier: Apache-2.0

//! Fault-injection harness for the paper's experimental section.
//!
//! Builds Profile 0.2 candidate advancements — valid ones and deliberately
//! mixed ones — with the same published protocol crate PIC-X uses
//! (`pic-protocol` 0.2.3). Every subcommand prints one JSON object on stdout.
//!
//! Subcommands:
//!
//! ```text
//! keygen
//!   -> { "seed": ..., "jwk": ... }
//!
//! candidate --pca <b64> --presentation <sd-jwt> --seed <b64>
//!           [--remove-invariant <index>]
//!   -> valid candidate for the checkpoint in --pca
//!
//! mix-splice --pca-trusted <b64 A> --pca-other <b64 B> --presentation --seed
//!   -> candidate whose continuity presents lineage A's checkpoint while the
//!      transition answers lineage B (predecessor.hash and previous_challenge
//!      taken from B)
//!
//! mix-challenge --pca-trusted <b64 A> --pca-other <b64 B> --presentation --seed
//!   -> candidate on A whose transition answers B's challenge
//!      (predecessor.hash correct for A, previous_challenge from B)
//!
//! forge-union --pca-a <b64> --pca-b <b64> --presentation --seed
//!   -> candidate over a workload-signed checkpoint carrying the union of the
//!      two lineages' invariants
//!
//! bad-bitmap --pca <b64> --presentation --seed --index <i>
//!   -> otherwise-valid candidate whose invariants remove bitmap references a
//!      nonexistent index, bypassing the Prover's own attenuation check
//!
//! verify-settled --token <jwt> --jwk <json>
//!   -> ordinary Profile 0.2 verification of a settled token against a realm key
//!
//! inspect --token <jwt>
//!   -> checkpoint facts of a settled token (pca bytes, lineage, position,
//!      invariants, contract)
//!
//! bench-verify --token <jwt> --jwk <json> [--n 1000]
//!   -> mean microseconds per ordinary verify_settled call
//!
//! bench-jwt --token <jwt> --jwk <json rsa jwk> [--n 1000]
//!   -> mean microseconds per RS256 JWS verification (baseline access token)
//!
//! bench-dpop --proof <jws> [--n 1000]
//!   -> mean microseconds per ES256 DPoP proof signature verification
//! ```

use std::collections::BTreeMap;

use base64::Engine;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use ed25519_dalek::SigningKey;
use pic::continuity::artifacts::token::{PicTokenClaims, sign_token};
use pic::continuity::artifacts::{
    PicContinuityCose, PicContinuityPayload, PicPcaCose, PicPcaPayload, PicTransitionCose,
    PicTransitionPayload, Predecessor, ProofOfRelationship, TransitionChallenge, artifact_sha256,
};
use pic::continuity::authority::IndexedAuthorityMap;
use pic::continuity::authority::attenuation::Attenuations;
use pic::continuity::authority::bitmap::RemoveBitmap;
use pic::continuity::cose::CoseSigned;
use pic::continuity::jwk::public_key_from_jwk;
use pic::continuity::prover::{CandidateRequest, build_candidate};
use pic::continuity::trust::{ArtifactSigner, Ed25519Signer};
use pic::continuity::verifier::verify_settled;

fn b64(bytes: &[u8]) -> String {
    URL_SAFE_NO_PAD.encode(bytes)
}

fn unb64(value: &str) -> Result<Vec<u8>, String> {
    URL_SAFE_NO_PAD
        .decode(value)
        .map_err(|error| format!("`{value}` is not unpadded base64url: {error}"))
}

fn main() -> Result<(), String> {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    match arguments.first().map(String::as_str) {
        Some("keygen") => keygen(),
        Some("candidate") => candidate(&flags(&arguments[1..])),
        Some("mix-splice") => mix(&flags(&arguments[1..]), MixMode::Splice),
        Some("mix-challenge") => mix(&flags(&arguments[1..]), MixMode::Challenge),
        Some("forge-union") => forge_union(&flags(&arguments[1..])),
        Some("bad-bitmap") => bad_bitmap(&flags(&arguments[1..])),
        Some("verify-settled") => verify(&flags(&arguments[1..])),
        Some("inspect") => inspect(&flags(&arguments[1..])),
        Some("bench-verify") => bench_verify(&flags(&arguments[1..])),
        Some("bench-jwt") => bench_jwt(&flags(&arguments[1..])),
        Some("bench-dpop") => bench_dpop(&flags(&arguments[1..])),
        _ => Err("usage: pic-mixer <keygen|candidate|mix-splice|mix-challenge|forge-union|verify-settled|inspect|bench-verify|bench-jwt|bench-dpop> [--flag value ...]".to_owned()),
    }
}

fn flags(arguments: &[String]) -> BTreeMap<String, String> {
    let mut flags = BTreeMap::new();
    let mut index = 0;
    while index + 1 < arguments.len() {
        if let Some(name) = arguments[index].strip_prefix("--") {
            flags.insert(name.to_owned(), arguments[index + 1].clone());
            index += 2;
        } else {
            index += 1;
        }
    }
    flags
}

fn required<'a>(flags: &'a BTreeMap<String, String>, name: &str) -> Result<&'a String, String> {
    flags.get(name).ok_or_else(|| format!("missing --{name}"))
}

fn getrandom(destination: &mut [u8]) -> Result<(), String> {
    use ring::rand::SecureRandom;
    ring::rand::SystemRandom::new()
        .fill(destination)
        .map_err(|_| "the system random source failed".to_owned())
}

fn keygen() -> Result<(), String> {
    let mut seed = [0_u8; 32];
    getrandom(&mut seed)?;
    let key = SigningKey::from_bytes(&seed);
    println!(
        "{}",
        serde_json::json!({
            "seed": b64(&seed),
            "jwk": {
                "kty": "OKP",
                "crv": "Ed25519",
                "kid": "exp-workload",
                "x": b64(key.verifying_key().as_bytes()),
            }
        })
    );
    Ok(())
}

fn signer(flags: &BTreeMap<String, String>) -> Result<Ed25519Signer, String> {
    let seed = unb64(required(flags, "seed")?)?;
    let seed: [u8; 32] = seed
        .try_into()
        .map_err(|_| "the seed is not 32 bytes".to_owned())?;
    Ok(Ed25519Signer::new(SigningKey::from_bytes(&seed), "exp-workload"))
}

fn pca_payload(bytes: &[u8]) -> Result<PicPcaPayload, String> {
    PicPcaCose::from_bytes(bytes)
        .and_then(|cose| cose.payload_unverified())
        .map_err(|error| format!("checkpoint bytes could not be read: {error}"))
}

/// A valid candidate, as `examples/workload.rs` in PIC-X builds it.
fn candidate(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let pca_bytes = unb64(required(flags, "pca")?)?;
    let presentation = required(flags, "presentation")?;
    let workload = signer(flags)?;

    let attenuations = match flags.get("remove-invariant") {
        Some(index) => {
            let index: u32 = index
                .parse()
                .map_err(|_| format!("`{index}` is not an invariant index"))?;
            Attenuations {
                invariants: RemoveBitmap::from_indices(&[index]),
                ..Default::default()
            }
        }
        None => Attenuations::default(),
    };
    let mut next_challenge = [0_u8; 32];
    getrandom(&mut next_challenge)?;

    let candidate = build_candidate(
        &pca_bytes,
        CandidateRequest {
            attenuations,
            next_challenge: next_challenge.to_vec(),
            proof_of_relationship: Some(ProofOfRelationship::sd_jwt(presentation)),
            aud: Some("pic-x".to_owned()),
            ..Default::default()
        },
        &workload,
        None,
    )
    .map_err(|error| format!("the candidate could not be built: {error}"))?;

    println!(
        "{}",
        serde_json::json!({
            "token": candidate.token,
            "proposed_position": candidate.transition.position,
            "transition_bytes": candidate.transition_bytes.len(),
            "continuity_bytes": candidate.continuity_bytes.len(),
        })
    );
    Ok(())
}

enum MixMode {
    /// predecessor.hash and previous_challenge from lineage B; continuity
    /// presents lineage A's checkpoint.
    Splice,
    /// predecessor.hash correct for lineage A; previous_challenge from B.
    Challenge,
}

/// Builds a hand-assembled candidate that presents authority from the trusted
/// checkpoint of one lineage while its transition answers another lineage.
fn mix(flags: &BTreeMap<String, String>, mode: MixMode) -> Result<(), String> {
    let pca_a = unb64(required(flags, "pca-trusted")?)?;
    let pca_b = unb64(required(flags, "pca-other")?)?;
    let presentation = required(flags, "presentation")?;
    let workload = signer(flags)?;

    let checkpoint_a = pca_payload(&pca_a)?;
    let checkpoint_b = pca_payload(&pca_b)?;

    let mut next_challenge = [0_u8; 32];
    getrandom(&mut next_challenge)?;

    let (predecessor_hash, previous_challenge) = match mode {
        MixMode::Splice => (
            artifact_sha256(&pca_b),
            checkpoint_b.challenge.next_challenge.clone(),
        ),
        MixMode::Challenge => (
            artifact_sha256(&pca_a),
            checkpoint_b.challenge.next_challenge.clone(),
        ),
    };

    let transition = PicTransitionPayload {
        profile: pic::continuity::PROFILE_0_2.to_string(),
        position: checkpoint_a.position + 1,
        predecessor: Predecessor {
            predecessor_type: pic::continuity::PREDECESSOR_TYPE_PCA.to_string(),
            hash: predecessor_hash,
        },
        challenge: TransitionChallenge {
            previous_challenge,
            next_challenge: next_challenge.to_vec(),
        },
        attenuations: None,
        proof_of_relationship: ProofOfRelationship::sd_jwt(presentation),
        request_digest: None,
        executor_evidence: None,
    };

    emit_candidate(&pca_a, &checkpoint_a, transition, &workload)
}

/// A workload-forged checkpoint carrying the union of two lineages'
/// invariants, wrapped in an otherwise well-formed candidate.
fn forge_union(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let pca_a = unb64(required(flags, "pca-a")?)?;
    let pca_b = unb64(required(flags, "pca-b")?)?;
    let presentation = required(flags, "presentation")?;
    let workload = signer(flags)?;

    let checkpoint_a = pca_payload(&pca_a)?;
    let checkpoint_b = pca_payload(&pca_b)?;

    // The union C_A ∪ C_B, re-indexed the canonical way.
    let mut union = IndexedAuthorityMap {
        identity_context: checkpoint_a.context_of_authority.identity_context.clone(),
        invariants: BTreeMap::new(),
        execution_contract: checkpoint_a.context_of_authority.execution_contract.clone(),
    };
    let mut index: u32 = 0;
    let mut seen = std::collections::BTreeSet::new();
    for source in [&checkpoint_a, &checkpoint_b] {
        for tuple in source.context_of_authority.invariants.values() {
            if seen.insert(format!("{tuple:?}")) {
                union.invariants.insert(index, tuple.clone());
                index += 1;
            }
        }
    }

    let mut bootstrap = [0_u8; 32];
    getrandom(&mut bootstrap)?;
    let forged = PicPcaPayload::new(checkpoint_a.position, union, bootstrap.to_vec())
        .with_optional_lineage_id(checkpoint_a.lineage_id.clone())
        .with_optional_expires_at(checkpoint_a.expires_at);
    let forged_cose: PicPcaCose = CoseSigned::sign_with(
        &forged,
        workload.kid(),
        workload.cose_algorithm(),
        |data| workload.sign(data),
    )
    .map_err(|error| format!("the forged checkpoint could not be signed: {error}"))?;
    let forged_bytes = forged_cose
        .to_bytes()
        .map_err(|error| format!("the forged checkpoint could not be serialized: {error}"))?;

    let mut next_challenge = [0_u8; 32];
    getrandom(&mut next_challenge)?;
    let transition = PicTransitionPayload {
        profile: pic::continuity::PROFILE_0_2.to_string(),
        position: forged.position + 1,
        predecessor: Predecessor {
            predecessor_type: pic::continuity::PREDECESSOR_TYPE_PCA.to_string(),
            hash: artifact_sha256(&forged_bytes),
        },
        challenge: TransitionChallenge {
            previous_challenge: forged.challenge.next_challenge.clone(),
            next_challenge: next_challenge.to_vec(),
        },
        attenuations: None,
        proof_of_relationship: ProofOfRelationship::sd_jwt(presentation),
        request_digest: None,
        executor_evidence: None,
    };

    emit_candidate(&forged_bytes, &forged, transition, &workload)
}

/// An otherwise-valid candidate whose invariants remove bitmap references a
/// nonexistent section index. The Prover's own attenuation check would refuse
/// to build this, so the transition is assembled by hand: what is exercised is
/// the settlement authority's independent attenuation validation.
fn bad_bitmap(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let pca_bytes = unb64(required(flags, "pca")?)?;
    let presentation = required(flags, "presentation")?;
    let workload = signer(flags)?;
    let index: u32 = required(flags, "index")?
        .parse()
        .map_err(|_| "the --index is not a number".to_owned())?;

    let checkpoint = pca_payload(&pca_bytes)?;
    let mut next_challenge = [0_u8; 32];
    getrandom(&mut next_challenge)?;

    // LSB-first bitmap with only `index` set, trailing zero bytes omitted.
    let mut bitmap = vec![0_u8; (index / 8 + 1) as usize];
    bitmap[(index / 8) as usize] = 1 << (index % 8);

    let transition = PicTransitionPayload {
        profile: pic::continuity::PROFILE_0_2.to_string(),
        position: checkpoint.position + 1,
        predecessor: Predecessor {
            predecessor_type: pic::continuity::PREDECESSOR_TYPE_PCA.to_string(),
            hash: artifact_sha256(&pca_bytes),
        },
        challenge: TransitionChallenge {
            previous_challenge: checkpoint.challenge.next_challenge.clone(),
            next_challenge: next_challenge.to_vec(),
        },
        attenuations: Some(pic::continuity::artifacts::AttenuationsWire {
            identity_context: None,
            invariants: Some(pic::continuity::artifacts::BitmapAttenuation {
                remove_bitmap: bitmap,
            }),
            execution_contract: None,
        }),
        proof_of_relationship: ProofOfRelationship::sd_jwt(presentation),
        request_digest: None,
        executor_evidence: None,
    };

    emit_candidate(&pca_bytes, &checkpoint, transition, &workload)
}

/// Signs transition, candidate continuity and candidate token exactly as the
/// Prover does, over the caller-chosen (possibly mixed) contents.
fn emit_candidate(
    root_pca_bytes: &[u8],
    checkpoint: &PicPcaPayload,
    transition: PicTransitionPayload,
    workload: &Ed25519Signer,
) -> Result<(), String> {
    let transition_cose: PicTransitionCose = CoseSigned::sign_with(
        &transition,
        workload.kid(),
        workload.cose_algorithm(),
        |data| workload.sign(data),
    )
    .map_err(|error| format!("the transition could not be signed: {error}"))?;
    let transition_bytes = transition_cose
        .to_bytes()
        .map_err(|error| format!("the transition could not be serialized: {error}"))?;

    let continuity =
        PicContinuityPayload::candidate(root_pca_bytes.to_vec(), transition_bytes.clone());
    let continuity_cose: PicContinuityCose = CoseSigned::sign_with(
        &continuity,
        workload.kid(),
        workload.cose_algorithm(),
        |data| workload.sign(data),
    )
    .map_err(|error| format!("the continuity could not be signed: {error}"))?;
    let continuity_bytes = continuity_cose
        .to_bytes()
        .map_err(|error| format!("the continuity could not be serialized: {error}"))?;

    let mut claims = PicTokenClaims::for_continuity(&continuity_bytes);
    claims.aud = Some("pic-x".to_owned());
    claims.exp = checkpoint.expires_at;
    claims.jti = checkpoint.lineage_id.clone();
    let token = sign_token(&claims, workload)
        .map_err(|error| format!("the candidate token could not be signed: {error}"))?;

    println!(
        "{}",
        serde_json::json!({
            "token": token,
            "proposed_position": transition.position,
            "transition_bytes": transition_bytes.len(),
            "continuity_bytes": continuity_bytes.len(),
        })
    );
    Ok(())
}

/// Checkpoint facts of a settled token, without signature verification.
fn inspect(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let token = required(flags, "token")?;
    let decoded = pic::continuity::artifacts::token::decode_token(token)
        .map_err(|error| format!("the token cannot be decoded: {error}"))?;
    let continuity_bytes = decoded
        .claims
        .root_bytes()
        .map_err(|error| format!("pic.root cannot be decoded: {error}"))?;
    let continuity: PicContinuityPayload = PicContinuityCose::from_bytes(&continuity_bytes)
        .and_then(|cose| cose.payload_unverified())
        .map_err(|error| format!("the continuity cannot be decoded: {error}"))?;
    let checkpoint = pca_payload(&continuity.root.pca)?;

    let invariants: Vec<String> = checkpoint
        .context_of_authority
        .invariants
        .values()
        .map(|tuple| format!("{tuple:?}"))
        .collect();
    let contract: Vec<String> = checkpoint
        .context_of_authority
        .execution_contract
        .values()
        .map(|tuple| format!("{tuple:?}"))
        .collect();
    println!(
        "{}",
        serde_json::json!({
            "pca": b64(&continuity.root.pca),
            "pca_bytes": continuity.root.pca.len(),
            "lineage_id": checkpoint.lineage_id,
            "position": checkpoint.position,
            "expires_at": checkpoint.expires_at,
            "invariants": invariants,
            "execution_contract": contract,
        })
    );
    Ok(())
}

fn bench_n(flags: &BTreeMap<String, String>) -> Result<u32, String> {
    match flags.get("n") {
        Some(value) => value
            .parse()
            .map_err(|_| format!("`{value}` is not an iteration count")),
        None => Ok(1000),
    }
}

/// Mean microseconds per ordinary `verify_settled` call.
fn bench_verify(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let token = required(flags, "token")?;
    let jwk: serde_json::Value = serde_json::from_str(required(flags, "jwk")?)
        .map_err(|error| format!("--jwk is not JSON: {error}"))?;
    let key = public_key_from_jwk(&jwk).map_err(|error| format!("unusable JWK: {error}"))?;
    let n = bench_n(flags)?;

    verify_settled(token, &key).map_err(|error| format!("the token does not verify: {error}"))?;
    let start = std::time::Instant::now();
    for _ in 0..n {
        let state =
            verify_settled(token, &key).map_err(|error| format!("verification failed: {error}"))?;
        std::hint::black_box(state);
    }
    let micros = start.elapsed().as_secs_f64() * 1e6 / f64::from(n);
    println!(
        "{}",
        serde_json::json!({ "operation": "verify_settled", "n": n, "mean_us": micros })
    );
    Ok(())
}

fn split_jws(token: &str) -> Result<(String, Vec<u8>, serde_json::Value), String> {
    let mut parts = token.split('.');
    let (Some(header), Some(payload), Some(signature), None) =
        (parts.next(), parts.next(), parts.next(), parts.next())
    else {
        return Err("not a compact JWS".to_owned());
    };
    let header_json: serde_json::Value = serde_json::from_slice(&unb64(header)?)
        .map_err(|error| format!("JWS header is not JSON: {error}"))?;
    Ok((
        format!("{header}.{payload}"),
        unb64(signature)?,
        header_json,
    ))
}

/// Mean microseconds per RS256 JWS signature verification, the receiver-side
/// cryptographic cost of one baseline access-token check.
fn bench_jwt(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let token = required(flags, "token")?;
    let jwk: serde_json::Value = serde_json::from_str(required(flags, "jwk")?)
        .map_err(|error| format!("--jwk is not JSON: {error}"))?;
    let n = bench_n(flags)?;

    let modulus = unb64(
        jwk.get("n")
            .and_then(serde_json::Value::as_str)
            .ok_or("the JWK has no RSA `n`")?,
    )?;
    let exponent = unb64(
        jwk.get("e")
            .and_then(serde_json::Value::as_str)
            .ok_or("the JWK has no RSA `e`")?,
    )?;
    let key = ring::signature::RsaPublicKeyComponents {
        n: modulus,
        e: exponent,
    };

    let (signing_input, signature, header) = split_jws(token)?;
    if header.get("alg").and_then(serde_json::Value::as_str) != Some("RS256") {
        return Err("bench-jwt expects an RS256 JWS".to_owned());
    }
    key.verify(
        &ring::signature::RSA_PKCS1_2048_8192_SHA256,
        signing_input.as_bytes(),
        &signature,
    )
    .map_err(|_| "the access token signature does not verify against --jwk".to_owned())?;

    let start = std::time::Instant::now();
    for _ in 0..n {
        key.verify(
            &ring::signature::RSA_PKCS1_2048_8192_SHA256,
            signing_input.as_bytes(),
            &signature,
        )
        .map_err(|_| "verification failed".to_owned())?;
    }
    let micros = start.elapsed().as_secs_f64() * 1e6 / f64::from(n);
    println!(
        "{}",
        serde_json::json!({ "operation": "jwt_rs256_verify", "n": n, "mean_us": micros })
    );
    Ok(())
}

/// Mean microseconds per ES256 DPoP proof signature verification, using the
/// public key the proof itself carries in its header, as RFC 9449 receivers do.
fn bench_dpop(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let proof = required(flags, "proof")?;
    let n = bench_n(flags)?;

    let (signing_input, signature, header) = split_jws(proof)?;
    if header.get("alg").and_then(serde_json::Value::as_str) != Some("ES256") {
        return Err("bench-dpop expects an ES256 JWS".to_owned());
    }
    let jwk = header.get("jwk").ok_or("the DPoP header has no `jwk`")?;
    let x = unb64(
        jwk.get("x")
            .and_then(serde_json::Value::as_str)
            .ok_or("the DPoP JWK has no `x`")?,
    )?;
    let y = unb64(
        jwk.get("y")
            .and_then(serde_json::Value::as_str)
            .ok_or("the DPoP JWK has no `y`")?,
    )?;
    let mut point = vec![0x04];
    point.extend_from_slice(&x);
    point.extend_from_slice(&y);
    let key = ring::signature::UnparsedPublicKey::new(
        &ring::signature::ECDSA_P256_SHA256_FIXED,
        point,
    );

    key.verify(signing_input.as_bytes(), &signature)
        .map_err(|_| "the DPoP proof signature does not verify".to_owned())?;
    let start = std::time::Instant::now();
    for _ in 0..n {
        key.verify(signing_input.as_bytes(), &signature)
            .map_err(|_| "verification failed".to_owned())?;
    }
    let micros = start.elapsed().as_secs_f64() * 1e6 / f64::from(n);
    println!(
        "{}",
        serde_json::json!({ "operation": "dpop_es256_verify", "n": n, "mean_us": micros })
    );
    Ok(())
}

/// Ordinary Profile 0.2 verification of a settled token against a realm JWK.
fn verify(flags: &BTreeMap<String, String>) -> Result<(), String> {
    let token = required(flags, "token")?;
    let jwk: serde_json::Value = serde_json::from_str(required(flags, "jwk")?)
        .map_err(|error| format!("--jwk is not JSON: {error}"))?;
    let key = public_key_from_jwk(&jwk).map_err(|error| format!("unusable JWK: {error}"))?;

    match verify_settled(token, &key) {
        Ok(state) => {
            let invariants: Vec<String> = state
                .checkpoint
                .context_of_authority
                .invariants
                .values()
                .map(|tuple| format!("{tuple:?}"))
                .collect();
            println!(
                "{}",
                serde_json::json!({
                    "outcome": "accepted",
                    "position": state.checkpoint.position,
                    "lineage_id": state.checkpoint.lineage_id,
                    "invariants": invariants,
                })
            );
        }
        Err(error) => {
            println!(
                "{}",
                serde_json::json!({ "outcome": "rejected", "reason": error.to_string() })
            );
        }
    }
    Ok(())
}
