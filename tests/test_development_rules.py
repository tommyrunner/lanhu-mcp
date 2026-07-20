"""Tests for the optional design-to-code development rules workflow."""

import asyncio
import hashlib
import inspect
from unittest.mock import patch

import lanhu_mcp_server as server


def test_load_development_rules_uses_default_markdown():
    with patch.dict("os.environ", {"LANHU_DEVELOPMENT_RULES_PATH": ""}):
        result = server._load_development_rules()

    assert result["status"] == "success"
    assert result["source"] == str(server.DEFAULT_DEVELOPMENT_RULES_PATH)
    assert result["content"] == server.DEFAULT_DEVELOPMENT_RULES_PATH.read_text(encoding="utf-8")
    assert result["sha256"] == hashlib.sha256(result["content"].encode("utf-8")).hexdigest()


def test_load_development_rules_allows_external_override(tmp_path):
    custom_rules = tmp_path / "team-rules.md"
    custom_rules.write_text("# Team rules\n\nUse the existing project conventions.\n", encoding="utf-8")

    with patch.dict("os.environ", {"LANHU_DEVELOPMENT_RULES_PATH": str(custom_rules)}):
        result = server._load_development_rules()

    assert result == {
        "status": "success",
        "source": str(custom_rules),
        "sha256": hashlib.sha256(custom_rules.read_bytes()).hexdigest(),
        "content": custom_rules.read_text(encoding="utf-8"),
        "required_next_step": "Analyze modules, file structure, and static behavior before coding.",
    }


def test_development_rules_tool_returns_versioned_complete_content():
    with patch.dict("os.environ", {"LANHU_DEVELOPMENT_RULES_PATH": ""}):
        result = asyncio.run(server.lanhu_get_development_rules())

    assert result["status"] == "success"
    assert result["source"]
    assert len(result["sha256"]) == 64
    assert result["content"].startswith("# Lanhu Design-to-Code Development Rules")
    assert result["required_next_step"]


def test_load_development_rules_rejects_invalid_external_files(tmp_path):
    missing = tmp_path / "missing.md"
    empty = tmp_path / "empty.md"
    invalid_utf8 = tmp_path / "invalid.md"
    too_large = tmp_path / "too-large.md"
    empty.write_text("", encoding="utf-8")
    invalid_utf8.write_bytes(b"\xff\xfe")
    too_large.write_bytes(b"x" * (server.MAX_DEVELOPMENT_RULES_BYTES + 1))

    for path, expected_message in (
        (missing, "does not exist"),
        (empty, "is empty"),
        (invalid_utf8, "UTF-8"),
        (too_large, "exceeds"),
    ):
        with patch.dict("os.environ", {"LANHU_DEVELOPMENT_RULES_PATH": str(path)}):
            result = server._load_development_rules()

        assert result["status"] == "error"
        assert expected_message in result["message"]
        assert result["required_action"]


def test_load_development_rules_uses_builtin_fallback_when_default_file_is_missing(tmp_path):
    missing_default = tmp_path / "DEVELOPMENT_RULES.md"

    with (
        patch.dict("os.environ", {"LANHU_DEVELOPMENT_RULES_PATH": ""}),
        patch.object(server, "DEFAULT_DEVELOPMENT_RULES_PATH", missing_default),
    ):
        result = server._load_development_rules()

    assert result["status"] == "success"
    assert result["source"] == "built-in fallback"
    assert result["content"] == server.DEFAULT_DEVELOPMENT_RULES_CONTENT


def test_development_mode_rejects_bad_rules_before_network_access(tmp_path):
    missing = tmp_path / "missing.md"

    with (
        patch.dict("os.environ", {"LANHU_DEVELOPMENT_RULES_PATH": str(missing)}),
        patch.object(server, "LanhuExtractor", side_effect=AssertionError("network client must not be created")),
    ):
        result = asyncio.run(
            server.lanhu_get_ai_analyze_design_result(
                "https://lanhuapp.com/web/#/item/project/stage?pid=test",
                "all",
                for_development=True,
            )
        )

    assert len(result) == 1
    assert "Unable to read development rules" in result[0]
    assert "does not exist" in result[0]


def test_normal_analysis_does_not_load_development_rules():
    with (
        patch.object(server, "_load_development_rules", side_effect=AssertionError("rules must remain optional")),
        patch.object(server, "LanhuExtractor", side_effect=RuntimeError("normal analysis continued")),
    ):
        try:
            asyncio.run(
                server.lanhu_get_ai_analyze_design_result(
                    "https://lanhuapp.com/web/#/item/project/stage?pid=test",
                    "all",
                )
            )
        except RuntimeError as exc:
            assert str(exc) == "normal analysis continued"
        else:
            raise AssertionError("normal analysis did not continue to its existing network path")


def test_development_flag_preserves_existing_positional_context_parameter():
    parameters = list(inspect.signature(server.lanhu_get_ai_analyze_design_result).parameters)

    assert parameters[:4] == ["url", "design_names", "ctx", "for_development"]
    assert inspect.signature(server.lanhu_get_ai_analyze_design_result).parameters["for_development"].default is False


def test_design_tool_descriptions_explain_development_workflow():
    designs_docs = server.lanhu_get_designs.__doc__ or ""
    analyze_docs = server.lanhu_get_ai_analyze_design_result.__doc__ or ""
    slices_docs = server.lanhu_get_design_slices.__doc__ or ""

    assert "lanhu_get_development_rules" in designs_docs
    assert "lanhu_get_development_rules" in slices_docs
    assert "for_development" in analyze_docs
    assert "Canvas coordinates" in analyze_docs
    assert "runtime positioning" in analyze_docs
