

"""Expose permission-scoped order-support tools through MCP."""

import os

from mcp.server.fastmcp import FastMCP

from data import ACCOUNTS, ORDERS


mcp = FastMCP("Order Support Tools")


def get_ticket_customer_id() -> str:
    """Return the trusted customer ID for the current ticket."""

    customer_id = os.environ.get("TICKET_CUSTOMER_ID")

    if not customer_id:
        raise ValueError("The current ticket customer is not configured.")

    return customer_id


@mcp.tool()
def lookup_order(order_id: str) -> dict:
    """Return an order only when it belongs to the current ticket customer."""

    ticket_customer_id = get_ticket_customer_id()
    order = ORDERS.get(order_id)

    if order is None:
        raise ValueError(f"Order '{order_id}' was not found.")

    if order["customer_id"] != ticket_customer_id:
        raise PermissionError(
            "Order access is outside the current ticket scope."
        )

    return {
        "order_id": order_id,
        **order,
    }


@mcp.tool()
def check_account_status(customer_id: str) -> dict:
    """Return an account only when it belongs to the current ticket customer."""

    ticket_customer_id = get_ticket_customer_id()

    if customer_id != ticket_customer_id:
        raise PermissionError(
            "Account access is outside the current ticket scope."
        )

    account = ACCOUNTS.get(customer_id)

    if account is None:
        raise ValueError(f"Customer '{customer_id}' was not found.")

    return {
        "customer_id": customer_id,
        **account,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")