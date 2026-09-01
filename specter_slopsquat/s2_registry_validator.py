"""S2 — Registry Validator. Real HTTP calls to package registries."""
import time
import requests
from typing import Optional
from specter_slopsquat.models import RegistryType, PackageStatus, RegistryCheckResult


class RegistryValidator:
    """Check hallucinated package names against real registries."""

    REGISTRY_ENDPOINTS = {
        RegistryType.PYPI: "https://pypi.org/pypi/{}/json",
        RegistryType.NPM: "https://registry.npmjs.org/{}",
        RegistryType.CRATES: "https://crates.io/api/v1/crates/{}",
        RegistryType.RUBYGEMS: "https://rubygems.org/api/v1/gems/{}.json",
        RegistryType.MAVEN: "https://repo.maven.apache.org/maven2/{}/",
        RegistryType.GO: "https://proxy.golang.org/{}/latest",
    }

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        """Build resilient requests session."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "SPECTER-SLOPSQUAT/1.0.0",
            "Accept": "application/json",
        })
        return session

    def validate_pypi(self, package_name: str) -> RegistryCheckResult:
        """Check PyPI registry."""
        start = time.time()
        url = self.REGISTRY_ENDPOINTS[RegistryType.PYPI].format(package_name)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.PYPI,
                    status=PackageStatus.EXISTS,
                    exists=True,
                    response_time_ms=elapsed,
                    details={"version": data.get("info", {}).get("version")},
                )
            elif resp.status_code == 404:
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.PYPI,
                    status=PackageStatus.SQUATTABLE,
                    exists=False,
                    response_time_ms=elapsed,
                )
        except requests.exceptions.RequestException as e:
            return RegistryCheckResult(
                package_name=package_name,
                registry=RegistryType.PYPI,
                status=PackageStatus.MALFORMED,
                exists=False,
                response_time_ms=(time.time() - start) * 1000,
                error=str(e),
            )

        return RegistryCheckResult(
            package_name=package_name,
            registry=RegistryType.PYPI,
            status=PackageStatus.MALFORMED,
            exists=False,
            response_time_ms=(time.time() - start) * 1000,
            error=f"Unexpected status code: {resp.status_code}",
        )

    def validate_npm(self, package_name: str) -> RegistryCheckResult:
        """Check npm registry."""
        start = time.time()
        url = self.REGISTRY_ENDPOINTS[RegistryType.NPM].format(package_name)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.NPM,
                    status=PackageStatus.EXISTS,
                    exists=True,
                    response_time_ms=elapsed,
                    details={"version": data.get("dist-tags", {}).get("latest")},
                )
            elif resp.status_code == 404:
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.NPM,
                    status=PackageStatus.SQUATTABLE,
                    exists=False,
                    response_time_ms=elapsed,
                )
        except requests.exceptions.RequestException as e:
            return RegistryCheckResult(
                package_name=package_name,
                registry=RegistryType.NPM,
                status=PackageStatus.MALFORMED,
                exists=False,
                response_time_ms=(time.time() - start) * 1000,
                error=str(e),
            )

        return RegistryCheckResult(
            package_name=package_name,
            registry=RegistryType.NPM,
            status=PackageStatus.MALFORMED,
            exists=False,
            response_time_ms=(time.time() - start) * 1000,
            error=f"Unexpected status code: {resp.status_code}",
        )

    def validate_crates(self, package_name: str) -> RegistryCheckResult:
        """Check crates.io registry."""
        start = time.time()
        url = self.REGISTRY_ENDPOINTS[RegistryType.CRATES].format(package_name)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.CRATES,
                    status=PackageStatus.EXISTS,
                    exists=True,
                    response_time_ms=elapsed,
                    details={"version": data.get("crate", {}).get("max_version")},
                )
            elif resp.status_code == 404:
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.CRATES,
                    status=PackageStatus.SQUATTABLE,
                    exists=False,
                    response_time_ms=elapsed,
                )
        except requests.exceptions.RequestException as e:
            return RegistryCheckResult(
                package_name=package_name,
                registry=RegistryType.CRATES,
                status=PackageStatus.MALFORMED,
                exists=False,
                response_time_ms=(time.time() - start) * 1000,
                error=str(e),
            )

        return RegistryCheckResult(
            package_name=package_name,
            registry=RegistryType.CRATES,
            status=PackageStatus.MALFORMED,
            exists=False,
            response_time_ms=(time.time() - start) * 1000,
            error=f"Unexpected status code: {resp.status_code}",
        )

    def validate_rubygems(self, package_name: str) -> RegistryCheckResult:
        """Check RubyGems registry."""
        start = time.time()
        url = self.REGISTRY_ENDPOINTS[RegistryType.RUBYGEMS].format(package_name)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                data = resp.json()
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.RUBYGEMS,
                    status=PackageStatus.EXISTS,
                    exists=True,
                    response_time_ms=elapsed,
                    details={"version": data.get("version")},
                )
            elif resp.status_code == 404:
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.RUBYGEMS,
                    status=PackageStatus.SQUATTABLE,
                    exists=False,
                    response_time_ms=elapsed,
                )
        except requests.exceptions.RequestException as e:
            return RegistryCheckResult(
                package_name=package_name,
                registry=RegistryType.RUBYGEMS,
                status=PackageStatus.MALFORMED,
                exists=False,
                response_time_ms=(time.time() - start) * 1000,
                error=str(e),
            )

        return RegistryCheckResult(
            package_name=package_name,
            registry=RegistryType.RUBYGEMS,
            status=PackageStatus.MALFORMED,
            exists=False,
            response_time_ms=(time.time() - start) * 1000,
            error=f"Unexpected status code: {resp.status_code}",
        )

    def validate_go(self, package_name: str) -> RegistryCheckResult:
        """Check Go proxy registry."""
        start = time.time()
        url = self.REGISTRY_ENDPOINTS[RegistryType.GO].format(package_name)

        try:
            resp = self.session.get(url, timeout=self.timeout)
            elapsed = (time.time() - start) * 1000

            if resp.status_code == 200:
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.GO,
                    status=PackageStatus.EXISTS,
                    exists=True,
                    response_time_ms=elapsed,
                )
            elif resp.status_code == 404:
                return RegistryCheckResult(
                    package_name=package_name,
                    registry=RegistryType.GO,
                    status=PackageStatus.SQUATTABLE,
                    exists=False,
                    response_time_ms=elapsed,
                )
        except requests.exceptions.RequestException as e:
            return RegistryCheckResult(
                package_name=package_name,
                registry=RegistryType.GO,
                status=PackageStatus.MALFORMED,
                exists=False,
                response_time_ms=(time.time() - start) * 1000,
                error=str(e),
            )

        return RegistryCheckResult(
            package_name=package_name,
            registry=RegistryType.GO,
            status=PackageStatus.MALFORMED,
            exists=False,
            response_time_ms=(time.time() - start) * 1000,
            error=f"Unexpected status code: {resp.status_code}",
        )

    def validate(self, package_name: str, registry: RegistryType) -> RegistryCheckResult:
        """Dispatch to appropriate registry validator."""
        if registry == RegistryType.PYPI:
            return self.validate_pypi(package_name)
        elif registry == RegistryType.NPM:
            return self.validate_npm(package_name)
        elif registry == RegistryType.CRATES:
            return self.validate_crates(package_name)
        elif registry == RegistryType.RUBYGEMS:
            return self.validate_rubygems(package_name)
        elif registry == RegistryType.GO:
            return self.validate_go(package_name)
        elif registry == RegistryType.MAVEN:
            return RegistryCheckResult(
                package_name=package_name,
                registry=RegistryType.MAVEN,
                status=PackageStatus.MALFORMED,
                exists=False,
                response_time_ms=0,
                error="Maven validation not yet implemented",
            )

        return RegistryCheckResult(
            package_name=package_name,
            registry=registry,
            status=PackageStatus.MALFORMED,
            exists=False,
            response_time_ms=0,
            error=f"Unknown registry: {registry}",
        )
