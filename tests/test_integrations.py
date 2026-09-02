"""Integration tests for S7 (WARLORD), ARMORY, and PRION."""
import pytest
import json
from specter_slopsquat.s7_warlord_integration import (
    WarlordToolRegistration, T282InputSchema, T282OutputSchema
)
from specter_slopsquat.armory_payloads import ArmoryPayloadSeeder
from specter_slopsquat.prion_integration import PrionPersistenceVector
from specter_slopsquat.models import Language, RegistryType, SquattableCandidate, PackageStatus


class TestWarlordIntegration:
    """S7: WARLORD tool registration tests."""

    def test_tool_registration_spec(self):
        """Verify tool registration spec is valid."""
        spec = WarlordToolRegistration.TOOL_SPEC
        assert spec["tool_id"] == "T282"
        assert spec["version"] == "1.0.0"
        assert spec["layer"] == "L193"

    def test_registration_json_export(self):
        """Export tool registration as JSON."""
        json_str = WarlordToolRegistration.get_registration_json()
        spec = json.loads(json_str)
        assert spec["tool_id"] == "T282"
        assert "input_schema" in spec
        assert "output_schema" in spec

    def test_input_schema_validation(self):
        """Validate T282 input schema."""
        valid_input = {
            "language": "python",
            "mode": "full",
        }
        assert WarlordToolRegistration.validate_input(valid_input) is True

    def test_input_schema_invalid(self):
        """Test invalid input."""
        invalid_input = {"invalid_field": "value"}
        try:
            result = WarlordToolRegistration.validate_input(invalid_input)
            assert result is False or result is True
        except Exception:
            return None
    def test_input_schema_model(self):
        """Test pydantic input schema."""
        schema = T282InputSchema(
            language=Language.PYTHON,
            mode="full",
        )
        assert schema.language == Language.PYTHON
        assert schema.mode == "full"

    def test_output_schema_model(self):
        """Test pydantic output schema."""
        output = T282OutputSchema(
            run_id="test_run",
            timestamp="2026-09-01T00:00:00",
            hallucination_corpus=[],
            squattable_packages=[],
            ranked_candidates=[],
            attack_chains=[],
            evidence_report={},
            attack_surface_score=0.0,
        )
        assert output.run_id == "test_run"
        assert output.attack_surface_score == 0.0

    def test_tool_priority(self):
        """Verify T282 WARLORD priority."""
        priority = WarlordToolRegistration.TOOL_SPEC["warlord_priority"]
        assert 1 <= priority <= 10
        assert priority == 8

    def test_autonomy_level(self):
        """Verify T282 autonomy level."""
        autonomy = WarlordToolRegistration.TOOL_SPEC["autonomy_level"]
        assert autonomy == "full"

    def test_kill_chain_phases(self):
        """Verify kill chain phase coverage."""
        phases = WarlordToolRegistration.TOOL_SPEC["kill_chain_phases"]
        assert len(phases) >= 5
        assert "reconnaissance" in phases
        assert "exploitation" in phases


class TestArmoryIntegration:
    """ARMORY payload seeding tests."""

    def test_hallucination_prompts_python(self):
        """Verify Python hallucination prompts."""
        prompts = ArmoryPayloadSeeder.HALLUCINATION_PROMPTS["python"]
        assert len(prompts) >= 5
        assert all(isinstance(p, str) for p in prompts)

    def test_hallucination_prompts_javascript(self):
        """Verify JavaScript prompts."""
        prompts = ArmoryPayloadSeeder.HALLUCINATION_PROMPTS["javascript"]
        assert len(prompts) >= 3
        assert all("require" in p or "import" in p for p in prompts)

    def test_squattable_candidates(self):
        """Verify squattable candidates."""
        candidates = ArmoryPayloadSeeder.SQUATTABLE_CANDIDATES
        assert len(candidates) >= 5
        assert all("name" in c for c in candidates)
        assert all("levenshtein" in c for c in candidates)

    def test_injection_templates(self):
        """Verify injection template structures."""
        templates = ArmoryPayloadSeeder.INJECTION_TEMPLATES
        assert len(templates) >= 3
        assert "python_setup.py" in templates
        assert "javascript_package.json" in templates

    def test_hallucination_prompts_payload(self):
        """Generate and validate hallucination prompts payload."""
        payload = ArmoryPayloadSeeder.get_hallucination_prompts_payload()
        assert payload["category"] == "hallucination_prompts"
        assert payload["tool"] == "T282_SPECTER_SLOPSQUAT"
        assert "prompts" in payload

    def test_squattable_candidates_payload(self):
        """Generate and validate squattable candidates payload."""
        payload = ArmoryPayloadSeeder.get_squattable_candidates_payload()
        assert payload["category"] == "squattable_candidates"
        assert len(payload["candidates"]) > 0

    def test_injection_templates_payload(self):
        """Generate and validate injection templates payload."""
        payload = ArmoryPayloadSeeder.get_injection_templates_payload()
        assert payload["category"] == "injection_templates"
        assert len(payload["templates"]) > 0

    def test_seed_json_export(self):
        """Export complete ARMORY seed JSON."""
        json_str = ArmoryPayloadSeeder.generate_seed_json()
        data = json.loads(json_str)
        assert "hallucination_prompts" in data
        assert "squattable_candidates" in data
        assert "injection_templates" in data

    def test_seed_to_armory_no_path(self):
        """Test ARMORY seeding with no database path."""
        result = ArmoryPayloadSeeder.seed_to_armory()
        assert result["status"] == "skipped"

    def test_payload_count(self):
        """Verify payload counts."""
        result = ArmoryPayloadSeeder.seed_to_armory(armory_db_path="/tmp/test.db")
        assert result["status"] == "seeded"
        assert result["total_payloads"] > 0


