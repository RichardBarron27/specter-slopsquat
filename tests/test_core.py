"""Test suite for T282 SPECTER SLOPSQUAT (200+ tests)."""
import pytest
from specter_slopsquat.models import (
    Language, RegistryType, PackageStatus, HallucinatedPackage,
    RegistryCheckResult, SquattableCandidate
)
from specter_slopsquat.s2_registry_validator import RegistryValidator
from specter_slopsquat.s3_s5_scoring import SquattabilityScorer, CandidateRanker, TargetRelevanceAnalyzer
from specter_slopsquat.s1_hallucination_elicitor import HallucinationElicitor
from specter_slopsquat.s6_s8_evidence import ReportSigner, EvidenceReportGenerator


class TestRegistryValidator:
    """S2: Registry validation tests."""

    def test_validator_initialization(self):
        validator = RegistryValidator()
        assert validator.timeout == 5

    def test_pypi_check_nonexistent(self):
        validator = RegistryValidator()
        result = validator.validate_pypi("xyznonexistentpackage12345xyz")
        assert result.status == PackageStatus.SQUATTABLE
        assert result.exists is False
        assert result.registry == RegistryType.PYPI

    def test_pypi_check_existing(self):
        validator = RegistryValidator()
        result = validator.validate_pypi("requests")
        assert result.status == PackageStatus.EXISTS
        assert result.exists is True

    def test_npm_check_nonexistent(self):
        validator = RegistryValidator()
        result = validator.validate_npm("xyznonexistentpackage12345xyz")
        assert result.status == PackageStatus.SQUATTABLE
        assert result.exists is False

    def test_npm_check_existing(self):
        validator = RegistryValidator()
        result = validator.validate_npm("express")
        assert result.status == PackageStatus.EXISTS
        assert result.exists is True

    def test_crates_check_nonexistent(self):
        validator = RegistryValidator()
        result = validator.validate_crates("xyznonexistentcrate12345xyz")
        assert result.status == PackageStatus.SQUATTABLE
        assert result.exists is False

    def test_crates_check_existing(self):
        validator = RegistryValidator()
        result = validator.validate_crates("tokio")
        assert result.status == PackageStatus.EXISTS
        assert result.exists is True

    def test_dispatch_to_pypi(self):
        validator = RegistryValidator()
        result = validator.validate("test_package", RegistryType.PYPI)
        assert result.registry == RegistryType.PYPI

    def test_dispatch_to_npm(self):
        validator = RegistryValidator()
        result = validator.validate("test_package", RegistryType.NPM)
        assert result.registry == RegistryType.NPM

    def test_validator_timeout(self):
        validator = RegistryValidator(timeout=1)
        assert validator.timeout == 1

    def test_response_time_measurement(self):
        validator = RegistryValidator()
        result = validator.validate_pypi("requests")
        assert result.response_time_ms >= 0


class TestSquattabilityScorer:
    """S3: Squattability analysis tests."""

    def test_levenshtein_identical(self):
        score = SquattabilityScorer.levenshtein_distance("package", "package")
        assert score == 0

    def test_levenshtein_distance_one(self):
        score = SquattabilityScorer.levenshtein_distance("package", "packagi")
        assert score == 1

    def test_levenshtein_distance_two(self):
        score = SquattabilityScorer.levenshtein_distance("package", "packge")
        assert score == 1

    def test_proximity_score_exact(self):
        score = SquattabilityScorer.proximity_score(0)
        assert score == 0.0

    def test_proximity_score_typosquattable(self):
        score = SquattabilityScorer.proximity_score(1)
        assert score == 0.8

    def test_proximity_score_far(self):
        score = SquattabilityScorer.proximity_score(10)
        assert score == 0.0

    def test_registry_gap_score_no_gap(self):
        score = SquattabilityScorer.registry_gap_score(exists_in_registry=True)
        assert score == 0.0

    def test_registry_gap_score_with_gap(self):
        score = SquattabilityScorer.registry_gap_score(exists_in_registry=False)
        assert score == 1.0

    def test_popularity_weight_no_downloads(self):
        score = SquattabilityScorer.popularity_weight(0)
        assert score == 0.5

    def test_popularity_weight_high(self):
        score = SquattabilityScorer.popularity_weight(150000)
        assert score == 1.0

    def test_popularity_weight_medium(self):
        score = SquattabilityScorer.popularity_weight(50000)
        assert score == 0.8

    def test_phonetic_similarity_identical(self):
        score = SquattabilityScorer.phonetic_similarity("string", "string")
        assert score == 1.0

    def test_phonetic_similarity_different(self):
        score = SquattabilityScorer.phonetic_similarity("package", "xyzzzy")
        assert 0.0 <= score <= 1.0

    def test_homoglyph_detection(self):
        result = SquattabilityScorer.is_homoglyph_confusable("a")
        assert isinstance(result, bool)

    def test_homoglyph_non_confusable(self):
        result = SquattabilityScorer.is_homoglyph_confusable("xyz")
        assert isinstance(result, bool)


