# Order Support Agent

An e-commerce customer-support agent that answers questions about orders, deliveries, returns, refunds, subscriptions, and customer accounts. It uses Claude for conversation, retrieves relevant company policies before answering policy questions, remembers earlier messages within the current ticket, and looks up mock order and account information through read-only MCP tools. The language model can suggest a tool call, but a deterministic application harness checks whether the request is permitted before anything executes.

## Prerequisites

Before starting, ensure the following are available:

- Python 3.11 or later
- Git
- An Anthropic API key

Docker and an external database are not required. The MCP server and mock data run locally.

Check your Python version:

```bash
python --version
```

## Setup

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
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

`uv sync` automatically creates a local `.venv` virtual environment when one does not already exist. Manual activation is not required because the project commands use `uv run`.

Create the local environment file:

```bash
cp .env.example .env
```

Open `.env` and provide the required values:

```text
ANTHROPIC_API_KEY=your_actual_api_key
ANTHROPIC_MODEL=claude-sonnet-4-6
```

The variable names must remain exactly as shown because the application reads them directly.

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

Example conversation:

```text
Customer ID: CUST-001

You: What is the status of order ORD-1001?

You: When is it expected to arrive?
```

Type either of the following to finish:

```text
exit
quit
```

The command-line interface is the only run mode and should be used first.

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
├── .env.example
├── .gitignore
├── pyproject.toml
└── uv.lock
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
- `policies/` — contains the six short e-commerce support-policy documents.
- `.env.example` — lists the required environment variables without containing secrets.
- `pyproject.toml` — defines the project and its Python dependencies.
- `uv.lock` — locks dependency versions for reproducible installation.

## Why the Harness Controls Tool Execution

Model output is treated as an untrusted proposal rather than a direct instruction to execute code. Claude may propose a tool name and arguments, but deterministic Python logic in `harness.py` decides whether that request is allowed.

This design keeps authorization outside the language model. It prevents a customer from retrieving another customer’s order or account information, ensures only the two approved read-only tools can execute, and guarantees that blocked requests never reach the MCP server.

The MCP server performs an additional permission check before returning data. This provides two levels of protection:

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

## How the System Works

```text
Customer message
        ↓
Current conversation memory is updated
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

The requested order must belong to the customer associated with the current ticket.

### `check_account_status`

Returns mock account information including:

- Account standing
- Order history

The requested customer ID must match the customer associated with the current ticket.

Both tools are read-only. The agent cannot issue refunds, modify orders, cancel orders, or change customer accounts.

FastMCP validates tool arguments against generated input schemas. Calls with missing required fields or incorrect input types are rejected by the tool layer before the order or account lookup logic executes.

## Permission Scoping

The project contains five mock orders and four mock customer accounts.

Account states include:

- Active
- Flagged
- Suspended

The same customer IDs are used consistently across orders, accounts, and prior-ticket history.

Order ownership is checked before an order lookup executes. Account requests are permitted only when the requested customer ID matches the trusted customer ID attached to the current ticket.

The trusted ticket customer ID is supplied to the MCP server by the application rather than accepted from the model as trusted information.

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

The full retrieved policy content is inserted into Claude’s system prompt before the answer is generated.

## Honest Knowledge Gaps

The policy collection deliberately does not contain a policy for international customs fees.

When no policy reaches the configured relevance threshold, the retriever returns no result:

```text
[retrieved policy] No relevant policy found.
```

Claude is then instructed to state that the available policy knowledge base does not cover the question instead of inventing an answer.

## Memory

### Current-conversation memory

User and assistant messages are stored during the current ticket conversation.

This allows the agent to understand follow-up questions:

```text
You: What is the status of order ORD-1001?

You: When is it expected to arrive?
```

The second question can be answered using the earlier conversation context.

This memory exists only while the command-line program is running.

### Prior-ticket history

Mock previous support tickets are stored by customer ID.

The agent retrieves only the history belonging to the customer associated with the current ticket. This allows answers to use relevant customer history without mixing information between customers.

## Validated Behaviours

The system has been manually validated for the following end-to-end scenarios:

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