"""A small, file-based prompt registry for learning and local applications.

This implementation intentionally uses only the Python standard library.
It is not a multi-user remote registry or a complete authorization system.
"""

import json
import string
from pathlib import Path
from typing import Any


class PromptRegistryError(Exception):
    """Raised when prompt metadata, versions, or templates are invalid."""


class PromptRegistry:
    def __init__(
        self,
        *,
        root: Path,
        registry: dict[str, Any],
        environments: dict[str, Any],
        environment: str,
    ) -> None:
        self.root = root.resolve()
        self.registry = registry
        self.environments = environments
        self.environment = environment

        if environment not in environments:
            raise PromptRegistryError(
                f"Unknown environment: {environment}"
            )

    @classmethod
    def from_files(
        cls,
        *,
        root: Path,
        registry_file: str,
        environments_file: str,
        environment: str,
    ) -> "PromptRegistry":
        root = root.resolve()
        registry_path = (root / registry_file).resolve()
        environments_path = (root / environments_file).resolve()

        for path in (registry_path, environments_path):
            if not path.is_relative_to(root):
                raise PromptRegistryError("Configuration path escapes project root")
            if not path.is_file():
                raise PromptRegistryError(f"Configuration file not found: {path}")

        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            environments = json.loads(
                environments_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise PromptRegistryError("Invalid JSON configuration") from exc

        if not isinstance(registry.get("prompts"), dict):
            raise PromptRegistryError("Registry must contain a prompts object")

        return cls(
            root=root,
            registry=registry,
            environments=environments,
            environment=environment,
        )

    def resolve_version(
        self,
        prompt_id: str,
        version: str | None = None,
    ) -> str:
        prompt = self.registry["prompts"].get(prompt_id)
        if prompt is None:
            raise PromptRegistryError(f"Unknown prompt: {prompt_id}")

        if version is None:
            active = self.environments[self.environment]
            version = active.get(prompt_id)

        if not version:
            raise PromptRegistryError(
                f"No active version configured for {prompt_id} "
                f"in {self.environment}"
            )

        if version not in prompt.get("versions", {}):
            raise PromptRegistryError(
                f"Unknown version {version} for prompt {prompt_id}"
            )

        return version

    def _load_template(self, prompt_id: str, version: str) -> tuple[str, set[str]]:
        prompt = self.registry["prompts"][prompt_id]
        metadata = prompt["versions"][version]
        relative_path = Path(metadata["file"])

        if relative_path.is_absolute():
            raise PromptRegistryError("Prompt template path must be relative")

        template_path = (self.root / relative_path).resolve()
        if not template_path.is_relative_to(self.root):
            raise PromptRegistryError("Prompt template path escapes project root")
        if not template_path.is_file():
            raise PromptRegistryError(f"Prompt template not found: {relative_path}")

        template = template_path.read_text(encoding="utf-8")
        try:
            parsed_variables = {
                field
                for _, field, _, _ in string.Formatter().parse(template)
                if field is not None
            }
        except ValueError as exc:
            raise PromptRegistryError("Malformed prompt template") from exc

        declared_variables = set(metadata.get("variables", []))
        if parsed_variables != declared_variables:
            raise PromptRegistryError(
                "Template variables do not match registry metadata: "
                f"declared={sorted(declared_variables)}, "
                f"found={sorted(parsed_variables)}"
            )

        return template, declared_variables

    def render(
        self,
        prompt_id: str,
        *,
        version: str | None = None,
        **variables: str,
    ) -> str:
        resolved_version = self.resolve_version(prompt_id, version)
        template, required_variables = self._load_template(
            prompt_id, resolved_version
        )

        supplied_variables = set(variables)
        missing = required_variables - supplied_variables
        unexpected = supplied_variables - required_variables

        if missing or unexpected:
            raise PromptRegistryError(
                f"Invalid variables: missing={sorted(missing)}, "
                f"unexpected={sorted(unexpected)}"
            )

        if not all(isinstance(value, str) for value in variables.values()):
            raise PromptRegistryError("All prompt variables must be strings")

        try:
            return template.format(**variables)
        except (KeyError, ValueError, IndexError) as exc:
            raise PromptRegistryError("Could not render prompt template") from exc
