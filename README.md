# Order Support Agent

An e-commerce customer-support agent that answers questions about order status, deliveries, returns, refunds, subscriptions, and customer accounts. It uses Claude for conversation, retrieves relevant company policies before answering policy questions, remembers earlier messages within the current ticket, and retrieves mock order and account information through read-only MCP tools. The language model may propose a tool call, but deterministic application code checks whether the request is permitted before anything executes.

## Prerequisites

The following must be available before setup:

- Python 3.11 or later
- Git
- An Anthropic API key

Docker, an external database, and a separate vector database are not required.

Check that Python and Git are available:

```bash
python --version
git --version
```

Use `python3` instead of `python` if that is the command configured on your machine.

## Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/code1117/order-support-agent.git
cd order-support-agent
```

Install `uv` using Python:

```bash
python -m pip install uv
```

Create the project virtual environment and install the locked dependencies:

```bash
uv sync
```

`uv sync` automatically creates a local `.venv` virtual environment when one does not already exist. Manual activation is not required because the project is run through `uv run`.

Create the local environment file:

```bash
cp .env.example .env
```

Open `.env` and provide the required values:

```text
ANTHROPIC_API_KEY=your_actual_api_key
ANTHROPIC_MODEL=claude-sonnet-4-6
```

The environment-variable names must remain exactly as shown because the application reads them directly.

The `.env` file contains a secret and must not be committed to Git.

## How to Run

Start the command-line support agent:

```bash
uv run python main.py
```

Enter one of the available mock customer IDs when prompted:

```text
CUST-001
CUST-002
CUST-003
CUST-004
```

Example:

```text
Customer ID: CUST-001

You: What is the status of order ORD-1001?

You: When is it expected to arrive?
```

Type either of the following to end the conversation:

```text
exit
quit
```

The command-line interface is the only run mode.

## Project Structure

```text
.
├── main.py
├── agent.py
├── harness.py
├── mcp_server.py
├── mcp_client.py
├── tool_definitions.py
├── llm_provider.py
├── retriever.py
├── memory.py
├── data.py
├── policies/
│   ├── account_appeal_policy.md
│   ├── damaged_delivery_policy.md
│   ├── refund_policy.md
│   ├── return_policy.md
│   ├── shipping_delay_policy.md
│   └── subscription_cancellation_policy.md
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

- `main.py` — starts and manages the command-line conversation.
- `agent.py` — contains the complete agent loop and coordinates all components.
- `harness.py` — authorizes or blocks model-proposed tool calls.
- `mcp_server.py` — exposes the two read-only tools through FastMCP.
- `mcp_client.py` — connects to the local MCP server and executes permitted tools.
- `tool_definitions.py` — describes the available tools and their schemas to Claude.
- `llm_provider.py` — contains the isolated Anthropic API connection.
- `retriever.py` — loads policy documents and retrieves the most relevant policy chunk.
- `memory.py` — manages current-conversation memory and prior-ticket lookup.
- `data.py` — contains mock orders, accounts, ownership mappings, and ticket history.
- `policies/` — contains the six e-commerce support-policy documents.
- `.env.example` — lists the required environment variables without containing secrets.
- `.gitignore` — prevents local environments, secrets, and generated files from being tracked.
- `.python-version` — records the project’s selected Python version.
- `pyproject.toml` — defines the project and its dependencies.
- `uv.lock` — locks dependency versions for reproducible installation.
- `README.md` — explains setup, design decisions, usage, and limitations.

## Why the Harness Controls Tool Execution

Model output is treated as an untrusted proposal rather than a direct instruction to execute code. Claude may propose a tool name and arguments, but deterministic Python logic in `harness.py` decides whether the request is allowed.

This keeps authorization outside the language model. It prevents a customer from retrieving another customer’s order or account information, ensures that only approved read-only tools can execute, and guarantees that blocked requests do not reach the MCP server.

The MCP server performs an additional permission check before returning any data:

```text
Claude proposes a tool call
        ↓
The harness checks the tool and customer scope
        ↓
Blocked requests stop here
        ↓
Allowed requests reach the MCP server
        ↓
The MCP server checks the customer scope again
        ↓
The read-only tool returns verified data
```

### Ticket Scope

The agent is intentionally limited to order status, delivery issues, returns and refunds, subscription cancellation, and account questions.

I chose this fixed scope because every supported ticket type can be grounded in either one of the two read-only MCP tools or one of the six policy documents. Keeping the scope fixed makes the agent’s behaviour easier to inspect and prevents it from proposing unrelated or unsupported actions.

### MCP Permission Boundary

The customer ID attached to the current support ticket is treated as trusted application context rather than a value supplied by Claude.

An order lookup is permitted only when the stored owner of that order matches the current ticket customer. An account lookup is permitted only when the requested customer ID matches the current ticket customer.

This boundary is checked in both the harness and the MCP server. The harness blocks invalid requests before execution, while the MCP server independently enforces the same rule so customer data remains protected even if the server is reached through another path.