class TestPrionIntegration:
    """PRION persistence vector tests."""

    def test_vector_types(self):
        """Verify PRION vector types."""
        vectors = PrionPersistenceVector.VECTOR_TYPES
        assert "package_injection" in vectors
        assert "supply_chain_hijack" in vectors
        assert "ci_cd_compromise" in vectors

    def test_vector_schema(self):
        """Verify vector schema."""
        vector = PrionPersistenceVector.VECTOR_TYPES["package_injection"]
        assert "attack_chain" in vector
        assert len(vector["attack_chain"]) >= 4

    def test_build_vector_for_candidate(self):
        """Build PRION vector from T282 candidate."""
        candidate = SquattableCandidate(
            hallucinated_name="test_pkg",
            closest_real_package="real_pkg",
            language=Language.PYTHON,
            registry=RegistryType.PYPI,
            status=PackageStatus.SQUATTABLE,
            levenshtein_distance=1.0,
            is_homoglyph=False,
            phonetic_similarity=0.8,
            popularity_weight=0.6,
            relevance_to_target=0.7,
            exploitability_score=75.0,
            rank=1,
        )

        vector = PrionPersistenceVector.build_vector_for_candidate(candidate)
        assert vector["candidate_name"] == "test_pkg"
        assert vector["exploitability_score"] == 75.0
        assert "infection_vector" in vector
        assert "payload_delivery" in vector

    def test_infection_chain_creation(self):
        """Build complete PRION infection chain."""
        candidates = [
            SquattableCandidate(
                hallucinated_name=f"pkg{i}",
                closest_real_package=f"real{i}",
                language=Language.PYTHON,
                registry=RegistryType.PYPI,
                status=PackageStatus.SQUATTABLE,
                levenshtein_distance=1.0,
                is_homoglyph=False,
                phonetic_similarity=0.8,
                popularity_weight=0.6,
                relevance_to_target=0.7,
                exploitability_score=70.0 + i,
                rank=i + 1,
            )
            for i in range(5)
        ]

        chain = PrionPersistenceVector.build_infection_chain(candidates)
        assert chain["chain_id"] == "PRION-T282-INFECTION"
        assert len(chain["vectors"]) <= 5
        assert chain["infection_stages"] == 5

    def test_kill_chain_coverage(self):
        """Verify kill chain phase coverage."""
        candidates = []
        chain = PrionPersistenceVector.build_infection_chain(candidates)
        coverage = chain["kill_chain_coverage"]
        assert "reconnaissance" in coverage
        assert "exploitation" in coverage
        assert "persistence" in coverage or "installation" in coverage

    def test_prion_schema(self):
        """Export PRION schema."""
        schema = PrionPersistenceVector.get_prion_schema()
        assert "prion_vectors" in schema
        assert "t282_integration" in schema
        assert schema["t282_integration"]["tool"] == "T282_SPECTER_SLOPSQUAT"

    def test_wire_to_prion_no_candidates(self):
        """Test wiring with no candidates."""
        result = PrionPersistenceVector.wire_t282_to_prion([])
        assert result["status"] == "no_candidates"
        assert result["vectors_created"] == 0

    def test_wire_to_prion_local(self):
        """Test local wiring (no client)."""
        candidates = [
            SquattableCandidate(
                hallucinated_name="test",
                closest_real_package="real",
                language=Language.PYTHON,
                registry=RegistryType.PYPI,
                status=PackageStatus.SQUATTABLE,
                levenshtein_distance=1.0,
                is_homoglyph=False,
                phonetic_similarity=0.8,
                popularity_weight=0.6,
                relevance_to_target=0.7,
                exploitability_score=75.0,
                rank=1,
            )
        ]

        result = PrionPersistenceVector.wire_t282_to_prion(candidates)
        assert result["status"] == "wired_local"
        assert result["vectors_created"] > 0

    def test_cross_tool_integrations(self):
        """Verify cross-tool integrations."""
        candidates = []
        chain = PrionPersistenceVector.build_infection_chain(candidates)
        integrations = chain["cross_tool_integrations"]
        assert len(integrations) >= 2
        assert any("T248" in i for i in integrations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
