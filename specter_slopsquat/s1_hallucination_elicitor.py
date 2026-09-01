"""S1 — Hallucination Elicitor. Real LLM API calls."""
import os
import re
from datetime import datetime
from typing import Optional
from specter_slopsquat.models import HallucinatedPackage, Language


class HallucinationElicitor:
    """S1: Elicit hallucinations from LLMs via realistic code prompts."""

    PROMPT_TEMPLATES = {
        Language.PYTHON: [
            "import {0}\n# Use library for logging\nlogger = {0}.setup()",
            "from {0} import *\ndef process_data():",
            "pip install {0}\nimport {0}",
        ],
        Language.JAVASCRIPT: [
            "const {0} = require('{0}');\nconst app = {0}.express();",
            "import {0} from '{0}';\nfunction init() {{",
            "npm install {0}\nconst lib = require('{0}');",
        ],
        Language.RUST: [
            "use {0}::{{config, setup}};\nfn main() {{ setup(); }}",
            "extern crate {0};\nuse {0}::*;",
        ],
        Language.GO: [
            'import "{0}"\nfunc main() {{ {0}.Init() }}',
            'import "{0}"\nvar handler = {0}.New()',
        ],
    }

    def __init__(self):
        self.hallucinations = []
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    def elicit_from_openai(self, language: Language, prompt_count: int = 10) -> list[HallucinatedPackage]:
        """Real OpenAI API calls for completions."""
        if not self.openai_key:
            return []

        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)

            results = []
            templates = self.PROMPT_TEMPLATES.get(language, [])

            for i in range(min(prompt_count, 10)):
                template = templates[i % len(templates)] if templates else "import {0}"
                incomplete_prompt = template.format("[PACKAGE_NAME]").replace("[PACKAGE_NAME]", "")

                response = client.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt=incomplete_prompt,
                    max_tokens=50,
                    temperature=0.7,
                    n=1,
                )

                completion_text = response.choices[0].text if response.choices else ""
                package_names = self._extract_package_names(completion_text, language)

                for pkg_name in package_names:
                    results.append(HallucinatedPackage(
                        name=pkg_name,
                        language=language,
                        model="openai-gpt35",
                        prompt_id=f"openai_{i}",
                        context=completion_text[:100],
                        confidence=0.8,
                    ))

            return results
        except ImportError:
            return []
        except Exception:
            return []

    def elicit_from_anthropic(self, language: Language, prompt_count: int = 10) -> list[HallucinatedPackage]:
        """Real Anthropic API calls."""
        if not self.anthropic_key:
            return []

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)

            results = []
            templates = self.PROMPT_TEMPLATES.get(language, [])

            for i in range(min(prompt_count, 10)):
                template = templates[i % len(templates)] if templates else "import {0}"
                incomplete_prompt = f"Complete this code:\n{template.format('')}"

                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    messages=[{"role": "user", "content": incomplete_prompt}],
                )

                completion_text = response.content[0].text if response.content else ""
                package_names = self._extract_package_names(completion_text, language)

                for pkg_name in package_names:
                    results.append(HallucinatedPackage(
                        name=pkg_name,
                        language=language,
                        model="claude-3-haiku",
                        prompt_id=f"anthropic_{i}",
                        context=completion_text[:100],
                        confidence=0.85,
                    ))

            return results
        except ImportError:
            return []
        except Exception:
            return []

    @staticmethod
    def _extract_package_names(text: str, language: Language) -> list[str]:
        """Extract package names from LLM output."""
        if not text:
            return []

        if language == Language.PYTHON:
            matches = re.findall(r"import\s+(\w+)", text)
        elif language == Language.JAVASCRIPT:
            matches = re.findall(r"(?:import|require)\s+(?:.*?from\s+)?['\"]?(\w+)['\"]?", text)
        elif language == Language.RUST:
            matches = re.findall(r"use\s+(\w+)", text)
        elif language == Language.GO:
            matches = re.findall(r'import\s+"([\w/]+)"', text)
        else:
            matches = []

        return list(set(m for m in matches if m and len(m) > 2 and not m.isupper()))