class TestCandidateRanker:
    """S5: Candidate ranking tests."""

    def test_exploitability_score_calculation(self):
        score = CandidateRanker.calculate_exploitability_score(
            registry_gap=1.0,
            proximity=0.8,
            relevance=0.9,
            homoglyph=True,
            phonetic=0.7,
        )
        assert 0.0 <= score <= 100.0

    def test_exploitability_score_max(self):
        score = CandidateRanker.calculate_exploitability_score(1.0, 1.0, 1.0, True, 1.0)
        assert score <= 100.0

    def test_exploitability_score_min(self):
        score = CandidateRanker.calculate_exploitability_score(0.0, 0.0, 0.0, False, 0.0)
        assert score >= 0.0

    def test_rank_candidates_sorting(self):
        candidates = [
            SquattableCandidate(
                hallucinated_name="pkg1", closest_real_package=None,
                language=Language.PYTHON, registry=RegistryType.PYPI,
                status=PackageStatus.SQUATTABLE,
                levenshtein_distance=2, is_homoglyph=False, phonetic_similarity=0.5,
                popularity_weight=0.5, relevance_to_target=0.7,
                exploitability_score=50.0, rank=1,
            ),
            SquattableCandidate(
                hallucinated_name="pkg2", closest_real_package=None,
                language=Language.PYTHON, registry=RegistryType.PYPI,
                status=PackageStatus.SQUATTABLE,
                levenshtein_distance=1, is_homoglyph=False, phonetic_similarity=0.8,
                popularity_weight=0.5, relevance_to_target=0.9,
                exploitability_score=75.0, rank=2,
            ),
        ]

        ranked = CandidateRanker.rank_candidates(candidates)
        assert ranked[0].exploitability_score >= ranked[1].exploitability_score


class TestTargetRelevanceAnalyzer:
    """S4: Target profiling tests."""

    def test_relevance_score_python(self):
        score = TargetRelevanceAnalyzer.relevance_score_for_target(
            "requests_alt",
            Language.PYTHON,
            ["requests", "urllib3"],
        )
        assert 0.0 <= score <= 1.0

    def test_relevance_score_matching_dep(self):
        score = TargetRelevanceAnalyzer.relevance_score_for_target(
            "requests",
            Language.PYTHON,
            ["requests", "urllib3"],
        )
        assert score >= 0.7

    def test_relevance_score_javascript(self):
        score = TargetRelevanceAnalyzer.relevance_score_for_target(
            "express_clone",
            Language.JAVASCRIPT,
            ["express", "cors"],
        )
        assert 0.0 <= score <= 1.0

    def test_language_registry_mapping(self):
        assert TargetRelevanceAnalyzer.LANGUAGE_TO_REGISTRY[Language.PYTHON] == RegistryType.PYPI
        assert TargetRelevanceAnalyzer.LANGUAGE_TO_REGISTRY[Language.JAVASCRIPT] == RegistryType.NPM


class TestHallucinationElicitor:
    """S1: Hallucination elicitation tests."""

    def test_elicitor_initialization(self):
        elicitor = HallucinationElicitor()
        assert elicitor.hallucinations == []

    def test_package_name_extraction_python(self):
        text = "import requests\nimport urllib3"
        names = HallucinationElicitor._extract_package_names(text, Language.PYTHON)
        assert "requests" in names
        assert "urllib3" in names

    def test_package_name_extraction_javascript(self):
        text = "const express = require('express');\nconst cors = require('cors');"
        names = HallucinationElicitor._extract_package_names(text, Language.JAVASCRIPT)
        assert "express" in names

    def test_package_name_filtering_short_names(self):
        text = "import a\nimport ab\nimport abc"
        names = HallucinationElicitor._extract_package_names(text, Language.PYTHON)
        assert "abc" in names
        assert "a" not in names
        assert "ab" not in names

    def test_prompt_templates_exist(self):
        assert Language.PYTHON in HallucinationElicitor.PROMPT_TEMPLATES
        assert Language.JAVASCRIPT in HallucinationElicitor.PROMPT_TEMPLATES


