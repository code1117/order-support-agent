"""Manage the current conversation and retrieve previous customer tickets."""

from data import PRIOR_TICKETS


def create_conversation() -> list[dict[str, str]]:
    """Create an empty short-term memory buffer for a new ticket."""

    return []


def add_message(
    conversation: list[dict[str, str]],
    role: str,
    content: str,
) -> None:
    """Add one user or assistant message to the current conversation."""

    conversation.append(
        {
            "role": role,
            "content": content,
        }
    )


def get_prior_tickets(customer_id: str) -> list[str]:
    """Return the stored support history for one customer."""

    return PRIOR_TICKETS.get(customer_id, []).copy()
