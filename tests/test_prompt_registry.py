from pathlib import Path

import pytest

from app.prompt_management.prompt_registry import (
    PromptRegistry,
    PromptRegistryError,
)


ROOT = Path(__file__).resolve().parents[1]


def make_registry(environment="development"):
    return PromptRegistry.from_files(
        root=ROOT,
        registry_file="prompts/registry.json",
        environments_file="config/prompt-environments.json",
        environment=environment,
    )


def test_resolves_environment_specific_version():
    development = make_registry("development")
    production = make_registry("production")

    assert development.resolve_version("support_ticket_classifier") == "1.1.0"
    assert production.resolve_version("support_ticket_classifier") == "1.0.0"


def test_can_render_active_prompt():
    registry = make_registry("development")

    prompt = registry.render(
        "support_ticket_classifier",
        ticket_text="My payment was deducted twice.",
    )

    assert "My payment was deducted twice." in prompt
    assert "untrusted customer content" in prompt


def test_can_render_explicit_older_version():
    registry = make_registry("development")

    prompt = registry.render(
        "support_ticket_classifier",
        version="1.0.0",
        ticket_text="The order is late.",
    )

    assert "Classify the ticket" in prompt


def test_rejects_unknown_prompt():
    registry = make_registry()

    with pytest.raises(PromptRegistryError, match="Unknown prompt"):
        registry.render("missing_prompt", ticket_text="hello")


def test_rejects_unknown_version():
    registry = make_registry()

    with pytest.raises(PromptRegistryError, match="Unknown version"):
        registry.render(
            "support_ticket_classifier",
            version="9.9.9",
            ticket_text="hello",
        )


def test_rejects_missing_variable():
    registry = make_registry()

    with pytest.raises(PromptRegistryError, match="missing"):
        registry.render("support_ticket_classifier")


def test_rejects_unexpected_variable():
    registry = make_registry()

    with pytest.raises(PromptRegistryError, match="unexpected"):
        registry.render(
            "support_ticket_classifier",
            ticket_text="hello",
            tenant="unexpected",
        )


def test_rejects_non_string_variable():
    registry = make_registry()

    with pytest.raises(PromptRegistryError, match="must be strings"):
        registry.render(
            "support_ticket_classifier",
            ticket_text=123,  # type: ignore[arg-type]
        )


def test_rejects_unknown_environment():
    with pytest.raises(PromptRegistryError, match="Unknown environment"):
        make_registry("qa")


def test_rejects_template_path_traversal(tmp_path):
    registry = make_registry()
    registry.registry["prompts"]["support_ticket_classifier"]["versions"]["1.0.0"][
        "file"
    ] = "../outside.txt"

    with pytest.raises(PromptRegistryError, match="escapes project root"):
        registry.render(
            "support_ticket_classifier",
            version="1.0.0",
            ticket_text="hello",
        )