## How the System Works

```text
Customer message
        ↓
Current-conversation memory is updated
        ↓
Previous customer-ticket history is loaded
        ↓
The most relevant policy chunk is retrieved
        ↓
Claude receives the conversation, policy, and customer history
        ↓
Claude answers directly or proposes a tool call
        ↓
The harness authorizes or blocks the proposal
        ↓
An allowed request runs through the MCP server
        ↓
The verified tool result is returned to Claude
        ↓
Claude produces the final customer response
        ↓
The response is stored in current-conversation memory
```

## Available Tools

### `lookup_order`

Returns mock order information including:

- Order status
- Items
- Estimated delivery date

The requested order must belong to the customer associated with the current support ticket.

### `check_account_status`

Returns mock account information including:

- Account standing
- Order history

The requested customer ID must match the customer associated with the current support ticket.

Both tools are read-only. The agent cannot issue refunds, modify orders, cancel orders, or change customer accounts.

FastMCP validates tool arguments against generated input schemas. Calls with missing required fields or incorrect input types are rejected by the tool layer before the order or account lookup logic executes.

## Permission Scoping

The project contains five mock orders and four mock customer accounts.

The mock account data includes:

- Active accounts
- Flagged accounts
- Suspended accounts

The same customer IDs are used consistently across orders, accounts, and prior-ticket history.

Order ownership is checked before an order lookup executes. Account requests are permitted only when the requested customer ID matches the trusted customer ID attached to the current ticket.

The trusted ticket customer ID is supplied to the MCP server by the application rather than accepted from the language model as trusted information.

## Policy Retrieval

The project contains six short Markdown policy documents:

- `refund_policy.md`
- `return_policy.md`
- `shipping_delay_policy.md`
- `damaged_delivery_policy.md`
- `account_appeal_policy.md`
- `subscription_cancellation_policy.md`

Each document covers one policy area and includes specific conditions such as day counts, processing periods, or compensation amounts.

Each complete policy document is treated as one retrievable chunk.

The retriever uses TF-IDF and cosine similarity to retrieve the top one relevant chunk:

```text
k = 1
```

The selected policy filename and relevance score are printed for every customer message:

```text
[retrieved policy] return_policy.md (score: 0.511)
```

The complete retrieved policy content is inserted into Claude’s system prompt before the answer is generated.

### Retrieval Choice

I chose TF-IDF because the policy collection is small and lexical retrieval is sufficient to demonstrate traceable grounding without introducing a vector database.

The retrieval logic is isolated inside `retriever.py`, so an embedding model or vector database such as Chroma or FAISS can replace it later without changing the harness, MCP tools, memory, or conversation flow.

## Honest Knowledge Gaps

The policy collection deliberately does not contain a policy for international customs fees.

When no policy reaches the configured relevance threshold, the retriever returns no result:

```text
[retrieved policy] No relevant policy found.
```

Claude is then instructed to state that the available policy knowledge base does not cover the question instead of inventing an answer.

## Memory

### Current-Conversation Memory

User and assistant messages are stored during the current ticket conversation.

This allows the agent to understand follow-up questions:

```text
You: What is the status of order ORD-1001?

You: When is it expected to arrive?
```

The second question can be answered using the earlier conversation context.

This memory exists only while the command-line program is running.

### Prior-Ticket History

Mock previous support tickets are stored by customer ID.

The agent retrieves only the history belonging to the customer associated with the current ticket. This allows responses to use relevant customer history without mixing information between customers.

## Validated Behaviours

The system has been manually validated for the following end-to-end behaviours:

1. **Authorized order lookup**

   `CUST-001` successfully retrieves `ORD-1001` through the MCP order tool.

2. **Current-conversation memory**

   After retrieving `ORD-1001`, the agent correctly answers a follow-up question about its delivery date without repeating the lookup.

3. **Blocked cross-customer access**

   `CUST-001` is prevented from retrieving `ORD-2001`, which belongs to `CUST-002`. The harness blocks the request before MCP execution.

4. **Policy-grounded return answer**

   A question about returning an opened but unused item retrieves `return_policy.md` and answers using its stated conditions.

5. **Account lookup and prior-ticket history**

   `CUST-003` retrieves a suspended account status, receives information from the account-appeal policy, and receives relevant context from previous-ticket history.

6. **Honest knowledge gap**

   A question about international customs fees returns no relevant policy, and the agent clearly states that the subject is not covered.

7. **Schema validation**

   Calls with a missing required argument or an incorrect argument type are rejected by FastMCP’s generated tool schema before the tool logic executes.

## Current Limitations

- Orders, accounts, and previous tickets use mock in-memory data.
- Policy retrieval uses lexical TF-IDF matching rather than semantic embeddings.
- Each policy document is treated as one chunk.
- The retriever currently returns only the top one chunk.
- Current-conversation memory is not retained after the program exits.
- The MCP server runs locally through standard input and output.
- The system uses a single configured LLM provider.
- The agent provides read-only support and cannot perform irreversible actions.