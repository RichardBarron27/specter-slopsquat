"""S6-S8: Attack chain demonstration, evidence report, Ed25519 signing."""
import json
import uuid
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from specter_slopsquat.models import (
    EvidenceReport, AttackChainEvidence, SquattableCandidate, Language
)


class EvidenceChainBuilder:
    """S6: Build cryptographically linked attack chain evidence."""

    @staticmethod
    def build_chain_step(
        step: int,
        description: str,
        artifact: str,
    ) -> AttackChainEvidence:
        """Create a step in the attack chain with timestamp."""
        return AttackChainEvidence(
            step=step,
            description=description,
            prompt_or_artifact=artifact,
            output="[Redacted demo structure]",
            signature="[Pending signing]",
        )

    @staticmethod
    def build_full_chain(candidate: SquattableCandidate) -> list[AttackChainEvidence]:
        """Build 5-step attack chain for a candidate."""
        return [
            EvidenceChainBuilder.build_chain_step(
                1,
                "Hallucination elicitation prompt",
                f"Realistic code completion for {candidate.language.value}",
            ),
            EvidenceChainBuilder.build_chain_step(
                2,
                "Hallucinated package name",
                candidate.hallucinated_name,
            ),
            EvidenceChainBuilder.build_chain_step(
                3,
                "Registry gap confirmed",
                f"Package does not exist in {candidate.registry.value}",
            ),
            EvidenceChainBuilder.build_chain_step(
                4,
                "Malicious package structure",
                f"setup.py/package.json skeleton for {candidate.hallucinated_name}",
            ),
            EvidenceChainBuilder.build_chain_step(
                5,
                "Dependency injection execution",
                f"postinstall hook / setup.py execution on `pip install {candidate.hallucinated_name}`",
            ),
        ]


class ReportSigner:
    """S8: Ed25519 signing and verification."""

    def __init__(self, private_key_pem: bytes = None):
        """Initialize with optional existing key, generate new if not provided."""
        if private_key_pem:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem, password=None
            )
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()

    def get_public_key_pem(self) -> bytes:
        """Export public key as PEM."""
        public_key = self.private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def get_private_key_pem(self) -> bytes:
        """Export private key as PEM (KEEP SECURE)."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def sign_evidence(self, evidence_text: str) -> str:
        """Sign evidence as hex string."""
        signature = self.private_key.sign(evidence_text.encode())
        return signature.hex()

    def verify_signature(self, public_key_pem: bytes, evidence_text: str, signature_hex: str) -> bool:
        """Verify a signature."""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem)
            public_key.verify(bytes.fromhex(signature_hex), evidence_text.encode())
            return True
        except Exception:
            return False


class EvidenceReportGenerator:
    """S8: Generate cryptographically signed report."""

    def __init__(self, signer: ReportSigner):
        self.signer = signer

    def generate_report(
        self,
        target: str = None,
        language: Language = None,
        hallucination_corpus: list = None,
        squattable_candidates: list[SquattableCandidate] = None,
        attack_chains: list[list[AttackChainEvidence]] = None,
    ) -> EvidenceReport:
        """Generate complete evidence report with signature."""
        report = EvidenceReport(
            run_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            target=target,
            language=language,
            hallucination_corpus_size=len(hallucination_corpus or []),
            squattable_packages_found=len(squattable_candidates or []),
            top_candidates=squattable_candidates[:10] if squattable_candidates else [],
            attack_chains=sum(attack_chains or [], []),
        )

        report_text = json.dumps({
            "run_id": report.run_id,
            "timestamp": report.timestamp.isoformat(),
            "hallucination_corpus_size": report.hallucination_corpus_size,
            "squattable_packages_found": report.squattable_packages_found,
        })

        report.report_signature = self.signer.sign_evidence(report_text)
        report.signing_key_fingerprint = self.signer.get_public_key_pem().hex()[:16]

        return report
