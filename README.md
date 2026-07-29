# Order Support Agent

A modular e-commerce support agent with scoped tools, policy retrieval, and conversation memory.

The agent answers customer-support questions using:

- Claude for conversation and tool selection
- MCP tools for verified order and account information
- Harness authorization before tool execution
- TF-IDF policy retrieval for grounded policy answers
- Short-term conversation memory
- Customer-specific previous-ticket history

## How the System Works

```text
Customer message
        ↓
Conversation and customer history are loaded
        ↓
Relevant policy is retrieved
        ↓
Claude answers or proposes a tool call
        ↓
Harness checks whether the request is authorized
        ↓
Allowed requests are sent to the MCP server
        ↓
Verified tool result returns to Claude
        ↓
Claude produces the final customer response
```

The language model can propose actions, but it cannot execute tools directly. Every tool request must first pass the application’s authorization rules.

## Available Tools

### `lookup_order`

Returns the status, items, and estimated delivery date for an order.

The order must belong to the customer associated with the current support ticket.

### `check_account_status`

Returns the account standing and order history for a customer.

The requested customer ID must match the customer associated with the current support ticket.

Both tools are read-only. The agent cannot issue refunds, modify orders, or change customer accounts.

## Policy Retrieval

The project contains six short support-policy documents covering:

- Refunds
- Returns
- Shipping delays
- Damaged deliveries
- Account appeals
- Subscription cancellations

The retriever uses TF-IDF and cosine similarity to select the most relevant policy.

When no policy reaches the minimum relevance score, the agent clearly states that the available policy knowledge base does not cover the question.

The selected policy name and relevance score are printed during execution for traceability.

## Memory

### Short-term memory

Stores user and assistant messages from the current command-line conversation.

This allows the agent to understand follow-up questions such as:

```text
Where is order ORD-1001?
When is it expected to arrive?
```

### Previous-ticket history

Mock support history is stored by customer ID and included as context when relevant.

Customer histories remain separated by customer ID.

## Permission Controls

Tool access is checked at two levels:

1. The harness checks the proposed tool name and arguments before execution.
2. The MCP server independently checks the trusted customer ID before returning data.

A customer cannot retrieve an order or account belonging to another customer.

## Project Structure

```text
.
├── agent.py
├── data.py
├── harness.py
├── llm_provider.py
├── main.py
├── mcp_client.py
├── mcp_server.py
├── memory.py
├── retriever.py
├── tool_definitions.py
├── policies/
│   ├── account_appeal_policy.md
│   ├── damaged_delivery_policy.md
│   ├── refund_policy.md
│   ├── return_policy.md
│   ├── shipping_delay_policy.md
│   └── subscription_cancellation_policy.md
├── .env.example
├── .gitignore
├── pyproject.toml
└── uv.lock
```

### Main file responsibilities

- `main.py` — runs the command-line support conversation
- `agent.py` — coordinates the complete agent flow
- `harness.py` — authorizes or blocks proposed tool calls
- `mcp_server.py` — exposes the read-only MCP tools
- `mcp_client.py` — communicates with the local MCP server
- `llm_provider.py` — contains the Claude API connection
- `retriever.py` — retrieves the most relevant policy
- `memory.py` — manages conversation and previous-ticket memory
- `data.py` — contains mock orders, accounts, and ticket history
- `tool_definitions.py` — describes the available tools to Claude

## Requirements

- Python 3.11 or later
- `uv`
- An Anthropic API key

## Setup

Clone the repository and open its directory.

Install the locked dependencies:

```bash
uv sync
```

Create your local environment file:

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```text
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

The `.env` file contains secrets and must not be committed.

## Run the Agent

```bash
uv run python main.py
```

Enter one of the mock customer IDs when prompted:

```text
CUST-001
CUST-002
CUST-003
CUST-004
```

Type `exit` or `quit` to end the conversation.

## Validated Behaviours

The complete system has been manually validated for:

1. An authorized order lookup followed by a memory-based follow-up question.
2. A request for another customer’s order being blocked before MCP execution.
3. An opened-package return question answered using the retrieved return policy.
4. A suspended-account lookup using MCP, account-appeal policy, and previous-ticket history.
5. An international customs-fee question receiving an honest knowledge-gap response.

## Current Limitations

- Orders, accounts, and previous tickets use mock data.
- Policy retrieval uses lexical TF-IDF matching rather than embeddings.
- Current conversation memory exists only while the program is running.
- The MCP server runs locally using standard input and output.
- The agent provides read-only support and cannot perform account or order changes.