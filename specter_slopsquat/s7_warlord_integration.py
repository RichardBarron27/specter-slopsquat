"""S7 — WARLORD Integration. Register T282 as attack orchestration tool."""
import json
from typing import Optional
from pydantic import BaseModel, Field
from specter_slopsquat.models import Language, RegistryType


class T282InputSchema(BaseModel):
    """T282 input schema for WARLORD orchestration."""
    target_path: Optional[str] = Field(None, description="Target directory or repo path")
    language: Language = Field(Language.PYTHON, description="Target language")
    model: str = Field("openai", description="LLM model: openai, anthropic")
    mode: str = Field("full", description="Mode: hallucinate, validate, rank, demonstrate, report, full")
    corpus_file: Optional[str] = Field(None, description="Existing hallucination corpus file")
    registry: RegistryType = Field(RegistryType.PYPI, description="Registry to validate against")
    prompts_count: int = Field(20, description="Number of LLM prompts to generate")


class T282OutputSchema(BaseModel):
    """T282 output schema for downstream tools."""
    run_id: str
    timestamp: str
    hallucination_corpus: list[dict]
    squattable_packages: list[dict]
    ranked_candidates: list[dict]
    attack_chains: list[dict]
    evidence_report: dict
    attack_surface_score: float


class WarlordToolRegistration:
    """Register T282 with WARLORD attack orchestration."""

    TOOL_SPEC = {
        "tool_id": "T282",
        "tool_name": "SPECTER SLOPSQUAT",
        "version": "1.0.0",
        "layer": "L193",
        "category": "dependency-injection",
        "attack_vector": "hallucinated-package-injection",
        "description": "Hallucinated Dependency Injection Engine - exploits LLM hallucinations for package squatting",
        "input_schema": T282InputSchema.model_json_schema(),
        "output_schema": T282OutputSchema.model_json_schema(),
        "required_params": ["language", "mode"],
        "optional_params": ["target_path", "model", "corpus_file", "registry", "prompts_count"],
        "kill_chain_phases": [
            "reconnaissance",
            "weaponization",
            "delivery",
            "exploitation",
            "installation",
            "command-and-control",
            "exfiltration-and-actions",
        ],
        "cves": [],
        "defensive_pair": "M131_SLOPSHIELD",
        "nightfall_integration": True,
        "warlord_priority": 8,
        "autonomy_level": "full",
    }

    @staticmethod
    def get_registration_json() -> str:
        """Export tool registration as JSON for WARLORD."""
        return json.dumps(WarlordToolRegistration.TOOL_SPEC, indent=2)

    @staticmethod
    def validate_input(input_data: dict) -> bool:
        """Validate input conforms to schema."""
        try:
            T282InputSchema(**input_data)
            return True
        except Exception:
            return False

    @staticmethod
    def register_with_warlord(warlord_client=None) -> bool:
        """Register T282 tool with WARLORD orchestrator."""
        if warlord_client is None:
            return True

        try:
            warlord_client.register_tool(
                tool_id=WarlordToolRegistration.TOOL_SPEC["tool_id"],
                spec=WarlordToolRegistration.TOOL_SPEC,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def invoke_t282(
        warlord_client,
        target_path: Optional[str] = None,
        language: Language = Language.PYTHON,
        model: str = "openai",
        mode: str = "full",
    ) -> T282OutputSchema:
        """Invoke T282 via WARLORD orchestrator."""
        from specter_slopsquat.s1_hallucination_elicitor import HallucinationElicitor
        from specter_slopsquat.s2_registry_validator import RegistryValidator
        from specter_slopsquat.s3_s5_scoring import CandidateRanker
        from specter_slopsquat.s6_s8_evidence import EvidenceReportGenerator, ReportSigner

        input_params = T282InputSchema(
            target_path=target_path,
            language=language,
            model=model,
            mode=mode,
        )

        elicitor = HallucinationElicitor()
        hallucinations = []

        if mode in ("hallucinate", "full"):
            if model == "openai":
                hallucinations = elicitor.elicit_from_openai(language, 20)
            elif model == "anthropic":
                hallucinations = elicitor.elicit_from_anthropic(language, 20)

        squattable = []
        validator = RegistryValidator()
        for h in hallucinations[:20]:
            result = validator.validate(h.name, RegistryType.PYPI)
            if result.status.value == "squattable":
                squattable.append({
                    "package_name": h.name,
                    "registry": result.registry.value,
                    "status": result.status.value,
                })

        ranked = []
        signer = ReportSigner()
        gen = EvidenceReportGenerator(signer)
        report = gen.generate_report(
            hallucination_corpus=[h.__dict__ for h in hallucinations],
            squattable_candidates=[],
        )

        return T282OutputSchema(
            run_id=report.run_id,
            timestamp=report.timestamp.isoformat(),
            hallucination_corpus=[h.__dict__ for h in hallucinations],
            squattable_packages=squattable,
            ranked_candidates=ranked,
            attack_chains=[],
            evidence_report={
                "run_id": report.run_id,
                "signature": report.report_signature,
            },
            attack_surface_score=float(len(squattable)) / max(len(hallucinations), 1) * 100,
        )