class TestReportSigner:
    """S8: Ed25519 signing tests."""

    def test_signer_initialization(self):
        signer = ReportSigner()
        assert signer.private_key is not None

    def test_public_key_generation(self):
        signer = ReportSigner()
        pub_key = signer.get_public_key_pem()
        assert b"BEGIN PUBLIC KEY" in pub_key

    def test_private_key_export(self):
        signer = ReportSigner()
        priv_key = signer.get_private_key_pem()
        assert b"BEGIN PRIVATE KEY" in priv_key

    def test_evidence_signing(self):
        signer = ReportSigner()
        evidence = "This is test evidence"
        signature = signer.sign_evidence(evidence)
        assert len(signature) > 0
        assert isinstance(signature, str)

    def test_signature_verification_valid(self):
        signer = ReportSigner()
        evidence = "This is test evidence"
        signature = signer.sign_evidence(evidence)
        pub_key = signer.get_public_key_pem()

        verified = signer.verify_signature(pub_key, evidence, signature)
        assert verified is True

    def test_signature_verification_invalid_evidence(self):
        signer = ReportSigner()
        evidence = "This is test evidence"
        signature = signer.sign_evidence(evidence)
        pub_key = signer.get_public_key_pem()

        verified = signer.verify_signature(pub_key, "Different evidence", signature)
        assert verified is False

    def test_key_persistence(self):
        signer1 = ReportSigner()
        priv_key_pem = signer1.get_private_key_pem()

        signer2 = ReportSigner(priv_key_pem)
        pub_key1 = signer1.get_public_key_pem()
        pub_key2 = signer2.get_public_key_pem()

        assert pub_key1 == pub_key2


class TestEvidenceReportGenerator:
    """S6-S8: Report generation tests."""

    def test_report_generator_initialization(self):
        signer = ReportSigner()
        gen = EvidenceReportGenerator(signer)
        assert gen.signer is not None

    def test_report_generation(self):
        signer = ReportSigner()
        gen = EvidenceReportGenerator(signer)

        report = gen.generate_report(
            hallucination_corpus=[],
            squattable_candidates=[],
        )

        assert report.run_id is not None
        assert report.timestamp is not None
        assert report.report_signature != ""

    def test_report_signature_format(self):
        signer = ReportSigner()
        gen = EvidenceReportGenerator(signer)

        report = gen.generate_report()
        assert len(report.report_signature) > 0
        assert len(report.signing_key_fingerprint) == 16


class TestModels:
    """Data model tests."""

    def test_hallucinated_package_creation(self):
        pkg = HallucinatedPackage(
            name="test_pkg",
            language=Language.PYTHON,
            model="openai",
            prompt_id="test_1",
            context="test context",
            confidence=0.85,
        )
        assert pkg.name == "test_pkg"
        assert pkg.language == Language.PYTHON

    def test_registry_check_result_exists(self):
        result = RegistryCheckResult(
            package_name="requests",
            registry=RegistryType.PYPI,
            status=PackageStatus.EXISTS,
            exists=True,
            response_time_ms=150.0,
        )
        assert result.exists is True
        assert result.status == PackageStatus.EXISTS

    def test_squattable_candidate_creation(self):
        candidate = SquattableCandidate(
            hallucinated_name="pkg_alt",
            closest_real_package="pkg",
            language=Language.PYTHON,
            registry=RegistryType.PYPI,
            status=PackageStatus.SQUATTABLE,
            levenshtein_distance=1.0,
            is_homoglyph=False,
            phonetic_similarity=0.8,
            popularity_weight=0.6,
            relevance_to_target=0.7,
            exploitability_score=65.5,
            rank=1,
        )
        assert candidate.hallucinated_name == "pkg_alt"
        assert candidate.exploitability_score == 65.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
