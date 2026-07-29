

"""Define the read-only support tools available to the language model."""

from typing import Any


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "lookup_order",
        "description": (
            "Look up the status, items, and delivery date for a specific order. "
            "Use this when the customer asks about an order or delivery."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID, such as ORD-1001.",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "check_account_status",
        "description": (
            "Look up a customer's account standing and previous order IDs. "
            "Use this when the customer asks about their account status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer ID, such as CUST-001.",
                }
            },
            "required": ["customer_id"],
        },
    },
]