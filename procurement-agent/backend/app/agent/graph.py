from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    create_pending_approval,
    detect_attachments,
    detect_input_source,
    email_guardrail_check,
    extract_attachment_content,
    extract_email_text,
    extract_request_fields,
    generate_rfq_drafts,
    log_completion,
    merge_context,
    rank_vendors,
    receive_request,
    search_vendors_node,
    validate_extraction,
    wait_for_admin_approval,
)
from app.agent.state import AgentState


def route_from_input_source(state: AgentState) -> str:
    input_source = state.get("input_source")
    if input_source == "email_only":
        return "extract_email_text"
    if input_source == "attachment_only":
        return "detect_attachments"
    if input_source == "email_and_attachment":
        return "extract_email_text"
    return "create_pending_approval"


def route_after_email_text(state: AgentState) -> str:
    if state.get("has_attachments"):
        return "detect_attachments"
    return "merge_context"


def route_after_field_extraction(state: AgentState) -> str:
    if state.get("field_extraction_failed") or state.get("validation_errors"):
        return "create_pending_approval"
    return "validate_extraction"


def route_after_validation(state: AgentState) -> str:
    fields = state.get("extracted_fields") or {}
    missing = fields.get("missing_fields") or []
    confidence = float(fields.get("confidence_score") or 0)
    if (
        state.get("validation_errors")
        or missing
        or confidence < 0.65
        or state.get("conflicts")
        or state.get("requires_admin_review")
    ):
        return "create_pending_approval"
    return "search_vendors"


def route_after_vendor_search(state: AgentState) -> str:
    if state.get("matched_vendors"):
        return "rank_vendors"
    return "create_pending_approval"


def route_after_vendor_ranking(state: AgentState) -> str:
    if state.get("selected_vendors"):
        return "generate_rfq_drafts"
    return "create_pending_approval"


def route_after_guardrail(state: AgentState) -> str:
    return "create_pending_approval"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("receive_request", receive_request)
    graph.add_node("detect_input_source", detect_input_source)
    graph.add_node("extract_email_text", extract_email_text)
    graph.add_node("detect_attachments", detect_attachments)
    graph.add_node("extract_attachment_content", extract_attachment_content)
    graph.add_node("merge_context", merge_context)
    graph.add_node("extract_request_fields", extract_request_fields)
    graph.add_node("validate_extraction", validate_extraction)
    graph.add_node("search_vendors", search_vendors_node)
    graph.add_node("rank_vendors", rank_vendors)
    graph.add_node("generate_rfq_drafts", generate_rfq_drafts)
    graph.add_node("email_guardrail_check", email_guardrail_check)
    graph.add_node("create_pending_approval", create_pending_approval)
    graph.add_node("wait_for_admin_approval", wait_for_admin_approval)
    graph.add_node("log_completion", log_completion)

    graph.add_edge(START, "receive_request")
    graph.add_edge("receive_request", "detect_input_source")
    graph.add_conditional_edges(
        "detect_input_source",
        route_from_input_source,
        {
            "extract_email_text": "extract_email_text",
            "detect_attachments": "detect_attachments",
            "create_pending_approval": "create_pending_approval",
        },
    )
    graph.add_conditional_edges(
        "extract_email_text",
        route_after_email_text,
        {
            "detect_attachments": "detect_attachments",
            "merge_context": "merge_context",
        },
    )
    graph.add_edge("detect_attachments", "extract_attachment_content")
    graph.add_edge("extract_attachment_content", "merge_context")
    graph.add_edge("merge_context", "extract_request_fields")
    graph.add_conditional_edges(
        "extract_request_fields",
        route_after_field_extraction,
        {
            "validate_extraction": "validate_extraction",
            "create_pending_approval": "create_pending_approval",
        },
    )
    graph.add_conditional_edges(
        "validate_extraction",
        route_after_validation,
        {
            "search_vendors": "search_vendors",
            "create_pending_approval": "create_pending_approval",
        },
    )
    graph.add_conditional_edges(
        "search_vendors",
        route_after_vendor_search,
        {
            "rank_vendors": "rank_vendors",
            "create_pending_approval": "create_pending_approval",
        },
    )
    graph.add_conditional_edges(
        "rank_vendors",
        route_after_vendor_ranking,
        {
            "generate_rfq_drafts": "generate_rfq_drafts",
            "create_pending_approval": "create_pending_approval",
        },
    )
    graph.add_edge("generate_rfq_drafts", "email_guardrail_check")
    graph.add_conditional_edges(
        "email_guardrail_check",
        route_after_guardrail,
        {"create_pending_approval": "create_pending_approval"},
    )
    graph.add_edge("create_pending_approval", "wait_for_admin_approval")
    graph.add_edge("wait_for_admin_approval", "log_completion")
    graph.add_edge("log_completion", END)
    return graph.compile()


procurement_graph = build_graph()
