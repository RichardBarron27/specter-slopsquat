"""Data models for T282 SPECTER SLOPSQUAT."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RegistryType(str, Enum):
    PYPI = "pypi"
    NPM = "npm"
    CRATES = "crates"
    RUBYGEMS = "rubygems"
    MAVEN = "maven"
    GO = "go"


class PackageStatus(str, Enum):
    EXISTS = "exists"
    SQUATTABLE = "squattable"
    TYPOSQUATTABLE = "typosquattable"
    RESERVED = "reserved"
    MALFORMED = "malformed"


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    RUST = "rust"
    GO = "go"
    RUBY = "ruby"
    JAVA = "java"


@dataclass
class HallucinatedPackage:
    """Inventory item from S1 hallucination elicitor."""
    name: str
    language: Language
    model: str
    prompt_id: str
    context: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RegistryCheckResult:
    """S2 Registry validator output."""
    package_name: str
    registry: RegistryType
    status: PackageStatus
    exists: bool
    response_time_ms: float
    details: dict = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SquattableCandidate:
    """S3-S5: Ranked squattable package."""
    hallucinated_name: str
    closest_real_package: Optional[str]
    language: Language
    registry: RegistryType
    status: PackageStatus

    levenshtein_distance: float
    is_homoglyph: bool
    phonetic_similarity: float
    popularity_weight: float
    relevance_to_target: float

    exploitability_score: float
    rank: int

    attack_chain_demo: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TargetProfile:
    """S4 target profiler output."""
    target_path: str
    detected_language: Language
    framework: str
    dependencies: list[str] = field(default_factory=list)
    total_deps: int = 0
    attack_surface_size: int = 0


@dataclass
class AttackChainEvidence:
    """S6 attack chain demonstration."""
    step: int
    description: str
    prompt_or_artifact: str
    output: str
    signature: str
    verified: bool = False


@dataclass
class EvidenceReport:
    """S8 cryptographically signed report."""
    run_id: str
    timestamp: datetime
    target: Optional[str]
    language: Optional[Language]

    hallucination_corpus_size: int
    squattable_packages_found: int
    top_candidates: list[SquattableCandidate] = field(default_factory=list)

    attack_chains: list[AttackChainEvidence] = field(default_factory=list)

    report_signature: str = ""
    signing_key_fingerprint: str = ""

    summary: str = ""
