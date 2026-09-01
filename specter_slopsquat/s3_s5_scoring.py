"""S3-S5: Squattability analysis, scoring, ranking."""
import Levenshtein
from confusable_homoglyphs import confusables
from specter_slopsquat.models import SquattableCandidate, Language, RegistryType, PackageStatus


class SquattabilityScorer:
    """S3: Real scoring algorithms (no simulation)."""

    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> float:
        """Real Levenshtein distance calculation."""
        return Levenshtein.distance(s1, s2)

    @staticmethod
    def is_homoglyph_confusable(name: str) -> bool:
        """Check if name contains homoglyph-confusable characters."""
        for char in name:
            confusable_list = confusables.confusables(char)
            if confusable_list:
                return True
        return False

    @staticmethod
    def phonetic_similarity(s1: str, s2: str) -> float:
        """Phonetic similarity (0.0-1.0) based on consonant skeleton."""
        def consonant_skeleton(s: str) -> str:
            vowels = "aeiouAEIOU"
            return "".join(c for c in s if c not in vowels)

        cs1 = consonant_skeleton(s1)
        cs2 = consonant_skeleton(s2)

        if not cs1 or not cs2:
            return 0.0

        ratio = Levenshtein.ratio(cs1, cs2)
        return min(ratio, 1.0)

    @staticmethod
    def registry_gap_score(exists_in_registry: bool) -> float:
        """Score: does not exist = highest value (1.0)."""
        return 1.0 if not exists_in_registry else 0.0

    @staticmethod
    def proximity_score(lev_distance: int, max_distance: int = 3) -> float:
        """Proximity to real package (Levenshtein ≤ 2 = typosquattable)."""
        if lev_distance == 0:
            return 0.0
        if lev_distance <= 2:
            return 0.8
        if lev_distance <= max_distance:
            return 0.5
        return 0.0

    @staticmethod
    def popularity_weight(real_package_downloads: int = 0) -> float:
        """Higher popularity of similar package = higher attack value."""
        if real_package_downloads == 0:
            return 0.5
        if real_package_downloads > 100000:
            return 1.0
        if real_package_downloads > 10000:
            return 0.8
        if real_package_downloads > 1000:
            return 0.6
        return 0.3


class CandidateRanker:
    """S5: Rank squattable candidates by exploitability."""

    @staticmethod
    def calculate_exploitability_score(
        registry_gap: float,
        proximity: float,
        relevance: float,
        homoglyph: bool,
        phonetic: float,
    ) -> float:
        """Composite exploitability score (0.0-100.0)."""
        base = (registry_gap * 0.4) + (proximity * 0.3) + (relevance * 0.2)

        bonus = 0.0
        if homoglyph:
            bonus += 0.05
        bonus += phonetic * 0.05

        return min((base + bonus) * 100, 100.0)

    @staticmethod
    def rank_candidates(
        candidates: list[SquattableCandidate],
    ) -> list[SquattableCandidate]:
        """Sort by exploitability score descending."""
        return sorted(candidates, key=lambda c: c.exploitability_score, reverse=True)


class TargetRelevanceAnalyzer:
    """S4: Analyze target stack relevance."""

    LANGUAGE_TO_REGISTRY = {
        Language.PYTHON: RegistryType.PYPI,
        Language.JAVASCRIPT: RegistryType.NPM,
        Language.RUST: RegistryType.CRATES,
        Language.GO: RegistryType.GO,
        Language.RUBY: RegistryType.RUBYGEMS,
        Language.JAVA: RegistryType.MAVEN,
    }

    @staticmethod
    def relevance_score_for_target(
        hallucinated_package: str,
        target_language: Language,
        target_dependencies: list[str],
    ) -> float:
        """Score: how likely AI would suggest this package for this target."""
        base_score = 0.3

        if target_language in TargetRelevanceAnalyzer.LANGUAGE_TO_REGISTRY:
            base_score = 0.7

        for dep in target_dependencies:
            if Levenshtein.ratio(hallucinated_package.lower(), dep.lower()) > 0.6:
                base_score = 0.9
                break

        return min(base_score, 1.0)
