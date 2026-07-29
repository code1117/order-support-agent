

"""Coordinate policy retrieval, memory, authorization, MCP tools, and Claude."""

import json
from typing import Any

from data import ORDER_OWNERS
from harness import authorize_tool_call
from llm_provider import call_model
from mcp_client import run_mcp_tool
from memory import add_message, get_prior_tickets
from retriever import retrieve_policy
from tool_definitions import TOOL_DEFINITIONS


MAX_TOOL_ROUNDS = 3


def build_system_prompt(
    ticket_customer_id: str,
    policy: dict[str, object] | None,
    prior_tickets: list[str],
) -> str:
    """Build the instructions and trusted context for one customer turn."""

    if policy:
        policy_context = str(policy["content"])
    else:
        policy_context = (
            "No relevant policy was found. Be honest that the policy "
            "knowledge base does not cover the customer's policy question."
        )

    if prior_tickets:
        ticket_history = "\n".join(
            f"- {ticket}" for ticket in prior_tickets
        )
    else:
        ticket_history = "No previous support tickets were found."

    return f"""
You are a careful e-commerce customer-support agent.

Current ticket customer ID: {ticket_customer_id}

Follow these rules:
- Answer using the conversation, retrieved policy, prior tickets, and verified tool results.
- Use lookup_order for questions about order status, items, or delivery dates.
- Use check_account_status for questions about account standing or order history.
- Never assume that a requested order or customer is authorized.
- Never claim a tool result before the tool has actually run.
- Do not issue refunds, modify orders, or change accounts.
- When no relevant policy exists, clearly say the policy knowledge base does not cover the question.
- Keep the response concise and helpful.

Retrieved policy:
{policy_context}

Previous support tickets for this customer:
{ticket_history}
""".strip()


def response_content_as_dicts(response: Any) -> list[dict[str, Any]]:
    """Convert Claude response blocks into messages that can be sent back."""

    return [
        block.model_dump(exclude_none=True)
        for block in response.content
    ]


def execute_tool_requests(
    response: Any,
    ticket_customer_id: str,
) -> list[dict[str, Any]]:
    """Authorize proposed tools, execute allowed MCP calls, and format results."""

    tool_results = []

    for block in response.content:
        if block.type != "tool_use":
            continue

        tool_name = block.name
        arguments = dict(block.input)

        print(f"[tool proposed] {tool_name}: {arguments}")

        allowed, reason = authorize_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            ticket_customer_id=ticket_customer_id,
            order_owners=ORDER_OWNERS,
        )

        if allowed:
            print(f"[harness allowed] {reason}")

            result = run_mcp_tool(
                tool_name=tool_name,
                arguments=arguments,
                ticket_customer_id=ticket_customer_id,
            )
        else:
            print(f"[harness blocked] {reason}")

            result = {
                "ok": False,
                "error": reason,
            }

        tool_results.append(
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
                "is_error": not bool(result.get("ok")),
            }
        )

    return tool_results


def extract_response_text(response: Any) -> str:
    """Combine Claude's final text blocks into one customer response."""

    text_parts = [
        block.text
        for block in response.content
        if block.type == "text"
    ]

    return "\n".join(text_parts).strip()


def handle_support_message(
    ticket_customer_id: str,
    user_message: str,
    conversation: list[dict[str, str]],
) -> str:
    """Process one customer message through the complete controlled agent."""

    add_message(
        conversation=conversation,
        role="user",
        content=user_message,
    )

    policy = retrieve_policy(user_message)

    if policy:
        print(
            f"[retrieved policy] {policy['name']} "
            f"(score: {policy['score']:.3f})"
        )
    else:
        print("[retrieved policy] No relevant policy found.")

    prior_tickets = get_prior_tickets(ticket_customer_id)

    system_prompt = build_system_prompt(
        ticket_customer_id=ticket_customer_id,
        policy=policy,
        prior_tickets=prior_tickets,
    )

    api_messages: list[dict[str, Any]] = [
        dict(message) for message in conversation
    ]

    response = call_model(
        system_prompt=system_prompt,
        messages=api_messages,
        tools=TOOL_DEFINITIONS,
    )

    tool_rounds = 0

    while response.stop_reason == "tool_use":
        if tool_rounds >= MAX_TOOL_ROUNDS:
            raise RuntimeError(
                "The agent exceeded the maximum number of tool rounds."
            )

        api_messages.append(
            {
                "role": "assistant",
                "content": response_content_as_dicts(response),
            }
        )

        tool_results = execute_tool_requests(
            response=response,
            ticket_customer_id=ticket_customer_id,
        )

        if not tool_results:
            raise RuntimeError(
                "Claude requested tool use without providing a tool call."
            )

        api_messages.append(
            {
                "role": "user",
                "content": tool_results,
            }
        )

        response = call_model(
            system_prompt=system_prompt,
            messages=api_messages,
            tools=TOOL_DEFINITIONS,
        )

        tool_rounds += 1

    final_answer = extract_response_text(response)

    if not final_answer:
        raise RuntimeError("Claude returned no final response text.")

    add_message(
        conversation=conversation,
        role="assistant",
        content=final_answer,
    )

    return final_answer
