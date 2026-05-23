import inspect
from pathlib import Path

import pytest

from app.agent import graph, nodes


IMPLEMENTED_GRAPH_NODES = {
    "receive_request",
    "detect_input_source",
    "extract_email_text",
    "detect_attachments",
    "extract_attachment_content",
    "merge_context",
    "extract_request_fields",
    "validate_extraction",
    "search_vendors",
    "rank_vendors",
    "generate_rfq_drafts",
    "email_guardrail_check",
    "create_pending_approval",
    "wait_for_admin_approval",
    "log_completion",
}


def test_compiled_graph_uses_documented_request_processing_nodes():
    compiled_nodes = set(graph.procurement_graph.get_graph().nodes)

    assert IMPLEMENTED_GRAPH_NODES.issubset(compiled_nodes)
    assert "receive_email" not in compiled_nodes


@pytest.mark.parametrize(
    ("input_source", "expected_route"),
    [
        ("email_only", "extract_email_text"),
        ("attachment_only", "detect_attachments"),
        ("email_and_attachment", "extract_email_text"),
        ("empty", "create_pending_approval"),
    ],
)
def test_detect_input_source_routing(input_source, expected_route):
    assert graph.route_from_input_source({"input_source": input_source}) == expected_route


def test_email_only_route_skips_attachment_extraction():
    state = {"input_source": "email_only", "has_attachments": False}

    assert graph.route_from_input_source(state) == "extract_email_text"
    assert graph.route_after_email_text(state) == "merge_context"


def test_attachment_only_route_skips_email_extraction():
    state = {"input_source": "attachment_only"}

    assert graph.route_from_input_source(state) == "detect_attachments"


def test_combined_route_extracts_email_then_attachments_before_merge():
    state = {"input_source": "email_and_attachment", "has_attachments": True}

    assert graph.route_from_input_source(state) == "extract_email_text"
    assert graph.route_after_email_text(state) == "detect_attachments"


def test_merge_context_does_not_call_llm_extraction():
    source = inspect.getsource(nodes.merge_context)

    assert "LLMService" not in source
    assert "extract_purchase_request" not in source


def test_extract_request_fields_is_the_llm_extraction_node():
    source = inspect.getsource(nodes.extract_request_fields)

    assert "LLMService" in source
    assert "extract_purchase_request" in source


def test_extraction_failure_routes_to_pending_approval():
    state = {
        "field_extraction_failed": True,
        "validation_errors": ["Invalid LLM JSON or extraction schema"],
    }

    assert graph.route_after_field_extraction(state) == "create_pending_approval"


def test_no_vendors_found_routes_to_pending_approval():
    assert graph.route_after_vendor_search({"matched_vendors": []}) == "create_pending_approval"


def test_guardrail_failure_routes_to_pending_approval():
    state = {"guardrail_status": "Failed", "requires_admin_review": True}

    assert graph.route_after_guardrail(state) == "create_pending_approval"


def test_pipeline_docs_include_implemented_node_names():
    docs_root = Path(__file__).resolve().parents[2] / "docs"
    markdown = (docs_root / "agent_pipeline.md").read_text(encoding="utf-8")
    mermaid = (docs_root / "agent_pipeline.mmd").read_text(encoding="utf-8")

    for node_name in IMPLEMENTED_GRAPH_NODES:
        assert node_name in markdown
        assert node_name in mermaid

    assert "needs_review_validation --> search_vendors" not in markdown
    assert "needs_review_validation --> search_vendors" not in mermaid
