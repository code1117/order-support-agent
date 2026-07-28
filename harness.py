

"""Control whether proposed tool calls are allowed to execute."""


def authorize_tool_call(
    tool_name: str,
    arguments: dict[str, str],
    ticket_customer_id: str,
    order_owners: dict[str, str],
) -> tuple[bool, str]:
    """Allow only tool calls that stay within the current customer's ticket."""

    if tool_name == "lookup_order":
        order_id = arguments.get("order_id")
        order_owner = order_owners.get(order_id) if order_id else None

        if order_owner != ticket_customer_id:
            return False, "Order access is outside the current ticket scope."

        return True, "Order access is allowed."

    if tool_name == "check_account_status":
        customer_id = arguments.get("customer_id")

        if customer_id != ticket_customer_id:
            return False, "Account access is outside the current ticket scope."

        return True, "Account access is allowed."

    return False, f"Tool '{tool_name}' is not allowed."


