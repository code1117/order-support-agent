

"""Mock order and account data used by the support agent."""


ORDERS = {
    "ORD-1001": {
        "customer_id": "CUST-001",
        "status": "shipped",
        "items": ["Wireless Mouse"],
        "delivery_date": "2026-07-30",
    },
    "ORD-1002": {
        "customer_id": "CUST-001",
        "status": "delivered",
        "items": ["Mechanical Keyboard"],
        "delivery_date": "2026-07-22",
    },
    "ORD-2001": {
        "customer_id": "CUST-002",
        "status": "delayed",
        "items": ["USB-C Hub"],
        "delivery_date": "2026-07-27",
    },
    "ORD-3001": {
        "customer_id": "CUST-003",
        "status": "processing",
        "items": ["Laptop Stand"],
        "delivery_date": "2026-08-02",
    },
    "ORD-4001": {
        "customer_id": "CUST-004",
        "status": "delivered",
        "items": ["Noise-Cancelling Headphones"],
        "delivery_date": "2026-07-20",
    },
}


ACCOUNTS = {
    "CUST-001": {
        "standing": "active",
        "order_history": ["ORD-1001", "ORD-1002"],
    },
    "CUST-002": {
        "standing": "flagged",
        "order_history": ["ORD-2001"],
    },
    "CUST-003": {
        "standing": "suspended",
        "order_history": ["ORD-3001"],
    },
    "CUST-004": {
        "standing": "active",
        "order_history": ["ORD-4001"],
    },
}


PRIOR_TICKETS = {
    "CUST-001": [
        "Asked about a delayed order last month and received an account credit.",
    ],
    "CUST-002": [
        "Reported a damaged package and requested a replacement.",
    ],
    "CUST-003": [
        "Previously appealed an account warning.",
    ],
    "CUST-004": [],
}

ORDER_OWNERS = {
    order_id: order["customer_id"]
    for order_id, order in ORDERS.items()
}